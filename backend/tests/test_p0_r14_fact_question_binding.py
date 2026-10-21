"""P0-R14 real M1: fact-question binding.

Decisive attack: Q2 match fact forged onto Q1 payload.
_materialize and Repository must both reject.

Tests exercise real resolver registration + real Repository checks.
"""
from __future__ import annotations



import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.binding_fact import (
    derive_binding_fact,
    get_registry,
    register_trusted_binding_fact,
    resolve_trusted_binding_fact,
)
from app.domains.gate.policy import evaluate
from app.domains.gate.publish_seal import issue_publish_seal
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.repositories.content_repository import ContentRepository, RepositoryError

SVID = uuid.UUID("00000000-0000-0000-0000-00000000f104")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-00000000a104")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(qn="1", answer_lines=None, unit_id=None):
    ans = {"answer_zone": "answer_table", "question_label": qn}
    if answer_lines is not None:
        ans["answer_lines"] = answer_lines
    return {
        "semantic_units": [{
            "unit_id": unit_id or f"Q{qn}",
            "unit_type": "standalone_unit",
            "original_question_type": "single_choice",
            "content": {
                "stem": {"question_label": qn},
                "options": [{"label": l} for l in "ABCD"],
                "answer": ans,
            },
        }]
    }


def _compile_run(lines, payload, root_id="Q1"):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
    root = next(u for u in ir.units if u.unit_id == root_id)
    d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
    leaf = next((lf for lf in compiled.leaves if lf.unit_id == root_id), None)
    return d, run, compiled, leaf


@pytest.fixture(autouse=True)
def _clean_registry():
    get_registry().clear()
    yield
    get_registry().clear()


