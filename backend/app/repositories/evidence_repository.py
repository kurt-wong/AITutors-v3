"""Evidence Authority Repository（EB-008 /92号 §5.1 §5.4 §5.5，DEC-016）。

validation_events 表的唯一写入口。append-only 约束（92号 §5.5 Phase-1 必做）：
- 本类无 update/delete 方法
- insert 前执行状态机检查（enforce_state_transition，与 domain log 同源）
- replay 幂等（R1-R5）：同 (candidate_id, claim_id) 已有同结果事件 → no-op 返回既有
  （replay 永不改变 Authority）

Authority 投影（Rev-4 §5）：project_authority() 事件序列 latest-by-validated_at wins。
proof 验证不在此层自动执行——human_review 事件的 proof 由消费方（Admission Boundary）
调用 verify_review_proof()（关注点分离：Repository 管存储，Boundary 管准入判定）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.domains.evidence.models import (
    AUTHORITY_INVALIDATED,
    AUTHORITY_NONE,
    AUTHORITY_REJECTED,
    AUTHORITY_VALIDATED,
    CheckResult,
    ValidationEvent,
    enforce_state_transition,
)
from app.models.evidence import ValidationEventRecord
from app.models.snapshot import AdmissionCandidate
from app.repositories.base import (
    AppendOnlyViolation,
    BaseRepository,
    RepositoryError,
)

# INVALIDATED 事件的默认 validator（92号 §5.4）
SYSTEM_VALIDATOR = "system/v1"

# 攻击修复（MIMO EB-008 A1，2026-09-29）：validated_at 为投影排序键（Rev-4 §5），
# 调用方若写入未来时间戳，会压过之后的 invalidate 级联（级联写 now），使
# Authority 投影停留在 VALIDATED、approve 穿透。允许时钟偏移，拒绝远期未来时间。
_MAX_CLOCK_SKEW = timedelta(minutes=5)

__all__ = [
    "AUTHORITY_INVALIDATED",
    "AUTHORITY_NONE",
    "AUTHORITY_REJECTED",
    "AUTHORITY_VALIDATED",
    "EvidenceRepository",
    "SYSTEM_VALIDATOR",
    "delete_validation_event",
    "update_validation_event",
]


class EvidenceRepository(BaseRepository):
    """validation_events append-only Repository。

    唯一写入口：append_event() / append_human_review_event() / invalidate_claims_*()。
    公共接口无 update/delete（5.5 验收：应用代码无 UPDATE/DELETE validation_events 路径）。
    """

    # ------------------------------------------------------------------ 写入
    async def append_event(
        self,
        event: ValidationEvent,
        *,
        candidate_id: uuid.UUID,
        source_version_id: uuid.UUID,
        review_proof: str | None = None,
    ) -> ValidationEventRecord:
        """持久化一条 ValidationEvent（INSERT-only）。

        - replay 幂等：既有 latest 同结果 → no-op 返回既有行（R4）
        - 状态机：enforce_state_transition 违规 → ValueError（terminal 拒新事件等）
        - 首事件为 invalidated → ValueError（无 prior VALIDATED）
        """
        if event.validation_method == "human_review" and not review_proof:
            raise RepositoryError(
                "human_review ValidationEvent requires review_proof (EB-008 §5.2)"
            )
        # A1 防御：未来时间戳会劫持 latest-by-validated_at 投影，使后续 invalidate 失效。
        if event.validated_at > datetime.now(timezone.utc) + _MAX_CLOCK_SKEW:
            raise ValueError(
                f"validated_at {event.validated_at.isoformat()} is more than "
                f"{_MAX_CLOCK_SKEW} in the future; rejecting (EB-008 A1 projection attack)"
            )
        existing = await self.find_events_for_claim(candidate_id, event.claim_id)
        if existing:
            latest = max(existing, key=lambda r: r.validated_at)
            # replay 幂等（R1-R5）：同结果重放不改 Authority，返回既有
            if latest.validation_result == event.validation_result:
                return latest
        # 状态机检查（与 domain AppendOnlyEventLog 同源）；违规抛 ValueError
        enforce_state_transition(
            tuple(_to_domain(r) for r in existing),
            event.validation_result,
            event.claim_id,
        )
        record = ValidationEventRecord(
            claim_id=event.claim_id,
            candidate_id=candidate_id,
            source_version_id=source_version_id,
            validation_result=event.validation_result,
            checks=[_check_to_dict(c) for c in event.checks],
            validation_method=event.validation_method,
            validator=event.validator,
            reference_ids=list(event.reference_ids) if event.reference_ids else None,
            review_proof=review_proof,
            validated_at=event.validated_at,
        )
        await self.add(record)
        await self.flush()  # 回填 record.id
        return record

    async def append_human_review_event(
        self,
        *,
        candidate_id: uuid.UUID,
        source_version_id: uuid.UUID,
        claim_id: str,
        review_result: str,
        reviewer_id: str,
        reviewed_at: datetime,
        review_proof: str,
    ) -> ValidationEventRecord:
        """人工审核结果 → human_review ValidationEvent（92号 §5.2 生成时机）。

        review_result ∈ {validated, rejected}（对应人工 approve / reject）。
        proof 由调用方（AdmissionService）生成——生成与持久化分离，便于测试与审计。
        """
        if review_result not in ("validated", "rejected"):
            raise RepositoryError(
                f"human review_result must be validated|rejected, got {review_result!r}"
            )
        from app.domains.evidence.proof import human_validator

        event = ValidationEvent(
            event_id=f"ve-{claim_id}-{uuid.uuid4().hex[:8]}",
            claim_id=claim_id,
            validation_result=review_result,
            checks=(),
            validation_method="human_review",
            validator=human_validator(reviewer_id),
            validated_at=reviewed_at,
        )
        return await self.append_event(
            event,
            candidate_id=candidate_id,
            source_version_id=source_version_id,
            review_proof=review_proof,
        )

    # ------------------------------------------------------------------ 读取
    async def find_events_for_claim(
        self, candidate_id: uuid.UUID, claim_id: str
    ) -> list[ValidationEventRecord]:
        """(candidate_id, claim_id) 全事件，按 validated_at 升序。"""
        res = await self._session.execute(
            select(ValidationEventRecord)
            .where(
                ValidationEventRecord.candidate_id == candidate_id,
                ValidationEventRecord.claim_id == claim_id,
            )
            .order_by(ValidationEventRecord.validated_at)
        )
        return list(res.scalars().all())

    async def find_events_for_candidate(
        self, candidate_id: uuid.UUID
    ) -> list[ValidationEventRecord]:
        """candidate 全部事件（投影/级联用）。"""
        res = await self._session.execute(
            select(ValidationEventRecord)
            .where(ValidationEventRecord.candidate_id == candidate_id)
            .order_by(ValidationEventRecord.validated_at)
        )
        return list(res.scalars().all())

    # ------------------------------------------------------------------ 投影
    async def project_authority(
        self, candidate_id: uuid.UUID, claim_id: str
    ) -> tuple[str, ValidationEventRecord | None]:
        """Authority 投影（Rev-4 §5 /92号 §5.3）：latest-by-validated_at wins。

        返回 (state, latest_record)；无事件 → (AUTHORITY_NONE, None)。
        proof 验证不在本函数内（Boundary 职责）——调用方对 human_review 记录
        另行 verify_review_proof()。
        """
        events = await self.find_events_for_claim(candidate_id, claim_id)
        if not events:
            return AUTHORITY_NONE, None
        latest = max(events, key=lambda r: r.validated_at)
        return latest.validation_result, latest

    async def project_candidate_authority(
        self, candidate_id: uuid.UUID
    ) -> dict[str, tuple[str, ValidationEventRecord | None]]:
        """candidate 下每个 claim_id 的 Authority 投影。"""
        events = await self.find_events_for_candidate(candidate_id)
        by_claim: dict[str, list[ValidationEventRecord]] = {}
        for e in events:
            by_claim.setdefault(e.claim_id, []).append(e)
        out: dict[str, tuple[str, ValidationEventRecord | None]] = {}
        for claim, rows in by_claim.items():
            latest = max(rows, key=lambda r: r.validated_at)
            out[claim] = (latest.validation_result, latest)
        return out

    # ------------------------------------------------------------------ invalidate 级联（5.4）
    async def invalidate_claims_for_source_version(
        self,
        source_version_id: uuid.UUID,
        *,
        reason: str,
        validation_method: str = "byte_proven",
        validator: str = SYSTEM_VALIDATOR,
    ) -> list[ValidationEventRecord]:
        """source_version 失效级联：该 sv 下所有 latest=VALIDATED 的 claim → INVALIDATED。

        触发场景（92号 §5.4）：source_version 被取代 / OCR 升级等。
        恢复路径：不在同 claim 恢复（INVALIDATED terminal）；新证据 → 新 le_hash →
        新 candidate → 新 Authority。
        """
        res = await self._session.execute(
            select(AdmissionCandidate).where(
                AdmissionCandidate.source_version_id == source_version_id
            )
        )
        candidates = list(res.scalars().all())
        return await self._invalidate_candidates(
            candidates, reason=reason,
            validation_method=validation_method, validator=validator,
        )

    async def invalidate_claims_for_annotation(
        self,
        annotation_id: uuid.UUID,
        *,
        reason: str,
        validation_method: str = "structural_consistency",
        validator: str = SYSTEM_VALIDATOR,
    ) -> list[ValidationEventRecord]:
        """annotation 失效级联：该 annotation 下所有 latest=VALIDATED 的 claim → INVALIDATED。

        触发场景（92号 §5.4）：annotation 变更（valid→superseded）。
        """
        res = await self._session.execute(
            select(AdmissionCandidate).where(
                AdmissionCandidate.annotation_id == annotation_id
            )
        )
        candidates = list(res.scalars().all())
        return await self._invalidate_candidates(
            candidates, reason=reason,
            validation_method=validation_method, validator=validator,
        )

    async def _invalidate_candidates(
        self,
        candidates: list[AdmissionCandidate],
        *,
        reason: str,
        validation_method: str,
        validator: str,
    ) -> list[ValidationEventRecord]:
        """对每个 latest=VALIDATED 的 (candidate, claim) append INVALIDATED 事件。

        已 INVALIDATED/REJECTED 的 claim 跳过（terminal，无 resurrection）；
        审计：checks.detail 记录触发原因（92号 §5.4）。
        """
        created: list[ValidationEventRecord] = []
        now = datetime.now(timezone.utc)
        for cand in candidates:
            events = await self.find_events_for_candidate(cand.id)
            by_claim: dict[str, list[ValidationEventRecord]] = {}
            for e in events:
                by_claim.setdefault(e.claim_id, []).append(e)
            for claim_id, rows in by_claim.items():
                latest = max(rows, key=lambda r: r.validated_at)
                if latest.validation_result != "validated":
                    continue  # terminal 或 rejected：不级联
                # A1 防御：级联事件必须严格晚于既有 latest，否则 invalidate 输掉投影。
                cascade_at = max(now, latest.validated_at) + timedelta(microseconds=1)
                event = ValidationEvent(
                    event_id=f"ve-{claim_id}-{uuid.uuid4().hex[:8]}",
                    claim_id=claim_id,
                    validation_result="invalidated",
                    checks=(
                        CheckResult(
                            check_id="INVALIDATE_CASCADE",
                            result="fail",
                            detail=reason,
                        ),
                    ),
                    validation_method=validation_method,
                    validator=validator,
                    validated_at=cascade_at,
                )
                rec = await self.append_event(
                    event,
                    candidate_id=cand.id,
                    source_version_id=cand.source_version_id,
                )
                created.append(rec)
        return created


# ------------------------------------------------------------------ helpers
def _check_to_dict(check: CheckResult) -> dict:
    return {"check_id": check.check_id, "result": check.result, "detail": check.detail}


def _to_domain(record: ValidationEventRecord) -> ValidationEvent:
    """ORM 行 → domain ValidationEvent（状态机复用 domain 类型）。"""
    return ValidationEvent(
        event_id=str(record.id),
        claim_id=record.claim_id,
        validation_result=record.validation_result,
        checks=tuple(
            CheckResult(
                check_id=c.get("check_id", ""),
                result=c.get("result", "fail"),
                detail=c.get("detail"),
            )
            for c in (record.checks or [])
        ),
        validation_method=record.validation_method,
        validator=record.validator,
        reference_ids=tuple(record.reference_ids or ()),
        validated_at=record.validated_at,
    )


async def update_validation_event(*_args: object, **_kwargs: object) -> None:
    """显式拒 UPDATE（5.5 验收探针可调用；正常代码不得引用）。"""
    raise AppendOnlyViolation("validation_events is append-only; UPDATE forbidden")


async def delete_validation_event(*_args: object, **_kwargs: object) -> None:
    """显式拒 DELETE（5.5 验收探针可调用；正常代码不得引用）。"""
    raise AppendOnlyViolation("validation_events is append-only; DELETE forbidden")
