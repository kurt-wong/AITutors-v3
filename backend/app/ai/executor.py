"""LLMExecutor（H Phase 4，30 §5/§10/§11）：唯一 LLM 执行入口 + 真实 Invocation 熔断计数。

调用链：Domain → LLMExecutor → LLMGateway → Provider（Lock-3 唯一入口；mock/live/disabled
不因运行模式改调用架构）。一次 `complete()` = 一个 Logical LLM Request。M1 每个 Attempt 恰
一个 Logical Request ⇒ Attempt:Audit = 1:1（G5 不变式；架构能力 1:N 为 Note-2 保留，不预加
request_seq，F-3）。

Live 生命周期（用户裁决 §7 冻结顺序）：
  1. ensure 五账户 + reserve + create_audit(started) —— 同一事务（Lock-6；audit 创建失败
     → rollback 自动补偿 reserve，探针 P2 实证）
  2. bounded internal retry：每轮 `gateway.complete(prompt, task_id=…)`。真实 Provider
     Invocation seam 在 gateway `_live`（counter.consume 在 provider.complete 正前方，
     Lock-4/Note-1）——熔断按真实调用计，非 attempt/audit 数
  3. 成功 → finalize(completed) + settle(actual=reserve)；失败 → finalize(failed) +
     settle(release, actual=0) → re-raise；记账异常（BudgetSettlementError）不吞（F-6）

executor 是跨网络调用的运行时事务编排者：reserve/audit 边界与 finalize/settle 边界由本层
显式 commit/rollback；`consume` 每次立即 commit（计数须在 provider 调用前持久）。
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.audit import build_idempotency_key
from app.ai.budget import BudgetService, five_account_refs
from app.ai.gateway import LLMGateway
from app.core.config import settings
from app.core.errors import CircuitOpen, LLMNetworkError, LLMProviderError
from app.repositories.runtime_repository import LlmCallAuditRepository, TaskRepository

DEFAULT_RESERVE_AMOUNT = Decimal("1")

_RETRYABLE_LLM_ERRORS = (LLMNetworkError, LLMProviderError)


class ProviderInvocationCounter:
    """真实 Provider Invocation 原子熔断计数（Lock-4/Clarification-2）。

    consume() 须在每次真实 provider 调用前执行：tasks.llm_invocations 条件 UPDATE
    （count < max → +1 放行；越界 → CircuitOpen，provider 不发出）。每次 consume 立即
    commit——计数在 provider 调用前持久，请求后续失败/rollback 不得吞掉真实调用。
    """

    def __init__(self, session: AsyncSession, *, max_invocations: int) -> None:
        self._session = session
        self._max = max_invocations
        self._tasks = TaskRepository(session)

    async def consume(self, task_id: uuid.UUID) -> None:
        allowed = await self._tasks.consume_llm_invocation(
            task_id=task_id, max_invocations=self._max
        )
        if not allowed:
            await self._session.rollback()
            raise CircuitOpen(
                f"MAX_LLM_CALLS_PER_TASK reached ({self._max}): task={task_id}"
            )
        await self._session.commit()


class LLMExecutor:
    """唯一执行入口：按 gateway.mode 内部分流，mock/disabled 复用同一 complete() 入口。"""

    def __init__(
        self,
        session: AsyncSession,
        gateway: LLMGateway,
        *,
        retry_count: int | None = None,
        reserve_amount: Decimal = DEFAULT_RESERVE_AMOUNT,
        max_invocations: int | None = None,
    ) -> None:
        self._session = session
        self._gateway = gateway
        self._retry_count = (
            settings.llm_request_retry_count if retry_count is None else retry_count
        )
        self._reserve_amount = reserve_amount
        self._max_invocations = (
            settings.max_llm_calls_per_task if max_invocations is None else max_invocations
        )

    async def complete(
        self,
        prompt: str,
        *,
        le_stage: str,
        le_hash: str,
        attempt_id: uuid.UUID | None = None,
        task_id: uuid.UUID | None = None,
        document_id: uuid.UUID | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> str:
        """执行一个 Logical LLM Request，返回 provider 文本。

        mock/disabled → 不产生 audit/budget/计数副作用（G4），语义由 gateway 决定（disabled
        抛 GatewayDisabledError）；task_id/document_id/provider/model 此时为可选项，供 live
        使用、不参与 mock 路径。live → 完整 reserve/audit/retry/settle 生命周期，四个身份
        参数全部必需（缺任一 fail-closed raise，Lock-4 计数与 audit 行不可缺字段）。
        """
        if self._gateway.mode != "live":
            return await self._gateway.complete(prompt)
        return await self._complete_live(
            prompt,
            le_stage=le_stage,
            le_hash=le_hash,
            attempt_id=attempt_id,
            task_id=task_id,
            document_id=document_id,
            provider=provider,
            model=model,
        )

    async def _complete_live(
        self,
        prompt: str,
        *,
        le_stage: str,
        le_hash: str,
        attempt_id: uuid.UUID | None,
        task_id: uuid.UUID | None,
        document_id: uuid.UUID | None,
        provider: str | None,
        model: str | None,
    ) -> str:
        if task_id is None or document_id is None:
            raise ValueError("live execution requires task_id and document_id")
        if provider is None or model is None:
            raise ValueError("live execution requires provider and model")

        s = self._session
        repo = LlmCallAuditRepository(s)
        budget = BudgetService(s)
        request_id = uuid.uuid4()  # 绑定 request 预算账户 scope 与 audit 行身份（同 id）
        refs = five_account_refs(
            request_id=str(request_id),
            task_id=str(task_id),
            le_hash=le_hash,
            le_stage=le_stage,
            document_id=str(document_id),
            day=datetime.now(timezone.utc).date().isoformat(),
        )
        idem = build_idempotency_key(
            logical_execution_stage=le_stage,
            logical_execution_hash=le_hash,
            attempt_id=attempt_id,
            provider=provider,
            model=model,
            stage=le_stage,
        )
        counter = ProviderInvocationCounter(s, max_invocations=self._max_invocations)

        # Phase A：ensure 五账户 + reserve + audit STARTED 同一事务（Lock-6）
        try:
            for ref in refs:
                await budget.ensure(ref)
            await budget.reserve(refs, self._reserve_amount)
            await repo.create_audit(
                request_id=request_id,
                idempotency_key=idem,
                logical_execution_stage=le_stage,
                logical_execution_hash=le_hash,
                attempt_id=attempt_id,
                task_id=task_id,
                document_id=document_id,
                stage=le_stage,
                provider=provider,
                model=model,
                status="started",
                prompt_chars=len(prompt),
            )
            await s.commit()
        except BaseException:
            # audit 创建/reserve 失败 → 同事务 rollback 补偿（零残留，无部分 reservation）
            await s.rollback()
            raise

        # Phase B：bounded internal retry（重试沿用同 audit / 同 logical request）
        outcome: str | None = None
        last_exc: Exception | None = None
        try:
            for i in range(self._retry_count + 1):
                try:
                    outcome = await self._gateway.complete(
                        prompt, task_id=task_id, invocation_counter=counter
                    )
                    break
                except _RETRYABLE_LLM_ERRORS as exc:
                    # BUG-V3-034：LLMProviderError(retryable=False)（4xx 非 transient）不重试。
                    if isinstance(exc, LLMProviderError) and not exc.retryable:
                        raise
                    if i < self._retry_count:
                        continue
                    raise
        except Exception as exc:
            # 含 CircuitOpen（熔断不重试）与非重试性错误 → 一律进入失败终态化。
            # CancelledError/KeyboardInterrupt/SystemExit（BaseException 非 Exception）不在此捕获 →
            # 直接传播，audit 保持 STARTED 由 recovery 判 unknown（不误 finalize 为 failed）。
            last_exc = exc

        # Phase C1：audit terminalization（Provider Invocation Runtime Truth，30 §10）
        # 独立于 settle 先行 commit——audit 终态一旦确定，不因后续 settle 失败回滚为 STARTED。
        # Lock-6 只要求 reserve + audit STARTED 同事务（Phase A），未要求 finalize + settle 同事务。
        try:
            if outcome is not None:
                await repo.finalize_audit(request_id, status="completed")
            else:
                await repo.finalize_audit(
                    request_id, status="failed",
                    error_type=self._error_type(last_exc),
                )
            await s.commit()
        except Exception as exc:
            await s.rollback()
            raise

        # Phase C2：budget settle（accounting，30 §11）后行——失败显式暴露（F-6），不掩盖
        # provider 结果（audit 已在 C1 terminalized）；reserve 残留由 reclaim 对账回收。
        try:
            if outcome is not None:
                await budget.settle(
                    refs, reserved=self._reserve_amount, actual=self._reserve_amount
                )
            else:
                await budget.settle(
                    refs, reserved=self._reserve_amount, actual=Decimal("0")
                )
            await s.commit()
        except Exception as exc:
            await s.rollback()
            raise

        if last_exc is not None:
            raise last_exc
        return outcome  # type: ignore[return-value]  # outcome 非 None 已由上面保证

    @staticmethod
    def _error_type(exc: BaseException | None) -> str:
        if exc is None:
            return "unknown"
        return getattr(exc, "error_type", "unknown")
