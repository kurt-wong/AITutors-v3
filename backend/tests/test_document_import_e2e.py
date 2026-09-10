"""Phase I-2A Import Boundary E2E 测试。

验证：upload PDF → document exists → task exists → API 可查询状态。
"""

import hashlib

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def sample_pdf() -> bytes:
    """PyMuPDF 生成的最小 PDF。"""
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Test question for import boundary")
    data = doc.tobytes()
    doc.close()
    return data


@pytest.mark.asyncio
async def test_import_document_e2e(session, sample_pdf):
    """upload PDF → document exists → task exists → frontend can query status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload file
        files = {"file": ("test_import.pdf", sample_pdf, "application/pdf")}
        resp = await client.post("/api/documents/import", files=files)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # 2. Verify response
        assert data["is_new"] is True
        assert data["file_name"] == "test_import.pdf"
        expected_sha = hashlib.sha256(sample_pdf).hexdigest()
        assert data["sha256"] == expected_sha
        assert data["document_id"] is not None
        assert data["task_id"] is not None

        document_id = data["document_id"]
        task_id = data["task_id"]

        # 3. Verify document exists via GET /api/documents
        resp2 = await client.get("/api/documents")
        assert resp2.status_code == 200
        docs = resp2.json()["documents"]
        doc_ids = [d["id"] for d in docs]
        assert document_id in doc_ids

        # 4. Verify document detail
        resp3 = await client.get(f"/api/documents/{document_id}")
        assert resp3.status_code == 200
        detail = resp3.json()
        assert detail["document"]["file_name"] == "test_import.pdf"
        assert detail["document"]["processing_status"] == "imported"

        # 5. Verify task exists
        resp4 = await client.get("/api/tasks")
        assert resp4.status_code == 200
        tasks = resp4.json()["tasks"]
        task_ids = [t["id"] for t in tasks]
        assert task_id in task_ids

        # 6. Verify task status is queued
        task = next(t for t in tasks if t["id"] == task_id)
        assert task["status"] == "queued"
        assert task["task_type"] == "document_ingest"


@pytest.mark.asyncio
async def test_import_duplicate_pdf_idempotent(session, sample_pdf):
    """同 SHA256 再次导入 → is_new=False，不重复创建 Document。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First import
        files = {"file": ("dup_test.pdf", sample_pdf, "application/pdf")}
        resp1 = await client.post("/api/documents/import", files=files)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["is_new"] is True

        # Second import (same bytes)
        files2 = {"file": ("dup_test_again.pdf", sample_pdf, "application/pdf")}
        resp2 = await client.post("/api/documents/import", files=files2)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["is_new"] is False
        assert data2["document_id"] == data1["document_id"]
        assert data2["task_id"] is None  # no new task for duplicate


@pytest.mark.asyncio
async def test_import_rejects_unsupported_type(session):
    """非 PDF/DOCX 文件 → 400。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("test.txt", b"hello", "text/plain")}
        resp = await client.post("/api/documents/import", files=files)
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_import_rejects_empty_file(session):
    """空文件 → 400。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        resp = await client.post("/api/documents/import", files=files)
        assert resp.status_code == 400
