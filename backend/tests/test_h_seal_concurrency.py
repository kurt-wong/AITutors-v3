"""H-1（BUG-V3-029/007）seal 并发幂等（真实 PostgreSQL 真并发）。

BUG-V3-007 终裁：documents.UNIQUE(original_sha256) + document_source_versions.UNIQUE(stage,hash)
= 并发 seal 同 file 同 role/provider 收敛到恰 1 Document + 1 sealed Version（winner/loser 同
canonical identity），不再产生重复行（修复前真 DB 探针 FAIL：2 document）。
"""

import asyncio

import pytest
from sqlalchemy import text

from app.ai.ocr.result import OCRLine, OCRResult
from app.db.session import async_session_maker
from app.domains.source.seal import SealService

_FILE = b"same-pdf-content"
_CLEANUP = (
    "document_source_lines", "document_source_versions", "documents",
)


def _mock_extractor():
    async def extract(file_bytes):
        return OCRResult(
            provider="native", model="pymupdf", pages=1,
            lines=tuple(OCRLine(text=t, page_no=1) for t in ("1. 题干", "A. 甲")),
            source_meta={},
        )
    return extract


async def _seal():
    async with async_session_maker() as s:
        v = await SealService(s).seal_document(
            file_bytes=_FILE, file_name="x.pdf", file_type="pdf",
            role="native", provider="native", extractor=_mock_extractor(),
        )
        await s.commit()
        return v.id


@pytest.fixture(autouse=True)
async def _cleanup():
    yield
    async with async_session_maker() as s:
        for t in _CLEANUP:
            await s.execute(text(f"DELETE FROM {t}"))
        await s.commit()


async def test_concurrent_seal_single_document_version():
    ids = await asyncio.gather(_seal(), _seal())
    assert len(set(ids)) == 1, f"并发 seal 应收敛到同一 version，实为 {ids}"
    async with async_session_maker() as s:
        n_doc = (await s.execute(text("SELECT count(*) FROM documents"))).scalar()
        n_ver = (await s.execute(text("SELECT count(*) FROM document_source_versions"))).scalar()
        n_lines = (await s.execute(text("SELECT count(*) FROM document_source_lines"))).scalar()
    assert n_doc == 1, f"并发 seal 应恰 1 document，实为 {n_doc}"
    assert n_ver == 1, f"并发 seal 应恰 1 version，实为 {n_ver}"
    assert n_lines == 2, f"并发 seal 应恰 2 line（无重复 append），实为 {n_lines}"


async def test_cross_role_multiple_versions_allowed():
    """BUG-V3-007：同 original_sha256 跨 role/provider 允许多 version（非 duplicate）。"""
    async def seal_role(role: str, provider: str):
        async with async_session_maker() as s:
            v = await SealService(s).seal_document(
                file_bytes=_FILE, file_name="x.pdf", file_type="pdf",
                role=role, provider=provider, extractor=_mock_extractor(),
            )
            await s.commit()
            return v.id

    native_id = await seal_role("native", "native")
    cloud_id = await seal_role("ocr_ppsv3", "ppsv3")
    assert native_id != cloud_id, "跨 role/provider 应产生不同 version"
    async with async_session_maker() as s:
        n_doc = (await s.execute(text("SELECT count(*) FROM documents"))).scalar()
        n_ver = (await s.execute(text("SELECT count(*) FROM document_source_versions"))).scalar()
    assert n_doc == 1, f"同 original_sha256 应恰 1 document，实为 {n_doc}"
    assert n_ver == 2, f"跨 role/provider 应 2 version，实为 {n_ver}"
