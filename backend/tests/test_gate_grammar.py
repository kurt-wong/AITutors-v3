"""Gate G — Allowed-Answer Grammar：三种开放题型 + golden 正/反例 + 边界（20 §8.4）。

grammar 是纯函数格式校验（必要不充分，20 §8.3）；True=通过、None=不开放/无法表达。
raw answer text 常带 E char-span 题号前缀（"1. A"）与行尾空格/标点，grammar 须剥除。
"""

import pytest

from app.domains.gate.grammar import verify

LABELS_ABCD = ("A", "B", "C", "D")


# ------------------------------------------------------------------ single_choice
def test_single_choice_pass_with_qn_prefix():
    assert verify("single_choice", "1. A", LABELS_ABCD) is True
    assert verify("single_choice", "3．C", LABELS_ABCD) is True


def test_single_choice_pass_without_qn_prefix():
    assert verify("single_choice", "B", LABELS_ABCD) is True


def test_single_choice_rejects_letter_outside_labels():
    # 选项 A-D，答案是 E → 无法确定性表达（不得 auto）
    assert verify("single_choice", "1. E", LABELS_ABCD) is None


def test_single_choice_rejects_multiple_letters():
    assert verify("single_choice", "1. AB", LABELS_ABCD) is None


def test_single_choice_rejects_no_letter():
    assert verify("single_choice", "1. 略", LABELS_ABCD) is None
    assert verify("single_choice", "1. 2分", LABELS_ABCD) is None


def test_single_choice_rejects_empty():
    assert verify("single_choice", "", LABELS_ABCD) is None
    assert verify("single_choice", "   ", LABELS_ABCD) is None


def test_single_choice_trailing_whitespace_ok():
    # E 同行多题切片止于下一 qn 前，含尾随空格
    assert verify("single_choice", "1. A  ", LABELS_ABCD) is True


# ------------------------------------------------------------------ multiple_choice
def test_multiple_choice_pass_tight_letters():
    assert verify("multiple_choice", "1. ABD", LABELS_ABCD) is True


def test_multiple_choice_pass_separated_and_reordered():
    assert verify("multiple_choice", "1. C、A", LABELS_ABCD) is True
    assert verify("multiple_choice", "1. A C B", LABELS_ABCD) is True


def test_multiple_choice_pass_duplicate_tolerated():
    assert verify("multiple_choice", "1. AAB", LABELS_ABCD) is True


def test_multiple_choice_rejects_letter_outside_labels():
    assert verify("multiple_choice", "1. AE", LABELS_ABCD) is None


def test_multiple_choice_rejects_no_letter():
    assert verify("multiple_choice", "1. 不确定", LABELS_ABCD) is None


# ------------------------------------------------------------------ true_false
@pytest.mark.parametrize(
    "answer",
    ["1. 对", "1. T", "1. t", "1. 正确", "1. 是", "1. √", "1. ✓",
     "1. 错", "1. F", "1. 错误", "1. 否", "1. ×", "1. ✗"],
)
def test_true_false_canonical_tokens_pass(answer):
    assert verify("true_false", answer, ()) is True


def test_true_false_trailing_noise_stripped():
    assert verify("true_false", "1. 对。", ()) is True
    assert verify("true_false", "1. T,", ()) is True


def test_true_false_ab_not_allowed():
    # 用户裁决：判断题答案区写 A/B → 不通过 grammar（pending_review），不补 A/B 映射
    assert verify("true_false", "1. A", ()) is None
    assert verify("true_false", "1. B", ()) is None


def test_true_false_unmappable_rejected_as_none():
    assert verify("true_false", "1. 不确定", ()) is None
    assert verify("true_false", "1. true", ()) is None  # DISPLAY 禁 true/false 作值
    assert verify("true_false", "", ()) is None


# ------------------------------------------------------------------ 不开放题型
@pytest.mark.parametrize("ctype", ["fill_in", "short_answer", "essay"])
def test_non_open_types_return_none(ctype):
    assert verify(ctype, "anything", ()) is None


def test_unknown_type_returns_none():
    assert verify("seven_to_five", "1. B", ()) is None
    assert verify("foo", "1. A", ()) is None


def test_strict_auto_types_frozen_domain_023():
    """BUG-V3-023 终裁：开放集冻结 = {single_choice, multiple_choice, true_false}；
    其余 9 型（fill_in/short_answer/essay/cloze/reading/grammar_fill/vocabulary_fill/
    seven_to_five/reading_expression）grammar=None → pending_review。"""
    from app.domains.compile import CANONICAL_TYPES
    from app.domains.gate import STRICT_AUTO_TYPES
    assert STRICT_AUTO_TYPES == frozenset(
        {"single_choice", "multiple_choice", "true_false"}
    )
    assert STRICT_AUTO_TYPES <= CANONICAL_TYPES
    for ctype in sorted(CANONICAL_TYPES - STRICT_AUTO_TYPES):
        assert verify(ctype, "1. A", LABELS_ABCD) is None
