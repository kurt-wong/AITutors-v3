"""TaskExecutor（H Phase 8）：Worker 循环编排，只拥 Runtime Authority（用户修正 7）。

编排 `document_ingest` 三 stage：Seal → Annotation → Compile（Resolve + Compile + Gate +
Admission 由 `GateService.run` 收口）。每个 stage 独立 session 事务（30 §12 崩溃窗口只在
stage 边界）；Artifact-first 复用由 domain service 的 LE 幂等保证——复用返回既有行、不落
新 attempt_id（Lock-2「Attempt 只在真执行时创建」）。Seal 本地确定性、不贯通 attempt_id
（plan Phase 5：SealService 本轮不碰）。

H8-2 双层失败语义：`llm_call_audit` = Provider Invocation Runtime Truth（executor 已终态化
completed/failed）；`task` = Logical Execution Outcome（本层把下游失败分类并写入 task failure）。
parse/forbidden 在 audit 层 completed、task 层 failed。H8-1：失败详情经 `TaskService.fail`
持久化到 task_claims（outcome/error_type + lease_snapshot.error_detail），不丢诊断信息。

TaskExecutor 不判 Question Identity / Dedup / Gate / Admission / decision_status——只驱动既有
domain service 执行与恢复安全。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from app.ai.executor import LLMExecutor
from app.ai.gateway import LLMGateway
from app.core.config import settings
from app.core.errors import LLMNetworkError, LLMProviderError, V3Error
from app.core.hashing import sha256_hex
from app.domains.annotation.service import AnnotationService
from app.domains.gate.service import GateService
from app.domains.source.seal import SealService
from app.domains.task.service import TaskService
from app.models.runtime import Task
from app.models.snapshot import SemanticAnnotation
from app.models.source import DocumentSourceVersion
from app.repositories.base import RepositoryError
from app.repositories.runtime_repository import LeaseConflict

logger = logging.getLogger(__name__)

_TASK_TYPE = "document_ingest"

# BUG-V3-035（Phase 9-3）：仅 retryable failure 可触发 fallback。CancelledError 为
# BaseException 不在此（直接传播）；LLMProviderError(retryable=False) 为 provider 明确
# 拒绝，不 fallback（在循环内显式判断）。
_FALLBACK_RETRYABLE = (LLMNetworkError, LLMProviderError)


def build_annotation_prompt(body_text: str) -> str:
    """M1 最小 prompt 构造（annotation 的 prompt 由 caller 提供，本层即 caller）。

    prompt 契约属未来完善（真实 live 前）；M1 mock/确定性流程仅需把 sealed 正文喂给
    annotation stage，真实指令模板不在本轮冻结。
    """
    return (
        "你是题目语义标注助手。对下列文档文本做语义标注，输出符合 "
        "semantic-metadata-annotation schema 的 JSON（semantic_units 数组）。\n\n"
        f"<document>\n{body_text}\n</document>\n"
    )


def _classify_error(exc: BaseException) -> str:
    """失败分类（H8-2）：domain service 异常 → task failure 的 error_type 分类。

    V3Error 携带其 error_type（provider_error/network_error/conflict/…）；ValueError 为
    parse/forbidden 校验失败（audit 已完成 → task 判 failed）→ validation_error。
    """
    if isinstance(exc, V3Error):
        return exc.error_type
    if isinstance(exc, ValueError):
        return "validation_error"
    return "system_error"


class TaskExecutor:
    """Worker 编排器：claim → 逐 stage 调 domain service → complete / fail（token 条件写）。"""

    def __init__(
        self,
        session_factory,
        *,
        llm_gateway: LLMGateway,
        ocr_extractor,
        default_provider: str = "ollama",
        default_model: str = "qwen3.5-9b",
        lease_seconds: int | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._gateway = llm_gateway
        self._ocr_extractor = ocr_extractor
        self._default_provider = default_provider
        self._default_model = default_model
        self._lease_seconds = lease_seconds

    # ------------------------------------------------------------------ run_once

    async def run_once(self, *, worker_id: str) -> bool:
        """claim 一个 queued task 并处理完整生命周期。返回是否处理了 task（False = 无 queued）。"""
        lease_token = uuid.uuid4().hex
        claimed = await self._claim_next(worker_id, lease_token)
        if claimed is None:
            return False
        task_id = claimed["id"]
        try:
            await self._process(task_id, worker_id, lease_token)
        except Exception as exc:
            # 只捕获业务异常；CancelledError/KeyboardInterrupt/SystemExit 正常传播
            # （审查 MEDIUM：except BaseException 会吞掉取消/中断信号，导致 Ctrl+C 后
            # 进程不退出且把任务误标 failed）。
            await self._fail_task(task_id, worker_id, lease_token, exc)
        return True

    async def _claim_next(self, worker_id: str, lease_token: str) -> dict | None:
        async with self._session_factory() as s:
            claimed = await self._task_service(s).claim_next(
                worker_id=worker_id, lease_token=lease_token
            )
            if claimed is None:
                return None
            await s.commit()
            return claimed

    # ------------------------------------------------------------------ process

    async def _process(self, task_id: uuid.UUID, worker_id: str, lease_token: str) -> None:
        params = await self._load_params(task_id)
        await self._heartbeat(task_id, worker_id, lease_token)
        version = await self._seal_stage(params)
        await self._heartbeat(task_id, worker_id, lease_token)
        async with self._lease_heartbeat(task_id, worker_id, lease_token):
            ann = await self._annotation_stage(task_id, version, params)
        await self._heartbeat(task_id, worker_id, lease_token)
        await self._compile_stage(version, ann)
        await self._complete_task(task_id, worker_id, lease_token)

    async def _load_params(self, task_id: uuid.UUID) -> dict:
        async with self._session_factory() as s:
            task = await s.get(Task, task_id)
            if task is None:
                raise RepositoryError(f"task {task_id} not found")
            return dict(task.task_params)

    # -- stage 1: Seal（本地确定性；attempt_id 不贯通，plan Phase 5） --------------

    async def _seal_stage(self, params: dict) -> DocumentSourceVersion:
        file_path = params.get("file_path")
        if not file_path:
            raise RepositoryError("task_params.file_path missing (seal requires file bytes)")
        file_bytes = Path(file_path).read_bytes()
        async with self._session_factory() as s:
            version = await SealService(s).seal_document(
                file_bytes=file_bytes,
                file_name=params.get("file_name", "document.pdf"),
                file_type=params.get("file_type", "pdf"),
                role=params.get("role", "native"),
                provider=params.get("seal_provider", "native"),
                extractor=self._ocr_extractor,
            )
            await s.commit()
            return version

    # -- stage 2: Annotation（LLM stage 经 LLMExecutor；分配 attempt，Lock-2） ----

    async def _annotation_stage(
        self,
        task_id: uuid.UUID,
        version: DocumentSourceVersion,
        params: dict,
    ) -> SemanticAnnotation:
        prompt = build_annotation_prompt(version.body_text)
        # 同一 Task Attempt 贯穿 primary + fallback（BUG-V3-035：fallback 不得改变 Task Attempt）。
        attempt_id = uuid.uuid4()

        # primary 的 model_config_hash：显式优先（向后兼容）；否则按实际 invocation 配置算。
        # fallback 必须按实际 provider/model 算（新 config → 新 LE，X≠Y），不得复用 primary
        # 显式 hash——否则 fallback 换 provider 却得到同一 LE，违反 BUG-V3-035 身份边界。
        provider = params.get("llm_provider", self._default_provider)
        model = params.get("llm_model", self._default_model)
        chain = [
            (
                provider,
                model,
                params.get("model_config_hash")
                or sha256_hex({"provider": provider, "model": model}),
            )
        ]
        # fallback：默认关闭；显式、有限、有序列表（禁自动发现/随机/动态推断，BUG-V3-035）。
        # 去重：禁 fallback 到 primary 自己 / 循环 fallback（同一 provider+model 只尝试一次）。
        seen = {(provider, model)}
        if settings.provider_fallback_enabled:
            for fb in params.get("llm_fallback", []):
                fb_provider = fb["provider"]
                fb_model = fb["model"]
                key = (fb_provider, fb_model)
                if key in seen:
                    continue
                seen.add(key)
                chain.append(
                    (
                        fb_provider,
                        fb_model,
                        sha256_hex({"provider": fb_provider, "model": fb_model}),
                    )
                )

        last_exc: Exception | None = None
        for prov, mdl, mch in chain:
            try:
                async with self._session_factory() as s:
                    executor = LLMExecutor(s, self._gateway)
                    ann = await AnnotationService(s, executor).annotate(
                        source_version_id=version.id,
                        prompt=prompt,
                        model_config_hash=mch,
                        task_type=_TASK_TYPE,
                        attempt_id=attempt_id,
                        task_id=task_id,
                        document_id=version.document_id,
                        provider=prov,
                        model=mdl,
                    )
                    await s.commit()
                    return ann
            except _FALLBACK_RETRYABLE as exc:
                # BUG-V3-035：provider 明确拒绝（retryable=False，4xx 非 transient）不 fallback，
                # 立即传播。CancelledError 为 BaseException 不在此捕获，直接传播。
                if isinstance(exc, LLMProviderError) and not exc.retryable:
                    raise
                last_exc = exc
                continue
        # primary + 全部 fallback 耗尽 → re-raise 最后一个 retryable 异常（task fail）
        assert last_exc is not None
        raise last_exc

    # -- stage 3: Compile（Resolve + Compile + Gate + Admission） -----------------

    async def _compile_stage(
        self,
        version: DocumentSourceVersion,
        ann: SemanticAnnotation,
    ) -> None:
        async with self._session_factory() as s:
            await GateService(s).run(
                source_version_id=version.id,
                annotation_id=ann.id,
                task_type=_TASK_TYPE,
                attempt_id=uuid.uuid4(),
            )
            await s.commit()

    # ------------------------------------------------------------------ liveness

    async def _heartbeat(
        self, task_id: uuid.UUID, worker_id: str, lease_token: str
    ) -> None:
        """续租（liveness renewal）：把 lease 滑到 now()+lease（DB now() 单源，独立 session
        commit）。stage 边界调用；长 LLM stage 内由 _lease_heartbeat 持续调用（BUG-V3-037）。
        """
        async with self._session_factory() as s:
            await self._task_service(s).heartbeat(
                task_id, worker_id=worker_id, lease_token=lease_token
            )
            await s.commit()

    # -- 持续 heartbeat（BUG-V3-037：长 LLM stage 内续租） --------------------------

    @property
    def _resolved_lease_seconds(self) -> int:
        """实际生效的 lease 秒数（与 _task_service 的 lease_seconds 解析一致）。"""
        if self._lease_seconds is not None:
            return self._lease_seconds
        return settings.task_claim_lease_seconds

    @property
    def _heartbeat_interval_seconds(self) -> float:
        """持续 heartbeat 周期 = lease / 4（严格 < lease，lease 过期前至少续一次）。"""
        return self._resolved_lease_seconds / 4.0

    @asynccontextmanager
    async def _lease_heartbeat(
        self, task_id: uuid.UUID, worker_id: str, lease_token: str
    ) -> AsyncIterator[asyncio.Task[None]]:
        """长阻塞 stage 内的持续续租（BUG-V3-037）。

        后台 renew loop 周期调用 _heartbeat，把 lease 持续滑到 now()+lease，使慢 LLM 调用
        （> lease）不再天然触发 lease 过期。只做 liveness renewal（复用 _heartbeat，独立
        session + commit，DB now() 单源），不创建 attempt / 不写 audit / 不耗 budget /
        不参与 artifact identity（R6）。

        异常语义（R5）：
          - LeaseConflict（情况 B：lease 真丢失 / 被 recover 接管 / 四元组不匹配）→ 停循环
            （不无限重试失效 claim）；边界 _heartbeat/_complete 会再抛 LeaseConflict 走既有
            fail-loud 路径。
          - 其它 Exception（情况 A：瞬时 DB/网络故障等）→ 下一 tick 重试（Worker 仍自认拥有
            Task，只是暂时无法向 DB 证明）。
          - CancelledError（BaseException）→ 静默退出（finally 清理所致）。
        finally 保证 loop cancel + await，无 orphan background task（R2）。
        """
        stop = asyncio.Event()

        async def _renew_loop() -> None:
            try:
                while not stop.is_set():
                    await asyncio.sleep(self._heartbeat_interval_seconds)
                    if stop.is_set():
                        return
                    try:
                        await self._heartbeat(task_id, worker_id, lease_token)
                    except LeaseConflict as exc:
                        # 情况 B：lease ownership 已失 → 停续租；边界检查会 fail-loud
                        logger.warning(
                            "task %s heartbeat stopped: lease ownership lost (%s) by worker %s",
                            task_id, exc, worker_id,
                        )
                        return
                    except Exception as exc:
                        # 情况 A：瞬时 DB/网络故障 → 下一 tick 重试
                        logger.warning(
                            "task %s heartbeat renewal failed; will retry (%s) by worker %s",
                            task_id, exc, worker_id,
                        )
            except asyncio.CancelledError:
                pass

        loop = asyncio.create_task(_renew_loop())
        try:
            yield loop
        finally:
            stop.set()
            loop.cancel()
            try:
                await loop
            except asyncio.CancelledError:
                pass

    # ------------------------------------------------------------------ terminal

    async def _complete_task(
        self, task_id: uuid.UUID, worker_id: str, lease_token: str
    ) -> None:
        async with self._session_factory() as s:
            await self._task_service(s).complete(
                task_id, worker_id=worker_id, lease_token=lease_token
            )
            await s.commit()

    async def _fail_task(
        self, task_id: uuid.UUID, worker_id: str, lease_token: str, exc: BaseException
    ) -> None:
        try:
            async with self._session_factory() as s:
                await self._task_service(s).fail(
                    task_id,
                    worker_id=worker_id,
                    lease_token=lease_token,
                    error_type=_classify_error(exc),
                    error_detail=str(exc),
                )
                await s.commit()
        except LeaseConflict:
            # lease 已失效（task 已被 recover 接管）→ 不重复写终态；状态由 recover 处理
            logger.warning(
                "task %s failure not persisted: lease already lost (recover-owned)", task_id
            )

    # ------------------------------------------------------------------ helpers

    def _task_service(self, session) -> TaskService:
        if self._lease_seconds is None:
            return TaskService(session)
        return TaskService(session, lease_seconds=self._lease_seconds)
