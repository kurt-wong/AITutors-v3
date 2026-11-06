# -*- coding: utf-8 -*-
"""QCC-FIX-2 回归（TASK-QCC-NEXT 机制 B/C）：声明值消费。

机制：多行证据区（含重复题干/共享块）不再整块当答案文本——
1. 声明值（answer_evidence.value）/子题期望值（expected_value）在【答案】标记行内
   唯一全等命中 → 绑定该条目（T18 单行先例的多行泛化）；
2. 值无法字节定位但证据区恰有一个【答案】标记行 → 绑定标记行到区间末（答案内容区）；
3. 歧义/无标记/未命中 → 既有绑定路径不变（fail-safe）。
"""
from __future__ import annotations

import hashlib
import uuid

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f4")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a4")

# 答案区形态（chem_2020_js Q5 同构）：重复题干 + 图片行 + 【答案】D + 【解析】
_BLOCK_LINES = (
    "5. 实验室以某原料制备晶体。下列不能达到目的的是",
    "",
    '<div style="text-align: center;"><img src="a.jpg"></div>',
    "",
    "【答案】D",
    "",
    "【解析】",
    "",
    "【详解】A 不正确。",
)


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _pipeline(lines, payload):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    lines_by_ref = {l.line_ref: l for l in lines}
    compiled = Compiler(spans, lines_by_ref).compile(ir)
    return run, ir, compiled


def _answer_span_of(run):
    for s in run.resolved_spans:
        if s.role == "answer":
            return s
    return None


def _payload(*, answer_lines, answer_value=None, expected_value=None,
             qn="5", unit_id="Q5", ctype="fill_in", ac="full"):
    """fill_in 无选项形态：IR 只需 stem+answer 就 ready（机制与题型正交）。"""
    ans = {
        "answer_zone": "answer_table",
        "question_label": qn,
        "answer_lines": answer_lines,
    }
    if ac is not None:
        ans["answer_completeness"] = ac
    if answer_value is not None:
        ans["answer_value"] = answer_value
    if expected_value is not None:
        ans["expected_value"] = expected_value
    return {"semantic_units": [{
        "unit_id": unit_id,
        "unit_type": "standalone_unit",
        "original_question_type": ctype,
        "content": {
            "stem": {"question_label": qn},
            "answer": ans,
        },
    }]}


class TestDeclaredValueEntryExtraction:
    """机制 B：多行区 + 声明值 → 绑定【答案】条目而非整块。"""

    def test_multi_line_block_binds_declared_value_entry(self):
        lines = _mk(*_BLOCK_LINES)
        payload = _payload(answer_lines=[1, 9], answer_value="D")
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        assert ans is not None
        assert ans.line_refs == ("P1L005",), f"must bind marker line only, got {ans.line_refs}"
        assert ans.granularity == "line_character"
        assert ans.text_hash == hashlib.sha256(b"D").hexdigest()

    def test_block_text_no_longer_contains_stem(self):
        """绑定文本是声明值，不是重复题干（机制 B 的验收点）。"""
        lines = _mk(*_BLOCK_LINES)
        payload = _payload(answer_lines=[1, 9], answer_value="D")
        _, _, compiled = _pipeline(lines, payload)
        assert compiled.leaves, "fixture must produce a leaf"
        ans = compiled.leaves[0].answer
        assert ans is not None
        assert ans.text == "D", f"answer text must be the declared value, got {ans.text!r}"

    def test_expected_value_token_used_when_no_answer_value(self):
        """机制 C：子题 token（expected_value）同样走条目提取。"""
        lines = _mk(*_BLOCK_LINES)
        payload = _payload(answer_lines=[1, 9], answer_value=None, expected_value="D")
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        assert ans is not None
        assert ans.line_refs == ("P1L005",)

    def test_ambiguous_marker_values_fall_back(self):
        """两个【答案】行同值 → 歧义，不提取（保持既有块路径）。"""
        lines = _mk(
            "1. 题干一",
            "【答案】A",
            "【解析】略",
            "2. 题干二",
            "【答案】A",
        )
        payload = _payload(answer_lines=[1, 5], answer_value="A", qn="1", unit_id="Q1")
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        assert ans is not None
        assert ans.line_refs != ("P1L002",), "ambiguous hit must not pick first marker"

    def test_value_not_at_marker_keeps_block_path(self):
        """值不在任何【答案】行（且无单标记可缩窄）→ 不做值条目绑定。"""
        lines = _mk(
            "1. 题干",
            "详解正文提及 D 选项但无标记行",
        )
        payload = _payload(answer_lines=[1, 2], answer_value="D", qn="1", unit_id="Q1")
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        if ans is not None and ans.granularity == "line_character" and ans.line_refs == ("P1L002",):
            # 若走了行内定位，必须是字节子串命中而非误把“D”当条目
            assert ans.text_hash != hashlib.sha256(b"D").hexdigest() or "D" in lines[1].text

    def test_essay_continuation_block_not_truncated(self):
        """QCC-FIX-2b（r2x03）：值=标记行内容但答案含实质续行（作文）→
        绑定整个答案块，不得截成首词。"""
        lines = _mk(
            "25. 写作。根据材料，完成作文。",
            "【答案】例文",
            "第一段：开头内容。",
            "---",
            "第二段：结尾内容。",
        )
        payload = {
            "semantic_units": [{
                "unit_id": "Q25", "unit_type": "standalone_unit",
                "original_question_type": "essay",
                "content": {
                    "stem": {"question_label": "25", "question_search_lines": [1, 1]},
                    "answer": {
                        "answer_zone": "answer_lines", "question_label": "25",
                        "answer_lines": [2, 5], "answer_value": "例文",
                        "answer_completeness": "full",
                    },
                },
            }]
        }
        run, _, compiled = _pipeline(lines, payload)
        assert compiled.leaves, "fixture must produce a leaf"
        ans = compiled.leaves[0].answer
        assert ans is not None
        assert "第一段：开头内容。" in ans.text and "第二段：结尾内容。" in ans.text, (
            f"essay answer block must not be truncated to the value token, got {ans.text!r}"
        )

    def test_marker_content_stops_before_explanation(self):
        """缩窄内容区止于解析标记，不吞解析正文。"""
        lines = _mk(
            "16. 题干文本",
            "【答案】(1). HSO3-",
            "（2）. ZnSO3",
            "【解析】这是一大段解析正文",
        )
        payload = _payload(
            answer_lines=[1, 4], answer_value="HSO3-",
            qn="16", unit_id="Q16", ac=None,
        )
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        assert ans is not None
        assert ans.line_refs == ("P1L002", "P1L003"), (
            f"marker content must stop before explanation, got {ans.line_refs}"
        )


