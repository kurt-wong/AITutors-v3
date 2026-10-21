"""Question 只读查询 API（M3a Review Console）。

展示已 Admission 物化的真实 Question / QuestionInstance / InstanceRoleContent。
不做业务写入；subject/grade 为 NULL 时原样返回（前端显示“未设置”）。
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import (
    InstanceRoleContentInfo,
    QuestionDetail,
    QuestionInstanceInfo,
    QuestionListResponse,
    QuestionSummary,
)
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from app.models.source import Document, DocumentSourceVersion

router = APIRouter(prefix="/questions", tags=["questions"])


def _subject_or_unset(v: str | None) -> str | None:
    return v  # NULL stays NULL; UI renders 未设置


def _public_answer_status(status: dict | None) -> dict | None:
    """Student/consumer API: never expose review-only candidate text or
    internal trust-chain diagnostics (B4 / P2-API).
    Frontend only needs verified_correct / ownership / publish for UI trust
    signaling; publish_seal and binding_fact_id stay server-side.
    """
    if not status:
        return status
    _drop = {"candidate_text", "publish_seal", "binding_fact_id", "answer_text_hash"}
    out = {k: v for k, v in status.items() if k not in _drop}
    return out


@router.get("", response_model=QuestionListResponse)
async def list_questions(
    document_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> QuestionListResponse:
    """已物化 Question 列表（按 instance_order / question_number 排序）。"""
    stmt = (
        select(Question, QuestionInstance)
        .join(QuestionInstance, QuestionInstance.question_id == Question.id)
        .order_by(QuestionInstance.instance_order, QuestionInstance.question_number)
    )
    if document_id is not None:
        stmt = stmt.where(QuestionInstance.document_id == document_id)
    rows = (await db.execute(stmt)).all()
    total = len(rows)
    page = rows[offset : offset + limit]

    items = [
        QuestionSummary(
            id=q.id,
            subject=_subject_or_unset(q.subject),
            grade=_subject_or_unset(q.grade),
            canonical_question_type=q.canonical_question_type,
            instance_id=qi.id,
            document_id=qi.document_id,
            source_version_id=qi.source_version_id,
            question_number=qi.question_number,
            question_number_range=qi.question_number_range,
            page_no=qi.page_no,
            instance_order=qi.instance_order,
            created_at=q.created_at,
        )
        for q, qi in page
    ]
    return QuestionListResponse(questions=items, total=total)


@router.get("/{question_id}", response_model=QuestionDetail)
async def get_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> QuestionDetail:
    """Question 详情：identity + 全部 occurrence + role contents（stem/option/answer）。"""
    q = await db.get(Question, question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="question not found")

    inst_rows = (
        await db.execute(
            select(QuestionInstance)
            .where(QuestionInstance.question_id == question_id)
            .order_by(QuestionInstance.instance_order)
        )
    ).scalars().all()

    instances: list[QuestionInstanceInfo] = []
    for qi in inst_rows:
        contents = (
            await db.execute(
                select(InstanceRoleContent)
                .where(InstanceRoleContent.instance_id == qi.id)
                .order_by(
                    InstanceRoleContent.role,
                    InstanceRoleContent.role_index,
                    InstanceRoleContent.label,
                )
            )
        ).scalars().all()
        doc = await db.get(Document, qi.document_id)
        sv = await db.get(DocumentSourceVersion, qi.source_version_id)
        instances.append(
            QuestionInstanceInfo(
                id=qi.id,
                document_id=qi.document_id,
                document_file_name=doc.file_name if doc else None,
                source_version_id=qi.source_version_id,
                source_role=sv.role if sv else None,
                source_artifact_kind=sv.artifact_kind if sv else None,
                question_number=qi.question_number,
                question_number_range=qi.question_number_range,
                page_no=qi.page_no,
                instance_order=qi.instance_order,
                occurrence_key=qi.occurrence_key,
                contents=[
                    InstanceRoleContentInfo(
                        id=c.id,
                        role=c.role,
                        label=c.label,
                        role_index=c.role_index,
                        text=c.text,
                        text_hash=c.text_hash,
                        source_span=c.source_span,
                        answer_status=_public_answer_status(c.answer_status),
                    )
                    for c in contents
                ],
            )
        )

    return QuestionDetail(
        id=q.id,
        subject=_subject_or_unset(q.subject),
        grade=_subject_or_unset(q.grade),
        canonical_question_type=q.canonical_question_type,
        dedup_key=q.dedup_key,
        created_at=q.created_at,
        instances=instances,
    )
