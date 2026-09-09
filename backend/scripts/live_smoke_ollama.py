"""I-1-D — Ollama Live Smoke Harness（不进 pytest；runtime/model/env-dependent）。

证明：真实 Ollama Provider 在既有 Live Policy 下驱动完整 V3 Runtime 链路，并在 PostgreSQL
留下可验证的 Task / Attempt / Audit / Budget / Artifact provenance。显式记录 provider/model/
live；显式构造 live gateway（task_context/budget_ok），不 monkeypatch / 不 fake allow /
不绕过 _live() 放行规则。

用法（env 在 import 前由 shell 注入，Settings 读 .env + env）：
    LLM_GATEWAY_MODE=live \
    OLLAMA_BASE_URL=http://localhost:11434/v1 \
    OLLAMA_MODEL=qwen3.5:4b \
    LLM_REQUEST_TIMEOUT_SECONDS=300 \
    DATABASE_URL=postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors \
    python scripts/live_smoke_ollama.py [--pdf <path>]

缺省生成 ASCII 单选 PDF（PyMuPDF 文本层，Native OCR 可靠提取）；真实中文 PDF 用 --pdf 指入。
"""

import argparse
import asyncio
import os
import sys
import uuid

os.environ.setdefault("APP_ENV", "smoke")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors"
)

from sqlalchemy import func, select, text

from app.ai.gateway import build_gateway
from app.ai.ocr.providers import NativeTextProvider
from app.core.config import settings
from app.db.session import async_session_maker
from app.domains.task.executor import TaskExecutor
from app.domains.task.service import TaskService
from app.models.content import Question, QuestionInstance
from app.models.snapshot import AdmissionCandidate, SemanticAnnotation
from app.models.source import Document, DocumentSourceVersion

_CLEANUP_TABLES = (
    "admission_events", "instance_role_contents", "material_links",
    "unit_group_members", "question_instances", "unit_groups", "materials",
    "admission_candidates", "semantic_annotations", "document_source_lines",
    "task_claims", "document_source_versions", "documents", "questions", "tasks",
)

_SMOKE_LINES = (
    "1. Which of the following is a fruit?",
    "A. Apple",
    "B. Banana",
    "C. Car",
    "D. Desk",
    "【答案】",
    "1. A",
    # Smoke harness correction（独立于 BUG-V3-038）：模型声明 explanation role 时，
    # fixture 须提供对应 source evidence（【详解】区），否则 Resolver fail-loud 判
    # missing → IR incomplete（行为正确，非生产 bug）。
    "【详解】",
    "1. Apple is a fruit.",
)


def _make_pdf(path: str) -> None:
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    for i, line in enumerate(_SMOKE_LINES):
        # china-s：PyMuPDF 内置简体中文 CID 字体——【答案】须可渲染且文本层可提取
        # （frozen is_answer_header 只认中文表头，BUG-V3-031）。
        page.insert_text((72, 72 + i * 18), line, fontname="china-s")
    doc.save(path)
    doc.close()


async def _purge_all() -> None:
    async with async_session_maker() as s:
        for table in _CLEANUP_TABLES:
            await s.execute(text(f"DELETE FROM {table}"))
        await s.commit()


async def _count(model, **where) -> int:
    async with async_session_maker() as s:
        stmt = select(func.count()).select_from(model)
        if where:
            stmt = stmt.where(*[getattr(model, k) == v for k, v in where.items()])
        return (await s.execute(stmt)).scalar()


async def _scalar(sql: str, params: dict):
    async with async_session_maker() as s:
        return (await s.execute(text(sql), params)).scalar()


async def _enqueue(file_path: str) -> uuid.UUID:
    async with async_session_maker() as s:
        t = await TaskService(s).enqueue(
            task_type="document_ingest",
            task_params={
                "file_path": file_path,
                "file_name": "smoke.pdf",
                "file_type": "pdf",
                "role": "native",
                "seal_provider": "native",
                "llm_provider": "ollama",
                "llm_model": settings.ollama_model,  # 对齐 HTTPLLMProvider 实际 model（防 audit 漂移）
            },
        )
        await s.commit()
        return t.id


