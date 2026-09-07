"""HTTPLLMProvider：live external 调用（OpenAI 兼容 chat completions）。段 C 不实际发送。

BUG-V3-034（Phase 9-0 冻结）：transport exception → LLMNetworkError（可重试）；HTTP response
error → LLMProviderError（408/429/5xx retryable、4xx 其他 non-retryable）。不得混 transport
failure（client 无法连接）与 HTTP response failure（provider 返回非 2xx）。
"""

import httpx

from app.core.errors import LLMNetworkError, LLMProviderError

# BUG-V3-034：HTTP response status → retryable（transient）分类。
_RETRYABLE_STATUS = frozenset({408, 429}) | set(range(500, 600))


class HTTPLLMProvider:
    def __init__(self, *, name: str, api_key: str, base_url: str, model: str, timeout: float) -> None:
        self.name = name
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def complete(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={"model": self._model, "messages": [{"role": "user", "content": prompt}]},
                )
        except httpx.TransportError as exc:
            # 无法建立/维持 HTTP transport → network error（可重试）
            raise LLMNetworkError(f"LLM transport failed: {exc}") from exc
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            raise LLMProviderError(
                f"LLM provider returned HTTP {status}",
                retryable=status in _RETRYABLE_STATUS,
            ) from exc
        data = resp.json()
        return data["choices"][0]["message"]["content"]
