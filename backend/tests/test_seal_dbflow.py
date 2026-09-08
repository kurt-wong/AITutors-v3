"""Gate B1/B2(DB)/B3/B4/B7 — seal 全链路真实 DB（沿用段 A dbflow 模式 + 可重入）。

每测试用独立 session（conftest yield→rollback）：同文件 seal 幂等在单一事务内验证
（flush 可见），测试结束回滚 → 不污染 documents/source_versions（段 C 可重入教训）。
"""

import hashlib

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.ai.ocr.gateway import OCRGateway
from app.ai.ocr.providers import MockOCRProvider, NativeTextProvider
from app.ai.ocr.result import OCRLine, OCRResult
from app.domains.source.line_index import compute_body_hash
from app.domains.source.seal import SealService
from app.models.runtime import Budget, LlmCallAudit
from app.models.source import Document, DocumentSourceLine, DocumentSourceVersion
from app.repositories.base import AppendOnlyViolation, SealedVersionError
from app.repositories.source_repository import SourceRepository


async def _seal(session, pdf_bytes: bytes, role: str = "native", provider: str = "native"):
    return await SealService(session).seal_document(
        file_bytes=pdf_bytes,
        file_name="sample.pdf",
        file_type="pdf",
        role=role,
        provider=provider,
        extractor=NativeTextProvider().extract,
    )


async def test_b1_seal_idempotent_single_doc_single_version(session, pdf_bytes):
    v1 = await _seal(session, pdf_bytes)
    await session.flush()
    v1_id = v1.id
    assert v1.status == "sealed"

    v2 = await _seal(session, pdf_bytes)  # 同文件 + 同 role/provider/contract → 既有行
    await session.flush()
    assert v2.id == v1_id

    n_docs = (await session.execute(select(func.count()).select_from(Document))).scalar()
    n_vers = (
        await session.execute(select(func.count()).select_from(DocumentSourceVersion))
    ).scalar()
    assert n_docs == 1
    assert n_vers == 1


async def test_b2_line_ref_db_unique_constraint(session, pdf_bytes):
    v = await _seal(session, pdf_bytes)
    await session.flush()
    dup = DocumentSourceLine(
        source_version_id=v.id,
        line_ref="P1L001",  # 与既有第一行重复
        seq=999,
        page_no=1,
        line_no_in_page=999,
        text="dup",
        block_type="text",
        bbox=None,
        raw_sources={"provider": "native"},
        selected_source="native",
        evidence="x",
        line_hash="h" * 64,
    )
    await SourceRepository(session).append_line(dup)
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_b3_sealed_version_immutable_and_append_only(session, pdf_bytes):
    v = await _seal(session, pdf_bytes)
    await session.flush()
    repo = SourceRepository(session)
    with pytest.raises(SealedVersionError):
        await repo.update_version(v.id, body_text="tampered")
    with pytest.raises(AppendOnlyViolation):
        await repo.update_line()
    with pytest.raises(AppendOnlyViolation):
        await repo.update_figure()


async def test_b4_body_rebuild_from_db_matches_hash(session, pdf_bytes):
    v = await _seal(session, pdf_bytes)
    await session.flush()
    res = await session.execute(
        select(DocumentSourceLine)
        .where(DocumentSourceLine.source_version_id == v.id)
        .order_by(DocumentSourceLine.seq)
    )
    db_lines = res.scalars().all()
    rebuilt = "\n".join(l.text for l in db_lines)
    stored = v.body_text
    assert rebuilt == stored  # IS-4：line index 按 seq 可确定性重建 body
    assert compute_body_hash(rebuilt) == v.body_hash  # 重建 hash 匹配落库


async def test_b7_native_seal_zero_audit_budget(session, pdf_bytes):
    """native 本地确定性 seal：零 audit/budget 消耗（deterministic local ≠ external）。

    budget/audit 表可能含既有残留（如段 C budget 测试的 commit 账户行），故用
    seal 前后计数不变断言「不新增」，而非全表为 0。
    """
    audit_before = (await session.execute(select(func.count()).select_from(LlmCallAudit))).scalar()
    budget_before = (await session.execute(select(func.count()).select_from(Budget))).scalar()

    v = await _seal(session, pdf_bytes)
    await session.flush()
    assert v.status == "sealed"
    doc = await session.get(Document, v.document_id)
    assert doc.processing_status == "sealed"

    audit_after = (await session.execute(select(func.count()).select_from(LlmCallAudit))).scalar()
    budget_after = (await session.execute(select(func.count()).select_from(Budget))).scalar()
    assert audit_after == audit_before
    assert budget_after == budget_before
    # seal LE 幂等身份已落 provenance（10 §3 (stage, hash)）
    assert v.logical_execution_stage == "seal"
    assert v.logical_execution_hash is not None


