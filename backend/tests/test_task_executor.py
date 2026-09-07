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
import uuid

import pytest
from sqlalchemy import func, select, text

from app.ai.gateway import LLMGateway
from app.ai.ocr.result import OCRLine, OCRResult
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


def _executor(gateway) -> TaskExecutor:
    return TaskExecutor(
        async_session_maker,
        llm_gateway=gateway,
        ocr_extractor=_mock_extractor(),
    )


async def _enqueue(file_path) -> uuid.UUID:
    async with async_session_maker() as s:
        t = await TaskService(s).enqueue(
            task_type="document_ingest",
            task_params={
                "file_path": str(file_path),
                "file_name": "t.pdf",
                "file_type": "pdf",
                "role": "main",
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
