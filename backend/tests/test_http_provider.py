"""Phase 9-2 — HTTPLLMProvider HTTP transport retry（BUG-V3-033/034 冻结语义）。

锁定（用户裁决 9-2 指令）：
  HTTP transport retry 属同一次 Provider Invocation 内的传输层重试——bounded
  （http_retry_count），仅对 httpx.TransportError 重试，不新增业务 invocation / audit /
  budget（计数点在 gateway provider seam，先于本层）。HTTP status retry 语义不在本层扩展
  （408/429/5xx 仍由 LLMProviderError(retryable=…) 表达，交 LLMExecutor 层）。CancelledError
  为 BaseException，不被 except httpx.TransportError 捕获，自然传播。

本文件为 HTTPLLMProvider 单元级对抗测试：用脚本化 AsyncClient 逐次注入 transport/response/
cancellation 行为，观测 attempts 次数（post 调用数）与最终异常翻译。集成级「不增 invocation/
audit/budget」反证见 test_executor.py::test_transport_retry_does_not_increase_accounting。
"""

import asyncio

import httpx
import pytest

from app.ai.providers.http import HTTPLLMProvider
from app.core.errors import LLMNetworkError, LLMProviderError


class _FakeResponse:
    """最小 response：仅支持 raise_for_status() 与 json()。"""

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


def _patch_client(monkeypatch, script: list):
    """monkeypatch httpx.AsyncClient 为脚本化 client，返回 post 调用记录（attempts 数）。

    script 每项为 ("raise", exc) 或 ("response", _FakeResponse)。每次 retry 新建 AsyncClient
    复用同一 script，pop 推进；calls 记录每次 post（= 一次 HTTP transport attempt）。
    """
    calls: list = []

    class _FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> bool:
            return False

        async def post(self, url, **kwargs):
            calls.append(url)
            step = script.pop(0)
            if step[0] == "raise":
                raise step[1]
            return step[1]

    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    return calls


def _provider(http_retry_count: int | None = None) -> HTTPLLMProvider:
    return HTTPLLMProvider(
        name="deepseek",
        api_key="k",
        base_url="http://localhost",
        model="deepseek-chat",
        timeout=1.0,
        http_retry_count=http_retry_count,
    )


# ---- BUG-V3-033：transport-only retry，bounded by http_retry_count ----


async def test_http_retry_count_zero_transport_failure_single_attempt(monkeypatch) -> None:
    """http_retry_count=0 + transport 失败 → 恰 1 次 HTTP attempt，最终 LLMNetworkError。"""
    calls = _patch_client(monkeypatch, [("raise", httpx.ConnectError("boom"))])
    with pytest.raises(LLMNetworkError):
        await _provider(http_retry_count=0).complete("q")
    assert len(calls) == 1  # 1 + http_retry_count(0)


async def test_transport_retry_two_failures_then_success(monkeypatch) -> None:
    """http_retry_count=2 + 前两次 transport 失败、第三次成功 → 3 attempts，返回文本。"""
    calls = _patch_client(
        monkeypatch,
        [
            ("raise", httpx.ConnectError("boom #1")),
            ("raise", httpx.ConnectTimeout("boom #2")),
            ("response", _FakeResponse(200, "recovered")),
        ],
    )
    out = await _provider(http_retry_count=2).complete("q")
    assert out == "recovered"
    assert len(calls) == 3  # 1 + http_retry_count(2)


async def test_transport_retry_exhausted_attempts_one_plus_count(monkeypatch) -> None:
    """retry 耗尽 → attempts = 1 + http_retry_count，最终翻译仍为 LLMNetworkError。"""
    calls = _patch_client(
        monkeypatch,
        [("raise", httpx.ConnectError("boom"))] * 3,
    )
    with pytest.raises(LLMNetworkError):
        await _provider(http_retry_count=2).complete("q")
    assert len(calls) == 3  # 1 + 2


async def test_default_http_retry_count_from_settings(monkeypatch) -> None:
    """未显式传 http_retry_count → 用 settings.http_retry_count（默认 2）。"""
    from app.core.config import settings

    calls = _patch_client(
        monkeypatch,
        [("raise", httpx.ConnectError("boom"))] * (settings.http_retry_count + 1),
    )
    with pytest.raises(LLMNetworkError):
        await _provider().complete("q")
    assert len(calls) == settings.http_retry_count + 1


# ---- 不扩展 HTTP status retry：4xx/408/429/5xx 走 LLMProviderError，非 transport retry ----


async def test_http_4xx_not_transport_retried(monkeypatch) -> None:
    """HTTP 400（非 transient）→ 单 attempt，翻译为 LLMProviderError(retryable=False)。"""
    calls = _patch_client(monkeypatch, [("response", _FakeResponse(400))])
    with pytest.raises(LLMProviderError) as ei:
        await _provider(http_retry_count=2).complete("q")
    assert ei.value.retryable is False
    assert len(calls) == 1  # status error 不走 transport retry


async def test_http_408_not_transport_retried(monkeypatch) -> None:
    """HTTP 408（transient）→ 单 attempt，LLMProviderError(retryable=True)，不重复 transport。"""
    calls = _patch_client(monkeypatch, [("response", _FakeResponse(408))])
    with pytest.raises(LLMProviderError) as ei:
        await _provider(http_retry_count=2).complete("q")
    assert ei.value.retryable is True
    assert len(calls) == 1


async def test_http_5xx_not_transport_retried(monkeypatch) -> None:
    """HTTP 500（transient）→ 单 attempt，LLMProviderError(retryable=True)，不重复 transport。"""
    calls = _patch_client(monkeypatch, [("response", _FakeResponse(500))])
    with pytest.raises(LLMProviderError) as ei:
        await _provider(http_retry_count=2).complete("q")
    assert ei.value.retryable is True
    assert len(calls) == 1


# ---- cancellation 传播：CancelledError 不被 transport retry 吞掉 ----


async def test_cancellation_propagates_during_transport_retry(monkeypatch) -> None:
    """第二次 transport attempt 抛 CancelledError → 直接传播（BaseException 不落 except
    httpx.TransportError），不被 finalize 为 LLMNetworkError/重试。"""
    calls = _patch_client(
        monkeypatch,
        [
            ("raise", httpx.ConnectError("boom")),
            ("raise", asyncio.CancelledError()),
        ],
    )
    with pytest.raises(asyncio.CancelledError):
        await _provider(http_retry_count=2).complete("q")
    assert len(calls) == 2  # 第一次 transport 失败重试，第二次取消即终止（无第三次 attempt）


async def test_success_single_attempt(monkeypatch) -> None:
    """正常成功 → 单 attempt，返回文本。"""
    calls = _patch_client(monkeypatch, [("response", _FakeResponse(200, "ok"))])
    out = await _provider(http_retry_count=2).complete("q")
    assert out == "ok"
    assert len(calls) == 1
