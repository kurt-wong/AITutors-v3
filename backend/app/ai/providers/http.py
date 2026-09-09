"""HTTPLLMProvider：live external 调用（OpenAI 兼容 chat completions）。段 C 不实际发送。

BUG-V3-034（Phase 9-0 冻结）：transport exception → LLMNetworkError（可重试）；HTTP response
error → LLMProviderError（408/429/5xx retryable、4xx 其他 non-retryable）。不得混 transport
failure（client 无法连接）与 HTTP response failure（provider 返回非 2xx）。

BUG-V3-033（Phase 9-0 冻结）：HTTP transport retry 属同一次 Provider Invocation 内的传输层
重试——bounded（http_retry_count），仅对 httpx.TransportError 重试，不新增业务 invocation /
audit / budget（计数点在 gateway provider seam，先于本层）。HTTP status retry 语义不在此层
扩展（408/429/5xx 仍由 LLMProviderError(retryable=…) 表达，交 LLMExecutor 层）。CancelledError
为 BaseException，不被 except httpx.TransportError 捕获，自然传播。
"""

import json

import httpx

from app.core.config import settings
from app.core.errors import LLMNetworkError, LLMProviderError

# BUG-V3-034：HTTP response status → retryable（transient）分类。
_RETRYABLE_STATUS = frozenset({408, 429}) | set(range(500, 600))


class HTTPLLMProvider:
    def __init__(
        self,
        *,
        name: str,
        api_key: str | None = None,
        base_url: str,
        model: str,
        timeout: float,
        http_retry_count: int | None = None,
    ) -> None:
        self.name = name
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._http_retry_count = (
            settings.http_retry_count if http_retry_count is None else http_retry_count
        )
        if self._http_retry_count < 0:
            raise ValueError(f"http_retry_count must be >= 0, got {self._http_retry_count}")

    async def complete(self, prompt: str) -> str:
        resp = None
        last_transport_error: httpx.TransportError | None = None
        # I-1-A：条件 Authorization 头——api_key 非空才发，空/None 完全不发（Ollama 无 key，
        # 不伪造 Bearer）。I-1-A：trust_env=False——不读系统/环境代理，防 Windows 本地代理
        # （如 127.0.0.1:55219）劫持 localhost 直连。
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        for _ in range(self._http_retry_count + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout, trust_env=False) as client:
                    resp = await client.post(
                        f"{self._base_url}/chat/completions",
                        headers=headers,
                        json={"model": self._model, "messages": [{"role": "user", "content": prompt}]},
                    )
            except httpx.TransportError as exc:
                # 无法建立/维持 HTTP transport → 同 invocation 内 transport retry（BUG-V3-033）。
                # CancelledError 为 BaseException，不在此捕获，直接传播。
                last_transport_error = exc
                continue
            break
        if resp is None:
            # 全部 transport attempt 耗尽 → network error（可重试，交 LLMExecutor 层）
            raise LLMNetworkError(f"LLM transport failed: {last_transport_error}") from last_transport_error
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            raise LLMProviderError(
                f"LLM provider returned HTTP {status}",
                retryable=status in _RETRYABLE_STATUS,
            ) from exc
        try:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            # B-2（对抗审查）：HTTP 200 但 body 违反 adapter contract（非 JSON / choices 缺失/
            # 空 / message/content 缺失）→ 翻译为 LLMProviderError(retryable=False)。不得泄漏裸
            # JSONDecodeError/IndexError/KeyError/TypeError——会被 LLMExecutor._error_type 误分类
            # 为 'unknown'，且不在 retry/fallback 白名单内。retryable=False：请求已达 provider 且
            # 返回 200，属 contract violation 而非 transport/transient 失败，重试无意义（用户裁决）。
            raise LLMProviderError(
                f"LLM provider returned malformed body: {exc}", retryable=False
            ) from exc
        if content is None:
            # content 键存在但为 null → 同样 contract violation（明确按 adapter contract 处理）
            raise LLMProviderError(
                "LLM provider returned malformed body: content is null", retryable=False
            )
        return content
