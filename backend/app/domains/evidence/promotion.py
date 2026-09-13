"""Evidence Promotion Service — Phase 1 (75_EVIDENCE_PROMOTION_CONTRACT.md v1.1.0).

Phase 1 responsibilities:
1. Create EvidenceReference list from ResolvedRun (bridge: Source Binding → Evidence Lifecycle)
2. Record ValidationEvent from Gate decisions (append-only event log)
3. Provide EvidencePromotionService for GateService integration

Phase 1 Hardening (adversarial review 2026-09-13):
- Append-only enforced by AppendOnlyEventLog (tuple-based, Critical 1 fix)
- State machine: REJECTED terminal, INVALIDATED requires prior VALIDATED (Critical 2 fix)
- ValidationEvent.reference_ids links to EvidenceReference IDs (Critical 3 fix)
- validation_method derived from gate layers, not hardcoded (High 4 fix)
- Structured CheckResult objects replace narrative strings (High 5 fix)
- is_evidence_validated uses timestamp, not list position (Medium 7 fix)

Phase 1 does NOT:
- Create explicit EvidenceProposal / EvidenceClaim dataclasses (Phase 2)
- Change ResolvedSpan schema (frozen — architecture review)
- Change existing pipeline flow (additive only)

Architecture principle: Resolver produces ResolvedSpan (location). EvidenceReference
adds proposal metadata. Neither alone constitutes evidence authority. Only
ValidationEvent (from Gate) produces authority.
"""

from __future__ import annotations

import uuid

