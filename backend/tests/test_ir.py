"""Gate F — IR 装配 + 不变量 1-8（段 F，20 §6）。用段 E SourceResolver 产出 ResolvedRun 作输入。"""

import uuid

from app.domains.compile.ir import IRBuilder
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000f")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000f0")


def mk(*texts):
    return tuple(SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
                 for i, t in enumerate(texts))


def _run(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)


def _single_choice_payload(qn="1", original="single_choice", options=("A", "B", "C", "D"),
                           with_answer=True):
    content = {
        "stem": {"question_label": qn},
        "options": [{"label": l} for l in options],
    }
    if with_answer:
        content["answer"] = {"answer_zone": "answer_table", "question_label": qn}
    return {"semantic_units": [{"unit_id": f"Q{qn}", "unit_type": "standalone_unit",
             "original_question_type": original, "content": content}]}


def _ready_lines():
    return mk("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
              "【答案】", "1. A")


async def test_standalone_ready():
    payload = _single_choice_payload()
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert len(ir.units) == 1
    node = ir.units[0]
    assert node.semantic_status == "ready"
    assert node.original_question_type == "single_choice"
    assert {c.role for c in node.content} == {"stem", "option", "answer"}
    assert all(c.span_id for c in node.content)


async def test_unknown_canonical_type_incomplete():
    payload = _single_choice_payload(original="foo")
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_alias_type_not_resolved_incomplete():
    """BUG-V3-014：别名（single-choice/单选题）不映射，fail-loud 判 incomplete（禁 alias resolver）。"""
    for alias in ("single-choice", "单选题"):
        payload = _single_choice_payload(original=alias)
        ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
        assert ir.units[0].semantic_status == "incomplete"


def test_semantic_status_domain_m2():
    """X2.6 M.2: SEMANTIC_STATUS 值域 = {ready, incomplete, unknown}。

    D10 provenance:
        previous: SEMANTIC_STATUS == frozenset({"ready", "incomplete"})
        why: BUG-V3-018 froze domain at two values; X2.6 M.2 unfreezes
        new: SEMANTIC_STATUS == frozenset({"ready", "incomplete", "unknown"})
        provenance: X2.6-OD-D9-01 (OD-FINAL-01) + X2.6-IMPL-AUTH-01 + M.2
        note: unknown = semantic expression, NOT migration; old IR unchanged
    """
    from app.domains.compile import SEMANTIC_STATUS
    assert SEMANTIC_STATUS == frozenset({"ready", "incomplete", "unknown"})


def test_semantic_status_domain_historical_fixture():
    """HISTORICAL FIXTURE (D10): pre-M.2 domain was {ready, incomplete} (BUG-V3-018).

    Preserves original constraint for provenance. M.2 expanded to 3 values;
    ready/incomplete behavior unchanged (compatibility).
    """
    from app.domains.compile import SEMANTIC_STATUS
    historical_domain = frozenset({"ready", "incomplete"})
    assert historical_domain.issubset(SEMANTIC_STATUS), (
        "ready and incomplete must remain in SEMANTIC_STATUS after M.2"
    )


def test_content_roles_m1_contract_frozen():
    """BUG-V3-016：12×4 M1 role contract 冻结；逐型锁定 content_roles_for（零语义扩展）。"""
    from app.domains.compile import CANONICAL_TYPES, content_roles_for
    choice = frozenset({"single_choice", "multiple_choice", "true_false"})
    for t in sorted(CANONICAL_TYPES):
        roles = content_roles_for(t)
        assert roles["stem"] == "required"
        assert roles["answer"] == "required"
        assert roles["explanation"] == "optional"
        assert roles["options"] == ("required_for_choice" if t in choice else "not_applicable")
    # canonical_type=None（未知题型）→ 保守三元，无 options 键
    assert content_roles_for(None) == {
        "stem": "required", "answer": "required", "explanation": "optional",
    }


