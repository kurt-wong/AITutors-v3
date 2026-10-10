"""M3a: Question read-only API + Producer grade/subject mapping (no LLM)."""

from __future__ import annotations

import uuid

import pytest

from app.api.routers.questions import get_question, list_questions
from app.models.content import (
    InstanceRoleContent,
    Question,
    QuestionInstance,
)
from app.models.source import Document, DocumentSourceVersion


async def _seed_question(session) -> tuple[Question, QuestionInstance, Document]:
    doc = Document(
        id=uuid.uuid4(),
        original_object_key="k",
        original_sha256="a" * 64,
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
        body_hash="b" * 64,
        integrity_hash="c" * 64,
        page_count=1,
        line_count=1,
        status="sealed",
    )
    session.add(sv)
    q = Question(
        id=uuid.uuid4(),
        subject="化学",
        grade="高一",
        canonical_question_type="single_choice",
        dedup_key="d" * 64,
    )
    session.add(q)
    await session.flush()
    qi = QuestionInstance(
        id=uuid.uuid4(),
        question_id=q.id,
        document_id=doc.id,
        source_version_id=sv.id,
        occurrence_key="occ-1",
        question_number="8",
        question_number_range="8",
        page_no=3,
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
            text_hash="e" * 64,
            source_span={"span_id": "sp-Q8.option.B"},
        )
    )
    session.add(
        InstanceRoleContent(
            id=uuid.uuid4(),
            instance_id=qi.id,
            role="stem",
            label=None,
            role_index=0,
            text="8. 下列物质中…",
            text_hash="f" * 64,
            source_span={"span_id": "sp-Q8.stem"},
        )
    )
    await session.flush()
    return q, qi, doc


@pytest.mark.asyncio
async def test_list_and_get_question_real_content(session):
    q, qi, doc = await _seed_question(session)

    listed = await list_questions(document_id=None, limit=50, offset=0, db=session)
    assert listed.total >= 1
    assert any(item.id == q.id for item in listed.questions)
    hit = next(item for item in listed.questions if item.id == q.id)
    assert hit.subject == "化学"
    assert hit.grade == "高一"
    assert hit.question_number == "8"

    detail = await get_question(question_id=q.id, db=session)
    assert detail.subject == "化学"
    assert detail.grade == "高一"
    assert detail.canonical_question_type == "single_choice"
    assert detail.instances and detail.instances[0].id == qi.id
    roles = {c.role for c in detail.instances[0].contents}
    assert "stem" in roles and "option" in roles
    opt = next(c for c in detail.instances[0].contents if c.role == "option")
    assert "CO_{2}" in opt.text  # raw LaTeX preserved, not rewritten


@pytest.mark.asyncio
async def test_question_null_subject_render_as_none(session):
    q = Question(
        id=uuid.uuid4(),
        subject=None,
        grade=None,
        canonical_question_type="fill_in",
        dedup_key="9" * 64,
    )
    session.add(q)
    await session.flush()
    detail = await get_question(question_id=q.id, db=session)
    assert detail.subject is None
    assert detail.grade is None


@pytest.mark.asyncio
async def test_question_not_found(session):
    with pytest.raises(Exception) as exc:
        await get_question(question_id=uuid.uuid4(), db=session)
    assert "not found" in str(exc.value).lower() or getattr(exc.value, "status_code", None) == 404


def test_grade_subject_from_rel_path_owner_rules():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(r"D:/Project/Papers/scripts")))
    from reslice_pipeline import grade_subject_from_rel_path as g

    assert g("会考/化学/2018北京春季高中会考化学（教师版）(1).md") == (
        "高一",
        "化学",
        "path_keyword:会考/合格考/学业水平考试",
    )
    assert g("高二/物理/卷.md")[0] == "高二"
    assert g("高三/数学/卷.md")[0] == "高三"
    assert g("高考真题/语文/卷.md")[0] == "高三"
    # 五年级真值，不进兜底
    grade, subject, src = g("五年级/数学/卷.md")
    assert grade == "五年级"
    assert subject == "数学"
    assert "fallback" not in src
    # 无法分辨 → 兜底 高三
    assert g("某地/化学/卷.md") == ("高三", "化学", "fallback")
