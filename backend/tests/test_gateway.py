"""Gate C1 — Gateway disabled/mock/live（30 §6）。段 C 不实调 live provider。

Phase 4（Lock-4/Note-1）：live 每次真实 invocation 前须经 invocation_counter.consume；
B-1（独立对抗审查）缺 counter/task_id → fail-closed。live allowed 用例带 fake counter 锁 seam。
"""

import pytest

from app.ai.gateway import LLMGateway
from app.ai.providers.mock import MockLLMProvider
from app.core.errors import GatewayDeniedError, GatewayDisabledError


class _FakeLiveProvider:
    name = "fake"

    def __init__(self, out: str = "live-ok") -> None:
        self._out = out

    async def complete(self, prompt: str) -> str:
        return self._out


class _FakeCounter:
    """记录 consume 调用的 task_id；live allowed 用例验证 seam 在 provider 前触发。"""

    def __init__(self) -> None:
        self.consumed: list = []

    async def consume(self, task_id) -> None:
        self.consumed.append(task_id)


async def test_disabled_raises_no_side_effect() -> None:
    g = LLMGateway("disabled", live_provider=_FakeLiveProvider())  # live provider 存在但不 init/调用
    with pytest.raises(GatewayDisabledError):
        await g.complete("hello")
    assert g._live_provider is not None  # 存在即可，未调用 = 无副作用


async def test_mock_returns_injected_fixture() -> None:
    g = LLMGateway("mock", mock_provider=MockLLMProvider({"q": "a"}))
    assert await g.complete("q") == "a"


async def test_mock_default_response() -> None:
    g = LLMGateway("mock")
    assert await g.complete("anything") == "mock-response"


async def test_live_denied_when_preconditions_missing() -> None:
    g = LLMGateway("live", live_provider=_FakeLiveProvider())
    with pytest.raises(GatewayDeniedError):
        await g.complete("x")


async def test_live_denied_reason_reports_missing_allow_live() -> None:
    g = LLMGateway("live", task_context="t", budget_ok=True, live_provider=_FakeLiveProvider())
    with pytest.raises(GatewayDeniedError) as ei:
        await g.complete("x")
    assert "--allow-live" in str(ei.value)


async def test_live_allowed_when_all_four_present() -> None:
    """live 四前置齐 + counter/task_id → provider 放行；consume seam 在 provider 前触发一次。"""
    g = LLMGateway("live", allow_live=True, task_context="t", budget_ok=True, live_provider=_FakeLiveProvider())
    counter = _FakeCounter()
    assert await g.complete("x", task_id="t1", invocation_counter=counter) == "live-ok"
    assert counter.consumed == ["t1"]  # Lock-4 seam：provider 前 consume 恰一次


async def test_live_denied_when_missing_counter() -> None:
    """live 缺 invocation_counter → fail-closed（B-1：Lock-4 熔断不可被绕过），provider 不调。"""
    calls: list = []

    class _Probe(_FakeLiveProvider):
        async def complete(self, prompt: str) -> str:
            calls.append(prompt)
            return "should-not-reach"

    g = LLMGateway("live", allow_live=True, task_context="t", budget_ok=True, live_provider=_Probe())
    with pytest.raises(GatewayDeniedError) as ei:
        await g.complete("x", task_id="t1")  # 有 task_id 但无 counter
    assert "counter" in str(ei.value)
    assert calls == []  # provider 从未被调


async def test_live_denied_when_missing_task_id() -> None:
    """live 缺 task_id → fail-closed（计数无处归属即拒），provider 不调。"""
    calls: list = []

    class _Probe(_FakeLiveProvider):
        async def complete(self, prompt: str) -> str:
            calls.append(prompt)
            return "should-not-reach"

    g = LLMGateway("live", allow_live=True, task_context="t", budget_ok=True, live_provider=_Probe())
    with pytest.raises(GatewayDeniedError) as ei:
        await g.complete("x", invocation_counter=_FakeCounter())
    assert "task_id" in str(ei.value)
    assert calls == []
