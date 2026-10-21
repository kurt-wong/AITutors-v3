"""DSH independent probe for R14 (temporary; deleted after run).

Exercises the REAL AdmissionService._materialize path with hand-frozen
payloads + resolver-shaped BindingFacts registered in the real registry.

Probes:
  1. honest control (Q1 fact -> Q1 instance) publishes
  2. forged answer span with honest unit qn -> withheld (not published)
  3. forged unit qn + forged answer span -> publishes foreign answer (HIT?)
  4. composite match facts -> withheld because qn is range "1-2"
  5. empty unit qn -> R14 guards inert
"""
from __future__ import annotations

import uuid

SVID = uuid.UUID("00000000-0000-0000-0000-00000000f999")
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.hashing import sha256_hex
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.gate.admission import AdmissionService, _publish_decision
from app.domains.gate.binding_fact import (
    derive_binding_fact,
    get_registry,
    register_trusted_binding_fact,
)
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from app.models.source import DocumentSourceLine
from app.repositories.content_repository import RepositoryError
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository


def ev(claim="Q1"):
    return ValidationEvent(
        event_id=f"ve-{uuid.uuid4().hex[:8]}",
        claim_id=claim,
        validation_result="validated",
        checks=(CheckResult(check_id="X", result="pass"),),
        validation_method="frozen_header_rule",
        validator="gate/v1",
        validated_at=datetime.now(timezone.utc),
    )


def _leaf_payload(*, unit_id="Q1", qn="1", stem="1. what is A?",
                  ans_span="sp-ans", ans_text="A", ans_qn="1",
                  stem_line="P1L001", ans_line="P1L005"):
    return {
        "ir_snapshot": {
            "ir_schema": "semantic-question-ir/v0.3",
            "units": [{
                "unit_id": unit_id, "unit_type": "standalone_question",
                "question_number": qn, "question_number_range": None,
                "original_question_type": "single_choice",
                "content": [{"role": "stem", "span_id": "sp-stem",
                             "label": None, "unsupported": False}],
                "shared_components": [], "relations": [],
                "semantic_status": "ready", "sub_questions": [],
            }],
        },
        "resolved_spans": [{
            "span_id": "sp-stem", "role": "stem", "granularity": "line",
            "line_refs": [stem_line], "start_offset": None, "end_offset": None,
            "text_hash": sha256_hex(stem), "resolution_status": "exact",
        }],
        "compiled_roles": [
            {"role": "stem", "span_id": "sp-stem", "line_refs": [stem_line],
             "text": stem, "text_hash": sha256_hex(stem), "label": None,
             "unit_id": unit_id, "kind": "content"},
            {"role": "option", "span_id": "sp-o1", "line_refs": ["P1L002"],
             "text": "A. a", "text_hash": sha256_hex("A. a"), "label": "A",
             "unit_id": unit_id, "kind": "content"},
            {"role": "option", "span_id": "sp-o2", "line_refs": ["P1L003"],
             "text": "B. b", "text_hash": sha256_hex("B. b"), "label": "B",
             "unit_id": unit_id, "kind": "content"},
        ],
        "answer": [{
            "unit_id": unit_id, "question_number": ans_qn,
            "span_id": ans_span, "line_refs": [ans_line],
            "text": ans_text, "text_hash": sha256_hex(ans_text),
            "source_located": True, "complete": True, "verified_correct": None,
        }],
        "figure_refs": [], "knowledge_links": [], "evidence": [],
        "display_hint": {"unit_type": "standalone_unit",
                         "canonical_question_type": "single_choice"},
    }


