"""数据域 A（10 §6）：内容事实域 10 张表（live relational）。schema source of truth = 10 v1.2.1。"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """questions（10 §6.1）。无 status 列（存在即已 Admission）。"""

    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("dedup_key", name="uq_questions_dedup_key"),
    )

    subject: Mapped[str] = mapped_column(String, nullable=False)
    grade: Mapped[str] = mapped_column(String, nullable=False)
    canonical_question_type: Mapped[str] = mapped_column(String, nullable=False)
    dedup_key: Mapped[str] = mapped_column(String(64), nullable=False)


class QuestionInstance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """question_instances（10 §6.2）。UNIQUE(question_id, source_version_id, occurrence_key)。"""

    __tablename__ = "question_instances"
    __table_args__ = (
        UniqueConstraint("question_id", "source_version_id", "occurrence_key"),
    )

    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("questions.id"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id"), nullable=False
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    unit_group_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("unit_groups.id"), nullable=True
    )
    occurrence_key: Mapped[str] = mapped_column(String(64), nullable=False)
    question_number: Mapped[str] = mapped_column(String, nullable=False)
    question_number_range: Mapped[str] = mapped_column(String, nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    instance_order: Mapped[int] = mapped_column(Integer, nullable=False)
    logical_execution_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    logical_execution_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class InstanceRoleContent(UUIDPrimaryKeyMixin, Base):
    """instance_role_contents（10 §6.3）。text 永不来自 LLM；source_span 是应用层 provenance。"""

    __tablename__ = "instance_role_contents"
    __table_args__ = (
        UniqueConstraint("instance_id", "role", "label", "role_index"),
    )

    instance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("question_instances.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    role_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_span: Mapped[dict] = mapped_column(JSONB, nullable=False)
    answer_status: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class Material(UUIDPrimaryKeyMixin, Base):
    """materials（10 §6.4）。Source-scoped；M1 不做跨 Source Version 自动共享。"""

    __tablename__ = "materials"

    subject: Mapped[str] = mapped_column(String, nullable=False)
    grade: Mapped[str] = mapped_column(String, nullable=False)
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_span: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dedup_key: Mapped[str | None] = mapped_column(String(64), nullable=True)


class MaterialLink(Base):
    """material_links（10 §6.4）。10 无显式 UNIQUE 声明——复合 PK 表达 link 唯一性，不额外加 UNIQUE。"""

    __tablename__ = "material_links"

    instance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("question_instances.id"), primary_key=True
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("materials.id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String, primary_key=True)
    order: Mapped[int] = mapped_column(Integer, primary_key=True)


class UnitGroup(UUIDPrimaryKeyMixin, Base):
    """unit_groups（10 §6.5）。只表达 presentation/grouping identity，不决定 Question 语义独立性。"""

    __tablename__ = "unit_groups"

    unit_type: Mapped[str] = mapped_column(String, nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id"), nullable=False
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    question_number_range: Mapped[str | None] = mapped_column(String, nullable=True)
    shared_material_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("materials.id"), nullable=True
    )


class UnitGroupMember(Base):
    """unit_group_members（10 §6.5）。10 无显式 UNIQUE 声明——复合 PK，不额外加 UNIQUE。"""

    __tablename__ = "unit_group_members"

    unit_group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("unit_groups.id"), primary_key=True
    )
    instance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("question_instances.id"), primary_key=True
    )
    member_order: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_in_group: Mapped[str | None] = mapped_column(String, nullable=True)


class InstanceFigureLink(Base):
    """instance_figure_links（10 §6.6）。唯一 = 复合 PK(instance, figure, role, order)。"""

    __tablename__ = "instance_figure_links"

    instance_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("question_instances.id"), primary_key=True
    )
    source_figure_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("source_figures.id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String, primary_key=True)
    order: Mapped[int] = mapped_column(Integer, primary_key=True)


class KnowledgeNode(UUIDPrimaryKeyMixin, Base):
    """knowledge_nodes（10 §6.7）。M1 Knowledge 为 optional derived mapping，非 Admission 硬依赖。"""

    __tablename__ = "knowledge_nodes"

    tree_version: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)


class QuestionKnowledgeLink(Base):
    """question_knowledge_links（10 §6.7）。10 无显式 UNIQUE 声明——复合 PK，不额外加 UNIQUE。"""

    __tablename__ = "question_knowledge_links"

    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("questions.id"), primary_key=True
    )
    knowledge_node_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("knowledge_nodes.id"), primary_key=True
    )
    mapped_by: Mapped[str] = mapped_column(String, primary_key=True)
    mapped_from_claim: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
