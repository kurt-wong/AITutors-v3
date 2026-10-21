# -*- coding: utf-8 -*-
"""WP7-C: approve must update reused Instance's verified_correct.

Regression: materialize_for_review creates Instance with verified_correct=null.
When approve() later runs, the reuse branch (existing Instance) must update
answer_status.verified_correct=True (20 §8.3 approved materialize → True).
Previously the reuse branch silently returned, leaving Candidate=approved
but Instance still showing 待审核 (verified_correct=null).

Also covers: never downgrade True; materialize_for_review keeps null;
double approve is idempotent.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from app.core.hashing import sha256_hex
from app.domains.gate.admission import AdmissionService
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from app.models.snapshot import AdmissionCandidate, AdmissionEvent
from app.models.source import DocumentSourceLine
from app.repositories.content_repository import ContentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository
from app.domains.evidence.models import CheckResult, ValidationEvent

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000c7")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000c8")

FILLIN_LINES = ("1. 填空：___", "【答案】", "1. 苹果")


def _fillin_payload():
    return {
        "ir_snapshot": {
            "ir_schema": "semantic-question-ir/v0.3",
            "source_version_id": str(SVID), "annotation_id": str(ANN_ID),
            "units": [
                {"unit_id": "Q1", "unit_type": "standalone_question",
                 "question_number": "1", "question_number_range": None,
                 "original_question_type": "fill_in",
                 "content": [{"role": "stem", "span_id": "sp-Q1.stem", "label": None,
                              "unsupported": False}],
                 "shared_components": [], "relations": [], "semantic_status": "ready",
                 "sub_questions": []},
            ],
        },
        "resolved_spans": [
            {"span_id": "sp-Q1.stem", "role": "stem", "granularity": "line",
             "line_refs": ["P1L001"], "start_offset": None, "end_offset": None,
             "text_hash": "0" * 64, "resolution_status": "exact"},
        ],
        "compiled_roles": [
            {"role": "stem", "span_id": "sp-Q1.stem", "line_refs": ["P1L001"],
             "text": "1. 填空：___", "text_hash": sha256_hex("1. 填空：___"),
             "label": None, "unit_id": "Q1", "kind": "content"},
        ],
        "answer": [
            {"unit_id": "Q1", "question_number": "1", "span_id": "sp-Q1.answer",
             "line_refs": ["P1L003"], "text": "1. 苹果", "text_hash": sha256_hex("1. 苹果"),
             "source_located": True, "complete": True, "verified_correct": None},
        ],
        "figure_refs": [], "knowledge_links": [],
        "evidence": [], "display_hint": {"unit_type": "standalone_unit",
                                          "canonical_question_type": "fill_in"},
    }


def _pending_gd():
    return {"gate_policy_version": "admission-gate/v1", "decision": "pending_review",
            "layers": {}, "reasons": []}


def _human_approve_trail():
    return [{"decision": "approve", "verified_by": "human",
             "reviewer_id": "test-reviewer",
             "confirmed_fields": ["stem", "answer"]}]


async def _seed(session):
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="f.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    n = len(FILLIN_LINES)
    sv = await src.create_source_version(
        document_id=doc.id, artifact_kind="raw_l1", role="native", provider="native",
        body_text="\n".join(FILLIN_LINES), body_hash=sha256_hex(list(FILLIN_LINES)),
        integrity_hash=sha256_hex(list(FILLIN_LINES)), page_count=1, line_count=n,
        status="draft",
    )
    await session.flush()
    for i, t in enumerate(FILLIN_LINES):
        await src.append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref=f"P1L{i + 1:03d}", seq=i + 1,
            page_no=1, line_no_in_page=i + 1, text=t, block_type="text",
            line_hash=sha256_hex(t),
        ))
    await session.flush()
    await src.seal_version(sv.id)
    await session.flush()
    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id, annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1", model_config_hash=sha256_hex("m"),
        payload={"semantic_units": [{"unit_id": "Q1", "unit_type": "standalone_unit",
                                      "original_question_type": "fill_in",
                                      "content": {"stem": {"question_label": "1"},
                                                   "answer": {"answer_zone": "answer_table",
                                                              "question_label": "1"}}}],
                 "document_metadata_claims": {"subject": "语文", "grade": "高一"}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann


async def _make_pending_candidate(session, sv, ann, *, with_human_trail=False):
    snap = SnapshotRepository(session)
    cand = await snap.create_admission_candidate(
        unit_type="standalone_unit", source_version_id=sv.id, annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=_fillin_payload(), gate_decision=_pending_gd(),
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
        review_trail=_human_approve_trail() if with_human_trail else [],
    )
    await session.flush()
    return cand


async def _seed_authority(session, cand, sv, claim_id="Q1"):
    await EvidenceRepository(session).append_event(
        ValidationEvent(
            event_id=f"ve-{uuid.uuid4().hex[:8]}",
            claim_id=claim_id,
            validation_result="validated",
            checks=(CheckResult(check_id="BYTE_PROVEN", result="pass"),),
            validation_method="frozen_header_rule",
            validator="gate/v1",
        ),
        candidate_id=cand.id, source_version_id=sv.id,
    )
    await session.flush()


async def _answer_statuses(session):
    res = await session.execute(
        select(InstanceRoleContent.answer_status)
        .where(InstanceRoleContent.role == "answer")
    )
    return [r[0] for r in res.all()]


class TestApproveReuseUpdatesVerifiedCorrect:
    """WP7-C: approve on an already-materialized Instance updates verified_correct."""

    async def test_materialize_for_review_keeps_verified_null(self, session):
        """Pending materialize → verified_correct stays null (待审核)."""
        sv, ann = await _seed(session)
        cand = await _make_pending_candidate(session, sv, ann)
        admission = AdmissionService(session)
        await admission.materialize_for_review(
            candidate_id=cand.id, annotation_id=ann.id)
        await session.flush()
        assert cand.decision_status == "pending_review"
        statuses = await _answer_statuses(session)
        assert len(statuses) >= 1
        for s in statuses:
            assert (s or {}).get("verified_correct") is None, (
                f"materialize_for_review must not set verified_correct: {s}"
            )

    async def test_approve_after_materialize_updates_verified(self, session):
        """approve after materialize_for_review → verified_correct=True on reuse."""
        sv, ann = await _seed(session)
        cand = await _make_pending_candidate(session, sv, ann, with_human_trail=True)
        await _seed_authority(session, cand, sv)
        admission = AdmissionService(session)
        # Step 1: materialize for review (creates Instance, verified_correct=null)
        await admission.materialize_for_review(
            candidate_id=cand.id, annotation_id=ann.id)
        await session.flush()
        statuses = await _answer_statuses(session)
        assert all((s or {}).get("verified_correct") is None for s in statuses)

        # Step 2: approve — must update existing Instance's verified_correct
        decided = await admission.approve(
            candidate_id=cand.id,
            provenance={"source": "human", "reviewer_id": "test-reviewer"},
        )
        await session.flush()
        assert decided.decision_status == "approved"
        statuses = await _answer_statuses(session)
        assert len(statuses) >= 1
        for s in statuses:
            assert (s or {}).get("verified_correct") is True, (
                f"approve must set verified_correct=True on reuse: {s}"
            )
        # Instance count unchanged (reuse, not double-create)
        n_inst = (await session.execute(
            select(func.count()).select_from(QuestionInstance))).scalar()
        assert n_inst == 1

    async def test_approve_never_downgrades_verified(self, session):
        """update_answer_verified_correct never turns True → null/False."""
        sv, ann = await _seed(session)
        cand = await _make_pending_candidate(session, sv, ann, with_human_trail=True)
        await _seed_authority(session, cand, sv)
        admission = AdmissionService(session)
        await admission.materialize_for_review(
            candidate_id=cand.id, annotation_id=ann.id)
        await session.flush()
        # First approve sets True
        await admission.approve(
            candidate_id=cand.id,
            provenance={"source": "human", "reviewer_id": "r1"},
        )
        await session.flush()
        # Attempting to "update" to None must not downgrade
        content = ContentRepository(session)
        inst = (await session.execute(
            select(QuestionInstance))).scalars().first()
        n = await content.update_answer_verified_correct(
            instance_id=inst.id, verified_correct=None)
        assert n == 0, "must not downgrade True → None"
        statuses = await _answer_statuses(session)
        assert all((s or {}).get("verified_correct") is True for s in statuses)

    async def test_double_approve_idempotent(self, session):
        """Second approve is no-op; verified_correct stays True; no double Instance."""
        sv, ann = await _seed(session)
        cand = await _make_pending_candidate(session, sv, ann, with_human_trail=True)
        await _seed_authority(session, cand, sv)
        admission = AdmissionService(session)
        await admission.materialize_for_review(
            candidate_id=cand.id, annotation_id=ann.id)
        await session.flush()
        await admission.approve(
            candidate_id=cand.id,
            provenance={"source": "human", "reviewer_id": "r1"},
        )
        await session.flush()
        n_inst_1 = (await session.execute(
            select(func.count()).select_from(QuestionInstance))).scalar()
        n_event_1 = (await session.execute(
            select(func.count()).select_from(AdmissionEvent))).scalar()
        # Second approve
        decided2 = await admission.approve(
            candidate_id=cand.id,
            provenance={"source": "human", "reviewer_id": "r2"},
        )
        await session.flush()
        assert decided2.decision_status == "approved"
        n_inst_2 = (await session.execute(
            select(func.count()).select_from(QuestionInstance))).scalar()
        n_event_2 = (await session.execute(
            select(func.count()).select_from(AdmissionEvent))).scalar()
        assert n_inst_2 == n_inst_1, "double approve must not create new Instance"
        # Event may or may not be created on no-op — but Instance must not double
        statuses = await _answer_statuses(session)
        assert all((s or {}).get("verified_correct") is True for s in statuses)

    async def test_existing_approved_not_downgraded_by_fix(self, session):
        """Approved path (fresh materialize with mark_verified=True) stays True."""
        sv, ann = await _seed(session)
        cand = await _make_pending_candidate(session, sv, ann, with_human_trail=True)
        await _seed_authority(session, cand, sv)
        admission = AdmissionService(session)
        # Direct approve without prior materialize_for_review
        await admission.approve(
            candidate_id=cand.id,
            provenance={"source": "human", "reviewer_id": "r1"},
        )
        await session.flush()
        statuses = await _answer_statuses(session)
        assert all((s or {}).get("verified_correct") is True for s in statuses)
        # Idempotent re-approve does not break anything
        await admission.approve(
            candidate_id=cand.id,
            provenance={"source": "human", "reviewer_id": "r2"},
        )
        await session.flush()
        statuses = await _answer_statuses(session)
        assert all((s or {}).get("verified_correct") is True for s in statuses)
