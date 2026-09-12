"""B2-B2 诊断：unknown 类型和 range_table 失败的深入分析。"""

import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gate_b2b2_answer_table import (
    load_corpus,
    detect_answer_type,
    extract_question_answer,
    _extract_question_number,
    _ANSWER_PATTERNS,
)


def diagnose_unknown_types(cases):
    """诊断 unknown 类型的具体格式。"""
    unknown_samples = []
    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            ans = mu.get("answer_lines")
            if not ans or not isinstance(ans, list) or len(ans) != 2 or not ans[0] or not ans[1]:
                continue
            start, end = ans[0], ans[1]
            if start < 1 or end > len(case.md_lines):
                continue
            raw = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
            non_empty = [l for l in raw if l.strip()]
            if not non_empty:
                continue
            atype = detect_answer_type(raw)
            if atype == "unknown":
                unknown_samples.append({
                    "case_id": case.case_id,
                    "unit_id": uid,
                    "region": [start, end],
                    "raw_lines": raw[:6],
                    "line_count": len(raw),
                    "non_empty_count": len(non_empty),
                })

    print(f"\nTotal unknown type: {len(unknown_samples)}")

    categories = Counter()
    for s in unknown_samples:
        joined = "\n".join(s["raw_lines"])
        if re.search(r"（\d+）", joined):
            categories["sub_question_cn"] += 1
        elif re.search(r"\(\d+\)", joined):
            categories["sub_question_en"] += 1
        elif re.search(r"【答案】", joined):
            categories["marked_but_failed"] += 1
        elif re.search(r"<table", joined, re.IGNORECASE):
            categories["html_but_not_detected"] += 1
        elif re.search(r"\d+\s*[-–~]\s*\d+", joined):
            categories["range_but_failed"] += 1
        elif len(s["raw_lines"]) <= 2:
            categories["short_single_line"] += 1
        else:
            categories["other_multi_line"] += 1

    print(f"\nUnknown type categories:")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}")

    shown = set()
    for s in unknown_samples:
        joined = "\n".join(s["raw_lines"])
        if re.search(r"（\d+）", joined):
            cat = "sub_question_cn"
        elif re.search(r"\(\d+\)", joined):
            cat = "sub_question_en"
        elif re.search(r"【答案】", joined):
            cat = "marked_but_failed"
        elif re.search(r"<table", joined, re.IGNORECASE):
            cat = "html_but_not_detected"
        elif re.search(r"\d+\s*[-–~]\s*\d+", joined):
            cat = "range_but_failed"
        elif len(s["raw_lines"]) <= 2:
            cat = "short_single_line"
        else:
            cat = "other_multi_line"

        if cat not in shown:
            shown.add(cat)
            print(f"\n  [{cat}] {s['case_id']}/{s['unit_id']} (region {s['region']}, {s['line_count']} lines)")
            for line in s["raw_lines"][:4]:
                print(f"    | {line[:90]}")

    return unknown_samples


def diagnose_range_table_failures(cases):
    """诊断 range_table 类型中提取失败的 case。"""
    failures = []
    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            ans = mu.get("answer_lines")
            if not ans or not isinstance(ans, list) or len(ans) != 2 or not ans[0] or not ans[1]:
                continue
            start, end = ans[0], ans[1]
            if start < 1 or end > len(case.md_lines):
                continue
            raw = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
            atype = detect_answer_type(raw)
            if atype != "range_table":
                continue
            qn = _extract_question_number(uid, mu)
            extracted = extract_question_answer(raw, qn, atype)
            if not extracted:
                failures.append({
                    "case_id": case.case_id,
                    "unit_id": uid,
                    "question_number": qn,
                    "region": [start, end],
                    "raw_lines": raw[:4],
                })

    print(f"\n{'='*60}")
    print(f"Range table extraction failures: {len(failures)}")
    print(f"{'='*60}")

    for f in failures[:15]:
        print(f"\n  {f['case_id']}/{f['unit_id']}: qn={f['question_number']}, region={f['region']}")
        for line in f["raw_lines"]:
            print(f"    | {line[:90]}")

    categories = Counter()
    for f in failures:
        if f["question_number"] is None:
            categories["qn_not_extractable"] += 1
        else:
            joined = "\n".join(f["raw_lines"])
            ranges = _ANSWER_PATTERNS["range_table"].finditer(joined)
            found = False
            for m in ranges:
                s, e = int(m.group(1)), int(m.group(2))
                if s <= f["question_number"] <= e:
                    found = True
                    break
            if found:
                categories["qn_in_range_but_extraction_failed"] += 1
            else:
                categories["qn_outside_all_ranges"] += 1

    print(f"\n  Failure categories:")
    for cat, count in categories.most_common():
        print(f"    {cat}: {count}")

    return failures


def diagnose_marked_failures(cases):
    """诊断 marked 类型中提取失败的 case。"""
    failures = []
    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            ans = mu.get("answer_lines")
            if not ans or not isinstance(ans, list) or len(ans) != 2 or not ans[0] or not ans[1]:
                continue
            start, end = ans[0], ans[1]
            if start < 1 or end > len(case.md_lines):
                continue
            raw = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)]
            atype = detect_answer_type(raw)
            if atype != "marked":
                continue
            qn = _extract_question_number(uid, mu)
            extracted = extract_question_answer(raw, qn, atype)
            if not extracted:
                failures.append({
                    "case_id": case.case_id,
                    "unit_id": uid,
                    "question_number": qn,
                    "region": [start, end],
                    "raw_lines": raw[:4],
                })

    print(f"\n{'='*60}")
    print(f"Marked type extraction failures: {len(failures)}")
    print(f"{'='*60}")

    for f in failures[:10]:
        print(f"\n  {f['case_id']}/{f['unit_id']}: qn={f['question_number']}, region={f['region']}")
        for line in f["raw_lines"]:
            print(f"    | {line[:90]}")

    return failures


def main():
    base_dir = "D:/Project/Papers/Ocr-markdown"
    cases = load_corpus(base_dir)
    print(f"Corpus: {len(cases)} cases")

    unknown_samples = diagnose_unknown_types(cases)
    range_failures = diagnose_range_table_failures(cases)
    marked_failures = diagnose_marked_failures(cases)


if __name__ == "__main__":
    main()
