"""EB-008 Evidence Authority Enforcement — 验收测试（92号 §5 Checklist）。

覆盖五项验收标准：
- 5.1 validation_events 持久化：Gate 运行落行；replay 幂等；状态机违规抛错
- 5.2 Review Proof：合法通过；篡改失败；无 proof 不产生 Authority
- 5.3 Admission enforcement：无事件 fail-closed；VALIDATED 可物化；篡改 proof 拒
- 5.4 Invalidate 级联：annotation supersede → invalidated；approve 被拒；恢复=新 Entity
- 5.5 Append-only：无 update/delete；显式拒
+ F-2 正向回归（原 spec_gap 缺口证明闭合）
"""

from __future__ import annotations

import pathlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.domains.evidence.models import ValidationEvent
from app.domains.evidence.proof import (
    generate_review_proof,
    human_validator,
    require_app_secret,
    verify_review_proof,
)
from app.domains.gate.admission import AdmissionService
from app.models.snapshot import AdmissionCandidate
from app.repositories.base import AppendOnlyViolation, RepositoryError
from app.repositories.evidence_repository import (
    AUTHORITY_INVALIDATED,
    AUTHORITY_VALIDATED,
    EvidenceRepository,
    delete_validation_event,
    update_validation_event,
)
from app.repositories.snapshot_repository import SnapshotRepository
from tests.eb008_helpers import (
    CLAIM_ID,
    auto_gate_decision,
    pending_gate_decision,
    rejected_gate_decision,
    seed_candidate,
    seed_validated_authority,
)


