"""Evidence Promotion Contract Phase 1 — comprehensive tests.

Phase 1 Hardening: Updated for new interface.
- ValidationEvent uses `checks: tuple[CheckResult, ...]` instead of checks_passed/checks_failed
- checks_passed/checks_failed are now derived properties
- AppendOnlyEventLog enforces append-only at data structure level
- State machine enforcement: REJECTED terminal, INVALIDATED requires VALIDATED
- reference_ids links ValidationEvent to EvidenceReference
"""

from __future__ import annotations

import uuid
from dataclasses import FrozenInstanceError

import pytest

from app.domains.evidence.models import (
    VALID_PRODUCER_TYPES,
    VALID_VALIDATION_METHODS,
    VALID_VALIDATION_RESULTS,
    AppendOnlyEventLog,
    CheckResult,
    EvidenceReference,
    ProposerIdentity,
    ValidationEvent,
)
from app.domains.evidence.promotion import (
    EvidencePromotionService,
    create_evidence_references,
    record_validation_event,
)
from app.domains.resolver.span import ResolvedRun, ResolvedSpan
from app.repositories.evidence_repository import EvidenceRepository
from tests.eb008_helpers import rejected_gate_decision, seed_candidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_span(
    span_id: str = "sp-test-1",
    role: str = "answer",
    svid: uuid.UUID | None = None,
) -> ResolvedSpan:
    return ResolvedSpan(
        span_id=span_id,
        source_version_id=svid or uuid.uuid4(),
        role=role,
        start_line_ref="P001L001",
        end_line_ref="P001L003",
        line_refs=("P001L001", "P001L002", "P001L003"),
        granularity="line",
        start_offset=None,
        end_offset=None,
        text_hash="abc123",
        resolution_status="exact",
    )


def _make_run(*spans: ResolvedSpan) -> ResolvedRun:
    return ResolvedRun(
        source_version_id=spans[0].source_version_id if spans else uuid.uuid4(),
        resolved_spans=spans,
    )


def _make_proposer(producer_type: str = "llm") -> ProposerIdentity:
    return ProposerIdentity(producer_type=producer_type)


def _make_check(check_id: str = "TEST", result: str = "pass") -> CheckResult:
    return CheckResult(check_id=check_id, result=result)


def _make_event(
    claim_id: str = "claim-1",
    result: str = "validated",
    checks: tuple[CheckResult, ...] | None = None,
    method: str = "frozen_header_rule",
    reference_ids: tuple[str, ...] = (),
) -> ValidationEvent:
    return ValidationEvent(
        event_id=f"ve-{claim_id}-{uuid.uuid4().hex[:8]}",
        claim_id=claim_id,
        validation_result=result,
        checks=checks or (_make_check(),),
        validation_method=method,
        validator="gate/v1",
        reference_ids=reference_ids,
    )


def _gate_auto_approve() -> dict:
    return {
        "decision": "auto_approve",
        "reasons": ["strict-auto: all answers verified_correct=true"],
        "layers": {
            "structural": {"status": "pass", "reasons": []},
            "provenance": {"status": "pass", "reasons": []},
            "semantic": {"status": "pass", "reasons": []},
            "admission": {"status": "pass", "reasons": ["strict-auto"]},
        },
    }


def _gate_rejected() -> dict:
    return {
        "decision": "rejected",
        "reasons": ["leaf 'u1' answer span overlaps explanation region"],
        "layers": {
            "structural": {"status": "pass", "reasons": []},
            "provenance": {"status": "fail", "reasons": ["text_hash mismatch"]},
            "semantic": {"status": "pass", "reasons": []},
            "admission": {"status": "fail", "reasons": ["overlap"]},
        },
    }


# ---------------------------------------------------------------------------
# ProposerIdentity
# ---------------------------------------------------------------------------

class TestProposerIdentity:
    def test_valid_producer_types(self):
        for pt in VALID_PRODUCER_TYPES:
            p = ProposerIdentity(producer_type=pt)
            assert p.producer_type == pt

    def test_invalid_producer_type_raises(self):
        with pytest.raises(ValueError, match="Invalid producer_type"):
            ProposerIdentity(producer_type="invalid_type")

    def test_with_model_and_version(self):
        p = ProposerIdentity(producer_type="llm", model="qwen3.5-9b", pipeline_version="v1.0")
        assert p.model == "qwen3.5-9b"

    def test_frozen(self):
        p = ProposerIdentity(producer_type="ocr")
        with pytest.raises(FrozenInstanceError):
            p.producer_type = "llm"


