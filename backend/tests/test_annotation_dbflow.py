"""Gate D2/D3 — Annotation 幂等 + supersede + persistence boundary（真实 DB，可重入）。

参照段 B test_seal_dbflow.py 模式：session yield→rollback 隔离；先 seal PDF 产生
source_version，再 annotation。
"""

import json
import uuid

import pytest
from sqlalchemy import func, select

from app.ai.gateway import LLMGateway
from app.ai.ocr.providers import NativeTextProvider
from app.domains.annotation import (
    ANNO_SCHEMA_VERSION,
    ANN_PROMPT_VERSION,
    validate_annotation_payload,
)
from app.domains.annotation.service import AnnotationService
from app.domains.source.seal import SealService
from app.models.snapshot import SemanticAnnotation
from app.repositories.base import RepositoryError
from app.repositories.snapshot_repository import SnapshotRepository


class _FixedJSONProvider:
    """mock provider：始终返回固定 JSON 字符串（段 D mock，不调真实 LLM）。"""

    name = "mock"

    def __init__(self, json_str: str):
        self._json = json_str

    async def complete(self, prompt: str) -> str:
        return self._json


def _valid_json():
    return json.dumps(
        {
            "annotation_schema": ANNO_SCHEMA_VERSION,
            "document_metadata_claims": {"subject": None},
            "sections": [],
            "semantic_units": [
                {
                    "type": "standalone_question",
                    "question_label": "1",
                    "stem_ref": {
                        "role": "question_label",
                        "label": "1",
                        "start_marker": {"kind": "question_label", "text": "1"},
                        "end_marker": None,
                    },
                }
            ],
            "annotation_meta": {
                "model": "mock",
                "prompt_version": ANN_PROMPT_VERSION,
                "status": "complete",
                "warnings": [],
            },
        }
    )


def _invalid_schema_json():
    p = json.loads(_valid_json())
    p["stem_text"] = "问题正文"  # forbidden field
    return json.dumps(p)


def _invalid_json():
    return "not valid json {"


async def _seal_source(session, pdf_bytes):
    v = await SealService(session).seal_document(
        file_bytes=pdf_bytes,
        file_name="ann_test.pdf",
        file_type="pdf",
        role="native",
        provider="native",
        extractor=NativeTextProvider().extract,
    )
    await session.flush()
    return v


def _mchash(name: str) -> str:
    from app.core.hashing import sha256_hex

    return sha256_hex(name)


async def test_d2_idempotent_same_le_returns_existing(session, pdf_bytes):
    """D2：同 LE hash 写两次 → 恰 1 行（第二次返回既有 valid 行）。"""
    sv = await _seal_source(session, pdf_bytes)
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_valid_json()))
    svc = AnnotationService(session, gw)
    mc = _mchash("mock-v1")

    ann1 = await svc.annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc
    )
    await session.flush()
    ann2 = await svc.annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc
    )
    await session.flush()
    assert ann1.id == ann2.id
    assert ann1.status == "valid"


async def test_d2_supersede_explicit(session, pdf_bytes):
    """D2：显式 supersede（create 不自动修改旧行，P2-a）。"""
    sv = await _seal_source(session, pdf_bytes)
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_valid_json()))
    snap = SnapshotRepository(session)
    svc = AnnotationService(session, gw)
    mc1, mc2 = _mchash("v1"), _mchash("v2")

    ann1 = await svc.annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc1
    )
    await session.flush()
    assert ann1.status == "valid"

    ann2 = await svc.annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc2
    )
    await session.flush()
    assert ann2.id != ann1.id
    assert ann2.status == "valid"
    assert ann1.status == "valid"  # create 不自动修改旧行（P2-a）

    updated = await snap.set_annotation_status(ann1.id, "superseded")
    await session.flush()
    assert updated.status == "superseded"
    assert ann1.status == "superseded"


async def test_d2_set_status_rejects_invalid_transition(session, pdf_bytes):
    """set_annotation_status 只允许 valid→superseded，其余拒绝。"""
    sv = await _seal_source(session, pdf_bytes)
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_invalid_schema_json()))
    snap = SnapshotRepository(session)
    svc = AnnotationService(session, gw)

    with pytest.raises(ValueError):
        await svc.annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=_mchash("inv")
        )
    await session.flush()
    inv = (await session.execute(select(SemanticAnnotation))).scalars().first()
    assert inv.status == "invalid"
    with pytest.raises(RepositoryError):
        await snap.set_annotation_status(inv.id, "superseded")


async def test_d3_valid_persisted_payload_no_forbidden(session, pdf_bytes):
    """D3：valid payload 落库 payload 不含禁字段。"""
    sv = await _seal_source(session, pdf_bytes)
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_valid_json()))
    svc = AnnotationService(session, gw)

    ann = await svc.annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=_mchash("ok")
    )
    await session.flush()
    assert ann.status == "valid"
    ok, violations = validate_annotation_payload(ann.payload)
    assert ok is True and violations == []


