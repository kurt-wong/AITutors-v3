"""H Phase 4 — LLMExecutor 唯一执行入口 + ProviderInvocationCounter 熔断计数（真 PostgreSQL）。

锁定（裁决 §6/§7/§8 + G4/G5）：
  四个数量级分别锁：Attempt=1 · Logical Request=1 · Audit=1 · Provider Invocations=N，且
  MAX_LLM_CALLS 按真实 Invocation 累计（=N）。
  G4 mock/disabled 同入口、零 audit/budget/计数副作用；G5 每 Attempt 恰一 audit（M1 1:1）。
  Lock-6 reserve+audit STARTED 同事务（BudgetExceeded 时 rollback 零残留、零 audit 行）。
  熔断：consume 越界 → CircuitOpen，provider 不发出；计数为任务生命周期累计。
可重入性：每测试唯一 task/document scope + commit 后各 session 读取；daily 账户用自然日
scope（DEFAULT_LIMITS 2000 上限远超本文件累计，可重入两遍）。
"""

import asyncio
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.ai.budget import AccountRef, BudgetService
from app.ai.executor import LLMExecutor, ProviderInvocationCounter
from app.ai.gateway import LLMGateway
from app.ai.providers.mock import MockLLMProvider
from app.core.errors import (
    BudgetExceededError,
    BudgetSettlementError,
    CircuitOpen,
    GatewayDeniedError,
    GatewayDisabledError,
    LLMNetworkError,
    LLMProviderError,
)
from app.db.session import async_session_maker
from app.repositories.runtime_repository import TaskRepository


class _FlakyProvider:
    """前 fail_first 次抛 transient LLMNetworkError，其后返回固定文本；记录真实调用次数。"""

    name = "flaky"

    def __init__(self, fail_first: int, out: str = "ok-text") -> None:
        self._fail = fail_first
        self._out = out
        self.calls = 0

    async def complete(self, prompt: str) -> str:
        self.calls += 1
        if self.calls <= self._fail:
            raise LLMNetworkError(f"transient failure #{self.calls}")
        return self._out


def _live_gateway(provider) -> LLMGateway:
    return LLMGateway(
        "live", allow_live=True, task_context="t", budget_ok=True, live_provider=provider
    )


def _exec_params(task_id, document_id, *, attempt_id=None):
    # le_hash 每次唯一（64 hex），使 le 预算账户 scope 每请求独立，测试互不污染
    return dict(
        le_stage="ann", le_hash=uuid.uuid4().hex + uuid.uuid4().hex, attempt_id=attempt_id,
        task_id=task_id, document_id=document_id,
        provider="deepseek", model="deepseek-chat",
    )


async def _mk_task(session) -> uuid.UUID:
    t = await TaskRepository(session).create(
        task_type="document_ingest", task_params={}, status="queued"
    )
    await session.commit()
    return t.id


async def _invocations(session, task_id) -> int:
    return (await session.execute(
        text("SELECT llm_invocations FROM tasks WHERE id=:i"), {"i": task_id}
    )).scalar_one()


async def _audit_statuses(session, task_id) -> list[str]:
    res = await session.execute(
        text("SELECT status FROM llm_call_audit WHERE task_id=:i ORDER BY start"), {"i": task_id}
    )
    return list(res.scalars().all())


async def _budget_row(session, dim, scope):
    row = (await session.execute(
        text("SELECT used, reserved FROM budget WHERE account_dim=:d AND scope_id=:s"),
        {"d": dim, "s": scope},
    )).mappings().first()
    if row is None:
        return None
    return {"used": row["used"], "reserved": row["reserved"]}


async def _seed_limit(session, dim, scope, limit: Decimal) -> None:
    ref = AccountRef(dim, scope)
    await BudgetService(session).ensure(ref, limit=limit)
    await session.commit()


# ---- 四数量级：Attempt=1 · Request=1 · Audit=1 · Invocations=N ----


async def test_live_success_one_invocation_one_audit_settled() -> None:
    """live 成功：1 real invocation、恰 1 条 completed audit、settle 后 reserved=0 used=1。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    provider = _FlakyProvider(fail_first=0)
    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(provider), retry_count=2)
        out = await ex.complete("q", **_exec_params(task_id, doc_id, attempt_id=uuid.uuid4()))
        assert out == "ok-text"
    assert provider.calls == 1  # Invocation=1
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 1
        assert await _audit_statuses(s, task_id) == ["completed"]  # Audit=1，恰一
        row = await _budget_row(s, "task", str(task_id))
        assert row == {"used": Decimal("1"), "reserved": Decimal("0")}  # settle 生效


async def test_live_transient_then_success_retries_same_request() -> None:
    """瞬时失败后成功：Invocation=2（重试），Audit 恰 1 条 completed（重试沿用同 logical request）。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    provider = _FlakyProvider(fail_first=1)  # 第 1 次失败，第 2 次成功
    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(provider), retry_count=2)
        out = await ex.complete("q", **_exec_params(task_id, doc_id, attempt_id=uuid.uuid4()))
        assert out == "ok-text"
    assert provider.calls == 2  # Invocation=2
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 2  # MAX_LLM_CALLS 按真实 Invocation +2
        assert await _audit_statuses(s, task_id) == ["completed"]  # 仍恰 1 audit，未因重试重复建账


