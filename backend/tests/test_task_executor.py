"""H Phase 8 — TaskExecutor 编排（真实 PostgreSQL，可重入）。

锁定（plan Phase 8 验证项 + H8-1/H8-2）：
  - 端到端：enqueue(document_ingest, file_path) → run_once → task succeeded +
    seal(1 doc + 1 version) + annotation(1 valid) + compile(1 candidate approved) +
    admission 物化(1 Question + 1 Instance)
  - 幂等 replay：成功后 retry 再 run → 全链路 artifact 复用（零新增，Lock-2）
  - 失败：annotation provider 失败 → task failed + task_claims.outcome=failed +
    error_type/error_detail 持久化（H8-1）
  - parse 失败 → task failed + error_type=validation_error（H8-2 双层失败语义：
    audit 层 completed / task 层 failed）
  - TaskService.complete/fail 写 task_claims 终态（claim 生命周期完整）

可重入性：每个测试 enqueue 唯一 file_path（tmp_path），cleanup 按 FK 序删净（串行安全）。
"""

import json
import asyncio
import uuid

import pytest
from sqlalchemy import func, select, text

from app.ai.gateway import LLMGateway
from app.ai.ocr.result import OCRLine, OCRResult
from app.core.config import settings
from app.core.errors import LLMNetworkError, LLMProviderError
from app.core.hashing import sha256_hex
from app.db.session import async_session_maker
from app.domains.task.executor import TaskExecutor
from app.domains.task.service import TaskService
from app.models.content import Question, QuestionInstance
from app.models.snapshot import AdmissionCandidate, SemanticAnnotation
from app.models.source import Document, DocumentSourceVersion
from test_annotation_dbflow import _FixedJSONProvider
from test_gate_service import SINGLE_LINES, _single_units

_CLEANUP_TABLES = (
    "admission_events", "instance_role_contents", "material_links",
    "unit_group_members", "question_instances", "unit_groups", "materials",
    "validation_events",  # EB-008：FK → admission_candidates / source_versions
    "admission_candidates", "semantic_annotations", "document_source_lines",
    "task_claims", "document_source_versions", "documents", "questions", "tasks",
)


def _mock_extractor():
    """mock OCR extractor：返回 SINGLE_LINES 中文行（绕过 PyMuPDF 默认字体无中文字形，
    把中文替换成 U+00B7 的限制）。真实 seal 的中文 PDF 提取依赖 PDF 内嵌字体，不在本测
    试资产范围；TaskExecutor 的 ocr_extractor 是注入点，测试用 mock 确定性中文行。"""

    async def extract(file_bytes: bytes) -> OCRResult:
        return OCRResult(
            provider="mock", model="mock", pages=1,
            lines=tuple(OCRLine(text=t, page_no=1) for t in SINGLE_LINES),
            source_meta={},
        )

    return extract


def _compile_payload_json() -> str:
    """compile 阶段消费的 annotation payload（unit_id/content 形态，test_gate_service 同构）。"""
    return json.dumps(
        {
            "semantic_units": _single_units(),
            "document_metadata_claims": {"subject": "数学", "grade": "三年级"},
        }
    )


class _BoomProvider:
    name = "boom"

    async def complete(self, prompt: str) -> str:
        raise RuntimeError("provider boom")


def _executor(gateway, *, lease_seconds: int | None = None) -> TaskExecutor:
    return TaskExecutor(
        async_session_maker,
        llm_gateway=gateway,
        ocr_extractor=_mock_extractor(),
        lease_seconds=lease_seconds,
    )


async def _enqueue(file_path) -> uuid.UUID:
    async with async_session_maker() as s:
        t = await TaskService(s).enqueue(
            task_type="document_ingest",
            task_params={
                "file_path": str(file_path),
                "file_name": "t.pdf",
                "file_type": "pdf",
                "role": "native",
                "seal_provider": "native",
                "model_config_hash": sha256_hex("mc"),
            },
        )
        await s.commit()
        return t.id


async def _task_status(task_id) -> str:
    async with async_session_maker() as s:
        return (
            await s.execute(text("SELECT status FROM tasks WHERE id=:i"), {"i": task_id})
        ).scalar_one()


async def _claims_row(task_id) -> dict | None:
    async with async_session_maker() as s:
        row = (
            await s.execute(
                text(
                    "SELECT claim_round, outcome, error_type, lease_snapshot "
                    "FROM task_claims WHERE task_id=:i ORDER BY start"
                ),
                {"i": task_id},
            )
        ).mappings().first()
        return dict(row) if row else None


