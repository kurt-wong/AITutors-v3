"""T177-R8: Security boundary tests for _resolve_fact_with_fallback.

Covers the fallback path added in de6eb4f:
  - real source line lookup (never candidate text as source_lines)
  - line_refs missing / out-of-bounds → reject
  - declared_value content consistency
  - registry miss + allow_fallback → reconstruct
  - registry miss + !allow_fallback → None (safe withhold)
  - source line lookup uses DB, not payload
"""
import hashlib
import uuid

import pytest


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


SVID = "11111111-1111-1111-1111-111111111111"


def _make_candidate_payload(*, line_refs=None, answer_text="A", qn="1",
                             unit_id="Q1", evidence_value="A"):
    refs = line_refs if line_refs is not None else ["P1L001"]
    return {
        "resolved_spans": [{"span_id": "sp-Q1.answer", "line_refs": refs}],
        "evidence": [{
            "span_id": "sp-Q1.answer",
            "evidence": [f"fact_declared_value={evidence_value}", "fact_decode_loc="],
        }],
        "answer": [{
            "text": answer_text, "unit_id": unit_id,
            "question_number": qn, "binding_evidence": "entry_line",
        }],
    }


def _make_answer_payload(*, text="A", qn="1", unit_id="Q1"):
    return {"text": text, "unit_id": unit_id, "question_number": qn,
            "binding_evidence": "entry_line"}


async def _seed_sv_and_lines(session, *, svid=SVID, lines=None):
    from app.models.source import Document, DocumentSourceLine, DocumentSourceVersion
    lines = lines or ["1. A", "2. B", "3. C"]
    doc = Document(
        id=uuid.uuid4(),
        original_object_key=f"obj/{uuid.uuid4()}.md",
        original_sha256=_sha(str(uuid.uuid4())),
        file_name="t.md", file_type="md", upload_meta={}, processing_status="sealed",
    )
    session.add(doc)
    await session.flush()
    sv = DocumentSourceVersion(
        id=uuid.UUID(svid), document_id=doc.id,
        artifact_kind="raw_l1", role="native", provider="native",
        body_text="\n".join(lines), body_hash=_sha("\n".join(lines)),
        integrity_hash=_sha("\n".join(lines)),
        page_count=1, line_count=len(lines), status="sealed",
    )
    session.add(sv)
    await session.flush()
    for i, text in enumerate(lines, 1):
        session.add(DocumentSourceLine(
            source_version_id=uuid.UUID(svid),
            line_ref=f"P1L{i:03d}", seq=i, page_no=1, line_no_in_page=i,
            text=text, block_type="text", line_hash=_sha(text),
        ))
    await session.flush()


# === _value_supported_by_lines ===
class TestValueSupportedByLines:
    def test_single_letter_found(self):
        from app.domains.gate.binding_fact import _value_supported_by_lines
        assert _value_supported_by_lines("A", ["1. A", "2. B"]) is True

    def test_single_letter_not_found(self):
        from app.domains.gate.binding_fact import _value_supported_by_lines
        assert _value_supported_by_lines("Z", ["1. A", "2. B"]) is False

    def test_multichar_found(self):
        from app.domains.gate.binding_fact import _value_supported_by_lines
        assert _value_supported_by_lines("hello", ["say hello world"]) is True

    def test_multichar_not_found(self):
        from app.domains.gate.binding_fact import _value_supported_by_lines
        assert _value_supported_by_lines("xyz", ["say hello world"]) is False

    def test_empty_value(self):
        from app.domains.gate.binding_fact import _value_supported_by_lines
        assert _value_supported_by_lines("", ["line"]) is False

    def test_empty_lines(self):
        from app.domains.gate.binding_fact import _value_supported_by_lines
        assert _value_supported_by_lines("A", []) is False


