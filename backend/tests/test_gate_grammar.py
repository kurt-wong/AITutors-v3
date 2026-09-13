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


# --------------------------------------------------------------------------- #
# AnswerTokenContract（BUG-V3-044，用户裁决 2026-09-13）
#
# 白名单契约：剥除题号前缀后，答案文本必须完全落在允许形态内。
# 见 grammar.py 模块注释与 80_B2B5_CLOSURE.md §3。
# --------------------------------------------------------------------------- #

class TestAnswerTokenContractPositive:
    """正向：合法 token 形态必须仍可通过（不得因收紧而误伤）。"""

    @pytest.mark.parametrize("answer", [
        "A", "B", "C", "D",          # 裸字母
        "1. A", "3．C", "12. D",      # 剥题号前缀后为裸字母（20 §5.5 切片形态）
        "A、", "B、",                 # 裸字母 + 顿号
        "（A）", "(A)", "（C）", "(D)",  # 括号形态（全角/半角）
        "1. （B）", "2. (C)",         # 题号 + 括号
        "1. A  ",                     # 行尾空白
    ])
    def test_single_choice_accepted_forms(self, answer):
        assert verify("single_choice", answer, LABELS_ABCD) is True

    @pytest.mark.parametrize("answer", [
        "【答案】D", "【答案】B", "【答案】 A",     # 答案标记 + 字母
        "1. 【答案】D",                            # 题号 + 答案标记
        "（3分）D", "(3分)D", "（20分）B",           # 分值前缀 + 字母
        "1. （3分）D",
        "D。", "B.", "A．",                        # 字母 + 句号（全/半角）
        "1. D。",
    ])
    def test_single_choice_accepted_extended_forms(self, answer):
        """真实语料实测的三种合法形态（2026-09-13 用户裁决扩展）。"""
        assert verify("single_choice", answer, LABELS_ABCD) is True

    @pytest.mark.parametrize("answer", [
        "ABD", "1. ABD",
        "A、C", "1. C、A",
        "A C B", "1. A B",
        "AAB",                        # 重复容忍
        "1. A, C",
        "【答案】AB", "1. 【答案】ABD",   # 答案标记 + 多字母
        "（3分）AB",
    ])
    def test_multiple_choice_accepted_forms(self, answer):
        assert verify("multiple_choice", answer, LABELS_ABCD) is True


class TestAnswerTokenContractBoundaryAttacks:
    """边界攻击：任何非 token 正文必须判 None（→ pending_review，不得 auto）。"""

    @pytest.mark.parametrize("answer", [
        "【解答】A",
        "【考点】A",
        "【分析】本题考查正确使用成语的能力，能力层级为表达运用E。",
        "1. 【解答】A",
        "1. 【考点】本题考查词义辨析。【解答】A",
        "参见教材A册第三章",
        "见解析A页",
        "正确答案为A",
        "略A",
        "A页",
    ])
    def test_single_choice_rejects_explanation_prefix(self, answer):
        assert verify("single_choice", answer, LABELS_ABCD) is None

    @pytest.mark.parametrize("answer", [
        # 合法形态 + 额外正文（全串锚定必须拒）
        "【答案】D[\"莫问当年事\"中饱含作者的沉痛]",
        "（3分）D[\"莫问当年事\"中饱含作者的沉痛]",
        "（3分）D（A. 有误；B. 不准确）",
        "D。本句采用的是暗喻。",
        "【答案】D详见解析",
        "B. 本句采用的是暗喻，比喻自己与妻子的深情再无物能及。",
        # 混合括号（对抗性审查 A1 发现：开闭括号必须配对）
        "（A)", "(A）", "（3分)D", "(3分）D",
    ])
    def test_single_choice_rejects_legal_token_plus_extra_prose(self, answer):
        """扩展形态只接受全串恰好为该形态；任何尾巴一律 None。"""
        assert verify("single_choice", answer, LABELS_ABCD) is None

    @pytest.mark.parametrize("answer", ["A B", "AA", "A.B", "1. AB"])
    def test_single_choice_rejects_multi_letter_forms(self, answer):
        # 单选只允许恰好一个字母；多字母（含被分隔的）→ None
        assert verify("single_choice", answer, LABELS_ABCD) is None

    @pytest.mark.parametrize("answer", [
        "【解答】AB",
        "参见教材A、B册",
        "A和B",
        "1. 【考点】多选，答案AB",
    ])
    def test_multiple_choice_rejects_non_token_text(self, answer):
        assert verify("multiple_choice", answer, LABELS_ABCD) is None

    @pytest.mark.parametrize("answer", ["【解答】对", "【考点】正确", "答案是对"])
    def test_true_false_rejects_explanation_prefix(self, answer):
        # true_false 本就是白名单 token，确认同样不受污染
        assert verify("true_false", answer, ()) is None

    def test_single_choice_rejects_letter_outside_labels_after_contract(self):
        # 契约通过但字母不在 labels → None（原有语义保持）
        assert verify("single_choice", "E", LABELS_ABCD) is None
        assert verify("single_choice", "（E）", LABELS_ABCD) is None


class TestAnswerTokenTypeIsolation:
    """题型隔离：非 strict-auto 题型不受 AnswerTokenContract 影响（恒 None）。"""

    @pytest.mark.parametrize("ctype", [
        "short_answer", "reading", "essay", "fill_in", "cloze",
        "grammar_fill", "vocabulary_fill", "seven_to_five", "reading_expression",
    ])
    def test_non_strict_auto_types_unaffected(self, ctype):
        # 无论答案文本是干净 token 还是污染正文，非开放题型恒 None
        assert verify(ctype, "A", LABELS_ABCD) is None
        assert verify(ctype, "【解答】A", LABELS_ABCD) is None
        assert verify(ctype, "参见教材A册第三章", LABELS_ABCD) is None