async def _count(model, **where) -> int:
    async with async_session_maker() as s:
        stmt = select(func.count()).select_from(model)
        if where:
            stmt = stmt.where(*[getattr(model, k) == v for k, v in where.items()])
        return (await s.execute(stmt)).scalar()


async def _purge_all() -> None:
    async with async_session_maker() as s:
        for table in _CLEANUP_TABLES:
            await s.execute(text(f"DELETE FROM {table}"))
        await s.commit()


@pytest.fixture(autouse=True)
async def _cleanup():
    # 测试前也清理：防其它测试文件（如 test_task_service 用独立 session commit 不 cleanup）
    # 残留的 queued task 被 next_queued_id 误 claim（本文件依赖「tasks 表无残留 queued」）。
    await _purge_all()
    yield
    await _purge_all()


# ---- 端到端 ----

async def test_run_once_end_to_end_success(tmp_path):
    """seal → annotation → compile 全链路：task succeeded + 1 doc/version/annotation/
    candidate(approved) + 1 Question/Instance（物化）。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue(pdf)

    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_compile_payload_json()))
    assert await _executor(gw).run_once(worker_id="w1") is True

    assert await _task_status(task_id) == "succeeded"
    assert await _count(Document) == 1
    assert await _count(DocumentSourceVersion) == 1
    assert await _count(SemanticAnnotation, status="valid") == 1
    assert await _count(AdmissionCandidate) == 1
    cand = await _load_candidate()
    assert cand.decision_status == "approved"
    assert await _count(Question) == 1
    assert await _count(QuestionInstance) == 1
    row = await _claims_row(task_id)
    assert row is not None and row["outcome"] == "succeeded"


async def _load_candidate() -> AdmissionCandidate:
    async with async_session_maker() as s:
        return (await s.execute(select(AdmissionCandidate))).scalars().first()


# ---- 幂等 replay（Lock-2：命中复用，零新 artifact） ----

async def test_run_once_replay_reuses_artifacts(tmp_path):
    """同 file_path 二次 ingest（等价 replay）：LE 幂等复用（document/version/annotation/
    candidate/instance 全零新增；attempt 复用不落新值，Lock-2）。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task1 = await _enqueue(pdf)

    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_compile_payload_json()))
    ex = _executor(gw)
    assert await ex.run_once(worker_id="w1") is True
    assert await _task_status(task1) == "succeeded"

    # 重新 enqueue 相同 file_path（同 sha256 → 同 LE，等价 replay 重放）
    task2 = await _enqueue(pdf)
    assert await ex.run_once(worker_id="w1") is True
    assert await _task_status(task2) == "succeeded"

    assert await _count(Document) == 1
    assert await _count(DocumentSourceVersion) == 1
    assert await _count(SemanticAnnotation) == 1
    assert await _count(AdmissionCandidate) == 1
    assert await _count(Question) == 1
    assert await _count(QuestionInstance) == 1


# ---- 失败：provider / parse（H8-1 / H8-2） ----

async def test_run_once_provider_failure_task_failed_with_detail(tmp_path):
    """annotation provider 失败 → task failed + task_claims.outcome=failed +
    error_type + error_detail 持久化（H8-1：详情不丢）。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue(pdf)

    gw = LLMGateway("mock", mock_provider=_BoomProvider())
    assert await _executor(gw).run_once(worker_id="w1") is True

    assert await _task_status(task_id) == "failed"
    assert await _count(SemanticAnnotation) == 0  # 失败无 artifact（方案 B）
    row = await _claims_row(task_id)
    assert row is not None
    assert row["outcome"] == "failed"
    assert row["error_type"] == "system_error"  # RuntimeError 非 V3Error/ValueError
    assert "provider boom" in row["lease_snapshot"]["error_detail"]


async def test_run_once_parse_failure_task_failed_validation(tmp_path):
    """parse 失败 → task failed + error_type=validation_error（H8-2 双层：audit 层
    completed / task 层 failed；mock 无 audit 行，以 task error_type 区分）。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue(pdf)

    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider("not valid json {"))
    assert await _executor(gw).run_once(worker_id="w1") is True

    assert await _task_status(task_id) == "failed"
    assert await _count(SemanticAnnotation) == 0
    row = await _claims_row(task_id)
    assert row["outcome"] == "failed"
    assert row["error_type"] == "validation_error"
    assert "not valid JSON" in row["lease_snapshot"]["error_detail"]


