"""DocumentImportService：Phase I-2A Import Boundary。

职责边界：
- 接收文件 bytes → 计算 SHA256 → 创建 Document → 创建 Task(queued)
- 禁止：OCR、LLM、Resolver、Compiler、任何 pipeline 执行

一个原始文件对应一个 Document 主档（BUG-V3-007 终裁）。
幂等：同 SHA256 再次导入返回既有 Document + 不重复创建 Task。
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Document
from app.models.runtime import Task
from app.repositories.source_repository import SourceRepository
from app.domains.task.service import TaskService

# Phase I-2A：文件暂存到本地目录（后续可切换 MinIO）
_IMPORT_DIR = Path("data/imports")

_ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class ImportError_(Exception):
    """导入失败（文件类型不合法等）。"""


class DocumentImportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._source_repo = SourceRepository(session)
        self._task_service = TaskService(session)

    async def import_file(
        self,
        *,
        file_bytes: bytes,
        file_name: str,
        created_by: str | None = None,
    ) -> tuple[Document, Task | None, bool]:
        """导入文件。返回 (document, task, is_new)。

        is_new=False 表示同 SHA256 已存在（幂等），task 可能为 None。
        """
        # 1. 校验文件类型
        ext = Path(file_name).suffix.lower()
        if ext not in _ALLOWED_EXTENSIONS:
            raise ImportError_(
                f"unsupported file type: {ext!r}; allowed: {sorted(_ALLOWED_EXTENSIONS)}"
            )

        if len(file_bytes) == 0:
            raise ImportError_("empty file")

        # 2. 计算 SHA256
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # 3. 检查是否已存在（幂等）
        existing = await self._source_repo.find_document_by_sha256(sha256)
        if existing is not None:
            return existing, None, False

        # 4. 存储文件到本地
        _IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        object_key = f"{sha256}{ext}"
        file_path = _IMPORT_DIR / object_key
        file_path.write_bytes(file_bytes)

        # 5. 创建 Document
        document = await self._source_repo.create_document(
            original_object_key=str(file_path),
            original_sha256=sha256,
            file_name=file_name,
            file_type=ext.lstrip("."),
            upload_meta={
                "file_size": len(file_bytes),
                "imported_by": created_by or "admin",
            },
            processing_status="imported",
        )

        # 6. 创建 Task（queued，等待 Worker 消费）
        task = await self._task_service.enqueue(
            task_type="document_ingest",
            task_params={
                "document_id": str(document.id),
                "original_sha256": sha256,
                "file_name": file_name,
                "file_path": str(file_path),
                "file_type": ext.lstrip("."),
            },
            created_by=created_by or "admin",
        )

        return document, task, True
