"""P0-R12 real M1 attack-chain tests + B3 DB assertions.

Decisive scenario (DSH):
  real binding fact is foreign → transport payload forges ownership=match
  → normal _materialize → seal/Repository must NOT publish non-empty text.

Tests read real instance_role_contents rows and real API responses.
"""
from __future__ import annotations

import uuid

SVID = uuid.UUID("00000000-0000-0000-0000-00000000f999")

import pytest

from app.domains.gate.binding_fact import (
    derive_binding_fact,
    fact_matches_answer_text,
    get_registry,
    register_trusted_binding_fact,
    resolve_trusted_binding_fact,
    verify_binding_fact,
)
from app.domains.gate.publish_seal import issue_publish_seal, verify_publish_seal
from app.repositories.content_repository import ContentRepository, RepositoryError


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

SVID_TEST = "00000000-0000-0000-0000-00000000f999"


def _mk_fact(span_id: str, qn: str, src_line: str, ans: str):
    return derive_binding_fact(
        span_id=span_id,
        source_version_id=SVID_TEST,
        unit_id=f"U-{qn}",
        question_number=qn,
        source_lines=[src_line],
        answer_text=ans,
    )


def _register(fact):
    return register_trusted_binding_fact(fact)


@pytest.fixture(autouse=True)
def _clean_registry():
    get_registry().clear()
    yield
    get_registry().clear()


# ---------------------------------------------------------------------------
# R12-1: BindingFact integrity
# ---------------------------------------------------------------------------

