"""运行域表（30 §10/§11/§17）。段 C 仅建 llm_call_audit + budget；tasks/task_claims 归段 H。

schema source of truth = 30；audit 列 SQL 类型为实现自由度（spec 未给类型）。
budget.reserved 为规格缺口补列（30 §11 需「预留量」，§17 列清单遗漏 → BUG-V3-006）。
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
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


class Task(Base):
    """tasks（30 §17 + §5 lease）。运行域任务状态行；状态迁移只能经 Task Service 显式接口。

    §5 lease 顶层列（worker_id/lease_token/started_at/heartbeat_at/lease_expires_at）是运行中
    租约状态；task_params 只存目标引用 id（documents.id 等），不内嵌内容正文。
    """

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    # created/queued/running/succeeded/failed/interrupted（无 DB CHECK，30 §17）
    status: Mapped[str] = mapped_column(String, nullable=False)
    task_params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    claim_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # §5 lease：运行中的租约状态（task 级，非 LE attempt）
    worker_id: Mapped[str | None] = mapped_column(String, nullable=True)
    lease_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TaskClaim(Base):
    """task_claims（30 §17，append-only）。task 级租约记录，非 LE attempt。

    Lock-1：worker_id/lease_token 仅经 lease_snapshot JSONB 保存 Claim Runtime Evidence，
    不进 task_claims 顶层列（与 tasks 顶层的运行中租约状态是不同来源）。
    """

    __tablename__ = "task_claims"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tasks.id"), nullable=False)
    claim_round: Mapped[int] = mapped_column(Integer, nullable=False)
    start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String, nullable=True)
    lease_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