async def test_live_persistent_failure_exhausts_retries() -> None:
    """持久失败：retry_count=2 → Invocation=3；Audit 恰 1 条 failed；reserve 释放（used=0）；re-raise。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    provider = _FlakyProvider(fail_first=999)
    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(provider), retry_count=2)
        with pytest.raises(LLMNetworkError):
            await ex.complete("q", **_exec_params(task_id, doc_id, attempt_id=uuid.uuid4()))
    assert provider.calls == 3  # Invocation=3 = retry_count+1
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 3  # 熔断按真实调用累计 3
        assert await _audit_statuses(s, task_id) == ["failed"]  # Audit=1 failed
        row = await _budget_row(s, "task", str(task_id))
        assert row == {"used": Decimal("0"), "reserved": Decimal("0")}  # 失败释放保留


# ---- 熔断：越界 CircuitOpen，provider 不发出 ----


async def test_live_circuit_open_blocks_provider_call() -> None:
    """max_invocations=0 → consume 越界 CircuitOpen；provider 从未被调；audit failed + reserve 释放。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    provider = _FlakyProvider(fail_first=999)
    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(provider), retry_count=0, max_invocations=0)
        with pytest.raises(CircuitOpen):
            await ex.complete("q", **_exec_params(task_id, doc_id))
    assert provider.calls == 0  # 熔断在 provider 发出前拦截
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 0
        assert await _audit_statuses(s, task_id) == ["failed"]
        row = await _budget_row(s, "task", str(task_id))
        assert row == {"used": Decimal("0"), "reserved": Decimal("0")}


async def test_counter_concurrent_exactly_one_allow() -> None:
    """Clarification-2：两 session 并发 consume 同 task（max=1）→ 恰一放行（原子条件 UPDATE）。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)

    async def consume() -> str:
        async with async_session_maker() as sess:
            c = ProviderInvocationCounter(sess, max_invocations=1)
            try:
                await c.consume(task_id)
                return "allow"
            except CircuitOpen:
                return "open"

    results = await asyncio.gather(consume(), consume())
    assert sorted(results) == ["allow", "open"]
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 1


async def test_live_missing_document_id_guard() -> None:
    """live 缺 document_id → ValueError（执行前 guard，不触 DB/不建 audit）。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(_FlakyProvider(0)))
        with pytest.raises(ValueError):
            await ex.complete("q", **_exec_params(task_id, None))
    async with async_session_maker() as s:
        assert await _audit_statuses(s, task_id) == []
        assert await _invocations(s, task_id) == 0


async def test_live_non_retryable_denied_finalizes_failed() -> None:
    """非重试性错误（GatewayDeniedError，live 前置缺）→ 不重试；audit failed；reserve 释放；re-raise。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    provider = _FlakyProvider(fail_first=0)
    gw = LLMGateway("live", allow_live=False, task_context="t", budget_ok=True,
                    live_provider=provider)
    async with async_session_maker() as s:
        ex = LLMExecutor(s, gw, retry_count=2)
        with pytest.raises(GatewayDeniedError):
            await ex.complete("q", **_exec_params(task_id, doc_id))
    assert provider.calls == 0  # 非重试性错误不触发任何 provider invocation
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 0
        assert await _audit_statuses(s, task_id) == ["failed"]
        row = await _budget_row(s, "task", str(task_id))
        assert row == {"used": Decimal("0"), "reserved": Decimal("0")}


# ---- Lock-6：reserve+audit 同事务，BudgetExceeded 时 rollback 零残留 ----


async def test_live_budget_exceeded_rolls_back_no_audit() -> None:
    """reserve 任一账户超限 → BudgetExceededError；无 audit 行（同事务 rollback，Lock-6）；provider 不调。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    # 预置 task 账户 limit=0（ensure on_conflict 保留既有 limit），使 reserve 第二阶段失败
    async with async_session_maker() as s:
        await _seed_limit(s, "task", str(task_id), Decimal("0"))
    doc_id = uuid.uuid4()
    provider = _FlakyProvider(fail_first=999)
    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(provider))
        with pytest.raises(BudgetExceededError):
            await ex.complete("q", **_exec_params(task_id, doc_id))
    assert provider.calls == 0
    async with async_session_maker() as s:
        assert await _audit_statuses(s, task_id) == []  # 零 audit 行
        assert await _invocations(s, task_id) == 0
        # 同事务 ensure/reserve 已整体回滚：本任务专属 le/document 账户未残留
        assert await _budget_row(s, "document", str(doc_id)) is None
        task_row = await _budget_row(s, "task", str(task_id))
        assert task_row is not None  # 预置 limit=0 行仍在
        assert task_row == {"used": Decimal("0"), "reserved": Decimal("0")}  # reserve 已回滚


