# -*- coding: utf-8 -*-
"""P2 — vertical-format answer table extraction (题号|答案 column headers)."""
import pytest

from app.domains.resolver.resolver import (
    decode_answer_table_cell,
    decode_answer_table_vertical,
)


# ═══════════════════════════════════════════════════════════════
# Vertical format: 题号|答案 as column headers
# ═══════════════════════════════════════════════════════════════

TABLE_VERT_Q21 = (
    "<table><tr>"
    "<td>题号</td><td>答案</td><td>分数</td>"
    "</tr><tr>"
    "<td rowspan='2'>21</td><td>正</td><td>2分</td>"
    "</tr><tr>"
    "<td>变小</td><td>2分</td>"
    "</tr><tr>"
    "<td rowspan='2'>22</td><td>$ \\frac{U}{I} $</td><td>2分</td>"
    "</tr><tr>"
    "<td>$ \\frac{US}{IL} $</td><td>2分</td>"
    "</tr><tr>"
    "<td rowspan='2'>23</td><td>0.72</td><td>2分</td>"
    "</tr><tr>"
    "<td>打点计时器打下A点时小车的速度</td><td>2分</td>"
    "</tr></table>"
)

TABLE_VERT_Q24 = (
    "<table><tr>"
    "<td>题号</td><td>答案</td><td>分数</td><td>说明</td>"
    "</tr><tr>"
    "<td>24（5分）</td><td>解：（1）a=3.0</td><td>3分2分</td><td>按其它方法</td>"
    "</tr><tr>"
    "<td>25（5分）</td><td>解：（1）U=2.0</td><td>3分2分</td><td>同第24题</td>"
    "</tr><tr>"
    "<td>26（6分）</td><td>解：（1）书包从A处</td><td>2分</td><td>同第24题</td>"
    "</tr></table>"
)

TABLE_VERT_Q27 = (
    "<table><tr>"
    "<td></td><td>$ t=L/V=8.0s $</td><td>4分</td><td></td>"
    "</tr><tr>"
    "<td>27（6分）</td><td>解：（1）返回舱加速度</td><td></td><td></td>"
    "</tr><tr>"
    "<td>28（6分）</td><td>解：（1）每秒钟到达B板</td><td>2分2分</td><td></td>"
    "</tr></table>"
)


class TestVerticalFormat:
    def test_header_detection(self):
        """题号|答案 as column headers → vertical format detected."""
        r = decode_answer_table_vertical(TABLE_VERT_Q21, "21")
        assert r is not None

    def test_q21_simple_answer(self):
        r = decode_answer_table_vertical(TABLE_VERT_Q21, "21")
        assert r is not None
        start, end, val = r
        assert "正" in val

    def test_q21_rowspan_continuation(self):
        """Q21 rowspan=2 → answer includes '正' and '变小'."""
        r = decode_answer_table_vertical(TABLE_VERT_Q21, "21")
        assert r is not None
        _, _, val = r
        assert "正" in val
        assert "变小" in val

    def test_q22_rowspan(self):
        r = decode_answer_table_vertical(TABLE_VERT_Q21, "22")
        assert r is not None
        _, _, val = r
        assert "U/I" in val or "\\frac{U}{I}" in val
        assert "US/IL" in val or "\\frac{US}{IL}" in val

    def test_q23_rowspan(self):
        r = decode_answer_table_vertical(TABLE_VERT_Q21, "23")
        assert r is not None
        _, _, val = r
        assert "0.72" in val
        assert "打点计时器" in val

    def test_q24_with_suffix(self):
        """Q24 cell is '24（5分）' — suffix must still match."""
        r = decode_answer_table_vertical(TABLE_VERT_Q24, "24")
        assert r is not None
        _, _, val = r
        assert "a=3.0" in val

    def test_q25_with_suffix(self):
        r = decode_answer_table_vertical(TABLE_VERT_Q24, "25")
        assert r is not None
        _, _, val = r
        assert "U=2.0" in val

    def test_q26_with_suffix(self):
        r = decode_answer_table_vertical(TABLE_VERT_Q24, "26")
        assert r is not None
        _, _, val = r
        assert "书包从A处" in val

    def test_q27_continuation_row_skip(self):
        """First row is Q26 continuation (empty first cell) — Q27 still found."""
        r = decode_answer_table_vertical(TABLE_VERT_Q27, "27")
        assert r is not None
        _, _, val = r
        assert "返回舱加速度" in val

    def test_q28_last_row(self):
        r = decode_answer_table_vertical(TABLE_VERT_Q27, "28")
        assert r is not None
        _, _, val = r
        assert "每秒钟到达B板" in val

    def test_q26_not_in_q27_table(self):
        """Q26 continuation row has empty first cell — should NOT match qn=26."""
        r = decode_answer_table_vertical(TABLE_VERT_Q27, "26")
        # First row has empty first cell — no question number match
        assert r is None

    def test_missing_qn_returns_none(self):
        r = decode_answer_table_vertical(TABLE_VERT_Q21, "99")
        assert r is None

    def test_not_vertical_format_returns_none(self):
        """Horizontal format should return None (handled by decode_answer_table_cell)."""
        horiz = (
            "<table><tr>"
            "<td>题号</td><td>1</td><td>2</td>"
            "</tr><tr>"
            "<td>答案</td><td>A</td><td>B</td>"
            "</tr></table>"
        )
        assert decode_answer_table_vertical(horiz, "1") is None


class TestHorizontalStillWorks:
    """decode_answer_table_cell (horizontal) must remain unchanged."""

    def test_horizontal_format_unchanged(self):
        horiz = (
            "<table><tr>"
            "<td>题号</td><td>1</td><td>2</td>"
            "</tr><tr>"
            "<td>答案</td><td>A</td><td>B</td>"
            "</tr></table>"
        )
        r = decode_answer_table_cell(horiz, "1")
        assert r is not None
        assert r[2] == "A"

    def test_horizontal_q2(self):
        horiz = (
            "<table><tr>"
            "<td>题号</td><td>1</td><td>2</td>"
            "</tr><tr>"
            "<td>答案</td><td>A</td><td>B</td>"
            "</tr></table>"
        )
        r = decode_answer_table_cell(horiz, "2")
        assert r is not None
        assert r[2] == "B"
