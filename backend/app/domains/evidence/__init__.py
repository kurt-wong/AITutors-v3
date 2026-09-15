"""V3 Evidence Promotion Contract — Phase 1 + EB-008 (75 + 92号).

Phase 1 scope:
- ProposerIdentity: who proposed this evidence (provenance, not reliability)
- EvidenceReference: bridge from ResolvedSpan (Source Binding) to Evidence Lifecycle
- ValidationEvent: append-only record of Gate validation outcomes
- CheckResult: structured check with machine-parseable ID (Hardening)
- AppendOnlyEventLog: tuple-based immutable log (Hardening; state machine shared with DB path)
- enforce_state_transition: state machine single source (EB-008 §5.1)

EB-008 scope (92号):
- proof: review proof generate/verify (§5.2)
- EvidencePromotionService: DB-backed via EvidenceRepository (§5.1)

Key frozen rules enforced here:
- R1: SourceFragment (ResolvedSpan) never contains semantic role — stays pure location
- R2: EvidenceProposal (EvidenceReference) never has evidence authority
- R4: Only ValidationEvent produces Evidence Authority
"""

from app.domains.evidence.models import (
    AppendOnlyEventLog,
    CheckResult,
    EvidenceReference,
    ProposerIdentity,
    ValidationEvent,
    enforce_state_transition,
)
from app.domains.evidence.proof import (
    generate_review_proof,
    human_validator,
    require_app_secret,
    verify_review_proof,
)
from app.domains.evidence.promotion import (
    EvidencePromotionService,
    create_evidence_references,
    record_validation_event,
)

__all__ = [
    "AppendOnlyEventLog",
    "CheckResult",
    "EvidenceReference",
    "EvidencePromotionService",
    "ProposerIdentity",
    "ValidationEvent",
    "create_evidence_references",
    "enforce_state_transition",
    "generate_review_proof",
    "human_validator",
    "record_validation_event",
    "require_app_secret",
    "verify_review_proof",
]
