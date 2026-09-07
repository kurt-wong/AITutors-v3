"""Budget 服务（30 §11/§17）：五账户正交，一次 reserve/settle 共享同一事务边界。

禁止单账户提前 commit；任一账户失败 → 抛错，由调用方 rollback，不留部分 reservation。
Service 自身不 commit（事务边界由一次完整操作/外层统一管理）。
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BudgetExceededError, BudgetSettlementError
from app.repositories.runtime_repository import BudgetRepository

DEFAULT_LIMITS: dict[str, Decimal] = {
    "request": Decimal("1"),
    "task": Decimal("100"),
    "le": Decimal("50"),
    "document": Decimal("500"),
    "daily": Decimal("2000"),
}


@dataclass(frozen=True)
class AccountRef:
    account_dim: str
    scope_id: str
    stage: str | None = None


class BudgetService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = BudgetRepository(session)

    async def ensure(
        self, ref: AccountRef, *, limit: Decimal | None = None
    ) -> None:
        lim = limit if limit is not None else DEFAULT_LIMITS[ref.account_dim]
        await self._repo.ensure_account(
            account_dim=ref.account_dim, scope_id=ref.scope_id, stage=ref.stage, limit=lim
        )

    async def reserve(self, refs: list[AccountRef], amount: Decimal) -> None:
        """五账户同一事务 reserve；任一失败抛 BudgetExceededError（不自 commit，调用方 rollback）。"""
        try:
            for ref in refs:
                await self._repo.reserve(
                    account_dim=ref.account_dim, scope_id=ref.scope_id,
                    stage=ref.stage, amount=amount,
                )
        except LookupError as exc:
            raise BudgetExceededError(str(exc)) from exc

    async def settle(self, refs: list[AccountRef], *, reserved: Decimal, actual: Decimal) -> None:
        """reserve 释放：reserved→used 恰一次。记账不一致（reserved<释放量/双 settle）→
        BudgetSettlementError（F-6：与超限语义分离，不得伪装 BudgetExceeded）。"""
        try:
            for ref in refs:
                await self._repo.settle(
                    account_dim=ref.account_dim, scope_id=ref.scope_id,
                    stage=ref.stage, reserved=reserved, actual=actual,
                )
        except LookupError as exc:
            raise BudgetSettlementError(str(exc)) from exc


def five_account_refs(*, request_id: str, task_id: str, le_hash: str, le_stage: str, document_id: str, day: str) -> list[AccountRef]:
    """一次 request 同时作用五账户（正交，禁父子树）。le 用 (stage, hash) scope。"""
    return [
        AccountRef("request", request_id),
        AccountRef("task", task_id),
        AccountRef("le", le_hash, le_stage),
        AccountRef("document", document_id),
        AccountRef("daily", day),
    ]