# ---- TaskService 终态写 claim（finalize_claim 基础） ----

async def test_complete_writes_claim_outcome_succeeded(session):
    svc = TaskService(session)
    t = await svc.enqueue(task_type="document_ingest", task_params={})
    await session.commit()
    await svc.claim(t.id, worker_id="w", lease_token="tok")
    await session.commit()
    await svc.complete(t.id, worker_id="w", lease_token="tok")
    await session.commit()
    row = await _claims_row(t.id)
    assert row["outcome"] == "succeeded"
    assert row["error_type"] is None


async def test_fail_writes_claim_outcome_and_error_detail(session):
    svc = TaskService(session)
    t = await svc.enqueue(task_type="document_ingest", task_params={})
    await session.commit()
    await svc.claim(t.id, worker_id="w", lease_token="tok")
    await session.commit()
    await svc.fail(
        t.id, worker_id="w", lease_token="tok",
        error_type="validation_error", error_detail="forbidden fields: [x]",
    )
    await session.commit()
    row = await _claims_row(t.id)
    assert row["outcome"] == "failed"
    assert row["error_type"] == "validation_error"
    assert row["lease_snapshot"]["error_detail"] == "forbidden fields: [x]"


async def test_model_config_hash_tracks_actual_provider(tmp_path):
    """Batch 3-4：model_config_hash 编码实际 provider/model（30 §7：不同 provider → 新 LE）。

    未提供显式 model_config_hash 时，由实际 invocation 配置（provider+model）计算，杜绝
    「LE identity 说默认 model、实际用自定义 provider」的漂移。同 file 不同 provider →
    不同 LE → 2 annotation（seal 复用同 document）。
    """
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")

    async def enqueue(provider):
        async with async_session_maker() as s:
            t = await TaskService(s).enqueue(
                task_type="document_ingest",
                task_params={"file_path": str(pdf), "file_name": "t.pdf", "file_type": "pdf",
                             "role": "native", "seal_provider": "native",
                             "llm_provider": provider},  # 不提供 model_config_hash
            )
            await s.commit()
            return t.id

    t1 = await enqueue("provider-a")
    t2 = await enqueue("provider-b")
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_compile_payload_json()))
    ex = _executor(gw)
    assert await ex.run_once(worker_id="w") is True  # 处理 provider-a task
    assert await ex.run_once(worker_id="w") is True  # 处理 provider-b task

    async with async_session_maker() as s:
        n_doc = (await s.execute(text("SELECT count(*) FROM documents"))).scalar()
        n_ann = (await s.execute(text("SELECT count(*) FROM semantic_annotations"))).scalar()
        hashes = (await s.execute(
            text("SELECT logical_execution_hash FROM semantic_annotations ORDER BY logical_execution_hash")
        )).scalars().all()
    assert n_doc == 1, f"同 file 应复用 1 document，实为 {n_doc}"
    assert n_ann == 2, f"不同 provider 应 2 annotation（新 LE），实为 {n_ann}"
    assert len(set(hashes)) == 2, "不同 provider 应不同 LE hash"


# ---- Phase 9-3：Explicit Provider Fallback（BUG-V3-035） ----


class _FailProvider:
    """恒抛指定异常；记录调用次数。"""

    def __init__(self, name: str, exc: Exception) -> None:
        self.name = name
        self._exc = exc
        self.calls = 0

    async def complete(self, prompt: str) -> str:
        self.calls += 1
        raise self._exc


def _live_gateway_with_fallback(providers: dict[str, object]) -> LLMGateway:
    return LLMGateway(
        "live",
        allow_live=True,
        task_context="t",
        budget_ok=True,
        live_providers=providers,
    )


async def _enqueue_fallback(
    file_path, *, llm_provider: str, llm_model: str, llm_fallback: list[dict]
) -> uuid.UUID:
    async with async_session_maker() as s:
        t = await TaskService(s).enqueue(
            task_type="document_ingest",
            task_params={
                "file_path": str(file_path),
                "file_name": "t.pdf",
                "file_type": "pdf",
                "role": "native",
                "seal_provider": "native",
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                "llm_fallback": llm_fallback,
            },
        )
        await s.commit()
        return t.id


async def _audit_providers(task_id) -> list[dict]:
    async with async_session_maker() as s:
        rows = (await s.execute(
            text(
                "SELECT status, provider, model, logical_execution_hash "
                "FROM llm_call_audit WHERE task_id=:i ORDER BY start"
            ),
            {"i": task_id},
        )).mappings().all()
        return [dict(r) for r in rows]


