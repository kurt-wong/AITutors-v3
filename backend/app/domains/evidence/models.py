"""Evidence Promotion Contract — data models (75_EVIDENCE_PROMOTION_CONTRACT.md v1.1.0).

Five-layer lifecycle: SourceFragment → Proposal → Claim → Validation → ValidatedEvidence.

Phase 1 implements three of these layers as frozen dataclasses:
- ProposerIdentity: provenance metadata (who proposed, not how reliable)
- EvidenceReference: bridge from ResolvedSpan to Evidence Lifecycle (Proposal layer)
- ValidationEvent: append-only validation record (Validation layer)

Phase 1 Hardening (adversarial review 2026-09-13):
- CheckResult: structured check with machine-parseable ID + human-readable detail
- ValidationEvent.reference_ids: links to EvidenceReference IDs (Critical 3 fix)
- AppendOnlyEventLog: tuple-based immutable log (Critical 1 fix)

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
# Check Result: structured check with machine-parseable ID
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CheckResult:
    """A single structured check result.

    Phase 1 Hardening (High 5 fix): Separates machine-parseable check_id from
    human-readable detail. Gate reasons are narrative strings; CheckResult
    extracts the structured check identity.

    check_id: Machine-parseable identifier (e.g., "TEXT_HASH_MATCH",
              "ROLE_PROVENANCE_OVERLAP", "STRICT_AUTO_GRAMMAR").
    result:   "pass" | "fail"
    detail:   Human-readable description (optional, for audit logs).
    """

    check_id: str
    result: str  # "pass" | "fail"
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.result not in ("pass", "fail"):
            raise ValueError(
                f"Invalid check result {self.result!r}; must be 'pass' or 'fail'"
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

    Phase 1 Hardening:
    - reference_ids links this event to EvidenceReference IDs (Critical 3 fix).
    - checks stores structured CheckResult objects (High 5 fix).
    - validation_method derived from actual gate layers (High 4 fix).

    Frozen rule R4: Only ValidationEvent produces Evidence Authority.
    No module may manually set a "validated" flag.
    """

    event_id: str
    claim_id: str                           # identifies what was validated (unit_id)
    validation_result: str                  # "validated" | "rejected" | "invalidated"
    checks: tuple[CheckResult, ...]         # structured check results
    validation_method: str                  # "frozen_header_rule" | "byte_proven" | ...
    validator: str                          # e.g., "gate/v1" (deterministic, not LLM)
    reference_ids: tuple[str, ...] = ()     # links to EvidenceReference IDs
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
    def checks_passed(self) -> tuple[str, ...]:
        """Machine-parseable IDs of checks that passed."""
        return tuple(c.check_id for c in self.checks if c.result == "pass")

    @property
    def checks_failed(self) -> tuple[str, ...]:
        """Machine-parseable IDs of checks that failed."""
        return tuple(c.check_id for c in self.checks if c.result == "fail")

    @property
    def is_validated(self) -> bool:
        """True only if validation passed. Convenience — does NOT replace
        checking the event chain. ValidatedEvidence still requires this event."""
        return self.validation_result == "validated"

    @property
    def is_terminal(self) -> bool:
        """True if this event ends the lifecycle (rejected or invalidated)."""
        return self.validation_result in ("rejected", "invalidated")


# ---------------------------------------------------------------------------
# Append-Only Event Log: tuple-based immutable log with state machine
# ---------------------------------------------------------------------------

# State machine constants (moved from promotion.py for encapsulation)
_TERMINAL_STATES = frozenset({"rejected", "invalidated"})

# Authority 投影状态（Rev-4 §5 /92号 §5.3）。定义在 domain 层，供 Repository/Service
# 共享（避免 promotion ↔ repository 循环导入）。
AUTHORITY_NONE = "none"
AUTHORITY_VALIDATED = "validated"
AUTHORITY_REJECTED = "rejected"
AUTHORITY_INVALIDATED = "invalidated"


