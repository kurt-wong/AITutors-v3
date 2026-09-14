"""Gate G — AdmissionService：decision_status 唯一入口 + 物化事务（真实 DB）。

覆盖状态机探针（plan 表）：Repository 公共接口直改 → AppendOnlyViolation；approve 物化
同事务（A 域 + admission_event + approved）；P0-G-002（gate_decision=rejected 拒 approve）；
P0-G-003（machine/human reject 证据链）；防双物化 no-op；terminal 拒迁；人工 approve 路径。
"""

import asyncio
import uuid

import pytest
from sqlalchemy import func, select, text

from app.core.hashing import sha256_hex
from app.db.session import async_session_maker
from app.domains.gate.admission import AdmissionService
from app.models.content import InstanceRoleContent, Question, QuestionInstance, UnitGroup
from app.models.snapshot import (
    AdmissionCandidate,
    AdmissionEvent,
)
from app.models.source import DocumentSourceLine
from app.repositories.base import AppendOnlyViolation, RepositoryError
from app.repositories.content_repository import ContentRepository
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
                     "answer": {"answer_zone": "answer_table", "question_label": "1"}}}
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
                  "reviewer_id": "u1", "confirmed_fields": ["answer"]})
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
    assert trail[-1]["reasons"] == ["student file expired"]
    assert trail[-1]["verified_by"] == "human"
    assert "time" in trail[-1] and trail[-1]["time"]  # BUG-V3-025：append 统一注入 time


async def test_review_trail_entry_schema_frozen_025(session):
    """BUG-V3-025 终裁：review_trail 统一 entry schema——公共字段 {decision,
    verified_by, reviewer_id, time}（time 由 append_review_trail 注入）；approve→
    confirmed_fields，reject→reasons，二者互不共存（不制造无意义空字段）。"""
    sv, ann = await _seed(session)
    cand = await _make_candidate(session, sv, ann, _pending_gd())
    await session.flush()
    snap = SnapshotRepository(session)
    await snap.append_review_trail(cand.id, {
        "decision": "approve", "verified_by": "human",
        "reviewer_id": "u1", "confirmed_fields": ["answer"]})
    await snap.append_review_trail(cand.id, {
        "decision": "reject", "verified_by": "golden",
        "reviewer_id": "g1", "reasons": ["expired"]})
    await session.flush()
    approve_entry, reject_entry = cand.review_trail
    for entry in (approve_entry, reject_entry):
        assert entry["verified_by"] in ("human", "golden")
        assert entry["reviewer_id"]
        assert "time" in entry and isinstance(entry["time"], str) and entry["time"]
    assert approve_entry["decision"] == "approve"
    assert approve_entry["confirmed_fields"] == ["answer"]
    assert "reasons" not in approve_entry
    assert reject_entry["decision"] == "reject"
    assert reject_entry["reasons"] == ["expired"]
    assert "confirmed_fields" not in reject_entry


async def test_human_reject_gate_decision_immutable_026(session):
    """BUG-V3-026 终裁：人工 reject 不改 gate_decision（逐字段保留机器判断）；机器拒受
    理由在 gate_decision.reasons，人工拒受理由在 review_trail.reasons，二者不同物。"""
    sv, ann = await _seed(session)
    gd = {"gate_policy_version": "admission-gate/v1", "decision": "pending_review",
          "layers": {}, "reasons": ["machine-kept"]}
    cand = await _make_candidate(session, sv, ann, gd)
    await session.flush()
    decided = await AdmissionService(session).reject(
        candidate_id=cand.id, reasons=["human-reason"], source="human", reviewer_id="u9")
    assert decided.decision_status == "rejected"
    assert decided.gate_decision == {
        "gate_policy_version": "admission-gate/v1", "decision": "pending_review",
        "layers": {}, "reasons": ["machine-kept"]}  # gate_decision 保留，人工不改
    assert decided.review_trail[-1]["reasons"] == ["human-reason"]
    assert decided.review_trail[-1]["reasons"] != decided.gate_decision["reasons"]


async def test_terminal_rejected_approve_denied(session):
    sv, ann = await _seed(session)
    cand = await _make_candidate(session, sv, ann, _pending_gd())
    await session.flush()
    admission = AdmissionService(session)
    await admission.reject(candidate_id=cand.id, reasons=["x"], source="human")
    with pytest.raises(RepositoryError, match="only from pending_review"):
        await admission.approve(candidate_id=cand.id,
                                provenance={"source": "human", "reviewer_id": "u"})


# ------------------------------------------------------------------ F1/F2 转正
# 二轮对抗审查（_audit_g2 GA4/GA5）经显式 commit 真实 DB 暴露两实现缺陷，已修复：
#   F1 物化把 payload IR root 的 standalone_question 误写 unit_groups.unit_type（10 §6.5
#      值域 = standalone_unit/composite_unit）；改用 candidate.unit_type（service 已映射 A 域）。
#   F2 create_instance 未带 candidate 的 LE provenance → 落 NULL（10 §6.2/§3「由产生它的
#      admission 带出」）；改为从 candidate 原样继承（copy，非新建）。
# 两测试走显式 commit + 新 session reload，断言持久值而非 ORM 内存对象。

