"""Gate G — GateService 编排（真实 DB）：E→F→G → candidate + 幂等 + auto approve。

run() 从 source_version + valid annotation 读行，per-ready-top-level-unit 产 candidate；
auto_approve → 同事务物化 A 域（AdmissionService 独立入口，不重跑 E/F/G）。
覆盖：standalone auto approved、幂等同 LE 复用、incomplete 不进 candidate、fill_in
pending_review、composite 全子题物化（material 单出 + unit_group members）。
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.core.hashing import logical_execution_hash, sha256_hex
from app.domains.gate.service import GateService
from app.models.content import (
    InstanceRoleContent,
    Material,
    MaterialLink,
    Question,
    QuestionInstance,
    UnitGroup,
    UnitGroupMember,
)
from app.models.snapshot import AdmissionCandidate, AdmissionEvent
from app.models.source import DocumentSourceLine
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

SINGLE_LINES = ("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
                "【答案】", "1. A")
FILLIN_LINES = ("1. 填空：___", "【答案】", "1. 苹果")
COMPOSITE_LINES = ("材料开始", "材料中间内容段落", "材料结束",
                   "1. 第一问", "A. 甲", "B. 乙", "C. 丙",
                   "2. 第二问", "A. 甲", "B. 乙", "C. 丙",
                   "【答案】", "1. A", "2. B")


def _single_units():
    return [
        {"unit_id": "Q1", "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "1"},
                     "options": [{"label": l} for l in "ABCD"],
                     "answer": {"answer_zone": "answer_table", "question_label": "1"}}}
    ]


def _fillin_units():
    return [
        {"unit_id": "Q1", "original_question_type": "fill_in",
         "content": {"stem": {"question_label": "1"},
                     "answer": {"answer_zone": "answer_table", "question_label": "1"}}}
    ]


def _composite_units():
    def sub(uid, qlabel, qn):
        return {"unit_id": uid, "question_label": qlabel,
                "original_question_type": "single_choice",
                "content": {"stem": {"question_label": qlabel},
                            "options": [{"label": l} for l in "ABC"],
                            "answer": {"answer_zone": "answer_table", "question_label": qn}}}
    return [
        {"unit_id": "U1-1", "unit_type": "composite_unit",
         "original_question_type": "single_choice",
         "shared_components": {"material": {
             "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                              "text": "材料开始"},
             "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                            "text": "材料结束"}}},
         "sub_questions": [sub("Q1", "1", "1"), sub("Q2", "2", "2")]}
    ]


def _foo_units():
    return [
        {"unit_id": "Q1", "original_question_type": "foo",
         "content": {"stem": {"question_label": "1"},
                     "options": [{"label": l} for l in "ABCD"],
                     "answer": {"answer_zone": "answer_table", "question_label": "1"}}}
    ]


async def _seed(session, texts=SINGLE_LINES, units=None, claims=None):
    units = _single_units() if units is None else units
    if claims is None:
        claims = {"subject": "数学", "grade": "三年级"}
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="g.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        document_id=doc.id, artifact_kind="pdf", role="native", provider="native",
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
        source_version_id=sv.id, annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1", model_config_hash=sha256_hex("m"),
        payload={"semantic_units": units,
                 "document_metadata_claims": claims},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return sv, ann


async def _count(session, model):
    return (await session.execute(select(func.count()).select_from(model))).scalar()


async def test_single_choice_auto_approved_end_to_end(session):
    sv, ann = await _seed(session)
    candidates, skipped = await GateService(session).run(
        source_version_id=sv.id, annotation_id=ann.id)
    assert skipped == []
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.decision_status == "approved"
    assert cand.unit_type == "standalone_unit"
    assert cand.gate_decision["decision"] == "auto_approve"
    assert cand.payload["display_hint"]["canonical_question_type"] == "single_choice"
    assert cand.payload["figure_refs"] == []
    assert (await _count(session, AdmissionCandidate)) == 1
    assert (await _count(session, AdmissionEvent)) == 1
    assert (await _count(session, Question)) == 1
    assert (await _count(session, QuestionInstance)) == 1
    assert (await _count(session, UnitGroup)) == 1
    q = (await session.execute(select(Question))).scalars().first()
    assert q.subject == "数学" and q.canonical_question_type == "single_choice"


async def test_gate_service_idempotent_same_le_reuses(session):
    sv, ann = await _seed(session)
    svc = GateService(session)
    c1, _ = await svc.run(source_version_id=sv.id, annotation_id=ann.id)
    await session.flush()
    # 同 annotation 再跑：LE 幂等命中既有，不重复物化
    c2, _ = await svc.run(source_version_id=sv.id, annotation_id=ann.id)
    await session.flush()
    assert len(c2) == 1 and c2[0].id == c1[0].id
    assert (await _count(session, AdmissionCandidate)) == 1
    assert (await _count(session, QuestionInstance)) == 1
    assert (await _count(session, AdmissionEvent)) == 1


async def test_incomplete_unit_not_enter_candidate(session):
    sv, ann = await _seed(session, texts=SINGLE_LINES, units=_foo_units())
    candidates, skipped = await GateService(session).run(
        source_version_id=sv.id, annotation_id=ann.id)
    assert candidates == []
    assert skipped == ["Q1"]
    assert (await _count(session, AdmissionCandidate)) == 0


async def test_fill_in_pending_review_not_auto(session):
    sv, ann = await _seed(session, texts=FILLIN_LINES, units=_fillin_units())
    candidates, _ = await GateService(session).run(
        source_version_id=sv.id, annotation_id=ann.id)
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.gate_decision["decision"] == "pending_review"
    assert cand.decision_status == "pending_review"  # 不自动；等人工 review_trail
    assert (await _count(session, QuestionInstance)) == 0  # 未物化


async def test_composite_auto_materializes_group_and_material(session):
    sv, ann = await _seed(session, texts=COMPOSITE_LINES, units=_composite_units())
    candidates, skipped = await GateService(session).run(
        source_version_id=sv.id, annotation_id=ann.id)
    assert skipped == []
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.unit_type == "composite_unit"
    assert cand.gate_decision["decision"] == "auto_approve"
    assert cand.decision_status == "approved"
    # material 只出一次；unit_group 一个含两个 member；两个 instance 无父 answer
    assert (await _count(session, Material)) == 1
    assert (await _count(session, MaterialLink)) == 2  # 每 child 链同一 material
    assert (await _count(session, QuestionInstance)) == 2
    assert (await _count(session, UnitGroup)) == 1
    assert (await _count(session, UnitGroupMember)) == 2
    # 父 composite 无独立 answer role（D8）——answer role_content 只属两个 child instance
    n_answer = (await session.execute(
        select(func.count()).select_from(InstanceRoleContent)
        .where(InstanceRoleContent.role == "answer"))).scalar()
    assert n_answer == 2
    # 材料不复制进子题 stem
    stems = (await session.execute(
        select(InstanceRoleContent.text).where(InstanceRoleContent.role == "stem"))).scalars().all()
    assert all("材料" not in s for s in stems)


async def test_reannotation_same_occurrence_is_idempotent_no_dup_rows(session):
    """对抗审查 HIGH#1 回归：同 source_version 二次标注导出同一 occurrence → 复用既有
    Question/Instance，不再无条件重插 role_contents（否则 UNIQUE 冲突 → 回滚）。"""
    sv, ann = await _seed(session)
    svc = GateService(session)
    c1, _ = await svc.run(source_version_id=sv.id, annotation_id=ann.id)
    await session.flush()
    assert c1[0].decision_status == "approved"
    assert (await _count(session, Question)) == 1
    assert (await _count(session, QuestionInstance)) == 1
    # 同 sv 二次标注（annotation_id/model 不同 → LE 不同；同一题同 occurrence 重新导出）
    ann2 = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id, annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1", model_config_hash=sha256_hex("m2"),
        payload={"semantic_units": _single_units(),
                 "document_metadata_claims": {"subject": "数学", "grade": "三年级"}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    c2, skipped = await svc.run(source_version_id=sv.id, annotation_id=ann2.id)
    await session.flush()
    assert skipped == []
    assert len(c2) == 1 and c2[0].id != c1[0].id
    assert c2[0].decision_status == "approved"  # 全量复用：正常 approved，不崩溃
    assert (await _count(session, Question)) == 1
    assert (await _count(session, QuestionInstance)) == 1
    assert (await _count(session, UnitGroup)) == 1  # 全复用不建空 group
    assert (await _count(session, AdmissionEvent)) == 2  # 每 candidate 一条物化记录


async def test_option_source_span_keeps_own_line_refs(session):
    """对抗审查 MED#2 回归：option role 的 source_span.line_refs 须是其自身行，非 stem 行。"""
    sv, ann = await _seed(session)
    await GateService(session).run(source_version_id=sv.id, annotation_id=ann.id)
    await session.flush()
    rows = (await session.execute(
        select(InstanceRoleContent).where(InstanceRoleContent.role == "option"))).scalars().all()
    assert len(rows) == 4
    by = {r.label: r for r in rows}
    assert by["A"].source_span["span_id"]
    assert by["A"].source_span["line_refs"] == ["P1L002"]  # A 在 SINGLE_LINES 第 2 行
    assert by["B"].source_span["line_refs"] == ["P1L003"]
    assert by["C"].source_span["line_refs"] == ["P1L004"]
    assert by["D"].source_span["line_refs"] == ["P1L005"]
    # 与 stem 行（P1L001）区分：选项行 ≠ 题干行
    assert all(by[l].source_span["line_refs"] != ["P1L001"] for l in "ABCD")