async def test_stem_unresolved_incomplete():
    payload = _single_choice_payload(qn="9")
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_choice_options_missing_incomplete():
    payload = {"semantic_units": [{"unit_id": "Q1", "unit_type": "standalone_unit",
        "original_question_type": "single_choice",
        "content": {"stem": {"question_label": "1"},
                    "answer": {"answer_zone": "answer_table", "question_label": "1"}}}]}
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_answer_declared_but_unresolved_incomplete():
    payload = _single_choice_payload()
    lines = mk("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子")
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_composite_child_unresolved_not_ready():
    lines = mk("阅读材料", "根据材料回答第1～2题", "1. 第一问", "A. 甲", "B. 乙",
               "2. 第二问", "A. 丙", "B. 丁", "【答案】", "1. A", "2. A")
    payload = {
        "semantic_units": [{
            "unit_id": "U1-2", "unit_type": "composite_unit",
            "original_question_type": "single_choice",
            "shared_components": {"material": {
                "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                                 "text": "阅读材料"},
                "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                               "text": "根据材料回答第1～2题"}}},
            "sub_questions": [
                {"unit_id": "Q1", "unit_type": "standalone_unit", "question_label": "1",
                 "content": {
                    "stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_label": "1"}}},
                {"unit_id": "Q2", "unit_type": "standalone_unit", "question_label": "2",
                 "content": {
                    "stem": {"question_label": "9"},  # 题号 9 不存在
                    "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_label": "2"}}},
            ],
        }]
    }
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    comp = ir.units[0]
    assert comp.unit_type == "composite_unit"
    assert comp.semantic_status == "incomplete"  # invariant 7：子题 unresolved → composite 非 ready


async def test_composite_all_ready():
    lines = mk("阅读材料", "材料正文内容", "根据材料回答第1～2题",
               "1. 第一问", "A. 甲", "B. 乙",
               "2. 第二问", "A. 丙", "B. 丁", "【答案】", "1. A", "2. A")
    payload = {
        "semantic_units": [{
            "unit_id": "U1-2", "unit_type": "composite_unit",
            "original_question_type": "single_choice",
            "shared_components": {"material": {
                "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                                 "text": "阅读材料"},
                "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                               "text": "根据材料回答第1～2题"}}},
            "sub_questions": [
                {"unit_id": "Q1", "unit_type": "standalone_unit", "question_label": "1",
                 "content": {
                    "stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_label": "1"}}},
                {"unit_id": "Q2", "unit_type": "standalone_unit", "question_label": "2",
                 "content": {
                    "stem": {"question_label": "2"}, "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_label": "2"}}},
            ],
        }]
    }
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    comp = ir.units[0]
    assert comp.semantic_status == "ready"
    assert all(s.semantic_status == "ready" for s in comp.sub_questions)


async def test_ir_input_not_mutated():
    import copy
    payload = _single_choice_payload()
    lines = _ready_lines()
    payload_before = copy.deepcopy(payload)
    run = _run(lines, payload)
    IRBuilder.build(run, payload, SVID, ANN_ID)
    assert payload == payload_before


