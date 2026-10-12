# -*- coding: utf-8 -*-
"""P3-TD-01 — stem prefix correction: text AND source_span must both start at
the question number, not at the preceding anchor/range prefix.

P2-R lesson: text can be clean while span start is wrong (traceability drift).
This fix moves the start — assert both.
"""
import pytest

from app.domains.resolver.resolver import _find_question_entry_col

# Real source lines from geography paper
LINE_133 = (
    "北京市从 2017 年 12 月开始对洗车等高耗水行业征收水资源税。"
    "据此完成 16~17 题。16. 北京市水资源利用方面的主要问题是"
)
LINE_222 = (
    "2017年9月，中共中央国务院发布关于对《北京城市总体规划（2016年—2035年）》的批复，"
    "提出首都功能更加优化、深入推进京津冀协同发展等发展目标。"
    "读图7京津冀区域空间格局示意图，完成26－2926.优化首都功能应采取的措施是"
)


class TestFindQuestionEntryCol:
    """_find_question_entry_col must return the offset of the question number
    itself, not the regex match start (which includes leading anchor)."""

    def test_q16_col_points_to_question_number(self):
        col = _find_question_entry_col(LINE_133, "16")
        assert col is not None
        # Offset must be at '16', not at the preceding '。'
        assert LINE_133[col:].startswith("16."), f"got {LINE_133[col:col+10]!r}"

    def test_q26_col_points_to_question_number(self):
        col = _find_question_entry_col(LINE_222, "26")
        assert col is not None
        assert LINE_222[col:].startswith("26."), f"got {LINE_222[col:col+10]!r}"

    def test_q16_col_exact_offset(self):
        """Span start must be 47 for Q16 on line 133."""
        assert _find_question_entry_col(LINE_133, "16") == 47

    def test_q26_col_exact_offset(self):
        """Span start must be 98 for Q26 on line 222."""
        assert _find_question_entry_col(LINE_222, "26") == 98

    def test_q16_stem_text_clean(self):
        """Stem extracted from col must be clean (no leading 。)."""
        col = _find_question_entry_col(LINE_133, "16")
        stem = LINE_133[col:]
        assert not stem.startswith("。")
        assert stem == "16. 北京市水资源利用方面的主要问题是"

    def test_q26_stem_text_clean(self):
        """Stem extracted from col must be clean (no 26－29 prefix)."""
        col = _find_question_entry_col(LINE_222, "26")
        stem = LINE_222[col:]
        assert not stem.startswith("26－")
        assert stem == "26.优化首都功能应采取的措施是"

    def test_q17_unchanged(self):
        """Q17 on its own line (no anchor prefix) still returns 0."""
        line137 = "17\\. 北京市征收水资源税的主要目的是"
        col = _find_question_entry_col(line137, "17")
        assert col == 0

    def test_line_start_returns_zero(self):
        """Line-start question entries return 0."""
        col = _find_question_entry_col("18. 塑造图4所示地貌的主要外力作用是", "18")
        assert col == 0
