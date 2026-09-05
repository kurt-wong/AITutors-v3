"""数据域 B Repository：源写路径 + sealed/append-only 写保护（段 A，不做业务规则）。"""

import uuid

from app.models.source import (
    Document,
    DocumentSourceLine,
    DocumentSourceVersion,
    SourceFigure,
)
from app.repositories.base import (
    AppendOnlyViolation,
    BaseRepository,
    SealedVersionError,
)

_SEALED = "sealed"


class SourceRepository(BaseRepository):
    async def create_document(
        self,
        *,
        original_object_key: str,
        original_sha256: str,
        file_name: str,
        file_type: str,
        upload_meta: dict,
        processing_status: str,
    ) -> Document:
        doc = Document(
            original_object_key=original_object_key,
            original_sha256=original_sha256,
            file_name=file_name,
            file_type=file_type,
            upload_meta=upload_meta,
            processing_status=processing_status,
        )
        await self.add(doc)
        return doc

    async def create_source_version(
        self,
        *,
        document_id: uuid.UUID,
        artifact_kind: str,
        role: str,
        provider: str,
        body_text: str,
        body_hash: str,
        integrity_hash: str,
        page_count: int,
        line_count: int,
        status: str,
        parent_version_id: uuid.UUID | None = None,
        text_coverage: float | None = None,
        source_meta: dict | None = None,
    ) -> DocumentSourceVersion:
        version = DocumentSourceVersion(
            document_id=document_id,
            artifact_kind=artifact_kind,
            role=role,
            provider=provider,
            parent_version_id=parent_version_id,
            body_text=body_text,
            body_hash=body_hash,
            integrity_hash=integrity_hash,
            page_count=page_count,
            line_count=line_count,
            text_coverage=text_coverage,
            source_meta=source_meta,
            status=status,
        )
        await self.add(version)
        return version

    async def get_version(self, version_id: uuid.UUID) -> DocumentSourceVersion | None:
        return await self._session.get(DocumentSourceVersion, version_id)

    async def update_version(self, version_id: uuid.UUID, **changes: object) -> None:
        """受保护写路径：status=sealed 后任何 UPDATE → 抛错（不静默忽略）。"""
        row = await self._session.get(DocumentSourceVersion, version_id)
        if row is None:
            raise SealedVersionError(f"version {version_id} not found")
        if row.status == _SEALED:
            raise SealedVersionError(
                f"sealed source version {version_id} is immutable"
            )
        for field, value in changes.items():
            setattr(row, field, value)

    async def seal_version(self, version_id: uuid.UUID) -> None:
        """draft → sealed 一次性流转；若已 sealed 则抛错。"""
        row = await self._session.get(DocumentSourceVersion, version_id)
        if row is None:
            raise SealedVersionError(f"version {version_id} not found")
        if row.status == _SEALED:
            raise SealedVersionError(
                f"version {version_id} already sealed"
            )
        row.status = _SEALED

    async def append_line(self, line: DocumentSourceLine) -> None:
        await self.add(line)

    async def update_line(self, *_args: object, **_kwargs: object) -> None:
        """document_source_lines append-only：UPDATE → 抛错。"""
        raise AppendOnlyViolation("document_source_lines is append-only")

    async def append_figure(self, figure: SourceFigure) -> None:
        await self.add(figure)

    async def update_figure(self, *_args: object, **_kwargs: object) -> None:
        raise AppendOnlyViolation("source_figures is append-only")
