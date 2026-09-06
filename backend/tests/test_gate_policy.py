"""Gate G — GatePolicy 四层判定（20 §8.1/§8.2；D1 保留 resolution_status）。

一次 evaluate = 一个 candidate（top-level unit）。真实 E→F 链产 compiled + IR，喂
policy.evaluate(root, ir, compiled, resolved_run)；用 dataclasses.replace 构造
resolution 变体（contextual / text_hash mismatch）覆盖 provenance 边界。

decision：auto_approve / pending_review / rejected（P0-G-002：rejected terminal）。
"""

import dataclasses
import uuid

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.compile.snapshot import CompiledSnapshot
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import ResolvedRun, SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000e")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000ae")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _single_lines(answer_text="A"):
    return _mk("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
               "【答案】", f"1. {answer_text}")


def _single_payload(ctype="single_choice"):
    return {"semantic_units": [
        {"unit_id": "Q1", "original_question_type": ctype,
         "content": {"stem": {"question_label": "1"},
                     "options": [{"label": l} for l in "ABCD"],
                     "answer": {"answer_zone": "answer_table", "question_number": "1"}}}]}


def _pipeline(lines, payload, root_unit_id="Q1"):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    lines_by_ref = {l.line_ref: l for l in lines}
    compiled = Compiler(spans, lines_by_ref).compile(ir)
    root = next(u for u in ir.units if u.unit_id == root_unit_id)
    return root, ir, compiled, run


def _decision(root, ir, compiled, run):
    return evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)


# ---------------------------------------------------------------- standalone auto
def test_single_choice_auto_approve():
    root, ir, snap, run = _pipeline(_single_lines("A"), _single_payload())
    d = _decision(root, ir, snap, run)
    assert d["decision"] == "auto_approve"
    assert all(d["layers"][k]["status"] == "pass"
               for k in ("structural", "provenance", "semantic", "admission"))


def test_single_choice_auto_letter_shifted():
    root, ir, snap, run = _pipeline(_single_lines("B"), _single_payload())
    assert _decision(root, ir, snap, run)["decision"] == "auto_approve"


def test_multiple_choice_auto():
    root, ir, snap, run = _pipeline(_single_lines("ABD"), _single_payload("multiple_choice"))
    assert _decision(root, ir, snap, run)["decision"] == "auto_approve"


def test_single_choice_unmappable_answer_pending():
    # 答案区写非选项文本 → grammar None → pending_review（非 rejected）。
    root, ir, snap, run = _pipeline(_single_lines("略"), _single_payload())
    d = _decision(root, ir, snap, run)
    assert d["decision"] == "pending_review"
    assert any("grammar" in r for r in d["reasons"])


def test_fill_in_pending():
    # fill_in 不开放 strict-auto（D2 / 20 §8.4）→ pending_review。
    lines = _mk("1. 填空：___", "【答案】", "1. 苹果")
    payload = {"semantic_units": [
        {"unit_id": "Q1", "original_question_type": "fill_in",
         "content": {"stem": {"question_label": "1"},
                     "answer": {"answer_zone": "answer_table", "question_number": "1"}}}]}
    root, ir, snap, run = _pipeline(lines, payload)
    d = _decision(root, ir, snap, run)
    assert d["decision"] == "pending_review"
    assert any("not strict-auto" in r for r in d["reasons"])


def test_true_false_ab_pending_via_grammar_none():
    # true_false 答案区写 A → grammar A/B→None → pending（不补 A/B 映射，用户裁决）。
    # canonical 覆盖验证 decision 路径；grammar 语义已由 test_gate_grammar 锁定。
    root, ir, snap, run = _pipeline(_single_lines("A"), _single_payload())
    leaf = dataclasses.replace(snap.leaves[0], canonical_question_type="true_false")
    snap2 = CompiledSnapshot(snap.source_version_id, snap.annotation_id, (leaf,), snap.materials)
    assert _decision(root, ir, snap2, run)["decision"] == "pending_review"


# ---------------------------------------------------------------- contextual / provenance
def test_contextual_span_not_auto_pending():
    root, ir, snap, run = _pipeline(_single_lines("A"), _single_payload())
    new_spans = tuple(
        dataclasses.replace(s, resolution_status="contextual") for s in run.resolved_spans
    )
    run2 = ResolvedRun(source_version_id=run.source_version_id,
                       resolved_spans=new_spans,
                       unresolved_references=run.unresolved_references,
                       resolved_relations=run.resolved_relations,
                       unresolved_relations=run.unresolved_relations)
    d = _decision(root, ir, snap, run2)
    assert d["decision"] == "pending_review"  # contextual 可人工，不 rejected
    assert any("not byte-proven" in r for r in d["reasons"])
    assert d["layers"]["provenance"]["status"] == "pass"  # 非矛盾，仅不 auto


