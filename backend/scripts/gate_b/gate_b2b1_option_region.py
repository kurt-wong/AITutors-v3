"""Gate B2-B1: Option Region Structure Extraction.

验证：给定 options_lines Region，能否从 region 中正确恢复 per-option structure。

三层验证（对应 B2-B 统一框架）：
  Layer 1 — Region Binding:      options_lines region 存在且包含非空内容
  Layer 2 — Structure Extraction: region 内能解析出 ≥2 个 option（label + text）
  Layer 3 — Label Sequence:      解析出的 label 序列合理（连续/递增）

与 B1 的区别：
  B1 逐行拆分 region → 每行一个 option target（Q1 裁决：这是 interpretation bug）
  B2-B1 整个 region 作为输入 → 结构解析器恢复 per-option structure

实验 Harness——不修改生产代码。
"""

import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------- corpus

@dataclass
class CorpusCase:
    case_id: str
    source_path: str
    manifest_path: str
    md_lines: list[str]
    manifest_units: list[dict]
    subject: str


def load_corpus(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> list[CorpusCase]:
    """加载所有 mapping 一致的 corpus cases（读原始源文件）。"""
    manifests = glob.glob(f"{base_dir}/**/*.manifest.json", recursive=True)
    cases = []
    for mp in sorted(manifests):
        with open(mp, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        src_file = manifest.get("source_file", "")
        if src_file and os.path.exists(src_file):
            md_path = src_file
        else:
            md_path = mp.replace(".manifest.json", ".md")
            if not os.path.exists(md_path):
                continue

        with open(md_path, "r", encoding="utf-8") as f:
            md_lines = f.readlines()

        max_line = 0
        for u in manifest.get("units", []):
            for field_name in ("stem_lines", "options_lines", "answer_lines", "explanation_lines"):
                val = u.get(field_name)
                if val and isinstance(val, list) and len(val) == 2:
                    if val[1] and isinstance(val[1], int):
                        max_line = max(max_line, val[1])
        if max_line > len(md_lines):
            continue

        parts = mp.replace("\\", "/").split("/")
        subject = parts[-2] if len(parts) >= 2 else "unknown"
        cases.append(CorpusCase(
            case_id=os.path.basename(mp).replace(".manifest.json", ""),
            source_path=md_path,
            manifest_path=mp,
            md_lines=md_lines,
            manifest_units=manifest.get("units", []),
            subject=subject,
        ))
    return cases


# ---------------------------------------------------------------- option parser

# Option label patterns (ordered by specificity)
# 支持：A. / A．/ A、/ A) / A\.) / （A）/ [A]
_OPTION_LABEL_RE = re.compile(
    r"^[（(\[]?([A-H])[）)\]]?\\?[.、．:：)）]\s*(.*)"
)

# Multi-option single line: "A. xxx B. yyy" 或 "(A) xxx (B) yyy"
# 注意：
#   - 不含 `)` 单独作为 delimiter：避免化学式 Fe(OH)3 中的 H) 被误匹配
#   - 不含 `、`：避免化学元素枚举 H、O、P 中的 H、被误匹配
#   - 不含 `:`：避免 Lewis 结构记号 H: O 中的 H: 被误匹配
#   - `(A)` 格式要求括号完整配对，不会匹配 Fe(OH)3 中的 (OH)
_MULTI_OPTION_RE = re.compile(
    r"(?:([A-H])\\?[.．]|\(([A-H])\))\s*"
)


@dataclass
class ParsedOption:
    label: str
    text: str
    line_number: int  # 1-based line in source file


def parse_options_region(
    md_lines: list[str], start: int, end: int
) -> list[ParsedOption]:
    """从 options region 中解析出 per-option structure。

    策略：
    1. 逐行扫描 region
    2. 跳过空行、分隔线（---）、HTML 标签行
    3. 优先检测单行多选项（A. x B. y C. z D. w）
    4. 回退到单选项标签匹配
    5. 收集多行 option 内容
    """
    options: list[ParsedOption] = []
    current_label: str | None = None
    current_text_parts: list[str] = []
    current_line: int = 0

    for i in range(start, end + 1):
        if i < 1 or i > len(md_lines):
            continue
        line = md_lines[i - 1].rstrip("\n")
        stripped = line.strip()

        # Skip empty lines, separators, and pure HTML lines
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("<") and stripped.endswith(">"):
            continue
        # Strip inline HTML tags for matching (but keep content)
        clean = re.sub(r"<[^>]+>", " ", stripped).strip()
        if not clean:
            continue

        # Priority 1: Multi-option single line (≥2 labels on same line)
        multi_matches = list(_MULTI_OPTION_RE.finditer(clean))
        if len(multi_matches) >= 2:
            # Save previous option
            if current_label:
                options.append(ParsedOption(
                    label=current_label,
                    text=" ".join(current_text_parts).strip(),
                    line_number=current_line,
                ))
                current_label = None
                current_text_parts = []
            # Parse each option on this line
            for j, mm in enumerate(multi_matches):
                label = mm.group(1) or mm.group(2)  # A. format or (A) format
                text_start = mm.end()
                text_end = multi_matches[j + 1].start() if j + 1 < len(multi_matches) else len(clean)
                text = clean[text_start:text_end].strip()
                if text:  # only add if non-empty
                    options.append(ParsedOption(
                        label=label, text=text, line_number=i,
                    ))
            current_line = 0
            continue

        # Priority 2: Single option label match
        m = _OPTION_LABEL_RE.match(clean)
        if m:
            # Save previous option
            if current_label:
                options.append(ParsedOption(
                    label=current_label,
                    text=" ".join(current_text_parts).strip(),
                    line_number=current_line,
                ))
            current_label = m.group(1)
            current_text_parts = [m.group(2).strip()] if m.group(2).strip() else []
            current_line = i
            continue

        # Continuation of current option
        if current_label:
            current_text_parts.append(clean)

    # Save last option
    if current_label:
        options.append(ParsedOption(
            label=current_label,
            text=" ".join(current_text_parts).strip(),
            line_number=current_line,
        ))

    return options


# ---------------------------------------------------------------- B2-B1 experiment

@dataclass
class OptionRegionResult:
    """单个 options region 的三层验证结果。"""
    case_id: str
    unit_id: str
    subject: str
    region: list[int]  # [start, end]
    # Layer 1: Region Binding
    region_valid: bool = False
    region_non_empty: bool = False
    # Layer 2: Structure Extraction
    parsed_options: list[ParsedOption] = field(default_factory=list)
    structure_extracted: bool = False  # ≥2 options parsed
    # Layer 3: Label Sequence
    label_sequence: str = ""
    label_sequence_valid: bool = False  # continuous/increasing
    # Content type classification
    is_html_table: bool = False  # region is primarily HTML table content
    is_image: bool = False  # region is primarily image reference
    # Diagnostics
    raw_lines: list[str] = field(default_factory=list)
    failure_reason: str = ""


def _is_valid_label_sequence(labels: list[str]) -> bool:
    """检查 label 序列是否合理：连续递增（A,B,C,D... 或跳过但递增）。"""
    if len(labels) < 2:
        return False
    # Convert to ordinals
    ords = [ord(l) - ord("A") for l in labels]
    # Check strictly increasing
    for i in range(1, len(ords)):
        if ords[i] <= ords[i - 1]:
            return False
    # Check first is A or reasonable start
    if ords[0] < 0 or ords[0] > 3:  # A-D typical start
        return False
    return True


def run_gate_b2b1(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> dict:
    """执行 Gate B2-B1 Option Region Structure Extraction。"""
    print("=" * 60)
    print("Gate B2-B1: Option Region Structure Extraction")
    print("=" * 60)

    cases = load_corpus(base_dir)
    print(f"\nCorpus: {len(cases)} cases (mapping-consistent)")

    results: list[OptionRegionResult] = []

    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            opt = mu.get("options_lines")
            if not opt or not isinstance(opt, list) or len(opt) != 2:
                continue
            if not opt[0] or not opt[1]:
                continue

            start, end = opt[0], opt[1]
            result = OptionRegionResult(
                case_id=case.case_id, unit_id=uid,
                subject=case.subject, region=[start, end],
            )

            # Layer 1: Region Binding
            if start < 1 or end > len(case.md_lines) or start > end:
                result.failure_reason = f"range_invalid: [{start},{end}] vs [1,{len(case.md_lines)}]"
                results.append(result)
                continue
            result.region_valid = True

            raw = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
            result.raw_lines = raw
            non_empty = [l for l in raw if l.strip() and l.strip() != "---"]
            if not non_empty:
                result.failure_reason = "region_empty"
                results.append(result)
                continue
            result.region_non_empty = True

            # Classify content type
            joined = "\n".join(raw)
            result.is_html_table = "<table" in joined.lower()
            result.is_image = "<img" in joined.lower() or "<div" in joined.lower()

            # Layer 2: Structure Extraction (skip HTML table / image-only regions)
            if result.is_html_table or result.is_image:
                result.failure_reason = "html_table_or_image: B2-B4 territory"
                results.append(result)
                continue

            parsed = parse_options_region(case.md_lines, start, end)
            result.parsed_options = parsed
            result.structure_extracted = len(parsed) >= 2

            # Layer 3: Label Sequence
            labels = [p.label for p in parsed]
            result.label_sequence = ",".join(labels)
            result.label_sequence_valid = _is_valid_label_sequence(labels)

            if not result.structure_extracted:
                result.failure_reason = f"structure_extraction_failed: {len(parsed)} options parsed"

            results.append(result)

    # Aggregate
    total = len(results)
    region_valid = sum(1 for r in results if r.region_valid)
    region_non_empty = sum(1 for r in results if r.region_non_empty)
    structure_extracted = sum(1 for r in results if r.structure_extracted)
    label_valid = sum(1 for r in results if r.label_sequence_valid)

    # By subject
    by_subject = {}
    for r in results:
        s = r.subject
        if s not in by_subject:
            by_subject[s] = {"total": 0, "structure_ok": 0, "label_ok": 0}
        by_subject[s]["total"] += 1
        if r.structure_extracted:
            by_subject[s]["structure_ok"] += 1
        if r.label_sequence_valid:
            by_subject[s]["label_ok"] += 1

    # Failure reasons
    failure_reasons = {}
    for r in results:
        if r.failure_reason:
            reason_type = r.failure_reason.split(":")[0]
            failure_reasons[reason_type] = failure_reasons.get(reason_type, 0) + 1

    # Option count distribution
    option_count_dist = {}
    for r in results:
        if r.structure_extracted:
            n = len(r.parsed_options)
            option_count_dist[n] = option_count_dist.get(n, 0) + 1

    # Sample failures (separate HTML from non-HTML)
    html_failures = [r for r in results if r.is_html_table or r.is_image][:5]
    structure_failures = [r for r in results
                          if r.region_non_empty and not r.structure_extracted
                          and not r.is_html_table and not r.is_image][:8]
    label_failures = [r for r in results if r.structure_extracted and not r.label_sequence_valid][:8]

    comparison = {
        "total_option_regions": total,
        "region_valid": region_valid,
        "region_non_empty": region_non_empty,
        "structure_extracted": structure_extracted,
        "label_sequence_valid": label_valid,
        "region_valid_rate": region_valid / total if total else 0,
        "structure_extracted_rate": structure_extracted / total if total else 0,
        "label_sequence_valid_rate": label_valid / total if total else 0,
        "by_subject": by_subject,
        "option_count_distribution": option_count_dist,
        "failure_reasons": failure_reasons,
    }

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nTotal option regions: {total}")
    print(f"Region valid: {region_valid} ({region_valid/total:.1%})")
    print(f"Region non-empty: {region_non_empty} ({region_non_empty/total:.1%})")
    print(f"Structure extracted (≥2 options): {structure_extracted} ({structure_extracted/total:.1%})")
    print(f"Label sequence valid: {label_valid} ({label_valid/total:.1%})")

    print(f"\nOption count distribution:")
    for n in sorted(option_count_dist.keys()):
        print(f"  {n} options: {option_count_dist[n]} regions")

    print(f"\nBy subject:")
    for subj, stats in sorted(by_subject.items()):
        print(f"  {subj}: total={stats['total']}, "
              f"structure_ok={stats['structure_ok']}, "
              f"label_ok={stats['label_ok']}")

    print(f"\nFailure reasons:")
    for reason, count in sorted(failure_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")

    print(f"\nSample HTML table/image regions (B2-B4 territory):")
    for r in html_failures:
        print(f"  {r.case_id}/{r.unit_id}: region {r.region}")
        for line in r.raw_lines[:2]:
            print(f"    | {line[:80]}")

    print(f"\nSample non-HTML structure extraction failures:")
    for r in structure_failures:
        print(f"  {r.case_id}/{r.unit_id}: region {r.region}, "
              f"{len(r.parsed_options)} options parsed")
        for line in r.raw_lines[:4]:
            print(f"    | {line[:80]}")

    print(f"\nSample label sequence failures:")
    for r in label_failures:
        print(f"  {r.case_id}/{r.unit_id}: labels=[{r.label_sequence}]")
        for p in r.parsed_options[:5]:
            print(f"    {p.label}. {p.text[:60]}")

    return {
        "comparison": comparison,
        "all_results": results,
        "cases": cases,
    }


if __name__ == "__main__":
    result = run_gate_b2b1()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_b2b1_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result["comparison"], f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_path}")