async def _purge_materialized(session, *, sv_id: str, doc_id: str) -> None:
    """按 FK 序删净一次 approve 物化链（显式 commit 回归用，保 suite 隔离）。

    新建 Question 经本 sv 的 question_instances 反查删除：常规 suite 其它文档不 commit，
    无跨 sv FK 残留，本 sv instance 引用的即本候选新建。
    """
    cands = (await session.execute(text(
        "SELECT id FROM admission_candidates WHERE source_version_id=:s"),
        {"s": sv_id})).scalars().all()
    qids = (await session.execute(text(
        "SELECT DISTINCT question_id FROM question_instances "
        "WHERE source_version_id=:s"), {"s": sv_id})).scalars().all()
    if cands:
        ph = ",".join(f"'{c}'" for c in cands)
        await session.execute(text(
            f"DELETE FROM admission_events WHERE candidate_id IN ({ph})"))
        await session.execute(text(
            f"DELETE FROM admission_candidates WHERE id IN ({ph})"))
    await session.execute(text(
        "DELETE FROM instance_role_contents WHERE instance_id IN "
        "(SELECT id FROM question_instances WHERE source_version_id=:s)"), {"s": sv_id})
    await session.execute(text(
        "DELETE FROM unit_group_members WHERE instance_id IN "
        "(SELECT id FROM question_instances WHERE source_version_id=:s)"), {"s": sv_id})
    await session.execute(text(
        "DELETE FROM question_instances WHERE source_version_id=:s"), {"s": sv_id})
    await session.execute(text(
        "DELETE FROM unit_groups WHERE source_version_id=:s"), {"s": sv_id})
    await session.execute(text(
        "DELETE FROM semantic_annotations WHERE source_version_id=:s"), {"s": sv_id})
    await session.execute(text(
        "DELETE FROM document_source_spans WHERE source_version_id=:s"), {"s": sv_id})
    await session.execute(text(
        "DELETE FROM document_source_lines WHERE source_version_id=:s"), {"s": sv_id})
    await session.execute(text(
        "DELETE FROM document_source_versions WHERE id=:s"), {"s": sv_id})
    if qids:
        phq = ",".join(f"'{q}'" for q in qids)
        await session.execute(text(f"DELETE FROM questions WHERE id IN ({phq})"))
    await session.execute(text("DELETE FROM documents WHERE id=:d"), {"d": doc_id})


async def test_materialized_unit_group_unit_type_is_candidate_a_domain():
    """F1 回归（10 §6.5）：物化后 unit_groups.unit_type = candidate 的 A 域值，不得把
    payload IR 的 standalone_question 漏入展示/持久化域。commit + 新 session reload。"""
    sv_id = doc_id = None
    try:
        async with async_session_maker() as s1:
            sv, ann = await _seed(s1)
            sv_id, doc_id = str(sv.id), str(sv.document_id)
            cand = await _make_candidate(s1, sv, ann, _auto_gd())
            await s1.flush()
            # 复现原 bug 前提：candidate=A 域 standalone_unit，payload IR root=standalone_question
            assert cand.unit_type == "standalone_unit"
            assert cand.payload["ir_snapshot"]["units"][0]["unit_type"] == "standalone_question"
            await AdmissionService(s1).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"})
            await s1.commit()

        async with async_session_maker() as s2:  # 全新 session：读已提交持久值
            groups = (await s2.execute(select(UnitGroup))).scalars().all()
            assert len(groups) == 1
            assert groups[0].unit_type == "standalone_unit", (
                f"unit_groups.unit_type={groups[0].unit_type!r}，违反 10 §6.5 值域 "
                f"(standalone_unit/composite_unit)——IR standalone_question 不得写入")
            await s2.rollback()
    finally:
        if sv_id:
            async with async_session_maker() as sc:
                await _purge_materialized(sc, sv_id=sv_id, doc_id=doc_id)
                await sc.commit()


async def test_materialized_instance_inherits_candidate_le_provenance():
    """F2 回归（10 §6.2/§3）：instance 的 LE provenance 由产生它的 admission 带出——
    从 candidate 原样继承（copy，非新建/非 NULL）。commit + 新 session reload。"""
    sv_id = doc_id = None
    qids: list[str] = []
    expected = None
    try:
        async with async_session_maker() as s1:
            sv, ann = await _seed(s1)
            sv_id, doc_id = str(sv.id), str(sv.document_id)
            cand = await _make_candidate(s1, sv, ann, _auto_gd())
            await s1.flush()
            expected = (cand.logical_execution_stage,
                        cand.logical_execution_hash, cand.attempt_id)
            await AdmissionService(s1).approve(
                candidate_id=cand.id, provenance={"source": "auto_gate"})
            await s1.commit()

        async with async_session_maker() as s2:
            inst = (await s2.execute(select(QuestionInstance))).scalars().first()
            assert inst is not None
            assert (inst.logical_execution_stage,
                    inst.logical_execution_hash,
                    inst.attempt_id) == expected, (
                "instance LE provenance 应原样继承其物化 admission 的 candidate "
                "(10 §6.2/§3)，而非 NULL/新生成")
            await s2.rollback()
    finally:
        if sv_id:
            async with async_session_maker() as sc:
                await _purge_materialized(sc, sv_id=sv_id, doc_id=doc_id)
                await sc.commit()