async def test_answer_required_missing_incomplete():
    """F-R1：content_roles answer=required；缺 answer → incomplete（不得 ready）。"""
    payload = {"semantic_units": [{"unit_id": "Q1", "unit_type": "standalone_unit",
        "original_question_type": "single_choice",
        "content": {"stem": {"question_label": "1"},
                    "options": [{"label": l} for l in "ABCD"]}}]}  # 无 answer
    lines = mk("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子")
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_material_dependency_unresolved_composite_incomplete():
    """F-R2：子题 material_dependency 指向 material 但其 span 未 resolved → composite incomplete。"""
    lines = mk("材料开始", "材料结束", "1. 第一问", "A. 甲", "B. 乙", "【答案】", "1. A")
    payload = {"semantic_units": [
        {"unit_id": "U1-1", "unit_type": "composite_unit",
         "original_question_type": "single_choice",
         "shared_components": {"material": {
             "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                              "text": "材料开始"},
             "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                            "text": "材料结束"}}},
         "sub_questions": [
             {"unit_id": "Q1", "unit_type": "standalone_unit", "question_label": "1",
              "depends_on": [{"type": "material_dependency", "target": "material"}],
              "content": {"stem": {"question_label": "1"},
                          "options": [{"label": "A"}, {"label": "B"}],
                          "answer": {"answer_zone": "answer_table", "question_label": "1"}}}]}]}
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"  # material span 未 resolved


async def test_composite_child_missing_answer_propagates_incomplete():
    """invariant 7 传播：composite 一子题缺 answer → composite incomplete。"""
    lines = mk("阅读材料", "材料正文", "根据材料回答第1～2题",
               "1. 第一问", "A. 甲", "B. 乙",
               "2. 第二问", "A. 丙", "B. 丁", "【答案】", "1. A", "2. A")
    payload = {"semantic_units": [
        {"unit_id": "U1-2", "unit_type": "composite_unit",
         "original_question_type": "single_choice",
         "shared_components": {"material": {
             "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                              "text": "阅读材料"},
             "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                            "text": "根据材料回答第1～2题"}}},
         "sub_questions": [
             {"unit_id": "Q1", "unit_type": "standalone_unit", "question_label": "1",
              "content": {"stem": {"question_label": "1"},
                          "options": [{"label": "A"}, {"label": "B"}],
                          "answer": {"answer_zone": "answer_table", "question_label": "1"}}},
             {"unit_id": "Q2", "unit_type": "standalone_unit", "question_label": "2",
              "content": {"stem": {"question_label": "2"},
                          "options": [{"label": "A"}, {"label": "B"}]}}]}]}  # Q2 无 answer
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_declared_image_fail_loud_incomplete():
    """F-R3：annotation 声明 image（F 尚无合法 figure_refs）→ incomplete，不得静默丢弃。"""
    lines = mk("1. 看图片回答", "A. 甲", "B. 乙", "【答案】", "1. A")
    payload = {"semantic_units": [{"unit_id": "Q1", "unit_type": "standalone_unit",
        "original_question_type": "single_choice",
        "content": {"stem": {"question_label": "1"},
                    "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_label": "1"},
                    "image": {"image_ref": {"figure_id": "fig1"}}}}]}
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"  # fail-loud，非 ready + 丢图


# ================================================================ M.2 Acceptance Tests
# X2.6 M.2: SEMANTIC_STATUS unfreeze + UNKNOWN expression
# Cases: A(ready compat) B(incomplete compat) C(unknown IR) D(unknown compiler safety)
#        E(old fixture compat) — see test_x26_m2_semantic_status.py for Case F


async def test_m2_case_c_unknown_expressible_in_ir():
    """M.2 Case C: annotation payload with semantic_status="unknown" → IR preserves unknown."""
    payload = _single_choice_payload()
    payload["semantic_units"][0]["semantic_status"] = "unknown"
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "unknown"


async def test_m2_case_c_unknown_direct_construction():
    """M.2 Case C: IRNode directly constructed with semantic_status="unknown" is valid."""
    from app.domains.compile.ir import IR, IRNode, validate_ir
    node = IRNode(
        unit_id="U1", unit_type="standalone_question",
        question_number="1", question_number_range=None,
        original_question_type="single_choice",
        semantic_status="unknown",
    )
    ir = IR(
        ir_schema="semantic-question-ir/v0.3",
        source_version_id=SVID, annotation_id=ANN_ID, units=(node,),
    )
    validated = validate_ir(ir)
    assert validated.units[0].semantic_status == "unknown"


async def test_m2_case_d_unknown_no_compiler_leaves():
    """M.2 Case D: unknown IR node → compiler produces ZERO leaves (compiler safety boundary)."""
    from app.domains.compile.compiler import Compiler
    from app.domains.compile.ir import IR, IRContent, IRNode
    node = IRNode(
        unit_id="U1", unit_type="standalone_question",
        question_number="1", question_number_range=None,
        original_question_type="single_choice",
        content=(
            IRContent(role="stem", span_id="sp-U1.stem"),
            IRContent(role="answer", span_id="sp-U1.answer"),
        ),
        semantic_status="unknown",
    )
    ir = IR(
        ir_schema="semantic-question-ir/v0.3",
        source_version_id=SVID, annotation_id=ANN_ID, units=(node,),
    )
    compiler = Compiler(span_by_id={}, line_by_ref={})
    snapshot = compiler.compile(ir)
    assert len(snapshot.leaves) == 0, "unknown must not produce compiler leaves"
    assert len(snapshot.materials) == 0


async def test_m2_case_d_unknown_composite_no_compiler_leaves():
    """M.2 Case D: composite with unknown status → compiler produces ZERO leaves/materials."""
    from app.domains.compile.compiler import Compiler
    from app.domains.compile.ir import IR, IRContent, IRNode
    comp = IRNode(
        unit_id="U1-2", unit_type="composite_unit",
        question_number=None, question_number_range="1-2",
        original_question_type="single_choice",
        shared_components=(IRContent(role="material", span_id="sp-U1-2.material"),),
        sub_questions=(
            IRNode(
                unit_id="Q1", unit_type="standalone_question",
                question_number="1", question_number_range=None,
                original_question_type="single_choice",
                semantic_status="ready",
            ),
        ),
        semantic_status="unknown",
    )
    ir = IR(
        ir_schema="semantic-question-ir/v0.3",
        source_version_id=SVID, annotation_id=ANN_ID, units=(comp,),
    )
    compiler = Compiler(span_by_id={}, line_by_ref={})
    snapshot = compiler.compile(ir)
    assert len(snapshot.leaves) == 0, "unknown composite must not produce leaves"
    assert len(snapshot.materials) == 0, "unknown composite must not produce materials"


async def test_m2_case_e_compatibility_ready_still_works():
    """M.2 Case E: existing ready fixture produces correct IR after M.2 (no regression)."""
    payload = _single_choice_payload()
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "ready"
    assert ir.units[0].original_question_type == "single_choice"


async def test_m2_case_e_compatibility_incomplete_still_works():
    """M.2 Case E: existing incomplete fixture produces incomplete after M.2 (no regression)."""
    payload = _single_choice_payload(original="foo")
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_m2_ready_still_produces_leaves():
    """M.2 Case A: ready node still produces leaves after M.2 (compiler unchanged for ready)."""
    import uuid as _uuid
    from app.domains.compile.compiler import Compiler
    from app.domains.compile.ir import IR, IRContent, IRNode
    svid = _uuid.UUID("00000000-0000-0000-0000-00000000000f")
    annid = _uuid.UUID("00000000-0000-0000-0000-0000000000f0")

    class _FakeSpan:
        granularity = "multi_line"
        start_offset = None
        end_offset = None
        line_refs = ("P1L001",)

    class _FakeLine:
        text = "test content"

    node = IRNode(
        unit_id="U1", unit_type="standalone_question",
        question_number="1", question_number_range=None,
        original_question_type="single_choice",
        content=(
            IRContent(role="stem", span_id="sp-U1.stem"),
            IRContent(role="answer", span_id="sp-U1.answer"),
        ),
        semantic_status="ready",
    )
    ir = IR(
        ir_schema="semantic-question-ir/v0.3",
        source_version_id=svid, annotation_id=annid, units=(node,),
    )
    compiler = Compiler(
        span_by_id={"sp-U1.stem": _FakeSpan(), "sp-U1.answer": _FakeSpan()},
        line_by_ref={"P1L001": _FakeLine()},
    )
    snapshot = compiler.compile(ir)
    assert len(snapshot.leaves) == 1, "ready node must still produce a leaf after M.2"


# ================================================================ F-M3-04 Runtime Correction
# X2.6 F-M3-04: IRBuilder must reject non-canonical unit_type (no silent default).
# Owner decision: unknown/illegal unit_type → explicit rejection, NOT standalone_unit.
# Mechanism reused: ValueError + UNIT_TYPES closed set (same as gate._candidate_unit_type).
# OD-2 CLOSED: legacy vocabulary boundary normalization is NOT IR construction's job.


async def test_f_m3_04_case_a_valid_standalone_accepted():
    """F-M3-04 Test A: unit_type=standalone_unit → accepted by IRBuilder."""
    payload = _single_choice_payload()
    assert payload["semantic_units"][0]["unit_type"] == "standalone_unit"
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert ir.units[0].unit_type == "standalone_unit"
    assert ir.units[0].semantic_status == "ready"


async def test_f_m3_04_case_b_valid_composite_accepted():
    """F-M3-04 Test B: unit_type=composite_unit → accepted by IRBuilder."""
    lines = mk("阅读材料", "材料正文内容", "根据材料回答第1～2题",
               "1. 第一问", "A. 甲", "B. 乙",
               "2. 第二问", "A. 丙", "B. 丁", "【答案】", "1. A", "2. A")
    payload = {
        "semantic_units": [{
            "unit_id": "U1-2", "unit_type": "composite_unit",
            "original_question_type": "single_choice",
            "shared_components": {"material": {
                "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                                 "text": "阅读材料"},
                "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                               "text": "根据材料回答第1～2题"}}},
            "sub_questions": [
                {"unit_id": "Q1", "unit_type": "standalone_unit", "question_label": "1",
                 "content": {
                    "stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_label": "1"}}},
                {"unit_id": "Q2", "unit_type": "standalone_unit", "question_label": "2",
                 "content": {
                    "stem": {"question_label": "2"}, "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_label": "2"}}},
            ],
        }]
    }
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    assert ir.units[0].unit_type == "composite_unit"
    assert ir.units[0].semantic_status == "ready"


async def test_f_m3_04_case_c_unknown_value_explicit_failure():
    """F-M3-04 Test C: unit_type=unknown_unit → explicit failure, NOT standalone_unit."""
    import pytest
    payload = _single_choice_payload()
    payload["semantic_units"][0]["unit_type"] = "unknown_unit"
    with pytest.raises(ValueError, match="non-canonical unit_type"):
        IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)


async def test_f_m3_04_case_d_legacy_vocabulary_not_silently_accepted():
    """F-M3-04 Test D: legacy Producer vocabulary must not be silently accepted as Unit Type.

    standalone_question / composite_question are legacy Producer vocabulary (OD-2 CLOSED).
    Canonical runtime validation (IRBuilder) must reject them explicitly.
    This is NOT OD-2 re-implementation — it proves canonical runtime does not treat
    legacy vocabulary as canonical Unit Type.
    """
    import pytest
    for legacy in ("standalone_question", "composite_question"):
        payload = _single_choice_payload()
        payload["semantic_units"][0]["unit_type"] = legacy
        with pytest.raises(ValueError, match="non-canonical unit_type"):
            IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)


async def test_f_m3_04_case_e_missing_value_not_silent_default():
    """F-M3-04 Test E: missing unit_type → explicit failure, NOT silent default.

    Evidence that upstream schema does NOT guarantee presence at this boundary:
    historical test fixtures omitted unit_type and relied on the silent default
    (ir.py:112 unit.get("unit_type", "standalone_unit")). Therefore Test E is required.
    """
    import pytest
    payload = _single_choice_payload()
    del payload["semantic_units"][0]["unit_type"]
    with pytest.raises(ValueError, match="non-canonical unit_type"):
        IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)