# ------------------------------------------------------------------ 5.1 持久化
class TestValidationEventsPersistence:
    async def test_append_persists_row(self, session):
        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        rec = await seed_validated_authority(session, cand, sv)
        rows = await repo.find_events_for_claim(cand.id, CLAIM_ID)
        assert len(rows) == 1
        assert rows[0].id == rec.id
        assert rows[0].validation_result == "validated"
        assert rows[0].candidate_id == cand.id
        assert rows[0].source_version_id == sv.id

    async def test_projection_survives_new_session(self, session):
        """进程重启等价：新 session 读同一 DB → 投影不变（92号 §5.1 验收）。"""
        from sqlalchemy import text

        from app.db.session import async_session_maker

        sv, ann, cand = await seed_candidate(session)
        await seed_validated_authority(session, cand, sv)
        await session.commit()  # 持久化，供新 session 读
        try:
            async with async_session_maker() as s2:
                state, latest = await EvidenceRepository(s2).project_authority(
                    cand.id, CLAIM_ID
                )
                assert state == AUTHORITY_VALIDATED
                assert latest is not None
                await s2.rollback()
        finally:
            # 清理本测试 commit 的行，防污染其它文件的全局 count 断言
            async with async_session_maker() as sc:
                for sql, params in (
                    ("DELETE FROM validation_events WHERE candidate_id=:c",
                     {"c": cand.id}),
                    ("DELETE FROM admission_events WHERE candidate_id=:c",
                     {"c": cand.id}),
                    ("DELETE FROM admission_candidates WHERE id=:c", {"c": cand.id}),
                    ("DELETE FROM semantic_annotations WHERE id=:a", {"a": ann.id}),
                    ("DELETE FROM document_source_lines WHERE source_version_id=:s",
                     {"s": sv.id}),
                    ("DELETE FROM document_source_versions WHERE id=:s", {"s": sv.id}),
                    ("DELETE FROM documents WHERE id=:d", {"d": sv.document_id}),
                ):
                    await sc.execute(text(sql), params)
                await sc.commit()

    async def test_replay_noop_single_row(self, session):
        """R4：同 (candidate, claim) 同结果重放 → no-op，恰 1 行。"""
        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        first = await seed_validated_authority(session, cand, sv)
        event = ValidationEvent(
            event_id=f"ve-{uuid.uuid4().hex[:8]}",
            claim_id=CLAIM_ID, validation_result="validated", checks=(),
            validation_method="frozen_header_rule", validator="gate/v1",
        )
        second = await repo.append_event(
            event, candidate_id=cand.id, source_version_id=sv.id,
        )
        assert second.id == first.id
        assert len(await repo.find_events_for_claim(cand.id, CLAIM_ID)) == 1

    async def test_state_machine_violation_raises(self, session):
        """terminal 拒新事件（enforce_state_transition 在 DB 写入路径）。"""
        sv, _ann, cand = await seed_candidate(session, gate=rejected_gate_decision())
        repo = EvidenceRepository(session)
        await repo.append_event(
            ValidationEvent(
                event_id="ve-r1", claim_id=CLAIM_ID, validation_result="rejected",
                checks=(), validation_method="structural_consistency",
                validator="gate/v1",
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        with pytest.raises(ValueError, match="terminal"):
            await repo.append_event(
                ValidationEvent(
                    event_id="ve-v1", claim_id=CLAIM_ID, validation_result="validated",
                    checks=(), validation_method="frozen_header_rule",
                    validator="gate/v1",
                ),
                candidate_id=cand.id, source_version_id=sv.id,
            )

    async def test_gate_service_run_persists_events(self, session):
        """Gate 运行后 validation_events 有对应行（92号 §5.1 验收）。"""
        from tests.test_gate_service import _seed
        from app.domains.gate.service import GateService

        sv, ann = await _seed(session)
        candidates, _skipped = await GateService(session).run(
            source_version_id=sv.id, annotation_id=ann.id
        )
        await session.flush()
        assert candidates
        repo = EvidenceRepository(session)
        for cand in candidates:
            rows = await repo.find_events_for_candidate(cand.id)
            assert rows, f"candidate {cand.id} 无 validation_events 行"


# ------------------------------------------------------------------ 5.2 Review Proof
class TestReviewProof:
    def test_generate_and_verify_roundtrip(self):
        cid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        proof = generate_review_proof(
            candidate_id=cid, review_result="validated",
            reviewer_id="owner", reviewed_at=now,
        )
        assert len(proof) == 64  # SHA256 hex

        class _Rec:
            candidate_id = cid
            validation_result = "validated"
            validator = human_validator("owner")
            validated_at = now
            review_proof = proof
            validation_method = "human_review"

        assert verify_review_proof(_Rec) is True

    def test_tampered_result_fails_verify(self):
        cid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        proof = generate_review_proof(
            candidate_id=cid, review_result="validated",
            reviewer_id="owner", reviewed_at=now,
        )

        class _Tampered:
            candidate_id = cid
            validation_result = "rejected"  # 篡改
            validator = human_validator("owner")
            validated_at = now
            review_proof = proof
            validation_method = "human_review"

        assert verify_review_proof(_Tampered) is False

    def test_missing_secret_fails_closed(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "app_secret", "")
        with pytest.raises(RepositoryError, match="APP_SECRET"):
            require_app_secret()
        with pytest.raises(RepositoryError, match="APP_SECRET"):
            generate_review_proof(
                candidate_id=uuid.uuid4(), review_result="validated",
                reviewer_id="x", reviewed_at=datetime.now(timezone.utc),
            )

    def test_short_secret_fails_closed(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "app_secret", "too-short")
        with pytest.raises(RepositoryError, match="APP_SECRET"):
            require_app_secret()

    async def test_human_review_event_requires_proof(self, session):
        """无 proof 的 human_review 事件写入被拒（92号 §5.2 验收）。"""
        sv, _ann, cand = await seed_candidate(session, gate=pending_gate_decision())
        repo = EvidenceRepository(session)
        with pytest.raises(RepositoryError, match="review_proof"):
            await repo.append_event(
                ValidationEvent(
                    event_id="ve-h1", claim_id=CLAIM_ID,
                    validation_result="validated", checks=(),
                    validation_method="human_review",
                    validator=human_validator("owner"),
                ),
                candidate_id=cand.id, source_version_id=sv.id,
            )


# ------------------------------------------------------------------ 5.3 Admission enforcement
class TestAdmissionEnforcement:
    async def test_auto_approve_requires_validated_authority(self, session):
        """gate_decision=auto_approve 但无 Authority 事件 → fail-closed。"""
        from tests.test_admission import _make_candidate as _mk

        sv, ann, _seeded = await seed_candidate(session)
        cand = await _mk(session, sv, ann, auto_gate_decision())
        await session.flush()
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )
        row = await session.get(AdmissionCandidate, cand.id)
        assert row.decision_status == "pending_review"  # 不 reject

    async def test_validated_authority_approve_succeeds(self, session):
        """VALIDATED Authority → approve 成功物化（92号 §5.3 验收）。"""
        from tests.test_admission import _make_candidate as _mk

        sv, ann, _seeded = await seed_candidate(session)
        cand = await _mk(session, sv, ann, auto_gate_decision())
        await session.flush()
        await seed_validated_authority(session, cand, sv)
        decided = await AdmissionService(session).approve(
            candidate_id=cand.id, provenance={"source": "auto_gate"}
        )
        assert decided.decision_status == "approved"

    async def test_invalidated_authority_blocks_approve(self, session):
        """INVALIDATED Authority → approve 被拒（5.4 验收）。"""
        from tests.test_admission import _make_candidate as _mk

        sv, ann, _seeded = await seed_candidate(session)
        cand = await _mk(session, sv, ann, auto_gate_decision())
        await session.flush()
        await seed_validated_authority(session, cand, sv)
        await EvidenceRepository(session).append_event(
            ValidationEvent(
                event_id="ve-inv", claim_id=CLAIM_ID,
                validation_result="invalidated", checks=(),
                validation_method="structural_consistency", validator="system/v1",
                validated_at=datetime.now(timezone.utc) + timedelta(seconds=1),
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )

    async def test_tampered_human_proof_blocks_approve(self, session):
        """DB 直改 proof → human 路径 approve 失败（92号 §5.2 声明 2）。"""
        from tests.test_admission import _dummy_payload

        sv, ann, _seeded = await seed_candidate(session, gate=pending_gate_decision())
        snap = SnapshotRepository(session)
        cand = await snap.create_admission_candidate(
            unit_type="standalone_unit", source_version_id=sv.id, annotation_id=ann.id,
            build_versions={"v": "1"}, input_identity={},
            payload=_dummy_payload(), gate_decision=pending_gate_decision(),
            logical_execution_stage="compile",
            logical_execution_hash=uuid.uuid4().hex,
        )
        await session.flush()
        await snap.append_review_trail(cand.id, {
            "decision": "approve", "verified_by": "human", "reviewer_id": "owner",
        })
        # 插入 human_review 事件但 proof 无效（模拟 DB 直接篡改）
        await EvidenceRepository(session).append_event(
            ValidationEvent(
                event_id="ve-tamper", claim_id="Q1", validation_result="validated",
                checks=(), validation_method="human_review",
                validator=human_validator("owner"),
                validated_at=datetime.now(timezone.utc),
            ),
            candidate_id=cand.id, source_version_id=sv.id,
            review_proof="0" * 64,
        )
        with pytest.raises(RepositoryError, match="proof invalid"):
            await AdmissionService(session).approve(
                candidate_id=cand.id,
                provenance={"source": "human", "reviewer_id": "owner"},
            )

    async def test_human_approve_generates_proof_event(self, session):
        """人工 approve 路径：自动生成 human_review 事件 + 合法 proof。"""
        from tests.test_admission import _dummy_payload

        sv, ann, _seeded = await seed_candidate(session, gate=pending_gate_decision())
        snap = SnapshotRepository(session)
        cand = await snap.create_admission_candidate(
            unit_type="standalone_unit", source_version_id=sv.id, annotation_id=ann.id,
            build_versions={"v": "1"}, input_identity={},
            payload=_dummy_payload(), gate_decision=pending_gate_decision(),
            logical_execution_stage="compile",
            logical_execution_hash=uuid.uuid4().hex,
        )
        await session.flush()
        await snap.append_review_trail(cand.id, {
            "decision": "approve", "verified_by": "human", "reviewer_id": "owner",
        })
        decided = await AdmissionService(session).approve(
            candidate_id=cand.id,
            provenance={"source": "human", "reviewer_id": "owner"},
        )
        assert decided.decision_status == "approved"
        rows = await EvidenceRepository(session).find_events_for_claim(cand.id, "Q1")
        human_rows = [r for r in rows if r.validation_method == "human_review"]
        assert len(human_rows) == 1
        assert human_rows[0].review_proof
        assert verify_review_proof(human_rows[0]) is True

    async def test_enforcement_symbols_present(self):
        """F-2 正向回归（原 spec_gap）：admission 路径执行 Evidence Authority。"""
        app_root = pathlib.Path(__file__).resolve().parents[1] / "app"
        source = (app_root / "domains" / "gate" / "admission.py").read_text(
            encoding="utf-8"
        )
        assert "EvidenceRepository" in source
        assert "project_authority" in source
        assert "verify_review_proof" in source


# ------------------------------------------------------------------ 5.4 Invalidate 级联
class TestInvalidateCascade:
    async def test_annotation_supersede_cascades(self, session):
        """annotation valid→superseded → 下属 VALIDATED claims 全部 INVALIDATED。"""
        sv, ann, cand = await seed_candidate(session)
        await seed_validated_authority(session, cand, sv)
        state, _ = await EvidenceRepository(session).project_authority(
            cand.id, CLAIM_ID
        )
        assert state == AUTHORITY_VALIDATED

        await SnapshotRepository(session).set_annotation_status(ann.id, "superseded")
        await session.flush()

        state, latest = await EvidenceRepository(session).project_authority(
            cand.id, CLAIM_ID
        )
        assert state == AUTHORITY_INVALIDATED
        assert any(
            c.get("check_id") == "INVALIDATE_CASCADE" for c in (latest.checks or [])
        )

    async def test_invalidate_blocks_approve(self, session):
        from tests.test_admission import _make_candidate as _mk

        sv, ann, _seeded = await seed_candidate(session)
        cand = await _mk(session, sv, ann, auto_gate_decision())
        await session.flush()
        await seed_validated_authority(session, cand, sv)
        await SnapshotRepository(session).set_annotation_status(ann.id, "superseded")
        await session.flush()
        with pytest.raises(RepositoryError, match="fail-closed"):
            await AdmissionService(session).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"}
            )

    async def test_invalidate_is_terminal_no_resurrection(self, session):
        """INVALIDATED terminal：同 claim 不能重新 validated（恢复=新 Entity）。"""
        sv, ann, cand = await seed_candidate(session)
        await seed_validated_authority(session, cand, sv)
        await SnapshotRepository(session).set_annotation_status(ann.id, "superseded")
        await session.flush()
        with pytest.raises(ValueError, match="terminal"):
            await seed_validated_authority(session, cand, sv)

    async def test_invalidate_skips_rejected_claims(self, session):
        sv, _ann, cand = await seed_candidate(session, gate=rejected_gate_decision())
        repo = EvidenceRepository(session)
        await repo.append_event(
            ValidationEvent(
                event_id="ve-r", claim_id=CLAIM_ID, validation_result="rejected",
                checks=(), validation_method="structural_consistency",
                validator="gate/v1",
            ),
            candidate_id=cand.id, source_version_id=sv.id,
        )
        created = await repo.invalidate_claims_for_source_version(
            sv.id, reason="test"
        )
        assert created == []  # rejected 不级联

    async def test_source_version_cascade_entry_exists(self, session):
        """source_version 级联入口可用（触发场景 wiring 由调用方接）。"""
        sv, _ann, cand = await seed_candidate(session)
        await seed_validated_authority(session, cand, sv)
        created = await EvidenceRepository(session).invalidate_claims_for_source_version(
            sv.id, reason="source superseded"
        )
        assert len(created) == 1
        assert created[0].validation_result == "invalidated"


# ------------------------------------------------------------------ 5.5 Append-only
class TestAppendOnlyProtection:
    async def test_no_update_delete_methods(self, session):
        repo = EvidenceRepository(session)
        assert not hasattr(repo, "update_event")
        assert not hasattr(repo, "delete_event")
        assert not hasattr(repo, "update_validation_event")
        assert not hasattr(repo, "delete_validation_event")

    async def test_explicit_update_delete_rejected(self):
        with pytest.raises(AppendOnlyViolation):
            await update_validation_event()
        with pytest.raises(AppendOnlyViolation):
            await delete_validation_event()

    async def test_insert_replay_and_state_machine(self, session):
        """唯一写入口行为：replay no-op；非法迁移抛错（应用层双保护）。"""
        sv, _ann, cand = await seed_candidate(session)
        repo = EvidenceRepository(session)
        rec1 = await seed_validated_authority(session, cand, sv)
        rec2 = await seed_validated_authority(session, cand, sv)
        assert rec1.id == rec2.id  # replay no-op
        with pytest.raises(ValueError, match="only INVALIDATED"):
            await repo.append_event(
                ValidationEvent(
                    event_id="ve-bad", claim_id=CLAIM_ID,
                    validation_result="rejected", checks=(),
                    validation_method="structural_consistency",
                    validator="gate/v1",
                ),
                candidate_id=cand.id, source_version_id=sv.id,
            )


# ------------------------------------------------------------------ Replay 一致性（Gate 层）
class TestReplayConsistency:
    async def test_gate_rerun_same_le_single_authority(self, session):
        """同一 (sv, ann) 重跑 Gate：candidate 复用，Authority 恰 1 行且不变。"""
        from tests.test_gate_service import _seed
        from app.domains.gate.service import GateService

        sv, ann = await _seed(session)
        gate = GateService(session)
        c1, _ = await gate.run(source_version_id=sv.id, annotation_id=ann.id)
        await session.flush()
        repo = EvidenceRepository(session)
        events_1 = await repo.find_events_for_candidate(c1[0].id)
        claim = c1[0].payload["ir_snapshot"]["units"][0]["unit_id"]
        state_1, _ = await repo.project_authority(c1[0].id, claim)

        gate2 = GateService(session)
        c2, _ = await gate2.run(source_version_id=sv.id, annotation_id=ann.id)
        await session.flush()
        events_2 = await repo.find_events_for_candidate(c2[0].id)
        state_2, _ = await repo.project_authority(c2[0].id, claim)

        assert c1[0].id == c2[0].id  # le_hash 幂等复用
        assert len(events_1) == len(events_2) == 1  # replay 不新增
        assert state_1 == state_2 == AUTHORITY_VALIDATED  # Authority 不变

    async def test_identity_excludes_run_id(self):
        """I6：run_id 不参与 Authority 身份因素（模型层无 run_id 字段）。"""
        from app.models.evidence import ValidationEventRecord

        cols = {c.name for c in ValidationEventRecord.__table__.columns}
        assert "run_id" not in cols
        assert "attempt_id" not in cols
        assert {"claim_id", "candidate_id", "source_version_id"} <= cols
