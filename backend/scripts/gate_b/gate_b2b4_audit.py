"""
B2-B4-A: HTML Target Classification / Contract Freeze

Purpose: Classify all HTML answer targets into a contract matrix
before any parser work. Freeze the test scope for B2-B4-B.

This script is READ-ONLY on corpus data.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "backend")
from scripts.gate_b.gate_b2b2_answer_table import (
    load_corpus, detect_answer_type,
)


def classify_html_target(raw_lines: list[str], unit_id: str) -> dict:
    """Classify an HTML answer target into contract categories."""
    text = "\n".join(raw_lines)
    non_empty = [l for l in raw_lines if l.strip()]

    if not non_empty:
        return {"class": "H0_empty", "details": {}}

    table_count = len(re.findall(r"<table", text, re.IGNORECASE))
    tr_count = len(re.findall(r"<tr", text, re.IGNORECASE))
    td_count = len(re.findall(r"<td", text, re.IGNORECASE))
    th_count = len(re.findall(r"<th", text, re.IGNORECASE))

    has_colspan = bool(re.search(r"colspan", text, re.IGNORECASE))
    has_rowspan = bool(re.search(r"rowspan", text, re.IGNORECASE))
    has_text_outside = bool(re.search(r">[^<]{5,}<", text))
    has_image = bool(re.search(r"<img|!\[", text, re.IGNORECASE))
    has_math = bool(re.search(r"\$|\\frac|\\sqrt|\\alpha|\\beta", text))
    qn_in_cell = bool(re.search(r"<t[dh][^>]*>\s*[\(（]?\d+[\)）]?[\.、．:：]", text, re.IGNORECASE))
    mc_in_cell = bool(re.search(r"<t[dh][^>]*>\s*[A-H]{1,4}\s*</t[dh]>", text, re.IGNORECASE))
    has_answer_keyword = bool(re.search(r"答案|解答|answer", text, re.IGNORECASE))

    is_wellformed = (table_count > 0 and
                     text.count("<table") == text.count("</table>") and
                     text.count("<tr") >= text.count("</tr"))

    html_ratio = len(re.findall(r"<[^>]+>", text)) / max(len(text.split()), 1)

    if table_count == 0:
        if has_image:
            cls = "H9_image_only"
        elif has_math:
            cls = "H8_math_fragment"
        else:
            cls = "H7_html_fragment"
    elif table_count > 1:
        cls = "H2_multi_table"
    elif has_colspan or has_rowspan:
        cls = "H4_complex_structure"
    elif has_image:
        cls = "H6_html_with_image"
    elif qn_in_cell and mc_in_cell:
        cls = "H3_table_with_qn_and_mc"
    elif qn_in_cell:
        cls = "H3_table_with_qn"
    elif mc_in_cell:
        cls = "H3_table_with_mc"
    elif has_text_outside and html_ratio < 0.3:
        cls = "H5_mixed_content"
    elif not is_wellformed:
        cls = "H10_malformed"
    else:
        cls = "H1_simple_table"

    return {
        "class": cls,
        "details": {
            "table_count": table_count,
            "tr_count": tr_count,
            "td_count": td_count,
            "th_count": th_count,
            "has_colspan": has_colspan,
            "has_rowspan": has_rowspan,
            "has_image": has_image,
            "has_math": has_math,
            "qn_in_cell": qn_in_cell,
            "mc_in_cell": mc_in_cell,
            "is_wellformed": is_wellformed,
            "html_ratio": round(html_ratio, 2),
            "n_lines": len(raw_lines),
            "n_non_empty": len(non_empty),
        },
    }


def main() -> int:
    cases = load_corpus()
    print(f"Loaded {len(cases)} cases")

    html_targets = []

    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            ans = mu.get("answer_lines")
            if not ans or not isinstance(ans, list) or len(ans) != 2:
                continue
            start, end = ans[0], ans[1]
            if not start or not end:
                continue

            raw_lines = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)
                        if 1 <= i <= len(case.md_lines)]
            ans_type = detect_answer_type(raw_lines)
            if ans_type != "html":
                continue

            html_targets.append({
                "case_id": case.case_id,
                "unit_id": uid,
                "subject": case.subject,
                "region": [start, end],
                "raw_lines": raw_lines,
            })

    print(f"\nHTML answer targets: {len(html_targets)}")

    class_counts = {}
    class_examples = {}
    subject_by_class = {}
    classified_targets = []

    for item in html_targets:
        cls_info = classify_html_target(item["raw_lines"], item["unit_id"])
        cls = cls_info["class"]
        details = cls_info["details"]

        class_counts[cls] = class_counts.get(cls, 0) + 1

        if cls not in class_examples:
            class_examples[cls] = []
        if len(class_examples[cls]) < 3:
            first_line = next((l.strip() for l in item["raw_lines"] if l.strip()), "")
            class_examples[cls].append({
                "unit": item["unit_id"],
                "subject": item["subject"],
                "preview": first_line[:120],
            })

        if cls not in subject_by_class:
            subject_by_class[cls] = {}
        subj = item["subject"]
        subject_by_class[cls][subj] = subject_by_class[cls].get(subj, 0) + 1

        classified_targets.append({
            "case_id": item["case_id"],
            "unit_id": item["unit_id"],
            "subject": item["subject"],
            "region": item["region"],
            "class": cls,
            "details": details,
        })

    print("\n" + "=" * 60)
    print("B2-B4-A: HTML Target Classification")
    print("=" * 60)

    print("\n## Class Distribution")
    total = sum(class_counts.values())
    for cls in sorted(class_counts, key=lambda c: -class_counts[c]):
        count = class_counts[cls]
        pct = 100 * count / total if total else 0
        print(f"  {cls}: {count} ({pct:.1f}%)")
    print(f"  TOTAL: {total}")

    print("\n## Examples per Class")
    for cls in sorted(class_examples):
        print(f"\n  {cls}:")
        for ex in class_examples[cls]:
            print(f"    {ex['unit']} ({ex['subject']}): {ex['preview']}")

    print("\n## Subject Distribution per Class")
    for cls in sorted(subject_by_class):
        subjects = subject_by_class[cls]
        top = sorted(subjects.items(), key=lambda x: -x[1])[:3]
        print(f"  {cls}: {', '.join(f'{s}={c}' for s, c in top)}")

    output = {
        "audit_version": "B2-B4-A-v1",
        "total_html_targets": len(html_targets),
        "class_distribution": class_counts,
        "subject_by_class": subject_by_class,
        "classified_targets": classified_targets,
    }

    out_path = Path("Docs/V3_SPEC/gate_b2b4_frozen_testset.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nFrozen test set written to: {out_path}")
    print(f"  Total HTML targets: {len(html_targets)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
