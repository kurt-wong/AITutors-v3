# -*- coding: utf-8 -*-
"""E2E-009R2: Chinese composite per-child answers + declared label ranges."""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.domains.source.subq_expand import (
    expand_composite_sub_questions,
    specs_to_payload_subs,
)

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000c")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1) for i, t in enumerate(texts)
    )


class TestChinesePerChildAnswers:
    def test_packed_inline_entries_yield_distinct_answers(self):
        lines = [
            "",  # 0
            "1. 下列正确的是",  # 1
            "A. 甲 B. 乙 C. 丙 D. 丁",
            "2. 下列错误的是",
            "A. 甲 B. 乙 C. 丙 D. 丁",
            "3. 说法有误的是",
            "A. 甲 B. 乙 C. 丙 D. 丁",
            "4. 全对的是",
            "A. 甲 B. 乙 C. 丙 D. 丁",
            "【答案】1.C 2.B 3.C 4.D",  # 9
        ]
        payload = {
            "semantic_units": [
                {
                    "unit_id": "Q1",
                    "unit_type": "standalone_unit",
                    "question_number": "1",
                    "content": {
                        "stem": {"role": "stem", "question_label": "1", "stem_lines": [2, 2]},
                        "options": [{"role": "option", "label": x, "question_label": "1"} for x in "ABCD"],
                        "answer": {
                            "role": "answer",
                            "question_label": "1",
                            "answer_zone": "answer_table",
                            "answer_lines": [10, 10],
                        },
                    },
                },
                {
                    "unit_id": "Q2",
                    "unit_type": "standalone_unit",
                    "question_number": "2",
                    "content": {
                        "stem": {"role": "stem", "question_label": "2", "stem_lines": [4, 4]},
                        "options": [{"role": "option", "label": x, "question_label": "2"} for x in "ABCD"],
                        "answer": {
                            "role": "answer",
                            "question_label": "2",
                            "answer_zone": "answer_table",
                            "answer_lines": [10, 10],
                        },
                    },
                },
            ]
        }
        views = _mk(*lines)
        run = SourceResolver(source_version_id=SVID, lines=views).resolve(payload)
        by = {s.span_id: s for s in run.resolved_spans}
        a1, a2 = by["sp-Q1.answer"], by["sp-Q2.answer"]
        # distinct offsets / hashes — not the same whole block
        assert a1.text_hash != a2.text_hash
        assert a1.start_offset != a2.start_offset
        assert a1.line_refs == a2.line_refs  # same source line, different entries
        # reconstructed slices
        raw = views[9].text
        t1 = raw[a1.start_offset:a1.end_offset]
        t2 = raw[a2.start_offset:a2.end_offset]
        assert t1.strip().startswith("1."), t1
        assert t2.strip().startswith("2."), t2
        assert "2." not in t1
        assert "1." not in t2

    def test_shared_block_not_copied_when_entry_missing(self):
        """A child whose qn has no unique entry keeps the unresolved path
        (pending), rather than inheriting another child's answer."""
        lines = [
            "",
            "1. 题干",
            "A. 甲 B. 乙 C. 丙 D. 丁",
            "【答案】1.C 2.B 3.C 4.D",  # no '99.'
        ]
        payload = {
            "semantic_units": [
                {
                    "unit_id": "Q99",
                    "unit_type": "standalone_unit",
                    "question_number": "99",
                    "content": {
                        "stem": {"role": "stem", "question_label": "99", "stem_lines": [2, 2]},
                        "options": [{"role": "option", "label": x, "question_label": "99"} for x in "ABCD"],
                        "answer": {
                            "role": "answer",
                            "question_label": "99",
                            "answer_zone": "answer_table",
                            "answer_lines": [4, 4],
                        },
                    },
                }
            ]
        }
        run = SourceResolver(source_version_id=SVID, lines=_mk(*lines)).resolve(payload)
        ans = next(s for s in run.resolved_spans if s.span_id == "sp-Q99.answer")
        # must NOT be a neat per-qn entry slice of another question's answer
        raw = lines[3]
        if ans.start_offset is not None:
            slice_ = raw[ans.start_offset:ans.end_offset]
            assert not slice_.strip().startswith("1.C")
            assert not slice_.strip().startswith("2.B")
        # evidence must not claim a qn entry extraction for 99
        ev = str(ans.evidence)
        assert "multi-line entry" not in ev
        assert "single-line entry" not in ev


class TestDeclaredLabelRanges:
    def test_ad_children_under_ae_parent_expand(self):
        lines = [""] * 20
        lines[2] = "10. 题干甲"
        lines[4] = "A. 甲 B. 乙 C. 丙 D. 丁"
        lines[6] = "11. 题干乙"
        lines[8] = "A. 甲 B. 乙 C. 丙 D. 丁"
        lines[18] = "10. A 11. D"
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[10, 11],
            questions_range=(3, 9),
            answer_range=(19, 19),
            original_question_type="reading",
            has_declared_options=True,
        )
        assert [s.question_number for s in r.sub_questions] == [10, 11]
        for s in r.sub_questions:
            assert s.option_labels == ("A", "B", "C", "D")
        subs = specs_to_payload_subs("U10-13", r.sub_questions, original_question_type="reading")
        # choice children are canonical single_choice for Gate
        assert all(s["original_question_type"] == "single_choice" for s in subs)

    def test_ah_matching_child_fails_explicitly(self):
        lines = [""] * 20
        lines[2] = "5. 匹配题"
        lines[4] = "A.① B.② C.③ D.④ E.⑤ F.⑥ G.⑦ H.⑧"
        lines[18] = "5. ①②③④"
        r = expand_composite_sub_questions(
            lines,
            question_numbers=[5],
            questions_range=(3, 5),
            answer_range=(19, 19),
            original_question_type="reading",
            has_declared_options=True,
        )
        assert r.sub_questions == []
        assert 5 in r.skipped
        assert "option boundary" in r.skipped[5] or "labels" in r.skipped[5]