# ---- G4：mock/disabled 同入口、零 audit/budget/计数副作用 ----


async def test_mock_no_runtime_side_effect() -> None:
    """mock：同 complete() 入口返回注入文本；零 audit / 零 budget / 计数不变。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    gw = LLMGateway("mock", mock_provider=MockLLMProvider({"q": "mock-a"}))
    async with async_session_maker() as s:
        ex = LLMExecutor(s, gw)
        out = await ex.complete("q", **_exec_params(task_id, doc_id))
        assert out == "mock-a"
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 0
        assert await _audit_statuses(s, task_id) == []
        assert await _budget_row(s, "task", str(task_id)) is None  # 未建预算行


async def test_disabled_raises_no_runtime_side_effect() -> None:
    """disabled：同入口抛 GatewayDisabledError；零 audit / 零 budget / 计数不变。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    async with async_session_maker() as s:
        ex = LLMExecutor(s, LLMGateway("disabled"))
        with pytest.raises(GatewayDisabledError):
            await ex.complete("q", **_exec_params(task_id, doc_id))
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 0
        assert await _audit_statuses(s, task_id) == []
        assert await _budget_row(s, "task", str(task_id)) is None


class _CancelProvider:
    """complete 恒抛 asyncio.CancelledError（进程取消信号，非 provider 失败）。"""

    name = "cancel"

    async def complete(self, prompt: str) -> str:
        raise asyncio.CancelledError()


class _NonRetryableProvider:
    """complete 恒抛 LLMProviderError(retryable=False)（4xx 非 transient，provider 明确拒绝）。"""

    name = "non-retryable"

    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, prompt: str) -> str:
        self.calls += 1
        raise LLMProviderError("provider rejected HTTP 400", retryable=False)


async def test_non_retryable_provider_error_not_retried() -> None:
    """BUG-V3-034：LLMProviderError(retryable=False) 不重试——Invocation=1，直接 re-raise。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    provider = _NonRetryableProvider()
    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(provider), retry_count=2)
        with pytest.raises(LLMProviderError):
            await ex.complete("q", **_exec_params(task_id, doc_id, attempt_id=uuid.uuid4()))
    assert provider.calls == 1  # 不重试
    async with async_session_maker() as s:
        assert await _invocations(s, task_id) == 1
        assert await _audit_statuses(s, task_id) == ["failed"]


async def test_live_cancellation_propagates_audit_stays_started() -> None:
    """Batch 3-1：CancelledError 是取消信号非 provider 失败——必须传播（不被吞、不被
    finalize 为 failed）；audit 保持 STARTED，由 recovery 判 unknown（30 §10）。"""
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(_CancelProvider()), retry_count=2)
        with pytest.raises(asyncio.CancelledError):
            await ex.complete("q", **_exec_params(task_id, doc_id, attempt_id=uuid.uuid4()))
    async with async_session_maker() as s:
        # CancelledError 不被 finalize 为 failed/unknown —— audit 保持 STARTED（等 recovery）
        assert await _audit_statuses(s, task_id) == ["started"]
        # reserve 未被 settle（Phase C 未执行），由 recovery 对账回收
        row = await _budget_row(s, "task", str(task_id))
        assert row == {"used": Decimal("0"), "reserved": Decimal("1")}


async def test_settle_failure_does_not_rollback_audit(monkeypatch) -> None:
    """Batch 3-3：settle 失败（BudgetSettlementError）不回滚 audit 终态（30 §10/§11 + F-6）。

    audit terminalization（C1）独立于 settle（C2）先行 commit——provider 已成功、audit 已
    completed，settle 失败只显式暴露（F-6），不把 audit 回滚成假的 STARTED。
    """
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
    doc_id = uuid.uuid4()
    provider = _FlakyProvider(fail_first=0)  # 成功返回文本

    async def _boom_settle(self, refs, *, reserved, actual):
        raise BudgetSettlementError("settle boom")

    monkeypatch.setattr(BudgetService, "settle", _boom_settle)

    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gateway(provider), retry_count=2)
        with pytest.raises(BudgetSettlementError):
            await ex.complete("q", **_exec_params(task_id, doc_id, attempt_id=uuid.uuid4()))
    async with async_session_maker() as s:
        # audit 保持 completed（provider 成功的 Runtime Truth 不被 settle 失败回滚）
        assert await _audit_statuses(s, task_id) == ["completed"]
        # reserve 未 settle 释放（残留由 reclaim 对账回收）
        row = await _budget_row(s, "task", str(task_id))
        assert row == {"used": Decimal("0"), "reserved": Decimal("1")}
