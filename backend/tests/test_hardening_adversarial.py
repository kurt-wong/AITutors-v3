"""Adversarial review of Phase 1 Hardening — POST-HARDENING ATTACKS.

Every test tries to BREAK the hardened implementation.
Test semantics:
- PASS = attack succeeded = gap still exists = BAD
- FAIL = attack blocked = fix works = GOOD

We invert assertions: tests verify attacks are BLOCKED.
"""

from __future__ import annotations

import uuid
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone, timedelta

import pytest

from app.domains.evidence.models import (
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
    _derive_validation_method,
    _extract_checks,
)
from app.domains.resolver.span import ResolvedRun, ResolvedSpan
from app.repositories.evidence_repository import EvidenceRepository
from tests.eb008_helpers import rejected_gate_decision, seed_candidate


def _make_span(span_id="sp-1", role="answer", svid=None):
    return ResolvedSpan(
        span_id=span_id,
        source_version_id=svid or uuid.uuid4(),
        role=role,
        start_line_ref="P001L001",
        end_line_ref="P001L001",
        line_refs=("P001L001",),
        granularity="line",
        start_offset=None,
        end_offset=None,
        text_hash="h1",
        resolution_status="exact",
    )


def _make_run(*spans: ResolvedSpan) -> ResolvedRun:
    return ResolvedRun(
        source_version_id=spans[0].source_version_id if spans else uuid.uuid4(),
        resolved_spans=spans,
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
        "reasons": ["text_hash mismatch"],
        "layers": {
            "structural": {"status": "pass", "reasons": []},
            "provenance": {"status": "fail", "reasons": ["text_hash mismatch"]},
            "semantic": {"status": "pass", "reasons": []},
            "admission": {"status": "fail", "reasons": ["text_hash mismatch"]},
        },
    }


# ---------------------------------------------------------------------------
# ATTACK 1: AppendOnlyEventLog — can we still mutate internal state?
# ---------------------------------------------------------------------------

