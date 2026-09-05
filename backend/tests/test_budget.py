"""Gate C3/C4 — budget 并发条件 UPDATE + 五账户原子 rollback + 正交/LE 跨 attempt。

可重入性：每测试用唯一 scope（uuid4 hex），不依赖首跑残留、不污染共享预算行。
"""

import asyncio
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.ai.budget import AccountRef, BudgetService
from app.core.errors import BudgetExceededError
from app.db.session import async_session_maker

_uniq = lambda p: f"{p}-{uuid.uuid4().hex}"


def _ref(dim, sid, st=None):
    return AccountRef(dim, sid, st)


async def _commit_ensure(session, ref, limit) -> None:
    await BudgetService(session).ensure(ref, limit=limit)
    await session.commit()


async def _reserved(session, dim, sid, st=None) -> Decimal:
    res = await session.execute(
        text("SELECT COALESCE(reserved,0) FROM budget WHERE account_dim=:d AND scope_id=:s AND stage IS NOT DISTINCT FROM :t"),
        {"d": dim, "s": sid, "t": st},
    )
    row = res.scalar()
    return row if row is not None else Decimal("0")


async def test_c3a_single_account_concurrent_race() -> None:
    """同 scope 并发 reserve：仅一成功（条件 UPDATE 原子，无 read→compare→write）。"""
    ref = _ref("request", _uniq("R"))
    async with async_session_maker() as s:
        await _commit_ensure(s, ref, Decimal("10"))

    async def try_reserve():
        async with async_session_maker() as s:
            svc = BudgetService(s)
            try:
                await svc.reserve([ref], Decimal("6"))
                await s.commit()
                return "ok"
            except BudgetExceededError:
                await s.rollback()
                return "exceed"

    results = await asyncio.gather(try_reserve(), try_reserve())
    assert sorted(results) == ["exceed", "ok"]


async def test_c3b_five_account_atomic_rollback() -> None:
    """五账户任一失败 → 整体 rollback，无部分 reservation 残留。"""
    refs = [
        _ref("request", _uniq("R")), _ref("task", _uniq("T")),
        _ref("le", _uniq("H"), "ann"), _ref("document", _uniq("D")),
        _ref("daily", _uniq("DAY")),
    ]
    async with async_session_maker() as s:
        for ref in refs:
            lim = Decimal("100") if ref.account_dim != "daily" else Decimal("1")
            await _commit_ensure(s, ref, lim)

    async with async_session_maker() as s:
        svc = BudgetService(s)
        # daily limit 1 → amount 5 使 daily 失败，其余四个账户先成功后须整体回滚
        with pytest.raises(BudgetExceededError):
            await svc.reserve(refs, Decimal("5"))
        await s.rollback()

    async with async_session_maker() as s:
        for ref in refs:
            assert await _reserved(s, ref.account_dim, ref.scope_id, ref.stage) == Decimal("0")


async def test_c4_le_cross_attempt_shared() -> None:
    """同 (stage, hash) LE 跨 attempt 共享累计，不重领满；不同 stage 是独立行。"""
    hx = _uniq("HX")
    le = _ref("le", hx, "ann")
    async with async_session_maker() as s:
        await _commit_ensure(s, le, Decimal("50"))
    for _ in range(2):  # attempt1 + attempt2 累计到同一 LE 账户
        async with async_session_maker() as s:
            await BudgetService(s).reserve([le], Decimal("1"))
            await s.commit()
    async with async_session_maker() as s:
        assert await _reserved(s, "le", hx, "ann") == Decimal("2")
    # 不同 stage 同 hash = 独立行（唯一 (dim, scope, stage)）
    async with async_session_maker() as s:
        await _commit_ensure(s, _ref("le", hx, "compile"), Decimal("50"))
        res = await s.execute(text(
            "SELECT count(*) FROM budget WHERE account_dim='le' AND scope_id=:h"), {"h": hx})
        assert res.scalar() == 2