async def main(pdf: str | None) -> int:
    # ---- 前置配置校验（fail-fast，非 monkeypatch/fake） ----
    if settings.llm_gateway_mode != "live":
        print(f"[FAIL] LLM_GATEWAY_MODE={settings.llm_gateway_mode!r}，须为 live")
        return 1
    if not settings.ollama_base_url or not settings.ollama_model:
        print("[FAIL] OLLAMA_BASE_URL / OLLAMA_MODEL 未配置（见 docstring 用法）")
        return 1

    print("=== I-1-D Ollama Live Smoke ===")
    print(f"provider = ollama")
    print(f"model = {settings.ollama_model}")
    print(f"live = true")
    print(f"base_url = {settings.ollama_base_url}")
    print(f"timeout = {settings.llm_request_timeout_seconds}s")

    pdf_path = pdf or os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke.pdf")
    if not pdf:
        _make_pdf(pdf_path)
    print(f"document = {pdf_path}")

    # 显式构造 live gateway（走真实 _live() 放行，非绕过）
    gateway = build_gateway(allow_live=True, task_context="smoke", budget_ok=True)
    executor = TaskExecutor(
        async_session_maker,
        llm_gateway=gateway,
        ocr_extractor=NativeTextProvider().extract,
    )

    await _purge_all()
    task_id = await _enqueue(pdf_path)
    assert await executor.run_once(worker_id="smoke-w1") is True, "run_once 未 claim 到 task"

    # ---- Hard Gate 12 层 ----
    results: list[tuple[str, bool, str]] = []

    status = await _scalar("SELECT status FROM tasks WHERE id=:i", {"i": task_id})
    results.append(("Task succeeded", status == "succeeded", f"status={status}"))

    results.append(("Document persisted", await _count(Document) == 1, f"documents={await _count(Document)}"))
    results.append(("SourceVersion persisted", await _count(DocumentSourceVersion) == 1, f"versions={await _count(DocumentSourceVersion)}"))

    n_ann = await _count(SemanticAnnotation, status="valid")
    results.append(("Annotation valid", n_ann == 1, f"valid_annotations={n_ann}"))

    async with async_session_maker() as s:
        cand = (await s.execute(select(AdmissionCandidate))).scalars().first()
    results.append(("Candidate produced", cand is not None, f"candidate={'yes' if cand else 'no'}"))
    results.append(("Gate decision present", cand is not None and cand.decision_status is not None,
                    f"decision={cand.decision_status if cand else None}"))

    n_q = await _count(Question)
    n_i = await _count(QuestionInstance)
    results.append(("Question produced", n_q >= 1, f"questions={n_q}"))
    results.append(("Instance produced", n_i >= 1, f"instances={n_i}"))

    outcome = await _scalar("SELECT outcome FROM task_claims WHERE task_id=:i ORDER BY start LIMIT 1", {"i": task_id})
    results.append(("DB terminal state (claim outcome)", outcome == "succeeded", f"outcome={outcome}"))

    async with async_session_maker() as s:
        audits = (await s.execute(
            text("SELECT provider, model, status FROM llm_call_audit WHERE task_id=:i ORDER BY start"),
            {"i": task_id},
        )).mappings().all()
    prov_ok = len(audits) >= 1 and all(a["provider"] == "ollama" for a in audits)
    results.append(("Audit provider=ollama", prov_ok, f"audits={[dict(a) for a in audits]}"))

    async with async_session_maker() as s:
        b = (await s.execute(
            text("SELECT used, reserved FROM budget WHERE account_dim='task' AND scope_id=:i"),
            {"i": str(task_id)},
        )).mappings().first()
    results.append(("Budget settled", b is not None and b["used"] >= 1 and b["reserved"] == 0,
                    f"budget={dict(b) if b else None}"))

    # replay：同 file 二次 ingest → LE 幂等复用，零新增 artifact
    task2 = await _enqueue(pdf_path)
    assert await executor.run_once(worker_id="smoke-w1") is True
    results.append(("Replay zero duplicate", await _count(Document) == 1 and await _count(SemanticAnnotation) == 1,
                    f"docs={await _count(Document)}, anns={await _count(SemanticAnnotation)}"))

    # ---- 汇总 ----
    print("--- Hard Gate 结果 ---")
    all_ok = True
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        all_ok = all_ok and ok

    await _purge_all()
    print("=== " + ("SMOKE PASS" if all_ok else "SMOKE FAIL") + " ===")
    return 0 if all_ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python scripts/live_smoke_ollama.py")
    parser.add_argument("--pdf", help="真实 PDF 路径（缺省生成 ASCII 单选 PDF）")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.pdf)))
