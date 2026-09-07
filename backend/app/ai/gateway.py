"""LLM Gateway（30 §6）：external 副作用唯一收敛链。live 为组合放行，缺任一前置拒绝记原因。

段 C 不实调 live provider（段 F 后 live smoke）；这里把三态 + 放行链骨架建立起来。

Phase 4（Lock-4/Note-1）：live 真实 Provider Invocation seam = `_live()` 内
`provider.complete(...)` 正前方经 `invocation_counter.consume(task_id)` 原子计数——熔断按真实
Invocation 次数计，非 gateway.complete 层。mock/disabled 不计数。
"""

from app.ai.live_guard import require_allow_live
from app.ai.providers.mock import MockLLMProvider
from app.core.config import settings
from app.core.errors import GatewayDeniedError, GatewayDisabledError


class LLMGateway:
    """三态：disabled（默认，调用即抛）/ mock（测试）/ live（四前置组合放行）。"""

    def __init__(
        self,
        mode: str,
        *,
        allow_live: bool = False,
        task_context: object | None = None,
        budget_ok: bool = False,
        mock_provider: MockLLMProvider | None = None,
        live_provider: object | None = None,
    ) -> None:
        self.mode = mode
        self._allow_live = allow_live
        self._task_context = task_context
        self._budget_ok = budget_ok
        self._mock = mock_provider or MockLLMProvider()
        self._live_provider = live_provider

    async def complete(
        self,
        prompt: str,
        *,
        task_id: object | None = None,
        invocation_counter: object | None = None,
    ) -> str:
        if self.mode == "disabled":
            # 不初始化 HTTP client / live provider / 网络副作用（Gate C1）
            raise GatewayDisabledError("LLM gateway is disabled (30 §6)")
        if self.mode == "mock":
            return await self._mock.complete(prompt)
        if self.mode == "live":
            return await self._live(prompt, task_id=task_id, invocation_counter=invocation_counter)
        raise GatewayDisabledError(f"unknown gateway mode: {self.mode}")

    async def _live(self, prompt: str, *, task_id, invocation_counter) -> str:
        reasons: list[str] = []
        if not self._allow_live:
            reasons.append("--allow-live not granted")
        if self._task_context is None:
            reasons.append("task context missing")
        if not self._budget_ok:
            reasons.append("budget unavailable")
        if self._live_provider is None:
            reasons.append("no live provider configured")
        if reasons:
            raise GatewayDeniedError("live denied: " + "; ".join(reasons))
        require_allow_live(self._allow_live)
        # B-1（独立对抗审查）：live 缺 counter/task_id → fail-closed。executor 唯一入口恒传二者；
        # 缺 counter 的 live 调用 = 绕过 MAX_LLM_CALLS 熔断的意图（Lock-4），拒绝而非静默放行。
        if invocation_counter is None or task_id is None:
            raise GatewayDeniedError(
                "live denied: missing invocation_counter/task_id (Lock-4 circuit breaker)"
            )
        # Provider Invocation Port seam：每次真实 provider 调用前原子计数（Lock-4/Note-1）
        await invocation_counter.consume(task_id)
        return await self._live_provider.complete(prompt)


def build_gateway() -> LLMGateway:
    """从配置建 Gateway：disabled/mock 不构造 live provider；live 才需要凭证。"""
    mode = settings.llm_gateway_mode
    return LLMGateway(mode)