async def _invocations_row(task_id) -> int:
    async with async_session_maker() as s:
        return (await s.execute(
            text("SELECT llm_invocations FROM tasks WHERE id=:i"), {"i": task_id}
        )).scalar_one()


async def test_fallback_disabled_no_fallback(monkeypatch, tmp_path) -> None:
    """BUG-V3-035：provider_fallback_enabled=False（默认）→ 即使 task_params 有 llm_fallback
    也不触发；primary 失败 → task failed；fallback provider 从未被调。"""
    monkeypatch.setattr(settings, "provider_fallback_enabled", False)
    monkeypatch.setattr(settings, "llm_request_retry_count", 0)
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue_fallback(
        pdf, llm_provider="primary", llm_model="p-m",
        llm_fallback=[{"provider": "fallback", "model": "f-m"}],
    )
    primary = _FailProvider("primary", LLMNetworkError("primary down"))
    fb = _FailProvider("fallback", LLMNetworkError("should-not-run"))
    gw = _live_gateway_with_fallback({"primary": primary, "fallback": fb})
    assert await _executor(gw).run_once(worker_id="w") is True

    assert await _task_status(task_id) == "failed"
    assert primary.calls == 1
    assert fb.calls == 0  # disabled：fallback 不触发


async def test_fallback_enabled_new_le_new_invocation_new_audit(monkeypatch, tmp_path) -> None:
    """BUG-V3-035 核心：primary retryable 失败 + retry 耗尽 + enabled + 显式 fallback →
    fallback 成功；X≠Y LE（2 个不同 logical_execution_hash）+ Invocation=2 + Audit=2
    （1 failed + 1 completed）+ budget used=1（fallback 独立 settle）。"""
    monkeypatch.setattr(settings, "provider_fallback_enabled", True)
    monkeypatch.setattr(settings, "llm_request_retry_count", 0)
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue_fallback(
        pdf, llm_provider="primary", llm_model="p-m",
        llm_fallback=[{"provider": "fallback", "model": "f-m"}],
    )
    primary = _FailProvider("primary", LLMNetworkError("primary down"))
    fb = _FixedJSONProvider(_compile_payload_json())  # fallback 成功返回 valid JSON
    fb.name = "fallback"
    gw = _live_gateway_with_fallback({"primary": primary, "fallback": fb})
    assert await _executor(gw).run_once(worker_id="w") is True

    assert await _task_status(task_id) == "succeeded"
    assert primary.calls == 1
    assert (await _invocations_row(task_id)) == 2  # primary + fallback 各 1 invocation
    audits = await _audit_providers(task_id)
    assert [a["status"] for a in audits] == ["failed", "completed"]
    assert {a["provider"] for a in audits} == {"primary", "fallback"}
    # X≠Y：primary LE ≠ fallback LE（fallback 用实际 config 算新 model_config_hash → 新 LE）
    assert len({a["logical_execution_hash"] for a in audits}) == 2
    async with async_session_maker() as s:
        row = (await s.execute(
            text("SELECT used, reserved FROM budget WHERE account_dim='task' AND scope_id=:i"),
            {"i": str(task_id)},
        )).mappings().first()
    assert row["used"] == 1  # fallback 成功 settle；primary 失败已 release
    assert row["reserved"] == 0


async def test_fallback_not_triggered_on_non_retryable(monkeypatch, tmp_path) -> None:
    """BUG-V3-035：primary 抛 LLMProviderError(retryable=False)（4xx 明确拒绝）→ 不 fallback，
    即使 enabled + 有显式 fallback；task failed；fallback 未被调。"""
    monkeypatch.setattr(settings, "provider_fallback_enabled", True)
    monkeypatch.setattr(settings, "llm_request_retry_count", 0)
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue_fallback(
        pdf, llm_provider="primary", llm_model="p-m",
        llm_fallback=[{"provider": "fallback", "model": "f-m"}],
    )
    primary = _FailProvider("primary", LLMProviderError("HTTP 400", retryable=False))
    fb = _FailProvider("fallback", LLMNetworkError("should-not-run"))
    gw = _live_gateway_with_fallback({"primary": primary, "fallback": fb})
    assert await _executor(gw).run_once(worker_id="w") is True

    assert await _task_status(task_id) == "failed"
    assert primary.calls == 1
    assert fb.calls == 0  # 非 transient 不 fallback


