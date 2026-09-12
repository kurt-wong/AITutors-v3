"""Evidence Promotion Contract Phase 1 — comprehensive tests.

Tests cover:
- ProposerIdentity: valid/invalid producer types, frozen dataclass
- EvidenceReference: creation from ResolvedSpan, frozen, no authority
- ValidationEvent: valid/invalid results/methods, frozen, append-only semantics
- create_evidence_references: from ResolvedRun
- record_validation_event: gate_decision mapping
- EvidencePromotionService: integration, append-only, is_evidence_validated
- Frozen rules: R1 (ResolvedSpan no role), R2 (Proposal no authority), R4 (only Validation produces authority)
- Architecture constraints: ResolvedSpan not polluted, EvidenceReference is bridge
"""

from __future__ import annotations

import uuid
from dataclasses import FrozenInstanceError

import pytest

from app.domains.evidence.models import (
    VALID_PRODUCER_TYPES,
    VALID_VALIDATION_METHODS,
    VALID_VALIDATION_RESULTS,
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


def _make_proposer(producer_type: str = "native_parser") -> ProposerIdentity:
    return ProposerIdentity(producer_type=producer_type)


# ---------------------------------------------------------------------------
# ProposerIdentity
# ---------------------------------------------------------------------------

class TestProposerIdentity:
    def test_valid_producer_types(self):
        for pt in VALID_PRODUCER_TYPES:
            p = ProposerIdentity(producer_type=pt)
            assert p.producer_type == pt
            assert p.model is None
            assert p.pipeline_version is None

    def test_invalid_producer_type_raises(self):
        with pytest.raises(ValueError, match="Invalid producer_type"):
            ProposerIdentity(producer_type="invalid_type")

    def test_with_model_and_version(self):
        p = ProposerIdentity(
            producer_type="llm",
            model="qwen3.5-9b",
            pipeline_version="v1.0",
        )
        assert p.model == "qwen3.5-9b"
        assert p.pipeline_version == "v1.0"

    def test_frozen(self):
        p = ProposerIdentity(producer_type="ocr")
        with pytest.raises(FrozenInstanceError):
            p.producer_type = "llm"

    def test_llm_is_low_provenance(self):
        """Architecture review: LLM with temperature=0 is still Low provenance.
        Reliability comes from validation_method, not proposer claims."""
        p = ProposerIdentity(producer_type="llm", model="qwen3.5-9b")
        # ProposerIdentity has no trust_level field — provenance only
        assert not hasattr(p, "trust_level")


# ---------------------------------------------------------------------------
# EvidenceReference
# ---------------------------------------------------------------------------

class TestEvidenceReference:
    def test_from_resolved_span(self):
        span = _make_span()
        proposer = _make_proposer()
        ref = EvidenceReference.from_resolved_span(span, proposer)

        assert ref.reference_id == f"er-{span.span_id}"
        assert ref.span_id == span.span_id
        assert ref.proposed_role == span.role
        assert ref.proposer == proposer
        assert ref.source_version_id == span.source_version_id

    def test_frozen(self):
        ref = EvidenceReference.from_resolved_span(_make_span(), _make_proposer())
        with pytest.raises(FrozenInstanceError):
            ref.proposed_role = "explanation"

    def test_no_evidence_authority_field(self):
        """R2: EvidenceReference never has evidence authority.
        It is a Proposal, not a Claim."""
        ref = EvidenceReference.from_resolved_span(_make_span(), _make_proposer())
        # No validated, authority, or trust fields
        assert not hasattr(ref, "validated")
        assert not hasattr(ref, "authority")
        assert not hasattr(ref, "trust_level")

    def test_proposed_role_from_span(self):
        for role in ("answer", "explanation", "stem", "option"):
            span = _make_span(role=role)
            ref = EvidenceReference.from_resolved_span(span, _make_proposer())
            assert ref.proposed_role == role


# ---------------------------------------------------------------------------
# ValidationEvent
# ---------------------------------------------------------------------------

class TestValidationEvent:
    def test_valid_results(self):
        for result in VALID_VALIDATION_RESULTS:
            event = ValidationEvent(
                event_id="ve-1",
                claim_id="claim-1",
                validation_result=result,
                checks_passed=(),
                checks_failed=(),
                validation_method="frozen_header_rule",
                validator="gate/v1",
            )
            assert event.validation_result == result

    def test_invalid_result_raises(self):
        with pytest.raises(ValueError, match="Invalid validation_result"):
            ValidationEvent(
                event_id="ve-1",
                claim_id="claim-1",
                validation_result="unknown",
                checks_passed=(),
                checks_failed=(),
                validation_method="frozen_header_rule",
                validator="gate/v1",
            )

    def test_invalid_method_raises(self):
        with pytest.raises(ValueError, match="Invalid validation_method"):
            ValidationEvent(
                event_id="ve-1",
                claim_id="claim-1",
                validation_result="validated",
                checks_passed=(),
                checks_failed=(),
                validation_method="llm_verification",
                validator="gate/v1",
            )

    def test_frozen(self):
        event = ValidationEvent(
            event_id="ve-1",
            claim_id="claim-1",
            validation_result="validated",
            checks_passed=(),
            checks_failed=(),
            validation_method="frozen_header_rule",
            validator="gate/v1",
        )
        with pytest.raises(FrozenInstanceError):
            event.validation_result = "rejected"

    def test_is_validated(self):
        event = ValidationEvent(
            event_id="ve-1",
            claim_id="claim-1",
            validation_result="validated",
            checks_passed=(),
            checks_failed=(),
            validation_method="frozen_header_rule",
            validator="gate/v1",
        )
        assert event.is_validated is True
        assert event.is_terminal is False

    def test_is_terminal_rejected(self):
        event = ValidationEvent(
            event_id="ve-1",
            claim_id="claim-1",
            validation_result="rejected",
            checks_passed=(),
            checks_failed=("check1",),
            validation_method="frozen_header_rule",
            validator="gate/v1",
        )
        assert event.is_validated is False
        assert event.is_terminal is True

    def test_is_terminal_invalidated(self):
        event = ValidationEvent(
            event_id="ve-1",
            claim_id="claim-1",
            validation_result="invalidated",
            checks_passed=(),
            checks_failed=(),
            validation_method="human_review",
            validator="human",
        )
        assert event.is_validated is False
        assert event.is_terminal is True


# ---------------------------------------------------------------------------
# create_evidence_references
# ---------------------------------------------------------------------------

class TestCreateEvidenceReferences:
    def test_from_empty_run(self):
        run = _make_run()
        refs = create_evidence_references(run, _make_proposer())
        assert refs == ()

    def test_from_single_span(self):
        span = _make_span()
        run = _make_run(span)
        refs = create_evidence_references(run, _make_proposer())
        assert len(refs) == 1
        assert refs[0].span_id == span.span_id

    def test_from_multiple_spans(self):
        spans = (
            _make_span("sp-1", "stem"),
            _make_span("sp-2", "option"),
            _make_span("sp-3", "answer"),
        )
        run = _make_run(*spans)
        refs = create_evidence_references(run, _make_proposer())
        assert len(refs) == 3
        assert {r.span_id for r in refs} == {"sp-1", "sp-2", "sp-3"}

    def test_preserves_proposer_identity(self):
        proposer = ProposerIdentity(producer_type="ocr", model="paddleocr-v4")
        run = _make_run(_make_span())
        refs = create_evidence_references(run, proposer)
        assert refs[0].proposer == proposer


# ---------------------------------------------------------------------------
# record_validation_event
# ---------------------------------------------------------------------------

class TestRecordValidationEvent:
    def test_auto_approve_maps_to_validated(self):
        gate_decision = {"decision": "auto_approve", "reasons": ["grammar_ok"]}
        event = record_validation_event(claim_id="claim-1", gate_decision=gate_decision)
        assert event is not None
        assert event.validation_result == "validated"
        assert event.checks_passed == ("grammar_ok",)
        assert event.checks_failed == ()

    def test_rejected_maps_to_rejected(self):
        gate_decision = {"decision": "rejected", "reasons": ["hash_mismatch"]}
        event = record_validation_event(claim_id="claim-1", gate_decision=gate_decision)
        assert event is not None
        assert event.validation_result == "rejected"
        assert event.checks_failed == ("hash_mismatch",)

    def test_pending_review_returns_none(self):
        """pending_review: validation not concluded, human review needed."""
        gate_decision = {"decision": "pending_review", "reasons": ["grammar_none"]}
        event = record_validation_event(claim_id="claim-1", gate_decision=gate_decision)
        assert event is None

    def test_auto_approve_without_reasons(self):
        gate_decision = {"decision": "auto_approve"}
        event = record_validation_event(claim_id="claim-1", gate_decision=gate_decision)
        assert event is not None
        assert event.checks_passed == ("all_gate_checks",)

    def test_rejected_without_reasons(self):
        gate_decision = {"decision": "rejected"}
        event = record_validation_event(claim_id="claim-1", gate_decision=gate_decision)
        assert event is not None
        assert event.checks_failed == ("gate_rejected",)

    def test_validator_default(self):
        gate_decision = {"decision": "auto_approve"}
        event = record_validation_event(claim_id="claim-1", gate_decision=gate_decision)
        assert event.validator == "gate/v1"

    def test_custom_validator(self):
        gate_decision = {"decision": "auto_approve"}
        event = record_validation_event(
            claim_id="claim-1", gate_decision=gate_decision, validator="gate/v2"
        )
        assert event.validator == "gate/v2"


# ---------------------------------------------------------------------------
# EvidencePromotionService
# ---------------------------------------------------------------------------

class TestEvidencePromotionService:
    def test_create_references(self):
        service = EvidencePromotionService()
        run = _make_run(_make_span("sp-1"), _make_span("sp-2"))
        refs = service.create_references(run, _make_proposer())
        assert len(refs) == 2
        assert len(service.evidence_references) == 2

    def test_record_validation_validated(self):
        service = EvidencePromotionService()
        event = service.record_validation(
            "claim-1", {"decision": "auto_approve", "reasons": ["ok"]}
        )
        assert event is not None
        assert len(service.validation_events) == 1

    def test_record_validation_rejected(self):
        service = EvidencePromotionService()
        event = service.record_validation(
            "claim-1", {"decision": "rejected", "reasons": ["fail"]}
        )
        assert event is not None
        assert len(service.validation_events) == 1

    def test_record_validation_pending_no_event(self):
        service = EvidencePromotionService()
        event = service.record_validation(
            "claim-1", {"decision": "pending_review", "reasons": ["grammar_none"]}
        )
        assert event is None
        assert len(service.validation_events) == 0

    def test_append_only(self):
        """Multiple validations for same claim append, not overwrite."""
        service = EvidencePromotionService()
        service.record_validation("claim-1", {"decision": "auto_approve"})
        service.record_validation("claim-1", {"decision": "rejected", "reasons": ["source_changed"]})
        assert len(service.validation_events) == 2
        events = service.get_events_for_claim("claim-1")
        assert len(events) == 2

    def test_is_evidence_validated_true(self):
        service = EvidencePromotionService()
        service.record_validation("claim-1", {"decision": "auto_approve"})
        assert service.is_evidence_validated("claim-1") is True

    def test_is_evidence_validated_false_rejected(self):
        service = EvidencePromotionService()
        service.record_validation("claim-1", {"decision": "rejected"})
        assert service.is_evidence_validated("claim-1") is False

    def test_is_evidence_validated_false_no_events(self):
        service = EvidencePromotionService()
        assert service.is_evidence_validated("claim-1") is False

    def test_is_evidence_validated_superseded_by_invalidation(self):
        """Latest event wins: validated then invalidated → not validated."""
        service = EvidencePromotionService()
        service.record_validation("claim-1", {"decision": "auto_approve"})
        assert service.is_evidence_validated("claim-1") is True
        # Simulate invalidation (source changed)
        from app.domains.evidence.models import ValidationEvent
        invalidation = ValidationEvent(
            event_id="ve-inval-1",
            claim_id="claim-1",
            validation_result="invalidated",
            checks_passed=(),
            checks_failed=("source_changed",),
            validation_method="human_review",
            validator="human",
        )
        service._validation_events.append(invalidation)
        assert service.is_evidence_validated("claim-1") is False

    def test_get_events_for_claim_isolation(self):
        service = EvidencePromotionService()
        service.record_validation("claim-1", {"decision": "auto_approve"})
        service.record_validation("claim-2", {"decision": "rejected"})
        events_1 = service.get_events_for_claim("claim-1")
        events_2 = service.get_events_for_claim("claim-2")
        assert len(events_1) == 1
        assert len(events_2) == 1
        assert events_1[0].claim_id == "claim-1"
        assert events_2[0].claim_id == "claim-2"


# ---------------------------------------------------------------------------
# Frozen Rules (Architecture Contract)
# ---------------------------------------------------------------------------

class TestFrozenRules:
    def test_r1_resolved_span_no_semantic_role_pollution(self):
        """R1: ResolvedSpan (SourceFragment) never contains semantic role.
        EvidenceReference carries proposed_role separately."""
        span = _make_span(role="answer")
        # ResolvedSpan.role is location metadata from Resolver, not evidence authority
        ref = EvidenceReference.from_resolved_span(span, _make_proposer())
        # EvidenceReference.proposed_role is the proposal, not the span itself
        assert ref.proposed_role == "answer"
        # ResolvedSpan has no proposer, trust, or authority fields
        assert not hasattr(span, "proposer")
        assert not hasattr(span, "trust_level")
        assert not hasattr(span, "validated")

    def test_r2_proposal_no_authority(self):
        """R2: EvidenceReference never has evidence authority."""
        ref = EvidenceReference.from_resolved_span(_make_span(), _make_proposer())
        # No authority fields
        assert not hasattr(ref, "validated")
        assert not hasattr(ref, "authority")
        assert not hasattr(ref, "is_validated")

    def test_r4_only_validation_produces_authority(self):
        """R4: Only ValidationEvent produces Evidence Authority."""
        service = EvidencePromotionService()
        # Before any validation: not validated
        assert service.is_evidence_validated("claim-1") is False
        # After validation: validated
        service.record_validation("claim-1", {"decision": "auto_approve"})
        assert service.is_evidence_validated("claim-1") is True
        # EvidenceReference alone cannot grant authority
        ref = EvidenceReference.from_resolved_span(_make_span(), _make_proposer())
        assert not hasattr(ref, "validated")

    def test_resolved_span_not_polluted(self):
        """Architecture review: ResolvedSpan stays pure (location + resolution).
        EvidenceReference is the bridge, not a ResolvedSpan extension."""
        span = _make_span()
        # ResolvedSpan has only location fields
        location_fields = {
            "span_id", "source_version_id", "role", "start_line_ref",
            "end_line_ref", "line_refs", "granularity", "start_offset",
            "end_offset", "text_hash", "resolution_status", "evidence",
        }
        actual_fields = set(span.__dataclass_fields__.keys())
        assert actual_fields == location_fields

    def test_evidence_reference_is_bridge(self):
        """EvidenceReference bridges Source Binding → Evidence Lifecycle."""
        span = _make_span()
        proposer = _make_proposer()
        ref = EvidenceReference.from_resolved_span(span, proposer)
        # Carries span reference (Source Binding)
        assert ref.span_id == span.span_id
        assert ref.source_version_id == span.source_version_id
        # Carries proposal metadata (Evidence Lifecycle)
        assert ref.proposed_role == span.role
        assert ref.proposer == proposer
        # No authority (R2)
        assert not hasattr(ref, "validated")


# ---------------------------------------------------------------------------
# Integration: Gate decision → ValidationEvent → authority
# ---------------------------------------------------------------------------

class TestGateIntegration:
    def test_full_flow_validated(self):
        """Full flow: ResolvedSpan → EvidenceReference → Gate → ValidationEvent → authority."""
        service = EvidencePromotionService()

        # 1. Resolver produces ResolvedSpan
        span = _make_span("sp-answer-1", "answer")
        run = _make_run(span)

        # 2. Create EvidenceReferences (Proposal layer)
        proposer = ProposerIdentity(producer_type="native_parser", pipeline_version="v1.0")
        refs = service.create_references(run, proposer)
        assert len(refs) == 1

        # 3. Gate validates → auto_approve
        gate_decision = {"decision": "auto_approve", "reasons": ["grammar_ok"]}
        event = service.record_validation("unit-1", gate_decision)

        # 4. ValidationEvent produces authority (R4)
        assert event is not None
        assert event.validation_result == "validated"
        assert service.is_evidence_validated("unit-1") is True

    def test_full_flow_rejected(self):
        """Full flow: rejected → no authority."""
        service = EvidencePromotionService()

        span = _make_span("sp-answer-1", "answer")
        run = _make_run(span)
        proposer = ProposerIdentity(producer_type="ocr")
        service.create_references(run, proposer)

        gate_decision = {"decision": "rejected", "reasons": ["role_region_mismatch"]}
        event = service.record_validation("unit-1", gate_decision)

        assert event is not None
        assert event.validation_result == "rejected"
        assert service.is_evidence_validated("unit-1") is False

    def test_full_flow_pending_review(self):
        """Full flow: pending_review → no ValidationEvent, no authority."""
        service = EvidencePromotionService()

        span = _make_span("sp-answer-1", "answer")
        run = _make_run(span)
        proposer = ProposerIdentity(producer_type="llm")
        service.create_references(run, proposer)

        gate_decision = {"decision": "pending_review", "reasons": ["grammar_none"]}
        event = service.record_validation("unit-1", gate_decision)

        assert event is None
        assert len(service.validation_events) == 0
        assert service.is_evidence_validated("unit-1") is False

    def test_multiple_claims_independent(self):
        """Multiple claims validate independently."""
        service = EvidencePromotionService()

        service.record_validation("unit-1", {"decision": "auto_approve"})
        service.record_validation("unit-2", {"decision": "rejected"})
        service.record_validation("unit-3", {"decision": "pending_review"})

        assert service.is_evidence_validated("unit-1") is True
        assert service.is_evidence_validated("unit-2") is False
        assert service.is_evidence_validated("unit-3") is False
        # Only 2 events (pending_review doesn't create one)
        assert len(service.validation_events) == 2
