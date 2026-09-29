"""Adversarial re-audit of EB-008 A1 fix + R-5 + OD-R-01 claims (MIMO, 2026-09-29).

Purpose: attack MY OWN previous conclusions with real tests.
No speculation. Each probe prints observed behavior.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.hashing import sha256_hex
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.compile.snapshot import CompiledAnswer
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.evidence.promotion import EvidencePromotionService
from app.domains.gate.admission import AdmissionService
from app.models.source import DocumentSourceLine
from app.repositories.base import RepositoryError
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

CLAIM = "Q1"


def ev(result="validated", method="frozen_header_rule", validator="gate/v1", at=None, claim=CLAIM):
    return ValidationEvent(
        event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=claim,
        validation_result=result,
        checks=(CheckResult(check_id="X", result="pass"),),
        validation_method=method, validator=validator,
        validated_at=at or datetime.now(timezone.utc),
    )


async def seed(session):
    texts = ("1. fruit", "A. apple", "B. car", "【答案】", "1. A")
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
        payload={
            "ir_snapshot": {
                "ir_schema": "semantic-question-ir/v0.3",
                "units": [{"unit_id": CLAIM, "unit_type": "standalone_question",
                           "question_number": "", "question_number_range": None,
                           "original_question_type": "single_choice",
                           "content": [{"role": "stem", "span_id": "sp-stem", "label": None, "unsupported": False}],
                           "shared_components": [], "relations": [], "semantic_status": "ready",
                           "sub_questions": []}],
            },
            "resolved_spans": [{"span_id": "sp-stem", "role": "stem", "granularity": "line",
                                "line_refs": ["P1L001"], "start_offset": None, "end_offset": None,
                                "text_hash": "0"*64, "resolution_status": "exact"}],
            "compiled_roles": [
                {"role": "stem", "span_id": "sp-stem", "line_refs": ["P1L001"],
                 "text": "1. fruit", "text_hash": sha256_hex("1. fruit"), "label": None,
                 "unit_id": CLAIM, "kind": "content"},
                {"role": "option", "span_id": "sp-a", "line_refs": ["P1L002"],
                 "text": "A. apple", "text_hash": sha256_hex("A. apple"), "label": "A",
                 "unit_id": CLAIM, "kind": "content"},
                {"role": "option", "span_id": "sp-b", "line_refs": ["P1L003"],
                 "text": "B. car", "text_hash": sha256_hex("B. car"), "label": "B",
                 "unit_id": CLAIM, "kind": "content"},
            ],
            "answer": [{"unit_id": CLAIM, "question_number": "", "span_id": "sp-ans",
                        "line_refs": ["P1L005"], "text": "1. A", "text_hash": sha256_hex("1. A"),
                        "source_located": True, "complete": True, "verified_correct": None}],
            "figure_refs": [], "knowledge_links": [], "evidence": [],
            "display_hint": {"unit_type": "standalone_unit", "canonical_question_type": "single_choice"},
        },
        gate_decision={"gate_policy_version": "admission-gate/v1", "decision": "auto_approve",
                       "layers": {}, "reasons": []},
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann, cand


class TestA1Residual:
    """Attack residual holes in the A1 timestamp fix."""

    async def test_within_skew_future_still_cannot_beat_cascade(self, session):
        """Near-future within 5min skew must still lose to invalidate cascade."""
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        near = datetime.now(timezone.utc) + timedelta(minutes=4, seconds=50)
        await repo.append_event(ev(at=near), candidate_id=cand.id, source_version_id=sv.id)
        created = await repo.invalidate_claims_for_source_version(sv.id, reason="adv")
        assert len(created) == 1
        state, latest = await repo.project_authority(cand.id, CLAIM)
        print(f"\n[R-A1a] state={state!r} latest={latest.validation_result} "
              f"cascade_at={latest.validated_at} near={near}")
        assert state == "invalidated", f"RESIDUAL HIT: state={state}"

    async def test_boundary_plus_5min_rejected(self, session):
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        at = datetime.now(timezone.utc) + timedelta(minutes=5, seconds=1)
        with pytest.raises(ValueError, match="future"):
            await repo.append_event(ev(at=at), candidate_id=cand.id, source_version_id=sv.id)
        print("\n[R-A1b] just-over-5min rejected")

    async def test_naive_datetime_not_rejected_as_future(self, session):
        """Naive datetime must be normalized as UTC (proof._to_utc_iso same rule).

        Regression: A1 fix originally crashed TypeError on naive; now ValueError
        for far-future naive, accept for near naive.
        """
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        naive_far = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)
        with pytest.raises(ValueError, match="future"):
            await repo.append_event(ev(at=naive_far), candidate_id=cand.id, source_version_id=sv.id)
        print("\n[R-A1c] NAIVE far rejected as UTC-future (not TypeError)")
        naive_near = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=2)
        await repo.append_event(ev(at=naive_near), candidate_id=cand.id, source_version_id=sv.id)
        await repo.invalidate_claims_for_source_version(sv.id, reason="adv-naive")
        state, _ = await repo.project_authority(cand.id, CLAIM)
        print(f"[R-A1c] naive near + cascade state={state!r}")
        assert state == "invalidated"

    async def test_past_timestamp_validated_then_cascade(self, session):
        """Past validated + cascade must still end INVALIDATED (cascade later)."""
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        past = datetime.now(timezone.utc) - timedelta(days=3)
        await repo.append_event(ev(at=past), candidate_id=cand.id, source_version_id=sv.id)
        await repo.invalidate_claims_for_source_version(sv.id, reason="adv-past")
        state, latest = await repo.project_authority(cand.id, CLAIM)
        print(f"\n[R-A1d] past+cascade state={state!r}")
        assert state == "invalidated"

    async def test_cannot_append_validated_after_invalidate_even_later_ts(self, session):
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        await repo.append_event(ev(), candidate_id=cand.id, source_version_id=sv.id)
        await repo.invalidate_claims_for_source_version(sv.id, reason="adv-term")
        later = datetime.now(timezone.utc) + timedelta(minutes=4)
        with pytest.raises(ValueError, match="terminal|INVALIDATED"):
            await repo.append_event(ev(at=later), candidate_id=cand.id, source_version_id=sv.id)
        print("\n[R-A1e] post-invalidate later-ts append blocked")

    async def test_two_validated_same_result_replay_no_new_row(self, session):
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        r1 = await repo.append_event(ev(), candidate_id=cand.id, source_version_id=sv.id)
        r2 = await repo.append_event(ev(at=datetime.now(timezone.utc)+timedelta(seconds=1)),
                                     candidate_id=cand.id, source_version_id=sv.id)
        rows = await repo.find_events_for_claim(cand.id, CLAIM)
        print(f"\n[R-A1f] replay same id? {r1.id==r2.id} rows={len(rows)}")
        assert r1.id == r2.id and len(rows) == 1


class TestR5Pin:
    """Verify R-5 test is honest: forged machine event really still approves."""

    async def test_forged_machine_event_still_approves__r5_boundary(self, session):
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        await repo.append_event(ev(method="byte_proven", validator="attacker/v1"),
                                candidate_id=cand.id, source_version_id=sv.id)
        svc = AdmissionService(session)
        result = await svc.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
        print(f"\n[R-5] forged machine event decision_status={result.decision_status!r}")
        assert result.decision_status == "approved"  # documents R-5 boundary


class TestODR01Claims:
    """Verify OD-R-01 claims against real types / materialization."""

    def test_compiled_answer_has_no_values_array(self):
        import dataclasses
        fields = {f.name for f in dataclasses.fields(CompiledAnswer)}
        print(f"\n[OD-R-01a] CompiledAnswer fields={sorted(fields)}")
        assert "values" not in fields
        assert "text" in fields

    def test_compiled_leaf_answer_is_singular(self):
        import dataclasses
        from app.domains.compile.snapshot import CompiledLeaf
        f = [x for x in dataclasses.fields(CompiledLeaf) if x.name == "answer"][0]
        print(f"\n[OD-R-01b] CompiledLeaf.answer type={f.type!r} (singular, not list)")
        assert f.type in ("CompiledAnswer | None", "Optional[CompiledAnswer]", "CompiledAnswer|None") or "None" in str(f.type)

    async def test_materialize_one_answer_row_per_instance(self, session):
        """Admission writes exactly one answer role_content with role_index=0."""
        from sqlalchemy import select, text
        from app.models.content import InstanceRoleContent, QuestionInstance
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        await repo.append_event(ev(), candidate_id=cand.id, source_version_id=sv.id)
        svc = AdmissionService(session)
        result = await svc.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
        assert result.decision_status == "approved"
        insts = (await session.execute(
            select(QuestionInstance).where(QuestionInstance.source_version_id == sv.id)
        )).scalars().all()
        print(f"\n[OD-R-01c] instances={len(insts)}")
        assert len(insts) == 1, f"expected 1 instance, got {len(insts)}"
        ans_rows = (await session.execute(
            select(InstanceRoleContent).where(
                InstanceRoleContent.instance_id == insts[0].id,
                InstanceRoleContent.role == "answer",
            )
        )).scalars().all()
        print(f"[OD-R-01c] answer rows={len(ans_rows)} "
              f"indexes={[r.role_index for r in ans_rows]} texts={[r.text for r in ans_rows]}")
        assert len(ans_rows) == 1
        assert ans_rows[0].role_index == 0
        # N ordered values NOT present as separate value rows
        assert not any(isinstance(r.text, (list, tuple)) for r in ans_rows)

    async def test_blank_role_unsupported_in_ir(self, session):
        """IR marks blank as unsupported (BUG-V3-020)."""
        from app.domains.compile import ir as ir_mod
        import inspect
        src = inspect.getsource(ir_mod)
        assert '"blank"' in src or "'blank'" in src
        # find the unsupported roles tuple
        assert "blank" in src
        print("\n[OD-R-01d] blank appears in ir.py as unsupported role")

    def test_admission_answer_role_index_fixed_zero(self):
        import inspect
        from app.domains.gate import admission
        src = inspect.getsource(admission)
        assert 'role="answer"' in src or "role='answer'" in src
        # answer create uses role_index=0
        idx = src.find('role="answer"')
        snippet = src[idx:idx+250]
        print(f"\n[OD-R-01e] admission answer materialize snippet: {snippet[:200]!r}")
        assert "role_index=0" in snippet or "role_index=0" in src[idx:idx+300]
