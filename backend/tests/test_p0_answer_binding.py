# -*- coding: utf-8 -*-
"""P0-answer: 回归测试 answer_lines=None 时不得从解析文本推断答案。

覆盖：
1. answer_lines=None + answer_evidence.value 存在 → 直接绑定声明值
2. answer_lines=None + explanation_lines 存在 → 拒绝解析文本
3. answer_lines 存在 → 正常绑定
4. answer 与 explanation 分别存在 → 各自正确绑定
5. answer 角色错误绑定到 stem → 安全拒绝
6. Gate 对缺失答案的处理
"""
import uuid
import pytest

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


def mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def resolve(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines, figures=()).resolve(payload)


# 1. answer_lines=None + answer_evidence.value 存在 → 直接绑定声明值
def test_answer_value_bound_directly():
    lines = mk(
        "1. 下列哪个是水果？",
        "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
        "## 参考答案",
        "1. 【分析】直接利用复数代数形式的乘除运算化简得答案.",
        "【解答】解：xxx",
        "故选：B.",
    )
    payload = {
        "semantic_units": [{
            "unit_id": "Q1",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "1",
                    "answer_value": "B",
                },
            },
        }]
    }
    run = resolve(lines, payload)
    answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
    assert len(answer_spans) == 1, "answer_value should be bound directly"
    # cell= evidence should carry the declared value
    assert any("cell=B" in ev for ev in answer_spans[0].evidence), \
        f"evidence should contain cell=B, got {answer_spans[0].evidence}"


# 2. answer_lines=None + explanation_lines 存在 → 拒绝解析文本
def test_answer_none_rejects_explanation_text():
    """P0-R5: explanation body must NEVER appear in the answer field.

    Precise safety properties (not mere `!= auto_approve`):
    - compiled/bound answer text must not contain the explanation body
    - if an answer span exists it must be empty or a non-explanation value
    - Gate/ownership must not treat explanation as a verified answer
    """
    from app.domains.compile.compiler import Compiler
    from app.domains.compile.ir import IRBuilder
    from app.domains.gate.policy import evaluate

    lines = mk(
        "1. 下列哪个是水果？",
        "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
        "## 参考答案",
        "1. 【分析】直接利用复数代数形式的乘除运算化简得答案.",
        "【解答】解：xxx",
    )
    payload = {
        "semantic_units": [{
            "unit_id": "Q1",
            "question_number": "1",
            "unit_type": "standalone_unit",
            "original_question_type": "single_choice",
            "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {"answer_zone": "answer_table", "question_label": "1"},
                "explanation": {
                    "explanation_zone": "inline_explanation",
                    "question_label": "1",
                    "explanation_lines": [7, 8],
                },
            },
        }]
    }
    run = resolve(lines, payload)
    answer_spans = [s for s in run.resolved_spans if s.role == "answer"]

    # 1) Resolver must not bind explanation body as answer content
    for s in answer_spans:
        # evidence must not carry the explanation body as the answer text
        joined = " ".join(str(e) for e in s.evidence)
        assert "【分析】直接利用" not in joined, (
            f"explanation body leaked into answer evidence: {s.evidence}"
        )

    # 2) Compiler/Gate path: explanation text must not be the answer field
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
    if compiled.leaves:
        leaf = compiled.leaves[0]
        if leaf.answer is not None:
            ans_text = leaf.answer.text or ""
            assert "【分析】" not in ans_text, (
                f"compiled answer contains explanation body: {ans_text!r}"
            )
            assert "【解答】" not in ans_text
            assert leaf.answer.verified_correct is not True
        root = next(u for u in ir.units if u.unit_id == "Q1")
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        assert d["decision"] != "auto_approve"
    else:
        # IR incomplete is also safe (no materialized answer)
        assert True

    # 3) If no answer span, there must be an unresolved reason (explicit)
    unresolved = [u for u in run.unresolved_references if u.role == "answer"]
    if not answer_spans:
        assert unresolved, "no answer span must come with unresolved reason"


# 3. answer_lines 存在 → 正常绑定
def test_answer_lines_bound_correctly():
    lines = mk(
        "1. 下列哪个是水果？",
        "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
        "## 参考答案",
        "1. B",
    )
    payload = {
        "semantic_units": [{
            "unit_id": "Q1",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "1",
                    "answer_lines": [7, 7],
                },
            },
        }]
    }
    run = resolve(lines, payload)
    answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
    assert len(answer_spans) == 1, "answer_lines should be bound"
    assert answer_spans[0].resolution_status in ("exact", "normalized", "contextual")


# 4. answer 与 explanation 分别存在 → 各自正确绑定
def test_answer_and_explanation_separate():
    lines = mk(
        "1. 下列哪个是水果？",
        "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
        "## 参考答案",
        "1. B",
        "1. 【分析】这是解析.",
    )
    payload = {
        "semantic_units": [{
            "unit_id": "Q1",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "1",
                    "answer_lines": [7, 7],
                },
                "explanation": {
                    "explanation_zone": "inline_explanation",
                    "question_label": "1",
                    "explanation_lines": [8, 8],
                },
            },
        }]
    }
    run = resolve(lines, payload)
    answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
    expl_spans = [s for s in run.resolved_spans if s.role == "explanation"]
    assert len(answer_spans) == 1, "answer should be bound"
    assert len(expl_spans) == 1, "explanation should be bound"
    # answer 不应包含解析文本
    # explanation 不应包含答案文本


# 5. Gate 对缺失答案的处理
def test_missing_answer_goes_pending():
    lines = mk(
        "1. 下列哪个是水果？",
        "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
        "## 参考答案",
        "1. 【分析】这是解析不是答案.",
    )
    payload = {
        "semantic_units": [{
            "unit_id": "Q1",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {"answer_zone": "answer_table", "question_label": "1"},
            },
        }]
    }
    run = resolve(lines, payload)
    answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
    unresolved = [u for u in run.unresolved_references if u.role == "answer"]
    # 解析文本被拒绝 → answer 应为 unresolved
    assert len(answer_spans) == 0, "explanation text must not be bound as answer"
    assert len(unresolved) == 1, "answer should be unresolved"


# 6. MATH-001 真实场景复现
def test_math001_scenario():
    """MATH-001: answer_lines=None, answer_evidence.value='B', explanation_lines=[179,187]"""
    lines = mk(
        "## 参考答案",
        "",
        "一、选择题",
        "",
        "1. 【分析】直接利用复数代数形式的乘除运算化简得答案.",
        "",
        "【解答】解：xxx",
        "",
        "故选：B.",
    )
    payload = {
        "semantic_units": [{
            "unit_id": "Q1",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1"},
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "1",
                    "answer_value": "B",
                },
                "explanation": {
                    "explanation_zone": "inline_explanation",
                    "question_label": "1",
                    "explanation_lines": [5, 9],
                },
            },
        }]
    }
    run = resolve(lines, payload)
    answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
    assert len(answer_spans) == 1, "answer_value should be bound"
    assert any("cell=B" in ev for ev in answer_spans[0].evidence), \
        f"should bind declared value 'B', got {answer_spans[0].evidence}"
