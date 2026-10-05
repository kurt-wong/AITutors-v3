# -*- coding: utf-8 -*-
"""Question Identity Coverage — not-found ×7 evidence-driven recognition.

U16/U26: mid-line source entries (。N. / range-concat N－M N.)
U51-U55: Producer printed_number + questions_lines window (bug22_migration).
No global/local guessing; no ambiguous ×2 handling.
"""
import pytest

from app.domains.resolver.match_normalization import normalize_text
from app.domains.resolver.resolver import _line_has_question_entry
from app.domains.resolver.reference import extract_targets


# ═══════════════════════════════════════════════════════════════
# 行中入口识别（U16 / U26 真实形态）
# ═══════════════════════════════════════════════════════════════

class TestMidlineQuestionEntry:
    def test_u16_sentence_boundary_form(self):
        line = ("北京市从 2017 年 12 月开始对洗车等高耗水行业征收水资源税。"
                "据此完成 16~17 题。16. 北京市水资源利用方面的主要问题是")
        assert _line_has_question_entry(line, "16")
        assert not _line_has_question_entry(line, "17")  # 17 不在此行入口

    def test_u26_range_concat_form(self):
        line = ("2017年9月，中共中央国务院发布关于对《北京城市总体规划"
                "（2016年—2035年）》的批复…读图7“京津冀区域空间格局示意图”，"
                "完成26－2926.优化首都功能应采取的措施是")
        assert _line_has_question_entry(line, "26")
        assert not _line_has_question_entry(line, "29")  # 29 是区间尾，不是本行入口

    def test_plain_line_start_still_works(self):
        assert _line_has_question_entry("21. 题干", "21")
        assert _line_has_question_entry("21\\. 题干", "21")

    def test_no_false_positive_on_year(self):
        # 2016 / 2035 不得被当成题号 16 / 35
        line = "（2016年—2035年）批复。"
        assert not _line_has_question_entry(line, "16")
        assert not _line_has_question_entry(line, "35")

    def test_no_false_positive_on_range_without_entry(self):
        # 区间本身不产生题号入口
        line = "据此完成 16~17 题。"
        assert not _line_has_question_entry(line, "16")
        assert not _line_has_question_entry(line, "17")

    def test_126_not_match_26(self):
        assert not _line_has_question_entry("126. 题干", "26")
        assert _line_has_question_entry("126. 题干", "126")

    def test_answer_area_number_not_needed(self):
        # 答案区 "1. 本题共10分" 不在 question zone；此处只验证入口识别本身
        assert _line_has_question_entry("1. 本题共10分。每空1分。", "1")


# ═══════════════════════════════════════════════════════════════
# printed_number / questions_lines evidence transport
# ═══════════════════════════════════════════════════════════════

class TestPrintedNumberTransport:
    def test_printed_number_list_and_search_lines_reach_target(self):
        payload = {"semantic_units": [{
            "unit_id": "U-P2-1",
            "unit_type": "composite_unit",
            "question_number": "51",
            "original_question_type": "short_answer",
            "shared_components": {},
            "sub_questions": [{
                "unit_id": "U-P2-1.sub",
                "unit_type": "standalone_unit",
                "question_number": "51",
                "original_question_type": "short_answer",
                "content": {
                    "stem": {
                        "role": "stem",
                        "question_label": "51",
                        "question_label_printed": "1",
                        "question_search_lines": [456, 482],
                    },
                    "answer": {"role": "answer", "question_label": "51",
                               "answer_zone": "answer_table"},
                },
            }],
        }]}
        targets = extract_targets(payload)
        st = next(t for t in targets if t.kind == "question_label")
        assert st.question_number == "51"
        assert st.question_label_printed == "1"
        assert st.question_search_lines == (456, 482)

    def test_no_printed_no_search_lines(self):
        payload = {"semantic_units": [{
            "unit_id": "Q1", "unit_type": "standalone_unit",
            "question_number": "1", "original_question_type": "single_choice",
            "content": {
                "stem": {"role": "stem", "question_label": "1"},
                "answer": {"role": "answer", "question_label": "1",
                           "answer_zone": "answer_table"},
            },
        }]}
        st = next(t for t in extract_targets(payload) if t.kind == "question_label")
        assert st.question_label_printed is None
        assert st.question_search_lines is None