async def test_machine_rejected_candidate_auto_terminal(session, monkeypatch):
    """对抗审查 MED#3 回归：gate_decision=rejected → decision_status 立即 terminal
    rejected（确定性 Gate Policy 写状态，10 §5.2），不留 pending_review 僵尸。"""
    from app.domains.gate import service as gate_service

    def _fake_evaluate(**kwargs):
        return {"gate_policy_version": "admission-gate/v1", "decision": "rejected",
                "layers": {}, "reasons": ["structural contradiction (fixture)"]}

    monkeypatch.setattr(gate_service, "evaluate", _fake_evaluate)
    sv, ann = await _seed(session)
    candidates, skipped = await GateService(session).run(
        source_version_id=sv.id, annotation_id=ann.id)
    assert skipped == []
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.gate_decision["decision"] == "rejected"
    assert cand.decision_status == "rejected"
    assert (await _count(session, QuestionInstance)) == 0  # rejected 不物化
    assert (await _count(session, AdmissionEvent)) == 0  # reject 不写物化事件


def test_admission_question_dedup_matches_compiler_key():
    """对抗审查 MED#4 回归：admission._dedup_key 与 Compiler._question_dedup_key 对选项
    正文以数字开头时也同键（防跨路径把同一题建两遍 Question）。"""
    from app.domains.compile.compiler import Compiler
    from app.domains.compile.snapshot import CompiledRole
    from app.domains.gate.admission import _dedup_key

    stem_text = "1. 下列哪个是水果"
    opts = [{"label": "A", "text": "A. 1. 甲"}, {"label": "B", "text": "B. 2. 乙"}]
    stem = CompiledRole(role="stem", span_id="s0", line_refs=(),
                        text=stem_text, text_hash="0" * 64, label=None)
    opt_roles = tuple(
        CompiledRole(role="option", span_id=f"o{i}", line_refs=(),
                     text=o["text"], text_hash="0" * 64, label=o["label"])
        for i, o in enumerate(opts)
    )
    compiler_key = Compiler({}, {})._question_dedup_key("single_choice", stem, opt_roles)
    stem_dict = {"role": "stem", "span_id": "s0", "line_refs": [],
                 "text": stem_text, "text_hash": "0" * 64, "label": None}
    roles = [{"role": "option", "span_id": f"o{i}", "line_refs": [],
              "text": o["text"], "text_hash": "0" * 64, "label": o["label"]}
             for i, o in enumerate(opts)]
    assert _dedup_key("single_choice", stem_dict, roles) == compiler_key