async def test_fallback_all_exhausted_task_failed(monkeypatch, tmp_path) -> None:
    """BUG-V3-035：primary + fallback 全部 retryable 失败 → 依次尝试，最终 task failed；
    fallback provider 被调（但失败）。"""
    monkeypatch.setattr(settings, "provider_fallback_enabled", True)
    monkeypatch.setattr(settings, "llm_request_retry_count", 0)
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue_fallback(
        pdf, llm_provider="primary", llm_model="p-m",
        llm_fallback=[{"provider": "fallback", "model": "f-m"}],
    )
    primary = _FailProvider("primary", LLMNetworkError("primary down"))
    fb = _FailProvider("fallback", LLMNetworkError("fallback down"))
    gw = _live_gateway_with_fallback({"primary": primary, "fallback": fb})
    assert await _executor(gw).run_once(worker_id="w") is True

    assert await _task_status(task_id) == "failed"
    assert primary.calls == 1
    assert fb.calls == 1  # fallback 被尝试但失败


async def test_fallback_skips_primary_self_and_cycles(monkeypatch, tmp_path) -> None:
    """BUG-V3-035：llm_fallback 含 primary 自己 / 循环项 → 去重跳过，不无限 fallback 到
    primary 自己。primary 失败 → 仅去重后的 fallback 被尝试一次。"""
    monkeypatch.setattr(settings, "provider_fallback_enabled", True)
    monkeypatch.setattr(settings, "llm_request_retry_count", 0)
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue_fallback(
        pdf, llm_provider="primary", llm_model="p-m",
        llm_fallback=[
            {"provider": "primary", "model": "p-m"},  # 回 primary 自己 → 跳过
            {"provider": "fallback", "model": "f-m"},
            {"provider": "fallback", "model": "f-m"},  # 重复 → 跳过
        ],
    )
    primary = _FailProvider("primary", LLMNetworkError("primary down"))
    fb = _FailProvider("fallback", LLMNetworkError("fallback down"))
    gw = _live_gateway_with_fallback({"primary": primary, "fallback": fb})
    assert await _executor(gw).run_once(worker_id="w") is True

    assert await _task_status(task_id) == "failed"
    assert primary.calls == 1  # 只调一次（不因 fallback 回 primary 自己而二次调用）
    assert fb.calls == 1  # 去重后 fallback 只尝试一次


async def test_fallback_not_triggered_on_cancellation(monkeypatch, tmp_path) -> None:
    """BUG-V3-035：primary 抛 CancelledError（BaseException 非 Exception）→ 不 fallback、
    不被吞；直接传播出 run_once（进程取消信号）。fallback 未被调。"""
    monkeypatch.setattr(settings, "provider_fallback_enabled", True)
    monkeypatch.setattr(settings, "llm_request_retry_count", 0)
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue_fallback(
        pdf, llm_provider="primary", llm_model="p-m",
        llm_fallback=[{"provider": "fallback", "model": "f-m"}],
    )
    primary = _FailProvider("primary", asyncio.CancelledError())
    fb = _FailProvider("fallback", LLMNetworkError("should-not-run"))
    gw = _live_gateway_with_fallback({"primary": primary, "fallback": fb})

    # run_once 的 except Exception 不捕获 BaseException → CancelledError 直接传播
    with pytest.raises(asyncio.CancelledError):
        await _executor(gw).run_once(worker_id="w")

    assert primary.calls == 1
    assert fb.calls == 0  # 取消不 fallback


# ---- BUG-V3-037：Annotation 阶段持续 Heartbeat（lease 不因慢 LLM 调用过期） ----


class _SlowProvider:
    """sleep > lease 后返回 valid JSON，模拟真实慢 LLM cold-load。"""

    name = "slow"

    def __init__(self, delay: float, payload: str) -> None:
        self._delay = delay
        self._payload = payload

    async def complete(self, prompt: str) -> str:
        await asyncio.sleep(self._delay)
        return self._payload


class _GateProvider:
    """卡在 LLM 调用中直到 release，供测试在调用期间模拟 recover 接管。"""

    name = "gate"

    def __init__(self, started: asyncio.Event, release: asyncio.Event) -> None:
        self._started = started
        self._release = release

    async def complete(self, prompt: str) -> str:
        self._started.set()
        await self._release.wait()
        return _compile_payload_json()


