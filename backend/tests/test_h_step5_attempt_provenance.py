"""H Step 5 — attempt_id 贯通（Lock-5/Phase 5）+ Phase 6 并发幂等写（真实 DB）。

attempt_id 由 Task Executor 分配、domain/repository 只透传（禁自生成）；attempt_id 仅作
Artifact Runtime Provenance，不进 LE hash（Lock-5）。Phase 6：create_semantic_annotation /
create_admission_candidate 锚 UNIQUE(stage,hash) ON CONFLICT DO NOTHING → 同 LE idempotent
单行；同 LE invalid 残留阻挡 valid 写（须新 LE）。
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.ai.executor import LLMExecutor
from app.ai.gateway import LLMGateway
from app.core.hashing import sha256_hex
from app.domains.annotation.service import AnnotationService
from app.domains.gate.service import GateService
from app.models.snapshot import AdmissionCandidate, SemanticAnnotation
from app.repositories.base import RepositoryError
from app.repositories.snapshot_repository import SnapshotRepository
from test_annotation_dbflow import _FixedJSONProvider, _valid_json
from test_gate_service import _seed

_ANNO_SCHEMA = "semantic-metadata-annotation/v0.3"


def _ann_service(session, json_str: str) -> AnnotationService:
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(json_str))
    return AnnotationService(session, LLMExecutor(session, gw))


async def _count(session, model, **where):
    stmt = select(func.count()).select_from(model)
    if where:
        stmt = stmt.where(*[getattr(model, k) == v for k, v in where.items()])
    return (await session.execute(stmt)).scalar()


async def test_annotation_attempt_id_persisted_not_in_le_hash(session):
    """Lock-5：annotate(attempt_id=A) 落库 A；同输入 attempt_id=B → 同 LE 复用既有，
    provenance 保留首个（A），attempt 不进 LE hash。"""
    sv, _ = await _seed(session)
    A, B = uuid.uuid4(), uuid.uuid4()
    mc = sha256_hex("mc-v1")

    ann1 = await _ann_service(session, _valid_json()).annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc, attempt_id=A
    )
    await session.flush()
    await session.refresh(ann1)
    assert ann1.attempt_id == A

    ann2 = await _ann_service(session, _valid_json()).annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc, attempt_id=B
    )
    await session.flush()
    # 同 LE → 幂等返回既有行；attempt 差异不改变 hash → 不改写 provenance
    assert ann2.id == ann1.id
    assert ann2.attempt_id == A
    n = await _count(
        session, SemanticAnnotation,
        logical_execution_stage="ann", logical_execution_hash=ann1.logical_execution_hash,
    )
    assert n == 1


async def test_gate_attempt_id_threaded_to_candidate(session):
    """Phase 5 贯通：GateService.run(attempt_id=A) → candidate.attempt_id == A；
    再跑 attempt_id=B（同 annotation 同 LE）→ 复用既有 candidate，attempt 仍 A（compile LE
    排除 attempt，Lock-5）。"""
    sv, ann = await _seed(session)
    A, B = uuid.uuid4(), uuid.uuid4()
    svc = GateService(session)

    c1, _ = await svc.run(source_version_id=sv.id, annotation_id=ann.id, attempt_id=A)
    await session.flush()
    assert len(c1) == 1 and c1[0].attempt_id == A

    c2, _ = await svc.run(source_version_id=sv.id, annotation_id=ann.id, attempt_id=B)
    await session.flush()
    assert len(c2) == 1 and c2[0].id == c1[0].id and c2[0].attempt_id == A


async def test_phase6_annotation_same_le_idempotent_single_row(session):
    """Phase 6：同 (stage,hash) 二次 create_semantic_annotation(valid) → 单行收敛，
    返回既有行、不改写 provenance（首个 attempt 保留）。"""
    sv, _ = await _seed(session)
    snap = SnapshotRepository(session)
    le = sha256_hex("LE-ann")
    a1id, a2id = uuid.uuid4(), uuid.uuid4()

    base = dict(
        source_version_id=sv.id, annotation_schema_version=_ANNO_SCHEMA,
        prompt_version="p/v1", model_config_hash=sha256_hex("m"),
        status="valid", logical_execution_stage="ann", logical_execution_hash=le,
    )
    k1 = await snap.create_semantic_annotation(payload={"seq": 1}, attempt_id=a1id, **base)
    k2 = await snap.create_semantic_annotation(payload={"seq": 2}, attempt_id=a2id, **base)
    assert k2.id == k1.id
    assert k2.attempt_id == a1id  # 单行，首个 attempt provenance 保留
    assert (await _count(
        session, SemanticAnnotation, logical_execution_stage="ann",
        logical_execution_hash=le)) == 1


async def test_phase6_annotation_invalid_residue_blocks_valid(session):
    """Phase 6 语义：同 LE invalid 残留（find 不复用）阻挡 valid 写 → RepositoryError（须新 LE）。"""
    sv, _ = await _seed(session)
    snap = SnapshotRepository(session)
    le = sha256_hex("LE-ann-inv")

    base = dict(
        source_version_id=sv.id, annotation_schema_version=_ANNO_SCHEMA,
        prompt_version="p/v1", model_config_hash=sha256_hex("m"),
        logical_execution_stage="ann", logical_execution_hash=le,
    )
    await snap.create_semantic_annotation(
        payload={"parse_error": "boom"}, status="invalid", attempt_id=uuid.uuid4(), **base
    )
    with pytest.raises(RepositoryError):
        await snap.create_semantic_annotation(
            payload={"ok": 1}, status="valid", attempt_id=uuid.uuid4(), **base
        )


async def test_phase6_candidate_same_le_idempotent_single_row(session):
    """Phase 6：同 (stage,hash) 二次 create_admission_candidate → 单行收敛返回既有。"""
    sv, ann = await _seed(session)
    snap = SnapshotRepository(session)
    le = sha256_hex("LE-comp")
    cid1, cid2 = uuid.uuid4(), uuid.uuid4()

    base = dict(
        unit_type="standalone_unit", source_version_id=sv.id, annotation_id=ann.id,
        build_versions={}, input_identity={}, payload={},
        logical_execution_stage="compile", logical_execution_hash=le,
    )
    k1 = await snap.create_admission_candidate(attempt_id=cid1, **base)
    k2 = await snap.create_admission_candidate(attempt_id=cid2, **base)
    assert k2.id == k1.id
    assert k2.attempt_id == cid1
    assert (await _count(
        session, AdmissionCandidate, logical_execution_stage="compile",
        logical_execution_hash=le)) == 1


# test_service_invalid_residue_blocks_valid_and_masks_second_failure（Step 5 转正）已被
# Phase 7 方案 B 取代：annotate 失败不再落 invalid artifact → 无残留累积、无遮蔽（P2-1 消解）。
# 对应新失败政策回归见 test_h_step7_failure_policy.py；repo 级历史 invalid 残留防御由本文件
# test_phase6_annotation_invalid_residue_blocks_valid 保留。
