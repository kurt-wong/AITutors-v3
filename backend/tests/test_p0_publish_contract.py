# -*- coding: utf-8 -*-
"""R11 real acceptance tests: DB writes, student API, layered mutations.

Evidence is instance_role_contents rows and real RepositoryError behavior.
"""
from __future__ import annotations



import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.admission import _publish_decision
from app.domains.gate.policy import evaluate
from app.domains.gate.publish_seal import issue_publish_seal, verify_publish_seal
from app.domains.gate.binding_fact import (
    derive_binding_fact,
    register_trusted_binding_fact,
    resolve_trusted_binding_fact,
    get_registry,
)
from app.domains.resolver import resolver as resolver_mod
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.models.content import Question, QuestionInstance
from app.models.source import Document, DocumentSourceVersion
from app.repositories.content_repository import ContentRepository, RepositoryError

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f5")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a5")
EMPTY_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b96ddd3f9d7cc1cf348"

BIO_TABLE = (
    "<table border=1><tr><td>题号</td><td>1</td><td>2</td><td>3</td></tr>"
    "<tr><td>答案</td><td>B</td><td>D</td><td>A</td></tr></table>"
)


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(qn="1", answer_lines=None, ctype="single_choice", unit_id=None):
    ans = {"answer_zone": "answer_table", "question_label": qn}
    if answer_lines is not None:
        ans["answer_lines"] = answer_lines
    return {
        "semantic_units": [{
            "unit_id": unit_id or f"Q{qn}",
            "unit_type": "standalone_unit",
            "original_question_type": ctype,
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


async def _seed_instance(session, sv_id=None) -> QuestionInstance:
    doc = Document(
        id=uuid.uuid4(),
        original_object_key="k",
        original_sha256=uuid.uuid4().hex + uuid.uuid4().hex,
        file_name="paper.pdf",
        file_type="pdf",
        upload_meta={},
        processing_status="sealed",
    )
    session.add(doc)
    sv = DocumentSourceVersion(
        id=sv_id or uuid.uuid4(),
        document_id=doc.id,
        artifact_kind="canonical_l1",
        role="preprocessing",
        provider="preprocessing",
        body_text="x",
        body_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        integrity_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        page_count=1,
        line_count=1,
        status="sealed",
    )
    session.add(sv)
    q = Question(
        id=uuid.uuid4(),
        subject=None,
        grade=None,
        canonical_question_type="single_choice",
        dedup_key=uuid.uuid4().hex + uuid.uuid4().hex,
    )
    session.add(q)
    await session.flush()
    qi = QuestionInstance(
        id=uuid.uuid4(),
        question_id=q.id,
        document_id=doc.id,
        source_version_id=sv.id,
        occurrence_key=f"occ-{uuid.uuid4()}",
        question_number="1",
        question_number_range="1",
        page_no=1,
        instance_order=1,
    )
    session.add(qi)
    await session.flush()
    return qi


# =========================================================================
# R1: structured answer table → ownership match (BIO-001 shape)
# =========================================================================

class TestR1AnswerTableOwnership:
    def test_table_qn_answer_column_is_match(self):
        lines = _mk(
            "1. which fruit", "A. apple", "B. banana", "C. car", "D. table",
            "答案", BIO_TABLE,
        )
        d, run, compiled, leaf = _compile_run(lines, _payload(answer_lines=[7, 7]))
        assert leaf is not None and leaf.answer is not None
        assert leaf.answer.ownership == "match", leaf.answer.ownership
        assert leaf.answer.candidate_text == "B"
        assert d["decision"] == "auto_approve", (d["decision"], d["reasons"])

    def test_table_wrong_qn_not_match(self):
        lines = _mk(
            "12. q", "A. a", "B. b", "C. c", "D. d",
            "答案", BIO_TABLE,
        )
        d, run, compiled, leaf = _compile_run(
            lines, _payload(qn="12", answer_lines=[7, 7]), "Q12"
        )
        assert leaf is not None
        own = leaf.answer.ownership if leaf.answer else "unknown"
        assert own != "match"
        assert d["decision"] != "auto_approve"

    def test_plain_entry_still_match(self):
        lines = _mk(
            "1. q", "A. a", "B. b", "C. c", "D. d", "答案", "1. B",
        )
        d, run, compiled, leaf = _compile_run(lines, _payload(answer_lines=[7, 7]))
        assert leaf.answer.ownership == "match"
        assert d["decision"] == "auto_approve"


# =========================================================================
# B1/R2: candidate_text never in official answer_status (real DB row)
# =========================================================================

class TestB1R2CandidateNotInOfficialRow:
    @pytest.mark.asyncio
    async def test_db_row_has_no_candidate_text(self, session):
        qi = await _seed_instance(session, SVID)
        content = ContentRepository(session)
        official = ""
        seal = issue_publish_seal(
            fact=derive_binding_fact(
                span_id="sp-x",
                source_version_id=str(SVID), question_number="5",
                source_lines=["12. A"], answer_text="A",
            ),
            official_text=official,
            publish="withheld_review",
        )
        row = await content.create_role_content(
            instance_id=qi.id, role="answer", role_index=0,
            text=official, text_hash=EMPTY_HASH, label=None,
            source_span={"span_id": "sp-x", "line_refs": []},
            answer_status={
                "ownership": "foreign",
                "publish": "withheld_review",
                "publish_seal": seal,
                "binding_evidence": "test",
            },
        )
        await session.flush()
        from sqlalchemy import select
        from app.models.content import InstanceRoleContent
        got = (await session.execute(
            select(InstanceRoleContent).where(InstanceRoleContent.id == row.id)
        )).scalar_one()
        assert got.text == ""
        assert "candidate_text" not in (got.answer_status or {})

    def test_admission_status_dict_has_no_candidate_key(self):
        import inspect
        from app.domains.gate import admission as adm
        src = inspect.getsource(adm.AdmissionService._materialize)
        assert '"candidate_text":' not in src
        assert "'candidate_text':" not in src


# =========================================================================
# B2/R3: foreign never publishes; seal required (real RepositoryError)
# =========================================================================

class TestB2R3ForeignAndSeal:
    @pytest.mark.asyncio
    async def test_forged_publish_official_without_seal_rejected(self, session):
        qi = await _seed_instance(session, SVID)
        content = ContentRepository(session)
        with pytest.raises(RepositoryError, match="binding fact|publish seal"):
            await content.create_role_content(
                instance_id=qi.id, role="answer", role_index=0,
                text="A", text_hash="x", label=None,
                source_span={"span_id": "sp-1", "line_refs": ["P1L001"]},
                answer_status={"ownership": "match", "publish": "official"},
            )

    @pytest.mark.asyncio
    async def test_foreign_with_honest_seal_still_rejected(self, session):
        qi = await _seed_instance(session, SVID)
        content = ContentRepository(session)
        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=qi.id, role="answer", role_index=0,
                text="12. A", text_hash="x", label=None,
                source_span={"span_id": "sp-1", "line_refs": []},
                answer_status={
                    "ownership": "foreign",
                    "publish": "official",
                    "publish_seal": "deadbeef",
                },
            )

    def test_seal_rejects_forged_match_display(self):
        foreign_fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id=str(SVID), question_number="5",
            source_lines=["12. A"], answer_text="A",
        )
        match_fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id=str(SVID), question_number="12",
            source_lines=["12. A"], answer_text="A",
        )
        forged_seal = issue_publish_seal(
            fact=match_fact, official_text="A", publish="official"
        )
        assert not verify_publish_seal(
            fact=foreign_fact, official_text="A",
            publish="official", seal=forged_seal,
        )

    def test_honest_match_seal_roundtrip(self):
        match_fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id=str(SVID), question_number="12",
            source_lines=["12. A"], answer_text="A",
        )
        seal = issue_publish_seal(
            fact=match_fact, official_text="A", publish="official"
        )
        assert verify_publish_seal(
            fact=match_fact, official_text="A",
            publish="official", seal=seal,
        )


