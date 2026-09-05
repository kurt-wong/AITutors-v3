"""Gate C1 — Gateway disabled/mock/live（30 §6）。段 C 不实调 live provider。"""

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
    g = LLMGateway("live", allow_live=True, task_context="t", budget_ok=True, live_provider=_FakeLiveProvider())
    assert await g.complete("x") == "live-ok"
