"""HTTPLLMProvider：live external 调用（OpenAI 兼容 chat completions）。段 C 不实际发送。"""

import httpx


class HTTPLLMProvider:
    def __init__(self, *, name: str, api_key: str, base_url: str, model: str, timeout: float) -> None:
        self.name = name
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def complete(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "messages": [{"role": "user", "content": prompt}]},
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]