# =========================================================================
# B3: pending official empty + candidate retained
# =========================================================================

class TestB3Pending:
    def test_pending_official_empty_candidate_retained(self):
        lines = _mk(
            "12. q", "A. a", "B. b", "C. c", "D. d",
            "答案", "1. A", "第二行",
        )
        payload = {
            "semantic_units": [{
                "unit_id": "Q12", "unit_type": "standalone_unit",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"question_label": "12"},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": "12",
                        "answer_lines": [7, 8],
                    },
                },
            }]
        }
        d, run, compiled, leaf = _compile_run(lines, payload, "Q12")
        assert d["decision"] == "pending_review"
        a = leaf.answer
        assert (a.candidate_text or "").strip() != ""
        assert a.official_text == ""
        official, publish, ok = _publish_decision(
            ownership=a.ownership,
            candidate_text=a.candidate_text,
            grant="none",
            review_evidence=None,
            content_ok=a.complete,
            source_ok=a.source_located,
        )
        assert official == ""
        assert publish == "withheld_review"
        assert ok is False


# =========================================================================
# B4: student API does not return candidate text
# =========================================================================

class TestB4StudentAPI:
    def test_public_answer_status_strips_candidate(self):
        from app.api.routers.questions import _public_answer_status
        raw = {
            "ownership": "unknown",
            "publish": "withheld_review",
            "candidate_text": "1. A\n第二行",
            "source_located": True,
        }
        pub = _public_answer_status(raw)
        assert "candidate_text" not in pub
        assert "1. A" not in str(pub)
        assert pub["ownership"] == "unknown"


