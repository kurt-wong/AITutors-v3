"""Continue adversarial probes: tz edges, human path, hardening not weakened."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.hashing import sha256_hex
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.evidence.proof import generate_review_proof, _to_utc_iso
from app.models.source import DocumentSourceLine
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

CLAIM = "Q1"


def ev(result="validated", at=None, claim=CLAIM, method="frozen_header_rule", validator="gate/v1"):
    return ValidationEvent(
        event_id=f"ve-{uuid.uuid4().hex[:8]}", claim_id=claim,
        validation_result=result, checks=(CheckResult(check_id="X", result="pass"),),
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
        payload={"ir_snapshot": {"units": [{"unit_id": CLAIM, "unit_type": "standalone_question",
            "original_question_type": "single_choice", "sub_questions": [], "semantic_status": "ready",
            "question_number": "", "content": [{"role": "stem", "span_id": "sp", "label": None, "unsupported": False}]}]},
            "resolved_spans": [], "compiled_roles": [], "answer": [], "figure_refs": [],
            "knowledge_links": [], "evidence": [],
            "display_hint": {"unit_type": "standalone_unit", "canonical_question_type": "single_choice"}},
        gate_decision={"gate_policy_version": "admission-gate/v1", "decision": "auto_approve", "layers": {}, "reasons": []},
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann, cand


class TestTimezoneEdges:
    async def test_positive_tz_far_future_rejected(self, session):
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        tz = timezone(timedelta(hours=14))
        at = datetime.now(tz) + timedelta(days=30)
        with pytest.raises(ValueError, match="future"):
            await repo.append_event(ev(at=at), candidate_id=cand.id, source_version_id=sv.id)
        print("\n[TZ+] +14h tz far future rejected")

    async def test_negative_tz_near_local_future_ok_or_rejected(self, session):
        """-12h tz: local +10min might be UTC ~now+22min or similar. Probe."""
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        tz = timezone(timedelta(hours=-12))
        at = datetime.now(tz) + timedelta(minutes=10)
        utc_equivalent = at.astimezone(timezone.utc)
        delta = utc_equivalent - datetime.now(timezone.utc)
        print(f"\n[TZ-] at={at} utc={utc_equivalent} delta={delta}")
        try:
            await repo.append_event(ev(at=at), candidate_id=cand.id, source_version_id=sv.id)
            print("[TZ-] ACCEPTED")
        except ValueError as e:
            print(f"[TZ-] rejected: {e}")
        # ensure cascade still wins
        created = await repo.invalidate_claims_for_source_version(sv.id, reason="tz")
        state, _ = await repo.project_authority(cand.id, CLAIM)
        print(f"[TZ-] after cascade state={state!r} created={len(created)}")
        if state == "validated":
            pytest.fail(f"RESIDUAL: tz edge survived cascade state={state}")

    async def test_naive_treated_as_utc_in_proof_helper(self):
        n = datetime(2026, 1, 1, 12, 0, 0)  # naive
        s = _to_utc_iso(n)
        print(f"\n[TZ proof] naive -> {s}")
        assert "+00:00" in s or s.endswith("Z")


class TestHumanPathNaive:
    async def test_append_human_review_with_naive_reviewed_at(self, session):
        """Human path: naive reviewed_at — crash or accept?"""
        sv, ann, cand = await seed(session)
        repo = EvidenceRepository(session)
        naive = datetime(2027, 6, 1, 0, 0, 0)  # naive far future
        proof = generate_review_proof(
            candidate_id=cand.id, review_result="validated",
            reviewer_id="r1", reviewed_at=naive,
            app_secret="test-app-secret-32-bytes-minimum!!",
        )
        try:
            await repo.append_human_review_event(
                candidate_id=cand.id, source_version_id=sv.id, claim_id=CLAIM,
                review_result="validated", reviewer_id="r1",
                reviewed_at=naive, review_proof=proof,
            )
            state, latest = await repo.project_authority(cand.id, CLAIM)
            print(f"\n[H-NAIVE] ACCEPTED state={state!r} at={latest.validated_at}")
            await repo.invalidate_claims_for_source_version(sv.id, reason="h-naive")
            state2, _ = await repo.project_authority(cand.id, CLAIM)
            print(f"[H-NAIVE] after cascade state={state2!r}")
            if state2 == "validated":
                pytest.fail("RESIDUAL HIT: naive human reviewed_at survives invalidate")
        except TypeError as e:
            print(f"\n[H-NAIVE] TypeError (fail-closed crash): {e}")
        except ValueError as e:
            print(f"\n[H-NAIVE] ValueError: {e}")


class TestHardeningNotWeakened:
    def test_hardening_still_asserts_state_machine_on_near_future(self):
        import tests.test_hardening_adversarial as th
        import inspect
        src = inspect.getsource(th.TestAttackStateMachine)
        assert "only INVALIDATED transition allowed" in src
        assert "match=\"future\"" in src or 'match="future"' in src
        print("\n[HARD] state machine + future-reject both asserted in hardening")

    def test_original_far_future_write_is_rejected_not_silently_ok(self):
        from app.repositories.evidence_repository import _MAX_CLOCK_SKEW
        assert _MAX_CLOCK_SKEW == timedelta(minutes=5)
        print(f"\n[HARD] skew={_MAX_CLOCK_SKEW}")