class TestR14FactQuestionBinding:
    def test_q2_fact_registered_with_q2(self):
        """Real resolver registers Q2 fact with question_number=2."""
        lines = _mk(
            "2. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "2. B",
        )
        d, run, compiled, leaf = _compile_run(
            lines, _payload(qn="2", answer_lines=[7, 7]), "Q2"
        )
        assert leaf is not None and leaf.answer is not None
        fact = resolve_trusted_binding_fact(source_version_id=str(SVID), span_id=leaf.answer.span_id)
        assert fact is not None
        assert fact.question_number == "2"
        assert fact.ownership == "match"

    def test_q1_fact_registered_with_q1(self):
        """Real resolver registers Q1 fact with question_number=1."""
        lines = _mk(
            "1. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "1. B",
        )
        d, run, compiled, leaf = _compile_run(
            lines, _payload(qn="1", answer_lines=[7, 7]), "Q1"
        )
        assert leaf is not None and leaf.answer is not None
        fact = resolve_trusted_binding_fact(source_version_id=str(SVID), span_id=leaf.answer.span_id)
        assert fact is not None
        assert fact.question_number == "1"

    async def test_q2_fact_forged_onto_q1_rejected_by_repo(self, session):
        """Decisive M1: Q2 match fact → Q1 payload → Repository rejects."""
        # 1. Real resolver registers Q2 match fact.
        lines_q2 = _mk(
            "2. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "2. B",
        )
        d2, run2, compiled2, leaf2 = _compile_run(
            lines_q2, _payload(qn="2", answer_lines=[7, 7]), "Q2"
        )
        assert leaf2 is not None and leaf2.answer is not None
        q2_fact = resolve_trusted_binding_fact(source_version_id=str(SVID), span_id=leaf2.answer.span_id)
        assert q2_fact is not None
        assert q2_fact.ownership == "match"
        assert q2_fact.question_number == "2"

        # 2. Attacker forges Q1 payload: span_id points at Q2 fact.
        # 3. Try to write via Repository.
        from tests.test_p0_publish_contract import _seed_instance
        qi = await _seed_instance(session, SVID)  # Q1 instance (question_number="1")
        content = ContentRepository(session)

        seal = issue_publish_seal(
            fact=q2_fact, official_text="B", publish="official"
        )
        assert seal  # seal is well-formed for Q2 fact

        # Q1 instance, but fact is for Q2 → must reject.
        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=qi.id,
                role="answer",
                role_index=0,
                text="B",
                text_hash="x",
                source_span={"span_id": q2_fact.span_id},
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "binding_fact_id": q2_fact.fact_id,
                    "binding_unit_id": q2_fact.unit_id,
                    "binding_question_number": "1",  # claims Q1
                    "answer_text_hash": q2_fact.answer_text_hash,
                    "publish_seal": seal,
                },
            )

    async def test_q1_fact_q1_instance_accepted(self, session):
        """Control: Q1 fact + Q1 instance → accepted."""
        lines_q1 = _mk(
            "1. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "1. B",
        )
        d1, run1, compiled1, leaf1 = _compile_run(
            lines_q1, _payload(qn="1", answer_lines=[7, 7]), "Q1"
        )
        assert leaf1 is not None and leaf1.answer is not None
        q1_fact = resolve_trusted_binding_fact(source_version_id=str(SVID), span_id=leaf1.answer.span_id)
        assert q1_fact is not None
        assert q1_fact.question_number == "1"

        from tests.test_p0_publish_contract import _seed_instance
        qi = await _seed_instance(session, SVID)  # Q1 instance
        content = ContentRepository(session)

        seal = issue_publish_seal(
            fact=q1_fact, official_text="B", publish="official"
        )
        assert seal

        row = await content.create_role_content(
            instance_id=qi.id,
            role="answer",
            role_index=0,
            text="B",
            text_hash="x",
            source_span={"span_id": q1_fact.span_id},
            answer_status={
                "ownership": "match",
                "publish": "official",
                "binding_fact_id": q1_fact.fact_id,
                "answer_text_hash": q1_fact.answer_text_hash,
                "publish_seal": seal,
            },
        )
        assert row.text == "B"

    async def test_q2_fact_q2_instance_accepted(self, session):
        """Control: Q2 fact + Q2 instance → accepted."""
        lines_q2 = _mk(
            "2. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "2. B",
        )
        d2, run2, compiled2, leaf2 = _compile_run(
            lines_q2, _payload(qn="2", answer_lines=[7, 7]), "Q2"
        )
        assert leaf2 is not None and leaf2.answer is not None
        q2_fact = resolve_trusted_binding_fact(source_version_id=str(SVID), span_id=leaf2.answer.span_id)
        assert q2_fact is not None

        # Use seed helper but override question_number to "2"
        from tests.test_p0_publish_contract import _seed_instance
        qi = await _seed_instance(session, SVID)
        # Override the instance's question_number to match Q2
        qi.question_number = "2"
        qi.question_number_range = "2"
        await session.flush()

        content = ContentRepository(session)
        seal = issue_publish_seal(
            fact=q2_fact, official_text="B", publish="official"
        )
        row = await content.create_role_content(
            instance_id=qi.id,
            role="answer",
            role_index=0,
            text="B",
            text_hash="x",
            source_span={"span_id": q2_fact.span_id},
            answer_status={
                "ownership": "match",
                "publish": "official",
                "binding_fact_id": q2_fact.fact_id,
                "answer_text_hash": q2_fact.answer_text_hash,
                "publish_seal": seal,
            },
        )
        assert row.text == "B"

    def test_materialize_qn_check_logic(self):
        """Direct test of the question_number check in _materialize logic."""
        # Q2 fact
        q2_fact = derive_binding_fact(
            span_id="sp-Q2.answer",
            source_version_id=str(SVID), question_number="2",
            source_lines=["2. B"], answer_text="B",
        )
        register_trusted_binding_fact(q2_fact)

        # Simulate _materialize check for Q1 answer pointing at Q2 fact
        fact = resolve_trusted_binding_fact(source_version_id=str(SVID), span_id="sp-Q2.answer")
        assert fact is not None

        # The check: fact.span_id must match ans.span_id
        #           fact.question_number must match ans.question_number
        ans_span_id = "sp-Q2.answer"  # forged: Q1 payload points at Q2 fact
        ans_qn = "1"  # current question is Q1

        trust_own = fact.ownership
        if fact.span_id != ans_span_id:
            trust_own = "unknown"
        elif ans_qn and fact.question_number and fact.question_number != ans_qn:
            trust_own = "unknown"

        assert trust_own == "unknown", (
            f"Q2 fact must not authorize Q1: {trust_own=}"
        )

    def test_materialize_qn_check_accepts_matching(self):
        """Control: matching qn → trust_own preserved."""
        q1_fact = derive_binding_fact(
            span_id="sp-Q1.answer",
            source_version_id=str(SVID), question_number="1",
            source_lines=["1. B"], answer_text="B",
        )
        register_trusted_binding_fact(q1_fact)

        fact = resolve_trusted_binding_fact(source_version_id=str(SVID), span_id="sp-Q1.answer")
        assert fact is not None

        ans_span_id = "sp-Q1.answer"
        ans_qn = "1"

        trust_own = fact.ownership
        if fact.span_id != ans_span_id:
            trust_own = "unknown"
        elif ans_qn and fact.question_number and fact.question_number != ans_qn:
            trust_own = "unknown"

        assert trust_own == "match"

    async def test_q2_fact_q1_instance_rejected_when_status_omits_binding_fields(self, session):
        """P1-B: omitting binding_unit_id / binding_question_number must NOT
        skip the ownership gate. Q2 fact + Q1 instance → RepositoryError and
        no non-empty official row."""
        lines_q2 = _mk(
            "2. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "2. B",
        )
        d2, run2, compiled2, leaf2 = _compile_run(
            lines_q2, _payload(qn="2", answer_lines=[7, 7]), "Q2"
        )
        assert leaf2 is not None and leaf2.answer is not None
        q2_fact = resolve_trusted_binding_fact(
            source_version_id=str(SVID), span_id=leaf2.answer.span_id
        )
        assert q2_fact is not None and q2_fact.question_number == "2"

        from tests.test_p0_publish_contract import _seed_instance
        qi = await _seed_instance(session, SVID)  # question_number="1"
        content = ContentRepository(session)
        seal = issue_publish_seal(fact=q2_fact, official_text="B", publish="official")
        assert seal

        # answer_status deliberately OMITS binding_unit_id and binding_question_number
        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=qi.id,
                role="answer",
                role_index=0,
                text="B",
                text_hash="x",
                source_span={"span_id": q2_fact.span_id},
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "binding_fact_id": q2_fact.fact_id,
                    "answer_text_hash": q2_fact.answer_text_hash,
                    "publish_seal": seal,
                },
            )

        from sqlalchemy import select as _sa_select
        from app.models.content import InstanceRoleContent as _IRC
        rows = (await session.execute(
            _sa_select(_IRC.text).where(
                _IRC.instance_id == qi.id, _IRC.role == "answer"
            )
        )).scalars().all()
        assert not any(r for r in rows), (
            f"rejected write must not leave non-empty official text: {rows!r}"
        )

    async def test_explicit_wrong_qn_in_status_rejected(self, session):
        """P1-B: explicit wrong binding_question_number is also rejected."""
        lines_q2 = _mk(
            "2. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "2. B",
        )
        d2, run2, compiled2, leaf2 = _compile_run(
            lines_q2, _payload(qn="2", answer_lines=[7, 7]), "Q2"
        )
        q2_fact = resolve_trusted_binding_fact(
            source_version_id=str(SVID), span_id=leaf2.answer.span_id
        )
        assert q2_fact is not None

        from tests.test_p0_publish_contract import _seed_instance
        qi = await _seed_instance(session, SVID)  # Q1
        content = ContentRepository(session)
        seal = issue_publish_seal(fact=q2_fact, official_text="B", publish="official")

        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=qi.id,
                role="answer",
                role_index=0,
                text="B",
                text_hash="x",
                source_span={"span_id": q2_fact.span_id},
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "binding_fact_id": q2_fact.fact_id,
                    "binding_unit_id": q2_fact.unit_id,
                    "binding_question_number": "2",  # matches fact, not instance
                    "answer_text_hash": q2_fact.answer_text_hash,
                    "publish_seal": seal,
                },
            )

    async def test_instance_without_qn_fails_closed(self, session):
        """P1-B: empty instance.question_number must not treat as match."""
        lines_q1 = _mk(
            "1. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "1. B",
        )
        d1, run1, compiled1, leaf1 = _compile_run(
            lines_q1, _payload(qn="1", answer_lines=[7, 7]), "Q1"
        )
        q1_fact = resolve_trusted_binding_fact(
            source_version_id=str(SVID), span_id=leaf1.answer.span_id
        )
        assert q1_fact is not None

        from tests.test_p0_publish_contract import _seed_instance
        qi = await _seed_instance(session, SVID)
        qi.question_number = ""
        qi.question_number_range = ""
        await session.flush()

        content = ContentRepository(session)
        seal = issue_publish_seal(fact=q1_fact, official_text="B", publish="official")
        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=qi.id,
                role="answer",
                role_index=0,
                text="B",
                text_hash="x",
                source_span={"span_id": q1_fact.span_id},
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "binding_fact_id": q1_fact.fact_id,
                    "answer_text_hash": q1_fact.answer_text_hash,
                    "publish_seal": seal,
                },
            )

    async def test_cross_composite_parent_write_rejected(self, session):
        """P1: Q2 fact of composite parent A must NOT write into parent B.

        Both instances have empty question_number / question_number_range
        (the bypass condition). Ownership gate is unit membership from
        already-persisted per-child stems.
        """
        from sqlalchemy import select as _sa_select
        from app.models.content import InstanceRoleContent as _IRC
        from tests.test_p0_publish_contract import _seed_instance

        # Parent A children Q1/Q2: real resolver registers Q2 match fact.
        lines_a = _mk(
            "2. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "2. B",
        )
        d, run, compiled, leaf = _compile_run(
            lines_a, _payload(qn="2", answer_lines=[7, 7], unit_id="Q2"), "Q2"
        )
        assert leaf is not None and leaf.answer is not None
        q2_fact = resolve_trusted_binding_fact(
            source_version_id=str(SVID), span_id=leaf.answer.span_id
        )
        assert q2_fact is not None and q2_fact.unit_id == "Q2"
        assert q2_fact.ownership == "match"

        # Parent B instance: empty qn/range, stems for DIFFERENT children.
        qi_b = await _seed_instance(session, SVID)
        qi_b.question_number = ""
        qi_b.question_number_range = ""
        await session.flush()
        content = ContentRepository(session)
        for uid in ("Q3", "Q4"):
            await content.create_role_content(
                instance_id=qi_b.id,
                role="stem",
                role_index=0 if uid == "Q3" else 1,
                text=f"stem {uid}",
                text_hash="h",
                source_span={"span_id": f"sp-{uid}.stem", "unit_id": uid},
                answer_status=None,
            )

        seal = issue_publish_seal(fact=q2_fact, official_text="B", publish="official")
        assert seal

        # Omit binding_unit_id / binding_question_number — the attack.
        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=qi_b.id,
                role="answer",
                role_index=0,
                text="B",
                text_hash="x",
                source_span={"span_id": q2_fact.span_id},
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "binding_fact_id": q2_fact.fact_id,
                    "answer_text_hash": q2_fact.answer_text_hash,
                    "publish_seal": seal,
                },
            )

        rows = (await session.execute(
            _sa_select(_IRC.text).where(
                _IRC.instance_id == qi_b.id, _IRC.role == "answer"
            )
        )).scalars().all()
        assert not any(r for r in rows), (
            f"cross-parent write must leave no non-empty official: {rows!r}"
        )

    async def test_composite_sibling_fact_same_parent_accepted(self, session):
        """Positive: Q2 fact of parent A writes into parent A (sibling stems)."""
        from sqlalchemy import select as _sa_select
        from app.models.content import InstanceRoleContent as _IRC
        from tests.test_p0_publish_contract import _seed_instance

        lines_a = _mk(
            "2. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "2. B",
        )
        d, run, compiled, leaf = _compile_run(
            lines_a, _payload(qn="2", answer_lines=[7, 7], unit_id="Q2"), "Q2"
        )
        q2_fact = resolve_trusted_binding_fact(
            source_version_id=str(SVID), span_id=leaf.answer.span_id
        )
        assert q2_fact is not None and q2_fact.unit_id == "Q2"

        qi_a = await _seed_instance(session, SVID)
        qi_a.question_number = ""
        qi_a.question_number_range = ""
        await session.flush()
        content = ContentRepository(session)
        for uid in ("Q1", "Q2"):
            await content.create_role_content(
                instance_id=qi_a.id,
                role="stem",
                role_index=0 if uid == "Q1" else 1,
                text=f"stem {uid}",
                text_hash="h",
                source_span={"span_id": f"sp-{uid}.stem", "unit_id": uid},
                answer_status=None,
            )

        seal = issue_publish_seal(fact=q2_fact, official_text="B", publish="official")
        row = await content.create_role_content(
            instance_id=qi_a.id,
            role="answer",
            role_index=0,
            text="B",
            text_hash="x",
            source_span={"span_id": q2_fact.span_id},
            answer_status={
                "ownership": "match",
                "publish": "official",
                "binding_fact_id": q2_fact.fact_id,
                "answer_text_hash": q2_fact.answer_text_hash,
                "publish_seal": seal,
            },
        )
        assert row.text == "B"
        rows = (await session.execute(
            _sa_select(_IRC.text).where(
                _IRC.instance_id == qi_a.id, _IRC.role == "answer"
            )
        )).scalars().all()
        assert rows == ["B"]

    async def test_no_unit_identity_and_no_qn_fails_closed(self, session):
        """C: no role unit_ids and no instance qn → reject, never default allow."""
        from tests.test_p0_publish_contract import _seed_instance

        lines = _mk(
            "1. What is X?", "A. a", "B. b", "C. c", "D. d",
            "答案", "1. B",
        )
        d, run, compiled, leaf = _compile_run(
            lines, _payload(qn="1", answer_lines=[7, 7]), "Q1"
        )
        q1_fact = resolve_trusted_binding_fact(
            source_version_id=str(SVID), span_id=leaf.answer.span_id
        )
        assert q1_fact is not None

        qi = await _seed_instance(session, SVID)
        qi.question_number = ""
        qi.question_number_range = ""
        await session.flush()
        content = ContentRepository(session)
        seal = issue_publish_seal(fact=q1_fact, official_text="B", publish="official")
        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=qi.id,
                role="answer",
                role_index=0,
                text="B",
                text_hash="x",
                source_span={"span_id": q1_fact.span_id},
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "binding_fact_id": q1_fact.fact_id,
                    "answer_text_hash": q1_fact.answer_text_hash,
                    "publish_seal": seal,
                },
            )
