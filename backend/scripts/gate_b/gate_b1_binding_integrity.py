"""Gate B1: Binding Integrity Validation.

验证 Path B line_refs 是否指向合法、非空、结构匹配的 Source Evidence。

四层验证：
  Level 1 — Range Validity:     start/end 在 SourceLineView 范围内
  Level 2 — Content Validity:   resolved_text 非空
  Level 3 — Role Validity:      内容结构匹配声明 role（stem/options/answer/explanation）
  Level 4 — Semantic Validity:  内容符合 unit 语义（需独立证据，不由简单规则冒充）

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
    """加载所有 mapping 一致的 corpus cases。

    关键修复：读取 manifest['source_file'] 指向的原始源文件，
    而非同目录下的切片展示视图（compile_slices 产出，含区域标记，行号不同）。
    """
    manifests = glob.glob(f"{base_dir}/**/*.manifest.json", recursive=True)
    cases = []
    for mp in sorted(manifests):
        with open(mp, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # 优先使用 manifest 声明的原始源文件
        src_file = manifest.get("source_file", "")
        if src_file and os.path.exists(src_file):
            md_path = src_file
        else:
            # 回退：同目录 .md（可能是切片视图，行号可能错位）
            md_path = mp.replace(".manifest.json", ".md")
            if not os.path.exists(md_path):
                continue

        with open(md_path, "r", encoding="utf-8") as f:
            md_lines = f.readlines()

        # Mapping audit: skip if any line_ref exceeds md_lines
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


# ---------------------------------------------------------------- role targets

@dataclass
class RoleTarget:
    """统一的 Content Role Target：(case_id, unit_id, role, label)。"""
    case_id: str
    unit_id: str
    role: str  # stem | option | answer | explanation
    label: str | None = None  # option label (A/B/C/...)
    line_range: list[int] | None = None  # [start, end] from manifest


def build_role_targets(case: CorpusCase) -> list[RoleTarget]:
    """从 manifest units 构造统一的 Role Target 列表。

    每个 (unit_id, role) 是一个对比单位。
    Options 按 manifest 的 options_lines 范围推导实际行数，不假设 ABCD。
    """
    targets = []
    for mu in case.manifest_units:
        uid = mu.get("unit_id", "?")

        # stem
        stem = mu.get("stem_lines")
        if stem and isinstance(stem, list) and len(stem) == 2 and stem[0] and stem[1]:
            targets.append(RoleTarget(
                case_id=case.case_id, unit_id=uid, role="stem",
                line_range=stem,
            ))

        # options: 从 options_lines 范围推导实际行数
        opt = mu.get("options_lines")
        if opt and isinstance(opt, list) and len(opt) == 2 and opt[0] and opt[1]:
            start, end = opt[0], opt[1]
            n_options = end - start + 1
            labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            for i in range(min(n_options, len(labels))):
                targets.append(RoleTarget(
                    case_id=case.case_id, unit_id=uid, role="option",
                    label=labels[i],
                    line_range=[start + i, start + i],
                ))

        # answer
        ans = mu.get("answer_lines")
        if ans and isinstance(ans, list) and len(ans) == 2 and ans[0] and ans[1]:
            targets.append(RoleTarget(
                case_id=case.case_id, unit_id=uid, role="answer",
                line_range=ans,
            ))

        # explanation
        exp = mu.get("explanation_lines")
        if exp and isinstance(exp, list) and len(exp) == 2 and exp[0] and exp[1]:
            targets.append(RoleTarget(
                case_id=case.case_id, unit_id=uid, role="explanation",
                line_range=exp,
            ))

    return targets


# ---------------------------------------------------------------- binding integrity

@dataclass
class BindingIntegrityResult:
    """单个 RoleTarget 的四层验证结果。"""
    target: RoleTarget
    range_valid: bool = False
    content_valid: bool = False
    role_valid: bool = False
    semantic_valid: bool | None = None  # None = not evaluated
    resolved_text: str = ""
    failure_reason: str = ""


# Role-specific content patterns for Level 3 (Role Validity)
# 修复记录（2026-09-11 对抗性验证）：
#   - stem: 支持反斜杠转义点号 `1\.`（OCR markdown 常见）
#   - option: 支持反斜杠转义点号 `A\.`；单行多选项 `A. x B. y`
#   - answer: 支持答案表 `1-5: BBACB`、区间连写、`【答案】` 标记
#   - explanation: 用 search 而非 match，支持 `## 【解析】` 等 markdown 前缀
_ROLE_PATTERNS = {
    "stem": [
        r"^\d+\\?[.、．]",  # question number (支持转义点号)
        r"^\(",  # sub-question parenthesis
        r"^<div",  # HTML image
        r"^<table",  # HTML table
        r"^#",  # markdown heading
        r"^【",  # bracket marker
    ],
    "option": [
        r"^[A-H]\\?[.、．)]",  # option label (支持转义点号)
        r"^[A-H]\\?[.、．)].*[A-H]\\?[.、．)]",  # multi-option single line
        r"^---$",  # markdown horizontal rule (常见于选项间分隔)
    ],
    "answer": [
        r"^[A-H]$",  # single letter
        r"^[A-H][,、]",  # multiple letters
        r"^\d+\\?[.、．]",  # numbered answer
        r"答案",  # contains 答案
        r"^\d+[-–]\d+[:：\s]",  # range answer table: 1-5: BBACB 或 1-5 BBAAC
        r"^[A-H]{2,}",  # concatenated answers: BBACB
    ],
    "explanation": [
        r"解析",  # contains 解析 (search, not match)
        r"详解",  # contains 详解
        r"【解答】",  # bracket marker
        r"【分析】",  # bracket marker
        r"【点评】",  # bracket marker
        r"因为",  # contains 因为
        r"所以",  # contains 所以
        r"故选",  # contains 故选
    ],
}


def _match_role(role: str, text: str) -> bool:
    """检查文本是否匹配声明的 role 结构。

    stem/option/option 用 re.match（从头匹配）；
    explanation 用 re.search（允许 markdown 前缀如 `## 【解析】`）。
    """
    patterns = _ROLE_PATTERNS.get(role, [])
    if not patterns:
        return True
    if role == "explanation":
        return any(re.search(p, text) for p in patterns)
    return any(re.match(p, text) for p in patterns)


def validate_binding_integrity(
    target: RoleTarget, md_lines: list[str]
) -> BindingIntegrityResult:
    """对单个 RoleTarget 执行四层验证。"""
    result = BindingIntegrityResult(target=target)

    if not target.line_range or len(target.line_range) != 2:
        result.failure_reason = "no_line_range"
        return result

    start, end = target.line_range
    if not start or not end or not isinstance(start, int) or not isinstance(end, int):
        result.failure_reason = "invalid_line_range"
        return result

    # Level 1: Range Validity
    if start < 1 or end > len(md_lines) or start > end:
        result.failure_reason = f"range_invalid: [{start},{end}] vs [1,{len(md_lines)}]"
        return result
    result.range_valid = True

    # Level 2: Content Validity
    texts = [md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
    resolved_text = "\n".join(texts)
    non_empty_lines = [t for t in texts if t.strip()]
    if not non_empty_lines:
        result.failure_reason = "content_empty"
        return result
    result.content_valid = True
    result.resolved_text = resolved_text

    # Level 3: Role Validity
    first_non_empty = non_empty_lines[0].strip()
    if not _match_role(target.role, first_non_empty):
        result.failure_reason = f"role_mismatch: '{first_non_empty[:50]}' doesn't match {target.role} pattern"
        return result
    result.role_valid = True

    # Level 4: Semantic Validity — 需独立证据，不由简单规则冒充
    result.semantic_valid = None  # not evaluated

    return result


# ---------------------------------------------------------------- experiment

def run_gate_b1(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> dict:
    """执行 Gate B1 Binding Integrity 验证。"""
    print("=" * 60)
    print("Gate B1: Binding Integrity Validation")
    print("=" * 60)

    cases = load_corpus(base_dir)
    print(f"\nCorpus: {len(cases)} cases (mapping-consistent)")

    all_results: list[BindingIntegrityResult] = []

    for i, case in enumerate(cases):
        targets = build_role_targets(case)
        for target in targets:
            result = validate_binding_integrity(target, case.md_lines)
            all_results.append(result)

        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(cases)} cases...")

    # Aggregate metrics
    total = len(all_results)
    range_valid = sum(1 for r in all_results if r.range_valid)
    content_valid = sum(1 for r in all_results if r.content_valid)
    role_valid = sum(1 for r in all_results if r.role_valid)

    # By role breakdown
    by_role = {}
    for r in all_results:
        role = r.target.role
        if role not in by_role:
            by_role[role] = {"total": 0, "range_valid": 0, "content_valid": 0, "role_valid": 0}
        by_role[role]["total"] += 1
        if r.range_valid:
            by_role[role]["range_valid"] += 1
        if r.content_valid:
            by_role[role]["content_valid"] += 1
        if r.role_valid:
            by_role[role]["role_valid"] += 1

    # Failure reasons
    failure_reasons = {}
    for r in all_results:
        if r.failure_reason:
            reason_type = r.failure_reason.split(":")[0]
            failure_reasons[reason_type] = failure_reasons.get(reason_type, 0) + 1

    # Sample failures for inspection
    empty_spans = [r for r in all_results if r.range_valid and not r.content_valid][:5]
    role_mismatches = [r for r in all_results if r.content_valid and not r.role_valid][:5]

    comparison = {
        "total_targets": total,
        "range_valid": range_valid,
        "content_valid": content_valid,
        "role_valid": role_valid,
        "range_valid_rate": range_valid / total if total else 0,
        "content_valid_rate": content_valid / total if total else 0,
        "role_valid_rate": role_valid / total if total else 0,
        "by_role": by_role,
        "failure_reasons": failure_reasons,
    }

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nTotal role targets: {total}")
    print(f"Range valid: {range_valid} ({range_valid/total:.1%})")
    print(f"Content valid: {content_valid} ({content_valid/total:.1%})")
    print(f"Role valid: {role_valid} ({role_valid/total:.1%})")

    print(f"\nBy role:")
    for role, stats in sorted(by_role.items()):
        print(f"  {role}: total={stats['total']}, "
              f"range={stats['range_valid']}, "
              f"content={stats['content_valid']}, "
              f"role={stats['role_valid']}")

    print(f"\nFailure reasons:")
    for reason, count in sorted(failure_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")

    print(f"\nSample empty spans (range_valid but not content_valid):")
    for r in empty_spans:
        print(f"  {r.target.case_id}/{r.target.unit_id}/{r.target.role}: "
              f"lines {r.target.line_range} → empty")

    print(f"\nSample role mismatches (content_valid but not role_valid):")
    for r in role_mismatches:
        print(f"  {r.target.case_id}/{r.target.unit_id}/{r.target.role}: "
              f"'{r.resolved_text[:50]}'")

    return {
        "comparison": comparison,
        "all_results": all_results,
        "cases": cases,
    }


if __name__ == "__main__":
    result = run_gate_b1()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_b1_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result["comparison"], f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_path}")
