"""M3b: feedback API — persist, validate, never mutate question content."""

from __future__ import annotations

import uuid

import pytest

from app.api.routers.feedback import create_feedback, get_feedback, list_feedbacks
from app.api.schemas import FeedbackCreateRequest
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from app.models.source import Document, DocumentSourceVersion
from fastapi import HTTPException


async def _seed(session):
    doc = Document(
        id=uuid.uuid4(),
        original_object_key="k",
        original_sha256=uuid.uuid4().hex + uuid.uuid4().hex,
        file_name="paper.pdf",
        file_type="pdf",
        upload_meta={},
        processing_status="sealed",
    )
    session.add(doc)
    sv = DocumentSourceVersion(
        id=uuid.uuid4(),
        document_id=doc.id,
        artifact_kind="canonical_l1",
        role="preprocessing",
        provider="preprocessing",
        body_text="x",
        body_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        integrity_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        page_count=1,
        line_count=1,
        status="sealed",
        logical_execution_stage=None,
        logical_execution_hash=None,
    )
    session.add(sv)
    q = Question(
        id=uuid.uuid4(),
        subject="化学",
        grade="高一",
        canonical_question_type="single_choice",
        dedup_key=uuid.uuid4().hex + uuid.uuid4().hex,  # unique 64-hex
    )
    session.add(q)
    await session.flush()
    qi = QuestionInstance(
        id=uuid.uuid4(),
        question_id=q.id,
        document_id=doc.id,
        source_version_id=sv.id,
        occurrence_key="occ-q8",
        question_number="8",
        question_number_range="8",
        page_no=1,
        instance_order=8,
    )
    session.add(qi)
    await session.flush()
    session.add(
        InstanceRoleContent(
            id=uuid.uuid4(),
            instance_id=qi.id,
            role="option",
            label="B",
            role_index=1,
            text=" $CO_{2}$",
            text_hash="a" * 64,
            source_span={"span_id": "sp-Q8.option.B", "lines": [20, 20]},
        )
    )
    await session.flush()
    return q, qi


@pytest.mark.asyncio
async def test_create_feedback_persists_and_snapshots(session):
    q, qi = await _seed(session)
    out = await create_feedback(
        FeedbackCreateRequest(
            question_id=q.id,
            instance_id=qi.id,
            category="latex_render_error",
            description="选项B下标未渲染",
            created_by="tester",
        ),
        db=session,
    )
    assert out.id is not None
    assert out.question_id == q.id
    assert out.instance_id == qi.id
    assert out.category == "latex_render_error"
    assert out.status == "open"
    assert out.content_snapshot["question_number"] == "8"
    roles = out.content_snapshot["roles"]
    assert any(r["label"] == "B" for r in roles)
    assert out.source_evidence["source_version_id"] == str(qi.source_version_id)
    assert out.source_evidence["spans"]

    got = await get_feedback(feedback_id=out.id, db=session)
    assert got.description == "选项B下标未渲染"

    listed = await list_feedbacks(question_id=q.id, db=session)
    assert listed.total >= 1
    assert "latex_render_error" in listed.categories


@pytest.mark.asyncio
async def test_feedback_all_categories_persist(session):
    q, qi = await _seed(session)
    cats = [
        "stem_missing_or_incomplete",
        "option_missing_or_incomplete",
        "answer_missing_or_wrong",
        "explanation_missing_or_wrong",
        "material_missing_or_bad_ref",
        "latex_render_error",
        "identity_or_number_mismatch",
        "subject_grade_wrong_or_unset",
        "other",
    ]
    for c in cats:
        out = await create_feedback(
            FeedbackCreateRequest(
                question_id=q.id, category=c, description=f"desc for {c}"
            ),
            db=session,
        )
        assert out.category == c
    listed = await list_feedbacks(question_id=q.id, db=session)
    assert listed.total == len(cats)


@pytest.mark.asyncio
async def test_feedback_does_not_mutate_question(session):
    q, qi = await _seed(session)
    from sqlalchemy import select

    contents = (
        await session.execute(
            select(InstanceRoleContent).where(InstanceRoleContent.instance_id == qi.id)
        )
    ).scalars().all()
    hashes = {c.id: c.text_hash for c in contents}
    texts = {c.id: c.text for c in contents}

    await create_feedback(
        FeedbackCreateRequest(
            question_id=q.id,
            category="other",
            description="should not touch question",
        ),
        db=session,
    )

    contents2 = (
        await session.execute(
            select(InstanceRoleContent).where(InstanceRoleContent.instance_id == qi.id)
        )
    ).scalars().all()
    assert {c.id: c.text_hash for c in contents2} == hashes
    assert {c.id: c.text for c in contents2} == texts
    q2 = await session.get(Question, q.id)
    assert q2.subject == "化学"
    assert q2.grade == "高一"


@pytest.mark.asyncio
async def test_invalid_inputs_rejected(session):
    q, qi = await _seed(session)
    with pytest.raises(HTTPException) as e:
        await create_feedback(
            FeedbackCreateRequest(
                question_id=uuid.uuid4(), category="other", description="x"
            ),
            db=session,
        )
    assert e.value.status_code == 404

    with pytest.raises(HTTPException) as e:
        await create_feedback(
            FeedbackCreateRequest(question_id=q.id, category="nope", description="x"),
            db=session,
        )
    assert e.value.status_code == 422

    with pytest.raises(HTTPException) as e:
        await create_feedback(
            FeedbackCreateRequest(question_id=q.id, category="other", description="  "),
            db=session,
        )
    assert e.value.status_code == 422

    with pytest.raises(HTTPException) as e:
        await create_feedback(
            FeedbackCreateRequest(
                question_id=q.id,
                instance_id=uuid.uuid4(),
                category="other",
                description="x",
            ),
            db=session,
        )
    assert e.value.status_code == 422