class _SlowBoomProvider:
    """sleep 后抛异常：验证 LLM 异常时 heartbeat 循环已 tick 过再随 finally 清理。"""

    name = "slow-boom"

    async def complete(self, prompt: str) -> str:
        await asyncio.sleep(0.6)
        raise RuntimeError("provider boom after delay")


class _CancelProvider:
    """抛 CancelledError（BaseException）：验证取消路径 heartbeat 循环不残留。"""

    name = "cancel"

    async def complete(self, prompt: str) -> str:
        raise asyncio.CancelledError()


async def test_long_annotation_keeps_lease_alive(tmp_path):
    """BUG-V3-037 核心回归锁：annotation 慢（2.5s）> lease（1s），持续 heartbeat 保持
    lease 存活 → task succeeded。无此修复时 lease 在 1s 过期、边界 _heartbeat 抛
    LeaseConflict、task 卡 running。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue(pdf)

    gw = LLMGateway("mock", mock_provider=_SlowProvider(2.5, _compile_payload_json()))
    assert await _executor(gw, lease_seconds=1).run_once(worker_id="w1") is True

    assert await _task_status(task_id) == "succeeded"
    assert await _count(SemanticAnnotation, status="valid") == 1
    cand = await _load_candidate()
    assert cand.decision_status == "approved"
    assert await _count(Question) == 1


async def test_heartbeat_lease_loss_no_silent_success(tmp_path):
    """BUG-V3-037（R5 情况 B，ownership fencing）：annotation 期间 task 被 recover 接管
    （status→interrupted）→ executor 绝不写 succeeded，终态精确 = interrupted。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue(pdf)

    started = asyncio.Event()
    release = asyncio.Event()
    gw = LLMGateway("mock", mock_provider=_GateProvider(started, release))
    ex = _executor(gw, lease_seconds=1)

    run_task = asyncio.create_task(ex.run_once(worker_id="w1"))
    await started.wait()  # LLM 调用已开始（annotation stage 内，lease 已 claim）

    # 模拟 recover 接管：直接置 interrupted + lease 过期（等价 recover_expired）
    async with async_session_maker() as s:
        await s.execute(
            text(
                "UPDATE tasks SET status='interrupted', lease_expires_at=now(), "
                "heartbeat_at=now() WHERE id=:i"
            ),
            {"i": task_id},
        )
        await s.commit()

    release.set()
    assert await run_task is True

    assert await _task_status(task_id) == "interrupted"


async def test_heartbeat_stops_on_llm_error(tmp_path):
    """BUG-V3-037：慢 LLM 调用内抛异常 → 既有失败语义不变（task failed、0 artifact、
    error_type=system_error），且 heartbeat 循环已 tick 过并随 finally 清理。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue(pdf)

    gw = LLMGateway("mock", mock_provider=_SlowBoomProvider())
    assert await _executor(gw, lease_seconds=1).run_once(worker_id="w1") is True

    assert await _task_status(task_id) == "failed"
    assert await _count(SemanticAnnotation) == 0
    row = await _claims_row(task_id)
    assert row["outcome"] == "failed"
    assert row["error_type"] == "system_error"


async def test_heartbeat_cleanup_on_cancellation(tmp_path):
    """BUG-V3-037（R2）：annotation 抛 CancelledError → 直接传播（进程取消信号，非业务
    fail），heartbeat 循环在 finally 清理、不残留。"""
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"test pdf bytes")
    task_id = await _enqueue(pdf)

    gw = LLMGateway("mock", mock_provider=_CancelProvider())
    with pytest.raises(asyncio.CancelledError):
        await _executor(gw, lease_seconds=1).run_once(worker_id="w1")


async def test_lease_heartbeat_loop_cleaned_up():
    """BUG-V3-037（R2 无 orphan）：_lease_heartbeat context 退出后 renew loop 已 done
    （finally 已在正常生命周期内 cancel + await，非等 event-loop teardown 顺带取消）。"""
    async with async_session_maker() as s:
        t = await TaskService(s).enqueue(task_type="document_ingest", task_params={})
        await s.commit()
        await TaskService(s, lease_seconds=1).claim(
            t.id, worker_id="w1", lease_token="tok1"
        )
        await s.commit()

    ex = _executor(LLMGateway("mock"), lease_seconds=1)
    async with ex._lease_heartbeat(t.id, "w1", "tok1") as loop:
        assert not loop.done()
        await asyncio.sleep(0.6)  # 让 loop 至少 tick 一次
    assert loop.done()  # 无 orphan：finally 已 cancel + await