# ---------------------------------------------------------------------------
# EvidenceReference
# ---------------------------------------------------------------------------

class TestEvidenceReference:
    def test_from_resolved_span(self):
        span = _make_span()
        ref = EvidenceReference.from_resolved_span(span, _make_proposer())
        assert ref.reference_id == f"er-{span.span_id}"
        assert ref.span_id == span.span_id
        assert ref.proposed_role == span.role

    def test_frozen(self):
        ref = EvidenceReference.from_resolved_span(_make_span(), _make_proposer())
        with pytest.raises(FrozenInstanceError):
            ref.proposed_role = "explanation"

    def test_no_evidence_authority_field(self):
        ref = EvidenceReference.from_resolved_span(_make_span(), _make_proposer())
        assert not hasattr(ref, "validated")
        assert not hasattr(ref, "authority")


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------

class TestCheckResult:
    def test_valid(self):
        c = CheckResult(check_id="TEXT_HASH_MATCH", result="pass")
        assert c.check_id == "TEXT_HASH_MATCH"
        assert c.result == "pass"

    def test_with_detail(self):
        c = CheckResult(check_id="ROLE_OVERLAP", result="fail", detail="overlaps explanation")
        assert c.detail == "overlaps explanation"

    def test_invalid_result_raises(self):
        with pytest.raises(ValueError, match="Invalid check result"):
            CheckResult(check_id="X", result="unknown")

    def test_frozen(self):
        c = CheckResult(check_id="X", result="pass")
        with pytest.raises(FrozenInstanceError):
            c.result = "fail"


# ---------------------------------------------------------------------------
# ValidationEvent
# ---------------------------------------------------------------------------

class TestValidationEvent:
    def test_valid_results(self):
        for result in VALID_VALIDATION_RESULTS:
            event = _make_event(result=result)
            assert event.validation_result == result

    def test_invalid_result_raises(self):
        with pytest.raises(ValueError, match="Invalid validation_result"):
            _make_event(result="unknown")

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="Invalid validation_method"):
            _make_event(method="llm_verification")

    def test_frozen(self):
        event = _make_event()
        with pytest.raises(FrozenInstanceError):
            event.validation_result = "rejected"

    def test_is_validated(self):
        event = _make_event(result="validated")
        assert event.is_validated is True
        assert event.is_terminal is False

    def test_is_terminal_rejected(self):
        event = _make_event(result="rejected")
        assert event.is_terminal is True

    def test_checks_passed_derived(self):
        checks = (
            CheckResult(check_id="A", result="pass"),
            CheckResult(check_id="B", result="fail"),
            CheckResult(check_id="C", result="pass"),
        )
        event = _make_event(checks=checks)
        assert event.checks_passed == ("A", "C")
        assert event.checks_failed == ("B",)

    def test_reference_ids(self):
        event = _make_event(reference_ids=("er-sp-1", "er-sp-2"))
        assert event.reference_ids == ("er-sp-1", "er-sp-2")


# ---------------------------------------------------------------------------
# AppendOnlyEventLog
# ---------------------------------------------------------------------------

class TestAppendOnlyEventLog:
    def test_append(self):
        log = AppendOnlyEventLog()
        e1 = _make_event(claim_id="c1")
        e2 = _make_event(claim_id="c2")
        log.append(e1)
        log.append(e2)
        assert len(log) == 2

    def test_events_is_tuple(self):
        log = AppendOnlyEventLog()
        log.append(_make_event())
        assert isinstance(log.events, tuple)

    def test_no_clear_method(self):
        log = AppendOnlyEventLog()
        assert not hasattr(log, "clear")

    def test_for_claim(self):
        log = AppendOnlyEventLog()
        log.append(_make_event(claim_id="c1"))
        log.append(_make_event(claim_id="c2"))
        assert len(log.for_claim("c1")) == 1
        assert len(log.for_claim("c2")) == 1


# ---------------------------------------------------------------------------
# create_evidence_references
# ---------------------------------------------------------------------------

