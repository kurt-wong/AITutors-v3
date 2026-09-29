"""P1 hardening edge cases (matrix A). No multi-blank, no N-values, no schema.
Areas: Compiler edges, Admission fail-closed, replay, proof binding, event order.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.hashing import sha256_hex
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.evidence.proof import (
    generate_review_proof,
    require_app_secret,
    verify_review_proof,
)
from app.domains.gate.admission import AdmissionService
from app.models.source import DocumentSourceLine
from app.repositories.base import AppendOnlyViolation, RepositoryError
from app.repositories.evidence_repository import (
    EvidenceRepository,
    delete_validation_event,
    update_validation_event,
)
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

SECRET = "test-app-secret-32-bytes-minimum!!"
CLAIM = "Q1"


def ev(result="validated", at=None, claim=CLAIM, method="frozen_header_rule", validator="gate/v1"):
    return ValidationEvent(
        event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=claim,
        validation_result=result,
        checks=(CheckResult(check_id="X", result="pass"),),
        validation_method=method, validator=validator,
        validated_at=at or datetime.now(timezone.utc),
    )


def payload():
    return {
        "ir_snapshot": {
            "ir_schema": "semantic-question-ir/v0.3",
            "units": [{"unit_id": CLAIM, "unit_type": "standalone_question",
                       "question_number": "1", "question_number_range": None,
                       "original_question_type": "single_choice",
                       "content": [{"role": "stem", "span_id": "sp-s", "label": None, "unsupported": False}],
                       "shared_components": [], "relations": [], "semantic_status": "ready",
                       "sub_questions": []}],
        },
        "resolved_spans": [{"span_id": "sp-s", "role": "stem", "granularity": "line",
                            "line_refs": ["P1L001"], "start_offset": None, "end_offset": None,
                            "text_hash": "0"*64, "resolution_status": "exact"}],
        "compiled_roles": [
            {"role": "stem", "span_id": "sp-s", "line_refs": ["P1L001"],
             "text": "stem", "text_hash": sha256_hex("stem"), "label": None,
             "unit_id": CLAIM, "kind": "content"},
            {"role": "option", "span_id": "sp-a", "line_refs": ["P1L002"],
             "text": "A. x", "text_hash": sha256_hex("A. x"), "label": "A",
             "unit_id": CLAIM, "kind": "content"},
            {"role": "option", "span_id": "sp-b", "line_refs": ["P1L003"],
             "text": "B. y", "text_hash": sha256_hex("B. y"), "label": "B",
             "unit_id": CLAIM, "kind": "content"},
        ],
        "answer": [{"unit_id": CLAIM, "question_number": "1", "span_id": "sp-an",
                    "line_refs": ["P1L004"], "text": "A", "text_hash": sha256_hex("A"),
                    "source_located": True, "complete": True, "verified_correct": None}],
        "figure_refs": [], "knowledge_links": [], "evidence": [],
        "display_hint": {"unit_type": "standalone_unit", "canonical_question_type": "single_choice"},
    }


async def seed(session, *, gate_decision=None):
    texts = ("stem", "A. x", "B. y", "A")
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="g.pdf", file_type="pdf", upload_meta={}, processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        document_id=doc.id, artifact_kind="raw_l1", role="native", provider="native",
        body_text="\n".join(texts), body_hash=sha256_hex(list(texts)),
        integrity_hash=sha256_hex(list(texts)), page_count=1, line_count=len(texts),
        status="draft",
    )
    await session.flush()
    for i, t in enumerate(texts):
        await src.append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref=f"P1L{i+1:03d}", seq=i+1,
            page_no=1, line_no_in_page=i+1, text=t, block_type="text",
            line_hash=sha256_hex(t),
        ))
    await session.flush()
    await src.seal_version(sv.id)
    await session.flush()
    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id, annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1", model_config_hash=sha256_hex("m"),
        payload={"semantic_units": [], "document_metadata_claims": {"subject": "m", "grade": "3"}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    cand = await SnapshotRepository(session).create_admission_candidate(
        unit_type="standalone_unit", source_version_id=sv.id, annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=payload(),
        gate_decision=gate_decision or {
            "gate_policy_version": "admission-gate/v1", "decision": "auto_approve",
            "layers": {}, "reasons": []},
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann, cand


class TestAdmissionFailClosed:
    async def test_no_authority_blocks_and_stays_pending(self, session):
        sv, ann, cand = await seed(session)
        svc = AdmissionService(session)
        with pytest.raises(RepositoryError, match="fail-closed|authority"):
            await svc.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
        await session.refresh(cand)
        # must remain pending_review (not auto-reject)
        state = (await SnapshotRepository(session).find_candidate_by_id(cand.id)) if hasattr(
            SnapshotRepository(session), "find_candidate_by_id") else cand
        # re-read via lock
        c2 = await SnapshotRepository(session).lock_candidate(cand.id)
        print(f"\n[FAILCLOSED] status after blocked approve={c2.decision_status!r}")
        assert c2.decision_status == "pending_review"

    async def test_auto_gate_without_auto_approve_blocked(self, session):
        sv, ann, cand = await seed(session, gate_decision={
            "gate_policy_version": "admission-gate/v1", "decision": "pending_review",
            "layers": {}, "reasons": []})
        repo = EvidenceRepository(session)
        await repo.append_event(ev(), candidate_id=cand.id, source_version_id=sv.id)
        svc = AdmissionService(session)
        with pytest.raises(RepositoryError, match="auto_approve"):
            await svc.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
        print("\n[FAILCLOSED] auto_gate without auto_approve rejected")

    async def test_rejected_gate_blocks_approve_even_with_validated_event(self, session):
        sv, ann, cand = await seed(session, gate_decision={
            "gate_policy_version": "admission-gate/v1", "decision": "rejected",
            "layers": {}, "reasons": ["bad"]})
        repo = EvidenceRepository(session)
        await repo.append_event(ev(), candidate_id=cand.id, source_version_id=sv.id)
        svc = AdmissionService(session)
        with pytest.raises(RepositoryError, match="gate_decision=rejected"):
            await svc.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
        print("\n[FAILCLOSED] P0-G-002 holds: rejected gate cannot approve")


class TestReplayDeterminism:
    async def test_double_approve_noop_same_status(self, session):
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        await repo.append_event(ev(), candidate_id=cand.id, source_version_id=sv.id)
        svc = AdmissionService(session)
        r1 = await svc.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
        r2 = await svc.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
        print(f"\n[REPLAY] approve1={r1.decision_status} approve2={r2.decision_status} same={r1.id==r2.id}")
        assert r1.decision_status == r2.decision_status == "approved"
        assert r1.id == r2.id

    async def test_event_replay_same_result_single_row(self, session):
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        a = await repo.append_event(ev(), candidate_id=cand.id, source_version_id=sv.id)
        b = await repo.append_event(ev(at=datetime.now(timezone.utc)+timedelta(seconds=2)),
                                    candidate_id=cand.id, source_version_id=sv.id)
        rows = await repo.find_events_for_claim(cand.id, CLAIM)
        print(f"\n[REPLAY] rows={len(rows)} same_id={a.id==b.id}")
        assert len(rows) == 1 and a.id == b.id


class TestProofBinding:
    def test_proof_binds_all_fields(self):
        cid, ts = uuid.uuid4(), datetime.now(timezone.utc)
        base = generate_review_proof(candidate_id=cid, review_result="validated",
                                     reviewer_id="r1", reviewed_at=ts, app_secret=SECRET)

        class R:
            validation_method = "human_review"
            validator = "human/r1"
            candidate_id = cid
            validation_result = "validated"
            validated_at = ts

        class R2(R):
            validation_result = "rejected"
        class R3(R):
            validator = "human/r2"
        class R4(R):
            validated_at = ts + timedelta(seconds=1)

        for name, rec in [("result", R2()), ("reviewer", R3()), ("time", R4())]:
            rec.review_proof = base
            ok = verify_review_proof(rec)
            print(f"\n[PROOF] tamper {name} verify={ok}")
            assert ok is False

    def test_empty_secret_fail_closed(self, monkeypatch):
        monkeypatch.setattr("app.domains.evidence.proof.settings.app_secret", "")
        with pytest.raises(RepositoryError):
            require_app_secret()
        print("\n[PROOF] empty secret fail-closed")

    def test_short_secret_fail_closed(self, monkeypatch):
        monkeypatch.setattr("app.domains.evidence.proof.settings.app_secret", "x"*31)
        with pytest.raises(RepositoryError):
            require_app_secret()
        print("\n[PROOF] short secret fail-closed")


class TestAppendOnlyProbes:
    async def test_update_delete_probes_always_raise(self):
        with pytest.raises(AppendOnlyViolation):
            await update_validation_event()
        with pytest.raises(AppendOnlyViolation):
            await delete_validation_event()
        print("\n[APPEND] update/delete probes raise")
