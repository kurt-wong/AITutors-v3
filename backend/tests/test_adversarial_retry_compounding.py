"""对抗性审查 — 重试分层复合（H-ADV-RETRY）。

红线（30 §7 五行表 + BUG-V3-033/034/035）：
  HTTP transport retry ≠ LLM request retry ≠ Provider fallback —— 三层各自独立 bounded，
  不得复合成无界或无审计的调用风暴。

现有测试把三层**各自隔离**测过（test_http_provider / test_executor / test_task_executor），
但乘法路径从未被走过：所有 executor 重试测试用的是无 HTTP 层的 `_FlakyProvider`，
所有 HTTP 测试把 LLM retry 设为 0。本文件补上跨层复合的反证。

注：fallback × executor retry 的乘法路径（primary 3 次 attempt + fallback 1 次 =
4 Invocation / 2 Audit）**已实测通过**，但该用例需走完整 TaskExecutor 管线并写入
document 子树；在当前无跨测试隔离的套件里（见报告 F-1：dbflow 测试断言全局行数），
自清理极脆弱，故未纳入本文件。F-1 修复后应补回。
"""

import uuid
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import text

from app.ai.budget import AccountRef, BudgetService
from app.ai.executor import LLMExecutor
from app.ai.gateway import LLMGateway
from app.ai.providers.http import HTTPLLMProvider
from app.core.config import settings
from app.core.errors import LLMProviderError
from app.db.session import async_session_maker
from app.repositories.runtime_repository import TaskRepository


class _Resp:
    def __init__(self, status: int = 200, content: str = "ok-text") -> None:
        self.status_code = status
        self._content = content
        self._request = httpx.Request("POST", "http://localhost")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = httpx.Response(self.status_code, request=self._request)
            raise httpx.HTTPStatusError(
                f"server error {self.status_code}", request=self._request, response=response
            )

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def _patch_http(monkeypatch, script: list) -> list:
    """monkeypatch httpx.AsyncClient；返回 post 调用记录（= 真实 HTTP attempt 数）。"""
    calls: list = []

    class _FakeClient:
        def __init__(self, *a, **k) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a) -> bool:
            return False

        async def post(self, url, **kwargs):
            calls.append(url)
            step = script.pop(0)
            if step[0] == "raise":
                raise step[1]
            return step[1]

    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    return calls


def _provider(http_retry_count: int) -> HTTPLLMProvider:
    return HTTPLLMProvider(
        name="deepseek",
        api_key="k",
        base_url="http://localhost",
        model="deepseek-chat",
        timeout=1.0,
        http_retry_count=http_retry_count,
    )


def _live_gw(provider) -> LLMGateway:
    return LLMGateway(
        "live", allow_live=True, task_context="t", budget_ok=True, live_provider=provider
    )


async def _mk_task(session) -> uuid.UUID:
    t = await TaskRepository(session).create(
        task_type="document_ingest", task_params={}, status="queued"
    )
    await session.commit()
    return t.id


def _params(task_id, document_id):
    return dict(
        le_stage="ann",
        le_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        attempt_id=uuid.uuid4(),
        task_id=task_id,
        document_id=document_id,
        provider="deepseek",
        model="deepseek-chat",
    )


async def _invocations(session, task_id) -> int:
    return (await session.execute(
        text("SELECT llm_invocations FROM tasks WHERE id=:i"), {"i": task_id}
    )).scalar_one()


async def _audit_statuses(session, task_id) -> list[str]:
    res = await session.execute(
        text("SELECT status FROM llm_call_audit WHERE task_id=:i ORDER BY start"), {"i": task_id}
    )
    return list(res.scalars().all())


async def _budget(session, task_id):
    row = (await session.execute(
        text("SELECT used, reserved FROM budget WHERE account_dim='task' AND scope_id=:i"),
        {"i": str(task_id)},
    )).mappings().first()
    return None if row is None else {"used": row["used"], "reserved": row["reserved"]}


async def _seed(session, task_id, limit=Decimal("100")):
    await BudgetService(session).ensure(AccountRef("task", str(task_id)), limit=limit)
    await session.commit()


# ---- GAP-1：HTTP retry × LLM retry 乘法复合 ----


