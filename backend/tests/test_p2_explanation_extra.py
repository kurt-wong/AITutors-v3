# -*- coding: utf-8 -*-
"""P2 fixes: explanation mapping + extra_lines union in stem.

Verify:
1. content["explanation"] is now mapped from explanation_lines
2. extra_lines are included in stem as UNION (not contiguous extension)
3. Cross-question pollution in the gap is avoided
"""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000d1")


def _mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _resolve(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)


class TestExplanationMapping:
    """P2-fix-1: explanation_lines → content["explanation"] → resolved span."""

    def test_explanation_mapped_to_content(self):
        lines = ["1. stem", "A. a", "B. b", "C. c", "D. d", "【答案】A", "【解析】some explanation"]
        man = {"units": [{
            "unit_id": "Q1", "unit_type": "standalone_question",
            "question_numbers": [1], "original_question_type": "single_choice",
            "stem_lines": [1, 1], "options_lines": [2, 5],
            "answer_lines": [6, 6], "explanation_lines": [7, 7],
            "options": [{"label": l} for l in "ABCD"],
        }]}
        bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="a" * 64, manifest_identity_version=2)
        u = payload["semantic_units"][0]
        assert "explanation" in u.get("content", {}), "content.explanation missing"
        expl = u["content"]["explanation"]
        assert expl["explanation_lines"] == [7, 7]

    def test_explanation_resolves_to_span(self):
        lines = _mk("1. stem", "A. a", "B. b", "C. c", "D. d",
                     "【答案】A", "【解析】some explanation text here")
        payload = {"semantic_units": [{
            "unit_id": "Q1", "unit_type": "standalone_question",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1", "question_search_lines": [1, 1],
                          "stem_lines": [1, 1]},
                "options": [{"label": l, "question_label": "1"} for l in "ABCD"],
                "answer": {"answer_zone": "answer_table", "question_label": "1",
                            "answer_lines": [6, 6]},
                "explanation": {"role": "explanation", "question_label": "1",
                                 "explanation_zone": "inline_explanation",
                                 "explanation_lines": [7, 7]},
            },
        }]}
        run = _resolve(lines, payload)
        span_ids = {s.span_id for s in run.resolved_spans}
        assert "sp-Q1.explanation" in span_ids, f"explanation span missing: {span_ids}"
        expl = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.explanation")
        assert "P1L007" in expl.line_refs

    def test_no_explanation_no_crash(self):
        lines = ["1. stem", "A. a", "B. b", "C. c", "D. d", "【答案】A"]
        man = {"units": [{
            "unit_id": "Q1", "unit_type": "standalone_question",
            "question_numbers": [1], "original_question_type": "single_choice",
            "stem_lines": [1, 1], "options_lines": [2, 5], "answer_lines": [6, 6],
            "options": [{"label": l} for l in "ABCD"],
        }]}
        bound = bind_units_from_manifest(man, lines, source_content_sha256="b" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="b" * 64, manifest_identity_version=2)
        u = payload["semantic_units"][0]
        assert "explanation" not in u.get("content", {})


class TestExtraLinesUnion:
    """P2-fix-2: extra_lines included as UNION in stem, no gap pollution."""

    def test_extra_lines_in_stem_content(self):
        lines = ["stem text", "", "gap noise", "", "continuation text", "img html"]
        man = {"units": [{
            "unit_id": "Q1", "unit_type": "standalone_question",
            "question_numbers": [1], "original_question_type": "fill_in",
            "stem_lines": [1, 1], "extra_lines": [5, 6],
            "answer_lines": [6, 6],
        }]}
        bound = bind_units_from_manifest(man, lines, source_content_sha256="c" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="c" * 64, manifest_identity_version=2)
        u = payload["semantic_units"][0]
        stem = u["content"]["stem"]
        assert stem.get("extra_lines") == [5, 6], f"extra_lines not mapped: {stem}"

    def test_extra_lines_union_in_resolved_stem(self):
        """Q22 scenario: stem L1, continuation L5 (extra), gap L3 has other content."""
        lines = _mk(
            "4. stem start text",          # L1  (stem_lines=[1,1])
            "",
            "other question's image",      # L3  (gap — must NOT enter)
            "",
            "continuation of stem",        # L5  (extra_lines=[5,5])
            "<img src='pic.jpg'>",         # L6  (extra_lines)
        )
        payload = {"semantic_units": [{
            "unit_id": "Q1", "unit_type": "standalone_question",
            "question_number": "4",
            "content": {
                "stem": {
                    "question_label": "4",
                    "question_search_lines": [1, 1],
                    "stem_lines": [1, 1],
                    "extra_lines": [5, 6],
                },
                "answer": {"answer_zone": "answer_table", "question_label": "4",
                            "answer_lines": [6, 6]},
            },
        }]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.stem")
        refs = list(stem.line_refs)
        assert "P1L001" in refs  # stem text
        assert "P1L005" in refs  # continuation (extra)
        assert "P1L006" in refs  # image (extra)
        assert "P1L003" not in refs, f"gap pollution: {refs}"  # other question's content

    def test_no_extra_lines_uses_contiguous_only(self):
        lines = _mk("1. stem", "", "noise", "", "more", "A. opt")
        payload = {"semantic_units": [{
            "unit_id": "Q1", "unit_type": "standalone_question",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1", "question_search_lines": [1, 1],
                          "stem_lines": [1, 1]},
                "options": [{"label": "A", "question_label": "1"}],
                "answer": {"answer_zone": "answer_table", "question_label": "1",
                            "answer_lines": [6, 6]},
            },
        }]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.stem")
        refs = list(stem.line_refs)
        assert "P1L001" in refs
        # Without extra_lines, should NOT include L3/L5 (WP7-A clamp + no extras)
        assert "P1L003" not in refs
