# -*- coding: utf-8 -*-
"""G1/G3 parser compatibility (Owner: deterministic format, no semantic broadening)."""
import pytest

from app.domains.gate.grammar import verify, _clean_answer, _SC_FORMS_RE

SC = "single_choice"
LABELS = ("A", "B", "C", "D")


class TestG1EscapedDotPrefix:
    @pytest.mark.parametrize("raw,expect", [
        ("1\\. C", "C"),
        ("7\\.C", "C"),
        ("1. C", "C"),
        ("12\\. A", "A"),
        ("1、B", "B"),
    ])
    def test_lead_qn_stripped(self, raw, expect):
        cleaned = _clean_answer(raw)
        assert cleaned == expect, f"{raw!r} -> {cleaned!r}"
        assert verify(SC, raw, LABELS) is True

    def test_no_overstrip(self):
        # 不是题号前缀的不得误剥
        assert _clean_answer("D") == "D"
        assert verify(SC, "D", LABELS) is True


class TestG3TrailingScore:
    @pytest.mark.parametrize("raw,expect", [
        ("D（2分）", "D"),
        ("D (2分)", "D"),
        ("D（2 分）", "D"),
        ("C（3分）", "C"),
    ])
    def test_trailing_score_accepted(self, raw, expect):
        assert verify(SC, raw, LABELS) is True, raw
        m = _SC_FORMS_RE.match(raw)
        assert m is not None

    def test_leading_score_still_works(self):
        assert verify(SC, "（2分）D", LABELS) is True
        assert verify(SC, "(2分)D", LABELS) is True

    def test_no_semantic_broadening(self):
        # 仍然拒绝任意尾巴 / 自然语言
        assert verify(SC, "D（2分）说明文字", LABELS) is not True
        assert verify(SC, "答案是D", LABELS) is not True
        assert verify(SC, "【分析】D", LABELS) is not True


class TestQ7DoubleDefect:
    def test_q7_g1_then_g3(self):
        """语文 Q7 `7\\.C（3分）`：G1 剥 `7\\.` → G3 剥尾缀 → C → True。"""
        raw = "7\\.C（3分）"
        cleaned1 = _clean_answer(raw)
        assert cleaned1 == "C（3分）", f"G1 should strip qn prefix, got {cleaned1!r}"
        # G3: form accepts letter+trailing score
        assert verify(SC, cleaned1, LABELS) is True
        # full path
        assert verify(SC, raw, LABELS) is True

    def test_q6_trailing_only(self):
        assert verify(SC, _clean_answer("6. D（2分）"), LABELS) is True


class TestNoRegression:
    @pytest.mark.parametrize("raw", [
        "A", "A、", "（A）", "(A)", "【答案】A", "（3分）A", "A。", "A.", "A．",
    ])
    def test_existing_forms_still_pass(self, raw):
        assert verify(SC, raw, LABELS) is True, raw

    def test_prose_still_rejected(self):
        assert verify(SC, "【考点】三角函数", LABELS) is not True
        assert verify(SC, "参见教材A册", LABELS) is not True
