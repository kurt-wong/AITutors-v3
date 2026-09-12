"""
B2-B3: Fill-in Binding Contract — Target Classification
Classify all fill-in answer lines into a contract matrix before any parser work.
Output: classification data for contract freeze.
"""
from __future__ import annotations

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "backend")
from scripts.gate_b.gate_b2b2_answer_table import (
    load_corpus, detect_answer_type, _extract_question_number,
)


def classify_fillin_line(text: str) -> dict:
    """Classify a single answer line into contract matrix categories."""
    t = text.strip()
    if not t:
        return {"class": "empty"}

    # Check if it's an MC answer (should skip)
    m_mc = re.match(r"^[\(（]?(\d+)[\)）]?[\.、．:：]?\s*([A-H]{1,4})\s*$", t)
    if m_mc and len(m_mc.group(2)) <= 4:
        return {"class": "MC_skip"}

    # Extract question number if present
    qn = None
    m_qn = re.match(r"^[\(（]?(\d+)[\)）]?[\.、．:：\s]+", t)
    if m_qn:
        qn = int(m_qn.group(1))

    answer_part = t
    if qn is not None:
        answer_part = t[m_qn.end():].strip()

    if not answer_part:
        return {"class": "empty_answer", "qn": qn}

    # Flags
    numbers = re.findall(r"\d+", answer_part)
    multiple_numbers = len(numbers) >= 2

    has_comma = bool(re.search(r"[,，、]", answer_part))
    has_or = bool(re.search(r"或|或者", answer_part))
    has_slash = "/" in answer_part
    has_semicolon = bool(re.search(r"[;；]", answer_part))
    has_unit = bool(re.search(r"(mol|g|kg|L|mL|℃|°C|kPa|Pa|cm|mm|m|km|元|个|种|倍|%|分)", answer_part))
    has_formula = bool(re.search(r"[A-Z][a-z]?\d", answer_part))
    is_long = len(answer_part) > 50
    has_image = bool(re.search(r"如图|见图|图\s*\d|image|img", t, re.IGNORECASE))
    has_range = bool(re.search(r"\d+\s*[-–~～]\s*\d+", answer_part))
    has_chinese = bool(re.search(r'[一-鿿]', answer_part))

    # Classification logic
    if is_long:
        cls = "F8_long_text"
    elif has_image:
        cls = "F9_image"
    elif has_or or has_semicolon:
        cls = "F4_alternative"
    elif has_range:
        cls = "F6_range"
    elif multiple_numbers and has_comma:
        cls = "F2_multi_blank_comma"
    elif multiple_numbers and not has_comma:
        cls = "F3_concatenated"
    elif has_comma:
        cls = "F2_multi_blank_comma"
    elif has_slash:
        cls = "F4_alternative"
    elif has_unit or has_formula:
        cls = "F5_multi_token"
    elif qn is not None:
        cls = "F1_single_blank"
    else:
        cls = "F7_no_number"

    return {
        "class": cls,
        "qn": qn,
        "answer_part": answer_part[:80],
        "flags": {
            "multiple_numbers": multiple_numbers,
            "has_comma": has_comma,
            "has_or": has_or,
            "has_unit": has_unit,
            "has_formula": has_formula,
            "has_range": has_range,
            "is_long": is_long,
        },
    }


def main() -> int:
    cases = load_corpus()
    print(f"Loaded {len(cases)} cases")

    class_counts = {}
    class_examples = {}
    unit_results = []

    for case in cases:
        for mu in case.manifest_units:
            uid = mu.get("unit_id", "?")
            ans = mu.get("answer_lines")
            if not ans or not isinstance(ans, list) or len(ans) != 2:
                continue
            start, end = ans[0], ans[1]
            if not start or not end:
                continue

            # Check if this is fill_in type
            raw_lines = [case.md_lines[i - 1].rstrip("\n") for i in range(start, end + 1)
                        if 1 <= i <= len(case.md_lines)]
            ans_type = detect_answer_type(raw_lines)
            if ans_type != "fill_in":
                continue

            # Classify each line
            line_classes = []
            for line in raw_lines:
                if not line.strip():
                    continue
                cls_info = classify_fillin_line(line)
                if cls_info["class"] == "MC_skip":
                    continue
                line_classes.append(cls_info)

                cls = cls_info["class"]
                class_counts[cls] = class_counts.get(cls, 0) + 1
                if cls not in class_examples:
                    class_examples[cls] = []
                if len(class_examples[cls]) < 5:
                    class_examples[cls].append({
                        "unit": uid,
                        "text": line.strip()[:100],
                    })

            unit_results.append({
                "unit": uid,
                "n_lines": len(raw_lines),
                "classes": [c["class"] for c in line_classes],
            })

    print("=" * 60)
    print("B2-B3: Fill-in Answer Line Classification")
    print("=" * 60)

    print(f"\nTotal fill-in units: {len(unit_results)}")
    total_lines = sum(class_counts.values())
    print(f"Total classified lines: {total_lines}")

    print("\n## Class Distribution")
    for cls in sorted(class_counts, key=lambda c: -class_counts[c]):
        count = class_counts[cls]
        pct = 100 * count / total_lines if total_lines else 0
        print(f"  {cls}: {count} ({pct:.1f}%)")

    print("\n## Examples per Class")
    for cls in sorted(class_examples):
        print(f"\n  {cls}:")
        for ex in class_examples[cls]:
            print(f"    {ex['unit']}: {ex['text']}")

    # Unit-level: simple vs complex
    simple = {"F1_single_blank", "F5_multi_token"}
    complex_ = {"F2_multi_blank_comma", "F3_concatenated", "F4_alternative",
                "F6_range", "F7_no_number", "F8_long_text", "F9_image"}

    n_simple = sum(1 for u in unit_results if u["classes"] and all(c in simple for c in u["classes"]))
    n_complex = sum(1 for u in unit_results if any(c in complex_ for c in u["classes"]))
    n_empty = sum(1 for u in unit_results if not u["classes"])

    print(f"\n## Unit-Level Summary")
    print(f"  Simple (F1/F5 only): {n_simple}")
    print(f"  Complex (has F2-F9): {n_complex}")
    print(f"  Empty (no lines): {n_empty}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