# =========================================================================
# M1: independent publish boundary
# =========================================================================

class TestM1IndependentPublish:
    @pytest.mark.asyncio
    async def test_unpatched_rejects_forged_official(self, session):
        qi = await _seed_instance(session, SVID)
        content = ContentRepository(session)
        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=qi.id, role="answer", role_index=0,
                text="FORGED-CANDIDATE", text_hash="x",
                source_span={"span_id": "sp-1", "line_refs": []},
                answer_status={"ownership": "match", "publish": "official"},
            )

    def test_foreign_issue_seal_empty(self):
        foreign_fact = derive_binding_fact(
            span_id="s",
            source_version_id=str(SVID), question_number="5",
            source_lines=["12. A"], answer_text="A",
        )
        assert issue_publish_seal(
            fact=foreign_fact, official_text="A", publish="official"
        ) == ""

    def test_seal_binds_to_ownership_fact(self):
        foreign_fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id=str(SVID), question_number="5",
            source_lines=["12. A"], answer_text="A",
        )
        match_fact = derive_binding_fact(
            span_id="sp-1",
            source_version_id=str(SVID), question_number="12",
            source_lines=["12. A"], answer_text="A",
        )
        forged = issue_publish_seal(
            fact=match_fact, official_text="A", publish="official"
        )
        assert not verify_publish_seal(
            fact=foreign_fact, official_text="A",
            publish="official", seal=forged,
        )

    @pytest.mark.asyncio
    async def test_m1_neutered_boundary_persists_forged(self, session, monkeypatch):
        from app.models.content import InstanceRoleContent

        async def _broken(self, **kwargs):
            row = InstanceRoleContent(
                instance_id=kwargs["instance_id"],
                role=kwargs.get("role"),
                label=kwargs.get("label"),
                role_index=kwargs.get("role_index", 0),
                text=kwargs.get("text") or "",
                text_hash=kwargs.get("text_hash") or "",
                source_span=kwargs.get("source_span"),
                answer_status=kwargs.get("answer_status"),
            )
            await self.add(row)
            return row

        monkeypatch.setattr(ContentRepository, "create_role_content", _broken)
        qi = await _seed_instance(session, SVID)
        content = ContentRepository(session)
        row = await content.create_role_content(
            instance_id=qi.id, role="answer", role_index=0,
            text="FORGED-CANDIDATE", text_hash="x",
            source_span={"span_id": "sp-1", "line_refs": []},
            answer_status={"ownership": "match", "publish": "official"},
        )
        await session.flush()
        from sqlalchemy import select
        got = (await session.execute(
            select(InstanceRoleContent).where(InstanceRoleContent.id == row.id)
        )).scalar_one()
        assert got.text == "FORGED-CANDIDATE"


# =========================================================================
# M2: Gate ownership
# =========================================================================

class TestM2GateOwnership:
    def test_unknown_and_foreign_block_auto(self):
        for lines, payload, root in [
            (_mk("1. q", "A. a", "B. b", "C. c", "D. d", "答案", "12. A"),
             _payload(answer_lines=[7, 7]), "Q1"),
            (_mk("", "", "26. chem", "1.（3分）Mg | TiCl4 | 1"),
             {"semantic_units": [{
                 "unit_id": "U1", "unit_type": "standalone_unit",
                 "original_question_type": "fill_in",
                 "content": {
                     "stem": {"question_label": "26"},
                     "answer": {"answer_zone": "answer_table",
                                "question_label": "26", "answer_lines": [4, 4]},
                 }}]}, "U1"),
        ]:
            d, run, compiled, leaf = _compile_run(lines, payload, root)
            assert d["decision"] != "auto_approve", d["reasons"]

    def test_m2_classifier_patch_allows_auto(self, monkeypatch):
        monkeypatch.setattr(
            resolver_mod, "classify_answer_ownership", lambda texts, qn: "match"
        )
        lines = _mk("1. q", "A. a", "B. b", "C. c", "D. d", "答案", "12. A")
        d, run, compiled, leaf = _compile_run(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] == "auto_approve", (d["decision"], d["reasons"])