async def test_compile_le_hash_uses_minimal_domain(session):
    """BUG-V3-022：compile LE hash 只含 contract 4 项 + input 3 项（含 unit_id），
    不含 prompt_version/model_config_hash/source_version 等存储字段。"""
    from app.domains.gate import service as gate_service
    sv, ann = await _seed(session)
    candidates, _ = await GateService(session).run(
        source_version_id=sv.id, annotation_id=ann.id)
    cand = candidates[0]
    expected = logical_execution_hash(
        task_type="document_ingest",
        stage="compile",
        contract_domain={
            "resolver_version": gate_service.RESOLVER_VERSION,
            "ir_schema_version": gate_service.IR_SCHEMA_VERSION,
            "compiler_version": gate_service.COMPILER_VERSION,
            "gate_policy_version": gate_service.GATE_POLICY_VERSION,
        },
        input_domain={
            "annotation_id": str(ann.id),
            "annotation_payload_hash": sha256_hex(ann.payload),
            "unit_id": "Q1",
        },
    )
    assert cand.logical_execution_hash == expected


def test_compile_contract_domain_exact_field_set():
    """BUG-V3-022：contract_domain 恰 4 项（不含 ann 的 prompt/model_config/source）。"""
    contract = GateService._compile_contract_domain()
    assert set(contract) == {"resolver_version", "ir_schema_version",
                             "compiler_version", "gate_policy_version"}


