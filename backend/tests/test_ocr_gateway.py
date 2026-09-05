"""Gate B6 — cloud OCR gating：五前置缺任一 → deny，不进 provider invocation。

无 DB。契约 = 零 external side effect（非「httpx 不在 sys.modules」）；RecordingProvider
记录是否被调用，证明 deny 时 provider 未进入。
"""

import pytest

from app.ai.ocr.gateway import OCRGateway
from app.ai.ocr.providers import MockOCRProvider
from app.ai.ocr.result import OCRLine, OCRResult
from app.core.errors import GatewayDeniedError, GatewayDisabledError


class RecordingProvider:
    """记 extract 调用（验证 deny 时未进入 provider）。"""

    name = "rec"

    def __init__(self) -> None:
        self.calls: list[int] = []

    async def extract(self, file_bytes: bytes) -> OCRResult:
        self.calls.append(len(file_bytes))
        return OCRResult(provider=self.name, model="m", pages=1)


def _mock_result() -> OCRResult:
    return OCRResult(provider="mock", model="m", pages=1, lines=(OCRLine("mock line", 1),))


async def test_b6_disabled_raises_and_no_provider_call():
    p = RecordingProvider()
    g = OCRGateway(
        "disabled",
        live_provider=p,
        mock_provider=MockOCRProvider(_mock_result()),
    )
    with pytest.raises(GatewayDisabledError):
        await g.extract(b"x")
    assert p.calls == []


async def test_b6_mock_returns_without_external():
    g = OCRGateway("mock", mock_provider=MockOCRProvider(_mock_result()))
    r = await g.extract(b"x")
    assert r.provider == "mock"


async def test_b6_live_denied_without_allow_live():
    p = RecordingProvider()
    g = OCRGateway("live", live_provider=p, task_context=object(), budget_ok=True)
    with pytest.raises(GatewayDeniedError) as exc:
        await g.extract(b"x")
    assert "--allow-live" in str(exc.value)
    assert p.calls == []


async def test_b6_live_denied_without_task_context():
    p = RecordingProvider()
    g = OCRGateway("live", allow_live=True, live_provider=p, budget_ok=True)
    with pytest.raises(GatewayDeniedError) as exc:
        await g.extract(b"x")
    assert "task context" in str(exc.value)
    assert p.calls == []


async def test_b6_live_denied_without_budget():
    p = RecordingProvider()
    g = OCRGateway("live", allow_live=True, live_provider=p, task_context=object())
    with pytest.raises(GatewayDeniedError) as exc:
        await g.extract(b"x")
    assert "budget" in str(exc.value)
    assert p.calls == []


async def test_b6_live_all_gates_calls_provider_once():
    p = RecordingProvider()
    g = OCRGateway(
        "live",
        allow_live=True,
        task_context=object(),
        budget_ok=True,
        live_provider=p,
    )
    r = await g.extract(b"hello")
    assert r.provider == "rec"
    assert p.calls == [5]
