"""Evidence Promotion Service — Phase 1 (75_EVIDENCE_PROMOTION_CONTRACT.md v1.1.0).

Phase 1 responsibilities:
1. Create EvidenceReference list from ResolvedRun (bridge: Source Binding → Evidence Lifecycle)
2. Record ValidationEvent from Gate decisions (append-only event log)
3. Provide EvidencePromotionService for GateService integration

Phase 1 does NOT:
- Create explicit EvidenceProposal / EvidenceClaim dataclasses (Phase 2)
- Enforce state machine transitions (Phase 2)
- Change ResolvedSpan schema (frozen — architecture review)
- Change existing pipeline flow (additive only)

Architecture principle: Resolver produces ResolvedSpan (location). EvidenceReference
adds proposal metadata. Neither alone constitutes evidence authority. Only
ValidationEvent (from Gate) produces authority.
"""

from __future__ import annotations

import uuid

from app.domains.evidence.models import (
    EvidenceReference,
    ProposerIdentity,
    ValidationEvent,
)
from app.domains.resolver.span import ResolvedRun


def create_evidence_references(
    resolved_run: ResolvedRun,
    proposer: ProposerIdentity,
) -> tuple[EvidenceReference, ...]:
    """Create EvidenceReference for each ResolvedSpan in a ResolvedRun.

    Each resolved span becomes an evidence proposal. The proposer identity
    records who made the proposal (provenance). This does NOT grant evidence
    authority — that requires a ValidationEvent from Gate.

    Args:
        resolved_run: Output of SourceResolver.resolve()
        proposer: Who is proposing these evidence candidates

    Returns:
        Tuple of EvidenceReference, one per ResolvedSpan.
    """
    return tuple(
        EvidenceReference.from_resolved_span(span, proposer)
        for span in resolved_run.resolved_spans
    )


def record_validation_event(
    *,
    claim_id: str,
    gate_decision: dict,
    validator: str = "gate/v1",
) -> ValidationEvent | None:
    """Create a ValidationEvent from a Gate decision dict.

    Maps gate_decision.decision to validation_result:
    - "auto_approve" → "validated" (all checks passed, strict-auto grammar verified)
    - "rejected"     → "rejected"  (structural/semantic contradiction)
    - "pending_review" → None (validation not concluded; human review needed)

    Args:
        claim_id: Identifier for what was validated (e.g., candidate unit_id)
        gate_decision: Output of GatePolicy.evaluate()
        validator: Validator identifier (deterministic, not LLM)

    Returns:
        ValidationEvent if validation concluded (validated/rejected),
        None if pending_review (still awaiting human validation).
    """
    decision = gate_decision.get("decision")
    reasons = gate_decision.get("reasons", [])

    if decision == "auto_approve":
        # All checks passed. Extract passed check names from reasons or use standard set.
        checks_passed = tuple(reasons) if reasons else ("all_gate_checks",)
        return ValidationEvent(
            event_id=f"ve-{claim_id}-{uuid.uuid4().hex[:8]}",
            claim_id=claim_id,
            validation_result="validated",
            checks_passed=checks_passed,
            checks_failed=(),
            validation_method="frozen_header_rule",
            validator=validator,
        )

    if decision == "rejected":
        checks_failed = tuple(reasons) if reasons else ("gate_rejected",)
        return ValidationEvent(
            event_id=f"ve-{claim_id}-{uuid.uuid4().hex[:8]}",
            claim_id=claim_id,
            validation_result="rejected",
            checks_passed=(),
            checks_failed=checks_failed,
            validation_method="frozen_header_rule",
            validator=validator,
        )

    # pending_review: validation not concluded. No ValidationEvent.
    # The candidate stays in pending_review state awaiting human validation.
    return None


class EvidencePromotionService:
    """Phase 1 service for Evidence Promotion Contract integration.

    Provides the bridge between Resolver output and Gate validation recording.
    Designed for additive integration with GateService — does not change existing
    pipeline behavior.

    Phase 1 state:
    - In-memory append-only ValidationEvent log (DB persistence = Phase 2)
    - EvidenceReference creation from ResolvedRun
    - No state machine enforcement (Phase 2)

    Usage in GateService.run():
        promo = EvidencePromotionService()
        refs = promo.create_references(resolved_run, proposer_identity)
        ...
        event = promo.record_validation(unit_id, gate_decision)
    """

    def __init__(self) -> None:
        # Phase 1: in-memory append-only log. Phase 2: DB persistence.
        self._validation_events: list[ValidationEvent] = []
        self._evidence_references: list[EvidenceReference] = []

    def create_references(
        self,
        resolved_run: ResolvedRun,
        proposer: ProposerIdentity,
    ) -> tuple[EvidenceReference, ...]:
        """Create and store EvidenceReferences from a ResolvedRun."""
        refs = create_evidence_references(resolved_run, proposer)
        self._evidence_references.extend(refs)
        return refs

    def record_validation(
        self,
        claim_id: str,
        gate_decision: dict,
        validator: str = "gate/v1",
    ) -> ValidationEvent | None:
        """Record a ValidationEvent from a Gate decision. Append-only."""
        event = record_validation_event(
            claim_id=claim_id,
            gate_decision=gate_decision,
            validator=validator,
        )
        if event is not None:
            self._validation_events.append(event)
        return event

    @property
    def validation_events(self) -> tuple[ValidationEvent, ...]:
        """All recorded ValidationEvents (append-only, read-only access)."""
        return tuple(self._validation_events)

    @property
    def evidence_references(self) -> tuple[EvidenceReference, ...]:
        """All created EvidenceReferences (read-only access)."""
        return tuple(self._evidence_references)

    def get_events_for_claim(self, claim_id: str) -> tuple[ValidationEvent, ...]:
        """Get all ValidationEvents for a specific claim. Append-only means
        there may be multiple events (e.g., validated then invalidated)."""
        return tuple(e for e in self._validation_events if e.claim_id == claim_id)

    def is_evidence_validated(self, claim_id: str) -> bool:
        """Check if a claim has a terminal validated event.

        R4: Only ValidationEvent produces Evidence Authority.
        A claim is validated only if its LATEST event has result="validated".
        (A later INVALIDATED event supersedes a prior validated.)
        """
        events = self.get_events_for_claim(claim_id)
        if not events:
            return False
        # Latest event wins (append-only log, last entry is current state)
        latest = events[-1]
        return latest.validation_result == "validated"
