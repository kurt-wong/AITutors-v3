"""R2-3: Replay contract — three distinct capabilities.

Frozen spec (00_Master_Spec.md P7 / 10_Data_Model.md §9):
  - Exact Replay: same input_identity + same build_versions
    → replay resolver→ir→compiler→gate → deterministic equivalent results.
    This is BUILD REPRODUCIBILITY, not re-publishing from Registry.
  - Rebuild: change version → new Derived Representation (normal evolution).

Three DISTINCT capabilities (must not be conflated):
  1. Deterministic rebuild (P7 Exact Replay): re-run full chain from
     same source+manifest → equivalent BindingFacts and gate decisions.
  2. New process approving old Candidate: Registry miss → safe withhold
     (NOT re-publish). This is the process-restart scenario.
  3. Safe withhold: production AdmissionService.approve/_materialize
     withholds when binding facts are unavailable.

No new tables. No production replay-and-republish.
"""
from __future__ import annotations

import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.binding_fact import (
    derive_binding_fact,
    get_registry,
    resolve_trusted_binding_fact,
    verify_binding_fact,
)
from app.domains.gate.payload import build as build_payload
from app.domains.gate.policy import partition_candidate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000c104")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-00000000a104")


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


def _resolve_range_case():
    """Real range-key case: `19-23 DABCA` → per-qn letters."""
    lines = _mk(
        "19. What is A?", "A. a", "B. b", "C. c", "D. d",
        "20. What is B?", "A. a", "B. b", "C. c", "D. d",
        "21. What is C?", "A. a", "B. b", "C. c", "D. d",
        "22. What is D?", "A. a", "B. b", "C. c", "D. d",
        "23. What is E?", "A. a", "B. b", "C. c", "D. d",
        "答案", "19-23 DABCA",
    )
    payload_meta = {
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
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload_meta)
    ir = IRBuilder.build(run, payload_meta, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
    return lines, run, ir, compiled, payload_meta


class TestP7ExactReplay:
    """P7 Exact Replay: same inputs → deterministic equivalent results."""

    def test_exact_replay_same_inputs_same_ownership(self):
        """Re-running the full chain from same source+manifest yields
        identical BindingFacts (ownership, answer_text_hash, decode_loc)."""
        # First run
        get_registry().clear()
        lines1, run1, ir1, comp1, meta = _resolve_range_case()
        facts1 = {}
        for s in run1.resolved_spans:
            if s.role != "answer":
                continue
            f = resolve_trusted_binding_fact(
                source_version_id=str(SVID), span_id=s.span_id
            )
            if f is not None:
                facts1[s.span_id] = f

        # Second run (fresh registry = simulate replay)
        get_registry().clear()
        lines2, run2, ir2, comp2, meta2 = _resolve_range_case()
        facts2 = {}
        for s in run2.resolved_spans:
            if s.role != "answer":
                continue
            f = resolve_trusted_binding_fact(
                source_version_id=str(SVID), span_id=s.span_id
            )
            if f is not None:
                facts2[s.span_id] = f

        assert facts1, "first run must produce facts"
        assert set(facts1.keys()) == set(facts2.keys()), (
            f"Exact Replay span_id drift: {set(facts1)} vs {set(facts2)}"
        )
        for sid in facts1:
            a, b = facts1[sid], facts2[sid]
            assert a.ownership == b.ownership, (
                f"{sid}: ownership drift {a.ownership} → {b.ownership}"
            )
            assert a.answer_text_hash == b.answer_text_hash, (
                f"{sid}: answer_text_hash drift"
            )
            assert a.decode_loc == b.decode_loc, (
                f"{sid}: decode_loc drift"
            )
            assert a.source_hash == b.source_hash, (
                f"{sid}: source_hash drift"
            )
            assert verify_binding_fact(b), f"{sid}: replayed fact fails verify"

    def test_exact_replay_same_gate_decisions(self):
        """Re-running yields same gate decisions (P7 determinism)."""
        from app.domains.gate.policy import evaluate

        get_registry().clear()
        lines1, run1, ir1, comp1, meta = _resolve_range_case()
        decisions1 = {}
        for u in ir1.units:
            if u.semantic_status == "ready":
                d = evaluate(root=u, ir=ir1, compiled=comp1, resolved_run=run1)
                decisions1[u.unit_id] = d["decision"]

        get_registry().clear()
        lines2, run2, ir2, comp2, meta2 = _resolve_range_case()
        decisions2 = {}
        for u in ir2.units:
            if u.semantic_status == "ready":
                d = evaluate(root=u, ir=ir2, compiled=comp2, resolved_run=run2)
                decisions2[u.unit_id] = d["decision"]

        assert decisions1, "first run must produce gate decisions"
        assert decisions1 == decisions2, (
            f"Exact Replay gate decision drift: {decisions1} vs {decisions2}"
        )


class TestProductionSafeWithhold:
    """New process approving old Candidate: Registry miss → safe withhold."""

    def test_registry_miss_returns_none(self):
        """resolve_trusted_binding_fact returns None on Registry miss."""
        lines, run, ir, comp, meta = _resolve_range_case()
        span_ids = [s.span_id for s in run.resolved_spans if s.role == "answer"]
        assert span_ids

        # Before clear: facts exist
        before = {
            sid: resolve_trusted_binding_fact(source_version_id=str(SVID), span_id=sid)
            for sid in span_ids
        }
        assert any(f is not None for f in before.values()), (
            "expected registered facts before clear"
        )

        # After clear: all None
        get_registry().clear()
        for sid in span_ids:
            f = resolve_trusted_binding_fact(source_version_id=str(SVID), span_id=sid)
            assert f is None, f"Registry miss must return None, got {f}"

    async def test_admission_materialize_withholds_on_registry_miss(self, session):
        """REAL AdmissionService.approve/_materialize withholds when
        binding facts are unavailable (Registry miss).

        This is the production process-restart scenario: a Candidate exists
        in DB, but the new process has no BindingFact Registry. The approve
        path must WITHHOLD (not re-publish).
        """
        from datetime import datetime, timezone

        from app.core.hashing import sha256_hex
        from app.domains.evidence.models import CheckResult, ValidationEvent
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.payload import build as build_payload
        from app.models.source import DocumentSourceLine
        from app.repositories.evidence_repository import EvidenceRepository
        from app.repositories.snapshot_repository import SnapshotRepository
        from app.repositories.source_repository import SourceRepository

        lines, run, ir, comp, meta = _resolve_range_case()

        # Seed source
        src = SourceRepository(session)
        doc = await src.create_document(
            original_object_key=f"obj/{uuid.uuid4()}.md",
            original_sha256=sha256_hex(str(uuid.uuid4())),
            file_name="t.md", file_type="md", upload_meta={},
            processing_status="sealed",
        )
        await session.flush()
        sv = await src.create_source_version(
            id=SVID, document_id=doc.id, artifact_kind="raw_l1", role="native",
            provider="native", body_text="\n".join(l.text for l in lines),
            body_hash=sha256_hex(list(l.text for l in lines)),
            integrity_hash=sha256_hex(list(l.text for l in lines)),
            page_count=1, line_count=len(lines), status="draft",
        )
        await session.flush()
        for i, t in enumerate(lines):
            await src.append_line(DocumentSourceLine(
                source_version_id=sv.id, line_ref=f"P1L{i+1:03d}", seq=i + 1,
                page_no=1, line_no_in_page=i + 1, text=t.text,
                block_type="text", line_hash=sha256_hex(t.text),
            ))
        await session.flush()
        await src.seal_version(sv.id)
        await session.flush()

        # Build payload and create candidate
        root = next(u for u in ir.units if u.semantic_status == "ready")
        payload = build_payload(root=root, ir=ir, compiled=comp, resolved_run=run)

        ann = await SnapshotRepository(session).create_semantic_annotation(
            source_version_id=sv.id,
            annotation_schema_version="semantic-metadata-annotation/v0.3",
            prompt_version="semantic-annotation/v1",
            model_config_hash=sha256_hex("m"),
            payload={"semantic_units": [], "document_metadata_claims": {}},
            status="valid", logical_execution_stage="ann",
            logical_execution_hash=sha256_hex("ann"),
        )
        await session.flush()
        cand = await SnapshotRepository(session).create_admission_candidate(
            unit_type="standalone_unit", source_version_id=sv.id,
            annotation_id=ann.id,
            build_versions={"annotation_schema_version": "v0.3"},
            input_identity={"source_version_id": str(sv.id)},
            payload=payload,
            gate_decision={"decision": "auto_approve"},
            logical_execution_stage="compile",
            logical_execution_hash=sha256_hex("compile"),
        )
        await session.flush()
        ev = ValidationEvent(
            event_id=f"ve-{uuid.uuid4().hex[:8]}",
            claim_id=root.unit_id,
            validation_result="validated",
            checks=(CheckResult(check_id="X", result="pass"),),
            validation_method="frozen_header_rule",
            validator="gate/v1",
            validated_at=datetime.now(timezone.utc),
        )
        await EvidenceRepository(session).append_event(
            ev, candidate_id=cand.id, source_version_id=sv.id
        )

        # Simulate new process: Registry is empty
        get_registry().clear()

        # Production approve path
        result = await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )

        # R3: assert DB state on Registry miss — no non-empty official answer.
        from sqlalchemy import select
        from app.models.content import InstanceRoleContent, QuestionInstance

        insts = (await session.execute(
            select(QuestionInstance).where(
                QuestionInstance.source_version_id == sv.id
            )
        )).scalars().all()
        official_nonempty = []
        all_answers = []
        for inst in insts:
            for r in (await session.execute(
                select(InstanceRoleContent).where(
                    InstanceRoleContent.instance_id == inst.id,
                    InstanceRoleContent.role == "answer",
                )
            )).scalars().all():
                status = r.answer_status or {}
                all_answers.append({
                    "text": r.text,
                    "publish": status.get("publish"),
                    "ownership": status.get("ownership"),
                })
                if r.text and status.get("publish") == "official":
                    official_nonempty.append(r)

        # R4: assert answer records EXIST (not a no-op approve)
        assert len(all_answers) > 0, (
            "approve must create answer records (even if withheld); "
            "no records = approve was a complete no-op"
        )
        # HARD ASSERTION: Registry miss must NOT produce non-empty official answers
        assert not official_nonempty, (
            f"Registry miss must withhold: found {len(official_nonempty)} "
            f"non-empty official answers: {official_nonempty}"
        )
        # Every answer must be either empty or non-official (withheld)
        for a in all_answers:
            if a["text"]:
                assert a["publish"] != "official", (
                    f"non-empty answer with official publish on Registry miss: {a}"
                )
                assert a["ownership"] in ("unknown", "foreign", None), (
                    f"unexpected ownership {a['ownership']} on Registry miss"
                )
            else:
                # Empty answer must have withheld/non-official publish status
                assert a["publish"] in ("withheld_review", "pending", None, ""), (
                    f"empty answer must be withheld, got publish={a['publish']}"
                )


