# -*- coding: utf-8 -*-
"""R2 Fix C: composite explanation enters unit_out."""
from __future__ import annotations

from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)


class TestCompositeExplanation:
    """Fix C: composite unit_out.content.explanation is populated."""

    def test_composite_explanation_in_unit_out(self):
        lines = [f"L{i}" for i in range(1, 30)]
        lines[0] = "阅读材料。"
        lines[1] = "1. 第一题。"
        lines[2] = "A. 甲"
        lines[3] = "B. 乙"
        lines[4] = "C. 丙"
        lines[5] = "D. 丁"
        lines[6] = "2. 第二题。"
        lines[7] = "A. 甲"
        lines[8] = "B. 乙"
        lines[9] = "C. 丙"
        lines[10] = "D. 丁"
        lines[20] = "【答案】"
        lines[21] = "1. A"
        lines[22] = "2. B"
        lines[25] = "【解析】第一题考查…"
        lines[26] = "第二题考查…"
        man = {
            "units": [{
                "unit_id": "U1-2",
                "unit_type": "composite_question",
                "question_numbers": [1, 2],
                "original_question_type": "single_choice",
                "material_lines": [1, 1],
                "questions_lines": [2, 11],
                "options_lines": [3, 11],
                "answer_lines": [21, 22],
                "explanation_lines": [26, 27],
                "options": [{"label": l} for l in "ABCD"],
            }]
        }
        bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="a" * 64, manifest_identity_version=2)
        u = payload["semantic_units"][0]
        assert u["unit_type"] == "composite_unit"
        content = u.get("content") or {}
        assert "explanation" in content, f"composite explanation missing: {content.keys()}"
        expl = content["explanation"]
        assert expl["explanation_lines"] == [26, 27]
        # Must not damage other structures
        assert u.get("sub_questions") is not None
        assert u.get("shared_components") is not None

    def test_composite_no_explanation_no_crash(self):
        lines = [f"L{i}" for i in range(1, 20)]
        lines[0] = "材料。"
        lines[1] = "1. 题一。"
        lines[2] = "A. 甲"
        lines[3] = "B. 乙"
        lines[4] = "C. 丙"
        lines[5] = "D. 丁"
        lines[10] = "【答案】"
        lines[11] = "1. A"
        man = {
            "units": [{
                "unit_id": "U1",
                "unit_type": "composite_question",
                "question_numbers": [1],
                "original_question_type": "single_choice",
                "material_lines": [1, 1],
                "questions_lines": [2, 6],
                "options_lines": [3, 6],
                "answer_lines": [11, 11],
                "options": [{"label": l} for l in "ABCD"],
            }]
        }
        bound = bind_units_from_manifest(man, lines, source_content_sha256="b" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="b" * 64, manifest_identity_version=2)
        u = payload["semantic_units"][0]
        content = u.get("content") or {}
        assert "explanation" not in content

    def test_standalone_explanation_still_works(self):
        """Fix C must not break standalone explanation path."""
        lines = ["1. stem", "A. a", "B. b", "C. c", "D. d", "【答案】A", "【解析】explanation here"]
        man = {"units": [{
            "unit_id": "Q1", "unit_type": "standalone_question",
            "question_numbers": [1], "original_question_type": "single_choice",
            "stem_lines": [1, 1], "options_lines": [2, 5],
            "answer_lines": [6, 6], "explanation_lines": [7, 7],
            "options": [{"label": l} for l in "ABCD"],
        }]}
        bound = bind_units_from_manifest(man, lines, source_content_sha256="c" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="c" * 64, manifest_identity_version=2)
        u = payload["semantic_units"][0]
        assert u["content"]["explanation"]["explanation_lines"] == [7, 7]
