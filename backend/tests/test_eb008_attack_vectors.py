"""EB-008 P1 攻击向量测试（MIMO adversarial，2026-09-29）。

范围：92号 §5 / Implementation Notes §7 手册之外的边界攻击。
已接受风险 R-1..R-4 不当作新发现重复上报（Notes §6）。

FINDING-1 (A1) 已修复：未来时间戳劫持 invalidate 投影 → 修复后为回归测试。
FINDING-2 (A2) 登记：伪造机器 VALIDATED 事件可驱动 auto_approve（无 Gate 溯源绑定）。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.hashing import sha256_hex
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.evidence.proof import generate_review_proof, verify_review_proof
from app.domains.gate.admission import AdmissionService
from app.repositories.base import RepositoryError
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository
from app.models.source import DocumentSourceLine

CLAIM_ID = "Q1"
SECRET = "test-app-secret-32-bytes-minimum!!"


def _event(
    *,
    claim_id: str = CLAIM_ID,
    result: str = "validated",
    method: str = "frozen_header_rule",
    validator: str = "gate/v1",
    validated_at: datetime | None = None,
) -> ValidationEvent:
    return ValidationEvent(
        event_id=f"ve-{claim_id}-{uuid.uuid4().hex[:8]}",
        claim_id=claim_id,
        validation_result=result,
        checks=(CheckResult(check_id="BYTE_PROVEN", result="pass"),),
        validation_method=method,
        validator=validator,
        validated_at=validated_at or datetime.now(timezone.utc),
    )


def _payload() -> dict:
    return {
        "ir_snapshot": {
            "ir_schema": "semantic-question-ir/v0.3",
            "units": [
                {"unit_id": "Q1", "unit_type": "standalone_question",
                 "question_number": "", "question_number_range": None,
                 "original_question_type": "single_choice",
                 "content": [{"role": "stem", "span_id": "sp-Q1.stem", "label": None,
                              "unsupported": False}],
                 "shared_components": [], "relations": [], "semantic_status": "ready",
                 "sub_questions": []},
            ],
        },
        "resolved_spans": [
            {"span_id": "sp-Q1.stem", "role": "stem", "granularity": "line",
             "line_refs": ["P1L001"], "start_offset": None, "end_offset": None,
             "text_hash": "0" * 64, "resolution_status": "exact"},
        ],
        "compiled_roles": [
            {"role": "stem", "span_id": "sp-Q1.stem", "line_refs": ["P1L001"],
             "text": "1. fruit", "text_hash": sha256_hex("1. fruit"),
             "label": None, "unit_id": "Q1", "kind": "content"},
            {"role": "option", "span_id": "sp-Q1.option.A", "line_refs": ["P1L002"],
             "text": "A. apple", "text_hash": sha256_hex("A. apple"),
             "label": "A", "unit_id": "Q1", "kind": "content"},
            {"role": "option", "span_id": "sp-Q1.option.B", "line_refs": ["P1L003"],
             "text": "B. car", "text_hash": sha256_hex("B. car"),
             "label": "B", "unit_id": "Q1", "kind": "content"},
        ],
        "answer": [
            {"unit_id": "Q1", "question_number": "", "span_id": "sp-Q1.answer",
             "line_refs": ["P1L007"], "text": "1. A", "text_hash": sha256_hex("1. A"),
             "source_located": True, "complete": True, "verified_correct": None},
        ],
        "figure_refs": [], "knowledge_links": [],
        "evidence": [], "display_hint": {"unit_type": "standalone_unit",
                                          "canonical_question_type": "single_choice"},
    }


def _auto_gd():
    return {"gate_policy_version": "admission-gate/v1", "decision": "auto_approve",
            "layers": {}, "reasons": []}


async def _seed_materializable(session, *, gate=None):
    texts = ("1. fruit", "A. apple", "B. car", "【答案】", "1. A")
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="g.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
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
            source_version_id=sv.id, line_ref=f"P1L{i + 1:03d}", seq=i + 1,
            page_no=1, line_no_in_page=i + 1, text=t, block_type="text",
            line_hash=sha256_hex(t),
        ))
    await session.flush()
    await src.seal_version(sv.id)
    await session.flush()
    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id,
        annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1", model_config_hash=sha256_hex("m"),
        payload={"semantic_units": [],
                 "document_metadata_claims": {"subject": "math", "grade": "3"}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    cand = await SnapshotRepository(session).create_admission_candidate(
        unit_type="standalone_unit", source_version_id=sv.id, annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=_payload(), gate_decision=gate or _auto_gd(),
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann, cand


class TestTimestampProjectionAttack:
    """A1 回归：invalidate 级联不得被时间戳劫持。"""

    async def test_far_future_validated_at_rejected_on_write(self, session):
        sv, ann, cand = await _seed_materializable(session)
        repo = EvidenceRepository(session)
        far = datetime.now(timezone.utc) + timedelta(days=3650)
        with pytest.raises(ValueError, match="future"):
            await repo.append_event(
                _event(validated_at=far),
                candidate_id=cand.id, source_version_id=sv.id,
            )
        print("\n[A1] far-future validated_at rejected at write path")

    async def test_invalidate_wins_projection(self, session):
        sv, ann, cand = await _seed_materializable(session)
        repo = EvidenceRepository(session)
        # 在允许偏移内的未来时间（+2min < 5min skew）——级联仍须压过
        near = datetime.now(timezone.utc) + timedelta(minutes=2)
        await repo.append_event(
            _event(validated_at=near),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        created = await repo.invalidate_claims_for_source_version(
            sv.id, reason="attack: supersede"
        )
        assert len(created) == 1
        state, latest = await repo.project_authority(cand.id, CLAIM_ID)
        print(f"\n[A1] after invalidate: state={state!r} latest={latest.validation_result}")
        assert state == "invalidated"
        assert latest.validation_result == "invalidated"

    async def test_approve_blocked_after_invalidate(self, session):
        sv, ann, cand = await _seed_materializable(session)
        repo = EvidenceRepository(session)
        near = datetime.now(timezone.utc) + timedelta(minutes=2)
        await repo.append_event(
            _event(validated_at=near),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        await repo.invalidate_claims_for_source_version(sv.id, reason="attack")
        svc = AdmissionService(session)
        with pytest.raises(RepositoryError) as ei:
            await svc.approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        print(f"\n[A1b] approve blocked: {ei.value}")
        assert "fail-closed" in str(ei.value) or "authority" in str(ei.value).lower()


class TestForgedMachineEvent:
    """FINDING-2 (A2)：伪造机器 VALIDATED 事件 → auto_approve。

    无新业务字段约束下，机器事件无溯源绑定；与 R-3 的 in-process 信任相邻。
    登记为攻击证据：当前行为 = 放行（xfail 期望应拦截）。
    """

    @pytest.mark.xfail(
        reason="FINDING-2 A2: forged machine VALIDATED via append_event is accepted "
               "by auto_gate approve (no Gate provenance binding on machine events)",
        strict=True,
    )
    async def test_forged_machine_event_should_block_approve(self, session):
        sv, ann, cand = await _seed_materializable(session)
        repo = EvidenceRepository(session)
        await repo.append_event(
            _event(method="frozen_header_rule", validator="gate/v1"),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        svc = AdmissionService(session)
        result = await svc.approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        # 期望失败（被拦）；当前会 approved → xfail
        assert result.decision_status != "approved"


class TestProofBinding:
    """A3: proof 与 terminal 边界。"""

    def test_proof_binds_candidate_id(self):
        cid_a, cid_b = uuid.uuid4(), uuid.uuid4()
        ts = datetime.now(timezone.utc)
        proof_a = generate_review_proof(
            candidate_id=cid_a, review_result="validated",
            reviewer_id="r1", reviewed_at=ts, app_secret=SECRET,
        )

        class _Rec:
            validation_method = "human_review"
            review_proof = proof_a
            validator = "human/r1"
            candidate_id = cid_b
            validation_result = "validated"
            validated_at = ts

        ok = verify_review_proof(_Rec())
        print(f"\n[A3] cross-candidate proof verify={ok}")
        assert ok is False, "A3 HIT: proof not bound to candidate_id"

    async def test_reject_terminal_blocks_resurrection(self, session):
        sv, ann, cand = await _seed_materializable(session)
        repo = EvidenceRepository(session)
        await repo.append_event(
            _event(result="rejected"),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        with pytest.raises(ValueError):
            await repo.append_event(
                _event(result="validated",
                       validated_at=datetime.now(timezone.utc) + timedelta(minutes=1)),
                candidate_id=cand.id, source_version_id=sv.id,
            )
        print("\n[A3b] rejected terminal holds vs later-timestamp resurrection")


class TestClaimIdMismatch:
    """A4: 非 root claim 事件不得投影到 root。"""

    async def test_wrong_claim_id_not_projected_for_root(self, session):
        sv, ann, cand = await _seed_materializable(session)
        repo = EvidenceRepository(session)
        await repo.append_event(
            _event(claim_id="NOT_ROOT"),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        state, latest = await repo.project_authority(cand.id, CLAIM_ID)
        print(f"\n[A4] root projection state={state!r}")
        assert state == "none" and latest is None
        svc = AdmissionService(session)
        with pytest.raises(RepositoryError):
            await svc.approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        print("[A4] approve blocked for root claim without its own events")
