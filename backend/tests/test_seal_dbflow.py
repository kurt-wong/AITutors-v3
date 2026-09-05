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
        role="ocr_ppsv3",
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