# ------------------------------------------------------------------ P0：原子性 + 并发

async def test_materialize_failure_rolls_back_all_a_domain_rows():
    """Admission 失败原子性（10 §5.2/§5.4）：物化中途异常 → 调用方不 COMMIT →
    整体 ROLLBACK → A 域行数为 0，candidate 保持 pending_review。

    monkeypatch create_role_content 抛异常（Question + Instance 已 flush），
    验证 rollback 后 questions/question_instances/instance_role_contents/
    unit_groups/admission_events 全为空。
    """
    sv_id = doc_id = None
    cand_id = None
    try:
        async with async_session_maker() as s1:
            sv, ann = await _seed(s1)
            sv_id, doc_id = str(sv.id), str(sv.document_id)
            cand = await _make_candidate(s1, sv, ann, _auto_gd())
            cand_id = cand.id
            await s1.commit()

        # 注入失败：create_role_content 抛异常（Question + Instance 已 flush）
        original_crc = ContentRepository.create_role_content

        async def _boom(*args, **kwargs):
            raise RuntimeError("injected materialize failure")

        ContentRepository.create_role_content = _boom
        try:
            async with async_session_maker() as s2:
                with pytest.raises(RuntimeError, match="injected materialize failure"):
                    await AdmissionService(s2).approve(
                        candidate_id=cand_id, provenance={"source": "auto_gate"})
                await s2.rollback()  # 调用方不 COMMIT → 整体 ROLLBACK
        finally:
            ContentRepository.create_role_content = original_crc

        # 验证 rollback 后 A 域全空
        async with async_session_maker() as s3:
            assert await _counts(s3, Question) == 0, "rollback 后 questions 应为 0"
            assert await _counts(s3, QuestionInstance) == 0, "rollback 后 instances 应为 0"
            assert await _counts(s3, InstanceRoleContent) == 0, "rollback 后 role_contents 应为 0"
            assert await _counts(s3, UnitGroup) == 0, "rollback 后 unit_groups 应为 0"
            assert await _counts(s3, AdmissionEvent) == 0, "rollback 后 admission_events 应为 0"
            # candidate 仍 pending_review（无 "approved 但未物化" 中间态）
            row = (await s3.execute(
                text("SELECT decision_status FROM admission_candidates WHERE id=:i"),
                {"i": str(cand_id)})).scalar_one()
            assert row == "pending_review"
    finally:
        if sv_id:
            async with async_session_maker() as sc:
                await _purge_materialized(sc, sv_id=sv_id, doc_id=doc_id)
                await sc.commit()


async def test_concurrent_approve_single_materialization():
    """并发 Approval：两个 DB Session 同时 approve 同一 Candidate → 恰 1 物化。

    lock_candidate (FOR UPDATE) 串行化两个 session；后到者看到 approved → no-op。
    验证：两调用均返回 approved，admission_events=1，question_instances=1。
    """
    sv_id = doc_id = None
    try:
        async with async_session_maker() as s1:
            sv, ann = await _seed(s1)
            sv_id, doc_id = str(sv.id), str(sv.document_id)
            cand = await _make_candidate(s1, sv, ann, _auto_gd())
            cand_id = str(cand.id)
            await s1.commit()

        async def _approve():
            async with async_session_maker() as s:
                result = await AdmissionService(s).approve(
                    candidate_id=uuid.UUID(cand_id),
                    provenance={"source": "auto_gate"})
                await s.commit()
                return result.decision_status

        statuses = await asyncio.gather(_approve(), _approve())
        assert all(st == "approved" for st in statuses), \
            f"并发 approve 应均返回 approved，实为 {statuses}"

        # 验证单次物化
        async with async_session_maker() as s3:
            n_ev = (await s3.execute(text(
                "SELECT count(*) FROM admission_events WHERE candidate_id=:c"),
                {"c": cand_id})).scalar()
            n_i = (await s3.execute(text(
                "SELECT count(*) FROM question_instances WHERE source_version_id=:s"),
                {"s": sv_id})).scalar()
            assert n_ev == 1, f"并发 approve 应恰 1 admission_event，实为 {n_ev}"
            assert n_i == 1, f"并发 approve 应恰 1 instance，实为 {n_i}"
    finally:
        if sv_id:
            async with async_session_maker() as sc:
                await _purge_materialized(sc, sv_id=sv_id, doc_id=doc_id)
                await sc.commit()
