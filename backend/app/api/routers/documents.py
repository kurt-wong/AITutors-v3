"""Document API endpoints：列表 + 详情（含 pipeline 聚合）+ 导入。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import (
    CandidateSummary,
    DocumentDetail,
    DocumentListResponse,
    DocumentSummary,
    FigureInfo,
    ImportResponse,
    SourceLinesResponse,
    SourceLineInfo,
    SourceQualityReport,
    SourceVersionInfo,
)
from app.domains.source.import_service import DocumentImportService, ImportError_
from app.models.snapshot import AdmissionCandidate, SemanticAnnotation
from app.models.source import Document, DocumentSourceVersion, SourceFigure

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/import", response_model=ImportResponse)
async def import_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ImportResponse:
    """导入文件：SHA256 → Document → Task(queued)。不做任何 pipeline 执行。"""
    file_bytes = await file.read()
    service = DocumentImportService(db)
    try:
        document, task, is_new = await service.import_file(
            file_bytes=file_bytes,
            file_name=file.filename or "unknown",
            created_by="admin",
        )
    except ImportError_ as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    return ImportResponse(
        document_id=document.id,
        task_id=task.id if task else None,
        sha256=document.original_sha256,
        file_name=document.file_name,
        is_new=is_new,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """列出文档，可按 processing_status 筛选。"""
    stmt = select(Document)
    count_stmt = select(func.count()).select_from(Document)
    if status:
        stmt = stmt.where(Document.processing_status == status)
        count_stmt = count_stmt.where(Document.processing_status == status)

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(Document.file_name).offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    # 每个文档的 candidate 统计
    doc_ids = [r.id for r in rows]
    cand_counts: dict[uuid.UUID, tuple[int, int]] = {}
    if doc_ids:
        cand_stmt = (
            select(
                DocumentSourceVersion.document_id,
                func.count(AdmissionCandidate.id),
                func.count()
                .filter(AdmissionCandidate.decision_status == "pending_review"),
            )
            .join(
                SemanticAnnotation,
                SemanticAnnotation.source_version_id == DocumentSourceVersion.id,
            )
            .join(
                AdmissionCandidate,
                AdmissionCandidate.annotation_id == SemanticAnnotation.id,
            )
            .where(DocumentSourceVersion.document_id.in_(doc_ids))
            .group_by(DocumentSourceVersion.document_id)
        )
        for row in (await db.execute(cand_stmt)).all():
            cand_counts[row[0]] = (row[1], row[2])

    documents = []
    for r in rows:
        total_c, pending_c = cand_counts.get(r.id, (0, 0))
        documents.append(
            DocumentSummary(
                id=r.id,
                file_name=r.file_name,
                file_type=r.file_type,
                processing_status=r.processing_status,
                created_at=None,
                candidate_count=total_c,
                pending_count=pending_c,
            )
        )
    return DocumentListResponse(documents=documents, total=total)


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentDetail:
    """文档详情：document + source_versions + figures + candidates。"""
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")

    # source versions
    sv_stmt = (
        select(DocumentSourceVersion)
        .where(DocumentSourceVersion.document_id == document_id)
        .order_by(DocumentSourceVersion.role)
    )
    sv_rows = (await db.execute(sv_stmt)).scalars().all()
    source_versions = [
        SourceVersionInfo(
            id=sv.id,
            artifact_kind=sv.artifact_kind,
            role=sv.role,
            provider=sv.provider,
            status=sv.status,
            page_count=sv.page_count,
            line_count=sv.line_count,
            body_hash=sv.body_hash,
            integrity_hash=sv.integrity_hash,
            body_text=sv.body_text[:2000] if sv.body_text else None,
        )
        for sv in sv_rows
    ]

    # figures (from sealed versions)
    sealed_ids = [sv.id for sv in sv_rows if sv.status == "sealed"]
    figures: list[FigureInfo] = []
    if sealed_ids:
        fig_stmt = (
            select(SourceFigure)
            .where(SourceFigure.source_version_id.in_(sealed_ids))
            .order_by(SourceFigure.page_no, SourceFigure.figure_id)
        )
        figures = [
            FigureInfo(
                id=f.id,
                figure_id=f.figure_id,
                page_no=f.page_no,
                object_key=f.object_key,
                figure_hash=f.figure_hash,
            )
            for f in (await db.execute(fig_stmt)).scalars().all()
        ]

    # candidates via annotation → candidate chain
    sv_ids = [sv.id for sv in sv_rows]
    candidates: list[CandidateSummary] = []
    if sv_ids:
        cand_stmt = (
            select(AdmissionCandidate)
            .join(
                SemanticAnnotation,
                SemanticAnnotation.id == AdmissionCandidate.annotation_id,
            )
            .where(SemanticAnnotation.source_version_id.in_(sv_ids))
            .order_by(AdmissionCandidate.created_at)
        )
        candidates = [
            CandidateSummary(
                id=c.id,
                unit_type=c.unit_type,
                decision_status=c.decision_status,
                gate_decision=c.gate_decision,
                created_at=c.created_at,
            )
            for c in (await db.execute(cand_stmt)).scalars().all()
        ]

    doc_summary = DocumentSummary(
        id=doc.id,
        file_name=doc.file_name,
        file_type=doc.file_type,
        processing_status=doc.processing_status,
        created_at=None,
        candidate_count=len(candidates),
        pending_count=sum(
            1 for c in candidates if c.decision_status == "pending_review"
        ),
    )
    return DocumentDetail(
        document=doc_summary,
        source_versions=source_versions,
        figures=figures,
        candidates=candidates,
    )


@router.get("/{document_id}/source-quality", response_model=SourceQualityReport)
async def get_source_quality(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceQualityReport:
    """返回 sealed source version 的质量报告（从 source_meta.quality 读取）。"""
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")

    sv_stmt = (
        select(DocumentSourceVersion)
        .where(
            DocumentSourceVersion.document_id == document_id,
            DocumentSourceVersion.status == "sealed",
        )
        .order_by(DocumentSourceVersion.role)
        .limit(1)
    )
    sv = (await db.execute(sv_stmt)).scalar_one_or_none()
    if sv is None:
        raise HTTPException(status_code=404, detail="no sealed source version")

    quality = (sv.source_meta or {}).get("quality")
    if quality is None:
        raise HTTPException(status_code=404, detail="quality report not available")

    return SourceQualityReport(**quality)


@router.get("/{document_id}/source-lines", response_model=SourceLinesResponse)
async def get_source_lines(
    document_id: uuid.UUID,
    page_no: int | None = Query(None, ge=1),
    source_version_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> SourceLinesResponse:
    """返回 source lines（可按 page_no 过滤）。供 Page Source Viewer 使用。"""
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")

    # 确定 source version
    if source_version_id:
        sv = await db.get(DocumentSourceVersion, source_version_id)
        if sv is None or sv.document_id != document_id:
            raise HTTPException(status_code=404, detail="source version not found")
    else:
        sv_stmt = (
            select(DocumentSourceVersion)
            .where(
                DocumentSourceVersion.document_id == document_id,
                DocumentSourceVersion.status == "sealed",
            )
            .order_by(DocumentSourceVersion.role)
            .limit(1)
        )
        sv = (await db.execute(sv_stmt)).scalar_one_or_none()
        if sv is None:
            raise HTTPException(status_code=404, detail="no sealed source version")

    # 查询 lines
    from app.models.source import DocumentSourceLine

    line_stmt = select(DocumentSourceLine).where(
        DocumentSourceLine.source_version_id == sv.id
    )
    count_stmt = (
        select(func.count())
        .select_from(DocumentSourceLine)
        .where(DocumentSourceLine.source_version_id == sv.id)
    )
    if page_no is not None:
        line_stmt = line_stmt.where(DocumentSourceLine.page_no == page_no)
        count_stmt = count_stmt.where(DocumentSourceLine.page_no == page_no)

    total = (await db.execute(count_stmt)).scalar() or 0
    line_stmt = line_stmt.order_by(DocumentSourceLine.seq)
    rows = (await db.execute(line_stmt)).scalars().all()

    return SourceLinesResponse(
        source_version_id=sv.id,
        page_no=page_no,
        total_lines=total,
        lines=[
            SourceLineInfo(
                line_ref=r.line_ref,
                seq=r.seq,
                page_no=r.page_no,
                line_no_in_page=r.line_no_in_page,
                text=r.text,
                block_type=r.block_type,
                bbox=r.bbox,
                line_hash=r.line_hash,
            )
            for r in rows
        ],
    )
