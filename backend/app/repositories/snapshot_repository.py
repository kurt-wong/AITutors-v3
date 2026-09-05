"""数据域 C Repository：快照 append-only + decision_status 唯一入口防护（段 A）。"""

import uuid

from app.models.snapshot import (
    AdmissionCandidate,
    SemanticAnnotation,
)
from app.repositories.base import AppendOnlyViolation, BaseRepository


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
        prompt_version: str | None = None,
        model_config_hash: str | None = None,
        attempt_id: uuid.UUID | None = None,
    ) -> SemanticAnnotation:
        annotation = SemanticAnnotation(
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
        await self.add(annotation)
        return annotation

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
        review_trail: dict | None = None,
        attempt_id: uuid.UUID | None = None,
    ) -> AdmissionCandidate:
        """创建候选：decision_status 固定 pending_review（30 §12/20 §8.2 唯一入口，不得以其它值创建）。"""
        candidate = AdmissionCandidate(
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
        await self.add(candidate)
        return candidate

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