async def test_f_m3_04_sub_question_missing_unit_type_rejected():
    """F-M3-04: composite sub_question missing unit_type → explicit failure (no silent default)."""
    import pytest
    lines = mk("阅读材料", "材料正文", "根据材料回答第1～2题",
               "1. 第一问", "A. 甲", "B. 乙", "【答案】", "1. A")
    payload = {"semantic_units": [
        {"unit_id": "U1-2", "unit_type": "composite_unit",
         "original_question_type": "single_choice",
         "shared_components": {"material": {
             "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                              "text": "阅读材料"},
             "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                            "text": "根据材料回答第1～2题"}}},
         "sub_questions": [
             {"unit_id": "Q1", "question_label": "1",
              "content": {"stem": {"question_label": "1"},
                          "options": [{"label": "A"}, {"label": "B"}],
                          "answer": {"answer_zone": "answer_table", "question_label": "1"}}}]}]}
    with pytest.raises(ValueError, match="non-canonical unit_type"):
        IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)


def test_f_m3_04_no_silent_default_pattern_in_source():
    """F-M3-04: IRBuilder._node must not contain the silent-default pattern."""
    import inspect
    from app.domains.compile.ir import IRBuilder
    source = inspect.getsource(IRBuilder._node)
    assert 'get("unit_type", "standalone_unit")' not in source, (
        "IRBuilder._node must not silent-default missing unit_type to standalone_unit"
    )
    assert "UNIT_TYPES" in source, (
        "IRBuilder._node must validate against UNIT_TYPES closed set"
    )
    assert "standalone_question" not in source, (
        "IRBuilder._node must not reference legacy vocabulary as canonical Unit Type"
    )


def test_f_m3_04_unit_types_closed_set_unchanged():
    """F-M3-04: canonical Unit Type closed set remains {standalone_unit, composite_unit}."""
    from app.domains.compile import UNIT_TYPES
    from app.domains.gate import UNIT_TYPES as GATE_UNIT_TYPES
    assert UNIT_TYPES == frozenset({"standalone_unit", "composite_unit"})
    assert GATE_UNIT_TYPES is UNIT_TYPES, (
        "gate must re-export compile UNIT_TYPES (single source of truth)"
    )
