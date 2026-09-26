"""LLM Gateway (30 §6): external 副作用唯一收敛链。live 为组合放行，缺任一前置拒绝记原因。
Phase C 不实调 live provider（段 F 后 live smoke）；这里把三态 + 放行链骨架建立起来。
Phase 4（Lock-4/Note-1）：live 真实 Provider Invocation seam = `_live()` 内 `provider.complete(...)` 正前方经 `invocation_counter.consume(task_id)` 原子计数——熔断按真实
Invocation 次数计，非 gateway.complete 层。mock/disabled 不计数。
FORMAL-E2E-ENABLEMENT-01：
- 正式默认 provider = mimo / mimo-v2.6-pro（MIMO V2.6 PRO）
- DeepSeek 配置保留（fallback / future evaluation，不删除）
- Provider Reality Tracking：记录 configured vs actual
- authorize()：由真实运行上下文（claimed task + budget ensure）注入，禁止 hardcode
"""

from app.ai.live_guard import require_allow_live
from app.ai.providers.http import HTTPLLMProvider
from app.ai.providers.mock import MockLLMProvider
from app.core.config import settings
from app.core.errors import GatewayDeniedError, GatewayDisabledError

# 正式 MIMO V2.6 PRO model ID（实测 GET /v1/models 返回，非猜测）
MIMO_V26_PRO_MODEL = "mimo-v2.6-pro"
LEGACY_TEST_MODEL_IDS = frozenset({"mimo-x-pro-preview"})


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
        live_providers: dict[str, object] | None = None,
    ) -> None:
        self.mode = mode
        self._allow_live = allow_live
        self._task_context = task_context
        self._budget_ok = budget_ok
        self._mock = mock_provider or MockLLMProvider()
        self._live_provider = live_provider
        # BUG-V3-035（Phase 9-3）：fallback 显式有序 provider 映射。live_provider 为单一
        # 默认（向后兼容），live_providers 按 provider 名路由（fallback 换 provider 用）。
        self._live_providers = live_providers or {}
        # Provider Reality Tracking：最近一次实际执行的 provider 名（等价机制，无 schema 变更）
        self._last_actual_provider: str | None = None
        self._last_configured_model: str | None = None

    def authorize(self, *, task_context: object, budget_ok: bool = True) -> None:
        """由真实运行上下文注入 live 授权。

        FORMAL-E2E-ENABLEMENT-01：禁止 hardcode=True / object() / dummy context。
        调用方必须传入真实 claimed task 上下文；budget_ok 必须在 BudgetService.ensure
        成功建立预算权威之后才能为 True。
        """
        if task_context is None:
            raise GatewayDeniedError(
                "authorize() requires real task_context; dummy/None is forbidden"
            )
        self._task_context = task_context
        self._budget_ok = bool(budget_ok)

    @property
    def last_actual_provider(self) -> str | None:
        return self._last_actual_provider

    @property
    def last_configured_model(self) -> str | None:
        return self._last_configured_model

    async def complete(
        self,
        prompt: str,
        *,
        task_id: object | None = None,
        invocation_counter: object | None = None,
        provider: str | None = None,
    ) -> str:
        if self.mode == "disabled":
            # 不初始化 HTTP client / live provider / 网络副作用（Gate C1）
            raise GatewayDisabledError("LLM gateway is disabled (30 §6)")
        if self.mode == "mock":
            return await self._mock.complete(prompt)
        if self.mode == "live":
            return await self._live(
                prompt, task_id=task_id, invocation_counter=invocation_counter, provider=provider
            )
        raise GatewayDisabledError(f"unknown gateway mode: {self.mode}")

    async def _live(
        self, prompt: str, *, task_id, invocation_counter, provider: str | None = None
    ) -> str:
        reasons: list[str] = []
        if not self._allow_live:
            reasons.append("--allow-live not granted")
        if self._task_context is None:
            reasons.append("task context missing")
        if not self._budget_ok:
            reasons.append("budget unavailable")
        live = self._resolve_live_provider(provider)
        if live is None:
            reasons.append("no live provider configured")
        if reasons:
            raise GatewayDeniedError("live denied: " + "; ".join(reasons))
        require_allow_live(self._allow_live)
        # B-1（独立对抗检查）：live 缺 counter/task_id → fail-closed。executor 唯一入口恒传二者；
        # 缺 counter 的 live 调用 = 绕过 MAX_LLM_CALLS 熔断的意图（Lock-4），拒绝而非静默放行。
        if invocation_counter is None or task_id is None:
            raise GatewayDeniedError(
                "live denied: missing invocation_counter/task_id (Lock-4 circuit breaker)"
            )
        # Provider Invocation Port seam：每次真实 provider 调用前原子计数（Lock-4/Note-1）
        await invocation_counter.consume(task_id)
        # Provider Reality Tracking：记录实际执行的 provider 名（等价机制）
        self._last_actual_provider = getattr(live, "name", type(live).__name__)
        self._last_configured_model = getattr(live, "_model", None) or getattr(
            live, "model", None
        )
        return await live.complete(prompt)

    def _resolve_live_provider(self, provider: str | None) -> object | None:
        """按 provider 名路由（BUG-V3-035 fallback）；名未命中 fail-closed（返回 None→deny）。
        B-1（对抗检查）：multi-provider mode（live_providers 非空）下 provider 名必须命中，
        未命中 = 配置错误 → 返回 None（fail-closed，_live 拒绝），不得静默回退到 live_provider
        ——否则 audit 记 fallback 名、实际调 primary 对象，identity 漂移破坏 Runtime Truth。
        single-provider mode（live_providers 空）才回退唯一默认 live_provider（向后兼容）。
        """
        if provider is not None and provider in self._live_providers:
            return self._live_providers[provider]
        if self._live_providers:
            return None
        return self._live_provider


