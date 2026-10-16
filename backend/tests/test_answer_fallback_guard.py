# -*- coding: utf-8 -*-
"""E2E-013 data-safety: answer-zone fallback must not force-bind when
manifest declares answer_evidence.type=absent AND a validation issue exists.
Questions must be KEPT (unresolved/pending), not deleted from the pipeline."""
from __future__ import annotations

from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)
from app.domains.resolver.reference import _answer_target, ResolveTarget


def _make_manifest(units: list, validation_issues: list | None = None) -> dict:
    return {
        "units": units,
        "annotation_meta": {"validation_issues": validation_issues or []},
    }


def _make_unit(uid: str, qns: list, *, answer_evidence: dict | None = None) -> dict:
    return {
        "unit_id": uid,
        "unit_type": "standalone_question",
        "question_numbers": qns,
        "original_question_type": "vocabulary_fill",
        "stem_lines": [1, 1],
        "answer_lines": None,
        "answer_evidence": answer_evidence,
    }


SOURCE = [
    "56. upset",
    "57. recognize",
    "58. destroyed",
    "参考答案",
    "56. upset 57. recognize 58. destroyed",
]


class TestAnswerFallbackBlocked:
    def test_absent_plus_validation_issue_blocks_fallback(self):
        """U53-like: absent + validation issue → answer content exists but
        is empty (no wrong data). Question is kept for human review."""
        man = _make_manifest(
            [_make_unit("U53", [53], answer_evidence={"type": "absent", "lines": None, "value": None})],
            validation_issues=["U53: 无 answer_lines（题号 [53]）"],
        )
        bound = bind_units_from_manifest(man, SOURCE, source_content_sha256="x")
        assert len(bound) == 1
        assert bound[0].answer_fallback_blocked is True

        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="x", manifest_identity_version=2
        )
        content = payload["semantic_units"][0]["content"]
        # Answer content IS present (for IR readiness) but marked via fallback
        assert "answer" in content
        # Stem is present — question is kept
        assert "stem" in content

    def test_absent_without_validation_issue_allows_fallback(self):
        """absent but NO validation issue → fallback allowed."""
        man = _make_manifest(
            [_make_unit("U54", [54], answer_evidence={"type": "absent", "lines": None, "value": None})],
            validation_issues=[],
        )
        bound = bind_units_from_manifest(man, SOURCE, source_content_sha256="x")
        assert bound[0].answer_fallback_blocked is False

        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="x", manifest_identity_version=2
        )
        ans = payload["semantic_units"][0]["content"]["answer"]
        assert ans.get("answer_zone") is not None
        assert ans.get("fallback_blocked") is False

    def test_normal_answer_evidence_not_blocked(self):
        """Normal answer evidence (not absent) → fallback always allowed."""
        man = _make_manifest(
            [_make_unit("U55", [55], answer_evidence={"type": "answer_lines", "lines": [4, 4], "value": "58. destroyed"})],
            validation_issues=["U55: some other issue"],
        )
        bound = bind_units_from_manifest(man, SOURCE, source_content_sha256="x")
        assert bound[0].answer_fallback_blocked is False

    def test_no_answer_evidence_key_not_blocked(self):
        """Legacy manifest without answer_evidence → fallback allowed."""
        man = _make_manifest([_make_unit("U56", [56], answer_evidence=None)], validation_issues=[])
        bound = bind_units_from_manifest(man, SOURCE, source_content_sha256="x")
        assert bound[0].answer_fallback_blocked is False

    def test_resolve_target_carries_blocked_flag(self):
        """fallback_blocked flows through to ResolveTarget."""
        targets = []
        _answer_target(targets, "U53", {
            "answer_zone": "answer_table",
            "question_label": 53,
            "fallback_blocked": True,
        })
        assert len(targets) == 1
        assert targets[0].answer_fallback_blocked is True

    def test_resolve_target_default_not_blocked(self):
        """Without fallback_blocked → default False."""
        targets = []
        _answer_target(targets, "U54", {
            "answer_zone": "answer_table",
            "question_label": 54,
        })
        assert len(targets) == 1
        assert targets[0].answer_fallback_blocked is False


class TestUnitIdMatcher:
    """Q1 must not match Q10; U5 must not match U56."""

    def _blocked(self, uid: str, issues: list) -> bool:
        import re
        _uid_re = re.compile(rf"^{re.escape(uid)}(?:[:：\s]|$)")
        return any(_uid_re.match(str(issue).lstrip("! ")) for issue in issues)

    def test_q1_not_matched_by_q10_issue(self):
        assert self._blocked("Q1", ["Q10: 无 answer_lines"]) is False
        assert self._blocked("Q1", ["Q1: 无 answer_lines"]) is True

    def test_u5_not_matched_by_u56_issue(self):
        assert self._blocked("U5", ["U56: 无 answer_lines"]) is False
        assert self._blocked("U5", ["U5: 无 answer_lines"]) is True

    def test_q10_matched_by_q10_issue(self):
        assert self._blocked("Q10", ["Q10: 无 answer_lines"]) is True
        assert self._blocked("Q10", ["Q1: 无 answer_lines"]) is False

    def test_u56_matched_by_u56_issue(self):
        assert self._blocked("U56", ["U56: 无 answer_lines"]) is True
        assert self._blocked("U56", ["U5: 无 answer_lines"]) is False

    def test_bang_prefix_tolerated(self):
        assert self._blocked("U53", ["! U53: 无 answer_lines"]) is True

    def test_fullwidth_colon_tolerated(self):
        assert self._blocked("U53", ["U53：无 answer_lines"]) is True
