"""Evidence Promotion Contract — data models (75_EVIDENCE_PROMOTION_CONTRACT.md v1.1.0).

Five-layer lifecycle: SourceFragment → Proposal → Claim → Validation → ValidatedEvidence.

Phase 1 implements three of these layers as frozen dataclasses:
- ProposerIdentity: provenance metadata (who proposed, not how reliable)
- EvidenceReference: bridge from ResolvedSpan to Evidence Lifecycle (Proposal layer)
- ValidationEvent: append-only validation record (Validation layer)

Frozen rules enforced by dataclass design:
- R1: ResolvedSpan (SourceFragment) never contains semantic role — EvidenceReference
       carries proposed_role separately, ResolvedSpan stays pure location.
- R2: EvidenceReference never has evidence authority — it is a Proposal, not a Claim.
- R3: EvidenceClaim is a promotion request, not truth assertion (Phase 2).
- R4: Only ValidationEvent produces Evidence Authority.
- R5: Semantic IR can only reference ValidatedEvidence (Phase 2 enforcement).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Provenance: who produced this (not how reliable it is)
# ---------------------------------------------------------------------------

# Valid producer types (frozen — changes require architecture review).
VALID_PRODUCER_TYPES = frozenset({
    "native_parser",
    "ocr",
    "llm",
    "heuristic",
    "human",
})


@dataclass(frozen=True)
class ProposerIdentity:
    """Who proposed this evidence candidate (provenance).

    Architecture review (2026-09-13): Provenance and Reliability are separate.
    - Provenance (this class): who produced it — factual, immutable.
    - Reliability (validation_method on ValidationEvent): how it was verified —
      determined by the validation process, not the proposer.

    Frozen rule: LLM with temperature=0 is still Low provenance.
    Reliability comes from the validation method, not the proposer's claims.
    """

    producer_type: str  # must be in VALID_PRODUCER_TYPES
    model: str | None = None        # e.g., "qwen3.5-9b", "paddleocr-v4"
    pipeline_version: str | None = None

    def __post_init__(self) -> None:
        if self.producer_type not in VALID_PRODUCER_TYPES:
            raise ValueError(
                f"Invalid producer_type {self.producer_type!r}; "
                f"must be one of {sorted(VALID_PRODUCER_TYPES)}"
            )


# ---------------------------------------------------------------------------
# Evidence Reference: bridge from Source Binding to Evidence Lifecycle
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceReference:
    """Bridge from ResolvedSpan (Source Binding) to Evidence Lifecycle (Proposal).

    Architecture review (2026-09-13): ResolvedSpan is Source Binding ("where"),
    not Evidence Lifecycle ("why it qualifies"). EvidenceReference carries the
    proposal metadata without polluting ResolvedSpan.

    Frozen rule R2: This is a Proposal, never an authority. It says "someone
    proposed this span as role X", NOT "this span IS role X".

    Phase 1: Created from ResolvedSpan after Resolver completes.
    Phase 2: Will feed into EvidenceProposal → EvidenceClaim promotion.
    """

    reference_id: str
    span_id: str                    # points to ResolvedSpan
    proposed_role: str              # "answer" | "explanation" | "stem" | "option" | ...
    proposer: ProposerIdentity      # who proposed this
    source_version_id: uuid.UUID    # version anchoring
    created_at: datetime = field(default_factory=_utcnow)

    @classmethod
    def from_resolved_span(
        cls,
        span,  # ResolvedSpan — kept untyped to avoid circular import
        proposer: ProposerIdentity,
    ) -> "EvidenceReference":
        """Create an EvidenceReference from a ResolvedSpan.

        The ResolvedSpan provides location (span_id, source_version_id, role).
        The proposer provides provenance. Neither alone constitutes evidence authority.
        """
        return cls(
            reference_id=f"er-{span.span_id}",
            span_id=span.span_id,
            proposed_role=span.role,
            proposer=proposer,
            source_version_id=span.source_version_id,
        )


# ---------------------------------------------------------------------------
# Validation Event: append-only record of Gate validation outcomes
# ---------------------------------------------------------------------------

# Valid validation results (frozen).
VALID_VALIDATION_RESULTS = frozenset({"validated", "rejected", "invalidated"})

# Valid validation methods (frozen — deterministic only, no LLM).
VALID_VALIDATION_METHODS = frozenset({
    "frozen_header_rule",
    "byte_proven",
    "structural_consistency",
    "human_review",
})


@dataclass(frozen=True)
class ValidationEvent:
    """Append-only record of a Gate validation outcome.

    Architecture review (2026-09-13): Event sourcing, not mutable state.
    - Never set `evidence.validated = True` — that's a mutable field anti-pattern.
    - Instead, append a ValidationEvent. History is immutable.
    - When source changes / OCR upgrades / bug fixes occur, append INVALIDATED,
      never modify past events.

    Frozen rule R4: Only ValidationEvent produces Evidence Authority.
    No module may manually set a "validated" flag.
    """

    event_id: str
    claim_id: str                   # identifies what was validated (span_id or claim_id)
    validation_result: str          # "validated" | "rejected" | "invalidated"
    checks_passed: tuple[str, ...]  # which checks passed
    checks_failed: tuple[str, ...]  # which checks failed
    validation_method: str          # "frozen_header_rule" | "byte_proven" | ...
    validator: str                  # e.g., "gate/v1" (deterministic, not LLM)
    validated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if self.validation_result not in VALID_VALIDATION_RESULTS:
            raise ValueError(
                f"Invalid validation_result {self.validation_result!r}; "
                f"must be one of {sorted(VALID_VALIDATION_RESULTS)}"
            )
        if self.validation_method not in VALID_VALIDATION_METHODS:
            raise ValueError(
                f"Invalid validation_method {self.validation_method!r}; "
                f"must be one of {sorted(VALID_VALIDATION_METHODS)}"
            )

    @property
    def is_validated(self) -> bool:
        """True only if validation passed. Convenience — does NOT replace
        checking the event chain. ValidatedEvidence still requires this event."""
        return self.validation_result == "validated"

    @property
    def is_terminal(self) -> bool:
        """True if this event ends the lifecycle (rejected or invalidated)."""
        return self.validation_result in ("rejected", "invalidated")
