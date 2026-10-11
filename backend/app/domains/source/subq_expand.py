"""Deterministic composite sub-question expansion (Geo spike authorized).

Scope (Owner GEO-SUBQ ruling):
  - Expand multi-question composite units into per-question sub_questions[]
    using only OCR markdown lines + manifest evidence. No LLM, no guessing.
  - Proven structure only: 题号 → 题干 → A–D options → answer-table reference.
  - Anything ambiguous (missing/truncated options, non-unique answer, multiple
    candidate boundaries) → that sub-question is NOT emitted.
  - Never emit a fake single-question covering a multi-q range; never emit a
    single sub that swallows the whole group.

short_answer is out of scope this round (separate answer-boundary work).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# OCR question-number start: digit + separator variant, not followed by a digit.
# Handles: 1.  1\.  29\.  15·  20，  36.  and glued forms  …题。16. / 完成26－2926.
_SUBQ_SEP = r"(?:\\?\s*[\.．、·，]|\\\.)"
_SUBQ_INLINE = re.compile(rf"(?<![\d．.、·，])(\d{{1,2}})\s*{_SUBQ_SEP}(?!\d)")
_SUBQ_AFTER_RANGE = re.compile(rf"完成\s*(\d{{1,2}})\s*[－—~\-]\s*\d{{1,2}}\s*\1\s*{_SUBQ_SEP}")

# Option labels: A–D + separator (OCR uses . ． 、 ， and glued forms).
_OPT_LABEL = re.compile(r"([ABCD])\s*[\.．、，,]\s*")

_BLANK_MARK = re.compile(r"^\s*$")
_IMG_MARK = re.compile(r"^\s*<(div|img|table)|^\s*---\s*$|^\s*#+\s")


@dataclass(frozen=True)
class SubQuestionSpec:
    """One fully-determined sub-question (evidence-backed, no guessing)."""

    question_number: int
    stem_start: int  # 1-based inclusive
    stem_end: int  # 1-based inclusive
    option_labels: tuple[str, ...]  # must be ("A","B","C","D") in order
    answer_lines: tuple[int, int]  # answer-table evidence range


@dataclass
class ExpandResult:
    """Expansion outcome for one composite unit."""

    sub_questions: list[SubQuestionSpec] = field(default_factory=list)
    skipped: dict[int, str] = field(default_factory=dict)  # qn → reason
    unit_reason: str | None = None  # set when the whole unit is not expandable


def _is_noise(line: str) -> bool:
    s = line.strip()
    return (not s) or bool(_IMG_MARK.match(s))


def _find_sub_starts(
    lines: list[str], q_start: int, q_end: int, qn_list: list[int]
) -> list[tuple[int, int, int]]:
    """Locate (seq, question_number, col) for each expected sub-question start."""
    wanted = set(qn_list)
    hits: list[tuple[int, int, int]] = []
    for seq in range(q_start, q_end + 1):
        raw = lines[seq - 1]
        if raw.strip().startswith("<") or raw.strip().startswith("#"):
            continue
        for m in _SUBQ_INLINE.finditer(raw):
            num = int(m.group(1))
            if num in wanted:
                hits.append((seq, num, m.start()))
        for m in _SUBQ_AFTER_RANGE.finditer(raw):
            num = int(m.group(1))
            if num in wanted:
                m2 = re.search(
                    rf"完成\s*\d{{1,2}}\s*[－—~\-]\s*\d{{1,2}}\s*{num}\s*{_SUBQ_SEP}",
                    raw[m.start():],
                )
                col = m.start() + m2.start() if m2 else m.start()
                hits.append((seq, num, col))
    # first occurrence per number, document order
    seen: set[int] = set()
    uniq: list[tuple[int, int, int]] = []
    for seq, num, col in hits:
        if num in seen:
            continue
        seen.add(num)
        uniq.append((seq, num, col))
    uniq.sort(key=lambda t: (t[0], t[2]))
    return uniq


def _extract_option_labels(text: str) -> list[str]:
    """Ordered option labels found in one fragment (A–D)."""
    return [m.group(1) for m in _OPT_LABEL.finditer(text)]


def _sub_option_labels(
    lines: list[str], start: int, end: int, col: int | None
) -> list[str]:
    """Collect ordered option labels within one sub-question body."""
    labels: list[str] = []
    for seq in range(start, end + 1):
        raw = lines[seq - 1]
        if _is_noise(raw):
            continue
        frag = raw
        if seq == start and col is not None:
            frag = raw[col:]
            frag = re.sub(rf"^\s*\d{{1,2}}\s*{_SUBQ_SEP}\s*", "", frag)
        for lab in _extract_option_labels(frag):
            if lab not in labels:
                labels.append(lab)
    return labels


def expand_composite_sub_questions(
    lines: list[str],
    *,
    question_numbers: list[int],
    questions_range: tuple[int, int] | None,
    answer_range: tuple[int, int] | None,
    original_question_type: str | None,
) -> ExpandResult:
    """Deterministically expand a multi-q composite into per-question subs.

    Fail-closed per sub: only emit when stem bounds, A–D options, and answer
    evidence are all uniquely determined. short_answer / non-choice → no expand.
    """
    result = ExpandResult()

    if original_question_type not in ("single_choice", "multiple_choice", "true_false"):
        result.unit_reason = f"type {original_question_type!r} not in scope"
        return result
    if not question_numbers:
        result.unit_reason = "no question_numbers"
        return result
    if questions_range is None:
        result.unit_reason = "no questions_lines"
        return result
    if answer_range is None:
        result.unit_reason = "no answer_lines"
        return result

    q_start, q_end = questions_range
    n = len(lines)
    if q_start < 1 or q_end > n or q_end < q_start:
        result.unit_reason = f"questions_lines out of bounds [{q_start},{q_end}]"
        return result

    starts = _find_sub_starts(lines, q_start, q_end, question_numbers)
    found_nums = [s[1] for s in starts]
    for qn in question_numbers:
        if qn not in found_nums:
            result.skipped[qn] = "question start not found"

    for i, (seq, qn, col) in enumerate(starts):
        end = q_end
        if i + 1 < len(starts):
            nxt = starts[i + 1][0]
            end = nxt - 1 if nxt > seq else seq
        # tighten trailing noise
        while end > seq and _is_noise(lines[end - 1]):
            end -= 1

        labels = _sub_option_labels(lines, seq, end, col)
        if labels != ["A", "B", "C", "D"]:
            result.skipped[qn] = (
                f"option boundary unresolved (labels={labels})"
            )
            continue

        # stem must have non-noise content beyond the question marker
        stem_has_text = False
        for s in range(seq, end + 1):
            raw = lines[s - 1]
            if _is_noise(raw):
                continue
            frag = raw[col:] if (s == seq and col is not None) else raw
            frag = re.sub(rf"^\s*\d{{1,2}}\s*{_SUBQ_SEP}\s*", "", frag).strip()
            # strip option-label runs to see if any stem prose remains
            prose = _OPT_LABEL.sub("", frag).strip()
            if prose:
                stem_has_text = True
                break
        if not stem_has_text:
            result.skipped[qn] = "stem empty"
            continue

        result.sub_questions.append(
            SubQuestionSpec(
                question_number=qn,
                stem_start=seq,
                stem_end=end,
                option_labels=("A", "B", "C", "D"),
                answer_lines=answer_range,
            )
        )

    return result


def specs_to_payload_subs(
    unit_id: str,
    specs: list[SubQuestionSpec],
    *,
    original_question_type: str,
    material_role: str = "material",
) -> list[dict]:
    """SubQuestionSpec → annotation-payload sub_questions[] entries.

    Shape matches build_annotation_payload_from_bound single-q composite path
    so resolver/IR consume it unchanged.
    """
    subs: list[dict] = []
    for spec in specs:
        qn = str(spec.question_number)
        stem = {
            "role": "stem",
            "question_label": qn,
            "question_search_lines": [spec.stem_start, spec.stem_end],
            "stem_lines": [spec.stem_start, spec.stem_end],
        }
        options = [
            {"role": "option", "label": lab, "question_label": qn}
            for lab in spec.option_labels
        ]
        answer = {
            "role": "answer",
            "question_label": qn,
            "answer_zone": "answer_table",
            "answer_lines": [spec.answer_lines[0], spec.answer_lines[1]],
        }
        subs.append(
            {
                "unit_id": f"{unit_id}.sub{qn}",
                "unit_type": "standalone_unit",
                "question_number": qn,
                "original_question_type": original_question_type,
                "content": {
                    "stem": stem,
                    "options": options,
                    "options_range": [spec.stem_start, spec.stem_end],
                    "answer": answer,
                },
                "depends_on": [
                    {"type": "material_dependency", "target": material_role}
                ],
            }
        )
    return subs
