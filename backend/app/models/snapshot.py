"""数据域 C（10 §5）：管线快照域 3 张表（immutable snapshot）。schema source of truth = 10 v1.2.1。"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin


class SemanticAnnotation(UUIDPrimaryKeyMixin, Base):
    """semantic_annotations（10 §5.1）。payload 只含 Semantic Interpretation，永不回写 Source。"""

    __tablename__ = "semantic_annotations"
    __table_args__ = (
        UniqueConstraint("logical_execution_stage", "logical_execution_hash"),
    )

    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    annotation_schema_version: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    model_config_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    logical_execution_stage: Mapped[str] = mapped_column(String, nullable=False)
    logical_execution_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class AdmissionCandidate(UUIDPrimaryKeyMixin, Base):
    """admission_candidates（10 §5.2）。decision_status 只经 approve()/reject() 唯一入口写。"""

    __tablename__ = "admission_candidates"
    __table_args__ = (
        UniqueConstraint("logical_execution_stage", "logical_execution_hash"),
    )

    unit_type: Mapped[str] = mapped_column(String, nullable=False)
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    annotation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("semantic_annotations.id"), nullable=True
    )
    decision_status: Mapped[str] = mapped_column(String, nullable=False)
    gate_decision: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    build_versions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    input_identity: Mapped[dict] = mapped_column(JSONB, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    review_trail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    logical_execution_stage: Mapped[str] = mapped_column(String, nullable=False)
    logical_execution_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class AdmissionEvent(UUIDPrimaryKeyMixin, Base):
    """admission_events（10 §5.4）。candidate_id UNIQUE（同一候选至多一条物化记录）。"""

    __tablename__ = "admission_events"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("admission_candidates.id"), nullable=False, unique=True
    )
    materialized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_question_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(Uuid), nullable=True
    )
    created_instance_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(Uuid), nullable=True
    )
