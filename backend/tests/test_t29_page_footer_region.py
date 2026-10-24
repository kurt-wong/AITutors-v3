# -*- coding: utf-8 -*-
"""T2.9 回归：页脚 `N / M` 不得截断跨页选项窗（U49-52 sub49 C/D）。

真实卷证据（2018 北京春季会考英语，t2_7_package/paper.md）：
  L308  49. What does the second paragraph mainly talk about?
  L309  A. How metal detectors work.     B. Why magnetic waves change.
  L310  (blank)
  L311  ---
  L312  (blank)
  L313   6 / 12          ← PDF 页脚，不得判为题号 6
  L314  C. The danger of metal detectors.   D. The sounds of a metal detector.
  L315  50. What were the first metal detectors used for?

修复前：is_question_start('6 / 12')=='6'，_region_end 在 L313 截断，
        sub49 的 C/D（L314）落入 region_upper 之外 → option unresolved →
        composite incomplete → U49-52 整体不入库。
"""
import pytest

from app.domains.resolver.match_normalization import (
    is_question_start,
    normalize_text,
)


class TestPageFooterNotQuestionStart:
    @pytest.mark.parametrize("line", [
        " 6 / 12",
        "6 / 12",
        "6 / 12 ",
        " 1 / 12",
        "12 / 48",
        " 3 / 12",
    ])
    def test_page_footer_rejected(self, line):
        assert is_question_start(normalize_text(line)) is None, line

    @pytest.mark.parametrize("line,qn", [
        ("21", "21"),
        ("25", "25"),
        ("49. What does the second paragraph mainly talk about?", "49"),
        ("50. What were the first metal detectors used for?", "50"),
        ("6. 小题题干", "6"),
        ("12．2017年，我国科学家……", "12"),
    ])
    def test_real_question_entries_still_match(self, line, qn):
        assert is_question_start(normalize_text(line)) == qn, line


class TestU49OptionRegionNotCutByPageFooter:
    """端到端护栏：页脚不得把 sub49 的选项窗截断在 C/D 之前。"""

    def test_sub49_cd_options_resolve(self):
        from app.domains.resolver.resolver import SourceLineView, SourceResolver

        lines_raw = [
            "Metal detectors help them find these things.",
            "49. What does the second paragraph mainly talk about?",
            "A. How metal detectors work.     B. Why magnetic waves change.",
            "",
            "---",
            "",
            " 6 / 12",
            "C. The danger of metal detectors.   D. The sounds of a metal detector.",
            "50. What were the first metal detectors used for?",
            "A. Removing bombs.      B. Finding needles in the clothes.",
            "C. Looking for minerals.    D. Searching for dangerous things.",
            "# 参考答案",
            "49.A 50.C",
        ]
        lines = tuple(
            SourceLineView(
                line_ref=f"P1L{i:03d}", text=t, seq=i, page_no=1, line_no_in_page=i
            )
            for i, t in enumerate(lines_raw, start=1)
        )
        payload = {
            "semantic_units": [
                {
                    "unit_id": "U49-52",
                    "unit_type": "composite_unit",
                    "question_number_range": "49-52",
                    "original_question_type": "reading",
                    "shared_components": {
                        "material": {
                            "role": "material",
                            "evidence_lines": [1, 1],
                        }
                    },
                    "sub_questions": [
                        {
                            "unit_id": "U49-52.sub49",
                            "unit_type": "standalone_unit",
                            "question_number": "49",
                            "original_question_type": "single_choice",
                            "content": {
                                "stem": {
                                    "role": "stem",
                                    "question_label": "49",
                                    "question_search_lines": [2, 8],
                                    "stem_lines": [2, 8],
                                },
                                "options": [
                                    {"role": "option", "label": "A", "question_label": "49"},
                                    {"role": "option", "label": "B", "question_label": "49"},
                                    {"role": "option", "label": "C", "question_label": "49"},
                                    {"role": "option", "label": "D", "question_label": "49"},
                                ],
                                "options_range": [2, 8],
                                "answer": {
                                    "role": "answer",
                                    "question_label": "49",
                                    "answer_zone": "answer_table",
                                    "answer_lines": [13, 13],
                                },
                            },
                            "depends_on": [
                                {"type": "material_dependency", "target": "material"}
                            ],
                        },
                    ],
                }
            ]
        }
        resolved = SourceResolver(
            source_version_id="00000000-0000-0000-0000-000000000009",
            lines=lines,
            figures=(),
        ).resolve(payload)
        by_id = {s.span_id: s for s in resolved.resolved_spans}
        for lab in "ABCD":
            sid = f"sp-U49-52.sub49.option.{lab}"
            assert sid in by_id, f"option {lab} unresolved: {sorted(by_id)}"
            assert by_id[sid].span_id == sid
        # C/D must sit on the post-footer line (seq 8), not be dropped
        c_span = by_id["sp-U49-52.sub49.option.C"]
        d_span = by_id["sp-U49-52.sub49.option.D"]
        assert "P1L008" in c_span.line_refs, c_span.line_refs
        assert "P1L008" in d_span.line_refs, d_span.line_refs
