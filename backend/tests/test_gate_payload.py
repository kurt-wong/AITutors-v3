"""Gate G — Candidate payload 组装（10 §5.3 + plan D6，纯函数；不触 DB）。

payload 是不可变可重放编译快照；本测试断言：顶层恰 8 字段、composite parent 无独立
answer（D8）、material 单出一次（20 #4）、figure_refs 恒空（M1 BUG-V3-020）、
gate_decision 不混入 payload（P0-1）、compiled text_hash 与正文一致（2d）。
"""

import hashlib
import uuid

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.payload import build
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000ae")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _pipeline(lines, payload, root_unit_id="Q1"):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    snap = Compiler({s.span_id: s for s in run.resolved_spans},
                    {l.line_ref: l for l in lines}).compile(ir)
    root = next(u for u in ir.units if u.unit_id == root_unit_id)
    return build(root=root, ir=ir, compiled=snap, resolved_run=run)


def _single_lines():
    return _mk("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
               "【答案】", "1. A")


def _single_payload():
    return {"semantic_units": [
        {"unit_id": "Q1", "unit_type": "standalone_unit",
         "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "1"}, "options": [{"label": l} for l in "ABCD"],
                     "answer": {"answer_zone": "answer_table", "question_label": "1"}}}]}


# ---------------------------------------------------------------- standalone
def test_standalone_payload_has_exact_eight_keys():
    p = _pipeline(_single_lines(), _single_payload())
    assert set(p) == {"ir_snapshot", "resolved_spans", "compiled_roles", "answer",
                      "figure_refs", "knowledge_links", "evidence", "display_hint"}
    assert p["figure_refs"] == [] and p["knowledge_links"] == []  # M1 恒空
    assert p["display_hint"]["canonical_question_type"] == "single_choice"
    assert p["display_hint"]["unit_type"] == "standalone_unit"


def test_standalone_compiled_roles_and_answer_consistent():
    p = _pipeline(_single_lines(), _single_payload())
    # compiled_roles：stem + 4 options（answer 独立进 answer[]）
    assert [r["role"] for r in p["compiled_roles"]] == ["stem", "option", "option", "option", "option"]
    for r in p["compiled_roles"]:
        assert r["text_hash"] == hashlib.sha256(r["text"].encode()).hexdigest()
        assert r["span_id"] and r["line_refs"] and r["unit_id"] == "Q1"
    assert len(p["answer"]) == 1
    a = p["answer"][0]
    assert a["source_located"] is True and a["complete"] is True and a["verified_correct"] is None
    assert a["text_hash"] == hashlib.sha256(a["text"].encode()).hexdigest()
    assert a["unit_id"] == "Q1"
    # question_number：顶层 standalone 由 F 自 unit 级 question_label 取（annotation 可空）。
    # resolved_spans 覆盖全部消费 span，逐条可溯源
    consumed = {r["span_id"] for r in p["compiled_roles"]} | {a["span_id"] for a in p["answer"]}
    got = {s["span_id"] for s in p["resolved_spans"]}
    assert consumed <= got


def test_evidence_only_resolver_compiler():
    p = _pipeline(_single_lines(), _single_payload())
    kinds = {e["kind"] for e in p["evidence"]}
    assert kinds <= {"resolver", "compiler"}  # gate reasons 不进 payload（P0-1）
    assert any(e["kind"] == "compiler" for e in p["evidence"])


# ---------------------------------------------------------------- composite（D8 / 20 #4）
def _composite():
    lines = _mk("材料开始", "材料中间内容段落", "材料结束",
                "1. 第一问", "A. 甲", "B. 乙", "C. 丙",
                "2. 第二问", "A. 甲", "B. 乙", "C. 丙",
                "【答案】", "1. A", "2. B")
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
              "original_question_type": "single_choice",
              "content": {"stem": {"question_label": "1"},
                          "options": [{"label": l} for l in "ABC"],
                          "answer": {"answer_zone": "answer_table", "question_label": "1"}}},
             {"unit_id": "Q2", "unit_type": "standalone_unit", "question_label": "2",
              "original_question_type": "single_choice",
              "content": {"stem": {"question_label": "2"},
                          "options": [{"label": l} for l in "ABC"],
                          "answer": {"answer_zone": "answer_table", "question_label": "2"}}}]}]}
    return lines, payload


def test_composite_payload_material_once_parent_no_answer():
    lines, payload = _composite()
    p = _pipeline(lines, payload, "U1-1")
    # ir_snapshot：root composite + 子题复数
    units = p["ir_snapshot"]["units"]
    assert units[0]["unit_type"] == "composite_unit"
    assert [u["unit_id"] for u in units] == ["U1-1", "Q1", "Q2"]
    assert len(p["answer"]) == 2  # D8：仅子题有 answer，无父空行
    assert {a["unit_id"] for a in p["answer"]} == {"Q1", "Q2"}
    # material 只输出一次（compiled_roles kind=material），不复制进子题
    mats = [r for r in p["compiled_roles"] if r["kind"] == "material"]
    assert len(mats) == 1
    assert mats[0]["unit_id"] == "U1-1"
    content_units = {r["unit_id"] for r in p["compiled_roles"] if r["kind"] == "content"}
    assert content_units == {"Q1", "Q2"}
    assert all("材料" not in r["text"] for r in p["compiled_roles"] if r["role"] == "stem")
    # display_hint：composite 呈现子题 canonical 集
    assert p["display_hint"]["unit_type"] == "composite_unit"
    assert p["display_hint"]["canonical_question_type"] == ["single_choice"]
