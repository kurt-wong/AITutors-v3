"""EB-008 测试辅助：seed document/sv/annotation/candidate + Authority 事件。

供 test_eb008_evidence_authority.py 与改造后的 evidence/promotion/admission 测试共用。
最小 payload（claim_id="Q1"）只保证 FK 与投影路径可用；完整物化结构由
test_admission._dummy_payload 覆盖。
"""

from __future__ import annotations

import uuid

from app.core.hashing import sha256_hex
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.models.source import DocumentSourceLine
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

CLAIM_ID = "Q1"


def minimal_payload(claim_id: str = CLAIM_ID) -> dict:
    """含 IR root unit 的最小 candidate payload（_candidate_claim_id 可解析）。"""
    return {
        "ir_snapshot": {
            "ir_schema": "semantic-question-ir/v0.3",
            "units": [
                {"unit_id": claim_id, "unit_type": "standalone_question",
                 "semantic_status": "ready", "sub_questions": []},
            ],
        },
        "resolved_spans": [], "compiled_roles": [], "answer": [],
    }


def auto_gate_decision() -> dict:
    return {"gate_policy_version": "admission-gate/v1", "decision": "auto_approve",
            "layers": {}, "reasons": []}


def pending_gate_decision() -> dict:
    return {"gate_policy_version": "admission-gate/v1", "decision": "pending_review",
            "layers": {}, "reasons": []}


def rejected_gate_decision() -> dict:
    return {"gate_policy_version": "admission-gate/v1", "decision": "rejected",
            "layers": {}, "reasons": ["bad"]}


async def seed_candidate(
    session,
    *,
    gate: dict | None = None,
    texts: tuple[str, ...] = ("1. stem line",),
    claim_id: str = CLAIM_ID,
):
    """手工 seed document+sealed sv+annotation+candidate（真实 DB 行）。

    返回 (source_version, annotation, candidate)。
    """
    gate = auto_gate_decision() if gate is None else gate
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="g.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    n = len(texts)
    sv = await src.create_source_version(
        document_id=doc.id, artifact_kind="pdf", role="native", provider="native",
        body_text="\n".join(texts), body_hash=sha256_hex(list(texts)),
        integrity_hash=sha256_hex(list(texts)), page_count=1, line_count=n,
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
                 "document_metadata_claims": {"subject": "数学", "grade": "三年级"}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    cand = await SnapshotRepository(session).create_admission_candidate(
        unit_type="standalone_unit", source_version_id=sv.id, annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=minimal_payload(claim_id), gate_decision=gate,
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann, cand


async def seed_validated_authority(
    session, candidate, source_version, *, claim_id: str = CLAIM_ID
):
    """为 (candidate, claim) 落一条 validated 事件（auto_gate 路径模拟）。"""
    repo = EvidenceRepository(session)
    event = ValidationEvent(
        event_id=f"ve-{claim_id}-{uuid.uuid4().hex[:8]}",
        claim_id=claim_id,
        validation_result="validated",
        checks=(CheckResult(check_id="BYTE_PROVEN", result="pass"),),
        validation_method="frozen_header_rule",
        validator="gate/v1",
    )
    rec = await repo.append_event(
        event,
        candidate_id=candidate.id,
        source_version_id=source_version.id,
    )
    await session.flush()
    return rec
