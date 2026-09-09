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
    """最小 response：仅支持 raise_for_status() 与 json()。

    json_body：直接返回给定 dict（注入 malformed contract body）；raw：非 JSON 文本，
    json() 内部 json.loads 抛 JSONDecodeError。二者均 None 时返回默认合法 body。
    """

    def __init__(self, status: int = 200, content: str = "ok-text", json_body=None, raw=None) -> None:
        self.status_code = status
        self._content = content
        self._json_body = json_body
        self._raw = raw
        self._request = httpx.Request("POST", "http://localhost")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = httpx.Response(self.status_code, request=self._request)
            raise httpx.HTTPStatusError(
                f"server error {self.status_code}", request=self._request, response=response
            )

    def json(self):
        if self._raw is not None:
            import json as _json

            return _json.loads(self._raw)
        if self._json_body is not None:
            return self._json_body
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


# ---- B-2（对抗审查）：HTTP 200 + malformed body → 翻译为 LLMProviderError(retryable=False) ----


@pytest.mark.parametrize(
    "body",
    [
        {"foo": "bar"},  # choices 缺失 → KeyError
        {"choices": None},  # choices 为 null → TypeError
        {"choices": []},  # choices 空 → IndexError
        {"choices": [{}]},  # 缺 message → KeyError
        {"choices": [{"message": {}}]},  # 缺 content → KeyError
        {"choices": [{"message": {"content": None}}]},  # content 为 null → 显式 contract 处理
    ],
    ids=[
        "missing-choices",
        "choices-null",
        "empty-choices",
        "missing-message",
        "missing-content",
        "content-null",
    ],
)
async def test_malformed_json_body_raises_provider_error(monkeypatch, body) -> None:
    """HTTP 200 + body 违反 adapter contract → LLMProviderError(retryable=False)，不泄漏裸异常。

    修复前缺陷：泄漏 IndexError/KeyError/TypeError，经 LLMExecutor._error_type 误分类为
    'unknown'（而非 provider_error），且不在 retry/fallback 白名单内 → 既不重试也不降级。
    """
    calls = _patch_client(monkeypatch, [("response", _FakeResponse(json_body=body))])
    with pytest.raises(LLMProviderError) as ei:
        await _provider(http_retry_count=0).complete("q")
    assert ei.value.retryable is False
    assert ei.value.error_type == "provider_error"
    assert len(calls) == 1  # 非 transport error，不走 transport retry


async def test_nonjson_body_raises_provider_error(monkeypatch) -> None:
    """HTTP 200 + 非 JSON body → LLMProviderError(retryable=False)，不泄漏 JSONDecodeError。"""
    calls = _patch_client(monkeypatch, [("response", _FakeResponse(raw="<html>not json</html>"))])
    with pytest.raises(LLMProviderError) as ei:
        await _provider(http_retry_count=0).complete("q")
    assert ei.value.retryable is False
    assert ei.value.error_type == "provider_error"
    assert len(calls) == 1


# ---- BUG-V3-036（C-1）：负 http_retry 构造 fail-fast + http_retry_count=0 合法边界 ----


def test_negative_http_retry_count_rejected() -> None:
    """http_retry_count=-1 必须在构造层 fail-fast（ValueError），0 transport call。"""
    with pytest.raises(ValueError):
        _provider(http_retry_count=-1)


async def test_http_retry_count_zero_success_single_attempt(monkeypatch) -> None:
    """C-1 边界：http_retry_count=0 合法——成功恰好 1 次 HTTP attempt（1 + 0）。"""
    calls = _patch_client(monkeypatch, [("response", _FakeResponse(200, "ok"))])
    out = await _provider(http_retry_count=0).complete("q")
    assert out == "ok"
    assert len(calls) == 1


# ---- I-1-A：条件 Authorization 头 + trust_env=False ----


async def test_conditional_auth_header_and_trust_env(monkeypatch) -> None:
    """I-1-A：api_key 非空才发 Authorization 头；空/None 不发（Ollama 无 key 不伪造 Bearer）；
    AsyncClient 用 trust_env=False（不读系统/环境代理，防 localhost 被代理劫持）。"""
    captured: dict = {}

    class _CapturingClient:
        def __init__(self, *args, **kwargs) -> None:
            captured["client_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> bool:
            return False

        async def post(self, url, **kwargs):
            captured["post_kwargs"] = kwargs
            return _FakeResponse(status=200, content="ok")

    monkeypatch.setattr(httpx, "AsyncClient", _CapturingClient)

    # 非空 key → 有 Authorization 头 + trust_env=False
    p = HTTPLLMProvider(name="x", api_key="k", base_url="http://localhost", model="m", timeout=1.0)
    assert await p.complete("q") == "ok"
    assert captured["post_kwargs"]["headers"].get("Authorization") == "Bearer k"
    assert captured["client_kwargs"].get("trust_env") is False

    # 空 key（None）→ 无 Authorization 头
    p2 = HTTPLLMProvider(name="x", api_key=None, base_url="http://localhost", model="m", timeout=1.0)
    assert await p2.complete("q") == "ok"
    assert "Authorization" not in captured["post_kwargs"]["headers"]
