"""P2-AID — Annotation 身份计算覆盖确定性 payload 语义。

验证：document_metadata_claims / semantic_units / sections 变化 → 新身份；
非确定性诊断字段变化 → 同身份复用；旧 Annotation 不被修改。
"""
import json
import uuid

import pytest

from app.ai.executor import LLMExecutor
from app.ai.gateway import LLMGateway
from app.ai.ocr.providers import NativeTextProvider
from app.domains.annotation import ANNO_SCHEMA_VERSION, ANN_PROMPT_VERSION
from app.domains.annotation.service import AnnotationService, _payload_semantic_hash
from app.domains.source.seal import SealService


def _base_payload(subject=None, grade="高一", extra_boundary=None):
    return {
        "document_metadata_claims": {
            "subject": subject, "grade": grade,
            "year": None, "school": None,
            "grade_source": "path_keyword:会考",
        },
        "sections": [],
        "semantic_units": [
            {
                "unit_id": "Q1",
                "unit_type": "standalone_unit",
                "question_number": 1,
                "content": {"stem": {"role": "stem"}, "answer": {"role": "answer"}},
            }
        ],
        "producer_boundary": {
            "normalization_rule": "test",
            "llm_unit_checks": extra_boundary or [],
        },
    }


class _MockGW:
    name = "mock"
    async def complete(self, prompt: str) -> str:
        return "{}"


async def _seal(session, pdf_bytes):
    v = await SealService(session).seal_document(
        file_bytes=pdf_bytes, file_name="p2aid.pdf", file_type="pdf",
        role="native", provider="native",
        extractor=NativeTextProvider().extract,
    )
    await session.flush()
    return v


def _svc(session):
    return AnnotationService(session, LLMExecutor(session, LLMGateway("mock", mock_provider=_MockGW())))


class TestPayloadSemanticHash:
    """辅助哈希的确定性。"""

    def test_same_semantics_same_hash(self):
        a = _payload_semantic_hash(_base_payload(subject="物理"))
        b = _payload_semantic_hash(_base_payload(subject="物理"))
        assert a == b

    def test_subject_change_changes_hash(self):
        a = _payload_semantic_hash(_base_payload(subject=None))
        b = _payload_semantic_hash(_base_payload(subject="物理"))
        assert a != b

    def test_grade_change_changes_hash(self):
        a = _payload_semantic_hash(_base_payload(grade="高一"))
        b = _payload_semantic_hash(_base_payload(grade="高二"))
        assert a != b

    def test_unit_structure_change_changes_hash(self):
        p1 = _base_payload()
        p2 = _base_payload()
        p2["semantic_units"][0]["content"]["stem"] = {"role": "stem", "text": "changed"}
        assert _payload_semantic_hash(p1) != _payload_semantic_hash(p2)

    def test_line_ref_change_does_not_change_hash(self):
        """line_refs 是 Source Binding Claim，不进 Semantic Identity。"""
        p1 = _base_payload()
        p2 = _base_payload()
        p2["semantic_units"][0]["line_refs"] = ["P1L001"]
        assert _payload_semantic_hash(p1) == _payload_semantic_hash(p2)

    def test_confidence_change_does_not_change_hash(self):
        p1 = _base_payload()
        p2 = _base_payload()
        p2["semantic_units"][0]["confidence"] = 0.9
        assert _payload_semantic_hash(p1) == _payload_semantic_hash(p2)

    def test_llm_unit_checks_change_does_not_change_hash(self):
        p1 = _base_payload(extra_boundary=[])
        p2 = _base_payload(extra_boundary=[{"check": "passed"}])
        assert _payload_semantic_hash(p1) == _payload_semantic_hash(p2)

    def test_sections_change_changes_hash(self):
        p1 = _base_payload()
        p2 = _base_payload()
        p2["sections"] = [{"id": "S1", "title": "part one"}]
        assert _payload_semantic_hash(p1) != _payload_semantic_hash(p2)


