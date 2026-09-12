"""
B2-B3-A: Target Classification Audit — Frozen Results

Purpose: Extract the ~34 real fill-in targets from the original 106,
excluding MC misclassifications. Output a frozen test set for B2-B3-B.

This script is READ-ONLY on corpus data. It does not modify any production code.
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


def is_mc_answer_line(text: str) -> bool:
    """Detect if a line is actually an MC answer (possibly with explanation)."""
    t = text.strip()

    m = re.match(r"^[\(（]?(\d+)[\)）]?[\.、．:：]?\s*([A-H]{1,4})\s*(.*)", t)
    if m:
        answer_letters = m.group(2)
        rest = m.group(3).strip()
        if all(c in "ABCDEFGH" for c in answer_letters):
            if not rest:
                return True
            if re.match(r'^[一-鿿]', rest):
                return True
            if re.match(r'^[\$\\（\(]', rest):
                return True

    if re.search(r"\d+[\.、．]?\s*[A-H]\s+\d+[\.、．]?\s*[A-H]", t):
        return True

    return False


def classify_real_fillin(text: str) -> str:
    """Classify a line that is confirmed to be a real fill-in answer."""
    t = text.strip()

    m_qn = re.match(r"^[\(（]?(\d+)[\)）]?[\.、．:：\s]+", t)
    answer_part = t[m_qn.end():].strip() if m_qn else t

    if not answer_part:
        return "F0_empty"

    numbers = re.findall(r"\d+", answer_part)
    multiple_numbers = len(numbers) >= 2
    has_comma = bool(re.search(r"[,，、]", answer_part))
    has_or = bool(re.search(r"或|或者", answer_part))
    has_unit = bool(re.search(r"(mol|g|kg|L|mL|℃|°C|kPa|Pa|cm|mm|m|元|个|种|倍|%|分)", answer_part))
    has_formula = bool(re.search(r"[A-Z][a-z]?\d", answer_part))
    has_range = bool(re.search(r"\d+\s*[-–~～]\s*\d+", answer_part))
    is_long = len(answer_part) > 50
    has_image = bool(re.search(r"如图|见图|图\s*\d", t))

    if is_long:
        return "F8_long"
    if has_image:
        return "F9_image"
    if has_or:
        return "F4_alternative"
    if has_range:
        return "F6_range"
    if multiple_numbers and has_comma:
        return "F2_multi_blank"
    if multiple_numbers and not has_comma:
        return "F3_concatenated"
    if has_comma:
        return "F2_multi_blank"
    if has_unit or has_formula:
        return "F5_multi_token"
    if m_qn:
        return "F1_single"
    return "F7_no_number"


def main() -> int:
    cases = load_corpus()
    print(f"Loaded {len(cases)} cases")

    all_fillin_units = []
    mc_misclassified = []
    real_fillin_units = []

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
            if ans_type != "fill_in":
                continue

            all_fillin_units.append({
                "case_id": case.case_id,
                "unit_id": uid,
                "subject": case.subject,
                "region": [start, end],
                "raw_lines": raw_lines,
            })

    print(f"\nOriginal fill_in targets: {len(all_fillin_units)}")

    for item in all_fillin_units:
        lines = item["raw_lines"]
        non_empty = [l for l in lines if l.strip()]

        all_mc = all(is_mc_answer_line(l) for l in non_empty)

        if all_mc:
            mc_misclassified.append(item)
        else:
            line_classes = []
            for line in non_empty:
                if is_mc_answer_line(line):
                    continue
                cls = classify_real_fillin(line)
                line_classes.append({"text": line.strip()[:100], "class": cls})

            real_fillin_units.append({
                **item,
                "line_classes": line_classes,
            })

    print(f"MC misclassified: {len(mc_misclassified)}")
    print(f"Real fill-in: {len(real_fillin_units)}")

    class_counts = {}
    for item in real_fillin_units:
        for lc in item["line_classes"]:
            cls = lc["class"]
            class_counts[cls] = class_counts.get(cls, 0) + 1

    print("\n## Real Fill-in Class Distribution")
    total_lines = sum(class_counts.values())
    for cls in sorted(class_counts, key=lambda c: -class_counts[c]):
        count = class_counts[cls]
        pct = 100 * count / total_lines if total_lines else 0
        print(f"  {cls}: {count} ({pct:.1f}%)")
    print(f"  TOTAL lines: {total_lines}")

    subject_counts = {}
    for item in real_fillin_units:
        subj = item["subject"]
        subject_counts[subj] = subject_counts.get(subj, 0) + 1

    print("\n## Subject Distribution (real fill-in)")
    for subj in sorted(subject_counts, key=lambda s: -subject_counts[s]):
        print(f"  {subj}: {subject_counts[subj]}")

    output = {
        "audit_version": "B2-B3-A-v1",
        "original_fillin_count": len(all_fillin_units),
        "mc_misclassified_count": len(mc_misclassified),
        "real_fillin_count": len(real_fillin_units),
        "class_distribution": class_counts,
        "subject_distribution": subject_counts,
        "mc_misclassified_units": [
            {"case_id": m["case_id"], "unit_id": m["unit_id"], "subject": m["subject"]}
            for m in mc_misclassified
        ],
        "real_fillin_test_set": [
            {
                "case_id": r["case_id"],
                "unit_id": r["unit_id"],
                "subject": r["subject"],
                "region": r["region"],
                "line_classes": r["line_classes"],
            }
            for r in real_fillin_units
        ],
    }

    out_path = Path("Docs/V3_SPEC/gate_b2b3_frozen_testset.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nFrozen test set written to: {out_path}")
    print(f"  Real fill-in units: {len(real_fillin_units)}")
    print(f"  MC misclassified: {len(mc_misclassified)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
