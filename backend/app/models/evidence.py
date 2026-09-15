"""Evidence Authority 持久化模型（EB-008 /92号 §5.1 §6，DEC-016）。

validation_events：Evidence Authority 的唯一持久化 ledger（append-only）。

约束（92号 §5.5，Phase-1 必做）：
- 应用层：Repository 无 update/delete 方法；唯一写入口 insert/append
- 应用层：状态机检查在 insert 前执行（terminal 状态拒新事件）
- DB 层触发器为后续加固项（trade-off 已记录，92号 §7 风险 2）

Authority 投影 = 事件序列 latest-by-validated_at wins（Rev-4 §5）；
本表无 UPDATE 路径，进程重启后投影结果不变（验收标准，92号 §5.1）。
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin, _utcnow


class ValidationEventRecord(UUIDPrimaryKeyMixin, Base):
    """validation_events（92号 §6 schema）。

    - claim_id：unit_id（candidate 内 semantic unit 标识）
    - AuthorityIdentity = (source_version_id, candidate_id, claim_id)（I5；run_id 禁入，I6）
    - review_proof：仅 human_review 事件非空（92号 §5.2）
    - checks / reference_ids：JSONB 结构化审计（CheckResult 列表 / EvidenceReference ID 列表）
    """

    __tablename__ = "validation_events"
    __table_args__ = (
        Index("idx_ve_claim_candidate", "claim_id", "candidate_id"),
        Index("idx_ve_candidate", "candidate_id"),
    )

    claim_id: Mapped[str] = mapped_column(String, nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("admission_candidates.id"), nullable=False
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_source_versions.id"), nullable=False
    )
    validation_result: Mapped[str] = mapped_column(String, nullable=False)
    checks: Mapped[list] = mapped_column(JSONB, nullable=False)
    validation_method: Mapped[str] = mapped_column(String, nullable=False)
    validator: Mapped[str] = mapped_column(String, nullable=False)
    reference_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    review_proof: Mapped[str | None] = mapped_column(String, nullable=True)
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
