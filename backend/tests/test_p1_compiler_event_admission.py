"""A-lane P1: Compiler edges + event ordering + admission deep (matrix A)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.hashing import sha256_hex
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IR, IRContent, IRNode
from app.domains.evidence.models import CheckResult, ValidationEvent, enforce_state_transition
from app.domains.gate.admission import AdmissionService
from app.domains.resolver.span import ResolvedSpan, SourceLineView
from app.repositories.base import RepositoryError
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository
from app.models.source import DocumentSourceLine

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")
AID = uuid.UUID("00000000-0000-0000-0000-0000000000ae")


def _span(sid, role, refs, start=None, end=None, gran="single_line"):
    return ResolvedSpan(
        span_id=sid, source_version_id=SVID, role=role,
        start_line_ref=refs[0], end_line_ref=refs[-1],
        line_refs=tuple(refs), granularity=gran,
        start_offset=start, end_offset=end, text_hash="0"*64,
        resolution_status="exact",
    )


def _node(uid, status="ready", ctype="single_choice", content=None, utype="standalone_question"):
    return IRNode(
        unit_id=uid, unit_type=utype, question_number="1",
        question_number_range=None, original_question_type=ctype,
        content=tuple(content or (IRContent(role="stem", span_id="sp-s"),)),
        shared_components=(), sub_questions=(), relations=(),
        semantic_status=status,
    )


def _ir(nodes):
    return IR(ir_schema="semantic-question-ir/v0.3",
              source_version_id=SVID, annotation_id=AID, units=tuple(nodes))


def _lines(**kw):
    return {k: SourceLineView(k, v, i+1, 1, i+1) for i, (k, v) in enumerate(kw.items())}


class TestCompilerEdges:
    def test_nonready_node_yields_no_leaves(self):
        snap = Compiler({}, {}).compile(_ir([_node("U1", status="incomplete")]))
        assert snap.leaves == ()
        print("\n[CMP] nonready -> 0 leaves")

    def test_missing_span_id_skips_leaf(self):
        n = _node("U1", content=(IRContent(role="stem", span_id=None),))
        snap = Compiler({}, {}).compile(_ir([n]))
        assert snap.leaves == ()
        print("\n[CMP] stem span_id None -> 0 leaves")

    def test_unknown_type_not_guessed(self):
        span = _span("sp-s", "stem", ["P1L001"])
        lines = _lines(P1L001="stem")
        c = Compiler({"sp-s": span}, lines)
        snap = c.compile(_ir([_node("U1", ctype="foo_question")]))
        print(f"\n[CMP] unknown type leaves={len(snap.leaves)} "
              f"canon={[l.canonical_question_type for l in snap.leaves]}")
        # if leaf produced, type must not be a guessed valid type
        for l in snap.leaves:
            assert l.canonical_question_type not in ("single_choice", "multi_choice", "true_false")

    def test_empty_text_slice(self):
        span = _span("sp-s", "stem", ["P1L001"])
        lines = _lines(P1L001="")
        snap = Compiler({"sp-s": span}, lines).compile(_ir([_node("U1")]))
        assert snap.leaves[0].stem.text == ""
        print("\n[CMP] empty slice ok")

    def test_line_character_offset(self):
        span = _span("sp-s", "stem", ["P1L001"], start=2, end=5, gran="line_character")
        lines = _lines(P1L001="XXabcdef")
        snap = Compiler({"sp-s": span}, lines).compile(_ir([_node("U1")]))
        assert snap.leaves[0].stem.text == "abc"
        print("\n[CMP] offset slice='abc'")

    def test_repeat_compile_deterministic(self):
        span = _span("sp-s", "stem", ["P1L001"])
        lines = _lines(P1L001="stem text")
        c = Compiler({"sp-s": span}, lines)
        s1 = c.compile(_ir([_node("U1")]))
        s2 = c.compile(_ir([_node("U1")]))
        assert s1.leaves[0].dedup_key == s2.leaves[0].dedup_key
        assert s1.leaves[0].stem.text_hash == s2.leaves[0].stem.text_hash
        print("\n[CMP] deterministic")

    def test_dangling_span_id_deterministic_reject(self):
        n = _node("U1", content=(IRContent(role="stem", span_id="sp-s"),))
        with pytest.raises(ValueError, match="unknown span_id"):
            Compiler({}, {}).compile(_ir([n]))
        print("\n[CMP] dangling span_id -> ValueError (not KeyError)")


class TestEventOrdering:
    def _ev(self, at, result="validated", claim="Q1"):
        return ValidationEvent(
            event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=claim,
            validation_result=result, checks=(),
            validation_method="frozen_header_rule", validator="gate/v1",
            validated_at=at,
        )

    def test_same_ts_double_validated_rejected(self):
        t = datetime(2026, 9, 29, 12, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            enforce_state_transition((self._ev(t),), "validated", "Q1")
        enforce_state_transition((self._ev(t),), "invalidated", "Q1")
        print("\n[EVT] same-ts rules hold")

    async def test_near_future_cascade_still_wins(self, session):
        from tests.eb008_helpers import seed_candidate
        sv, ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        near = datetime.now(timezone.utc) + timedelta(seconds=30)
        await repo.append_event(self._ev(near), candidate_id=cand.id, source_version_id=sv.id)
        await repo.invalidate_claims_for_source_version(sv.id, reason="ord")
        state, latest = await repo.project_authority(cand.id, "Q1")
        print(f"\n[EVT] near+30s cascade state={state!r}")
        assert state == "invalidated"
        assert latest.validated_at > near

    async def test_time_order_not_insert_order(self, session):
        from tests.eb008_helpers import seed_candidate
        sv, ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        now = datetime.now(timezone.utc)
        await repo.append_event(self._ev(past), candidate_id=cand.id, source_version_id=sv.id)
        await repo.append_event(self._ev(now, "invalidated"), candidate_id=cand.id, source_version_id=sv.id)
        state, _ = await repo.project_authority(cand.id, "Q1")
        print(f"\n[EVT] past+now -> {state!r}")
        assert state == "invalidated"


class TestAdmissionDeep:
    async def test_human_without_trail_blocked(self, session):
        from tests.eb008_helpers import seed_candidate, pending_gate_decision
        sv, ann, cand = await seed_candidate(session, gate=pending_gate_decision())
        repo = EvidenceRepository(session)
        await repo.append_event(
            ValidationEvent(
                event_id="v", claim_id="Q1", validation_result="validated", checks=(),
                validation_method="human_review", validator="human/r1",
                validated_at=datetime.now(timezone.utc),
            ),
            candidate_id=cand.id, source_version_id=sv.id, review_proof="0"*64,
        )
        svc = AdmissionService(session)
        with pytest.raises(RepositoryError, match="review_trail"):
            await svc.approve(candidate_id=cand.id, provenance={"source": "human"})
        print("\n[ADM] human without trail blocked")

    async def test_unknown_source_blocked(self, session):
        from tests.eb008_helpers import seed_candidate
        sv, ann, cand = await seed_candidate(session)
        with pytest.raises(RepositoryError, match="unknown approve source"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "evil"})
        print("\n[ADM] unknown source blocked")

    async def test_stale_human_proof_blocks_approve(self, session):
        """Insert human_review with wrong proof; auto_gate must fail-closed."""
        from tests.eb008_helpers import seed_candidate, auto_gate_decision
        sv, ann, cand = await seed_candidate(session, gate=auto_gate_decision())
        repo = EvidenceRepository(session)
        await repo.append_event(
            ValidationEvent(
                event_id="v", claim_id="Q1", validation_result="validated", checks=(),
                validation_method="human_review", validator="human/r1",
                validated_at=datetime.now(timezone.utc),
            ),
            candidate_id=cand.id, source_version_id=sv.id, review_proof="f"*64,
        )
        with pytest.raises(RepositoryError, match="proof|fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"})
        print("\n[ADM] stale/wrong human proof blocks approve")
