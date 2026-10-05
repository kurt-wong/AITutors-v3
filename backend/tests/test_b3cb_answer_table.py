# -*- coding: utf-8 -*-
"""B3c-B structured answer table + U44-46 option separator coverage."""
import uuid

from app.domains.resolver.resolver import (
    SourceResolver,
    decode_answer_table_cell,
)
from app.domains.resolver.span import SourceLineView


def _mk_lines(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


# Real geography-style answer table (row-major td sequence)
TABLE = (
    "<table border=1><tr><td>题号</td><td>1</td><td>2</td><td>3</td></tr>"
    "<tr><td>答案</td><td>B</td><td>D</td><td>A</td></tr></table>"
)

TABLE_PAGED = (
    "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
    "<tr><td>答案</td><td>C</td><td>D</td></tr>"
    "<tr><td>题号</td><td>11</td><td>12</td></tr>"
    "<tr><td>答案</td><td>A</td><td>B</td></tr></table>"
)

TABLE_NO_ANS_ROW = (
    "<table><tr><td>题号</td><td>1</td><td>2</td></tr></table>"
)


class TestDecodeAnswerTable:
    def test_basic_same_column(self):
        r = decode_answer_table_cell(TABLE, "2")
        assert r is not None
        assert r[2] == "D"
        # offsets slice back to the cell text
        assert TABLE[r[0]:r[1]] == "D"

    def test_paged_table(self):
        assert decode_answer_table_cell(TABLE_PAGED, "11")[2] == "A"
        assert decode_answer_table_cell(TABLE_PAGED, "1")[2] == "C"

    def test_missing_qn(self):
        assert decode_answer_table_cell(TABLE, "99") is None

    def test_missing_answer_row(self):
        assert decode_answer_table_cell(TABLE_NO_ANS_ROW, "1") is None

    def test_not_a_table(self):
        assert decode_answer_table_cell("27. 【答案】C", "27") is None

    def test_empty_cell(self):
        t = (
            "<table><tr><td>题号</td><td>1</td><td>2</td></tr>"
            "<tr><td>答案</td><td></td><td>A</td></tr></table>"
        )
        assert decode_answer_table_cell(t, "1") is None

    def test_duplicate_qn_column_rejected(self):
        t = (
            "<table><tr><td>题号</td><td>1</td><td>1</td></tr>"
            "<tr><td>答案</td><td>A</td><td>B</td></tr></table>"
        )
        assert decode_answer_table_cell(t, "1") is None

    def test_scoring_table_variant_not_decoded_without_answer_row(self):
        # 物理评分表变体：题号/说明/分数，无「答案」行 → 必须 None
        t = (
            "<table><tr><td>题号</td><td>21</td><td>22</td></tr>"
            "<tr><td>分数</td><td>2</td><td>3</td></tr></table>"
        )
        assert decode_answer_table_cell(t, "21") is None


class TestAnswerSpanUsesTableDecode:
    def test_single_line_table_becomes_char_span(self):
        payload = {
            "semantic_units": [{
                "unit_id": "Q1",
                "unit_type": "standalone_unit",
                "question_number": "1",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"role": "stem", "question_label": "1"},
                    "answer": {
                        "role": "answer", "question_label": "1",
                        "answer_zone": "answer_table",
                        "answer_lines": [1, 1],
                    },
                },
            }]
        }
        lines = _mk_lines(TABLE)
        run = SourceResolver(source_version_id=uuid.uuid4(), lines=lines).resolve(payload)
        ans = next(s for s in run.resolved_spans if s.role == "answer")
        assert ans.granularity == "line_character"
        assert TABLE[ans.start_offset:ans.end_offset] == "B"