def _build_mimo_provider() -> HTTPLLMProvider:
    """正式 MIMO V2.6 PRO provider。model 缺失/legacy ID → fail-closed。"""
    model = (settings.mimo_model or "").strip() or MIMO_V26_PRO_MODEL
    if model in LEGACY_TEST_MODEL_IDS:
        raise GatewayDisabledError(
            f"configured MIMO model {model!r} is a LEGACY TEST MODEL ID "
            f"(live API rejects it); formal target = {MIMO_V26_PRO_MODEL!r}"
        )
    base_url = (settings.mimo_base_url or "").strip() or "https://api.xiaomimimo.com/v1"
    return HTTPLLMProvider(
        name="mimo",
        api_key=settings.mimo_api_key,
        base_url=base_url,
        model=model,
        timeout=settings.llm_request_timeout_seconds,
    )


def _build_deepseek_provider() -> HTTPLLMProvider | None:
    """DeepSeek 配置保留（fallback / future evaluation）。缺 key/model 则不构建。"""
    key = (settings.deepseek_api_key or "").strip()
    model = (settings.deepseek_model or "").strip()
    if not key or not model:
        return None
    base_url = (settings.deepseek_base_url or "").strip() or "https://api.deepseek.com"
    return HTTPLLMProvider(
        name="deepseek",
        api_key=key,
        base_url=base_url,
        model=model,
        timeout=settings.llm_request_timeout_seconds,
    )


def build_gateway(
    *,
    allow_live: bool = False,
    task_context: object | None = None,
    budget_ok: bool = False,
) -> LLMGateway:
    """从配置建 Gateway（I-1-B）：live 模式优先 MIMO V2.6 PRO，DeepSeek 作显式 fallback。

    disabled/mock 不构造 live provider；live 才构造。timeout 由本 factory 显式从
    settings.llm_request_timeout_seconds 注入（Provider 保持 infrastructure 组件，
    不自行读全局 Settings）。
    FORMAL-E2E-ENABLEMENT-01：正式默认 = mimo / mimo-v2.6-pro。禁止把 legacy 测试
    model 当正式配置。Ollama 仅在未配置 MIMO 时作为本地开发回退（非正式生产路径）。
    """
    mode = settings.llm_gateway_mode
    live_provider = None
    live_providers: dict[str, object] = {}
    if mode == "live":
        mimo = _build_mimo_provider()
        live_providers["mimo"] = mimo
        live_provider = mimo  # single default = formal MIMO
        deepseek = _build_deepseek_provider()
        if deepseek is not None:
            live_providers["deepseek"] = deepseek
        if not settings.mimo_api_key and not (settings.ollama_base_url and settings.ollama_model):
            # 无 MIMO key 且无 Ollama → 仍构建 MIMO shell（缺 key 时 HTTP 层不发 Authorization，
            # 由 provider 返回 401/403 作为真实失败）；不静默切到未配置的 Ollama。
            pass
    return LLMGateway(
        mode,
        allow_live=allow_live,
        task_context=task_context,
        budget_ok=budget_ok,
        live_provider=live_provider,
        live_providers=live_providers if len(live_providers) > 1 else {},
    )