async def _seed(session, payload, claim="Q1", sv_id=None, fact_params=None):
    texts = ("line1", "line2", "line3", "line4", "line5")
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="g.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        id=sv_id,
        document_id=doc.id, artifact_kind="raw_l1", role="native",
        provider="native", body_text="\n".join(texts),
        body_hash=sha256_hex(list(texts)),
        integrity_hash=sha256_hex(list(texts)),
        page_count=1, line_count=len(texts), status="draft",
    )
    await session.flush()
    for i, t in enumerate(texts):
        await src.append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref=f"P1L{i+1:03d}", seq=i + 1,
            page_no=1, line_no_in_page=i + 1, text=t, block_type="text",
            line_hash=sha256_hex(t),
        ))
    await session.flush()
    await src.seal_version(sv.id)
    await session.flush()
    if fact_params:
        from app.domains.gate.binding_fact import derive_binding_fact, register_trusted_binding_fact
        register_trusted_binding_fact(derive_binding_fact(
            source_version_id=sv.id, **fact_params
        ))
    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id,
        annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1",
        model_config_hash=sha256_hex("m"),
        payload={"semantic_units": [],
                 "document_metadata_claims": {"subject": "m", "grade": "3"}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    cand = await SnapshotRepository(session).create_admission_candidate(
        unit_type="standalone_unit", source_version_id=sv.id,
        annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=payload,
        gate_decision={"gate_policy_version": "admission-gate/v1",
                       "decision": "auto_approve",
                       "layers": {}, "reasons": []},
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    await EvidenceRepository(session).append_event(
        ev(claim), candidate_id=cand.id, source_version_id=sv.id
    )
    return sv, ann, cand


@pytest.fixture(autouse=True)
def _clean_registry():
    get_registry().clear()
    yield
    get_registry().clear()


async def _answers(session, sv_id):
    insts = (await session.execute(
        select(QuestionInstance).where(
            QuestionInstance.source_version_id == sv_id
        )
    )).scalars().all()
    rows = []
    for inst in insts:
        q = await session.get(Question, inst.question_id)
        for r in (await session.execute(
            select(InstanceRoleContent).where(
                InstanceRoleContent.instance_id == inst.id,
                InstanceRoleContent.role == "answer",
            )
        )).scalars().all():
            rows.append((inst.question_number, q.canonical_question_type, r.text,
                         (r.answer_status or {}).get("publish"),
                         (r.answer_status or {}).get("ownership")))
    return rows


class TestDSHR14:
    async def test_1_control_honest_q1_publishes(self, session):
        register_trusted_binding_fact(derive_binding_fact(
            span_id="sp-ans",
            source_version_id=SVID, unit_id="Q1", question_number="1",
            source_lines=["1. A"], answer_text="A",
        ))
        sv, ann, cand = await _seed(
            session, _leaf_payload(qn="1", ans_text="A", ans_qn="1"),
            sv_id=SVID,
        )
        await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        rows = await _answers(session, sv.id)
        print(f"\n[1 CONTROL] {rows}")
        assert rows and rows[0][2] == "A", rows

    async def test_2_forged_span_honest_qn_withheld(self, session):
        # fact belongs to printed question 2, but unit is question 1
        register_trusted_binding_fact(derive_binding_fact(
            span_id="sp-ans",
            source_version_id=SVID, unit_id="Q1", question_number="2",
            source_lines=["2. B"], answer_text="B",
        ))
        sv, ann, cand = await _seed(
            session, _leaf_payload(qn="1", ans_text="B", ans_qn="1"),
            sv_id=SVID,
        )
        await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        rows = await _answers(session, sv.id)
        print(f"\n[2 FORGED SPAN honest qn] {rows}")
        assert rows and rows[0][2] == "", rows

    async def test_3_duplicate_qn_cross_span_publishes_foreign_answer(self, session):
        """Two distinct questions both printed as '2' (sectional numbering).

        Unit A (stem '2. ...') owns fact sp-ans-a (qn 2, text A).  Unit B
        owns fact sp-ans-b (qn 2, text B).  The frozen payload wires unit
        A's answer entry to sp-ans-b.  No label is forged: every qn field
        is a legitimate '2'.  If the binding really proves "this answer
        belongs to this question", B's answer must not land on A.
        """
        register_trusted_binding_fact(derive_binding_fact(
            span_id="sp-ans-a",
            source_version_id=SVID, unit_id="Q2a", question_number="2",
            source_lines=["2. A"], answer_text="A",
        ))
        register_trusted_binding_fact(derive_binding_fact(
            span_id="sp-ans-b",
            source_version_id=SVID, unit_id="Q2b", question_number="2",
            source_lines=["2. B"], answer_text="B",
        ))
        sv, ann, cand = await _seed(
            session,
            _leaf_payload(unit_id="Q2a", qn="2",
                          stem="2. What is 2+2?",
                          ans_span="sp-ans-b", ans_text="B", ans_qn="2"),
            claim="Q2a",
        sv_id=SVID,
        )
        await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        rows = await _answers(session, sv.id)
        print(f"\n[3 DUPLICATE QN cross-span] {rows}")
        assert rows, "no answer row"
        # P0-R15 FIXED: unit_id check catches cross-unit fact reuse.
        # Foreign answer must NOT be published.
        assert rows[0][2] == "" or rows[0][3] != "official", rows

    async def test_4_composite_match_fact_withheld(self, session):
        payload = {
            "ir_snapshot": {"ir_schema": "semantic-question-ir/v0.3", "units": [
                {"unit_id": "U1-1", "unit_type": "composite_unit",
                 "question_number": "1", "question_number_range": "1-2",
                 "original_question_type": "single_choice", "content": [],
                 "shared_components": [], "relations": [],
                 "semantic_status": "ready", "sub_questions": [
                     {"unit_id": "Q1", "unit_type": "standalone_question",
                      "question_number": "1", "question_number_range": None,
                      "original_question_type": "single_choice",
                      "content": [{"role": "stem", "span_id": "sp-a"}],
                      "shared_components": [], "relations": [],
                      "semantic_status": "ready", "sub_questions": []},
                     {"unit_id": "Q2", "unit_type": "standalone_question",
                      "question_number": "2", "question_number_range": None,
                      "original_question_type": "single_choice",
                      "content": [{"role": "stem", "span_id": "sp-b"}],
                      "shared_components": [], "relations": [],
                      "semantic_status": "ready", "sub_questions": []},
                 ]},
                {"unit_id": "Q1", "unit_type": "standalone_question",
                 "question_number": "1", "question_number_range": None,
                 "original_question_type": "single_choice", "content": [],
                 "shared_components": [], "relations": [],
                 "semantic_status": "ready", "sub_questions": []},
                {"unit_id": "Q2", "unit_type": "standalone_question",
                 "question_number": "2", "question_number_range": None,
                 "original_question_type": "single_choice", "content": [],
                 "shared_components": [], "relations": [],
                 "semantic_status": "ready", "sub_questions": []},
            ]},
            "resolved_spans": [
                {"span_id": "sp-mat", "role": "material", "granularity": "line",
                 "line_refs": ["P1L001"], "start_offset": None, "end_offset": None,
                 "text_hash": sha256_hex("passage"), "resolution_status": "exact"},
                {"span_id": "sp-a", "role": "stem", "granularity": "line",
                 "line_refs": ["P1L002"], "start_offset": None, "end_offset": None,
                 "text_hash": sha256_hex("1. what is A?"), "resolution_status": "exact"},
                {"span_id": "sp-b", "role": "stem", "granularity": "line",
                 "line_refs": ["P1L003"], "start_offset": None, "end_offset": None,
                 "text_hash": sha256_hex("2. what is B?"), "resolution_status": "exact"},
            ],
            "compiled_roles": [
                {"role": "material", "span_id": "sp-mat", "line_refs": ["P1L001"],
                 "text": "passage", "text_hash": sha256_hex("passage"),
                 "label": None, "unit_id": "U1-1", "kind": "material"},
                {"role": "stem", "span_id": "sp-a", "line_refs": ["P1L002"],
                 "text": "1. what is A?", "text_hash": sha256_hex("1. what is A?"),
                 "label": None, "unit_id": "Q1", "kind": "content"},
                {"role": "option", "span_id": "sp-aA", "line_refs": ["P1L002"],
                 "text": "A. x", "text_hash": sha256_hex("A. x"), "label": "A",
                 "unit_id": "Q1", "kind": "content"},
                {"role": "stem", "span_id": "sp-b", "line_refs": ["P1L003"],
                 "text": "2. what is B?", "text_hash": sha256_hex("2. what is B?"),
                 "label": None, "unit_id": "Q2", "kind": "content"},
                {"role": "option", "span_id": "sp-bA", "line_refs": ["P1L003"],
                 "text": "A. x", "text_hash": sha256_hex("A. x"), "label": "A",
                 "unit_id": "Q2", "kind": "content"},
                {"role": "option", "span_id": "sp-bB", "line_refs": ["P1L003"],
                 "text": "B. y", "text_hash": sha256_hex("B. y"), "label": "B",
                 "unit_id": "Q2", "kind": "content"},
            ],
            "answer": [
                {"unit_id": "Q1", "question_number": "1", "span_id": "sp-aa",
                 "line_refs": ["P1L004"], "text": "A",
                 "text_hash": sha256_hex("A"), "source_located": True,
                 "complete": True, "verified_correct": None},
                {"unit_id": "Q2", "question_number": "2", "span_id": "sp-ab",
                 "line_refs": ["P1L005"], "text": "B",
                 "text_hash": sha256_hex("B"), "source_located": True,
                 "complete": True, "verified_correct": None},
            ],
            "figure_refs": [], "knowledge_links": [], "evidence": [],
            "display_hint": {"unit_type": "composite_unit",
                             "canonical_question_type": "single_choice"},
        }
        register_trusted_binding_fact(derive_binding_fact(
            span_id="sp-aa",
            source_version_id=SVID, unit_id="Q1", question_number="1",
            source_lines=["1. A"], answer_text="A",
        ))
        register_trusted_binding_fact(derive_binding_fact(
            span_id="sp-ab",
            source_version_id=SVID, unit_id="Q2", question_number="2",
            source_lines=["2. B"], answer_text="B",
        ))
        sv, ann, cand = await _seed(session, payload, claim="U1-1", sv_id=SVID)
        await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        rows = await _answers(session, sv.id)
        would = _publish_decision(
            ownership="match", candidate_text="A", grant="auto_gate",
            review_evidence=None, content_ok=True, source_ok=True,
        )
        print(f"\n[4 COMPOSITE] rows={rows} r13_would_publish={would}")
        assert rows, "no composite answer rows"
        # P0-R15 FIXED: composite answers preserved child qn, now publish.
        assert all(r[2] != "" for r in rows), rows

    async def test_6_honest_qn_forged_ans_qn_repo_rejects(self, session):
        """Isolate the _ans_qn transport preference: unit qn honest 1,
        ans.question_number forged to 2 -> _materialize says match, only
        the Repository DB check blocks it."""
        register_trusted_binding_fact(derive_binding_fact(
            span_id="sp-ans",
            source_version_id=SVID, unit_id="Q1", question_number="2",
            source_lines=["2. B"], answer_text="B",
        ))
        sv, ann, cand = await _seed(
            session,
            _leaf_payload(qn="1", stem="1. what is capital of France?",
                          ans_text="B", ans_qn="2"),
        sv_id=SVID,
        )
        # P0-R15 FIXED: unit qn=1 but fact qn=2 → auxiliary qn check
        # withholds. No RepositoryError needed — _materialize blocks it.
        await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        rows = await _answers(session, sv.id)
        print(f"\n[6 HONEST QN forged ans qn] rows={rows}")
        assert rows, "no answer row"
        assert rows[0][2] == "" or rows[0][3] != "official", rows

    async def test_5_empty_unit_qn_guard_inert(self, session):
        register_trusted_binding_fact(derive_binding_fact(
            span_id="sp-ans",
            source_version_id=SVID, unit_id="Q1", question_number="2",
            source_lines=["2. B"], answer_text="B",
        ))
        sv, ann, cand = await _seed(
            session,
            _leaf_payload(qn="", stem="what is A?", ans_text="B", ans_qn=""),
        sv_id=SVID,
        )
        await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        rows = await _answers(session, sv.id)
        print(f"\n[5 EMPTY QN] {rows}")
        assert rows, "no answer row"
        assert rows[0][2] == "B" and rows[0][3] == "official", rows
