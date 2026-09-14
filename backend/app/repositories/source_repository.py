"""数据域 B Repository：源写路径 + sealed/append-only 写保护（段 A，不做业务规则）。"""

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.source import (
    Document,
    DocumentSourceLine,
    DocumentSourceSpan,
    DocumentSourceVersion,
    SourceFigure,
)
from app.repositories.base import (
    AppendOnlyViolation,
    BaseRepository,
    RepositoryError,
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
        """幂等写（H-1/BUG-V3-007 终裁）：锚 UNIQUE(original_sha256) ON CONFLICT DO NOTHING。

        插入成功 → returning 新行；同 original_sha256 冲突（并发）→ re-read existing（幂等收敛，
        一个原始文件一个 Document 主档）。
        """
        stmt = (
            pg_insert(Document)
            .values(
                original_object_key=original_object_key,
                original_sha256=original_sha256,
                file_name=file_name,
                file_type=file_type,
                upload_meta=upload_meta,
                processing_status=processing_status,
            )
            .on_conflict_do_nothing(index_elements=["original_sha256"])
            .returning(Document)
        )
        row = (await self._session.execute(stmt)).scalars().first()
        if row is not None:
            return row
        existing = await self.find_document_by_sha256(original_sha256)
        if existing is None:
            raise RepositoryError(
                "document (original_sha256) conflict but no existing row readable"
            )
        return existing

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
        logical_execution_stage: str | None = None,
        logical_execution_hash: str | None = None,
        attempt_id: uuid.UUID | None = None,
    ) -> DocumentSourceVersion:
        """幂等写（H-1/BUG-V3-007 终裁）：锚 UNIQUE(stage,hash) ON CONFLICT DO NOTHING。

        Seal Version canonical uniqueness 由 LE Identity 表达；同 Seal LE 冲突（并发）→
        re-read existing（winner/loser 收敛到同一 version）。stage/hash 为 None（非 seal 路径）
        在 NULLS DISTINCT 下不冲突，照常插入。
        """
        stmt = (
            pg_insert(DocumentSourceVersion)
            .values(
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
                logical_execution_stage=logical_execution_stage,
                logical_execution_hash=logical_execution_hash,
                attempt_id=attempt_id,
            )
            .on_conflict_do_nothing(
                index_elements=["logical_execution_stage", "logical_execution_hash"]
            )
            .returning(DocumentSourceVersion)
        )
        row = (await self._session.execute(stmt)).scalars().first()
        if row is not None:
            return row
        existing = await self._version_by_le(
            logical_execution_stage=logical_execution_stage,
            logical_execution_hash=logical_execution_hash,
        )
        if existing is None:
            raise RepositoryError(
                "source_version (stage,hash) conflict but no existing row readable"
            )
        return existing

    async def _version_by_le(
        self, *, logical_execution_stage: str, logical_execution_hash: str
    ) -> DocumentSourceVersion | None:
        """任意 status 的 (stage,hash) 读（冲突 re-read）。"""
        res = await self._session.execute(
            select(DocumentSourceVersion).where(
                DocumentSourceVersion.logical_execution_stage == logical_execution_stage,
                DocumentSourceVersion.logical_execution_hash == logical_execution_hash,
            )
        )
        return res.scalars().first()

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

    async def _assert_source_version_mutable(self, version_id: uuid.UUID) -> None:
        """sealed invariant：sealed SourceVersion 不可追加任何子行（10 §4.2）。

        BUG-V3-047：此前 append_line/append_figure/append_span 无 sealed 守卫，
        仅 SealService 层自律。repository boundary 才是不可绕过的最低可信边界。
        """
        row = await self._session.get(DocumentSourceVersion, version_id)
        if row is None:
            raise RepositoryError(f"source_version {version_id} not found")
        if row.status == _SEALED:
            raise AppendOnlyViolation(
                f"sealed source version {version_id} is immutable — "
                f"append on sealed version is forbidden (10 §4.2)"
            )

    async def append_line(self, line: DocumentSourceLine) -> None:
        await self._assert_source_version_mutable(line.source_version_id)
        await self.add(line)

    async def update_line(self, *_args: object, **_kwargs: object) -> None:
        """document_source_lines append-only：UPDATE → 抛错。"""
        raise AppendOnlyViolation("document_source_lines is append-only")

    async def append_figure(self, figure: SourceFigure) -> None:
        await self._assert_source_version_mutable(figure.source_version_id)
        await self.add(figure)

    async def update_figure(self, *_args: object, **_kwargs: object) -> None:
        raise AppendOnlyViolation("source_figures is append-only")

    async def append_span(self, span) -> None:
        """Phase I-3：追加 document_source_span（layout evidence）。"""
        await self._assert_source_version_mutable(span.source_version_id)
        await self.add(span)

    async def update_span(self, *_args: object, **_kwargs: object) -> None:
        raise AppendOnlyViolation("document_source_spans is append-only")

    async def find_document_by_sha256(self, original_sha256: str) -> Document | None:
        """document 级幂等：原始文件 hash 定位既有主档（10 §4.1；DB 无 UNIQUE，service lookup）。"""
        res = await self._session.execute(
            select(Document).where(Document.original_sha256 == original_sha256)
        )
        return res.scalar_one_or_none()

    async def find_sealed_version_by_le(
        self, *, document_id: uuid.UUID, logical_execution_hash: str
    ) -> DocumentSourceVersion | None:
        """version 级幂等：(document, stage=seal, hash) 查既有 sealed version（10 §3 LE 幂等）。"""
        res = await self._session.execute(
            select(DocumentSourceVersion).where(
                DocumentSourceVersion.document_id == document_id,
                DocumentSourceVersion.status == _SEALED,
                DocumentSourceVersion.logical_execution_stage == "seal",
                DocumentSourceVersion.logical_execution_hash == logical_execution_hash,
            )
        )
        return res.scalar_one_or_none()

    async def get_lines_by_version(
        self, version_id: uuid.UUID
    ) -> list[DocumentSourceLine]:
        """读某 sealed version 的全部行，按 seq 升序（确定性，20 §5.1 Exact Replay 前提）。"""
        res = await self._session.execute(
            select(DocumentSourceLine)
            .where(DocumentSourceLine.source_version_id == version_id)
            .order_by(DocumentSourceLine.seq)
        )
        return list(res.scalars().all())

    async def get_figures_by_version(
        self, version_id: uuid.UUID
    ) -> list[SourceFigure]:
        """读某 sealed version 的图，按 figure_id 稳定排序（确定性定位）。"""
        res = await self._session.execute(
            select(SourceFigure)
            .where(SourceFigure.source_version_id == version_id)
            .order_by(SourceFigure.figure_id)
        )
        return list(res.scalars().all())

    async def get_spans_by_version(
        self, version_id: uuid.UUID
    ) -> list[DocumentSourceSpan]:
        """Phase I-4：读某 sealed version 的全部 spans，按 (line_ref, seq) 排序。"""
        res = await self._session.execute(
            select(DocumentSourceSpan)
            .where(DocumentSourceSpan.source_version_id == version_id)
            .order_by(DocumentSourceSpan.line_ref, DocumentSourceSpan.seq)
        )
        return list(res.scalars().all())

    async def set_document_status(self, document_id: uuid.UUID, status: str) -> None:
        """documents.processing_status 写（Source 内容生命周期，10 §4.1，非 sealed 表）。"""
        doc = await self._session.get(Document, document_id)
        if doc is None:
            raise RepositoryError(f"document {document_id} not found")
        doc.processing_status = status
