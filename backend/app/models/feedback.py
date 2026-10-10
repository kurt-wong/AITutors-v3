"""Human Verification Console feedback domain (M3b).

Feedback is observational only: records problem + evidence + user judgment.
Never mutates Question / Instance / SourceVersion / Gate/Admission state.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin

# 首版封闭类别（Owner M3b §4.2）；扩展需契约变更，不静默加值。
FEEDBACK_CATEGORIES: tuple[str, ...] = (
    "stem_missing_or_incomplete",
    "option_missing_or_incomplete",
    "answer_missing_or_wrong",
    "explanation_missing_or_wrong",
    "material_missing_or_bad_ref",
    "latex_render_error",
    "identity_or_number_mismatch",
    "subject_grade_wrong_or_unset",
    "other",
)

FEEDBACK_STATUSES: tuple[str, ...] = (
    "open",
    "in_review",
    "resolved",
    "rejected",
)


class QuestionFeedback(UUIDPrimaryKeyMixin, Base):
    """question_feedbacks：结构化人工反馈（可追溯、与修复分离）。"""

    __tablename__ = "question_feedbacks"

    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("questions.id"), nullable=False, index=True
    )
    instance_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("question_instances.id"), nullable=True
    )
    source_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=True
    )
    producer_unit_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # 可复核来源：源行区间 / span_id / occurrence 等（不改写正文）
    source_evidence: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # 提交时内容快照，避免题目后续变化导致旧反馈失上下文
    content_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )
    # 仅记录处理备注，不代表自动修复
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
