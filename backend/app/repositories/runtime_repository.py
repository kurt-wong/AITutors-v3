"""运行域 Repository：audit append-only + budget 条件 UPDATE（30 §10/§11，段 C）。"""

import uuid
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.runtime import Budget, LlmCallAudit
from app.repositories.base import AppendOnlyViolation, BaseRepository


class LlmCallAuditRepository(BaseRepository):
    async def create_audit(
        self,
        *,
        idempotency_key: str,
        logical_execution_stage: str,
        logical_execution_hash: str,
        stage: str,
        provider: str,
        model: str,
        attempt_id: uuid.UUID | None = None,
        task_id: uuid.UUID | None = None,
        document_id: uuid.UUID | None = None,
        status: str = "started",
    ) -> LlmCallAudit:
        row = LlmCallAudit(
            idempotency_key=idempotency_key,
            logical_execution_stage=logical_execution_stage,
            logical_execution_hash=logical_execution_hash,
            attempt_id=attempt_id,
            task_id=task_id,
            document_id=document_id,
            stage=stage,
            provider=provider,
            model=model,
            status=status,
        )
        await self.add(row)
        return row

    async def update_audit(self, *_args: object, **_kwargs: object) -> None:
        """llm_call_audit append-only 不可变：UPDATE → 抛错（Gate C2）。"""
        raise AppendOnlyViolation("llm_call_audit is append-only immutable")


class BudgetRepository(BaseRepository):
    async def ensure_account(
        self, *, account_dim: str, scope_id: str, limit: Decimal, stage: str | None = None
    ) -> Budget:
        """幂等建账户行（唯一约束 on_conflict 不重复），limit 由调用方提供（单位语义未冻结，BUG 记录）。"""
        stmt = (
            pg_insert(Budget)
            .values(
                account_dim=account_dim,
                scope_id=scope_id,
                stage=stage,
                limit=limit,
                used=Decimal("0"),
                reserved=Decimal("0"),
            )
            .on_conflict_do_nothing(constraint="uq_budget_account_scope")
        )
        await self._session.execute(stmt)
        res = await self._session.execute(
            text(
                "SELECT * FROM budget WHERE account_dim=:ad AND scope_id=:sc "
                "AND stage IS NOT DISTINCT FROM :st"
            ),
            {"ad": account_dim, "sc": scope_id, "st": stage},
        )
        row = res.mappings().one()
        return Budget(**{k: row[k] for k in Budget.__table__.columns.keys()})

    async def reserve(self, *, account_dim: str, scope_id: str, amount: Decimal, stage: str | None = None) -> None:
        """条件 UPDATE：used+reserved+amount<=limit 原子；0 行 = 超限。"""
        res = await self._session.execute(
            text(
                "UPDATE budget SET reserved=reserved+:x, reserved_at=now(), updated_at=now() "
                "WHERE account_dim=:ad AND scope_id=:sc AND stage IS NOT DISTINCT FROM :st "
                'AND used+reserved+:x <= "limit" RETURNING id'
            ),
            {"x": amount, "ad": account_dim, "sc": scope_id, "st": stage},
        )
        if not res.first():
            raise LookupError(f"budget exceeded: {account_dim}/{scope_id}/{stage}")

    async def settle(self, *, account_dim: str, scope_id: str, reserved: Decimal, actual: Decimal, stage: str | None = None) -> None:
        res = await self._session.execute(
            text(
                "UPDATE budget SET reserved=reserved-:r, used=used+:a, updated_at=now() "
                "WHERE account_dim=:ad AND scope_id=:sc AND stage IS NOT DISTINCT FROM :st "
                "AND reserved>=:r RETURNING id"
            ),
            {"r": reserved, "a": actual, "ad": account_dim, "sc": scope_id, "st": stage},
        )
        if not res.first():
            raise LookupError(f"settle mismatch: {account_dim}/{scope_id}/{stage}")

    async def reclaim_expired(self, *, older_than_seconds: int) -> int:
        """reserve 超时确定性回收（30 §11；不调 LLM；不扩展 reservation 系统）。"""
        res = await self._session.execute(
            text(
                "UPDATE budget SET reserved=0 "
                "WHERE reserved_at < now() - make_interval(secs => :s) RETURNING id"
            ),
            {"s": older_than_seconds},
        )
        return len(res.all())
