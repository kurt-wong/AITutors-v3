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


# ---- B-1（对抗审查）：provider resolution fail-closed（BUG-V3-035 fallback 身份边界） ----


async def test_resolve_single_provider_backward_compat() -> None:
    """single-provider mode（live_providers 空）→ 任意名回退唯一默认 live_provider（向后兼容）。"""
    primary = _FakeLiveProvider()
    g = LLMGateway("live", live_provider=primary)
    assert g._resolve_live_provider("deepseek") is primary
    assert g._resolve_live_provider(None) is primary


async def test_resolve_multi_provider_hit() -> None:
    """multi-provider mode → 已注册名返回对应 provider（fallback 换 provider 正常路由）。"""
    a = _FakeLiveProvider("a")
    b = _FakeLiveProvider("b")
    g = LLMGateway("live", live_providers={"a": a, "b": b})
    assert g._resolve_live_provider("b") is b


async def test_resolve_multi_provider_miss_fails_closed() -> None:
    """multi-provider mode → 未注册名返回 None（fail-closed），不回退 live_provider。

    修复前缺陷：未注册名静默回退到 live_provider（primary），造成 audit provider 与实际
    invocation provider 身份漂移（Runtime Truth 破坏）。"""
    primary = _FakeLiveProvider("primary")
    g = LLMGateway("live", live_provider=primary, live_providers={"a": _FakeLiveProvider("a")})
    assert g._resolve_live_provider("missing") is None


async def test_live_denied_unregistered_provider_not_silently_primary() -> None:
    """完整路径：multi-provider 未注册名 → GatewayDeniedError，primary 不被静默调用。

    修复前缺陷：fallback 配了未注册 provider 名，gateway 静默用 primary 再跑一次（identity
    漂移），audit 记 fallback 名、实际调 primary 对象。修复后 fail-closed 拒绝。"""
    calls: list = []

    class _Primary(_FakeLiveProvider):
        async def complete(self, prompt: str) -> str:
            calls.append(("primary", prompt))
            return "should-not-reach"

    primary = _Primary()
    g = LLMGateway(
        "live",
        allow_live=True,
        task_context="t",
        budget_ok=True,
        live_provider=primary,
        live_providers={"registered": _FakeLiveProvider("x")},
    )
    counter = _FakeCounter()
    with pytest.raises(GatewayDeniedError):
        await g.complete("x", task_id="t1", invocation_counter=counter, provider="missing")
    assert calls == []  # primary 从未被静默调用（identity 漂移已封死）