def test_compile_input_domain_exact_field_set():
    """BUG-V3-022：input_domain 恰 3 项（不含派生指纹 source_version_id/resolver/compiler hash）。"""
    from types import SimpleNamespace
    ann = SimpleNamespace(payload={"semantic_units": []})
    input_domain = GateService._compile_input_domain(uuid.uuid4(), ann, "Q1")
    assert set(input_domain) == {"annotation_id", "annotation_payload_hash", "unit_id"}


async def test_compile_le_insensitive_to_ann_build_metadata(session):
    """BUG-V3-022 negative：prompt_version/model_config_hash 不进 compile LE → 改它们 LE 不变。"""
    sv, ann = await _seed(session)
    c1, _ = await GateService(session).run(source_version_id=sv.id, annotation_id=ann.id)
    ann.model_config_hash = sha256_hex("CHANGED-model")
    ann.prompt_version = "semantic-annotation/v99"
    await session.flush()
    c2, _ = await GateService(session).run(source_version_id=sv.id, annotation_id=ann.id)
    assert c2[0].id == c1[0].id  # 幂等复用：build metadata 不进 compile LE


async def test_compile_le_sensitive_to_resolver_version(session, monkeypatch):
    """BUG-V3-022 negative：resolver_version 在 contract → 变则 LE 变（新 candidate）。"""
    from app.domains.gate import service as gate_service
    sv, ann = await _seed(session)
    c1, _ = await GateService(session).run(source_version_id=sv.id, annotation_id=ann.id)
    monkeypatch.setattr(gate_service, "RESOLVER_VERSION", "resolver/v2")
    c2, _ = await GateService(session).run(source_version_id=sv.id, annotation_id=ann.id)
    assert c2[0].id != c1[0].id
    assert c1[0].logical_execution_hash != c2[0].logical_execution_hash


async def _reannotate(session, sv, claims):
    """同 source_version 二次标注（不同 annotation_id/model，同题同 occurrence）。"""
    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id, annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1", model_config_hash=sha256_hex(str(uuid.uuid4())),
        payload={"semantic_units": _single_units(), "document_metadata_claims": claims},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    return ann


async def test_subject_grade_nullable_on_missing_claim(session):
    """BUG-V3-021：claim 缺失 → subject/grade = NULL（非空串）。"""
    sv, ann = await _seed(session, claims={"grade": "三年级"})  # subject missing
    await GateService(session).run(source_version_id=sv.id, annotation_id=ann.id)
    await session.flush()
    q = (await session.execute(select(Question))).scalars().first()
    assert q.subject is None  # unknown = NULL，非 ""
    assert q.grade == "三年级"


async def test_metadata_convergence_null_to_known(session):
    """BUG-V3-021：NULL → known 允许补写。"""
    sv, ann = await _seed(session, claims={})  # 全缺失 → NULL
    await GateService(session).run(source_version_id=sv.id, annotation_id=ann.id)
    await session.flush()
    ann2 = await _reannotate(session, sv, {"subject": "数学", "grade": "三年级"})
    await GateService(session).run(source_version_id=sv.id, annotation_id=ann2.id)
    await session.flush()
    q = (await session.execute(select(Question))).scalars().first()
    assert q.subject == "数学"  # NULL → known 补写
    assert q.grade == "三年级"


async def test_metadata_conflict_fails_loud(session):
    """BUG-V3-021：known → different → fail-loud（RepositoryError，非静默覆盖）。"""
    from app.repositories.base import RepositoryError

    sv, ann = await _seed(session, claims={"subject": "数学", "grade": "三年级"})
    await GateService(session).run(source_version_id=sv.id, annotation_id=ann.id)
    await session.flush()
    ann2 = await _reannotate(session, sv, {"subject": "物理", "grade": "三年级"})
    with pytest.raises(RepositoryError):
        await GateService(session).run(source_version_id=sv.id, annotation_id=ann2.id)


async def test_missing_annotation_fails_fast_no_fallback(session):
    """BUG-V3-009：annotation_id 无效 → RepositoryError，绝不回退查询「最新 annotation」。"""
    from app.repositories.base import RepositoryError

    sv, _ = await _seed(session)
    with pytest.raises(RepositoryError):
        await GateService(session).run(
            source_version_id=sv.id, annotation_id=uuid.uuid4()
        )
