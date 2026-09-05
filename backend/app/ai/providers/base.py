"""LLM Provider 抽象（Gateway 单一构造链，00 §3/30 §6）。"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    async def complete(self, prompt: str) -> str: ...
