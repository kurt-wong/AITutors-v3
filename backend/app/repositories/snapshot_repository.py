"""数据域 C Repository：快照 append-only + decision_status 唯一入口防护（段 A / 段 G）。"""

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.snapshot import (
    AdmissionCandidate,
    AdmissionEvent,
    SemanticAnnotation,
)
from app.models.source import DocumentSourceVersion
from app.repositories.base import AppendOnlyViolation, BaseRepository, RepositoryError


class SnapshotRepository(BaseRepository):
    async def create_semantic_annotation(
        self,
        *,
        source_version_id: uuid.UUID,
        annotation_schema_version: str,
        payload: dict,
        status: str,
        logical_execution_stage: str,
        logical_execution_hash: str,
        prompt_version: str,
        model_config_hash: str,
        attempt_id: uuid.UUID | None = None,
    ) -> SemanticAnnotation:
        """幂等写（H Phase 6，H0-6）：锚 UNIQUE(stage,hash) ON CONFLICT DO NOTHING。

        BUG-V3-046（F-5）：10 §4.5 —— annotation 只能引用 sealed source_version。
        这是数据不变量（data invariant），不是业务规则：repository boundary 强制。

        插入成功 → returning 返回新行；同 (stage,hash) 冲突（并发或既有）→ re-read existing：
          valid/superseded → 返回既有（idempotent success）；
          invalid（残留失败行，find_annotation_by_le_hash 不复用）→ RepositoryError —— 同 LE
          valid 写入被 invalid 残留阻挡，须新 LE（原 IntegrityError 语义的显式化）。
        """
        # BUG-V3-046：sealed invariant — annotation 永远不能引用未封存 SourceVersion
        sv_row = await self._session.get(DocumentSourceVersion, source_version_id)
        if sv_row is None:
            raise RepositoryError(
                f"source_version {source_version_id} not found"
            )
        if sv_row.status != "sealed":
            raise RepositoryError(
                f"source_version {source_version_id} status={sv_row.status} "
                f"(not sealed) — annotation on non-sealed source is forbidden "
                f"(10 §4.5)"
            )
        stmt = (
            pg_insert(SemanticAnnotation)
            .values(
                source_version_id=source_version_id,
                annotation_schema_version=annotation_schema_version,
                prompt_version=prompt_version,
                model_config_hash=model_config_hash,
                payload=payload,
                status=status,
                logical_execution_stage=logical_execution_stage,
                logical_execution_hash=logical_execution_hash,
                attempt_id=attempt_id,
            )
            .on_conflict_do_nothing(
                index_elements=["logical_execution_stage", "logical_execution_hash"]
            )
            .returning(SemanticAnnotation)
        )
        res = await self._session.execute(stmt)
        row = res.scalars().first()
        if row is not None:
            return row
        existing = await self._annotation_by_le(
            logical_execution_stage=logical_execution_stage,
            logical_execution_hash=logical_execution_hash,
        )
        if existing is None:
            raise RepositoryError(
                "annotation (stage,hash) conflict but no existing row readable"
            )
        if existing.status not in ("valid", "superseded"):
            raise RepositoryError(
                "same LE annotation already ended %r; valid write requires new LE"
                % (existing.status,)
            )
        return existing

    async def _annotation_by_le(
        self, *, logical_execution_stage: str, logical_execution_hash: str
    ) -> SemanticAnnotation | None:
        """任意 status 的 (stage,hash) 读（冲突 re-read；区别于 find_annotation_by_le_hash
        只读 valid/superseded）。"""
        res = await self._session.execute(
            select(SemanticAnnotation).where(
                SemanticAnnotation.logical_execution_stage == logical_execution_stage,
                SemanticAnnotation.logical_execution_hash == logical_execution_hash,
            )
        )
        return res.scalars().first()

    async def create_admission_candidate(
        self,
        *,
        unit_type: str,
        source_version_id: uuid.UUID,
        annotation_id: uuid.UUID,
        build_versions: dict,
        input_identity: dict,
        payload: dict,
        logical_execution_stage: str,
        logical_execution_hash: str,
        gate_decision: dict | None = None,
        review_trail: list | None = None,
        attempt_id: uuid.UUID | None = None,
    ) -> AdmissionCandidate:
        """创建候选：decision_status 固定 pending_review（30 §12/20 §8.2 唯一入口，不得以其它值创建）。

        H Phase 6（H0-6）：ON CONFLICT DO NOTHING 锚 UNIQUE(stage,hash)；冲突 → re-read
        existing（恒 pending_review，idempotent success）。
        """
        stmt = (
            pg_insert(AdmissionCandidate)
            .values(
                unit_type=unit_type,
                source_version_id=source_version_id,
                annotation_id=annotation_id,
                decision_status="pending_review",
                gate_decision=gate_decision,
                build_versions=build_versions,
                input_identity=input_identity,
                payload=payload,
                review_trail=review_trail,
                logical_execution_stage=logical_execution_stage,
                logical_execution_hash=logical_execution_hash,
                attempt_id=attempt_id,
            )
            .on_conflict_do_nothing(
                index_elements=["logical_execution_stage", "logical_execution_hash"]
            )
            .returning(AdmissionCandidate)
        )
        res = await self._session.execute(stmt)
        row = res.scalars().first()
        if row is not None:
            return row
        existing = await self.find_candidate_by_le_hash(
            logical_execution_stage=logical_execution_stage,
            logical_execution_hash=logical_execution_hash,
        )
        if existing is None:
            raise RepositoryError(
                "admission_candidate (stage,hash) conflict but no existing row readable"
            )
        return existing

    async def update_snapshot(self, *_args: object, **_kwargs: object) -> None:
        """快照表 append-only：UPDATE → 抛错。"""
        raise AppendOnlyViolation("snapshot domain tables are append-only")

    async def update_candidate_decision(
        self, *_args: object, **_kwargs: object
    ) -> None:
        """decision_status 唯一入口（approve()/reject()，30 §12 / 20 §8.2）段 G 实装；Repository 不暴露直写。"""
        raise AppendOnlyViolation(
            "decision_status only via approve()/reject() unique entry (segment G)"
        )

    async def find_annotation_by_le_hash(
        self, *, logical_execution_stage: str, logical_execution_hash: str
    ) -> SemanticAnnotation | None:
        """幂等查找：(stage, hash) 查既有 annotation（valid 或 superseded）。invalid 不复用。"""
        res = await self._session.execute(
            select(SemanticAnnotation).where(
                SemanticAnnotation.logical_execution_stage == logical_execution_stage,
                SemanticAnnotation.logical_execution_hash == logical_execution_hash,
                SemanticAnnotation.status.in_(["valid", "superseded"]),
            )
        )
        return res.scalars().first()

    async def set_annotation_status(
        self, annotation_id: uuid.UUID, new_status: str
    ) -> SemanticAnnotation:
        """只允许 valid→superseded 流转（20 §4.7；不作通用 UPDATE）。"""
        row = await self._session.get(SemanticAnnotation, annotation_id)
        if row is None:
            raise RepositoryError(f"annotation {annotation_id} not found")
        if row.status != "valid" or new_status != "superseded":
            raise RepositoryError(
                f"invalid status transition: {row.status!r} → {new_status!r} "
                f"(only valid→superseded allowed)"
            )
        row.status = new_status
        return row

    # ------------------------------------------------------------------ 段 G
    async def find_candidate_by_le_hash(
        self, *, logical_execution_stage: str, logical_execution_hash: str
    ) -> AdmissionCandidate | None:
        """candidate 幂等查找：(stage, hash) 查既有（10 §3 / §5.2）。"""
        res = await self._session.execute(
            select(AdmissionCandidate).where(
                AdmissionCandidate.logical_execution_stage == logical_execution_stage,
                AdmissionCandidate.logical_execution_hash == logical_execution_hash,
            )
        )
        return res.scalars().first()

    async def lock_candidate(self, candidate_id: uuid.UUID) -> AdmissionCandidate:
        """Admission 事务锁行（SELECT FOR UPDATE）——approve/reject 并发防双物化。"""
        res = await self._session.execute(
            select(AdmissionCandidate)
            .where(AdmissionCandidate.id == candidate_id)
            .with_for_update()
        )
        row = res.scalar_one_or_none()
        if row is None:
            raise RepositoryError(f"admission_candidate {candidate_id} not found")
        return row

    async def find_annotation_by_id(
        self, annotation_id: uuid.UUID
    ) -> SemanticAnnotation | None:
        """读 annotation（物化取 document_metadata_claims.subject/grade，BUG-V3-021 M1）。"""
        return await self._session.get(SemanticAnnotation, annotation_id)

    async def append_review_trail(
        self, candidate_id: uuid.UUID, entry: dict
    ) -> AdmissionCandidate:
        """人工 review append 证据（20 §8.2 append 不覆盖）。只加证据，不迁状态。

        BUG-V3-025 终裁：`time` 由本方法统一注入（UTC ISO-8601，review event 的
        provenance timestamp）；调用方只提供业务字段（decision/verified_by/reviewer_id
        + confirmed_fields 或 reasons），不得手填 time。
        """
        from datetime import datetime, timezone

        row = await self.lock_candidate(candidate_id)
        trail = list(row.review_trail) if row.review_trail else []
        entry = {**entry, "time": datetime.now(timezone.utc).isoformat()}
        trail.append(entry)
        row.review_trail = trail
        return row

    async def _transition_decision(
        self, candidate_id: uuid.UUID, new_status: str
    ) -> AdmissionCandidate:
        """decision_status 受控迁移（AdmissionService 专用；P0-G-001：模块级约定非公共 API）。

        approve()/reject() 之外无合法 transition API；Repository 公共接口
        `update_candidate_decision` 恒抛 AppendOnlyViolation。
        """
        from datetime import datetime, timezone

        row = await self.lock_candidate(candidate_id)
        if row.decision_status not in ("pending_review",):
            raise RepositoryError(
                f"invalid decision transition: {row.decision_status!r} → {new_status!r} "
                f"(only pending_review has outgoing edge)"
            )
        row.decision_status = new_status
        row.decided_at = datetime.now(timezone.utc)
        return row

    async def create_admission_event(
        self,
        *,
        candidate_id: uuid.UUID,
        created_question_ids: list[uuid.UUID] | None = None,
        created_instance_ids: list[uuid.UUID] | None = None,
    ) -> AdmissionEvent:
        """admission_events（10 §5.4）。candidate_id UNIQUE：同一候选至多一条物化记录。"""
        event = AdmissionEvent(
            candidate_id=candidate_id,
            created_question_ids=created_question_ids,
            created_instance_ids=created_instance_ids,
        )
        await self.add(event)
        return event
