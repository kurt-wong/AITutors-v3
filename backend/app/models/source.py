"""数据域 B（10 §4）：不可变源域 6 张表。schema source of truth = 10 v1.2.1。"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
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

# ── Artifact compatibility rules（Frozen Spec 10 §4.2 + Errata PRIMARY-PATH-01 §2.6）──
# 单一权威定义。seal path 与 repository path 均调用本模块的校验函数。
# 禁止在其他位置复制闭集或配对规则。

_ARTIFACT_KINDS = frozenset({"original_binary", "raw_l1", "canonical_l1"})

_ROLE_PROVIDER_PAIRS: dict[str, frozenset[str]] = {
    "native": frozenset({"native"}),
    "ocr_ppsv3": frozenset({"ppsv3"}),
    "ocr_ppsvl": frozenset({"paddleocr-vl"}),
    "docx": frozenset({"docx"}),
    "preprocessing": frozenset({"preprocessing"}),
    # Spec 10 §4.2: "canonical role 无 provider" — DB 列 NOT NULL，约定空字符串。
    # [NEW-GAP-3 登记] provider="" 是实现约定（Spec 未指定 NOT NULL 列的空 provider 存储值），
    # 不是 Spec 声明。如 Owner 裁定其他约定，需同步修改此处与测试 fixture。
    "canonical": frozenset({""}),
}


def validate_artifact_compatibility(role: str, provider: str, artifact_kind: str) -> None:
    """校验 role/provider 封闭配对 + artifact_kind 闭集。非法值 fail-fast。

    所有 DocumentSourceVersion 写入路径必须经此校验（seal + repository）。
    """
    if artifact_kind not in _ARTIFACT_KINDS:
        raise ValueError(
            f"invalid artifact_kind: {artifact_kind!r} "
            f"(allowed: {sorted(_ARTIFACT_KINDS)})"
        )
    allowed = _ROLE_PROVIDER_PAIRS.get(role)
    if allowed is None:
        raise ValueError(f"unknown role: {role!r}")
    if provider not in allowed:
        raise ValueError(
            f"role/provider mismatch: role={role!r} provider={provider!r}"
            f" (allowed: {sorted(allowed)})"
        )


class Document(UUIDPrimaryKeyMixin, Base):
    """documents（10 §4.1）。不保存最终题目文本；processing_status 是 Source 内容生命周期摘要。"""

    __tablename__ = "documents"
    # BUG-V3-007 终裁（2026-09-07）：original_sha256 = Source/Document Identity，一个原始文件
    # 对应一个 Document 主档（非 Seal 层全局唯一——那是 document_source_versions 的职责）。
    __table_args__ = (
        UniqueConstraint("original_sha256", name="uq_documents_original_sha256"),
    )

    original_object_key: Mapped[str] = mapped_column(String, nullable=False)
    original_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    upload_meta: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processing_status: Mapped[str] = mapped_column(String, nullable=False)


class DocumentSourceVersion(UUIDPrimaryKeyMixin, ProvenanceMixin, Base):
    """document_source_versions（10 §4.2）。status=sealed 后禁 UPDATE（Repository 抛错）。"""

    __tablename__ = "document_source_versions"
    # BUG-V3-007 终裁：Seal Version 的 canonical uniqueness 由 Frozen LE Identity 表达
    # UNIQUE(logical_execution_stage, logical_execution_hash)——同 Seal 执行身份至多一个 version；
    # 跨 role/provider 得不同 LE hash → 多 version 合法。禁 UNIQUE(original_sha256)（Seal 层）。
    # NULLS DISTINCT（默认）：非 seal 路径（stage/hash NULL）的 version 不受约束。
    __table_args__ = (
        UniqueConstraint(
            "logical_execution_stage", "logical_execution_hash",
            name="uq_source_versions_le",
        ),
    )

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
    # BUG-011-E（10 §4.4 v1.2.2 ⑥）：UNIQUE(source_version_id, figure_id) = figure identity
    # invariant（version-scoped）；跨 version 同 figure_id 合法。
    __table_args__ = (
        UniqueConstraint(
            "source_version_id", "figure_id", name="uq_source_figures_figure_id"
        ),
    )

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


class DocumentSourceSpan(UUIDPrimaryKeyMixin, Base):
    """document_source_spans（Phase I-3）。Source layout evidence。

    span_hash = SHA256(text + font + size + flags + bbox + origin)，
    描述 source evidence instance（layout evidence identity），
    不表示 semantic equality。
    """

    __tablename__ = "document_source_spans"
    __table_args__ = (
        UniqueConstraint("source_version_id", "line_ref", "seq"),
        Index("idx_source_spans_version_line", "source_version_id", "line_ref", "seq"),
        Index("idx_source_spans_hash", "span_hash"),
    )

    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    line_ref: Mapped[str] = mapped_column(String, nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    font: Mapped[str | None] = mapped_column(String, nullable=True)
    size: Mapped[float | None] = mapped_column(Float, nullable=True)
    flags: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    origin: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    span_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


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
