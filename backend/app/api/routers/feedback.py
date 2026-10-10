"""Human Verification Console feedback API (M3b).

只记录问题/证据/用户判断；不改写 Question/Instance/Source/Gate/Admission。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import (
    FEEDBACK_CATEGORY_VALUES,
    FeedbackCreateRequest,
    FeedbackListResponse,
    FeedbackOut,
)
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from app.models.feedback import QuestionFeedback

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


def _to_out(f: QuestionFeedback) -> FeedbackOut:
    return FeedbackOut(
        id=f.id,
        question_id=f.question_id,
        instance_id=f.instance_id,
        source_version_id=f.source_version_id,
        producer_unit_id=f.producer_unit_id,
        source_evidence=f.source_evidence,
        content_snapshot=f.content_snapshot,
        category=f.category,
        description=f.description,
        status=f.status,
        created_by=f.created_by,
        created_at=f.created_at,
        review_note=f.review_note,
    )


def _validate_category(category: str) -> str:
    if category not in FEEDBACK_CATEGORY_VALUES:
        raise HTTPException(
            status_code=422,
            detail=f"invalid category {category!r}; allowed={list(FEEDBACK_CATEGORY_VALUES)}",
        )
    return category


@router.get("/categories")
async def list_categories() -> dict:
    return {"categories": list(FEEDBACK_CATEGORY_VALUES)}


@router.post("", response_model=FeedbackOut)
async def create_feedback(
    body: FeedbackCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackOut:
    """提交结构化反馈。绑定提交时的题目身份 + 内容快照 + 源证据。不改题目。"""
    if not body.description or not body.description.strip():
        raise HTTPException(status_code=422, detail="description required")
    category = _validate_category(body.category)

    q = await db.get(Question, body.question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="question not found")

    instance: QuestionInstance | None = None
    if body.instance_id is not None:
        instance = await db.get(QuestionInstance, body.instance_id)
        if instance is None or instance.question_id != q.id:
            raise HTTPException(
                status_code=422,
                detail="instance_id does not belong to question_id",
            )
    else:
        instance = (
            await db.execute(
                select(QuestionInstance)
                .where(QuestionInstance.question_id == q.id)
                .order_by(QuestionInstance.instance_order)
            )
        ).scalars().first()

    contents = []
    if instance is not None:
        contents = (
            await db.execute(
                select(InstanceRoleContent)
                .where(InstanceRoleContent.instance_id == instance.id)
                .order_by(InstanceRoleContent.role, InstanceRoleContent.role_index)
            )
        ).scalars().all()

    snapshot = {
        "subject": q.subject,
        "grade": q.grade,
        "canonical_question_type": q.canonical_question_type,
        "dedup_key": q.dedup_key,
        "question_number": instance.question_number if instance else None,
        "roles": [
            {
                "role": c.role,
                "label": c.label,
                "role_index": c.role_index,
                "text_hash": c.text_hash,
                "text_excerpt": (c.text or "")[:200],
            }
            for c in contents
        ],
    }
    source_evidence = {
        "document_id": str(instance.document_id) if instance else None,
        "source_version_id": str(instance.source_version_id) if instance else None,
        "occurrence_key": instance.occurrence_key if instance else None,
        "page_no": instance.page_no if instance else None,
        "spans": [c.source_span for c in contents if c.source_span],
        "producer_unit_id": body.producer_unit_id,
    }

    row = QuestionFeedback(
        question_id=q.id,
        instance_id=instance.id if instance else None,
        source_version_id=instance.source_version_id if instance else None,
        producer_unit_id=body.producer_unit_id,
        source_evidence=source_evidence,
        content_snapshot=snapshot,
        category=category,
        description=body.description.strip(),
        status="open",
        created_by=body.created_by or "console-user",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_out(row)


@router.get("", response_model=FeedbackListResponse)
async def list_feedbacks(
    question_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> FeedbackListResponse:
    stmt = select(QuestionFeedback).order_by(
        QuestionFeedback.created_at.desc(), QuestionFeedback.id
    )
    if question_id is not None:
        stmt = stmt.where(QuestionFeedback.question_id == question_id)
    if status is not None:
        stmt = stmt.where(QuestionFeedback.status == status)
    rows = (await db.execute(stmt)).scalars().all()
    total = len(rows)
    page = rows[offset : offset + limit]
    return FeedbackListResponse(
        feedbacks=[_to_out(r) for r in page],
        total=total,
        categories=list(FEEDBACK_CATEGORY_VALUES),
    )


@router.get("/{feedback_id}", response_model=FeedbackOut)
async def get_feedback(
    feedback_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FeedbackOut:
    row = await db.get(QuestionFeedback, feedback_id)
    if row is None:
        raise HTTPException(status_code=404, detail="feedback not found")
    return _to_out(row)
