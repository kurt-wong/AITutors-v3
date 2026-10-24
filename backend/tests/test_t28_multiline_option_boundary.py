"""T2.8 regression: multi-line option blocks vs cloze passage blanks.

Real failure shape (EN U26-40 text-layer MD):
  passage: `Once the bus came, she got in it  28  .`
  options:
    28. A. quickly
    B. easily
    C. lazily
    D. patiently

_find_sub_starts must prefer the option-row start so the sub window gets A–D.
"""
from __future__ import annotations

from app.domains.source.subq_expand import (
    _find_sub_starts,
    _sub_option_labels,
    expand_composite_sub_questions,
)

# Minimal reproduction of the T2.7 text-layer cloze layout.
LINES = [
    # L1 material (passage with blanks)
    "Once the bus came, she got in it  28  . She was very excited.",
    "29 the bus reached her school. Don't 35  . Just write. a few days 36  .",
    # L3 option block (one option per line — text-layer layout)
    "26. A. finished",
    "B. liked",
    "C. suggested",
    "D. practised",
    "27. A. anxious",
    "B. happy",
    "C. afraid",
    "D. calm",
    "28. A. quickly",
    "B. easily",
    "C. lazily",
    "D. patiently",
    "29. A. Until",
    "B. When",
    "C. Unless",
    "D. Although",
    "35. A. cry",
    "B. forget",
    "C. write",
    "D. worry",
    "36. A. on",
    "B. later",
    "C. back",
    "D. away",
]
# 1-based: L1-L2 passage, L3+ options. questions_range covers both.
QNS = [26, 27, 28, 29, 35, 36]
Q_RANGE = (1, len(LINES))
ANSWER_RANGE = (20, 20)  # dummy


def test_prefer_option_row_over_passage_blank():
    starts = _find_sub_starts(LINES, Q_RANGE[0], Q_RANGE[1], QNS)
    by = {n: (s, c) for s, n, c in starts}
    # 28 appears in passage L1 and option row L11 → must pick L11
    assert by[28][0] == 11, by
    # 35 appears in passage L2 and option row L19 → must pick L19
    assert by[35][0] == 19, by
    # 36 likewise
    assert by[36][0] == 23, by


def test_multi_line_options_bound_to_same_sub():
    starts = _find_sub_starts(LINES, Q_RANGE[0], Q_RANGE[1], QNS)
    by = {n: (s, c) for s, n, c in starts}
    seq = by[28][0]
    # window for 28: from start until next start
    ordered = sorted(starts, key=lambda t: t[0])
    idx = next(i for i, t in enumerate(ordered) if t[1] == 28)
    nxt = ordered[idx + 1][0]
    end = nxt - 1
    labels = _sub_option_labels(LINES, seq, end, by[28][1])
    assert labels == ["A", "B", "C", "D"], labels


def test_passage_blank_still_used_when_no_option_row():
    lines = [
        "Fill in the blank: the sky is  30  .",
        "31. A. red",
        "B. blue",
        "C. green",
        "D. yellow",
    ]
    # 30 has only a passage blank
    starts = _find_sub_starts(lines, 1, len(lines), [30, 31])
    by = {n: (s, c) for s, n, c in starts}
    assert by[30][0] == 1  # fallback to only candidate
    assert by[31][0] == 2


def test_no_cross_question_option_bleed():
    starts = _find_sub_starts(LINES, Q_RANGE[0], Q_RANGE[1], QNS)
    ordered = sorted(starts, key=lambda t: (t[0], t[2]))
    # 27 window must end before 28 option row
    by = {n: (s, c) for s, n, c in ordered}
    idx = next(i for i, t in enumerate(ordered) if t[1] == 27)
    end = ordered[idx + 1][0] - 1
    labels = _sub_option_labels(LINES, by[27][0], end, by[27][1])
    assert labels == ["A", "B", "C", "D"]
    # and its window should not include the `28.` line
    assert all("28." not in LINES[i - 1] for i in range(by[27][0], end + 1))


def test_expand_covers_all_with_abcd():
    res = expand_composite_sub_questions(
        LINES,
        question_numbers=QNS,
        questions_range=Q_RANGE,
        answer_range=ANSWER_RANGE,
        original_question_type="cloze",
        has_declared_options=True,
    )
    assert res.unit_reason is None
    assert sorted(s.question_number for s in res.sub_questions) == QNS
    for s in res.sub_questions:
        if s.question_number in (28, 35, 36):
            assert s.option_labels == ("A", "B", "C", "D"), (
                s.question_number,
                s.option_labels,
            )


def test_truly_missing_label_still_fails_closed():
    # 35 missing option D entirely → must NOT become ready A-D
    lines = [
        "Passage blank  35  .",
        "35. A. cry",
        "B. forget",
        "C. write",
    ]
    res = expand_composite_sub_questions(
        lines,
        question_numbers=[35],
        questions_range=(1, len(lines)),
        answer_range=(3, 3),
        original_question_type="cloze",
        has_declared_options=True,
    )
    # either skipped or no A-D options — must not claim full A-D
    for s in res.sub_questions:
        if s.question_number == 35:
            assert s.option_labels != ("A", "B", "C", "D")
    if not res.sub_questions:
        assert 35 in res.skipped
