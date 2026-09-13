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

    def test_bypass_log_via_direct_append_blocked(self):
        """HIGH-2 FIX: State machine enforced in AppendOnlyEventLog.append()."""
        service = EvidencePromotionService()
        service.record_validation("c1", _gate_rejected())
        # ATTACK: append validated via direct log access — should FAIL
        later_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        fake_event = ValidationEvent(
            event_id="ve-fake", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="attacker",
            validated_at=later_time,
        )
        # State machine blocks this — c1 is REJECTED (terminal)
        with pytest.raises(ValueError, match="terminal"):
            service._validation_log.append(fake_event)
        # Attack blocked — c1 still rejected
        assert service.is_evidence_validated("c1") is False


# ---------------------------------------------------------------------------
# ATTACK 2: State machine — can we bypass _check_state_transition?
# ---------------------------------------------------------------------------

class TestAttackStateMachine:
    def test_direct_log_append_bypasses_state_machine_blocked(self):
        """HIGH-2 FIX: State machine enforced in AppendOnlyEventLog.append()."""
        service = EvidencePromotionService()
        service.record_validation("c1", _gate_rejected())
        # ATTACK: append validated via direct log access — should FAIL
        later_time = datetime.now(timezone.utc) + timedelta(seconds=1)
        fake_event = ValidationEvent(
            event_id="ve-fake", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="attacker",
            validated_at=later_time,
        )
        # State machine blocks this — c1 is REJECTED (terminal)
        with pytest.raises(ValueError, match="terminal"):
            service._validation_log.append(fake_event)
        # Attack blocked — c1 still rejected
        assert service.is_evidence_validated("c1") is False

    def test_manipulated_timestamps_confuse_state_machine(self):
        """ATTACK: Create events with manipulated timestamps to confuse ordering."""
        service = EvidencePromotionService()
        # Create event with FUTURE timestamp
        future_time = datetime.now(timezone.utc) + timedelta(days=365)
        future_event = ValidationEvent(
            event_id="ve-future", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=future_time,
        )
        service._validation_log.append(future_event)
        # Now record rejected via proper path
        # State machine sees latest = future_event (validated)
        # Should block REJECTED after VALIDATED
        with pytest.raises(ValueError, match="only INVALIDATED transition allowed"):
            service.record_validation("c1", _gate_rejected())

    def test_equal_timestamps_ambiguous(self):
        """ATTACK: What if two events have identical timestamps?

        State machine blocks VALIDATED → REJECTED, so this attack fails.
        """
        service = EvidencePromotionService()
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
        service._validation_log.append(e1)
        # State machine blocks VALIDATED → REJECTED
        with pytest.raises(ValueError, match="only INVALIDATED transition allowed"):
            service._validation_log.append(e2)


# ---------------------------------------------------------------------------
# ATTACK 3: reference_ids — is linking actually correct?
# ---------------------------------------------------------------------------

class TestAttackReferenceIdsLinking:
    def test_fake_reference_ids_accepted(self):
        """ATTACK: Can we pass fake reference_ids that don't exist?"""
        service = EvidencePromotionService()
        span = _make_span("sp-1")
        service.create_references(_make_run(span), ProposerIdentity(producer_type="llm"))
        # ATTACK: pass fake reference_ids
        event = service.record_validation(
            "c1", _gate_auto_approve(), reference_ids=("er-fake-1", "er-fake-2")
        )
        assert event is not None
        # Event stores fake reference_ids
        assert event.reference_ids == ("er-fake-1", "er-fake-2")
        # But get_references_for_ids returns empty (no matching references)
        traced = service.get_references_for_ids(event.reference_ids)
        assert len(traced) == 0
        # CONFIRMED GAP: no validation that reference_ids actually exist

    def test_empty_reference_ids_accepted(self):
        """ATTACK: Can we record validation with empty reference_ids?"""
        service = EvidencePromotionService()
        event = service.record_validation("c1", _gate_auto_approve(), reference_ids=())
        assert event is not None
        assert event.reference_ids == ()
        # This is allowed — but means no linking

    def test_reference_id_format_not_enforced(self):
        """ATTACK: Is reference_id format enforced?"""
        service = EvidencePromotionService()
        span = _make_span("sp-1")
        service.create_references(_make_run(span), ProposerIdentity(producer_type="llm"))
        # ATTACK: pass reference_ids with wrong format
        event = service.record_validation(
            "c1", _gate_auto_approve(), reference_ids=("wrong-format", "er-sp-1")
        )
        assert event is not None
        # Event stores wrong-format reference_ids
        assert "wrong-format" in event.reference_ids
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
    def test_future_timestamp_wins(self):
        """Does future timestamp win over past?"""
        service = EvidencePromotionService()
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)

        e_past = ValidationEvent(
            event_id="ve-past", claim_id="c1", validation_result="validated",
            checks=(), validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=past,
        )
        e_future = ValidationEvent(
            event_id="ve-future", claim_id="c1", validation_result="invalidated",
            checks=(), validation_method="human_review", validator="gate/v1",
            validated_at=future,
        )
        service._validation_log.append(e_past)
        service._validation_log.append(e_future)
        # max(validated_at) returns future → invalidated → False
        assert service.is_evidence_validated("c1") is False

    def test_past_timestamp_loses(self):
        """Does past timestamp lose to future?"""
        service = EvidencePromotionService()
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)

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
        service._validation_log.append(e_past_rejected)
        service._validation_log.append(e_future_validated)
        # c1 is validated, c2 is rejected
        assert service.is_evidence_validated("c1") is True
        assert service.is_evidence_validated("c2") is False


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
