# -*- coding: utf-8 -*-
"""WP7-A: stem must not overshoot Producer-declared stem end.

Regression for CHN-001 Q9: fill_in stem_lines=[110,112] leaked the next
section header `## 三、文学类阅读（16分）` at line 114 into resolved_spans.

Root cause: _stem_span boundary = first_option | region_upper; declared stem
END was never used as a clamp.  Only tighten — never expand past declared end.
"""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000a7")


def _mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _resolve(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)


class TestStemDeclaredEndBoundary:
    """WP7-A: declared stem end tightens the stem span."""

    def test_fill_in_stem_does_not_swallow_next_section_header(self):
        """Q9 scenario: stem_lines=[3,5], section header at line 6 must NOT enter stem."""
        lines = _mk(
            "9. 在横线上填写诗文原句。",                          # P1L001 → wait, renumber
            "游学活动中，同学们来到滕王阁。",                      # P1L002
            "此情此境让大家感受到中国文化的意蕴优美。",              # P1L003
            "",                                                   # P1L004
            "## 三、文学类阅读（16分）",                           # P1L005 — LEAK target
            "阅读下面的文字，回答各题。",                          # P1L006
        )
        # Declare stem as lines 1-3 (like Q9's [110,112]); header is line 5.
        payload = {"semantic_units": [{
            "unit_id": "Q9",
            "unit_type": "standalone_question",
            "question_number": "9",
            "content": {
                "stem": {
                    "question_label": "9",
                    "question_search_lines": [1, 3],
                    "stem_lines": [1, 3],
                    "question_label_printed": "9",
                },
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "9",
                    "answer_lines": [6, 6],
                },
            },
        }]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q9.stem")
        assert "P1L005" not in stem.line_refs, (
            f"stem swallowed next section header: {stem.line_refs}"
        )
        assert stem.line_refs[0] == "P1L001"
        assert "P1L003" in stem.line_refs  # declared end line still included
        assert "P1L004" not in stem.line_refs  # pad after declared end excluded

    def test_declared_end_clamps_overshooting_region(self):
        """When region_upper would overshoot, declared end wins (tighten-only)."""
        lines = _mk(
            "9. fill-in stem line one",       # P1L001
            "fill-in stem line two",          # P1L002
            "fill-in stem line three",        # P1L003
            "noise that would be captured",   # P1L004
            "## next section",                # P1L005
            "1. next question start",         # P1L006
            "A. opt",                         # P1L007
            "B. opt",                         # P1L008
            "C. opt",                         # P1L009
            "D. opt",                         # P1L010
            "【答案】",                        # P1L011
            "1. A",                           # P1L012
        )
        payload = {"semantic_units": [
            {
                "unit_id": "Q9",
                "unit_type": "standalone_question",
                "question_number": "9",
                "content": {
                    "stem": {
                        "question_label": "9",
                        "question_search_lines": [1, 3],
                        "stem_lines": [1, 3],
                        "question_label_printed": "9",
                    },
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": "9",
                        "answer_lines": [11, 12],
                    },
                },
            },
            {
                "unit_id": "Q1",
                "unit_type": "standalone_question",
                "question_number": "1",
                "content": {
                    "stem": {
                        "question_label": "1",
                        "question_search_lines": [6, 6],
                        "stem_lines": [6, 6],
                        "question_label_printed": "1",
                    },
                    "options": [
                        {"label": "A", "question_label": "1"},
                        {"label": "B", "question_label": "1"},
                        {"label": "C", "question_label": "1"},
                        {"label": "D", "question_label": "1"},
                    ],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": "1",
                        "answer_lines": [11, 12],
                    },
                },
            },
        ]}
        run = _resolve(lines, payload)
        stem9 = next(s for s in run.resolved_spans if s.span_id == "sp-Q9.stem")
        assert "P1L004" not in stem9.line_refs
        assert "P1L005" not in stem9.line_refs
        assert list(stem9.line_refs) == ["P1L001", "P1L002", "P1L003"]
        # Neighbor Q1 stem must NOT regress (only one line).
        stem1 = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.stem")
        assert list(stem1.line_refs) == ["P1L006"]

    def test_option_boundary_still_wins_when_tighter(self):
        """When first option is BEFORE declared end, option boundary is used (min)."""
        lines = _mk(
            "1. question stem and options share region",  # P1L001
            "A. apple",                                    # P1L002
            "B. banana",                                   # P1L003
            "C. car",                                      # P1L004
            "D. table",                                    # P1L005
            "【答案】",                                      # P1L006
            "1. A",                                        # P1L007
        )
        payload = {"semantic_units": [{
            "unit_id": "Q1",
            "unit_type": "standalone_question",
            "question_number": "1",
            "content": {
                "stem": {
                    "question_label": "1",
                    "question_search_lines": [1, 5],  # generous declared end
                    "stem_lines": [1, 5],
                    "question_label_printed": "1",
                },
                "options": [
                    {"label": "A", "question_label": "1"},
                    {"label": "B", "question_label": "1"},
                    {"label": "C", "question_label": "1"},
                    {"label": "D", "question_label": "1"},
                ],
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "1",
                    "answer_lines": [6, 7],
                },
            },
        }]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.stem")
        # Option A at line 2 is the tighter boundary — stem stays line 1 only.
        assert "P1L002" not in stem.line_refs
        assert list(stem.line_refs) == ["P1L001"]

    def test_no_declared_end_keeps_current_behavior(self):
        """question_search_lines absent → no clamp (backward compatible)."""
        lines = _mk(
            "1. stem only question",
            "A. apple",
            "B. banana",
            "C. car",
            "D. table",
            "【答案】",
            "1. A",
        )
        payload = {"semantic_units": [{
            "unit_id": "Q1",
            "unit_type": "standalone_question",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1", "question_label_printed": "1"},
                "options": [
                    {"label": "A", "question_label": "1"},
                    {"label": "B", "question_label": "1"},
                    {"label": "C", "question_label": "1"},
                    {"label": "D", "question_label": "1"},
                ],
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "1",
                    "answer_lines": [6, 7],
                },
            },
        }]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.stem")
        assert "P1L001" in stem.line_refs