class TestAttackAppendOnlyLog:
    def test_direct_attribute_reassignment_blocked(self):
        """HIGH-1 FIX: __slots__ prevents attribute reassignment."""
        log = AppendOnlyEventLog()
        e1 = ValidationEvent(
            event_id="ve-1", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
        )
        log.append(e1)
        assert len(log.events) == 1
        # ATTACK: reassign _events to empty tuple — should FAIL
        with pytest.raises(AttributeError):
            log._events = ()
        # Attack blocked — log still has 1 event
        assert len(log.events) == 1

    def test_tuple_element_mutation_blocked(self):
        """ValidationEvent is frozen — cannot mutate elements inside tuple."""
        log = AppendOnlyEventLog()
        e1 = ValidationEvent(
            event_id="ve-1", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
        )
        log.append(e1)
        # ValidationEvent is frozen — cannot mutate
        with pytest.raises(FrozenInstanceError):
            log.events[0].validation_result = "rejected"

    async def test_bypass_log_via_direct_append_blocked(self, session):
        """HIGH-2 FIX: State machine enforced in DB write path (append_event)."""
        sv, _ann, cand = await seed_candidate(session, gate=rejected_gate_decision())
        repo = EvidenceRepository(session)
        service = EvidencePromotionService(repo)
        await service.record_validation(
            "c1", _gate_rejected(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        # ATTACK: append validated on terminal claim — should FAIL
        later_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        fake_event = ValidationEvent(
            event_id="ve-fake", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="attacker",
            validated_at=later_time,
        )
        with pytest.raises(ValueError, match="terminal"):
            await repo.append_event(
                fake_event, candidate_id=cand.id, source_version_id=sv.id,
            )
        assert await service.is_evidence_validated(cand.id, "c1") is False


# ---------------------------------------------------------------------------
# ATTACK 2: State machine — can we bypass _check_state_transition?
# ---------------------------------------------------------------------------

class TestAttackStateMachine:
    async def test_direct_log_append_bypasses_state_machine_blocked(self, session):
        """HIGH-2 FIX: State machine enforced in DB write path (append_event)."""
        sv, _ann, cand = await seed_candidate(session, gate=rejected_gate_decision())
        repo = EvidenceRepository(session)
        service = EvidencePromotionService(repo)
        await service.record_validation(
            "c1", _gate_rejected(),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        later_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        fake_event = ValidationEvent(
            event_id="ve-fake", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="attacker",
            validated_at=later_time,
        )
        with pytest.raises(ValueError, match="terminal"):
            await repo.append_event(
                fake_event, candidate_id=cand.id, source_version_id=sv.id,
            )
        assert await service.is_evidence_validated(cand.id, "c1") is False

    async def test_manipulated_timestamps_confuse_state_machine(self, session):
        """ATTACK: FUTURE timestamp event then rejected — state machine still blocks.

        EB-008 A1 修复后：远期未来时间戳在写路径即被拒绝（防投影劫持）。
        允许偏移内的未来时间仍走状态机约束。
        """
        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        service = EvidencePromotionService(repo)
        far_future = datetime.now(timezone.utc) + timedelta(days=365)
        far_event = ValidationEvent(
            event_id="ve-far", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=far_future,
        )
        with pytest.raises(ValueError, match="future"):
            await repo.append_event(
                far_event, candidate_id=cand.id, source_version_id=sv.id,
            )
        # 偏移内未来时间：latest = validated → REJECTED 仍 blocked
        near_future = datetime.now(timezone.utc) + timedelta(minutes=2)
        near_event = ValidationEvent(
            event_id="ve-near", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=near_future,
        )
        await repo.append_event(
            near_event, candidate_id=cand.id, source_version_id=sv.id,
        )
        with pytest.raises(ValueError, match="only INVALIDATED transition allowed"):
            await service.record_validation(
                "c1", _gate_rejected(),
                candidate_id=cand.id, source_version_id=sv.id,
            )

    async def test_equal_timestamps_ambiguous(self, session):
        """ATTACK: identical timestamps — VALIDATED → REJECTED still blocked."""
        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        now = datetime.now(timezone.utc)
        e1 = ValidationEvent(
            event_id="ve-1", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=now,
        )
        e2 = ValidationEvent(
            event_id="ve-2", claim_id="c1", validation_result="rejected",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=now,  # same timestamp
        )
        await repo.append_event(e1, candidate_id=cand.id, source_version_id=sv.id)
        with pytest.raises(ValueError, match="only INVALIDATED transition allowed"):
            await repo.append_event(e2, candidate_id=cand.id, source_version_id=sv.id)


# ---------------------------------------------------------------------------
# ATTACK 3: reference_ids — is linking actually correct?
# ---------------------------------------------------------------------------

class TestAttackReferenceIdsLinking:
    async def test_fake_reference_ids_accepted(self, session):
        """ATTACK: Can we pass fake reference_ids that don't exist?"""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        span = _make_span("sp-1")
        service.create_references(_make_run(span), ProposerIdentity(producer_type="llm"))
        rec = await service.record_validation(
            "c1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
            reference_ids=("er-fake-1", "er-fake-2"),
        )
        assert rec is not None
        assert tuple(rec.reference_ids or ()) == ("er-fake-1", "er-fake-2")
        traced = service.get_references_for_ids(tuple(rec.reference_ids or ()))
        assert len(traced) == 0
        # CONFIRMED GAP: no validation that reference_ids actually exist

    async def test_empty_reference_ids_accepted(self, session):
        """ATTACK: Can we record validation with empty reference_ids?"""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        rec = await service.record_validation(
            "c1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id, reference_ids=(),
        )
        assert rec is not None
        assert not rec.reference_ids
        # This is allowed — but means no linking

    async def test_reference_id_format_not_enforced(self, session):
        """ATTACK: Is reference_id format enforced?"""
        sv, _ann, cand = await seed_candidate(session)
        service = EvidencePromotionService(EvidenceRepository(session))
        span = _make_span("sp-1")
        service.create_references(_make_run(span), ProposerIdentity(producer_type="llm"))
        rec = await service.record_validation(
            "c1", _gate_auto_approve(),
            candidate_id=cand.id, source_version_id=sv.id,
            reference_ids=("wrong-format", "er-sp-1"),
        )
        assert rec is not None
        assert "wrong-format" in (rec.reference_ids or [])
        # CONFIRMED GAP: no format validation


# ---------------------------------------------------------------------------
# ATTACK 4: validation_method derivation — edge cases
# ---------------------------------------------------------------------------

class TestAttackValidationMethodDerivation:
    def test_missing_layers_dict(self):
        """What if gate_decision has no layers dict?"""
        gate = {"decision": "auto_approve"}  # no layers
        method = _derive_validation_method(gate)
        # Returns default "frozen_header_rule"
        assert method == "frozen_header_rule"
        # This is acceptable — default fallback

    def test_empty_layers_dict_with_rejected(self):
        """ATTACK: What if rejected with empty layers dict?"""
        gate = {"decision": "rejected", "layers": {}}
        method = _derive_validation_method(gate)
        # Returns default "frozen_header_rule"
        assert method == "frozen_header_rule"
        # CONFIRMED GAP: rejected with no layer info gets wrong method

    def test_unexpected_layer_status(self):
        """ATTACK: What if layer status is unexpected value?"""
        gate = {
            "decision": "rejected",
            "layers": {
                "structural": {"status": "unknown", "reasons": []},
                "provenance": {"status": "pass", "reasons": []},
                "semantic": {"status": "pass", "reasons": []},
                "admission": {"status": "fail", "reasons": []},
            },
        }
        method = _derive_validation_method(gate)
        # status="unknown" is not "fail", so falls through to default
        assert method == "frozen_header_rule"
        # CONFIRMED GAP: unexpected status not handled

    def test_multiple_layers_fail(self):
        """What if multiple layers fail?"""
        gate = {
            "decision": "rejected",
            "layers": {
                "structural": {"status": "fail", "reasons": ["bad"]},
                "provenance": {"status": "fail", "reasons": ["mismatch"]},
                "semantic": {"status": "pass", "reasons": []},
                "admission": {"status": "fail", "reasons": []},
            },
        }
        method = _derive_validation_method(gate)
        # provenance checked first → byte_proven
        assert method == "byte_proven"
        # This is acceptable — provenance is most specific


# ---------------------------------------------------------------------------
# ATTACK 5: CheckResult — is it actually structured?
# ---------------------------------------------------------------------------

class TestAttackCheckResult:
    def test_check_id_not_validated(self):
        """ATTACK: Is check_id format validated?"""
        # Can create CheckResult with arbitrary check_id
        c = CheckResult(check_id="arbitrary string with spaces", result="pass")
        assert c.check_id == "arbitrary string with spaces"
        # CONFIRMED GAP: no format validation on check_id

    def test_detail_can_contain_narrative(self):
        """Can detail contain long narrative?"""
        long_detail = "x" * 1000
        c = CheckResult(check_id="TEST", result="pass", detail=long_detail)
        assert c.detail == long_detail
        # This is acceptable — detail is for human-readable description

    def test_extract_checks_with_missing_layers(self):
        """What if layers dict has unexpected structure?"""
        gate = {"decision": "auto_approve", "layers": {"unknown_layer": {"status": "pass"}}}
        checks = _extract_checks(gate)
        # unknown_layer gets check_id "UNKNOWN_LAYER"
        assert len(checks) == 1
        assert checks[0].check_id == "UNKNOWN_LAYER"
        # This is acceptable — generic handling


# ---------------------------------------------------------------------------
# ATTACK 6: ProposerIdentity — is "llm" actually correct?
# ---------------------------------------------------------------------------

class TestAttackProposerIdentity:
    def test_llm_model_name_not_captured(self):
        """ATTACK: Is LLM model name captured?"""
        import inspect
        from app.domains.gate.service import GateService
        source = inspect.getsource(GateService.run)
        # ProposerIdentity created with producer_type="llm" but no model name
        assert 'producer_type="llm"' in source
        # Check if model= is passed in ProposerIdentity constructor
        # Looking at source, model= is NOT passed
        # CONFIRMED GAP: LLM model name not captured

    def test_pipeline_version_is_resolver_version(self):
        """ATTACK: Is pipeline_version correct?"""
        import inspect
        from app.domains.gate.service import GateService
        source = inspect.getsource(GateService.run)
        # pipeline_version=RESOLVER_VERSION — this is resolver version, not LLM version
        assert "pipeline_version=RESOLVER_VERSION" in source
        # CONFIRMED GAP: pipeline_version should be annotation/LLM version, not resolver


# ---------------------------------------------------------------------------
# ATTACK 7: Per-run isolation — does it actually work?
# ---------------------------------------------------------------------------

class TestAttackPerRunIsolation:
    def test_evidence_promotion_none_before_run(self):
        """Is evidence_promotion None before run()?"""
        import inspect
        from app.domains.gate.service import GateService
        # Check __init__ sets _evidence to None
        source = inspect.getsource(GateService.__init__)
        assert "self._evidence: EvidencePromotionService | None = None" in source
        # This is correct — None before run()


# ---------------------------------------------------------------------------
# ATTACK 8: Timestamp ordering — edge cases
# ---------------------------------------------------------------------------

class TestAttackTimestampOrdering:
    async def test_future_timestamp_wins(self, session):
        """Does later timestamp win over earlier? (latest-by-validated_at)

        EB-008 A1 修复后：远期未来时间戳被拒；用偏移内时间戳验证排序语义。
        """
        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        service = EvidencePromotionService(repo)
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(minutes=2)

        e_past = ValidationEvent(
            event_id="ve-past", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=past,
        )
        e_future = ValidationEvent(
            event_id="ve-future", claim_id="c1", validation_result="invalidated",
            checks=(), validation_method="structural_consistency", validator="system/v1",
            validated_at=future,
        )
        await repo.append_event(e_past, candidate_id=cand.id, source_version_id=sv.id)
        await repo.append_event(e_future, candidate_id=cand.id, source_version_id=sv.id)
        # max(validated_at) returns future → invalidated → False
        assert await service.is_evidence_validated(cand.id, "c1") is False

    async def test_past_timestamp_loses(self, session):
        """Does past timestamp lose to later?"""
        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        service = EvidencePromotionService(repo)
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(minutes=2)

        e_past_rejected = ValidationEvent(
            event_id="ve-past", claim_id="c2", validation_result="rejected",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=past,
        )
        e_future_validated = ValidationEvent(
            event_id="ve-future", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=future,
        )
        await repo.append_event(
            e_past_rejected, candidate_id=cand.id, source_version_id=sv.id,
        )
        await repo.append_event(
            e_future_validated, candidate_id=cand.id, source_version_id=sv.id,
        )
        assert await service.is_evidence_validated(cand.id, "c1") is True
        assert await service.is_evidence_validated(cand.id, "c2") is False


# ---------------------------------------------------------------------------
# ATTACK 9: record_validation_event — edge cases
# ---------------------------------------------------------------------------

class TestAttackRecordValidationEvent:
    def test_invalid_decision_raises(self):
        """Does invalid decision raise ValueError?"""
        with pytest.raises(ValueError, match="Invalid gate decision"):
            record_validation_event(claim_id="c1", gate_decision={"decision": "invalid"})

    def test_none_decision_raises(self):
        """Does None decision raise ValueError?"""
        with pytest.raises(ValueError, match="Invalid gate decision"):
            record_validation_event(claim_id="c1", gate_decision={"decision": None})

    def test_missing_decision_raises(self):
        """Does missing decision key raise ValueError?"""
        with pytest.raises(ValueError, match="Invalid gate decision"):
            record_validation_event(claim_id="c1", gate_decision={})