async def test_http_x_llm_retry_multiplicative_http_requests_bounded_accounting(monkeypatch) -> None:
    """GAP-1 反证：两层重试**同时开启**时，HTTP 请求按乘法放大，但业务记账不放大。

    构造：llm retry_count=2（3 次 LLM attempt）× http_retry_count=2（每次 3 个 HTTP attempt）。
    前两次 LLM attempt 把 3 个 HTTP attempt 全部耗尽（transport 失败）→ LLMNetworkError；
    第三次 LLM attempt 前两次 HTTP 失败、第三次成功。

    期望：
      HTTP post 调用      = 3×3 = 9   ← 乘法放大确实发生
      Provider Invocation = 3          ← 计数点在 gateway seam（先于 transport retry），每 LLM attempt 计 1
      Audit               = 恰 1 条 completed ← 重试沿用同 logical request，不得翻倍
      Budget              = used 1 / reserved 0
    若记账也被乘法放大（Audit=3 或 used=3），则违反 30 §7「每层独立 bounded」与
    「重试沿用同 audit」——这就是红线本身。
    """
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
        await _seed(s, task_id)
    doc_id = uuid.uuid4()

    boom = httpx.ConnectError("transport boom")
    script = (
        [("raise", boom)] * 3          # LLM attempt #1：3 个 HTTP attempt 全失败
        + [("raise", boom)] * 3        # LLM attempt #2：同上
        + [("raise", boom), ("raise", boom), ("response", _Resp(200, "recovered"))]
    )
    calls = _patch_http(monkeypatch, script)

    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gw(_provider(http_retry_count=2)), retry_count=2)
        out = await ex.complete("q", **_params(task_id, doc_id))
        assert out == "recovered"

    assert len(calls) == 9, (
        f"HTTP 层应按乘法放大到 9 次 post（3 LLM attempt × 3 HTTP attempt），实为 {len(calls)}"
    )
    async with async_session_maker() as s:
        inv = await _invocations(s, task_id)
        audits = await _audit_statuses(s, task_id)
        b = await _budget(s, task_id)
    assert inv == 3, f"Provider Invocation 应为 3（每 LLM attempt 计 1），实为 {inv}"
    assert audits == ["completed"], (
        f"Audit 必须恰 1 条且 completed（重试沿用同 logical request），实为 {audits}"
    )
    assert b == {"used": Decimal("1"), "reserved": Decimal("0")}, (
        f"Budget 不得被 HTTP/LLM 重试放大，实为 {b}"
    )


# ---- GAP-2：真实 HTTP 400 → executor 端到端不重试 ----


async def test_http_400_end_to_end_not_retried_by_executor(monkeypatch) -> None:
    """GAP-2 反证：http.py 把 400 译成 LLMProviderError(retryable=False)，executor 必须不重试。

    两层各自测过（test_http_provider 400→retryable=False；test_executor 不重试 retryable=False），
    但**端到端**从未穿过真实 HTTPLLMProvider。若分类或传播任一环节松动，乘法路径会放大它。
    """
    async with async_session_maker() as s:
        task_id = await _mk_task(s)
        await _seed(s, task_id)
    doc_id = uuid.uuid4()

    calls = _patch_http(monkeypatch, [("response", _Resp(400))])

    async with async_session_maker() as s:
        ex = LLMExecutor(s, _live_gw(_provider(http_retry_count=2)), retry_count=2)
        with pytest.raises(LLMProviderError) as ei:
            await ex.complete("q", **_params(task_id, doc_id))
    assert ei.value.retryable is False, "400 必须译为 retryable=False"

    assert len(calls) == 1, (
        f"400 是 status error 非 transport error → 不得 transport retry；"
        f"且 retryable=False → 不得 LLM retry。HTTP post 应为 1，实为 {len(calls)}"
    )
    async with async_session_maker() as s:
        inv = await _invocations(s, task_id)
        audits = await _audit_statuses(s, task_id)
    assert inv == 1, f"Invocation 应为 1（未重试），实为 {inv}"
    assert audits == ["failed"], f"Audit 应为恰 1 条 failed，实为 {audits}"


# ---- GAP-6：fallback 默认关闭的哨兵（不 monkeypatch） ----


def test_provider_fallback_default_is_false_sentinel() -> None:
    """GAP-6 哨兵：30 §182「Provider Fallback: explicit，默认关闭」。

    现有测试全部 monkeypatch 这个 flag，一旦 config 默认值被改成 True，全套 fallback
    测试仍会绿（它们显式设了 False/True），而生产语义已静默反转。此测试不经 monkeypatch，
    直接锁默认值。
    """
    assert settings.provider_fallback_enabled is False, (
        "30 §7 / BUG-V3-035：Provider Fallback 默认必须关闭。"
        f"当前默认 = {settings.provider_fallback_enabled!r}，改动默认值须先过审计/预算裁决。"
    )