async def test_d3_invalid_schema_persisted_then_raises(session, pdf_bytes):
    """D3：含禁字段 payload → 落库 status=invalid + 抛 ValueError（两者同时发生）。"""
    sv = await _seal_source(session, pdf_bytes)
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_invalid_schema_json()))
    svc = AnnotationService(session, gw)

    with pytest.raises(ValueError, match="forbidden fields"):
        await svc.annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=_mchash("bad")
        )
    await session.flush()
    ann = (await session.execute(select(SemanticAnnotation))).scalars().first()
    assert ann is not None
    assert ann.status == "invalid"
    assert ann.payload.get("stem_text") == "问题正文"  # payload 保留用于诊断


async def test_d3_invalid_json_persisted_then_raises(session, pdf_bytes):
    """D3：json.loads 失败 → 落库 status=invalid + payload parse_error + raise（BUG-V3-010）。"""
    sv = await _seal_source(session, pdf_bytes)
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_invalid_json()))
    svc = AnnotationService(session, gw)

    with pytest.raises(ValueError, match="not valid JSON"):
        await svc.annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=_mchash("parse")
        )
    await session.flush()
    ann = (await session.execute(select(SemanticAnnotation))).scalars().first()
    assert ann.status == "invalid"
    assert "parse_error" in ann.payload


async def test_d2_cross_transaction_idempotency(session, pdf_bytes):
    """D2 跨事务强化：commit 后新事务同 LE hash → 返回既有 annotation。"""
    from sqlalchemy import text
    from app.db.session import async_session_maker

    sv = await _seal_source(session, pdf_bytes)
    gw = LLMGateway("mock", mock_provider=_FixedJSONProvider(_valid_json()))
    mc = _mchash("cross-tx")
    ann1 = await AnnotationService(session, gw).annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc)
    await session.flush(); await session.commit()
    a1id = ann1.id
    try:
        async with async_session_maker() as s2:
            gw2 = LLMGateway("mock", mock_provider=_FixedJSONProvider(_valid_json()))
            ann2 = await AnnotationService(s2, gw2).annotate(
                source_version_id=sv.id, prompt="p", model_config_hash=mc)
            assert ann2.id == a1id
            n = (await s2.execute(select(func.count()).select_from(SemanticAnnotation))).scalar()
            assert n == 1
    finally:
        # 跨事务 commit 使 conftest rollback fixture 失效 → cleanup 必须按 FK 序删净
        # （annotation/lines → version → document），否则残留 documents 域数据污染
        # 后续 B seal 测试的 `n_docs == 1` 断言（FAIL-1 修复，参照 _audit_d.py test_t1）。
        async with async_session_maker() as sc:
            vid = str(sv.id)
            doc_id = (
                await sc.execute(
                    text("SELECT document_id FROM document_source_versions WHERE id=:v"),
                    {"v": vid},
                )
            ).scalar()
            await sc.execute(
                text("DELETE FROM semantic_annotations WHERE source_version_id=:v"),
                {"v": vid},
            )
            await sc.execute(
                text("DELETE FROM document_source_lines WHERE source_version_id=:v"),
                {"v": vid},
            )
            await sc.execute(
                text("DELETE FROM document_source_versions WHERE id=:v"),
                {"v": vid},
            )
            if doc_id:
                await sc.execute(text("DELETE FROM documents WHERE id=:d"), {"d": str(doc_id)})
            await sc.commit()


async def test_d2_invalid_not_reused_requires_new_le(session, pdf_bytes):
    """D2 invalid annotation 不复用（find 排除 invalid）；retry 必须新 LE（DB UNIQUE 同 hash 阻止）。"""
    sv = await _seal_source(session, pdf_bytes)
    gw_bad = LLMGateway("mock", mock_provider=_FixedJSONProvider(_invalid_schema_json()))
    mc = _mchash("inv-not-reuse")
    with pytest.raises(ValueError):
        await AnnotationService(session, gw_bad).annotate(
            source_version_id=sv.id, prompt="p", model_config_hash=mc)
    await session.flush()
    inv = (await session.execute(select(SemanticAnnotation))).scalars().first()
    assert inv.status == "invalid"
    # 同 LE hash 重试 → UNIQUE 阻止；retry 需新 LE
    gw_ok = LLMGateway("mock", mock_provider=_FixedJSONProvider(_valid_json()))
    mc2 = _mchash("inv-not-reuse-new")
    ann2 = await AnnotationService(session, gw_ok).annotate(
        source_version_id=sv.id, prompt="p", model_config_hash=mc2)
    await session.flush()
    n = (await session.execute(select(func.count()).select_from(SemanticAnnotation))).scalar()
    assert n == 2 and ann2.status == "valid"
