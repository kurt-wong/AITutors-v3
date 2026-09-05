"""MockLLMProvider：无外部副作用的测试/流程 provider（fixture 可注入，无业务分支）。"""


class MockLLMProvider:
    name = "mock"

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses = responses or {}

    async def complete(self, prompt: str) -> str:
        return self._responses.get(prompt, "mock-response")
