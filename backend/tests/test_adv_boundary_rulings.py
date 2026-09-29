"""Adversarial audit: Owner (3) / matrix vs L0 and implementation. Real evidence."""
from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import inspect as sa_inspect, select

from app.core.hashing import sha256_hex
from app.domains.compile.snapshot import CompiledAnswer
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.gate.admission import AdmissionService
from app.models.content import InstanceRoleContent, QuestionInstance
from app.models.evidence import ValidationEventRecord
from app.models.source import DocumentSourceLine
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

REPO = Path(__file__).resolve().parents[2]  # AITutors-v3/


def ev(result="validated", at=None, claim="U1-1"):
    return ValidationEvent(
        event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=claim,
        validation_result=result,
        checks=(CheckResult(check_id="X", result="pass"),),
        validation_method="frozen_header_rule", validator="gate/v1",
        validated_at=at or datetime.now(timezone.utc),
    )


def _payload_composite_flat():
    """Mirror gate payload._ir_snapshot: units = (root,) + root.sub_questions."""
    sub_a = {
        "unit_id": "Q1", "unit_type": "standalone_question",
        "question_number": "1", "question_number_range": None,
        "original_question_type": "single_choice",
        "content": [{"role": "stem", "span_id": "sp-a", "label": None, "unsupported": False}],
        "shared_components": [], "relations": [],
        "semantic_status": "ready", "sub_questions": [],
    }
    sub_b = {
        "unit_id": "Q2", "unit_type": "standalone_question",
        "question_number": "2", "question_number_range": None,
        "original_question_type": "single_choice",
        "content": [{"role": "stem", "span_id": "sp-b", "label": None, "unsupported": False}],
        "shared_components": [], "relations": [],
        "semantic_status": "ready", "sub_questions": [],
    }
    root = {
        "unit_id": "U1-1", "unit_type": "composite_unit",
        "question_number": "1", "question_number_range": "1-2",
        "original_question_type": "single_choice",
        "content": [],
        "shared_components": [{"role": "material", "span_id": "sp-mat", "label": None, "unsupported": False}],
        "relations": [], "semantic_status": "ready",
        "sub_questions": [sub_a, sub_b],
    }
    return {
        "ir_snapshot": {
            "ir_schema": "semantic-question-ir/v0.3",
            "units": [root, sub_a, sub_b],  # FLAT + nested, as payload.py
        },
        "resolved_spans": [
            {"span_id": "sp-mat", "role": "material", "granularity": "line",
             "line_refs": ["P1L001"], "start_offset": None, "end_offset": None,
             "text_hash": "0"*64, "resolution_status": "exact"},
            {"span_id": "sp-a", "role": "stem", "granularity": "line",
             "line_refs": ["P1L002"], "start_offset": None, "end_offset": None,
             "text_hash": "0"*64, "resolution_status": "exact"},
            {"span_id": "sp-b", "role": "stem", "granularity": "line",
             "line_refs": ["P1L003"], "start_offset": None, "end_offset": None,
             "text_hash": "0"*64, "resolution_status": "exact"},
        ],
        "compiled_roles": [
            {"role": "material", "span_id": "sp-mat", "line_refs": ["P1L001"],
             "text": "shared", "text_hash": sha256_hex("shared"),
             "label": None, "unit_id": "U1-1", "kind": "material"},
            {"role": "stem", "span_id": "sp-a", "line_refs": ["P1L002"],
             "text": "q1 stem", "text_hash": sha256_hex("q1 stem"),
             "label": None, "unit_id": "Q1", "kind": "content"},
            {"role": "option", "span_id": "sp-aA", "line_refs": ["P1L002"],
             "text": "A. x", "text_hash": sha256_hex("A. x"),
             "label": "A", "unit_id": "Q1", "kind": "content"},
            {"role": "option", "span_id": "sp-aB", "line_refs": ["P1L002"],
             "text": "B. y", "text_hash": sha256_hex("B. y"),
             "label": "B", "unit_id": "Q1", "kind": "content"},
            {"role": "stem", "span_id": "sp-b", "line_refs": ["P1L003"],
             "text": "q2 stem", "text_hash": sha256_hex("q2 stem"),
             "label": None, "unit_id": "Q2", "kind": "content"},
            {"role": "option", "span_id": "sp-bA", "line_refs": ["P1L003"],
             "text": "A. x", "text_hash": sha256_hex("A. x"),
             "label": "A", "unit_id": "Q2", "kind": "content"},
            {"role": "option", "span_id": "sp-bB", "line_refs": ["P1L003"],
             "text": "B. y", "text_hash": sha256_hex("B. y"),
             "label": "B", "unit_id": "Q2", "kind": "content"},
        ],
        "answer": [
            {"unit_id": "Q1", "question_number": "1", "span_id": "sp-aa",
             "line_refs": ["P1L004"], "text": "A1", "text_hash": sha256_hex("A1"),
             "source_located": True, "complete": True, "verified_correct": None},
            {"unit_id": "Q2", "question_number": "2", "span_id": "sp-ab",
             "line_refs": ["P1L005"], "text": "A2", "text_hash": sha256_hex("A2"),
             "source_located": True, "complete": True, "verified_correct": None},
        ],
        "figure_refs": [], "knowledge_links": [], "evidence": [],
        "display_hint": {"unit_type": "composite_unit", "canonical_question_type": "single_choice"},
    }


