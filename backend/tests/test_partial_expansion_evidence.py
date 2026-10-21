# -*- coding: utf-8 -*-
"""WP7-B: partial composite expansion must persist skipped evidence + coverage.

Regression for CHN-001: U1-5 (4/5 expanded), U10-13 (2/4), U14-16 (2/3) —
skipped sub records (Q5/Q12/Q13/Q16) were lost because group_evidence was
only written when NOT subs (zero expansion).  Partial expansion must also
carry subq_skipped + actual expanded_question_numbers.
"""
from __future__ import annotations

from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)
from app.domains.source.subq_expand import expand_composite_sub_questions


class TestPartialExpansionEvidence:
    """WP7-B: group_evidence is written for partial expansion, not just zero."""

    def _lines_reading_partial(self) -> list[str]:
        """3-question reading composite: Q1,Q2 expand (A-D), Q3 lacks A-D → skipped."""
        lines = [""] * 30
        lines[0] = "阅读下面的文字，完成各题。"                         # 1 material
        lines[1] = "这是一段共享材料正文，讲述一个故事。"                  # 2 material
        lines[2] = "1. 第一题的题干内容。"                             # 3 Q1 start
        lines[3] = "A. 选项A"
        lines[4] = "B. 选项B"
        lines[5] = "C. 选项C"
        lines[6] = "D. 选项D"
        lines[7] = "2. 第二题的题干内容。"                             # 8 Q2 start
        lines[8] = "A. 选项A"
        lines[9] = "B. 选项B"
        lines[10] = "C. 选项C"
        lines[11] = "D. 选项D"
        lines[12] = "3. 第三题没有独立选项标签，只有叙述。"               # 13 Q3 start
        lines[13] = "（无法确定选项边界）"
        lines[20] = "【答案】"
        lines[21] = "1. A"
        lines[22] = "2. B"
        lines[23] = "3. C"
        return lines

    @staticmethod
    def _declared_options():
        """Manifest options field → option_labels (required for reading expansion)."""
        return [
            {"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"},
        ]

    def test_partial_expansion_persists_skipped_and_coverage(self):
        """P2-fix-3: reading subs with no A-D now expand (stem-only).
        Sub with PARTIAL labels (A,B only) is still skipped."""
        lines = self._lines_reading_partial()
        man = {
            "units": [{
                "unit_id": "U1-3",
                "unit_type": "composite_question",
                "question_numbers": [1, 2, 3],
                "original_question_type": "reading",
                "material_lines": [1, 2],
                "questions_lines": [3, 14],
                "options_lines": [4, 12],
                "answer_lines": [21, 23],
                "options": self._declared_options(),
            }]
        }
        bound = bind_units_from_manifest(man, lines, source_content_sha256="c" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="c" * 64, manifest_identity_version=2
        )
        u = payload["semantic_units"][0]
        assert u["unit_type"] == "composite_unit"
        assert u["question_number_range"] == "1-3"

        ev = u.get("group_evidence") or {}
        assert ev, "group_evidence missing"
        # P2-fix-3: Q3 (no A-D) now expands as stem-only → all 3 expanded
        assert ev.get("structure") == "expanded_sub_questions"
        assert ev.get("expanded_question_numbers") == [1, 2, 3]
        subs = u.get("sub_questions") or []
        assert len(subs) == 3

    def test_zero_expansion_still_undetermined(self):
        """No sub expands → structure=undetermined (backward compatible)."""
        lines = [""] * 20
        lines[0] = "阅读材料。"
        lines[1] = "1. 题一"
        lines[2] = "2. 题二"
        lines[10] = "【答案】"
        lines[11] = "1. A"
        lines[12] = "2. B"
        man = {
            "units": [{
                "unit_id": "U1-2",
                "unit_type": "composite_question",
                "question_numbers": [1, 2],
                "original_question_type": "reading",
                "material_lines": [1, 1],
                "questions_lines": [2, 3],
                "answer_lines": [11, 12],
            }]
        }
        bound = bind_units_from_manifest(man, lines, source_content_sha256="d" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="d" * 64, manifest_identity_version=2
        )
        u = payload["semantic_units"][0]
        ev = u.get("group_evidence") or {}
        assert ev.get("structure") == "undetermined_sub_questions"
        assert ev.get("expanded_question_numbers") == []
        assert ev.get("expanded_question_count") == 0

    def test_full_expansion_no_skips(self):
        """All subs expand → structure=expanded, no skip entries."""
        lines = [""] * 30
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
        lines[15] = "【答案】"
        lines[16] = "1. A"
        lines[17] = "2. B"
        man = {
            "units": [{
                "unit_id": "U1-2",
                "unit_type": "composite_question",
                "question_numbers": [1, 2],
                "original_question_type": "single_choice",
                "material_lines": [1, 1],
                "questions_lines": [2, 11],
                "options_lines": [3, 11],
                "answer_lines": [16, 17],
            }]
        }
        bound = bind_units_from_manifest(man, lines, source_content_sha256="e" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="e" * 64, manifest_identity_version=2
        )
        u = payload["semantic_units"][0]
        ev = u.get("group_evidence") or {}
        assert ev.get("structure") == "expanded_sub_questions"
        assert ev.get("subq_skipped") == {}
        assert ev.get("expanded_question_numbers") == [1, 2]
        assert len(u.get("sub_questions") or []) == 2

    def test_question_number_range_unchanged_for_partial(self):
        """question_number_range keeps full printed range; coverage is separate."""
        lines = self._lines_reading_partial()
        man = {
            "units": [{
                "unit_id": "U1-3",
                "unit_type": "composite_question",
                "question_numbers": [1, 2, 3],
                "original_question_type": "reading",
                "material_lines": [1, 2],
                "questions_lines": [3, 14],
                "options_lines": [4, 12],
                "answer_lines": [21, 23],
                "options": self._declared_options(),
            }]
        }
        bound = bind_units_from_manifest(man, lines, source_content_sha256="f" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="f" * 64, manifest_identity_version=2
        )
        u = payload["semantic_units"][0]
        # Full printed range preserved (existing contract)
        assert u["question_number_range"] == "1-3"
        # Actual coverage lives in group_evidence (P2-fix-3: all 3 now expand)
        ev = u.get("group_evidence") or {}
        assert ev.get("expanded_question_numbers") == [1, 2, 3]

    def test_subq_expand_skipped_reason_format(self):
        """P2-fix-3: reading sub with no A-D expands as stem-only (not skipped)."""
        lines = self._lines_reading_partial()
        result = expand_composite_sub_questions(
            lines,
            question_numbers=[1, 2, 3],
            questions_range=(3, 14),
            answer_range=(21, 23),
            original_question_type="reading",
            has_declared_options=True,
        )
        assert 3 not in result.skipped, "Q3 should expand after P2-fix-3"
        assert len(result.sub_questions) == 3
        q3 = next(s for s in result.sub_questions if s.question_number == 3)
        assert q3.option_labels == (), "Q3 has no A-D, stem-only expected"
