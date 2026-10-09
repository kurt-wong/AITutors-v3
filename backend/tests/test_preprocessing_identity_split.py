"""Positive path: formal preprocessing import creates split identities.

Proves on a real DB:
- documents.original_sha256 == SHA256(original PDF bytes)
- source_meta.source_content_sha256 == SHA256(markdown bytes)
- the two hashes are DIFFERENT objects
- role/provider = preprocessing/preprocessing
- never written as original_sha256 = markdown hash
"""

from __future__ import annotations

import hashlib

import pytest

from app.ai.ocr.preprocessing_provider import PreprocessingTextExtractor
from app.domains.source.preprocessing_import import (
    PreprocessingImportService,
    PreprocessingPackage,
)
from app.domains.source.seal import SealService


MD_BODY = "# 练习卷\n\n1. 下列正确的是\nA. 甲\nB. 乙\n\n答案：A\n"
PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.mark.asyncio
async def test_import_package_splits_identities(session):
    md = MD_BODY.encode("utf-8")
    manifest = {"source_content_sha256": hashlib.sha256(md).hexdigest(), "identity_version": "v1"}
    package = PreprocessingPackage(
        original_bytes=PDF_BYTES,
        original_name="exam.pdf",
        source_md=md,
        manifest=manifest,
    )
    svc = PreprocessingImportService(session)
    result = await svc.import_package(package=package, created_by="test")
    await session.commit()

    pdf_sha = hashlib.sha256(PDF_BYTES).hexdigest()
    md_sha = hashlib.sha256(md).hexdigest()

    assert result.original_sha256 == pdf_sha
    assert result.source_content_sha256 == md_sha
    assert result.original_sha256 != result.source_content_sha256

    doc = result.document
    assert doc.original_sha256 == pdf_sha, "original_sha256 must be PDF identity"
    assert doc.upload_meta.get("source_mode") == "preprocessing"
    assert doc.upload_meta.get("source_content_sha256") == md_sha

    from app.models.source import DocumentSourceVersion

    sv = await session.get(DocumentSourceVersion, result.source_version_id)
    assert sv is not None
    assert sv.role == "preprocessing"
    assert sv.provider == "preprocessing"
    assert sv.body_text is not None
    assert "练习卷" in sv.body_text or "下" in sv.body_text
    assert sv.source_meta.get("source_content_sha256") == md_sha
    # Critical: markdown hash must NOT be stored as document identity
    assert doc.original_sha256 != md_sha


@pytest.mark.asyncio
async def test_preprocessing_extractor_rejects_native_substitution(session):
    """If MD is missing, no silent native fallback is available."""
    from app.domains.task.executor import TaskExecutor

    class DummyExecutor(TaskExecutor):
        def __init__(self):
            pass

    ex = DummyExecutor()
    with pytest.raises(Exception) as ei:
        await ex._build_preprocessing_extractor({"source_mode": "preprocessing"})
    assert "source_md_path" in str(ei.value)


@pytest.mark.asyncio
async def test_seal_is_idempotent_on_second_pass(session):
    md = MD_BODY.encode("utf-8")
    extractor = PreprocessingTextExtractor(md)
    seal = SealService(session)
    v1 = await seal.seal_document(
        file_bytes=PDF_BYTES,
        file_name="exam2.pdf",
        file_type="pdf",
        role="preprocessing",
        provider="preprocessing",
        extractor=extractor.extract,
    )
    await session.commit()
    v2 = await seal.seal_document(
        file_bytes=PDF_BYTES,
        file_name="exam2.pdf",
        file_type="pdf",
        role="preprocessing",
        provider="preprocessing",
        extractor=extractor.extract,
    )
    await session.commit()
    assert v1.id == v2.id
