"""V3 Evidence Promotion Contract — Phase 1 (75_EVIDENCE_PROMOTION_CONTRACT.md v1.1.0).

Phase 1 scope (最小改动):
- ProposerIdentity: who proposed this evidence (provenance, not reliability)
- EvidenceReference: bridge from ResolvedSpan (Source Binding) to Evidence Lifecycle
- ValidationEvent: append-only record of Gate validation outcomes
- CheckResult: structured check with machine-parseable ID (Hardening)
- AppendOnlyEventLog: tuple-based immutable log (Hardening)

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
    "record_validation_event",
]
