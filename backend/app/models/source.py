"""数据域 B（10 §4）：不可变源域 6 张表。schema source of truth = 10 v1.2.1。"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import ProvenanceMixin, TimestampMixin, UUIDPrimaryKeyMixin, _utcnow


class Document(UUIDPrimaryKeyMixin, Base):
    """documents（10 §4.1）。不保存最终题目文本；processing_status 是 Source 内容生命周期摘要。"""

    __tablename__ = "documents"

    original_object_key: Mapped[str] = mapped_column(String, nullable=False)
    original_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    upload_meta: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processing_status: Mapped[str] = mapped_column(String, nullable=False)


class DocumentSourceVersion(UUIDPrimaryKeyMixin, ProvenanceMixin, Base):
    """document_source_versions（10 §4.2）。status=sealed 后禁 UPDATE（Repository 抛错）。"""

    __tablename__ = "document_source_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id"), nullable=False
    )
    artifact_kind: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    body_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    integrity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False)
    text_coverage: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    source_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)


class DocumentSourceLine(UUIDPrimaryKeyMixin, Base):
    """document_source_lines（10 §4.3）。UNIQUE(source_version_id, line_ref)。"""

    __tablename__ = "document_source_lines"
    __table_args__ = (UniqueConstraint("source_version_id", "line_ref"),)

    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    line_ref: Mapped[str] = mapped_column(String, nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    line_no_in_page: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    block_type: Mapped[str] = mapped_column(String, nullable=False)
    bbox: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    selected_source: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    line_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class SourceFigure(UUIDPrimaryKeyMixin, Base):
    """source_figures（10 §4.4）。无 role_owner/题号归属字段。"""

    __tablename__ = "source_figures"

    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    figure_id: Mapped[str] = mapped_column(String, nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox: Mapped[dict] = mapped_column(JSONB, nullable=False)
    placement: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    object_key: Mapped[str] = mapped_column(String, nullable=False)
    figure_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class DocumentActiveSource(Base):
    """document_active_sources（10 §4.5）。复合 PK(document_id, role)。"""

    __tablename__ = "document_active_sources"

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String, primary_key=True)
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    selection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class DocumentSourceSelectionEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """document_source_selection_events（10 §4.5 append-only；列冻结缺失 → 补列，bug 见 bugs.md #2）。"""

    __tablename__ = "document_source_selection_events"

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    old_source_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=True
    )
    new_source_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=True
    )
    operated_by: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_id: Mapped[str | None] = mapped_column(String, nullable=True)