class TestCreateEvidenceReferences:
    def test_from_empty_run(self):
        assert create_evidence_references(_make_run(), _make_proposer()) == ()

    def test_from_multiple_spans(self):
        spans = (_make_span("sp-1", "stem"), _make_span("sp-2", "answer"))
        refs = create_evidence_references(_make_run(*spans), _make_proposer())
        assert len(refs) == 2


# ---------------------------------------------------------------------------
# record_validation_event
# ---------------------------------------------------------------------------

class TestRecordValidationEvent:
    def test_auto_approve_maps_to_validated(self):
        event = record_validation_event(claim_id="c1", gate_decision=_gate_auto_approve())
        assert event is not None
        assert event.validation_result == "validated"

    def test_rejected_maps_to_rejected(self):
        event = record_validation_event(claim_id="c1", gate_decision=_gate_rejected())
        assert event is not None
        assert event.validation_result == "rejected"

    def test_pending_review_returns_none(self):
        event = record_validation_event(
            claim_id="c1", gate_decision={"decision": "pending_review"}
        )
        assert event is None

    def test_validation_method_derived_from_layers(self):
        """High 4 fix: validation_method derived from gate layers."""
        # Provenance fail → byte_proven
        event = record_validation_event(claim_id="c1", gate_decision=_gate_rejected())
        assert event.validation_method == "byte_proven"
        # All pass → frozen_header_rule
        event = record_validation_event(claim_id="c1", gate_decision=_gate_auto_approve())
        assert event.validation_method == "frozen_header_rule"

    def test_structured_checks(self):
        """High 5 fix: checks are structured CheckResult objects."""
        event = record_validation_event(claim_id="c1", gate_decision=_gate_auto_approve())
        check_ids = [c.check_id for c in event.checks]
        assert "STRUCTURAL_CONSISTENCY" in check_ids
        assert "BYTE_PROVEN" in check_ids
        assert "STRICT_AUTO_GRAMMAR" in check_ids

    def test_reference_ids_passed_through(self):
        """Critical 3 fix: reference_ids links ValidationEvent to EvidenceReference."""
        event = record_validation_event(
            claim_id="c1",
            gate_decision=_gate_auto_approve(),
            reference_ids=("er-sp-1", "er-sp-2"),
        )
        assert event.reference_ids == ("er-sp-1", "er-sp-2")


# ---------------------------------------------------------------------------
# EvidencePromotionService (EB-008 §5.1: DB-backed via EvidenceRepository)
# ---------------------------------------------------------------------------

