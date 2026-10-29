"""DocumentImportService：Phase I-2A Import Boundary。

职责边界（B3-2 显式入口策略，Owner 2026-10-29 终版）：
- 正式链允许两种显式声明的入口：preprocessing 包（唯一主路径，
  PreprocessingImportService / POST /documents/import-preprocessing），
  以及显式 source_mode='native' 的任务（Fallback Path，调试/特殊输入）。
- 禁止缺席推断：mode 缺失一律显式失败，不静默改走 native/LLM（ROUND2 §1.2）。
- 本服务对新文件显式拒绝（可读错误，可控裁撤），不再创建 document_ingest。
- 幂等保留：同 SHA256 已存在 → 返回既有 Document（只读），不重复建 Task。
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

        # 3. 检查是否已存在（幂等，只读返回）
        existing = await self._source_repo.find_document_by_sha256(sha256)
        if existing is not None:
            return existing, None, False

        # 4. B3-2 显式入口策略（Owner 2026-10-29 终版）：通用上传显式拒绝
        #（可控裁撤，可读错误，不静默改走 native/LLM）。合法途径：
        #   - preprocessing 包 → POST /documents/import-preprocessing（唯一主路径）；
        #   - 或显式声明 source_mode='native' 的任务（Fallback Path，调试/特殊输入）。
        raise ImportError_(
            "explicit-entry policy: generic raw upload is rejected (no silent "
            "reroute); submit a preprocessing package via "
            "POST /documents/import-preprocessing, or create a task with "
            f"explicit source_mode='native' (rejected file_name={file_name!r}, "
            f"sha256={sha256})"
        )