def test_text_hash_mismatch_rejected():
    root, ir, snap, run = _pipeline(_single_lines("A"), _single_payload())
    leaf = snap.leaves[0]
    bad_answer = dataclasses.replace(leaf.answer, text_hash="0" * 64)
    bad_leaf = dataclasses.replace(leaf, answer=bad_answer)
    snap2 = CompiledSnapshot(snap.source_version_id, snap.annotation_id, (bad_leaf,), snap.materials)
    d = _decision(root, ir, snap2, run)
    assert d["decision"] == "rejected"  # 证据不成立 → terminal
    assert any("text_hash mismatch" in r for r in d["reasons"])


def test_structural_missing_leaf_rejected():
    # root incomplete / 未知 canonical 不产 leaf → structural fail → rejected。
    payload = _single_payload("foo")
    lines = _single_lines()
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    root = ir.units[0]
    spans = {s.span_id: s for s in run.resolved_spans}
    snap = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
    d = _decision(root, ir, snap, run)
    assert root.semantic_status == "incomplete"
    assert d["decision"] == "rejected"
    assert d["layers"]["structural"]["status"] == "fail"


# ---------------------------------------------------------------- composite
def _composite_lines():
    return _mk("材料开始", "材料中间内容段落", "材料结束",
               "1. 第一问", "A. 甲", "B. 乙", "C. 丙",
               "2. 第二问", "A. 甲", "B. 乙", "C. 丙",
               "【答案】", "1. A", "2. B")


def _composite_payload(sub2_type="single_choice"):
    return {"semantic_units": [
        {"unit_id": "U1-1", "unit_type": "composite_unit",
         "original_question_type": "single_choice",
         "shared_components": {"material": {
             "start_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                              "text": "材料开始"},
             "end_marker": {"kind": "instruction_marker", "granularity": "multi_line_pair",
                            "text": "材料结束"}}},
         "sub_questions": [
             {"unit_id": "Q1", "question_label": "1", "original_question_type": "single_choice",
              "content": {"stem": {"question_label": "1"},
                          "options": [{"label": l} for l in "ABC"],
                          "answer": {"answer_zone": "answer_table", "question_number": "1"}}},
             {"unit_id": "Q2", "question_label": "2",
              "original_question_type": sub2_type,
              "content": {"stem": {"question_label": "2"},
                          "options": [{"label": l} for l in "ABC"],
                          "answer": {"answer_zone": "answer_table", "question_number": "2"}}}]}]}


def test_composite_all_sub_ready_auto():
    root, ir, snap, run = _pipeline(_composite_lines(), _composite_payload(), "U1-1")
    assert len(snap.materials) == 1 and len(snap.leaves) == 2
    d = _decision(root, ir, snap, run)
    assert d["decision"] == "auto_approve"
    assert d["layers"]["semantic"]["status"] == "pass"


def test_composite_one_sub_not_strict_auto_pending():
    # composite 原子性（20 §8.5）：一子题 grammar None → 整个 composite 不自动。
    lines = _mk("材料开始", "材料中间内容段落", "材料结束",
                "1. 第一问", "A. 甲", "B. 乙", "C. 丙",
                "2. 填空___", "A. 甲", "B. 乙", "C. 丙",
                "【答案】", "1. A", "2. 苹果")
    payload = _composite_payload(sub2_type="fill_in")
    root, ir, snap, run = _pipeline(lines, payload, "U1-1")
    assert any(l.canonical_question_type == "fill_in" for l in snap.leaves)
    assert _decision(root, ir, snap, run)["decision"] == "pending_review"


# ---------------------------------------------------------------- multi-unit independence
def test_two_standalone_units_decide_independently():
    lines = _mk("1. 第一题", "A. 甲", "B. 乙",
                "2. 第二题", "A. 丙", "B. 丁",
                "【答案】", "1. A", "2. 不确定")
    payload = {"semantic_units": [
        {"unit_id": "Q1", "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "1"}, "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_number": "1"}}},
        {"unit_id": "Q2", "original_question_type": "single_choice",
         "content": {"stem": {"question_label": "2"}, "options": [{"label": "A"}, {"label": "B"}],
                     "answer": {"answer_zone": "answer_table", "question_number": "2"}}},
    ]}
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    snap = Compiler({s.span_id: s for s in run.resolved_spans},
                    {l.line_ref: l for l in lines}).compile(ir)
    d1 = _decision(next(u for u in ir.units if u.unit_id == "Q1"), ir, snap, run)
    d2 = _decision(next(u for u in ir.units if u.unit_id == "Q2"), ir, snap, run)
    assert d1["decision"] == "auto_approve"
    assert d2["decision"] == "pending_review"
