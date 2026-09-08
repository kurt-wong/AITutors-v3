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
        content["answer"] = {"answer_zone": "answer_table", "question_number": qn}
    return {"semantic_units": [{"unit_id": f"Q{qn}", "original_question_type": original,
             "content": content}]}


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


async def test_stem_unresolved_incomplete():
    payload = _single_choice_payload(qn="9")
    ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_choice_options_missing_incomplete():
    payload = {"semantic_units": [{"unit_id": "Q1", "original_question_type": "single_choice",
        "content": {"stem": {"question_label": "1"},
                    "answer": {"answer_zone": "answer_table", "question_number": "1"}}}]}
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
                {"unit_id": "Q1", "question_label": "1", "content": {
                    "stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_number": "1"}}},
                {"unit_id": "Q2", "question_label": "2", "content": {
                    "stem": {"question_label": "9"},  # 题号 9 不存在
                    "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_number": "2"}}},
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
                {"unit_id": "Q1", "question_label": "1", "content": {
                    "stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_number": "1"}}},
                {"unit_id": "Q2", "question_label": "2", "content": {
                    "stem": {"question_label": "2"}, "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_number": "2"}}},
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
    payload = {"semantic_units": [{"unit_id": "Q1", "original_question_type": "single_choice",
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
             {"unit_id": "Q1", "question_label": "1",
              "depends_on": [{"type": "material_dependency", "target": "material"}],
              "content": {"stem": {"question_label": "1"},
                          "options": [{"label": "A"}, {"label": "B"}],
                          "answer": {"answer_zone": "answer_table", "question_number": "1"}}}]}]}
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
             {"unit_id": "Q1", "question_label": "1",
              "content": {"stem": {"question_label": "1"},
                          "options": [{"label": "A"}, {"label": "B"}],
                          "answer": {"answer_zone": "answer_table", "question_number": "1"}}},
             {"unit_id": "Q2", "question_label": "2",
              "content": {"stem": {"question_label": "2"},
                          "options": [{"label": "A"}, {"label": "B"}]}}]}]}  # Q2 无 answer
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"


async def test_declared_image_fail_loud_incomplete():
    """F-R3：annotation 声明 image（F 尚无合法 figure_refs）→ incomplete，不得静默丢弃。"""
    lines = mk("1. 看图片回答", "A. 甲", "B. 乙", "【答案】", "1. A")
    payload = {"semantic_units": [{"unit_id": "Q1", "original_question_type": "single_choice",
        "content": {"stem": {"question_label": "1"},
                    "options": [{"label": "A"}, {"label": "B"}],
                    "answer": {"answer_zone": "answer_table", "question_number": "1"},
                    "image": {"image_ref": {"figure_id": "fig1"}}}}]}
    ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
    assert ir.units[0].semantic_status == "incomplete"  # fail-loud，非 ready + 丢图