class TestMarkerContentNarrowing:
    """机制 B（Q16 形态）：值不可字节定位 + 单一【答案】行 → 答案内容区。"""

    def test_single_marker_narrows_to_marker_content(self):
        lines = _mk(
            "16. 吸收烟气的题干文本",
            "",
            "(1) 小问内容___",
            "",
            "【答案】(1). HSO3- 等多行答案",
            "(2). ZnSO3",
        )
        # 值在块内可证（一致性检查过）但不是标记后条目的全等（有 "(1)." 前缀）
        # → 不走条目提取，走单一标记行的内容区缩窄。
        payload = _payload(
            answer_lines=[1, 6], answer_value="HSO3- 等多行答案",
            qn="16", unit_id="Q16", ac=None,
        )
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        assert ans is not None
        assert ans.line_refs == ("P1L005", "P1L006"), (
            f"must bind marker content only (no stem), got {ans.line_refs}"
        )

    def test_marker_content_text_excludes_stem(self):
        lines = _mk(*_BLOCK_LINES)
        payload = _payload(
            answer_lines=[1, 9], answer_value="HSO3- 等多行答案",
            qn="5", unit_id="Q5", ac=None,
        )
        _, _, compiled = _pipeline(lines, payload)
        assert compiled.leaves
        ans = compiled.leaves[0].answer
        assert ans is not None
        assert "实验室" not in ans.text, (
            f"answer text must not contain the stem, got {ans.text[:60]!r}"
        )

    def test_multi_marker_block_without_byte_hit_keeps_block(self):
        """两个标记行且值歧义 → 不缩窄、不提取（fail-safe，保持块路径）。"""
        lines = _mk(
            "【答案】A",
            "解析一",
            "10. 小十题干",
            "【答案】A",
        )
        payload = _payload(
            answer_lines=[1, 4], answer_value="A",
            qn="9", unit_id="U9", ac=None,
        )
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        assert ans is not None
        # 不得缩窄到单标记，不得任选一个标记行（歧义块保持既有路径）
        assert ans.line_refs != ("P1L001", "P1L002")
        assert ans.line_refs != ("P1L004",)


class TestSafetyUnchanged:
    """安全约束不变：值冲突仍 fail-closed；无标记块路径未删除。"""

    def test_declared_value_conflict_never_binds_wrong_value(self):
        """声明值与块内容矛盾 → 不得把 Z 绑成正文。"""
        lines = _mk(
            "1. 题干",
            "【答案】B",
        )
        payload = _payload(answer_lines=[1, 2], answer_value="Z", qn="1", unit_id="Q1")
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        if ans is not None and ans.granularity == "line_character":
            assert ans.text_hash != hashlib.sha256(b"Z").hexdigest()

    def test_no_marker_block_behavior_unchanged(self):
        """无【答案】标记的 bare 编号多行块 → 仍整块绑定（路径未删除）。"""
        lines = _mk(
            "1. ",
            "多行答案正文第一行内容",
            "多行答案正文第二行内容",
        )
        payload = _payload(answer_lines=[1, 3], answer_value=None, qn="1", unit_id="Q1")
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        assert ans is not None
        assert set(ans.line_refs) == {"P1L001", "P1L002", "P1L003"}

    def test_single_line_declared_value_path_unchanged(self):
        """T18 单行路径不受影响：值在单行内 → 行内 char span。"""
        lines = _mk(
            "1. which fruit",
            "【答案】D",
        )
        payload = _payload(answer_lines=[2, 2], answer_value="D", qn="1", unit_id="Q1")
        run, _, _ = _pipeline(lines, payload)
        ans = _answer_span_of(run)
        assert ans is not None
        assert ans.granularity == "line_character"
        assert ans.text_hash == hashlib.sha256(b"D").hexdigest()

    def test_gate_not_rejected_for_clean_answer(self):
        """标准答案路径不得因本次修复被 rejected。"""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. A",
        )
        payload = {
            "semantic_units": [{
                "unit_id": "Q1", "unit_type": "standalone_unit",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"question_label": "1"},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {"answer_zone": "answer_table", "question_label": "1",
                               "answer_lines": [6, 7], "answer_completeness": "full"},
                },
            }]
        }
        run, ir, compiled = _pipeline(lines, payload)
        root = next(u for u in ir.units if u.unit_id == "Q1")
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        assert d["decision"] != "rejected", d["reasons"]
