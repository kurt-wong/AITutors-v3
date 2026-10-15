# -*- coding: utf-8 -*-
"""E2E-009R1: header-less horizontal answer table (EN 2018 Shape B)."""
from __future__ import annotations

from app.domains.resolver.resolver import (
    decode_answer_table_cell,
    decode_answer_table_headerless_horizontal,
    decode_answer_table_vertical,
)

EN_TABLE = (
    "<table border=1><tr>"
    "<td>1</td><td>2</td><td>3</td>"
    "</tr><tr>"
    "<td>A</td><td>C</td><td>B</td>"
    "</tr><tr>"
    "<td>11</td><td>12</td><td>13</td>"
    "</tr><tr>"
    "<td>B</td><td>A</td><td>C</td>"
    "</tr></table>"
)


class TestHeaderlessHorizontalAnswerTable:
    def test_first_page_columns(self):
        assert decode_answer_table_headerless_horizontal(EN_TABLE, "1")[2] == "A"
        assert decode_answer_table_headerless_horizontal(EN_TABLE, "2")[2] == "C"
        assert decode_answer_table_headerless_horizontal(EN_TABLE, "3")[2] == "B"

    def test_second_page_columns(self):
        assert decode_answer_table_headerless_horizontal(EN_TABLE, "11")[2] == "B"
        assert decode_answer_table_headerless_horizontal(EN_TABLE, "13")[2] == "C"

    def test_missing_qn_returns_none(self):
        assert decode_answer_table_headerless_horizontal(EN_TABLE, "99") is None

    def test_does_not_steal_labeled_vertical_tables(self):
        vert = (
            "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
            "<tr><td>答案</td><td>A</td><td>C</td></tr></table>"
        )
        # labeled format still owned by existing decoders
        assert decode_answer_table_cell(vert, "1") is not None
        assert decode_answer_table_headerless_horizontal(vert, "1") is None

    def test_asymmetric_rows_fail_closed(self):
        bad = (
            "<table><tr><td>1</td><td>2</td><td>3</td></tr>"
            "<tr><td>A</td><td>C</td></tr></table>"
        )
        assert decode_answer_table_headerless_horizontal(bad, "1") is None

    def test_real_en_2018_shape(self):
        # first block A C B C B C B A A C — Q1=A Q2=C Q10=C
        raw = (
            "<table border=1 style='margin: auto; word-wrap: break-word;'>"
            + "".join(f"<td>{i}</td>" for i in range(1, 11))
            + "".join(f"<td>{a}</td>" for a in ["A", "C", "B", "C", "B", "C", "B", "A", "A", "C"])
            + "</table>"
        )
        assert decode_answer_table_headerless_horizontal(raw, "1")[2] == "A"
        assert decode_answer_table_headerless_horizontal(raw, "10")[2] == "C"
        # existing decoders must not claim this shape
        assert decode_answer_table_cell(raw, "1") is None
        assert decode_answer_table_vertical(raw, "1") is None