async def test_cloud_path_goes_through_gateway_mock(session, pdf_bytes):
    """SealService cloud 路径经 OCRGateway（mock）→ 确定性 seal；不经 CloudOCRProvider 直调。"""
    mock_result = OCRResult(
        provider="paddleocr-vl",
        model="PaddleOCR-VL-1.6",
        pages=1,
        lines=(OCRLine("mock cloud line 1", 1), OCRLine("mock cloud line 2", 1)),
    )
    gw = OCRGateway("mock", mock_provider=MockOCRProvider(mock_result))
    v = await SealService(session).seal_document(
        file_bytes=pdf_bytes,
        file_name="cloud.pdf",
        file_type="pdf",
        role="ocr_ppsvl",
        provider="paddleocr-vl",
        extractor=gw.extract,
    )
    await session.flush()
    assert v.status == "sealed"
    assert v.provider == "paddleocr-vl"
    assert v.line_count == 2
    assert v.logical_execution_hash is not None
    # 同文件不同 role/provider/contract → 不同 LE（BUG-V3-007 未冻结区，不覆写既有 native version）
    assert hashlib.sha256(pdf_bytes).hexdigest()  # 同一文件本体复用 document
    n_docs = (await session.execute(select(func.count()).select_from(Document))).scalar()
    assert n_docs == 1


async def test_b1_cross_transaction_idempotency(session, pdf_bytes):
    """B1 跨事务强化：commit 后新事务同文件 seal → 仍恰 1 sealed version（非仅同事务）。"""
    from sqlalchemy import text

    from app.db.session import async_session_maker

    sha = hashlib.sha256(pdf_bytes).hexdigest()
    async with async_session_maker() as s1:
        v1 = await _seal(s1, pdf_bytes)
        await s1.flush()
        await s1.commit()
        vid = v1.id
    try:
        async with async_session_maker() as s2:
            v2 = await _seal(s2, pdf_bytes)  # 新事务，DB 已持久化
            await s2.flush()
            assert v2.id == vid
            n = (
                await s2.execute(select(func.count()).select_from(DocumentSourceVersion))
            ).scalar()
            assert n == 1
    finally:
        async with async_session_maker() as sc:
            vids = (
                await sc.execute(
                    text(
                        "SELECT v.id FROM document_source_versions v JOIN documents d "
                        "ON d.id=v.document_id WHERE d.original_sha256=:s"
                    ),
                    {"s": sha},
                )
            ).scalars().all()
            for rid in vids:
                await sc.execute(
                    text("DELETE FROM document_source_lines WHERE source_version_id=:x"),
                    {"x": rid},
                )
                await sc.execute(
                    text("DELETE FROM document_source_versions WHERE id=:x"), {"x": rid}
                )
            await sc.execute(text("DELETE FROM documents WHERE original_sha256=:s"), {"s": sha})
            await sc.commit()


class _BoomProvider:
    name = "boom"

    async def extract(self, file_bytes: bytes):
        raise RuntimeError("boom")


async def test_extract_failure_marks_document_failed(session, pdf_bytes):
    """extractor 抛错 → document.processing_status='failed'（seal except 分支，防静默残留）。"""
    svc = SealService(session)
    with pytest.raises(RuntimeError):
        await svc.seal_document(
            file_bytes=pdf_bytes,
            file_name="boom.pdf",
            file_type="pdf",
            role="native",
            provider="native",
            extractor=_BoomProvider().extract,
        )
    await session.flush()
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    doc = (
        await session.execute(select(Document).where(Document.original_sha256 == sha))
    ).scalar_one_or_none()
    assert doc is not None
    assert doc.processing_status == "failed"


async def test_seal_integrity_recomputable_from_db(session, pdf_bytes):
    """integrity 完整性：seal 后从 DB lines 读回复算 line_hashes/body/integrity == 存储值。"""
    from app.domains.source.line_index import (
        compute_body_hash,
        compute_integrity_hash,
        compute_line_hash,
    )

    v = await _seal(session, pdf_bytes)
    await session.flush()
    rows = (
        await session.execute(
            select(DocumentSourceLine)
            .where(DocumentSourceLine.source_version_id == v.id)
            .order_by(DocumentSourceLine.seq)
        )
    ).scalars().all()
    body = "\n".join(r.text for r in rows)
    line_hashes = [
        compute_line_hash(
            text=r.text,
            raw_sources=r.raw_sources,
            selected_source=r.selected_source,
            evidence=r.evidence,
        )
        for r in rows
    ]
    ih = compute_integrity_hash(
        body_hash=compute_body_hash(body),
        line_hashes=line_hashes,
        figure_hashes=[],
        provenance={"role": v.role, "provider": v.provider, "artifact_kind": v.artifact_kind},
    )
    assert ih == v.integrity_hash
    for r in rows:
        assert r.line_hash == compute_line_hash(
            text=r.text,
            raw_sources=r.raw_sources,
            selected_source=r.selected_source,
            evidence=r.evidence,
        )