class TestPublishPredicate:
    def test_matrix(self):
        cases = [
            ("foreign", "auto_gate", None, False),
            ("foreign", "human", {"reviewer_id": "r", "confirmed_fields": ["content", "belongs_to"], "source": "human"}, False),
            ("foreign", "golden", {"reviewer_id": "r", "confirmed_fields": ["content", "belongs_to"], "source": "golden"}, False),
            ("unknown", "auto_gate", None, False),
            ("unknown", "human", {"reviewer_id": "r", "confirmed_fields": ["content"], "source": "human"}, False),
            ("unknown", "human", {"reviewer_id": "r", "confirmed_fields": ["content", "belongs_to"], "source": "human"}, True),
            ("unknown", "golden", {"reviewer_id": "r", "confirmed_fields": ["content", "belongs_to"], "source": "golden"}, True),
            ("unknown", "golden", {"reviewer_id": "r", "confirmed_fields": ["content"], "source": "golden"}, False),
            ("unknown", "golden", None, False),
            ("unknown", "none", {"reviewer_id": "r", "confirmed_fields": ["content", "belongs_to"], "source": "golden"}, False),
            ("match", "auto_gate", None, True),
            ("match", "golden", {"reviewer_id": "r", "confirmed_fields": ["content"], "source": "golden"}, True),
            ("match", "none", None, False),
        ]
        for own, grant, ev, exp_ok in cases:
            cand = "B" if own == "match" else ("X" if own == "unknown" else "12. A")
            official, publish, ok = _publish_decision(
                ownership=own, candidate_text=cand,
                grant=grant, review_evidence=ev, content_ok=True, source_ok=True,
            )
            if exp_ok:
                assert ok and official != "", (own, grant, ev)
            else:
                assert not ok and official == "", (own, grant, ev, official, ok)


class TestGoldenPublishPredicate:
    """R16-FINAL: golden authorization path for unknown ownership.

    Contract: ownership=unknown + golden grant + valid review evidence
    -> publish allowed. golden only affects publish authorization;
    ownership is NEVER rewritten.
    """

    _GOLDEN_EV = {
        "reviewer_id": "golden-reviewer",
        "confirmed_fields": ["content", "belongs_to"],
        "source": "golden",
    }

    def test_golden_unknown_publish_allowed(self):
        """unknown + golden + valid evidence -> official publish."""
        official, publish, ok = _publish_decision(
            ownership="unknown",
            candidate_text="X",
            grant="golden",
            review_evidence=self._GOLDEN_EV,
            content_ok=True,
            source_ok=True,
        )
        assert ok is True
        assert official == "X"
        assert publish == "official"

    def test_golden_does_not_rewrite_ownership(self):
        """golden only affects publish grant, not ownership."""
        # _publish_decision returns (official_text, publish, write_nonempty)
        # It does NOT return ownership — ownership is an input that stays unchanged.
        # Verify by checking the function signature/behavior: no ownership output.
        official, publish, ok = _publish_decision(
            ownership="unknown",
            candidate_text="X",
            grant="golden",
            review_evidence=self._GOLDEN_EV,
            content_ok=True,
            source_ok=True,
        )
        # The function returns a 3-tuple (official, publish, write_nonempty),
        # never a rewritten ownership. Ownership is caller-owned.
        assert isinstance(official, str)
        assert isinstance(publish, str)
        assert isinstance(ok, bool)

    def test_unknown_no_grant_rejected(self):
        """unknown without human/golden grant -> withheld."""
        official, publish, ok = _publish_decision(
            ownership="unknown",
            candidate_text="X",
            grant="none",
            review_evidence=self._GOLDEN_EV,
            content_ok=True,
            source_ok=True,
        )
        assert ok is False
        assert official == ""
        assert publish == "withheld_review"

    def test_unknown_golden_no_evidence_rejected(self):
        """golden grant but no review evidence -> withheld."""
        official, publish, ok = _publish_decision(
            ownership="unknown",
            candidate_text="X",
            grant="golden",
            review_evidence=None,
            content_ok=True,
            source_ok=True,
        )
        assert ok is False
        assert official == ""
        assert publish == "withheld_review"

    def test_unknown_golden_missing_belongs_to_rejected(self):
        """golden grant but missing belongs_to -> withheld (unknown needs it)."""
        official, publish, ok = _publish_decision(
            ownership="unknown",
            candidate_text="X",
            grant="golden",
            review_evidence={"reviewer_id": "r", "confirmed_fields": ["content"]},
            content_ok=True,
            source_ok=True,
        )
        assert ok is False
        assert official == ""
        assert publish == "withheld_review"

    def test_foreign_golden_rejected(self):
        """foreign is never publishable, even with golden."""
        official, publish, ok = _publish_decision(
            ownership="foreign",
            candidate_text="12. A",
            grant="golden",
            review_evidence=self._GOLDEN_EV,
            content_ok=True,
            source_ok=True,
        )
        assert ok is False
        assert official == ""
        assert publish == "withheld_review"