from app.domains.evidence.models import (
    AppendOnlyEventLog,
    CheckResult,
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


def _derive_validation_method(gate_decision: dict) -> str:
    """Derive validation_method from actual gate layer statuses.

    Phase 1 Hardening (High 4 fix): Previously hardcoded "frozen_header_rule"
    for all outcomes. Now derives from which layer caused the failure:
    - provenance fail (text_hash mismatch) → "byte_proven"
    - structural/semantic fail → "structural_consistency"
    - auto_approve or admission fail → "frozen_header_rule"
    """
    layers = gate_decision.get("layers", {})

    # Check provenance layer first (byte_proven failures are most specific)
    provenance = layers.get("provenance", {})
    if provenance.get("status") == "fail":
        return "byte_proven"

    # Check structural and semantic layers
    structural = layers.get("structural", {})
    semantic = layers.get("semantic", {})
    if structural.get("status") == "fail" or semantic.get("status") == "fail":
        return "structural_consistency"

    # Default: frozen_header_rule (admission/grammar checks)
    return "frozen_header_rule"


def _extract_checks(gate_decision: dict) -> tuple[CheckResult, ...]:
    """Extract structured CheckResult objects from gate decision layers.

    Phase 1 Hardening (High 5 fix): Gate reasons are narrative strings.
    This converts them to structured checks with machine-parseable IDs.
    """
    layers = gate_decision.get("layers", {})
    checks: list[CheckResult] = []

    # Map layer names to check IDs
    layer_check_ids = {
        "structural": "STRUCTURAL_CONSISTENCY",
        "provenance": "BYTE_PROVEN",
        "semantic": "SEMANTIC_CONSISTENCY",
        "admission": "STRICT_AUTO_GRAMMAR",
    }

    for layer_name, layer_data in layers.items():
        if not isinstance(layer_data, dict):
            continue
        status = layer_data.get("status", "unknown")
        reasons = layer_data.get("reasons", [])
        check_id = layer_check_ids.get(layer_name, layer_name.upper())

        checks.append(CheckResult(
            check_id=check_id,
            result="pass" if status == "pass" else "fail",
            detail="; ".join(reasons) if reasons else None,
        ))

    return tuple(checks)


def record_validation_event(
    *,
    claim_id: str,
    gate_decision: dict,
    validator: str = "gate/v1",
    reference_ids: tuple[str, ...] = (),
) -> ValidationEvent | None:
    """Create a ValidationEvent from a Gate decision dict.

    Maps gate_decision.decision to validation_result:
    - "auto_approve" → "validated" (all checks passed, strict-auto grammar verified)
    - "rejected"     → "rejected"  (structural/semantic contradiction)
    - "pending_review" → None (validation not concluded; human review needed)

    Phase 1 Hardening:
    - validation_method derived from gate layers (High 4 fix)
    - Structured CheckResult objects (High 5 fix)
    - reference_ids links to EvidenceReference IDs (Critical 3 fix)

    Args:
        claim_id: Identifier for what was validated (e.g., candidate unit_id)
        gate_decision: Output of GatePolicy.evaluate()
        validator: Validator identifier (deterministic, not LLM)
        reference_ids: EvidenceReference IDs covered by this validation

    Returns:
        ValidationEvent if validation concluded (validated/rejected),
        None if pending_review (still awaiting human validation).
    """
    decision = gate_decision.get("decision")

    if decision == "pending_review":
        # Validation not concluded. No ValidationEvent.
        return None

    if decision not in ("auto_approve", "rejected"):
        raise ValueError(
            f"Invalid gate decision {decision!r}; "
            f"must be 'auto_approve', 'rejected', or 'pending_review'"
        )

    # Derive validation_method from actual gate layers (High 4 fix)
    validation_method = _derive_validation_method(gate_decision)

    # Extract structured checks (High 5 fix)
    checks = _extract_checks(gate_decision)

    # Map decision to validation_result
    validation_result = "validated" if decision == "auto_approve" else "rejected"

    return ValidationEvent(
        event_id=f"ve-{claim_id}-{uuid.uuid4().hex[:8]}",
        claim_id=claim_id,
        validation_result=validation_result,
        checks=checks,
        validation_method=validation_method,
        validator=validator,
        reference_ids=reference_ids,
    )


class EvidencePromotionService:
    """Phase 1 service for Evidence Promotion Contract integration.

    Provides the bridge between Resolver output and Gate validation recording.
    Designed for additive integration with GateService — does not change existing
    pipeline behavior.

    Phase 1 Hardening state:
    - Append-only enforced by AppendOnlyEventLog (tuple-based, Critical 1 fix)
    - State machine enforcement in AppendOnlyEventLog.append() (Critical 2 fix)
    - ValidationEvent ↔ EvidenceReference linking via reference_ids (Critical 3 fix)
    - Per-run isolation: create new instance per GateService.run() call

    Architecture review (2026-09-13): State machine is in the ledger layer,
    not the service layer. This prevents bypass via direct log.append().

    Usage in GateService.run():
        promo = EvidencePromotionService()  # fresh per run
        refs = promo.create_references(resolved_run, proposer_identity)
        ...
        event = promo.record_validation(unit_id, gate_decision, reference_ids=...)
    """

    def __init__(self) -> None:
        # Phase 1: in-memory append-only log. Phase 2: DB persistence.
        self._validation_log = AppendOnlyEventLog()
        self._evidence_references: tuple[EvidenceReference, ...] = ()

    def create_references(
        self,
        resolved_run: ResolvedRun,
        proposer: ProposerIdentity,
    ) -> tuple[EvidenceReference, ...]:
        """Create and store EvidenceReferences from a ResolvedRun."""
        refs = create_evidence_references(resolved_run, proposer)
        self._evidence_references = self._evidence_references + refs
        return refs

    def record_validation(
        self,
        claim_id: str,
        gate_decision: dict,
        validator: str = "gate/v1",
        reference_ids: tuple[str, ...] = (),
    ) -> ValidationEvent | None:
        """Record a ValidationEvent from a Gate decision. Append-only.

        Phase 1 Hardening:
        - State machine enforcement in AppendOnlyEventLog.append() (Critical 2 fix)
        - reference_ids linking (Critical 3 fix)

        Raises ValueError on state machine violation.
        """
        event = record_validation_event(
            claim_id=claim_id,
            gate_decision=gate_decision,
            validator=validator,
            reference_ids=reference_ids,
        )
        if event is None:
            return None

        # State machine enforcement is INSIDE AppendOnlyEventLog.append()
        # Direct calls to _validation_log.append() cannot bypass it.
        self._validation_log.append(event)
        return event

    @property
    def validation_events(self) -> tuple[ValidationEvent, ...]:
        """All recorded ValidationEvents (append-only, read-only access)."""
        return self._validation_log.events

    @property
    def evidence_references(self) -> tuple[EvidenceReference, ...]:
        """All created EvidenceReferences (read-only access)."""
        return self._evidence_references

    def get_events_for_claim(self, claim_id: str) -> tuple[ValidationEvent, ...]:
        """Get all ValidationEvents for a specific claim."""
        return self._validation_log.for_claim(claim_id)

    def get_references_for_ids(
        self, reference_ids: tuple[str, ...]
    ) -> tuple[EvidenceReference, ...]:
        """Get EvidenceReferences by their IDs. Critical 3 fix: enables tracing
        from ValidationEvent back to the EvidenceReferences it validated."""
        id_set = set(reference_ids)
        return tuple(r for r in self._evidence_references if r.reference_id in id_set)

    def is_evidence_validated(self, claim_id: str) -> bool:
        """Check if a claim has a terminal validated event.

        R4: Only ValidationEvent produces Evidence Authority.
        A claim is validated only if its LATEST event (by timestamp) has
        result="validated". (A later INVALIDATED event supersedes a prior validated.)

        Phase 1 Hardening (Medium 7 fix): Uses timestamp ordering, not list position.
        """
        events = self.get_events_for_claim(claim_id)
        if not events:
            return False
        # Latest event by timestamp wins (Medium 7 fix)
        latest = max(events, key=lambda e: e.validated_at)
        return latest.validation_result == "validated"