class TestAnnotateFromPayloadIdentity:
    """annotate_from_payload 的实际去重行为。"""

    async def test_subject_change_creates_new_annotation(self, session, pdf_bytes):
        sv = await _seal(session, pdf_bytes)
        svc = _svc(session)
        mc = "mc-test-1"

        ann1 = await svc.annotate_from_payload(
            source_version_id=sv.id, payload=_base_payload(subject=None),
            model_config_hash=mc,
        )
        await session.flush()
        ann2 = await svc.annotate_from_payload(
            source_version_id=sv.id, payload=_base_payload(subject="物理"),
            model_config_hash=mc,
        )
        await session.flush()
        assert ann1.id != ann2.id, "subject null→物理 must produce new annotation"
        assert ann1.payload["document_metadata_claims"]["subject"] is None
        assert ann2.payload["document_metadata_claims"]["subject"] == "物理"

    async def test_same_semantics_reuses_annotation(self, session, pdf_bytes):
        sv = await _seal(session, pdf_bytes)
        svc = _svc(session)
        mc = "mc-test-2"

        ann1 = await svc.annotate_from_payload(
            source_version_id=sv.id, payload=_base_payload(subject="物理"),
            model_config_hash=mc,
        )
        await session.flush()
        ann2 = await svc.annotate_from_payload(
            source_version_id=sv.id, payload=_base_payload(subject="物理"),
            model_config_hash=mc,
        )
        await session.flush()
        assert ann1.id == ann2.id, "same semantics must reuse annotation"

    async def test_diagnostic_change_reuses_annotation(self, session, pdf_bytes):
        sv = await _seal(session, pdf_bytes)
        svc = _svc(session)
        mc = "mc-test-3"

        ann1 = await svc.annotate_from_payload(
            source_version_id=sv.id,
            payload=_base_payload(subject="化学", extra_boundary=[]),
            model_config_hash=mc,
        )
        await session.flush()
        ann2 = await svc.annotate_from_payload(
            source_version_id=sv.id,
            payload=_base_payload(subject="化学", extra_boundary=[{"check": "ok"}]),
            model_config_hash=mc,
        )
        await session.flush()
        assert ann1.id == ann2.id, "llm_unit_checks change must NOT create new annotation"

    async def test_old_annotation_not_modified(self, session, pdf_bytes):
        sv = await _seal(session, pdf_bytes)
        svc = _svc(session)
        mc = "mc-test-4"

        ann1 = await svc.annotate_from_payload(
            source_version_id=sv.id, payload=_base_payload(subject=None),
            model_config_hash=mc,
        )
        await session.flush()
        orig_id = ann1.id
        orig_subj = ann1.payload["document_metadata_claims"]["subject"]

        ann2 = await svc.annotate_from_payload(
            source_version_id=sv.id, payload=_base_payload(subject="生物"),
            model_config_hash=mc,
        )
        await session.flush()

        # Re-read ann1 from DB
        from app.models.snapshot import SemanticAnnotation
        from sqlalchemy import select
        row = (await session.execute(
            select(SemanticAnnotation).where(SemanticAnnotation.id == orig_id)
        )).scalar_one()
        assert row.id == orig_id
        assert row.payload["document_metadata_claims"]["subject"] == orig_subj, (
            "old annotation must not be modified"
        )

    async def test_unit_structure_change_creates_new(self, session, pdf_bytes):
        sv = await _seal(session, pdf_bytes)
        svc = _svc(session)
        mc = "mc-test-5"

        ann1 = await svc.annotate_from_payload(
            source_version_id=sv.id, payload=_base_payload(subject="地理"),
            model_config_hash=mc,
        )
        await session.flush()

        p2 = _base_payload(subject="地理")
        p2["semantic_units"][0]["question_number"] = 2  # structure change
        ann2 = await svc.annotate_from_payload(
            source_version_id=sv.id, payload=p2,
            model_config_hash=mc,
        )
        await session.flush()
        assert ann1.id != ann2.id, "unit structure change must produce new annotation"