class TestEvidencePromotionService:
    async def test_create_references(self, session):
        service = EvidencePromotionService(EvidenceRepository(session))
        run = _make_run(_make_span("sp-1"), _make_span("sp-2"))
        refs = service.create_references(run, _make_proposer())
        assert len(refs) == 2

    async def test_record_validation_validated(self, session):
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        rec = await service.record_validation(
            "claim-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert rec is not None
        assert rec.validation_result == "validated"
        # EB-008：事件持久化到 validation_events（非内存）
        rows = await EvidenceRepository(session).find_events_for_claim(cand.id, "claim-1")
        assert len(rows) == 1

    async def test_append_only_enforced(self, session):
        """EB-008 §5.5：Repository 无 update/delete；唯一写入口 append_event。"""
        repo = EvidenceRepository(session)
        assert not hasattr(repo, "update_event")
        assert not hasattr(repo, "delete_event")
        from app.repositories.base import AppendOnlyViolation
        from app.repositories.evidence_repository import (
            delete_validation_event,
            update_validation_event,
        )
        with pytest.raises(AppendOnlyViolation):
            await update_validation_event()
        with pytest.raises(AppendOnlyViolation):
            await delete_validation_event()

    async def test_state_machine_rejected_terminal(self, session):
        """Critical 2 fix: REJECTED is terminal（DB 路径同状态机）。"""
        sv, _ann, cand = await seed_candidate(session, gate=rejected_gate_decision())
        service = EvidencePromotionService(EvidenceRepository(session))
        await service.record_validation(
            "claim-1", _gate_rejected(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        with pytest.raises(ValueError, match="terminal"):
            await service.record_validation(
                "claim-1", _gate_auto_approve(),
                candidate_id=cand.id, source_version_id=sv.id,
            )

    async def test_replay_same_result_is_noop(self, session):
        """EB-008 R4：replay 同结果 → no-op，不新增行（replay 永不改变 Authority）。"""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        first = await service.record_validation(
            "claim-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        second = await service.record_validation(
            "claim-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert first.id == second.id
        rows = await EvidenceRepository(session).find_events_for_claim(cand.id, "claim-1")
        assert len(rows) == 1

    async def test_is_evidence_validated_true(self, session):
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        await service.record_validation(
            "claim-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.is_evidence_validated(cand.id, "claim-1") is True

    async def test_is_evidence_validated_false_rejected(self, session):
        sv, _ann, cand = await seed_candidate(session, gate=rejected_gate_decision())
        service = EvidencePromotionService(EvidenceRepository(session))
        await service.record_validation(
            "claim-1", _gate_rejected(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.is_evidence_validated(cand.id, "claim-1") is False

    async def test_is_evidence_validated_superseded_by_invalidation(self, session):
        from datetime import datetime, timedelta, timezone

        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        await service.record_validation(
            "claim-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.is_evidence_validated(cand.id, "claim-1") is True
        # EB-008 §5.4：VALIDATED → INVALIDATED 后投影为 invalidated（latest wins）
        later_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        invalidation = ValidationEvent(
            event_id="ve-inval-1",
            claim_id="claim-1",
            validation_result="invalidated",
            checks=(),
            validation_method="structural_consistency",
            validator="system/v1",
            validated_at=later_time,
        )
        await EvidenceRepository(session).append_event(
            invalidation,
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.is_evidence_validated(cand.id, "claim-1") is False

    async def test_get_references_for_ids(self, session):
        """Critical 3 fix: can trace from ValidationEvent back to EvidenceReferences."""
        service = EvidencePromotionService(EvidenceRepository(session))
        span = _make_span("sp-1")
        service.create_references(_make_run(span), _make_proposer())
        refs = service.get_references_for_ids(("er-sp-1",))
        assert len(refs) == 1
        assert refs[0].reference_id == "er-sp-1"


# ---------------------------------------------------------------------------
# Frozen Rules
# ---------------------------------------------------------------------------

class TestFrozenRules:
    def test_r1_resolved_span_no_semantic_role_pollution(self):
        span = _make_span(role="answer")
        ref = EvidenceReference.from_resolved_span(span, _make_proposer())
        assert ref.proposed_role == "answer"
        assert not hasattr(span, "proposer")
        assert not hasattr(span, "validated")

    def test_r2_proposal_no_authority(self):
        ref = EvidenceReference.from_resolved_span(_make_span(), _make_proposer())
        assert not hasattr(ref, "validated")
        assert not hasattr(ref, "authority")

    async def test_r4_only_validation_produces_authority(self, session):
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        assert await service.is_evidence_validated(cand.id, "claim-1") is False
        await service.record_validation(
            "claim-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.is_evidence_validated(cand.id, "claim-1") is True


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestGateIntegration:
    async def test_full_flow_validated_with_linking(self, session):
        """Full flow with Critical 3 fix: ValidationEvent ↔ EvidenceReference linking."""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        span = _make_span("sp-answer-1", "answer")
        service.create_references(_make_run(span), ProposerIdentity(producer_type="llm"))

        rec = await service.record_validation(
            "unit-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
            reference_ids=("er-sp-answer-1",),
        )
        assert rec is not None
        assert rec.validation_result == "validated"
        assert await service.is_evidence_validated(cand.id, "unit-1") is True
        # Critical 3: trace back to references
        traced = service.get_references_for_ids(tuple(rec.reference_ids or ()))
        assert len(traced) == 1
        assert traced[0].span_id == "sp-answer-1"

    async def test_multiple_claims_independent(self, session):
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        await service.record_validation(
            "unit-1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        await service.record_validation(
            "unit-2", _gate_rejected(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.record_validation(
            "unit-3", {"decision": "pending_review"},
            candidate_id=cand.id, source_version_id=sv.id,
        ) is None

        assert await service.is_evidence_validated(cand.id, "unit-1") is True
        assert await service.is_evidence_validated(cand.id, "unit-2") is False
        rows = await EvidenceRepository(session).find_events_for_candidate(cand.id)
        assert len(rows) == 2
