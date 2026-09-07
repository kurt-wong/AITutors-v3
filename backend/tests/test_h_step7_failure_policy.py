"""H Phase 7 — H0-15 方案 B failure policy（真实 PostgreSQL，可重入）。

方案 B：annotate 失败（provider / parse / forbidden-field）一律不创建 annotation artifact；
失败不再占 (stage,hash) → 同 LE 可重复失败后成功收敛恰 1 valid；P2-1（RepositoryError
遮蔽原始错误）随之消解；成功后的幂等复用不退化；历史 invalid 残留仍被 repo 防御，
service 对 RepositoryError 原样传播（不吞）。

锁定不变量（Step 7-3 常驻回归）：
  S7-1 provider failure  → 0 artifact + 原始异常类型保持
  S7-2 parse failure     → 0 artifact + ValueError
  S7-3 validation failure→ 0 artifact + ValueError
  S7-4 fail→fail→success → 恰 1 valid（同 LE，失败不占坑）
  S7-5 二次 provider failure 仍原始异常（无 RepositoryError 遮蔽 = P2-1 Closed 证据）
  S7-6 success 后同 LE retry → 复用 existing valid（Phase 6 幂等不退化）
"""

import pytest
from sqlalchemy import func, select

from app.ai.executor import LLMExecutor
from app.ai.gateway import LLMGateway
from app.core.hashing import logical_execution_hash, sha256_hex
from app.domains.annotation import ANNO_SCHEMA_VERSION, ANN_PROMPT_VERSION
from app.domains.annotation.service import AnnotationService
from app.models.snapshot import SemanticAnnotation
from app.repositories.base import RepositoryError
from app.repositories.snapshot_repository import SnapshotRepository
from test_annotation_dbflow import (
    _FixedJSONProvider,
    _invalid_json,
    _invalid_schema_json,
    _seal_source,
    _valid_json,
)


class _BoomProvider:
    """mock provider：complete 恒抛（provider/网络失败路径）。"""

    name = "mock-boom"

    async def complete(self, prompt: str) -> str:
        raise RuntimeError("provider boom")


def _svc(session, provider) -> AnnotationService:
    gw = LLMGateway("mock", mock_provider=provider)
    return AnnotationService(session, LLMExecutor(session, gw))


async def _n(session, *, source_version_id) -> int:
    return (
        await session.execute(
            select(func.count())
            .select_from(SemanticAnnotation)
            .where(SemanticAnnotation.source_version_id == source_version_id)
        )
    ).scalar()


async def test_s7_provider_failure_no_artifact_original_error(session, pdf_bytes):
    """S7-1 + S7-5：provider 失败 → 0 artifact；二次失败仍是原始 RuntimeError
    （P2-1 遮蔽消解的核心证据：不抛 RepositoryError）。"""
    sv = await _seal_source(session, pdf_bytes)
    mc = sha256_hex("s7-provider")
    # S7-1
    with pytest.raises(RuntimeError, match="provider boom"):
        await _svc(session, _BoomProvider()).annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=mc
        )
    await session.flush()
    assert await _n(session, source_version_id=sv.id) == 0
    # S7-5：同 LE 二次失败 → 仍原始错误，不出现 RepositoryError 遮蔽
    with pytest.raises(RuntimeError, match="provider boom"):
        await _svc(session, _BoomProvider()).annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=mc
        )
    await session.flush()
    assert await _n(session, source_version_id=sv.id) == 0


async def test_s7_parse_failure_no_artifact(session, pdf_bytes):
    """S7-2：JSON parse 失败 → 0 artifact + ValueError。"""
    sv = await _seal_source(session, pdf_bytes)
    with pytest.raises(ValueError, match="not valid JSON"):
        await _svc(session, _FixedJSONProvider(_invalid_json())).annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=sha256_hex("s7-parse")
        )
    await session.flush()
    assert await _n(session, source_version_id=sv.id) == 0


async def test_s7_validation_failure_no_artifact(session, pdf_bytes):
    """S7-3：forbidden payload → 0 artifact + ValueError。"""
    sv = await _seal_source(session, pdf_bytes)
    with pytest.raises(ValueError, match="forbidden fields"):
        await _svc(session, _FixedJSONProvider(_invalid_schema_json())).annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=sha256_hex("s7-forb")
        )
    await session.flush()
    assert await _n(session, source_version_id=sv.id) == 0


async def test_s7_fail_fail_success_same_le_single_valid(session, pdf_bytes):
    """S7-4：同 LE fail→fail→success → 恰 1 valid 行（失败不占 (stage,hash)，
    无需任何绕过 invalid 的逻辑）。"""
    sv = await _seal_source(session, pdf_bytes)
    mc = sha256_hex("s7-fail-success")
    for _ in range(2):
        with pytest.raises(RuntimeError, match="provider boom"):
            await _svc(session, _BoomProvider()).annotate(
                source_version_id=sv.id, prompt="p", model_config_hash=mc
            )
        await session.flush()
        assert await _n(session, source_version_id=sv.id) == 0
    ann = await _svc(session, _FixedJSONProvider(_valid_json())).annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc
    )
    await session.flush()
    assert ann.status == "valid"
    assert await _n(session, source_version_id=sv.id) == 1


async def test_s7_success_retry_same_le_idempotent(session, pdf_bytes):
    """S7-6：success 后同 LE retry → 复用 existing valid（Phase 6 幂等不退化）。"""
    sv = await _seal_source(session, pdf_bytes)
    mc = sha256_hex("s7-idem")
    a1 = await _svc(session, _FixedJSONProvider(_valid_json())).annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc
    )
    await session.flush()
    a2 = await _svc(session, _FixedJSONProvider(_valid_json())).annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc
    )
    await session.flush()
    assert a1.id == a2.id and a1.status == "valid"
    assert await _n(session, source_version_id=sv.id) == 1


async def test_s7_history_invalid_residue_still_blocks_via_service(session, pdf_bytes):
    """历史 invalid 残留防御（service 视角）：repo 直插 invalid 行同 LE → annotate
    好 provider：find 排除 invalid → create valid 撞残留 → RepositoryError 原样传播
    （service 不吞；方案 B 不清洗历史，须新 LE）。"""
    sv = await _seal_source(session, pdf_bytes)
    snap = SnapshotRepository(session)
    mc = sha256_hex("s7-history")
    le = logical_execution_hash(
        task_type="document_ingest",
        stage="ann",
        contract_domain={
            "annotation_schema_version": ANNO_SCHEMA_VERSION,
            "prompt_version": ANN_PROMPT_VERSION,
            "model_config_hash": mc,
        },
        input_domain={"source_version_id": str(sv.id)},
    )
    await snap.create_semantic_annotation(
        source_version_id=sv.id,
        annotation_schema_version=ANNO_SCHEMA_VERSION,
        prompt_version=ANN_PROMPT_VERSION,
        model_config_hash=mc,
        payload={},
        status="invalid",
        logical_execution_stage="ann",
        logical_execution_hash=le,
        attempt_id=None,
    )
    await session.flush()
    with pytest.raises(RepositoryError) as re_:
        await _svc(session, _FixedJSONProvider(_valid_json())).annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=mc
        )
    assert "invalid" in str(re_.value) or "new LE" in str(re_.value)