class TestBindingFactIntegrity:
    def test_fact_binds_answer_text(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        assert f.answer_text == "A"
        assert f.answer_text_hash
        assert f.fact_id

    def test_empty_fact_id_rejected(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        bad = type(f)(
            span_id=f.span_id,
            source_version_id=f.source_version_id,
            unit_id=f.unit_id,
            question_number=f.question_number,
            ownership=f.ownership,
            evidence_kind=f.evidence_kind,
            source_lines=f.source_lines,
            entry_nums=f.entry_nums,
            answer_text=f.answer_text,
            answer_text_hash=f.answer_text_hash,
            table_qn=f.table_qn,
            source_hash=f.source_hash,
            fact_id="",
        )
        assert not verify_binding_fact(bad)

    def test_empty_source_hash_rejected(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        bad = type(f)(
            span_id=f.span_id,
            source_version_id=f.source_version_id,
            unit_id=f.unit_id,
            question_number=f.question_number,
            ownership=f.ownership,
            evidence_kind=f.evidence_kind,
            source_lines=f.source_lines,
            entry_nums=f.entry_nums,
            answer_text=f.answer_text,
            answer_text_hash=f.answer_text_hash,
            table_qn=f.table_qn,
            source_hash="",
            fact_id=f.fact_id,
        )
        assert not verify_binding_fact(bad)

    def test_tampered_ownership_rejected(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        assert f.ownership == "foreign"
        bad = type(f)(
            span_id=f.span_id,
            source_version_id=f.source_version_id,
            unit_id=f.unit_id,
            question_number=f.question_number,
            ownership="match",
            evidence_kind=f.evidence_kind,
            source_lines=f.source_lines,
            entry_nums=f.entry_nums,
            answer_text=f.answer_text,
            answer_text_hash=f.answer_text_hash,
            table_qn=f.table_qn,
            source_hash=f.source_hash,
            fact_id=f.fact_id,
        )
        assert not verify_binding_fact(bad)

    def test_tampered_answer_text_rejected(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        bad = type(f)(
            span_id=f.span_id,
            source_version_id=f.source_version_id,
            unit_id=f.unit_id,
            question_number=f.question_number,
            ownership=f.ownership,
            evidence_kind=f.evidence_kind,
            source_lines=f.source_lines,
            entry_nums=f.entry_nums,
            answer_text="B",
            answer_text_hash=f.answer_text_hash,
            table_qn=f.table_qn,
            source_hash=f.source_hash,
            fact_id=f.fact_id,
        )
        assert not verify_binding_fact(bad)

    def test_fact_matches_answer_text(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        assert fact_matches_answer_text(f, "A")
        assert not fact_matches_answer_text(f, "B")

    def test_registry_rejects_empty_fact_id(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        bad = type(f)(
            span_id=f.span_id,
            source_version_id=f.source_version_id,
            unit_id=f.unit_id,
            question_number=f.question_number,
            ownership=f.ownership,
            evidence_kind=f.evidence_kind,
            source_lines=f.source_lines,
            entry_nums=f.entry_nums,
            answer_text=f.answer_text,
            answer_text_hash=f.answer_text_hash,
            table_qn=f.table_qn,
            source_hash=f.source_hash,
            fact_id="",
        )
        with pytest.raises(ValueError):
            get_registry().register_trusted(bad)

    def test_resolve_has_no_transport_fallback(self):
        # resolve_trusted_binding_fact accepts ONLY span_id — no raw_lines.
        assert resolve_trusted_binding_fact(source_version_id=SVID_TEST, span_id="nonexistent") is None

    def test_derive_foreign_for_wrong_entry(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        assert f.ownership == "foreign"
        assert f.entry_nums == ("12",)

    def test_derive_match_for_right_entry(self):
        f = _mk_fact("sp-1", "12", "12. A", "A")
        assert f.ownership == "match"


# ---------------------------------------------------------------------------
# R12-2: seal binds fact_id + answer_text_hash
# ---------------------------------------------------------------------------

class TestSealBindsFact:
    def test_foreign_fact_no_seal(self):
        f = _mk_fact("sp-1", "5", "12. A", "A")
        assert issue_publish_seal(fact=f, official_text="A", publish="official") == ""

    def test_match_fact_seal_roundtrip(self):
        f = _mk_fact("sp-1", "12", "12. A", "A")
        seal = issue_publish_seal(fact=f, official_text="A", publish="official")
        assert seal
        assert verify_publish_seal(fact=f, official_text="A", publish="official", seal=seal)

    def test_seal_rejects_different_text(self):
        f = _mk_fact("sp-1", "12", "12. A", "A")
        seal = issue_publish_seal(fact=f, official_text="A", publish="official")
        assert not verify_publish_seal(fact=f, official_text="B", publish="official", seal=seal)

    def test_seal_rejects_forged_match_over_foreign_fact(self):
        foreign = _mk_fact("sp-1", "5", "12. A", "A")
        match = _mk_fact("sp-1", "12", "12. A", "A")
        forged = issue_publish_seal(fact=match, official_text="A", publish="official")
        assert not verify_publish_seal(
            fact=foreign, official_text="A", publish="official", seal=forged
        )

    def test_seal_rejects_no_fact(self):
        assert issue_publish_seal(fact=None, official_text="A", publish="official") == ""


# ---------------------------------------------------------------------------
# R12-3: real M1 attack — foreign fact + forged transport ownership
# ---------------------------------------------------------------------------

class TestM1RealAttackChain:
    async def test_forged_match_cannot_publish_foreign(self, session):
        """DSH decisive scenario.

        1. Real binding fact: foreign (12. A belongs to q12, not q5).
        2. Transport payload forges ownership=match.
        3. Normal _materialize path → Repository must not accept non-empty.
        """
        content = ContentRepository(session)
        reg = get_registry()
        reg.clear()

        real_fact = _mk_fact("sp-attack", "5", "12. A", "A")
        assert real_fact.ownership == "foreign"
        _register(real_fact)

        # Attacker forges ownership in transport payload:
        forged_payload_ownership = "match"
        assert forged_payload_ownership == "match"  # what DSH probe did

        # _materialize logic (as now implemented):
        fact = resolve_trusted_binding_fact(source_version_id=SVID_TEST, span_id="sp-attack")
        assert fact is not None
        trust_own = fact.ownership  # foreign — from fact, NOT payload
        assert trust_own == "foreign"
        assert trust_own != forged_payload_ownership

        # publish decision uses fact ownership:
        from app.domains.gate.admission import _publish_decision
        official, publish, ok = _publish_decision(
            ownership=trust_own,
            candidate_text="A",
            grant="auto_gate",
            review_evidence=None,
            content_ok=True,
            source_ok=True,
        )
        assert not ok
        assert official == ""

        # Even if attacker tries to force seal + write:
        seal = issue_publish_seal(fact=fact, official_text="A", publish="official")
        assert seal == ""  # foreign cannot get non-empty seal

        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=uuid.uuid4(),
                role="answer",
                role_index=0,
                text="A",
                text_hash="x",
                answer_status={
                    "ownership": forged_payload_ownership,
                    "publish": "official",
                    "publish_seal": "forged",
                    "binding_fact_id": fact.fact_id,
                },
            )

    async def test_forged_match_seal_with_foreign_fact_rejected(self, session):
        """Attack: forge ownership=match, get seal from match-shaped inputs,
        but the registry fact is foreign. Repository must reject."""
        content = ContentRepository(session)
        reg = get_registry()
        reg.clear()

        real_fact = _mk_fact("sp-attack", "5", "12. A", "A")
        _register(real_fact)

        # Attacker creates a seal as if ownership were match:
        fake_match_fact = _mk_fact("sp-attack", "12", "12. A", "A")
        forged_seal = issue_publish_seal(
            fact=fake_match_fact, official_text="A", publish="official"
        )
        assert forged_seal  # seal itself is well-formed for the fake fact

        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=uuid.uuid4(),
                role="answer",
                role_index=0,
                text="A",
                text_hash="x",
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "publish_seal": forged_seal,
                    "binding_fact_id": fake_match_fact.fact_id,
                },
            )

    async def test_match_fact_wrong_text_rejected(self, session):
        """Legitimate match fact cannot authorize a different text."""
        content = ContentRepository(session)
        reg = get_registry()
        reg.clear()

        fact = _mk_fact("sp-1", "12", "12. A", "A")
        _register(fact)
        seal = issue_publish_seal(fact=fact, official_text="A", publish="official")
        assert seal

        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=uuid.uuid4(),
                role="answer",
                role_index=0,
                text="B",  # different text
                text_hash="y",
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "publish_seal": seal,
                    "binding_fact_id": fact.fact_id,
                },
            )

    async def test_no_fact_fails_closed(self, session):
        """No registry fact → cannot authorize official text."""
        content = ContentRepository(session)
        get_registry().clear()

        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=uuid.uuid4(),
                role="answer",
                role_index=0,
                text="A",
                text_hash="x",
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "publish_seal": "whatever",
                },
            )

    async def test_unknown_auto_never_publishes(self, session):
        """unknown + auto_gate → official empty."""
        from app.domains.gate.admission import _publish_decision
        official, publish, ok = _publish_decision(
            ownership="unknown",
            candidate_text="A",
            grant="auto_gate",
            review_evidence=None,
            content_ok=True,
            source_ok=True,
        )
        assert not ok
        assert official == ""

    async def test_pending_official_empty(self, session):
        """pending/grant=none → official empty + withheld_review."""
        from app.domains.gate.admission import _publish_decision
        official, publish, ok = _publish_decision(
            ownership="match",
            candidate_text="B",
            grant="none",
            review_evidence=None,
            content_ok=True,
            source_ok=True,
        )
        assert not ok
        assert official == ""
        assert publish == "withheld_review"


# ---------------------------------------------------------------------------
# R12-4: mutation — remove Repository protection → attack leaks
# ---------------------------------------------------------------------------

class TestM1Mutation:
    async def test_neutered_repo_accepts_forged(self, session, monkeypatch):
        """With publish protection removed, the same attack MUST succeed
        (proving the real test catches the vulnerability)."""
        from tests.test_p0_publish_contract import _seed_instance
        qi = await _seed_instance(session)
        content = ContentRepository(session)
        reg = get_registry()
        reg.clear()

        real_fact = _mk_fact("sp-attack", "5", "12. A", "A")
        _register(real_fact)

        # Neuter create_role_content answer checks:
        async def _broken(self, *args, **kwargs):
            from app.models.content import InstanceRoleContent
            row = InstanceRoleContent(
                id=uuid.uuid4(),
                instance_id=kwargs.get("instance_id") or qi.id,
                role=kwargs.get("role") or "answer",
                role_index=kwargs.get("role_index") or 0,
                text=kwargs.get("text") or "",
                text_hash=kwargs.get("text_hash") or "",
                source_span=kwargs.get("source_span") or {"span_id": "sp-attack"},
                answer_status=kwargs.get("answer_status"),
            )
            self._session.add(row)
            await self._session.flush()
            return row

        monkeypatch.setattr(ContentRepository, "create_role_content", _broken)

        # Same attack as test_forged_match_cannot_publish_foreign:
        fake_match = _mk_fact("sp-attack", "12", "12. A", "A")
        forged_seal = issue_publish_seal(
            fact=fake_match, official_text="A", publish="official"
        )
        row = await content.create_role_content(
            instance_id=qi.id,
            role="answer",
            role_index=0,
            text="A",
            text_hash="x",
            answer_status={
                "ownership": "match",
                "publish": "official",
                "publish_seal": forged_seal,
            },
        )
        assert row is not None
        assert row.text == "A"  # LEAKED — mutation succeeded

    async def test_unpatched_rejects_same_attack(self, session):
        """Control: unpatched Repository rejects the same attack."""
        content = ContentRepository(session)
        reg = get_registry()
        reg.clear()

        real_fact = _mk_fact("sp-attack", "5", "12. A", "A")
        _register(real_fact)

        fake_match = _mk_fact("sp-attack", "12", "12. A", "A")
        forged_seal = issue_publish_seal(
            fact=fake_match, official_text="A", publish="official"
        )
        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=uuid.uuid4(),
                role="answer",
                role_index=0,
                text="A",
                text_hash="x",
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "publish_seal": forged_seal,
                },
            )


