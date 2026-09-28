"""Gate A3 — Persistence Boundary：Repository 写路径保护（sealed/append-only/唯一入口）。"""

import uuid

import pytest

from app.models.source import DocumentSourceLine
from app.repositories.base import AppendOnlyViolation, SealedVersionError
from app.repositories.content_repository import ContentRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

_SHA = "a" * 64


async def _mk_draft(session):
    sr = SourceRepository(session)
    doc = await sr.create_document(
        original_object_key="obj/key.pdf",
        original_sha256=_SHA,
        file_name="paper.pdf",
        file_type="pdf",
        upload_meta={},
        processing_status="created",
    )
    await sr.flush()
    version = await sr.create_source_version(
        document_id=doc.id,
        artifact_kind="canonical_l1",
        role="canonical",
        provider="",
        body_text="",
        body_hash=_SHA,
        integrity_hash=_SHA,
        page_count=1,
        line_count=0,
        status="draft",
    )
    await sr.flush()
    return sr, doc, version


async def test_draft_update_allowed_then_seal_forbids(session) -> None:
    sr, _doc, version = await _mk_draft(session)
    await sr.update_version(version.id, page_count=2)  # draft 允许
    await sr.seal_version(version.id)
    with pytest.raises(SealedVersionError):
        await sr.update_version(version.id, page_count=3)  # sealed 拒绝（不静默忽略）


async def test_seal_twice_raises(session) -> None:
    sr, _doc, version = await _mk_draft(session)
    await sr.seal_version(version.id)
    with pytest.raises(SealedVersionError):
        await sr.seal_version(version.id)


async def test_append_only_lines_figures(session) -> None:
    sr, _doc, version = await _mk_draft(session)
    with pytest.raises(AppendOnlyViolation):
        await sr.update_line(version.id)
    with pytest.raises(AppendOnlyViolation):
        await sr.update_figure(version.id)


async def test_append_line_ok(session) -> None:
    sr, _doc, version = await _mk_draft(session)
    line = DocumentSourceLine(
        source_version_id=version.id,
        line_ref="P1L001",
        seq=1,
        page_no=1,
        line_no_in_page=1,
        text="hello",
        block_type="text",
        line_hash=_SHA,
    )
    await sr.append_line(line)
    await sr.flush()
    assert line.id is not None


async def test_snapshot_append_only(session) -> None:
    snap = SnapshotRepository(session)
    with pytest.raises(AppendOnlyViolation):
        await snap.update_snapshot()
    with pytest.raises(AppendOnlyViolation):
        await snap.update_candidate_decision()


async def test_content_create_success(session) -> None:
    cr = ContentRepository(session)
    question = await cr.create_question(
        subject="数学", grade="高一", canonical_question_type="single_choice", dedup_key=_SHA
    )
    await cr.flush()
    assert question.id is not None


async def test_candidate_created_pending_review(session) -> None:
    """decision_status 唯一入口：Repository 创建候选固定 pending_review，不接受任意值（R1）。

    Phase 6：create 立即落库（pg_insert + returning，非惰性 ORM add）——候选必须满足 FK，
    故先建真实 source_version 父行 + annotation 父行。
    BUG-V3-046：annotation 只能引用 sealed source_version（10 §4.5），故先 seal。
    """
    snap = SnapshotRepository(session)
    sr, _doc, version = await _mk_draft(session)
    await sr.seal_version(version.id)
    await session.flush()
    ann = await snap.create_semantic_annotation(
        source_version_id=version.id,
        annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="p/v1",
        model_config_hash=_SHA,
        payload={},
        status="valid",
        logical_execution_stage="ann",
        logical_execution_hash="c" * 64,
    )
    candidate = await snap.create_admission_candidate(
        unit_type="standalone_unit",
        source_version_id=version.id,
        annotation_id=ann.id,
        build_versions={},
        input_identity={},
        payload={},
        logical_execution_stage="compile",
        logical_execution_hash="b" * 64,
    )
    assert candidate.decision_status == "pending_review"
