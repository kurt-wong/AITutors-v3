"""Gate G — AdmissionService：decision_status 唯一入口 + 物化事务（真实 DB）。

覆盖状态机探针（plan 表）：Repository 公共接口直改 → AppendOnlyViolation；approve 物化
同事务（A 域 + admission_event + approved）；P0-G-002（gate_decision=rejected 拒 approve）；
P0-G-003（machine/human reject 证据链）；防双物化 no-op；terminal 拒迁；人工 approve 路径。
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.core.hashing import sha256_hex
from app.domains.gate.admission import AdmissionService
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from app.models.snapshot import (
    AdmissionCandidate,
    AdmissionEvent,
)
from app.models.source import DocumentSourceLine
from app.repositories.base import AppendOnlyViolation, RepositoryError
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000ae")

SINGLE_LINES = ("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
                "【答案】", "1. A")


def _single_units():
    return [
        {"unit_id": "Q1", "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "1"},
                     "options": [{"label": l} for l in "ABCD"],
                     "answer": {"answer_zone": "answer_table", "question_number": "1"}}}
    ]


async def _seed(session, texts=SINGLE_LINES, units=None):
    """手工 seed document+sealed version+lines+valid annotation（不经 PDF/seal/LLM）。

    UUIDPrimaryKeyMixin 的 PK default 在 flush 时才回填对象 id → 每阶段一次 flush。
    """
    units = _single_units() if units is None else units
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
        status="sealed",
    )
    await session.flush()
    for i, t in enumerate(texts):
        await src.append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref=f"P1L{i + 1:03d}", seq=i + 1,
            page_no=1, line_no_in_page=i + 1, text=t, block_type="text",
            line_hash=sha256_hex(t),
        ))
    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id, annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1", model_config_hash=sha256_hex("m"),
        payload={"semantic_units": units,
                 "document_metadata_claims": {"subject": "数学", "grade": "三年级"}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann


def _dummy_payload():
    """满足 approve 物化所需的 payload 结构（真实 G build 由 test_gate_service 覆盖）。"""
    return {
        "ir_snapshot": {
            "ir_schema": "semantic-question-ir/v0.3",
            "source_version_id": str(SVID), "annotation_id": str(ANN_ID),
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
             "text": "1. 下列哪个是水果", "text_hash": sha256_hex("1. 下列哪个是水果"),
             "label": None, "unit_id": "Q1", "kind": "content"},
            {"role": "option", "span_id": "sp-Q1.option.A", "line_refs": ["P1L002"],
             "text": "A. 苹果", "text_hash": sha256_hex("A. 苹果"),
             "label": "A", "unit_id": "Q1", "kind": "content"},
            {"role": "option", "span_id": "sp-Q1.option.B", "line_refs": ["P1L003"],
             "text": "B. 香蕉", "text_hash": sha256_hex("B. 香蕉"),
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


def _pending_gd():
    return {"gate_policy_version": "admission-gate/v1", "decision": "pending_review",
            "layers": {}, "reasons": []}


async def _make_candidate(session, sv, ann, gate):
    return await SnapshotRepository(session).create_admission_candidate(
        unit_type="standalone_unit", source_version_id=sv.id, annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=_dummy_payload(), gate_decision=gate,
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )


async def _counts(session, model):
    return (await session.execute(select(func.count()).select_from(model))).scalar()


# ------------------------------------------------------------------ 探针
async def test_repo_public_update_raises_append_only(session):
    """Repository 公共接口直改 decision_status → AppendOnlyViolation（P0-G-001）。"""
    snap = SnapshotRepository(session)
    with pytest.raises(AppendOnlyViolation):
        await snap.update_candidate_decision()


async def test_approve_materializes_same_tx(session):
    sv, ann = await _seed(session)
    cand = await _make_candidate(session, sv, ann, _auto_gd())
    await session.flush()
    admission = AdmissionService(session)
    decided = await admission.approve(candidate_id=cand.id,
                                      provenance={"source": "auto_gate"})
    await session.flush()
    assert decided.decision_status == "approved"
    # 同事务：A 域行 + admission_event + decision 同步可见
    assert (await _counts(session, Question)) >= 1
    assert (await _counts(session, QuestionInstance)) == 1
    assert (await _counts(session, InstanceRoleContent)) == 4  # stem + 2 options + answer
    assert (await _counts(session, AdmissionEvent)) == 1
    # 复用问题带 metadata claims（BUG-V3-021 M1）
    q = (await session.execute(select(Question))).scalars().first()
    assert q.subject == "数学" and q.grade == "三年级"
    rc = (await session.execute(
        select(InstanceRoleContent).where(InstanceRoleContent.role == "answer"))).scalars().first()
    assert rc.answer_status["verified_correct"] is True


async def test_approve_p0_g_002_rejected_gate_denied(session):
    """P0-G-002：gate_decision=rejected 即使 pending_review → 拒 approve。"""
    sv, ann = await _seed(session)
    cand = await _make_candidate(
        session, sv, ann,
        {"gate_policy_version": "admission-gate/v1", "decision": "rejected",
         "layers": {}, "reasons": ["bad"]})
    await session.flush()
    with pytest.raises(RepositoryError, match="gate_decision=rejected"):
        await AdmissionService(session).approve(candidate_id=cand.id,
                                                provenance={"source": "auto_gate"})
    # 无物化残留：candidate 仍 pending
    row = (await session.execute(select(AdmissionCandidate))).scalars().first()
    assert row.decision_status == "pending_review"
    assert (await _counts(session, QuestionInstance)) == 0


async def test_auto_approve_requires_gate_auto(session):
    """auto_gate source 但 gate=pending → 拒（非 auto 不可自动 approve）。"""
    sv, ann = await _seed(session)
    cand = await _make_candidate(session, sv, ann, _pending_gd())
    await session.flush()
    with pytest.raises(RepositoryError, match="auto approve requires"):
        await AdmissionService(session).approve(candidate_id=cand.id,
                                                provenance={"source": "auto_gate"})


async def test_manual_approve_requires_review_trail(session):
    """人工路径：无 review_trail approve 确认 → 拒；append 后再 approve → approved。"""
    sv, ann = await _seed(session)
    cand = await _make_candidate(session, sv, ann, _pending_gd())
    await session.flush()
    snap = SnapshotRepository(session)
    admission = AdmissionService(session)
    with pytest.raises(RepositoryError, match="manual approve requires"):
        await admission.approve(candidate_id=cand.id,
                                provenance={"source": "human", "reviewer_id": "u1"})
    await snap.append_review_trail(
        cand.id, {"decision": "approve", "verified_by": "human",
                  "reviewer_id": "u1", "confirmed_fields": ["answer"], "time": "2026-09-06T00:00:00Z"})
    await session.flush()
    decided = await admission.approve(candidate_id=cand.id,
                                      provenance={"source": "human", "reviewer_id": "u1"})
    assert decided.decision_status == "approved"


async def test_approved_approve_noop_no_second_event(session):
    """防双物化：approved → approve no-op，无第二物化/admission_event。"""
    sv, ann = await _seed(session)
    cand = await _make_candidate(session, sv, ann, _auto_gd())
    await session.flush()
    admission = AdmissionService(session)
    await admission.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
    await session.flush()
    again = await admission.approve(candidate_id=cand.id, provenance={"source": "auto_gate"})
    await session.flush()
    assert again.decision_status == "approved"
    assert (await _counts(session, AdmissionEvent)) == 1


async def test_rejected_gate_machine_reject_transitions(session):
    """machine_gate reject：gate 已 rejected → decision rejected；不重写 gate_decision。"""
    sv, ann = await _seed(session)
    gd = {"gate_policy_version": "admission-gate/v1", "decision": "rejected",
          "layers": {}, "reasons": ["structural contradiction"]}
    cand = await _make_candidate(session, sv, ann, gd)
    await session.flush()
    decided = await AdmissionService(session).reject(
        candidate_id=cand.id, reasons=["machine"], source="machine_gate")
    assert decided.decision_status == "rejected"
    assert decided.gate_decision["reasons"] == ["structural contradiction"]  # 未覆盖
    assert decided.review_trail is None  # machine reasons 不 append review_trail


async def test_human_reject_reasons_only_review_trail(session):
    """P0-G-003 human：reasons 只进 review_trail；gate_decision 保留机器判断。"""
    sv, ann = await _seed(session)
    cand = await _make_candidate(session, sv, ann, _pending_gd())
    await session.flush()
    decided = await AdmissionService(session).reject(
        candidate_id=cand.id, reasons=["student file expired"], source="human",
        reviewer_id="u9")
    assert decided.decision_status == "rejected"
    assert decided.gate_decision["decision"] == "pending_review"  # 保留
    trail = decided.review_trail
    assert trail and trail[-1]["decision"] == "reject"
    assert trail[-1]["reason"] == ["student file expired"]
    assert trail[-1]["verified_by"] == "human"


async def test_terminal_rejected_approve_denied(session):
    sv, ann = await _seed(session)
    cand = await _make_candidate(session, sv, ann, _pending_gd())
    await session.flush()
    admission = AdmissionService(session)
    await admission.reject(candidate_id=cand.id, reasons=["x"], source="human")
    with pytest.raises(RepositoryError, match="only from pending_review"):
        await admission.approve(candidate_id=cand.id,
                                provenance={"source": "human", "reviewer_id": "u"})
