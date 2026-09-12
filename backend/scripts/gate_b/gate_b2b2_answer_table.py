"""Gate B2-B2: Shared Answer Table — Question-Specific Answer Extraction.

验证：给定 answer_lines Region，能否从中提取出属于当前 Question 的答案。

Q2 裁决：共享答案表（`1-5: BBACB; 6-10: DBBBA`）的 Source Region 不等于
Question-level answer evidence。需要从共享 Region 中确定性定位本题答案。

四层验证：
  Layer 1 — Region Binding:       answer_lines region 存在且非空
  Layer 2 — Answer Type Detection: 识别答案格式（single/table/numbered/fill-in/html）
  Layer 3 — Question Extraction:   从 region 中提取本题答案
  Layer 4 — Answer Validity:       提取的答案格式合理（A-H 字母 / 数字 / 文本）

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


# ---------------------------------------------------------------- answer type detection

_ANSWER_PATTERNS = {
    "range_table": re.compile(r"(\d+)\s*[-–~～]{1,}\s*(\d+)\s*[:：]?\s*([A-H]+)"),
    "numbered": re.compile(r"^(\d+)\\?\s*[.、．:：]?\s*\(?\d*分?\)?\s*([A-H])\s*$"),
    "single_letter": re.compile(r"^([A-H])$"),
    "multi_letter": re.compile(r"^([A-H][,、\s]*)+$"),
    "fill_in": re.compile(r"^(\d+)\s*[.、．]?\s+(.+)$"),
    "marked": re.compile(r"【答案】\s*(.+)"),
    "html": re.compile(r"<table", re.IGNORECASE),
    "sub_question": re.compile(r"[（(]\d+[）)]"),  # （1）（2）(3)
    # 连写编号答案: "1\. C2\. C3\. A4\. B" 或 "1C, 2D, 3B"
    "concat_numbered": re.compile(r"\d+\\?[.、．:：]?\s*[A-H](?:\s*[,，]?\s*\d+\\?[.、．:：]?\s*[A-H])+"),
    # 连写填空: "21.Grady 22.61295 23.white"
    "concat_fill_in": re.compile(r"\d+\\?[.、．]?\s+\S+(?:\s+\d+\\?[.、．]?\s+\S+)+"),
    # checkbox 答案: "☑答案 D" / "☐答案 C" / "☑答案B"
    "checkbox": re.compile(r"[☑☐✓]\s*答案\s*([A-H])"),
    # 故选: "故选：D." / "故选 C"
    "gu_xuan": re.compile(r"故选\s*[:：]?\s*\$?\s*([A-H])\s*\$?\s*[.。]?"),
    # 故答案为: "故答案为：3；..."
    "gu_da_an": re.compile(r"故答案为\s*[:：]?\s*(.+)"),
}


@dataclass
class AnswerRegionInfo:
    case_id: str
    unit_id: str
    question_number: int | None
    region: list[int]
    raw_lines: list[str]
    answer_type: str = ""
    shared: bool = False
    shared_with: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    info: AnswerRegionInfo
    region_valid: bool = False
    region_non_empty: bool = False
    type_detected: bool = False
    extracted_answer: str = ""
    extraction_success: bool = False
    answer_valid: bool = False
    failure_reason: str = ""


def detect_answer_type(raw_lines: list[str]) -> str:
    joined = "\n".join(raw_lines)
    stripped = joined.strip()
    if not stripped:
        return "unknown"
    if _ANSWER_PATTERNS["html"].search(stripped):
        return "html"
    if _ANSWER_PATTERNS["checkbox"].search(stripped):
        return "checkbox"
    if _ANSWER_PATTERNS["gu_xuan"].search(stripped):
        return "gu_xuan"
    if _ANSWER_PATTERNS["gu_da_an"].search(stripped):
        return "gu_da_an"
    if _ANSWER_PATTERNS["marked"].search(stripped):
        return "marked"
    if _ANSWER_PATTERNS["range_table"].search(stripped):
        return "range_table"
    non_empty = [l.strip() for l in raw_lines if l.strip()]
    if len(non_empty) == 1 and _ANSWER_PATTERNS["single_letter"].match(non_empty[0]):
        return "single_letter"
    if all(_ANSWER_PATTERNS["numbered"].match(l) for l in non_empty):
        return "numbered"
    if all(_ANSWER_PATTERNS["multi_letter"].match(l) for l in non_empty):
        return "multi_letter"
    if all(_ANSWER_PATTERNS["fill_in"].match(l) for l in non_empty):
        return "fill_in"
    if _ANSWER_PATTERNS["concat_numbered"].search(stripped):
        return "concat_numbered"
    if _ANSWER_PATTERNS["concat_fill_in"].search(stripped):
        return "concat_fill_in"
    if _ANSWER_PATTERNS["sub_question"].search(stripped):
        return "sub_question"
    return "unknown"


def extract_question_answer(
    raw_lines: list[str], question_number: int | None, answer_type: str
) -> str:
    if question_number is None:
        return ""
    joined = "\n".join(raw_lines)
    stripped = joined.strip()
    if answer_type == "range_table":
        return _extract_from_range_table(stripped, question_number)
    elif answer_type == "numbered":
        return _extract_from_numbered(raw_lines, question_number)
    elif answer_type == "single_letter":
        return stripped
    elif answer_type == "multi_letter":
        return _extract_from_multi_letter(stripped, question_number)
    elif answer_type == "marked":
        m = _ANSWER_PATTERNS["marked"].search(stripped)
        if m:
            content = m.group(1).strip()
            if _ANSWER_PATTERNS["range_table"].search(content):
                return _extract_from_range_table(content, question_number)
            return content
        return ""
    elif answer_type == "fill_in":
        return _extract_from_fill_in(raw_lines, question_number)
    elif answer_type == "concat_numbered":
        return _extract_from_concat_numbered(stripped, question_number)
    elif answer_type == "concat_fill_in":
        return _extract_from_concat_fill_in(stripped, question_number)
    elif answer_type == "checkbox":
        m = _ANSWER_PATTERNS["checkbox"].search(stripped)
        return m.group(1) if m else ""
    elif answer_type == "gu_xuan":
        m = _ANSWER_PATTERNS["gu_xuan"].search(stripped)
        return m.group(1) if m else ""
    elif answer_type == "gu_da_an":
        m = _ANSWER_PATTERNS["gu_da_an"].search(stripped)
        return m.group(1).strip() if m else ""
    return ""


def _extract_from_concat_numbered(text: str, qn: int) -> str:
    """从连写编号答案提取本题答案。

    格式: "1\\. C2\\. C3\\. A4\\. B" 或 "1C, 2D, 3B"
    """
    # Pattern: number + optional escape dot + letter
    for m in re.finditer(r"(\d+)\\?[.、．:：]?\s*([A-H])", text):
        if int(m.group(1)) == qn:
            return m.group(2)
    return ""


def _extract_from_concat_fill_in(text: str, qn: int) -> str:
    """从连写填空答案提取本题答案。

    格式: "21.Grady 22.61295 23.white"
    """
    for m in re.finditer(r"(\d+)\\?[.、．]?\s+(\S+)", text):
        if int(m.group(1)) == qn:
            return m.group(2)
    return ""


def _extract_from_range_table(text: str, qn: int) -> str:
    for m in _ANSWER_PATTERNS["range_table"].finditer(text):
        start, end, answers = int(m.group(1)), int(m.group(2)), m.group(3)
        if start <= qn <= end:
            idx = qn - start
            if idx < len(answers):
                return answers[idx]
    return ""


def _extract_from_numbered(raw_lines: list[str], qn: int) -> str:
    for line in raw_lines:
        line = line.strip()
        m = _ANSWER_PATTERNS["numbered"].match(line)
        if m and int(m.group(1)) == qn:
            return m.group(2)
    return ""


def _extract_from_multi_letter(text: str, qn: int) -> str:
    letters = re.sub(r"[,、\s]", "", text)
    idx = qn - 1
    if 0 <= idx < len(letters):
        return letters[idx]
    return ""


def _extract_from_fill_in(raw_lines: list[str], qn: int) -> str:
    for line in raw_lines:
        line = line.strip()
        m = _ANSWER_PATTERNS["fill_in"].match(line)
        if m and int(m.group(1)) == qn:
            return m.group(2).strip()
    return ""


# ---------------------------------------------------------------- B2-B2 experiment

def _extract_question_number(unit_id: str, manifest_unit: dict) -> int | None:
    """从 unit_id 或 manifest_unit 中提取题号。

    支持格式：
      Q1, Q12 — 标准题号
      1, 12 — 纯数字
      U6-7, U21-24 — unit range（取起始题号）
      U51, N1 — unit/section 编号
      1-5 — range（取起始）
    """
    qn = manifest_unit.get("question_number")
    if qn is not None:
        try:
            return int(qn)
        except (ValueError, TypeError):
            pass

    # Q1, Q12
    m = re.search(r"Q(\d+)", unit_id)
    if m:
        return int(m.group(1))
    # U6-7, U21-24 — take start of range
    m = re.search(r"U(\d+)\s*[-–~]", unit_id)
    if m:
        return int(m.group(1))
    # U51, N1, N2
    m = re.search(r"[UN](\d+)$", unit_id)
    if m:
        return int(m.group(1))
    # Pure number or range: "1", "12", "1-5"
    m = re.match(r"^(\d+)(?:\s*[-–~]\s*\d+)?$", unit_id)
    if m:
        return int(m.group(1))
    return None


def _validate_answer(answer: str, answer_type: str) -> bool:
    if not answer:
        return False
    if answer_type in ("single_letter", "multi_letter", "range_table", "numbered",
                        "concat_numbered", "checkbox", "gu_xuan"):
        return bool(re.match(r"^[A-H]$", answer))
    return len(answer) > 0


def run_gate_b2b2(base_dir: str = "D:/Project/Papers/Ocr-markdown") -> dict:
    print("=" * 60)
    print("Gate B2-B2: Shared Answer Table — Question-Specific Extraction")
    print("=" * 60)

    cases = load_corpus(base_dir)
    print(f"\nCorpus: {len(cases)} cases")

    region_map: dict[str, list[tuple[str, str, int | None]]] = {}
    all_items: list[tuple[CorpusCase, dict, int | None]] = []

    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            ans = mu.get("answer_lines")
            if not ans or not isinstance(ans, list) or len(ans) != 2 or not ans[0] or not ans[1]:
                continue
            qn = _extract_question_number(uid, mu)
            key = f"{case.case_id}:{ans[0]}-{ans[1]}"
            if key not in region_map:
                region_map[key] = []
            region_map[key].append((case.case_id, uid, qn))
            all_items.append((case, mu, qn))

    print(f"\nTotal answer targets: {len(all_items)}")
    print(f"Unique answer regions: {len(region_map)}")

    shared_regions = {k: v for k, v in region_map.items() if len(v) > 1}
    print(f"Shared regions (≥2 units): {len(shared_regions)}")
    print(f"  Total units in shared regions: {sum(len(v) for v in shared_regions.values())}")

    results: list[ExtractionResult] = []

    for case, mu, qn in all_items:
        uid = mu.get("unit_id", "?")
        ans = mu.get("answer_lines")
        start, end = ans[0], ans[1]
        key = f"{case.case_id}:{start}-{end}"
        shared_units = region_map.get(key, [])
        is_shared = len(shared_units) > 1

        info = AnswerRegionInfo(
            case_id=case.case_id, unit_id=uid, question_number=qn,
            region=[start, end],
            raw_lines=[case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)
                       if 1 <= i <= len(case.md_lines)],
            shared=is_shared,
            shared_with=[u for _, u, _ in shared_units if u != uid],
        )

        result = ExtractionResult(info=info)

        if start < 1 or end > len(case.md_lines) or start > end:
            result.failure_reason = f"range_invalid: [{start},{end}] vs [1,{len(case.md_lines)}]"
            results.append(result)
            continue
        result.region_valid = True

        non_empty = [l for l in info.raw_lines if l.strip()]
        if not non_empty:
            result.failure_reason = "region_empty"
            results.append(result)
            continue
        result.region_non_empty = True

        info.answer_type = detect_answer_type(info.raw_lines)
        result.type_detected = info.answer_type != "unknown"

        extracted = extract_question_answer(info.raw_lines, qn, info.answer_type)
        result.extracted_answer = extracted
        result.extraction_success = bool(extracted)

        if extracted:
            result.answer_valid = _validate_answer(extracted, info.answer_type)

        if not result.extraction_success:
            result.failure_reason = f"extraction_failed: type={info.answer_type}, qn={qn}"

        results.append(result)

    # ---- Aggregate ----
    total = len(results)
    region_valid = sum(1 for r in results if r.region_valid)
    region_non_empty = sum(1 for r in results if r.region_non_empty)
    type_detected = sum(1 for r in results if r.type_detected)
    extraction_success = sum(1 for r in results if r.extraction_success)
    answer_valid = sum(1 for r in results if r.answer_valid)

    by_type = {}
    for r in results:
        t = r.info.answer_type or "unknown"
        if t not in by_type:
            by_type[t] = {"total": 0, "extracted": 0, "valid": 0}
        by_type[t]["total"] += 1
        if r.extraction_success:
            by_type[t]["extracted"] += 1
        if r.answer_valid:
            by_type[t]["valid"] += 1

    shared_results = [r for r in results if r.info.shared]
    non_shared_results = [r for r in results if not r.info.shared]
    shared_extracted = sum(1 for r in shared_results if r.extraction_success)
    non_shared_extracted = sum(1 for r in non_shared_results if r.extraction_success)

    failure_reasons = {}
    for r in results:
        if r.failure_reason:
            reason_type = r.failure_reason.split(":")[0]
            failure_reasons[reason_type] = failure_reasons.get(reason_type, 0) + 1

    extraction_failures = [r for r in results if r.region_non_empty and not r.extraction_success][:8]

    comparison = {
        "total_answer_targets": total,
        "unique_regions": len(region_map),
        "shared_regions": len(shared_regions),
        "region_valid": region_valid,
        "region_non_empty": region_non_empty,
        "type_detected": type_detected,
        "extraction_success": extraction_success,
        "answer_valid": answer_valid,
        "extraction_rate": extraction_success / total if total else 0,
        "valid_rate": answer_valid / total if total else 0,
        "by_type": by_type,
        "shared_extraction_rate": shared_extracted / len(shared_results) if shared_results else 0,
        "non_shared_extraction_rate": non_shared_extracted / len(non_shared_results) if non_shared_results else 0,
        "failure_reasons": failure_reasons,
    }

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nTotal answer targets: {total}")
    print(f"Region valid: {region_valid} ({region_valid/total:.1%})")
    print(f"Region non-empty: {region_non_empty} ({region_non_empty/total:.1%})")
    print(f"Type detected: {type_detected} ({type_detected/total:.1%})")
    print(f"Extraction success: {extraction_success} ({extraction_success/total:.1%})")
    print(f"Answer valid: {answer_valid} ({answer_valid/total:.1%})")

    print(f"\nBy answer type:")
    for t, stats in sorted(by_type.items(), key=lambda x: -x[1]["total"]):
        print(f"  {t}: total={stats['total']}, "
              f"extracted={stats['extracted']}, "
              f"valid={stats['valid']}")

    print(f"\nShared vs non-shared:")
    if shared_results:
        print(f"  Shared ({len(shared_results)} targets): "
              f"extracted={shared_extracted} ({shared_extracted/len(shared_results):.1%})")
    else:
        print(f"  Shared: none")
    if non_shared_results:
        print(f"  Non-shared ({len(non_shared_results)} targets): "
              f"extracted={non_shared_extracted} ({non_shared_extracted/len(non_shared_results):.1%})")
    else:
        print(f"  Non-shared: none")

    print(f"\nFailure reasons:")
    for reason, count in sorted(failure_reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")

    print(f"\nSample extraction failures:")
    for r in extraction_failures:
        print(f"  {r.info.case_id}/{r.info.unit_id}: type={r.info.answer_type}, "
              f"qn={r.info.question_number}, region={r.info.region}, shared={r.info.shared}")
        for line in r.info.raw_lines[:3]:
            print(f"    | {line[:80]}")

    return {
        "comparison": comparison,
        "all_results": results,
        "cases": cases,
    }


if __name__ == "__main__":
    result = run_gate_b2b2()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_b2b2_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result["comparison"], f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_path}")
