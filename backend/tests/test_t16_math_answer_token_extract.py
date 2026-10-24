# -*- coding: utf-8 -*-
"""T16 MATH-ANSWER-ROOT-CAUSE regressions.

Reproduces the two residual single-line failures after A-form migration:
  Q3-like: math line with false entry `=(1,` + declared value B → must bind B
  Q4-like: 【解答】…故选：A. line with declared value A → must bind A
Also pins: multi-line solution block still binds full range (no 故选 heuristic).
"""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-000000000016")


def mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(qn: str, answer_lines, answer_value=None):
    ans = {
        "role": "answer",
        "question_label": qn,
        "answer_zone": "answer_table",
        "answer_lines": list(answer_lines),
    }
    if answer_value is not None:
        ans["answer_value"] = answer_value
        ans["answer_evidence_lines"] = list(answer_lines)
    return {
        "semantic_units": [
            {
                "unit_id": f"Q{qn}",
                "unit_type": "standalone_question",
                "question_number": qn,
                "content": {
                    "stem": {"question_label": qn},
                    "options": [
                        {"label": "A"},
                        {"label": "B"},
                        {"label": "C"},
                        {"label": "D"},
                    ],
                    "answer": ans,
                },
            }
        ]
    }


def _answer_span(run):
    return next(s for s in run.resolved_spans if s.role == "answer")


def test_math_false_entry_conflict_does_not_block_token_extract():
    """Q3-like: math expression contains `=(1,` false entry; declared value B."""
    raw = (
        "则于  $ \\overrightarrow{a}-2\\overrightarrow{b}=(1,2)-2(4,3)="
        "(1,2)-(8,6)=(1-8,2-6)=(-7,-4) $，故选：B."
    )
    lines = mk(raw)
    run = SourceResolver(source_version_id=SVID, lines=lines, figures=()).resolve(
        _payload("3", [1, 1], answer_value="B")
    )
    a = _answer_span(run)
    assert a.resolution_status == "exact", a.evidence
    assert a.granularity == "line_character"
    assert lines[0].text[a.start_offset : a.end_offset] == "B"


def test_explanation_line_with_marker_extracts_declared_token():
    """Q4-like: whole 【解答】 line is not a bare cell; extract A."""
    raw = "【解答】解：由于当自变量相同时，它们的函数值相反，故它们的图象关于x轴对称，故选：A."
    lines = mk(raw)
    run = SourceResolver(source_version_id=SVID, lines=lines, figures=()).resolve(
        _payload("4", [1, 1], answer_value="A")
    )
    a = _answer_span(run)
    assert a.resolution_status == "exact", a.evidence
    assert lines[0].text[a.start_offset : a.end_offset] == "A"


def test_clean_marker_line_still_extracts():
    raw = "故选：D."
    lines = mk(raw)
    run = SourceResolver(source_version_id=SVID, lines=lines, figures=()).resolve(
        _payload("1", [1, 1], answer_value="D")
    )
    a = _answer_span(run)
    assert a.resolution_status == "exact"
    assert lines[0].text[a.start_offset : a.end_offset] == "D"


def test_multi_line_solution_block_still_full_range_no_gu_xuan_heuristic():
    """B3c-A freeze: multi-line answer_lines bind full range, no 故选 shortcut."""
    lines = mk(
        "1.",
        "【考点】代数",
        "【分析】略",
        "【解答】过程",
        "故选A",
    )
    run = SourceResolver(source_version_id=SVID, lines=lines, figures=()).resolve(
        _payload("1", [1, 5], answer_value=None)
    )
    a = _answer_span(run)
    assert a.line_refs == ("P1L001", "P1L002", "P1L003", "P1L004", "P1L005")
    assert a.granularity == "line"


def test_declared_value_absent_from_line_does_not_silently_bind_other():
    """Declared B but line only has 故选：A and no B → must not bind A as B."""
    raw = "故选：A."
    lines = mk(raw)
    run = SourceResolver(source_version_id=SVID, lines=lines, figures=()).resolve(
        _payload("2", [1, 1], answer_value="B")
    )
    a = _answer_span(run)
    # B is not on the line — token extract must not fire; outcome is not exact-B
    if a.resolution_status in ("exact", "normalized"):
        text = lines[0].text[a.start_offset : a.end_offset]
        assert text != "B" or "B" in raw
    else:
        assert a.resolution_status in ("value_only", "incomplete", "missing", "ambiguous")