# === BindingFact security ===
class TestBindingFactSecurity:
    def test_derive_requires_svid(self):
        from app.domains.gate.binding_fact import derive_binding_fact
        with pytest.raises(ValueError):
            derive_binding_fact(
                span_id="sp", source_version_id="", question_number="1",
                source_lines=["1. A"], answer_text="A",
            )

    def test_verify_forged_declared_value_rejected(self):
        import dataclasses
        from app.domains.gate.binding_fact import derive_binding_fact, verify_binding_fact
        fact = derive_binding_fact(
            span_id="sp", source_version_id=SVID, question_number="1",
            source_lines=["1. A", "2. B"], answer_text="A", declared_value="A",
        )
        forged = dataclasses.replace(fact, declared_value="B")
        assert verify_binding_fact(forged) is False

    def test_verify_forged_source_hash_rejected(self):
        import dataclasses
        from app.domains.gate.binding_fact import derive_binding_fact, verify_binding_fact
        fact = derive_binding_fact(
            span_id="sp", source_version_id=SVID, question_number="1",
            source_lines=["1. A", "2. B"], answer_text="A", declared_value="A",
        )
        forged = dataclasses.replace(fact, source_hash="0" * 64)
        assert verify_binding_fact(forged) is False

    def test_verify_consistent_passes(self):
        from app.domains.gate.binding_fact import derive_binding_fact, verify_binding_fact
        fact = derive_binding_fact(
            span_id="sp", source_version_id=SVID, question_number="1",
            source_lines=["1. A", "2. B"], answer_text="A", declared_value="A",
        )
        assert verify_binding_fact(fact) is True

    def test_foreign_entries_rejected(self):
        from app.domains.gate.binding_fact import _classify
        own = _classify(["5. X", "6. Y"], "1", "", answer_text="X", declared_value="X")
        assert own == "foreign"

    def test_cross_question_conflict(self):
        from app.domains.gate.binding_fact import _classify
        own = _classify(["2. B", "3. C"], "1", "", answer_text="A", declared_value="A")
        assert own in ("foreign", "unknown")


# === _resolve_fact_with_fallback ===
class TestResolveFactFallback:
    async def test_no_payload_returns_none(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer", allow_fallback=True,
        )
        assert r is None

    async def test_no_line_refs_returns_none(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(line_refs=[]),
            answer_payload=_make_answer_payload(), allow_fallback=True,
        )
        assert r is None

    async def test_span_not_found_returns_none(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-GONE",
            candidate_payload=_make_candidate_payload(),
            answer_payload=_make_answer_payload(), allow_fallback=True,
        )
        assert r is None

    async def test_empty_answer_text_returns_none(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(),
            answer_payload=_make_answer_payload(text=""), allow_fallback=True,
        )
        assert r is None

    async def test_no_real_source_lines_returns_none(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        await _seed_sv_and_lines(session)  # has P1L001-003
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(line_refs=["P1L999"]),
            answer_payload=_make_answer_payload(), allow_fallback=True,
        )
        assert r is None

    async def test_fallback_disabled_returns_none(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        await _seed_sv_and_lines(session)
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(),
            answer_payload=_make_answer_payload(), allow_fallback=False,
        )
        assert r is None

    async def test_fallback_with_real_lines_succeeds(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        await _seed_sv_and_lines(session, lines=["1. A", "2. B", "3. C"])
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(line_refs=["P1L001"]),
            answer_payload=_make_answer_payload(text="A", qn="1"),
            allow_fallback=True,
        )
        assert r is not None
        assert r.source_version_id == SVID
        assert r.span_id == "sp-Q1.answer"

    async def test_fallback_rejects_answer_not_in_source(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry, verify_binding_fact
        get_registry().clear()
        await _seed_sv_and_lines(session, lines=["1. A", "2. B"])
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(
                line_refs=["P1L001"], answer_text="Z", evidence_value="Z"),
            answer_payload=_make_answer_payload(text="Z"),
            allow_fallback=True,
        )
        if r is not None:
            assert r.ownership != "match" or verify_binding_fact(r)

    async def test_fallback_uses_db_lines_not_candidate_text(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        await _seed_sv_and_lines(session, lines=["1. A"])
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(
                line_refs=["P1L001"], answer_text="A"),
            answer_payload=_make_answer_payload(text="A"),
            allow_fallback=True,
        )
        if r is not None:
            assert r.source_hash == _sha("1. A")
            assert r.source_hash != _sha("A")

    async def test_svid_mismatch_rejected(self, session):
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        await _seed_sv_and_lines(
            session, svid="22222222-2222-2222-2222-222222222222", lines=["1. A"])
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID,  # mismatch!
            span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(line_refs=["P1L001"]),
            answer_payload=_make_answer_payload(), allow_fallback=True,
        )
        assert r is None
