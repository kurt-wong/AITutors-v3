"""R16c real Gate→Admission→DB e2e.

DSH R16b requirement: policy.evaluate must return auto_approve for legal
range/compact/per-line answers, then approve→_materialize→DB.
Fixtures MUST NOT hand-write gate_decision=auto_approve.

Also covers:
  A8 cross-SV isolation through the real chain
  negative: foreign/unknown must NOT auto_approve
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.core.hashing import sha256_hex
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.gate.admission import AdmissionService
from app.domains.gate.binding_fact import get_registry
from app.domains.gate.payload import build as build_payload
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from app.models.source import DocumentSourceLine
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

SVID = uuid.UUID("00000000-0000-0000-0000-00000000e2e1")
SVID_B = uuid.UUID("00000000-0000-0000-0000-00000000e2e2")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-00000000a2e1")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


@pytest.fixture(autouse=True)
def _clean_registry():
    get_registry().clear()
    yield
    get_registry().clear()


def _ev(claim: str) -> ValidationEvent:
    return ValidationEvent(
        event_id=f"ve-{uuid.uuid4().hex[:8]}",
        claim_id=claim,
        validation_result="validated",
        checks=(CheckResult(check_id="X", result="pass"),),
        validation_method="frozen_header_rule",
        validator="gate/v1",
        validated_at=datetime.now(timezone.utc),
    )


def _single_choice_payload(qn: int, *, answer_lines, question_type="single_choice",
                           options="ABCD", unit_prefix="Q"):
    return {
        "semantic_units": [
            {
                "unit_id": f"{unit_prefix}{qn}",
                "unit_type": "standalone_unit",
                "original_question_type": question_type,
                "content": {
                    "stem": {"question_label": str(qn)},
                    "options": [{"label": l} for l in options],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": str(qn),
                        "answer_lines": list(answer_lines),
                    },
                },
            }
        ]
    }


def _range_payload(start: int, end: int, *, answer_lines, options="ABCD",
                   question_type="single_choice"):
    return {
        "semantic_units": [
            {
                "unit_id": f"Q{n}",
                "unit_type": "standalone_unit",
                "original_question_type": question_type,
                "content": {
                    "stem": {"question_label": str(n)},
                    "options": [{"label": l} for l in options],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": str(n),
                        "answer_lines": list(answer_lines),
                    },
                },
            }
            for n in range(start, end + 1)
        ]
    }


def _resolve_compile_evaluate(lines, meta, svid=SVID, ann_id=ANN_ID):
    """Real E→F→G path. Returns (run, ir, compiled, gate_per_root)."""
    run = SourceResolver(source_version_id=svid, lines=lines).resolve(meta)
    ir = IRBuilder.build(run, meta, svid, ann_id)
    spans = {s.span_id: s for s in run.resolved_spans}
    compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
    gates = {}
    for root in ir.units:
        gates[root.unit_id] = evaluate(
            root=root, ir=ir, compiled=compiled, resolved_run=run
        )
    return run, ir, compiled, gates


async def _seed_source(session, texts, svid):
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="g.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        id=svid, document_id=doc.id, artifact_kind="raw_l1", role="native",
        provider="native", body_text="\n".join(texts),
        body_hash=sha256_hex(list(texts)), integrity_hash=sha256_hex(list(texts)),
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
    return sv


async def _seed_candidate(session, sv, payload, gate, unit_id, claim):
    """Create candidate with the REAL gate result (never hand-written)."""
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
        gate_decision=gate,  # REAL evaluate() output
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    await EvidenceRepository(session).append_event(
        _ev(claim), candidate_id=cand.id, source_version_id=sv.id
    )
    return ann, cand


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
            rows.append({
                "unit": inst.question_number,
                "type": q.canonical_question_type,
                "text": r.text,
                "publish": (r.answer_status or {}).get("publish"),
                "ownership": (r.answer_status or {}).get("ownership"),
            })
    return rows


class TestRealGateAdmissionDB:
    async def test_per_line_auto_approve_and_publish(self, session):
        """Real evaluate → auto_approve → approve → DB. No hand-written gate."""
        lines = _mk(
            "1. What is A?", "A. a", "B. b", "C. c", "D. d",
            "答案", "1. B",
        )
        meta = _single_choice_payload(1, answer_lines=[7, 7])
        run, ir, compiled, gates = _resolve_compile_evaluate(lines, meta)

        root_id = ir.units[0].unit_id
        gate = gates[root_id]
        # KEY: real evaluate says auto_approve (fixture does NOT write this)
        assert gate["decision"] == "auto_approve", gate["reasons"]

        # compiled ownership must already be match (R16c write-back)
        leaf = compiled.leaves[0]
        assert leaf.answer is not None
        assert leaf.answer.ownership == "match", leaf.answer.ownership

        sv = await _seed_source(session, [l.text for l in lines], SVID)
        payload = build_payload(
            root=ir.units[0], ir=ir, compiled=compiled, resolved_run=run,
        )
        # Tamper-proof: gate_decision comes from evaluate, not the fixture
        assert payload is not None
        _, cand = await _seed_candidate(session, sv, payload, gate, root_id, root_id)

        await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        rows = await _answers(session, sv.id)
        assert rows, "no answer rows"
        assert rows[0]["text"] == "B", rows
        assert rows[0]["publish"] == "official", rows
        assert rows[0]["ownership"] == "match", rows

    async def test_range_key_auto_approve_and_publish(self, session):
        """B3 `19-23 DABCA` through real evaluate → approve → DB.

        Realistic fixture: five separate questions (19–23), each with its
        own stem + options, sharing one range answer key line.
        """
        lines = _mk(
            "19. What is Q19?", "A. a", "B. b", "C. c", "D. d",
            "20. What is Q20?", "A. a", "B. b", "C. c", "D. d",
            "21. What is Q21?", "A. a", "B. b", "C. c", "D. d",
            "22. What is Q22?", "A. a", "B. b", "C. c", "D. d",
            "23. What is Q23?", "A. a", "B. b", "C. c", "D. d",
            "答案", "19-23 DABCA",
        )
        meta = {
            "semantic_units": [
                {
                    "unit_id": f"Q{n}",
                    "unit_type": "standalone_unit",
                    "question_label": str(n),
                    "original_question_type": "single_choice",
                    "content": {
                        "stem": {"question_label": str(n)},
                        "options": [{"label": l} for l in "ABCD"],
                        "answer": {
                            "answer_zone": "answer_table",
                            "question_label": str(n),
                            "answer_lines": [27, 27],
                        },
                    },
                }
                for n in range(19, 24)
            ]
        }
        run, ir, compiled, gates = _resolve_compile_evaluate(lines, meta)

        ready = [u for u in ir.units if u.semantic_status == "ready"]
        assert len(ready) == 5, (
            f"range fixture must yield 5 ready units, got {len(ready)}"
        )

        expected = {"19": "D", "20": "A", "21": "B", "22": "C", "23": "A"}
        sv = await _seed_source(session, [l.text for l in lines], SVID)
        published = []
        for root in ready:
            gate = gates[root.unit_id]
            assert gate["decision"] == "auto_approve", (
                f"{root.unit_id}: {gate['decision']} {gate['reasons']}"
            )
            for leaf in compiled.leaves:
                if leaf.unit_id == root.unit_id and leaf.answer is not None:
                    assert leaf.answer.ownership == "match", (
                        f"{root.unit_id} compiled ownership="
                        f"{leaf.answer.ownership}"
                    )

            payload = build_payload(
                root=root, ir=ir, compiled=compiled, resolved_run=run,
            )
            _, cand = await _seed_candidate(
                session, sv, payload, gate, root.unit_id, root.unit_id
            )
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
            rows = await _answers(session, sv.id)
            for r in rows:
                published.append(r)

        assert published, "no published rows"
        by_unit = {r["unit"]: r for r in published}
        assert set(by_unit.keys()) == set(expected.keys()), (
            f"range published qns {sorted(by_unit)} != expected {sorted(expected)}"
        )
        for qn, letter in expected.items():
            assert by_unit[qn]["text"] == letter, (
                f"qn {qn}: expected {letter}, got {by_unit[qn]}"
            )
            assert by_unit[qn]["publish"] == "official", by_unit[qn]
            assert by_unit[qn]["ownership"] == "match", by_unit[qn]

    async def test_compact_key_auto_approve_and_publish(self, session):
        """B3 `FGDAE` through real evaluate → approve → DB.

        Realistic fixture: five separate questions (1–5), each with
        its own stem + 7 options, sharing one compact answer key line.
        """
        lines = _mk(
            "1. What is Q1?", "A. a", "B. b", "C. c", "D. d", "E. e", "F. f", "G. g",
            "2. What is Q2?", "A. a", "B. b", "C. c", "D. d", "E. e", "F. f", "G. g",
            "3. What is Q3?", "A. a", "B. b", "C. c", "D. d", "E. e", "F. f", "G. g",
            "4. What is Q4?", "A. a", "B. b", "C. c", "D. d", "E. e", "F. f", "G. g",
            "5. What is Q5?", "A. a", "B. b", "C. c", "D. d", "E. e", "F. f", "G. g",
            "答案", "FGDAE",
        )
        meta = {
            "semantic_units": [
                {
                    "unit_id": f"Q{i}",
                    "unit_type": "standalone_unit",
                    "question_label": str(i),
                    "original_question_type": "single_choice",
                    "content": {
                        "stem": {"question_label": str(i)},
                        "options": [{"label": l} for l in "ABCDEFG"],
                        "answer": {
                            "answer_zone": "answer_table",
                            "question_label": str(i),
                            "answer_lines": [42, 42],
                        },
                    },
                }
                for i in range(1, 6)
            ]
        }
        run, ir, compiled, gates = _resolve_compile_evaluate(lines, meta)
        ready = [u for u in ir.units if u.semantic_status == "ready"]
        assert len(ready) == 5, (
            f"compact fixture must yield 5 ready units, got {len(ready)}"
        )

        sv = await _seed_source(session, [l.text for l in lines], SVID)
        published = []
        for root in ready:
            gate = gates[root.unit_id]
            assert gate["decision"] == "auto_approve", (
                f"{root.unit_id}: {gate['decision']} {gate['reasons']}"
            )
            for leaf in compiled.leaves:
                if leaf.unit_id == root.unit_id and leaf.answer is not None:
                    assert leaf.answer.ownership == "match", (
                        f"{root.unit_id} compiled ownership="
                        f"{leaf.answer.ownership}"
                    )
            payload = build_payload(
                root=root, ir=ir, compiled=compiled, resolved_run=run,
            )
            _, cand = await _seed_candidate(
                session, sv, payload, gate, root.unit_id, root.unit_id
            )
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
            published.extend(await _answers(session, sv.id))

        assert published, "no published rows"
        # R16c-FIX: require the COMPLETE 5-question set with exact qn→letter
        # mapping. 'FGDAE' → 1:F, 2:G, 3:D, 4:A, 5:E.
        expected_compact = {"1": "F", "2": "G", "3": "D", "4": "A", "5": "E"}
        by_unit = {r["unit"]: r for r in published}
        assert set(by_unit.keys()) == set(expected_compact.keys()), (
            f"compact published qns {sorted(by_unit)} != "
            f"expected {sorted(expected_compact)}"
        )
        for qn, letter in expected_compact.items():
            assert by_unit[qn]["text"] == letter, (
                f"qn {qn}: expected {letter}, got {by_unit[qn]}"
            )
            assert by_unit[qn]["publish"] == "official", by_unit[qn]
            assert by_unit[qn]["ownership"] == "match", by_unit[qn]

    async def test_foreign_not_auto_approved(self, session):
        """Negative: `12. A` bound to Q1 must NOT auto_approve."""
        lines = _mk(
            "1. What is A?", "A. a", "B. b", "C. c", "D. d",
            "答案", "12. A",
        )
        meta = _single_choice_payload(1, answer_lines=[7, 7])
        run, ir, compiled, gates = _resolve_compile_evaluate(lines, meta)
        gate = gates[ir.units[0].unit_id]
        assert gate["decision"] != "auto_approve", (
            f"foreign answer must not auto_approve: {gate}"
        )
        # compiled ownership must reflect foreign, not match
        leaf = compiled.leaves[0]
        if leaf.answer is not None:
            assert leaf.answer.ownership != "match", leaf.answer.ownership

    async def test_a8_cross_sv_isolation_via_real_chain(self, session):
        """A8: same span_id across two SVs must not cross-contaminate.

        Real resolve on two different SourceVersions; facts registered
        under (SV, span). Publish path must use the Instance's own SV.
        """
        lines_a = _mk(
            "1. QA?", "A. a", "B. b", "C. c", "D. d",
            "答案", "1. A",
        )
        lines_b = _mk(
            "1. QB?", "A. a", "B. b", "C. c", "D. d",
            "答案", "1. B",
        )
        meta = _single_choice_payload(1, answer_lines=[7, 7])

        run_a, ir_a, comp_a, gates_a = _resolve_compile_evaluate(
            lines_a, meta, svid=SVID, ann_id=ANN_ID
        )
        run_b, ir_b, comp_b, gates_b = _resolve_compile_evaluate(
            lines_b, meta, svid=SVID_B,
            ann_id=uuid.UUID("00000000-0000-0000-0000-00000000a2e2"),
        )
        assert gates_a[ir_a.units[0].unit_id]["decision"] == "auto_approve"
        assert gates_b[ir_b.units[0].unit_id]["decision"] == "auto_approve"

        sv_a = await _seed_source(session, [l.text for l in lines_a], SVID)
        sv_b = await _seed_source(session, [l.text for l in lines_b], SVID_B)

        payload_a = build_payload(
            root=ir_a.units[0], ir=ir_a, compiled=comp_a, resolved_run=run_a
        )
        payload_b = build_payload(
            root=ir_b.units[0], ir=ir_b, compiled=comp_b, resolved_run=run_b
        )
        _, cand_a = await _seed_candidate(
            session, sv_a, payload_a, gates_a[ir_a.units[0].unit_id],
            ir_a.units[0].unit_id, ir_a.units[0].unit_id,
        )
        _, cand_b = await _seed_candidate(
            session, sv_b, payload_b, gates_b[ir_b.units[0].unit_id],
            ir_b.units[0].unit_id, ir_b.units[0].unit_id,
        )
        await AdmissionService(session).approve(
            candidate_id=cand_a.id, provenance={"source": "auto_gate"}
        )
        await AdmissionService(session).approve(
            candidate_id=cand_b.id, provenance={"source": "auto_gate"}
        )

        rows_a = await _answers(session, SVID)
        rows_b = await _answers(session, SVID_B)
        assert rows_a and rows_b
        assert rows_a[0]["text"] == "A", rows_a
        assert rows_b[0]["text"] == "B", rows_b
        # Same local span_id across SVs must not swap answers
        assert rows_a[0]["text"] != rows_b[0]["text"]
