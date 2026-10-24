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


class TestValueSupportedNegative:
    """Negative tests: tolerance must NOT weaken answer verification."""

    def test_different_answer_rejected(self):
        """Source says A, value says B → reject."""
        from app.domains.gate.binding_fact import _value_supported_by_lines
        assert _value_supported_by_lines("B", ["1. A"]) is False

    def test_different_content_rejected(self):
        """Source has one answer, value has different answer → reject."""
        from app.domains.gate.binding_fact import _value_supported_by_lines
        assert _value_supported_by_lines(
            "孔子回答子路", ["孟子回答梁惠王"]
        ) is False

    def test_partial_overlap_rejected(self):
        """Value shares <70% with source → reject."""
        from app.domains.gate.binding_fact import _value_supported_by_lines
        src = "①久在樊笼里复得返自然②无以至今日无以终余年③醉不成欢惨将别别时茫茫江浸月"
        val = "①久在樊笼里复得返自然②完全不同③完全不同④完全不同"
        assert _value_supported_by_lines(val, [src]) is False

    def test_paraphrase_with_annotations_allowed(self):
        """Value with (重点字：X) annotations stripped → allow."""
        from app.domains.gate.binding_fact import _value_supported_by_lines
        src = "【解答】①久在樊笼里复得返自然（重点字：返）②无以至今日（重点字：至）"
        val = "①久在樊笼里复得返自然②无以至今日"
        assert _value_supported_by_lines(val, [src]) is True

    def test_fullwidth_parens_normalized(self):
        """Full-width （） vs half-width () → allow after normalization."""
        from app.domains.gate.binding_fact import _value_supported_by_lines
        src = "（1）A（2）B（3）C"
        val = "(1)A(2)B(3)C"
        assert _value_supported_by_lines(val, [src]) is True

    def test_high_overlap_wrong_answer_rejected(self):
        """CRITICAL: >70% overlap but wrong sub-answer → must reject."""
        from app.domains.gate.binding_fact import _value_supported_by_lines
        src = "①久在樊笼里复得返自然②无以至今日无以终余年③醉不成欢惨将别别时茫茫江浸月④千里逢迎高朋满座⑤群贤毕至少长咸集"
        val = "①久在樊笼里复得返自然②无以至今日无以终余年③醉不成欢惨将别别时茫茫江浸月④千里逢迎高朋满座⑤完全不同完全错误"
        assert _value_supported_by_lines(val, [src]) is False

    def test_high_overlap_wrong_letter_rejected(self):
        """CRITICAL: >70% overlap but wrong answer letter → must reject."""
        from app.domains.gate.binding_fact import _value_supported_by_lines
        src = "1. A 2. B 3. C 4. D 5. A 6. B 7. C 8. D 9. A 10. B"
        val = "1. A 2. B 3. C 4. D 5. A 6. B 7. C 8. D 9. A 10. C"
        assert _value_supported_by_lines(val, [src]) is False


# === Composite parent qn (Chinese sub-entries （1）（2）… under global qn) ===
class TestCompositeParentQn:
    def test_fw_paren_contiguous_entries_match(self):
        """Q4-style: parent qn=4, entries （1）（2）（3） contiguous → match."""
        from app.domains.resolver.resolver import classify_answer_ownership
        texts = ["（1）D。", "（2）A。", "（3）虎啸龙吟与和缓相对。"]
        assert classify_answer_ownership(texts, "4") == "match"

    def test_fw_paren_qn6_entries_match(self):
        """Q6-style: parent qn=6, entries （1）..（5） contiguous → match."""
        from app.domains.resolver.resolver import classify_answer_ownership
        texts = ["（1）B。", "（2）D。", "（3）第三段。", "（4）寓意。", "（5）启示。"]
        assert classify_answer_ownership(texts, "6") == "match"

    def test_plain_period_entries_still_foreign(self):
        """Plain `N.` entries with target > N are foreign, NOT composite."""
        from app.domains.resolver.resolver import classify_answer_ownership
        texts = ["1. A", "2. B", "3. C"]
        assert classify_answer_ownership(texts, "4") == "foreign"

    def test_non_contiguous_fw_paren_still_foreign(self):
        """Non-contiguous （1）（3） entries are NOT composite sub-parts."""
        from app.domains.resolver.resolver import classify_answer_ownership
        texts = ["（1）A", "（3）B"]
        assert classify_answer_ownership(texts, "5") == "foreign"

    def test_target_within_entries_still_match(self):
        """When target IS in entry_nums, direct match wins (no composite path)."""
        from app.domains.resolver.resolver import classify_answer_ownership
        texts = ["（2）A", "（3）B"]
        assert classify_answer_ownership(texts, "2") == "match"

    def test_target_le_max_entry_still_foreign(self):
        """target ≤ max entry and not in entry_nums → foreign (not composite)."""
        from app.domains.resolver.resolver import classify_answer_ownership
        texts = ["（1）A", "（3）B"]
        assert classify_answer_ownership(texts, "2") == "foreign"


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
        """Registry miss + real source lines → must return fact with match ownership."""
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
        assert r.ownership == "match", f"expected match, got {r.ownership}"

    async def test_fallback_rejects_answer_not_in_source(self, session):
        """answer_text='Z' but source says '1. A' → MUST return None."""
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
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
        assert r is None, "answer not in source must be rejected, got fact"

    async def test_fallback_uses_db_lines_not_candidate_text(self, session):
        """MUST return fact; source_hash from DB line, not candidate text."""
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
        assert r is not None, "fallback must reconstruct from real DB lines"
        assert r.source_hash == _sha("1. A"), "must hash real DB line, not candidate text"
        assert r.source_hash != _sha("A"), "must NOT self-proof with candidate text"

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

    async def test_content_gate_blocks_unknown_fact(self, session):
        """Source says '1. A' but answer is 'Z' → fallback must return None,
        NOT an unknown fact that human/golden could later publish as official."""
        from app.domains.gate.admission import AdmissionService
        from app.domains.gate.binding_fact import get_registry
        get_registry().clear()
        await _seed_sv_and_lines(session, lines=["1. A", "2. B", "3. C"])
        svc = AdmissionService(session)
        r = await svc._resolve_fact_with_fallback(
            source_version_id=SVID, span_id="sp-Q1.answer",
            candidate_payload=_make_candidate_payload(
                line_refs=["P1L001"], answer_text="Z", evidence_value="Z"),
            answer_payload=_make_answer_payload(text="Z"),
            allow_fallback=True,
        )
        assert r is None, (
            f"must reject unsupported answer, got ownership={getattr(r, 'ownership', None)}"
        )
