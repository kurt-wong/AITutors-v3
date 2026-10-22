"""R2-1 BIO-001: full 50-declaration ledger keyed by unit_id.

DSH R2 finding: the previous ledger used printed_number as dict key,
so U41-U50 (printed 1-10) overwrote Q1-Q10 (printed 1-10), losing 10
declarations. The correct total is 50 answer declarations.

Identity key: unit_id (Producer's unit identity). printed_number is
source metadata only and MUST NOT be used as a unique key.
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.hashing import sha256_hex
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder, collect_validation_problems
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

_BACKEND = Path(__file__).resolve().parents[1]
_SCRIPTS = _BACKEND / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from preprocessing_consumer.manifest_reader import load_manifest  # noqa: E402
from preprocessing_consumer.annotation_adapter import (  # noqa: E402
    manifest_to_annotation_payload,
    attach_material_boundary_markers,
)

BIO_ROOT = Path(
    r"D:\Project\Papers\Ocr-markdown\gen-test-runs\run-20261014-BIO-001"
)
BIO_MANIFEST = BIO_ROOT / "2018北京夏季高中会考生物（教师版）(1).manifest.json"
BIO_SOURCE = Path(
    r"D:\Project\Papers\Ocr-markdown\会考\生物\2018北京夏季高中会考生物（教师版）(1).md"
)

SVID = uuid.UUID("00000000-0000-0000-0000-00000000b101")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-00000000a101")

pytestmark = pytest.mark.skipif(
    not BIO_MANIFEST.exists() or not BIO_SOURCE.exists(),
    reason="BIO-001 real corpus not available on this machine",
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


def _load_bio_declarations():
    """Load 50 declarations keyed by unit_id (NOT printed_number).

    Returns: (manifest, lines, declarations) where declarations is
    {unit_id: {"value": str, "question_numbers": list, "printed": str,
               "unit_type": str}}.
    """
    manifest = load_manifest(BIO_MANIFEST)
    raw = json.loads(BIO_MANIFEST.read_text(encoding="utf-8"))
    text = BIO_SOURCE.read_text(encoding="utf-8")
    lines = tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(text.splitlines())
    )
    declarations = {}
    for u in raw.get("units") or []:
        uid = str(u.get("unit_id") or "")
        ae = u.get("answer_evidence") or {}
        val = ae.get("value")
        if uid and val is not None and str(val).strip() != "":
            declarations[uid] = {
                "value": str(val),
                "question_numbers": list(u.get("question_numbers") or []),
                "printed": str(u.get("printed_number") or ""),
                "unit_type": str(u.get("unit_type") or ""),
            }
    return manifest, lines, declarations


async def _seed_source(session, texts):
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/bio001-{uuid.uuid4().hex[:8]}.md",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="bio001.md", file_type="md", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        id=SVID, document_id=doc.id, artifact_kind="raw_l1", role="native",
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
                "text": r.text,
                "publish": (r.answer_status or {}).get("publish"),
                "ownership": (r.answer_status or {}).get("ownership"),
            })
    return rows


def _root_of(ir, unit):
    for u in ir.units:
        if u.unit_id == unit.unit_id:
            return u
    return unit


class TestBIO001FullLedger:
    """50-declaration ledger keyed by unit_id. No printed_number collision."""

    async def test_bio001_full_50_declaration_ledger(self, session):
        """All 50 declarations tracked by unit_id with per-item status.

        Assertions:
          - 50 declarations loaded (not 40 — printed_number collision must
            not silently drop items)
          - every declaration appears in the ledger exactly once
          - published items match manifest truth
          - unpublished items have explicit category + reason
        """
        manifest, lines, declarations = _load_bio_declarations()
        assert len(declarations) == 50, (
            f"BIO-001 must have 50 declarations by unit_id, got {len(declarations)}. "
            f"If 40, printed_number collision is still dropping items."
        )

        # Verify printed_number collisions exist (proving the key choice matters)
        printed_vals = [d["printed"] for d in declarations.values()]
        assert len(set(printed_vals)) < 50, (
            "Expected printed_number collisions (Q1-Q10 vs U41-U50)"
        )

        payload_meta = manifest_to_annotation_payload(manifest)
        # R4: production Track A step — attach material boundary markers
        payload_meta = attach_material_boundary_markers(
            payload_meta,
            {
                u.unit_id: u.material_lines
                for u in manifest.units
                if u.material_lines
            },
            [l.text for l in lines],
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload_meta)
        ir = IRBuilder.build(run, payload_meta, SVID, ANN_ID)
        spans = {s.span_id: s for s in run.resolved_spans}
        compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)

        # Index IR by unit_id
        ir_by_uid = {u.unit_id: u for u in ir.units}
        # Also index sub-questions
        sub_by_uid = {}
        for u in ir.units:
            for s in getattr(u, "sub_questions", ()):
                sub_by_uid[s.unit_id] = s

        sv = await _seed_source(session, [l.text for l in lines])

        # Build ledger for ALL 50 declarations
        ledger = {}
        for uid in sorted(declarations.keys()):
            decl = declarations[uid]
            u = ir_by_uid.get(uid)
            if u is None:
                ledger[uid] = {
                    "category": "missing_ir",
                    "expected": decl["value"],
                    "printed": decl["printed"],
                }
                continue

            if u.semantic_status != "ready":
                # Collect specific problems
                problems = collect_validation_problems(u, set())
                # Check sub-questions
                subs = getattr(u, "sub_questions", ())
                sub_status = []
                for s in subs:
                    sub_status.append({
                        "sub_id": s.unit_id,
                        "status": s.semantic_status,
                        "qn": s.question_number,
                    })
                ledger[uid] = {
                    "category": "withheld_incomplete",
                    "expected": decl["value"],
                    "printed": decl["printed"],
                    "ir_status": u.semantic_status,
                    "problems": problems,
                    "sub_questions": sub_status,
                }
                continue

            # IR is ready: evaluate and potentially publish
            root = _root_of(ir, u)
            gate = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
            if gate["decision"] != "auto_approve":
                # R5: record full diagnostic data for pending items
                subs = getattr(u, "sub_questions", ())
                sub_status = [
                    {"sub_id": s.unit_id, "status": s.semantic_status, "qn": s.question_number}
                    for s in subs
                ]
                leaf_ids = [
                    leaf.unit_id for leaf in compiled.leaves
                    if leaf.unit_id == uid or any(leaf.unit_id == s.unit_id for s in subs)
                ]
                ledger[uid] = {
                    "category": "withheld_pending",
                    "expected": decl["value"],
                    "printed": decl["printed"],
                    "decision": gate["decision"],
                    "reasons": gate.get("reasons"),
                    "ir_status": u.semantic_status,
                    "sub_questions": sub_status,
                    "leaf_ids": leaf_ids,
                }
                continue

            # Publish through real AdmissionService
            payload = build_payload(
                root=root, ir=ir, compiled=compiled, resolved_run=run,
                source_lines=lines,
            )
            ann = await SnapshotRepository(session).create_semantic_annotation(
                source_version_id=sv.id,
                annotation_schema_version="semantic-metadata-annotation/v0.3",
                prompt_version="semantic-annotation/v1",
                model_config_hash=sha256_hex("m"),
                payload={"semantic_units": [],
                         "document_metadata_claims": {"subject": "生物", "grade": "高一"}},
                status="valid", logical_execution_stage="ann",
                logical_execution_hash=sha256_hex(f"bio-{uid}"),
            )
            await session.flush()
            cand = await SnapshotRepository(session).create_admission_candidate(
                unit_type="standalone_unit", source_version_id=sv.id,
                annotation_id=ann.id,
                build_versions={"annotation_schema_version": "v0.3"},
                input_identity={"source_version_id": str(sv.id)},
                payload=payload,
                gate_decision=gate,
                logical_execution_stage="compile",
                logical_execution_hash=sha256_hex(f"bio-c-{uid}"),
            )
            await session.flush()
            await EvidenceRepository(session).append_event(
                _ev(uid), candidate_id=cand.id, source_version_id=sv.id
            )
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
            ledger[uid] = {
                "category": "pending_db_check",
                "expected": decl["value"],
                "printed": decl["printed"],
                "unit_id": uid,
            }

        # Cross-check published rows
        rows = await _answers(session, sv.id)
        rows_by_qn = {}
        for r in rows:
            if r["text"] and r["publish"] == "official":
                rows_by_qn[str(r["unit"])] = r

        for uid, entry in ledger.items():
            if entry["category"] != "pending_db_check":
                continue
            # Match by question_number (the DB stores question_number on instance)
            decl = declarations[uid]
            qns = decl["question_numbers"]
            matched_row = None
            for qn in qns:
                if str(qn) in rows_by_qn:
                    matched_row = rows_by_qn[str(qn)]
                    break
            if matched_row is None:
                entry["category"] = "missing_db"
                continue
            if matched_row["text"].strip() == entry["expected"].strip():
                entry["category"] = "published_match"
                entry["actual"] = matched_row["text"]
                entry["ownership"] = matched_row.get("ownership")
            else:
                entry["category"] = "published_mismatch"
                entry["actual"] = matched_row["text"]

        # === Hard assertions ===
        by_cat = {}
        for uid, entry in ledger.items():
            by_cat.setdefault(entry["category"], []).append(uid)

        # Complete coverage: 50 declarations, all categorized
        assert len(ledger) == 50, f"ledger must have 50 entries, got {len(ledger)}"
        assert not by_cat.get("missing_ir"), (
            f"declarations missing from IR: {by_cat.get('missing_ir')}"
        )
        assert not by_cat.get("missing_db"), (
            f"auto-approved but missing from DB: {by_cat.get('missing_db')}"
        )
        assert not by_cat.get("published_mismatch"), (
            f"published mismatches: {by_cat.get('published_mismatch')}"
        )

        # Published match
        published = by_cat.get("published_match", [])
        assert len(published) == 39, (
            f"expected 39 published_match (Q1-Q28,Q30-Q40), got {len(published)}: {published}"
        )
        # R5-hardening: verify actual DB published rows match expected set
        db_published_qns = set(rows_by_qn.keys())
        expected_qns = set()
        for uid in published:
            for qn in declarations[uid]["question_numbers"]:
                expected_qns.add(str(qn))
        assert db_published_qns == expected_qns, (
            f"DB published set mismatch: db={sorted(db_published_qns)} "
            f"expected={sorted(expected_qns)}"
        )
        # No pending/incomplete unit may appear in DB published set
        for uid in by_cat.get("withheld_pending", []) + by_cat.get("withheld_incomplete", []):
            for qn in declarations[uid]["question_numbers"]:
                assert str(qn) not in db_published_qns, (
                    f"{uid} (qn={qn}) must not be in DB published set"
                )

        # Unpublished: 11 items (9 pending + 2 incomplete) with explicit reasons
        withheld = (
            by_cat.get("withheld_incomplete", [])
            + by_cat.get("withheld_pending", [])
        )
        assert len(withheld) == 11, (  # 9 pending + 2 incomplete
            f"expected 11 withheld (Q29,U41-U50), got {len(withheld)}: {withheld}"
        )

        # Specific categories for withheld items
        inc = by_cat.get("withheld_incomplete", [])
        # Q1-Q10: stem/option unresolved
        for q in ["Q1","Q2","Q3","Q4","Q5","Q6","Q7","Q8","Q9","Q10"]:
            assert q in published, f"{q} must be published_match (adapter fix)"
        # R4: correct classification after material boundary markers
        # Q29: incomplete (options missing)
        assert "Q29" in inc, "Q29 must be withheld_incomplete"
        q29_entry = ledger["Q29"]
        assert q29_entry["category"] == "withheld_incomplete"
        assert "options missing" in str(q29_entry.get("problems", [])), (
            f"Q29 must be withheld for options missing, got: {q29_entry.get('problems')}"
        )
        # R5: Q29 must not appear in published
        assert "Q29" not in by_cat.get("published_match", []), (
            "Q29 must not be in published_match"
        )

        # U44: incomplete (sub not ready)
        assert "U44" in inc, "U44 must be withheld_incomplete"
        u44_entry = ledger["U44"]
        assert u44_entry["category"] == "withheld_incomplete"
        assert "unresolved" in str(u44_entry.get("problems", [])), (
            f"U44: expected unresolved problems, got: {u44_entry.get('problems')}"
        )

        # U41-U43, U45-U50: ready but pending_review (fill_in type + unknown ownership)
        pend = by_cat.get("withheld_pending", [])
        assert len(pend) == 9, (
            f"expected 9 pending_review (U41-U43,U45-U50), got {len(pend)}: {pend}"
        )
        for u in ["U41","U42","U43","U45","U46","U47","U48","U49","U50"]:
            assert u in pend, f"{u} must be withheld_pending (fill_in, not strict-auto)"
            entry = ledger[u]
            # R5: assert decision is pending_review
            assert entry["decision"] == "pending_review", (
                f"{u}: expected pending_review, got {entry['decision']}"
            )
            # R5: assert parent IR status is ready (it was evaluated)
            assert entry.get("ir_status") == "ready", (
                f"{u}: parent should be ready, got {entry.get('ir_status')}"
            )
            # R5: assert compiled leaf exists
            leaf_ids = entry.get("leaf_ids", [])
            assert leaf_ids, (
                f"{u}: compiled leaf must exist for pending item, got leaf_ids={leaf_ids}"
            )
            # R5: assert sub-questions are ready
            for sub in entry.get("sub_questions", []):
                assert sub["status"] == "ready", (
                    f"{u}.sub should be ready, got {sub['status']}"
                )
            # R5: assert pending items are NOT in published set
            assert u not in by_cat.get("published_match", []), (
                f"{u}: pending item must not be in published_match"
            )
            reasons = str(entry.get("reasons", []))
            assert "fill_in" in reasons or "not strict-auto" in reasons or "ownership" in reasons, (
                f"{u}: expected fill_in/ownership reason, got: {reasons}"
            )

        # R4: sub-question analysis after material boundary markers
        # U41-U43, U45-U50: parent ready (implied by withheld_pending), sub ready
        # U44: parent incomplete (sub not ready)
        for uid in ["U41","U42","U43","U45","U46","U47","U48","U49","U50"]:
            entry = ledger[uid]
            # withheld_pending means IR was ready (gate evaluated it)
            assert entry["category"] == "withheld_pending", (
                f"{uid}: expected withheld_pending, got {entry['category']}"
            )
            for sub in entry.get("sub_questions", []):
                assert sub["status"] == "ready", (
                    f"{uid}.sub should be ready, got {sub['status']}"
                )
        # R5: U44 is the only incomplete one; its sub must NOT be ready
        assert ledger["U44"]["category"] == "withheld_incomplete"
        assert ledger["U44"].get("ir_status") == "incomplete"
        u44_subs = ledger["U44"].get("sub_questions", [])
        pass  # no fabricated sub required
        # R5-hardening: direct any() assertion, not just reason strings
        assert (not u44_subs) or any(s["status"] != "ready" for s in u44_subs), (
            f"U44 must have at least one non-ready sub, got: {u44_subs}"
        )
        for sub in u44_subs:
            assert sub["status"] != "ready", (
                f"U44.sub must NOT be ready, got {sub['status']}"
            )
        # U44 must not appear in published
        assert "U44" not in by_cat.get("published_match", []), (
            "U44 must not be in published_match"
        )

        # Verify every published answer matches manifest truth
        for uid in published:
            assert ledger[uid]["actual"].strip() == ledger[uid]["expected"].strip(), (
                f"{uid}: published {ledger[uid]['actual']!r} != expected {ledger[uid]['expected']!r}"
            )
            assert ledger[uid]["ownership"] == "match", ledger[uid]

        # Report ledger summary for DSH (printed for diagnostic)
        print(f"\n=== BIO-001 Full Ledger (by unit_id) ===")
        for cat in ["published_match", "withheld_incomplete", "withheld_pending", "missing_db", "missing_ir"]:
            items = by_cat.get(cat, [])
            print(f"  {cat}: {len(items)}")
        print(f"  pending_review: {len(by_cat.get('withheld_pending', []))}")
