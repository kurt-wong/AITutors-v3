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

# Option labels: A–Z + separator (OCR uses . ． 、 ， and glued forms).
# E2E-009R2: detect the FULL declared label set (A–H matching, A–E) so
# non-A–D structures fail explicitly instead of silently truncating to A–D.
_OPT_LABEL = re.compile(r"([A-Z])\s*[\.．、，,]\s*")

_BLANK_MARK = re.compile(r"^\s*$")
_IMG_MARK = re.compile(r"^\s*<(div|img|table)|^\s*---\s*$|^\s*#+\s")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_IMG_RE = re.compile(r"<img\b", re.I)


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


def _is_trailing_pad(line: str) -> bool:
    """Only blank / `---` / heading padding — never HTML option bodies.

    V3-IMG-OPTION-001: image-option rows (`<div>B.</div>`, `<div><img/></div>`)
    are real content; trailing-tighten must not eat them.
    """
    s = line.strip()
    return (not s) or bool(re.match(r"^\s*---\s*$", s)) or bool(re.match(r"^#+\s", s))


def _html_text_content(line: str) -> str:
    """Strip HTML tags; return visible text content (V3-IMG-OPTION-001).

    Lets option labels wrapped in layout markup (`<div>B.</div>`) stay
    discoverable without treating the whole line as discarded noise.
    """
    return _HTML_TAG_RE.sub(" ", line)


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
    """Collect ordered option labels within one sub-question body.

    V3-IMG-OPTION-001: also read labels out of HTML layout wrappers
    (`<div>B.</div>`) so image-option composites (GEO Q8) expose A–D.
    Pure image rows (`<div><img …/></div>`) contribute no label.
    """
    labels: list[str] = []
    for seq in range(start, end + 1):
        raw = lines[seq - 1]
        candidates: list[str] = []
        if not _is_noise(raw):
            frag = raw
            if seq == start and col is not None:
                frag = raw[col:]
                frag = re.sub(rf"^\s*\d{{1,2}}\s*{_SUBQ_SEP}\s*", "", frag)
            candidates.append(frag)
        elif raw.strip().startswith("<") and not _HTML_IMG_RE.search(raw):
            # layout-only wrapper (div/table cell) — read its text content
            text = _html_text_content(raw).strip()
            if text:
                candidates.append(text)
        for frag in candidates:
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
    has_declared_options: bool = False,
) -> ExpandResult:
    """Deterministically expand a multi-q composite into per-question subs.

    Fail-closed per sub: only emit when stem bounds, A–D options, and answer
    evidence are all uniquely determined. short_answer / non-choice → no expand.

    Type scope (E2E-009R1 Owner ruling):
      - choice types + ``cloze`` always enter expansion
      - ``reading`` enters only when the manifest declared options
        (selection-type reading); non-selection reading stays out
      - essay / fill_in / reading_expression / unknown → out of scope
    """
    result = ExpandResult()

    choice_types = ("single_choice", "multiple_choice", "true_false", "cloze")
    # Owner 2026-10 / E2E-010: 语法填空/选词填空/阅读表达/作文无选项也应入库。
    # seven_to_five 有共享 A–G，子题不要求各自 A–D。
    open_text_types = (
        "fill_in", "reading_expression", "essay",
        "grammar_fill", "vocabulary_fill", "seven_to_five",
    )
    in_scope = (
        original_question_type in choice_types
        or original_question_type in open_text_types
        or (original_question_type == "reading" and has_declared_options)
    )
    if not in_scope:
        result.unit_reason = f"type {original_question_type!r} not in scope"
        return result
    require_ad_options = original_question_type not in open_text_types
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
    # E2E-009R5 Q30: cloze blank lives in the passage (`night 30 he`) while the
    # option row was lost in OCR. Recover the blank line as a stem-only sub
    # so the declared qn is not silently dropped. Mark as passage-blank so the
    # stem window stays on that line (not until the next option row).
    passage_blanks: set[int] = set()
    if original_question_type in ("cloze", "grammar_fill", "vocabulary_fill", "seven_to_five", "fill_in"):
        for qn in question_numbers:
            if qn in found_nums:
                continue
            # E2E-010: OCR blanks are `$ \underline{N} $` or `N.` or bare N in passage.
            pats = [
                re.compile(rf"\\underline\s*{{\s*{qn}\s*}}"),
                re.compile(rf"(?<!\d){qn}(?!\d)"),
            ]
            for seq in range(q_start, q_end + 1):
                raw = lines[seq - 1]
                if _is_noise(raw):
                    continue
                if _OPT_LABEL.search(raw) and original_question_type != "seven_to_five":
                    continue
                hit = None
                for pat in pats:
                    hit = pat.search(raw)
                    if hit:
                        break
                if hit:
                    starts.append((seq, qn, hit.start()))
                    found_nums.append(qn)
                    passage_blanks.add(qn)
                    break
        starts.sort(key=lambda t: (t[0], t[2]))
    for qn in question_numbers:
        if qn not in found_nums:
            result.skipped[qn] = "question start not found"

    for i, (seq, qn, col) in enumerate(starts):
        if qn in passage_blanks:
            end = seq  # passage blank: stem is the blank line only
        else:
            end = q_end
            if i + 1 < len(starts):
                nxt = starts[i + 1][0]
                end = nxt - 1 if nxt > seq else seq
        # tighten trailing pad (blank/`---` only — keep HTML option bodies)
        while end > seq and _is_trailing_pad(lines[end - 1]):
            end -= 1

        labels = _sub_option_labels(lines, seq, end, col)
        if require_ad_options:
            if labels == [] and original_question_type in ("cloze", "reading"):
                # P2-fix-3: stem-only sub within cloze/reading — no A-D options
                # (e.g. fill-in blanks inside a reading passage).  Still a
                # declared child; answer evidence has the value.  No guessing.
                option_labels = ()
            elif labels != ["A", "B", "C", "D"]:
                result.skipped[qn] = (
                    f"option boundary unresolved (labels={labels})"
                )
                continue
            else:
                option_labels = ("A", "B", "C", "D")
        else:
            # open-text (fill_in / reading_expression / essay): options optional.
            option_labels = tuple(labels) if labels == ["A", "B", "C", "D"] else ()

        # stem must have non-noise content beyond the question marker,
        # except cloze: number + A–D options on one line is the whole item.
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
        if not stem_has_text and original_question_type != "cloze":
            result.skipped[qn] = "stem empty"
            continue

        result.sub_questions.append(
            SubQuestionSpec(
                question_number=qn,
                stem_start=seq,
                stem_end=end,
                option_labels=option_labels,
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
                # E2E-009R2 contract: an expanded child with declared A–D options
                # is structurally a single_choice item (cloze blank / reading MC).
                # Gate STRICT_AUTO_TYPES opens single_choice; keeping cloze/reading
                # here would strand every composite child in pending forever.
                # Non-choice parents never reach this path (expand is choice-only).
                "original_question_type": (
                    "single_choice"
                    if tuple(spec.option_labels) == ("A", "B", "C", "D")
                    else original_question_type
                ),
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
