"""Evidence Promotion Service — DB-backed（75_EVIDENCE_PROMOTION_CONTRACT + EB-008）。

Phase 1 responsibilities:
1. Create EvidenceReference list from ResolvedRun（bridge: Source Binding → Evidence Lifecycle）
2. Record ValidationEvent from Gate decisions → **持久化到 validation_events**（EB-008 §5.1）
3. Provide EvidencePromotionService for GateService integration

EB-008（92号 §5.1）改造：
- 移除 in-memory AppendOnlyEventLog（DEC-016 Decision-3：所有关键证据必须持久化）
- 改为注入 EvidenceRepository（validation_events INSERT-only）
- record_validation / is_evidence_validated 为 async（DB 路径）
- claim 的 Authority 投影由 repository 承担（latest-by-validated_at wins）

EvidenceReferences 仍为 per-run 内存对象（Proposal 层元数据，非 Authority；R2）。
其 ID 通过 ValidationEvent.reference_ids 持久化（Critical 3），可从 DB 事件反查。

Architecture principle: Resolver produces ResolvedSpan (location). EvidenceReference
adds proposal metadata. Neither alone constitutes evidence authority. Only
ValidationEvent (from Gate, persisted in validation_events) produces authority.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.domains.evidence.models import (
    AUTHORITY_VALIDATED,
    CheckResult,
    EvidenceReference,
    ProposerIdentity,
    ValidationEvent,
)
from app.domains.resolver.span import ResolvedRun
from app.models.evidence import ValidationEventRecord

if TYPE_CHECKING:
    # 避免 promotion ↔ repository 循环导入（repository 依赖 domain models）
    from app.repositories.evidence_repository import EvidenceRepository


def create_evidence_references(
    resolved_run: ResolvedRun,
    proposer: ProposerIdentity,
) -> tuple[EvidenceReference, ...]:
    """Create EvidenceReference for each ResolvedSpan in a ResolvedRun.

    Each resolved span becomes an evidence proposal. The proposer identity
    records who made the proposal (provenance). This does NOT grant evidence
    authority — that requires a ValidationEvent from Gate.
    """
    return tuple(
        EvidenceReference.from_resolved_span(span, proposer)
        for span in resolved_run.resolved_spans
    )


def _derive_validation_method(gate_decision: dict) -> str:
    """Derive validation_method from actual gate layer statuses.

    Phase 1 Hardening (High 4 fix): derives from which layer caused the failure:
    - provenance fail (text_hash mismatch) → "byte_proven"
    - structural/semantic fail → "structural_consistency"
    - auto_approve or admission fail → "frozen_header_rule"
    """
    layers = gate_decision.get("layers", {})

    provenance = layers.get("provenance", {})
    if provenance.get("status") == "fail":
        return "byte_proven"

    structural = layers.get("structural", {})
    semantic = layers.get("semantic", {})
    if structural.get("status") == "fail" or semantic.get("status") == "fail":
        return "structural_consistency"

    return "frozen_header_rule"


def _extract_checks(gate_decision: dict) -> tuple[CheckResult, ...]:
    """Extract structured CheckResult objects from gate decision layers."""
    layers = gate_decision.get("layers", {})
    checks: list[CheckResult] = []

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
    """Create a ValidationEvent from a Gate decision dict (pure builder).

    Maps gate_decision.decision to validation_result:
    - "auto_approve" → "validated"
    - "rejected"     → "rejected"
    - "pending_review" → None (validation not concluded)
    """
    decision = gate_decision.get("decision")

    if decision == "pending_review":
        return None

    if decision not in ("auto_approve", "rejected"):
        raise ValueError(
            f"Invalid gate decision {decision!r}; "
            f"must be 'auto_approve', 'rejected', or 'pending_review'"
        )

    validation_method = _derive_validation_method(gate_decision)
    checks = _extract_checks(gate_decision)
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
    """DB-backed Evidence Promotion service（EB-008 §5.1）。

    - ValidationEvents 持久化到 validation_events（INSERT-only Repository）
    - replay 幂等由 Repository 保证（同结果 → no-op，R1-R5）
    - EvidenceReferences 为 per-run Proposal 元数据（R2，非 Authority）

    Usage in GateService.run():
        promo = EvidencePromotionService(EvidenceRepository(session))
        refs = promo.create_references(resolved_run, proposer_identity)
        ...
        await promo.record_validation(
            root.unit_id, gate,
            candidate_id=candidate.id,
            source_version_id=source_version_id,
            reference_ids=...,
        )
    """

    def __init__(self, repository: EvidenceRepository) -> None:
        self._repository = repository
        self._evidence_references: tuple[EvidenceReference, ...] = ()

    def create_references(
        self,
        resolved_run: ResolvedRun,
        proposer: ProposerIdentity,
    ) -> tuple[EvidenceReference, ...]:
        """Create and store EvidenceReferences from a ResolvedRun (per-run, Proposal 层)."""
        refs = create_evidence_references(resolved_run, proposer)
        self._evidence_references = self._evidence_references + refs
        return refs

    async def record_validation(
        self,
        claim_id: str,
        gate_decision: dict,
        *,
        candidate_id: uuid.UUID,
        source_version_id: uuid.UUID,
        validator: str = "gate/v1",
        reference_ids: tuple[str, ...] = (),
    ) -> ValidationEventRecord | None:
        """Record + persist a ValidationEvent from a Gate decision.

        pending_review → None（验证未结论，不落事件——fail-closed by design，92号 §7 风险6）。
        replay（同结果）→ 返回既有行（R4，不新增）。
        状态机违规 → ValueError（terminal 拒新事件）。
        """
        event = record_validation_event(
            claim_id=claim_id,
            gate_decision=gate_decision,
            validator=validator,
            reference_ids=reference_ids,
        )
        if event is None:
            return None
        return await self._repository.append_event(
            event,
            candidate_id=candidate_id,
            source_version_id=source_version_id,
        )

    @property
    def evidence_references(self) -> tuple[EvidenceReference, ...]:
        """All created EvidenceReferences (read-only, per-run Proposal 层)."""
        return self._evidence_references

    def get_references_for_ids(
        self, reference_ids: tuple[str, ...]
    ) -> tuple[EvidenceReference, ...]:
        """Get EvidenceReferences by their IDs (Critical 3: ValidationEvent → references)."""
        id_set = set(reference_ids)
        return tuple(r for r in self._evidence_references if r.reference_id in id_set)

    async def is_evidence_validated(
        self, candidate_id: uuid.UUID, claim_id: str
    ) -> bool:
        """Check if (candidate, claim) Authority projection is VALIDATED.

        R4: Only ValidationEvent (persisted) produces Evidence Authority.
        Latest-by-timestamp wins: a later INVALIDATED supersedes prior validated.
        """
        state, _ = await self._repository.project_authority(candidate_id, claim_id)
        return state == AUTHORITY_VALIDATED
