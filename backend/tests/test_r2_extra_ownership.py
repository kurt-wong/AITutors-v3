# -*- coding: utf-8 -*-
"""R2 Fixes A+B: extra_lines unit-ownership filter + fallback extra merge.

Fix A: extra_lines union must NOT include lines owned by other units.
Fix B: declared fallback branch must also merge owned extras.
"""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f1")


def _mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _resolve(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)


class TestExtraOwnershipFilter:
    """Fix A: extra_lines union excludes other units' stem lines."""

    def test_q19_style_pollution_prevented(self):
        """Q19 extras [308,318] contain Q21/Q22 stems — must be excluded."""
        lines = _mk(
            "1. Q19 stem text",                  # L1  (Q19 stem_lines=[1,1])
            "2. Q20 stem text",                  # L2  (Q20 stem_lines=[2,2])
            "3. Q21 stem text",                  # L3  (Q21 stem_lines=[3,3])
            "4. Q22 stem text",                  # L4  (Q22 stem_lines=[4,4])
            "<img Q19 pic>",                     # L5  (Q19 extra - OK)
            "",                                  # L6
            "<img other>",                       # L7  (Q19 extra range, but maybe OK)
        )
        # Q19: stem=[1,1], extra=[5,7]  (range covers L5-L7, L3-L4 are other stems)
        # Q21: stem=[3,3], Q22: stem=[4,4]
        payload = {"semantic_units": [
            {"unit_id": "Q19", "unit_type": "standalone_question",
             "question_number": "1",
             "content": {"stem": {"question_label": "1",
                                   "question_search_lines": [1, 1],
                                   "stem_lines": [1, 1],
                                   "extra_lines": [5, 7]},
                         "answer": {"answer_zone": "answer_table",
                                     "question_label": "1",
                                     "answer_lines": [7, 7]}}},
            {"unit_id": "Q21", "unit_type": "standalone_question",
             "question_number": "3",
             "content": {"stem": {"question_label": "3",
                                   "question_search_lines": [3, 3],
                                   "stem_lines": [3, 3]},
                         "answer": {"answer_zone": "answer_table",
                                     "question_label": "3",
                                     "answer_lines": [7, 7]}}},
            {"unit_id": "Q22", "unit_type": "standalone_question",
             "question_number": "4",
             "content": {"stem": {"question_label": "4",
                                   "question_search_lines": [4, 4],
                                   "stem_lines": [4, 4]},
                         "answer": {"answer_zone": "answer_table",
                                     "question_label": "4",
                                     "answer_lines": [7, 7]}}},
        ]}
        run = _resolve(lines, payload)
        q19_stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q19.stem")
        refs = list(q19_stem.line_refs)
        assert "P1L001" in refs  # own stem
        assert "P1L005" in refs  # own extra (image)
        # Q21 and Q22 stems must NOT pollute Q19
        assert "P1L003" not in refs, f"Q21 stem polluted Q19: {refs}"
        assert "P1L004" not in refs, f"Q22 stem polluted Q19: {refs}"

    def test_q22_continuation_preserved(self):
        """Q22's own extra continuation must remain even when other units exist."""
        lines = _mk(
            "4. Q22 stem start",                 # L1
            "",                                  # L2
            "other content",                     # L3 (gap)
            "",                                  # L4
            "continuation of Q22",               # L5 (extra, owned by Q22)
        )
        payload = {"semantic_units": [
            {"unit_id": "Q22", "unit_type": "standalone_question",
             "question_number": "4",
             "content": {"stem": {"question_label": "4",
                                   "question_search_lines": [1, 1],
                                   "stem_lines": [1, 1],
                                   "extra_lines": [5, 5]},
                         "answer": {"answer_zone": "answer_table",
                                     "question_label": "4",
                                     "answer_lines": [5, 5]}}},
        ]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q22.stem")
        refs = list(stem.line_refs)
        assert "P1L001" in refs
        assert "P1L005" in refs, f"continuation lost: {refs}"
        assert "P1L003" not in refs  # gap not included

    def test_q13_image_extras_preserved(self):
        """Q13's image extras must remain (no other unit claims those lines)."""
        lines = _mk(
            "13. stem text",                     # L1
            "",                                  # L2
            "A. opt1 B. opt2",                   # L3
            "<img pic1>",                        # L4 (extra)
            "<img pic2>",                        # L5 (extra)
        )
        payload = {"semantic_units": [{
            "unit_id": "Q13", "unit_type": "standalone_question",
            "question_number": "13",
            "content": {"stem": {"question_label": "13",
                                  "question_search_lines": [1, 1],
                                  "stem_lines": [1, 1],
                                  "extra_lines": [4, 5]},
                        "options": [{"label": "A"}, {"label": "B"}],
                        "answer": {"answer_zone": "answer_table",
                                    "question_label": "13",
                                    "answer_lines": [5, 5]}}},
        ]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q13.stem")
        refs = list(stem.line_refs)
        assert "P1L001" in refs
        assert "P1L004" in refs, f"extra image 1 lost: {refs}"
        assert "P1L005" in refs, f"extra image 2 lost: {refs}"


class TestFallbackExtraMerge:
    """Fix B: declared fallback branch must also merge owned extras."""

    def test_fallback_merges_extras(self):
        """When question_search_lines is used as fallback, extras must merge."""
        lines = _mk(
            "",                                  # L1 (no qn token - triggers fallback)
            "fill-in stem text here",            # L2
            "",                                  # L3
            "<img pic>",                         # L4 (extra, owned)
        )
        payload = {"semantic_units": [{
            "unit_id": "Q6", "unit_type": "standalone_question",
            "question_number": "6",
            "content": {"stem": {"question_label": "6",
                                  "question_search_lines": [2, 2],
                                  "stem_lines": [2, 2],
                                  "extra_lines": [4, 4]},
                        "answer": {"answer_zone": "answer_table",
                                    "question_label": "6",
                                    "answer_lines": [4, 4]}}},
        ]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q6.stem")
        refs = list(stem.line_refs)
        assert "P1L002" in refs, f"declared stem lost: {refs}"
        assert "P1L004" in refs, f"extra lost in fallback: {refs}"

    def test_fallback_no_cross_pollution(self):
        """Fallback extras must also respect ownership."""
        lines = _mk(
            "",                                  # L1
            "Q6 stem",                           # L2 (Q6 declared)
            "Q7 stem",                           # L3 (Q7 declared)
            "<img Q6 pic>",                      # L4 (Q6 extra - OK)
        )
        payload = {"semantic_units": [
            {"unit_id": "Q6", "unit_type": "standalone_question",
             "question_number": "6",
             "content": {"stem": {"question_label": "6",
                                   "question_search_lines": [2, 2],
                                   "stem_lines": [2, 2],
                                   "extra_lines": [3, 4]},  # range covers Q7!
                         "answer": {"answer_zone": "answer_table",
                                     "question_label": "6",
                                     "answer_lines": [4, 4]}}},
            {"unit_id": "Q7", "unit_type": "standalone_question",
             "question_number": "7",
             "content": {"stem": {"question_label": "7",
                                   "question_search_lines": [3, 3],
                                   "stem_lines": [3, 3]},
                         "answer": {"answer_zone": "answer_table",
                                     "question_label": "7",
                                     "answer_lines": [4, 4]}}},
        ]}
        run = _resolve(lines, payload)
        q6_stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q6.stem")
        refs = list(q6_stem.line_refs)
        assert "P1L002" in refs
        assert "P1L004" in refs  # own extra
        assert "P1L003" not in refs, f"Q7 stem polluted Q6: {refs}"