class TestCapabilityBoundary:
    """Explicit tri-state documentation test."""

    def test_three_capabilities_documented(self):
        """Three DISTINCT capabilities, must not be conflated:

        1. Exact Replay (P7): re-run full chain from same inputs
           → deterministic equivalent results. PROVEN by TestP7ExactReplay.
        2. New process approve old Candidate: Registry miss → safe withhold.
           PROVEN by TestProductionSafeWithhold.
        3. Safe withhold: production path withholds when facts unavailable.

        These are DIFFERENT scenarios. P7 does NOT require re-publishing
        from Registry. Safe withhold satisfies the frozen contract.
        """
        # This is a documentation test. The real assertions are in:
        # - TestP7ExactReplay: deterministic rebuild
        # - TestProductionSafeWithhold: DB-level safe withhold
        # Verify those classes exist and have test methods.
        import inspect
        p7_methods = [m for m in dir(TestP7ExactReplay) if m.startswith("test_")]
        withhold_methods = [m for m in dir(TestProductionSafeWithhold) if m.startswith("test_")]
        assert len(p7_methods) >= 2, f"TestP7ExactReplay must have >=2 tests, got {p7_methods}"
        assert len(withhold_methods) >= 2, f"TestProductionSafeWithhold must have >=2 tests, got {withhold_methods}"