async def seed_composite(session):
    texts = ("shared", "q1 stem", "q2 stem", "A1", "A2")
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
        unit_type="composite_unit", source_version_id=sv.id, annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=_payload_composite_flat(),
        gate_decision={"gate_policy_version": "admission-gate/v1", "decision": "auto_approve",
                       "layers": {}, "reasons": []},
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann, cand


class TestCompositePathReal:
    """(3) claims multi-part via sub_questions = N Instance x 1 Answer."""

    async def test_composite_two_subs_two_instances_one_answer_each(self, session):
        sv, ann, cand = await seed_composite(session)
        repo = EvidenceRepository(session)
        await repo.append_event(ev(claim="U1-1"), candidate_id=cand.id, source_version_id=sv.id)
        svc = AdmissionService(session)
        result = await svc.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
        print(f"\n[COMPOSITE] status={result.decision_status!r}")
        assert result.decision_status == "approved"
        insts = (await session.execute(
            select(QuestionInstance).where(QuestionInstance.source_version_id == sv.id)
        )).scalars().all()
        print(f"[COMPOSITE] instances={len(insts)}")
        assert len(insts) == 2
        for inst in insts:
            rows = (await session.execute(
                select(InstanceRoleContent).where(
                    InstanceRoleContent.instance_id == inst.id,
                    InstanceRoleContent.role == "answer",
                )
            )).scalars().all()
            print(f"[COMPOSITE] inst={inst.id} answers={[(r.role_index, r.text) for r in rows]}")
            assert len(rows) == 1 and rows[0].role_index == 0


class TestNValuesAbsent:
    def test_no_values_on_compiled_answer(self):
        fields = {f.name for f in dataclasses.fields(CompiledAnswer)}
        assert "values" not in fields
        print(f"\n[NVAL] CompiledAnswer fields={sorted(fields)}")

    def test_no_value_cols_on_validation_events(self):
        cols = {c.name for c in sa_inspect(ValidationEventRecord).columns}
        assert not any(c.startswith("value") for c in cols)
        print(f"[NVAL] ve cols ok")


class TestL0ConflictWithOwner3:
    """HIT probe: does Owner (3) contradict frozen L0 OD-R-01 text?"""

    def test_l0_forbids_n_instances_for_multiblank(self):
        t10 = (REPO / "Docs/V3_SPEC/10_Data_Model.md").read_text(encoding="utf-8")
        # frozen OD-R-01
        assert "三个空**不是**三个 QuestionInstance" in t10
        assert "多个有序值" in t10
        print("\n[L0] 10_Data_Model forbids 3 blanks = 3 QuestionInstance; requires ordered values")

    def test_owner3_in_ledger_says_n_instances(self):
        t84 = (REPO / "Docs/DECISIONS/84_CONFLICT_LEDGER.md").read_text(encoding="utf-8")
        assert "N Instance × 1 Answer" in t84 or "N Instance x 1 Answer" in t84
        assert "sub_questions" in t84
        print("[LEDGER] D-07 DECIDED (3) = sub_questions / N Instance")

    def test_conflict_is_live(self):
        """Both statements present => live Frozen Spec vs Owner Decision conflict."""
        t10 = (REPO / "Docs/V3_SPEC/10_Data_Model.md").read_text(encoding="utf-8")
        t84 = (REPO / "Docs/DECISIONS/84_CONFLICT_LEDGER.md").read_text(encoding="utf-8")
        l0 = "三个空**不是**三个 QuestionInstance" in t10
        o3 = ("N Instance × 1 Answer" in t84) or ("N Instance x 1 Answer" in t84)
        print(f"\n[CONFLICT] L0_forbids_N_instances={l0} Owner3_implies_N_instances={o3}")
        assert l0 and o3, "expected both sides present for conflict"
        # This test PASSES when conflict exists — documents the HIT.


class TestMatrixPaths:
    def test_matrix_and_clarification_exist(self):
        t = (REPO / "Docs/COORDINATION/LIMITED-IMPLEMENTATION-AUTHORIZATION-v0.3.md").read_text(encoding="utf-8")
        i_forb = t.find("- V3 production code modification")
        i_clar = t.find("Scope clarification")
        i_mat = t.find("## 6A. Implementation Boundary Matrix")
        print(f"\n[MATRIX] forb@{i_forb} clar@{i_clar} mat@{i_mat} order_ok={i_forb < i_clar < i_mat}")
        assert i_forb > 0 and i_clar > i_forb and i_mat > i_clar
        assert "N-values" in t