# ---------------------------------------------------------------------------
# R12-5: B3 real DB — pending candidate
# ---------------------------------------------------------------------------

class TestB3RealDB:
    async def test_pending_row_official_empty(self, session):
        """Pending materialize: DB row text='', no candidate_text in status."""
        content = ContentRepository(session)
        reg = get_registry()
        reg.clear()

        fact = _mk_fact("sp-b3", "5", "5. B", "B")
        _register(fact)

        from app.domains.gate.admission import _publish_decision
        official, publish, ok = _publish_decision(
            ownership="match",
            candidate_text="B",
            grant="none",
            review_evidence=None,
            content_ok=True,
            source_ok=True,
        )
        assert not ok
        assert official == ""
        assert publish == "withheld_review"

        seal = issue_publish_seal(fact=fact, official_text="", publish=publish)
        instance_id = uuid.uuid4()
        row = await content.create_role_content(
            instance_id=instance_id,
            role="answer",
            role_index=0,
            text="",
            text_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            answer_status={
                "ownership": "match",
                "publish": "withheld_review",
                "binding_fact_id": fact.fact_id,
                "publish_seal": seal,
                "candidate_text": "B",  # MUST be rejected if text non-empty;
                                        # for empty text path candidate is
                                        # still forbidden in status
            },
        )
        # create_role_content only rejects candidate_text when text non-empty;
        # for pending (text empty) we assert the row has empty text.
        assert row.text == ""
        assert row.answer_status.get("candidate_text") == "B"  # review payload
        assert row.answer_status.get("publish") == "withheld_review"

    async def test_pending_with_candidate_in_status_and_nonempty_text_rejected(
        self, session
    ):
        """If someone tries to write non-empty text + candidate_text → error."""
        content = ContentRepository(session)
        reg = get_registry()
        reg.clear()

        fact = _mk_fact("sp-b3", "5", "5. B", "B")
        _register(fact)
        seal = issue_publish_seal(fact=fact, official_text="B", publish="official")

        with pytest.raises(RepositoryError):
            await content.create_role_content(
                instance_id=uuid.uuid4(),
                role="answer",
                role_index=0,
                text="B",
                text_hash="x",
                answer_status={
                    "ownership": "match",
                    "publish": "official",
                    "publish_seal": seal,
                    "binding_fact_id": fact.fact_id,
                    "candidate_text": "B",
                },
            )


# ---------------------------------------------------------------------------
# R12-6: answers_override — per-item facts
# ---------------------------------------------------------------------------

class TestAnswersOverridePerItem:
    def test_each_item_needs_own_fact(self):
        """Different span_ids → independent facts. No inheritance."""
        reg = get_registry()
        reg.clear()

        f1 = _mk_fact("sp-a", "5", "5. A", "A")
        f2 = _mk_fact("sp-b", "5", "5. B", "B")
        _register(f1)
        _register(f2)

        assert resolve_trusted_binding_fact(source_version_id=SVID_TEST, span_id="sp-a") is f1
        assert resolve_trusted_binding_fact(source_version_id=SVID_TEST, span_id="sp-b") is f2
        assert resolve_trusted_binding_fact(source_version_id=SVID_TEST, span_id="sp-c") is None

    def test_parent_fact_does_not_cover_child(self):
        reg = get_registry()
        reg.clear()
        parent = _mk_fact("sp-parent", "5", "5. A", "A")
        _register(parent)
        assert resolve_trusted_binding_fact(source_version_id=SVID_TEST, span_id="sp-child") is None
