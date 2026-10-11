# -*- coding: utf-8 -*-
"""IR 边缘：composite 兄弟子题 unit_id 相同时，状态与原因必须一致。

DSH 推论：collect_validation_problems 与 _validate_node 若对 seen 语义不一致，
会出现父节点 ready / 原因为空，但子节点 incomplete。
"""
from app.domains.compile.ir import (
    IR,
    IRContent,
    IRNode,
    _validate_node,
    collect_validation_problems,
    validate_ir,
)


def _leaf(uid: str, *, ok: bool = True, status: str = "incomplete") -> IRNode:
    if ok:
        content = (
            IRContent(role="stem", span_id=f"sp-{uid}.stem"),
            IRContent(role="answer", span_id=f"sp-{uid}.answer"),
            IRContent(role="option", span_id=f"sp-{uid}.opt.A", label="A"),
        )
    else:
        content = ()
    return IRNode(
        unit_id=uid,
        unit_type="standalone_unit",
        question_number=None,
        question_number_range=None,
        original_question_type="single_choice",
        content=content,
        shared_components=(),
        sub_questions=(),
        relations=(),
        semantic_status=status,
    )


def _composite(uid: str, subs, *, status: str = "incomplete") -> IRNode:
    return IRNode(
        unit_id=uid,
        unit_type="composite_unit",
        question_number=None,
        question_number_range="1-2",
        original_question_type="single_choice",
        content=(),
        shared_components=(IRContent(role="material", span_id=f"sp-{uid}.material"),),
        sub_questions=tuple(subs),
        relations=(),
        semantic_status=status,
    )


def test_sibling_shared_unit_id_parent_not_ready_and_reason_matches():
    """兄弟子题同 unit_id：父不得 ready，且原因列表与校验状态一致。"""
    parent = _composite("U1-2", [_leaf("DUP"), _leaf("DUP")])

    reasons = collect_validation_problems(parent, set())
    validated = _validate_node(parent, set())
    sub_status = [s.semantic_status for s in validated.sub_questions]

    # 父节点原因必须包含子题未就绪（而非空列表）
    assert "composite sub_question not ready" in reasons, reasons
    # 父节点状态必须非 ready
    assert validated.semantic_status != "ready", validated.semantic_status
    # 子节点之间：重复 id 至少有一个非 ready（invariant 5）
    assert any(s != "ready" for s in sub_status), sub_status
    # 状态与原因一致：父 incomplete ⇔ 原因非空
    assert (validated.semantic_status == "incomplete") == bool(reasons)


def test_sibling_distinct_unit_id_still_ready():
    """正常路径不回归：兄弟 id 不同且内容齐备 → 父 ready、子全 ready。"""
    parent = _composite("U3-5", [_leaf("A1"), _leaf("B1")])
    reasons = collect_validation_problems(parent, set())
    validated = _validate_node(parent, set())
    assert reasons == []
    assert validated.semantic_status == "ready"
    assert [s.semantic_status for s in validated.sub_questions] == ["ready", "ready"]


def test_sibling_shared_unit_id_in_validate_ir():
    """走 validate_ir 全路径：composite 内重复 unit_id 不得整组 ready。"""
    parent = _composite("U1-2", [_leaf("DUP"), _leaf("DUP")])
    ir = IR(
        ir_schema="semantic-question-ir/v0.3",
        source_version_id=__import__("uuid").uuid4(),
        annotation_id=__import__("uuid").uuid4(),
        units=(parent,),
    )
    validated = validate_ir(ir)
    root = validated.units[0]
    assert root.semantic_status != "ready"
    assert [s.semantic_status for s in root.sub_questions] != ["ready", "ready"]


def test_unknown_child_marks_composite_not_ready():
    """M.2：子题 unknown 非 ready → composite 不得 ready（invariant 7）。"""
    parent = _composite("U8-9", [_leaf("S1", ok=True), _leaf("UNK", status="unknown")])
    reasons = collect_validation_problems(parent, set())
    validated = _validate_node(parent, set())
    assert "composite sub_question not ready" in reasons
    assert validated.semantic_status != "ready"
    # unknown 子题状态保留
    assert validated.sub_questions[1].semantic_status == "unknown"


def test_unknown_parent_does_not_false_duplicate_children():
    """unknown 父节点不得因 collect 预走子树而把子题误判 duplicate。"""
    child = _leaf("S1", ok=True, status="ready")
    parent = _composite("U1-2", [child], status="unknown")
    reasons = collect_validation_problems(parent, set())
    # 原因不应因预走子树而出现误报 duplicate
    assert "duplicate unit_id" not in reasons, reasons
    validated = _validate_node(parent, set())
    assert validated.semantic_status == "unknown"
    # 子题不因父节点 unknown 被误判 duplicate
    assert validated.sub_questions[0].semantic_status == "ready"
    assert "duplicate unit_id" not in collect_validation_problems(validated.sub_questions[0], set())
