"""运行域表（30 §10/§11/§17）。段 C 仅建 llm_call_audit + budget；tasks/task_claims 归段 H。

schema source of truth = 30；audit 列 SQL 类型为实现自由度（spec 未给类型）。
budget.reserved 为规格缺口补列（30 §11 需「预留量」，§17 列清单遗漏 → BUG-V3-006）。
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import _utcnow


class LlmCallAudit(Base):
    """llm_call_audit（30 §10 append-only 不可变）。真实 LLM 请求一次一条。"""

    __tablename__ = "llm_call_audit"

    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    logical_execution_stage: Mapped[str] = mapped_column(String, nullable=False)
    logical_execution_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    process_id: Mapped[str | None] = mapped_column(String, nullable=True)
    process_name: Mapped[str | None] = mapped_column(String, nullable=True)
    hostname: Mapped[str | None] = mapped_column(String, nullable=True)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # started/completed/failed/unknown（无 DB CHECK）
    prompt_chars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reasoning_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String, nullable=True)
    oversized_output: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class Budget(Base):
    """budget（30 §11/§17 + reserved 补列）。五账户正交；条件 UPDATE 并发安全。"""

    __tablename__ = "budget"
    __table_args__ = (
        UniqueConstraint(
            "account_dim", "scope_id", "stage",
            name="uq_budget_account_scope",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    account_dim: Mapped[str] = mapped_column(String, nullable=False)  # request/task/le/document/daily
    stage: Mapped[str | None] = mapped_column(String, nullable=True)  # 仅 le 账户用
    scope_id: Mapped[str] = mapped_column(String, nullable=False)
    limit: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    used: Mapped[Decimal] = mapped_column(Numeric, nullable=False, default=Decimal("0"))
    reserved: Mapped[Decimal] = mapped_column(Numeric, nullable=False, default=Decimal("0"))
    reserved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