def enforce_state_transition(
    existing_events: tuple[ValidationEvent, ...],
    new_result: str,
    claim_id: str,
) -> None:
    """Enforce state machine transitions. Raises ValueError on violation.

    EB-008（92号 §5.1「状态机接入」）：本函数是状态机的唯一实现，
    供 AppendOnlyEventLog（domain 内存 log）与 EvidenceRepository（DB 写入路径）共用。

    - 首事件：validated/rejected 允许；invalidated 禁止（无 prior VALIDATED）
    - REJECTED / INVALIDATED 为 terminal：拒绝一切新事件
    - VALIDATED → 仅 INVALIDATED 允许

    注意：同结果重放（replay idempotency，R1-R5）由调用方（EvidenceRepository）
    在调用本函数**之前**判定为 no-op；本函数只判定非法迁移。
    """
    if not existing_events:
        # First event: must be validated or rejected
        if new_result == "invalidated":
            raise ValueError(
                f"Cannot INVALIDATE claim {claim_id!r}: no prior VALIDATED event"
            )
        return

    # Find latest event by timestamp (Medium 7 fix)
    # key 归一为 UTC aware，防 naive/aware 混比 TypeError（与 repository._as_utc 同则）
    def _key(e: ValidationEvent):
        ts = e.validated_at
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    latest = max(existing_events, key=_key)

    # Terminal states: no more events allowed
    if latest.validation_result in _TERMINAL_STATES:
        raise ValueError(
            f"Claim {claim_id!r} is {latest.validation_result.upper()} (terminal); "
            f"cannot append new ValidationEvent"
        )

    # VALIDATED → only INVALIDATED allowed
    if latest.validation_result == "validated" and new_result != "invalidated":
        raise ValueError(
            f"Claim {claim_id!r} is VALIDATED; only INVALIDATED transition allowed, "
            f"got {new_result!r}"
        )


class AppendOnlyEventLog:
    """Append-only event log with built-in state machine enforcement.

    Phase 1 Hardening (Critical 1 + 2 fix):
    - Tuple-based immutable storage prevents external mutation
    - __slots__ prevents attribute reassignment
    - Name mangling (__events) makes direct access harder
    - State machine validation built into append() — cannot be bypassed

    Architecture review (2026-09-13): EventLog is the Evidence Authority Ledger.
    State machine must be enforced at the ledger level, not the service level.
    This prevents bypass via direct log.append() calls.

    Usage:
        log = AppendOnlyEventLog()
        log.append(event1)
        log.append(event2)
        log.events  # returns immutable tuple snapshot
    """

    __slots__ = ("__events",)

    def __init__(self) -> None:
        object.__setattr__(self, "_AppendOnlyEventLog__events", ())

    def _get_events(self) -> tuple[ValidationEvent, ...]:
        """Internal accessor using name mangling."""
        return object.__getattribute__(self, "_AppendOnlyEventLog__events")

    def _set_events(self, events: tuple[ValidationEvent, ...]) -> None:
        """Internal mutator using name mangling."""
        object.__setattr__(self, "_AppendOnlyEventLog__events", events)

    def _check_state_transition(
        self,
        existing_events: tuple[ValidationEvent, ...],
        new_result: str,
        claim_id: str,
    ) -> None:
        """Enforce state machine transitions. Raises ValueError on violation.

        Critical 2 fix: State machine enforcement at ledger level.
        EB-008：逻辑委托共享函数 enforce_state_transition（DB 写入路径同源）。
        """
        enforce_state_transition(existing_events, new_result, claim_id)

    def append(self, event: ValidationEvent) -> None:
        """Append an event with state machine validation.

        Critical 2 fix: State machine check is HERE, not in the service.
        Direct calls to append() cannot bypass state machine.
        """
        # State machine validation BEFORE append
        existing = self.for_claim(event.claim_id)
        self._check_state_transition(existing, event.validation_result, event.claim_id)

        # Append using immutable tuple concatenation
        current = self._get_events()
        self._set_events(current + (event,))

    @property
    def events(self) -> tuple[ValidationEvent, ...]:
        """All events as an immutable tuple snapshot."""
        return self._get_events()

    def for_claim(self, claim_id: str) -> tuple[ValidationEvent, ...]:
        """Get all events for a specific claim."""
        return tuple(e for e in self._get_events() if e.claim_id == claim_id)

    def __len__(self) -> int:
        return len(self._get_events())

    def __iter__(self):
        return iter(self._get_events())
