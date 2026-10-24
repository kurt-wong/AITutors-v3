# -*- coding: utf-8 -*-
"""T2.10 回归：正文装配不得并入纯分页标记；material 不得吞并其他 unit 的材料。

真实卷证据（2018 北京春季会考英语，t2_7_package）：
- U26-40 material_lines=[93,138] 跨入 U21-25 听力表格 [97,115]
- U41-44 material 内嵌 `---` + ` 4 / 12`
- Q59 stem 窗 [401,405] 尾部挂着 `---` + ` 8 / 12`
"""
import pytest

from app.domains.compile.compiler import _slice_span
from app.domains.resolver.match_normalization import (
    is_page_marker_line,
    is_question_start,
    normalize_text,
)
from app.domains.source.subq_expand import _is_trailing_pad


class TestPageMarkerLinePredicate:
    @pytest.mark.parametrize("line", [
        "---",
        " --- ",
        " 6 / 12",
        "6 / 12",
        " 3 / 12",
        "第6页",
        "共12页",
    ])
    def test_page_markers_detected(self, line):
        assert is_page_marker_line(line), line

    @pytest.mark.parametrize("line", [
        "6 / 12 is the fraction",     # embedded in prose
        "得分 6 / 12",
        "21.Grady  22.61295",
        "49. What does the second paragraph mainly talk about?",
        "A. How metal detectors work.     B. Why magnetic waves change.",
        "Anna was a 9-year-old girl from a small village.",
        "12．2017年，我国科学家……",
        "Start Time: 5 February 2018",
        "0 The Fifth Symphony was composed by Gustav Mahler",
    ])
    def test_real_content_not_page_marker(self, line):
        assert not is_page_marker_line(line), line


class TestSliceSpanDropsPageMarkers:
    def test_multi_line_join_skips_page_markers(self):
        class _Span:
            evidence = ()
            granularity = "line"
            start_offset = None
            end_offset = None
            line_refs = ("P1L001", "P1L002", "P1L003", "P1L004", "P1L005")

        class _Line:
            def __init__(self, text):
                self.text = text

        line_by_ref = {
            "P1L001": _Line("Anna was a 9-year-old girl."),
            "P1L002": _Line("---"),
            "P1L003": _Line(" 3 / 12"),
            "P1L004": _Line("Once the bus came, she got in it  28  ."),
            "P1L005": _Line(""),
        }
        text = _slice_span(_Span(), line_by_ref)
        assert "---" not in text
        assert "3 / 12" not in text
        assert "Anna was a 9-year-old girl." in text
        assert "Once the bus came" in text

    def test_answer_text_untouched(self):
        class _Span:
            evidence = ()
            granularity = "line"
            start_offset = None
            end_offset = None
            line_refs = ("P1L001",)

        class _Line:
            text = "21.Grady  22.61295   23.white   24.March   25.airport"

        assert "Grady" in _slice_span(_Span(), {"P1L001": _Line()})


class TestTrailingPadTightensPageFooter:
    def test_page_footer_is_trailing_pad(self):
        assert _is_trailing_pad(" 8 / 12")
        assert _is_trailing_pad("8 / 12")
        assert _is_trailing_pad("---")
        assert _is_trailing_pad("")

    def test_real_content_not_trailing_pad(self):
        assert not _is_trailing_pad("59. What did the author do after he moved to Italy?")
        assert not _is_trailing_pad("C. The danger of metal detectors.")
        assert not _is_trailing_pad("Start Time: 5 February 2018")


class TestQ59StemWindowTightens:
    """Q59 stem 末尾的 `---` + `8 / 12` 必须被 trailing-pad 收紧掉。"""

    def test_sub59_stem_end_excludes_page_break(self):
        from app.domains.source.subq_expand import expand_composite_sub_questions

        lines = [
            "As a teenager, I hated P.E. lessons.",
            "57. Why did the author hate P.E. lessons when he was a teenager?（不多于7 个单词）",
            "58. What club did the author go to when he was at university?（不多于3 个单词）",
            "59. What did the author do after he moved to Italy?     （不多于7 个单词）",
            "",
            "---",
            "",
            " 8 / 12",
            "60. How did the author become a sporty person?  （不多于8 个单词）",
            "57. Because he was not good at sports. 58. Kung Fu Club.",
            "59. He started doing a combat sport again. 60. Because he found the sport that suited him.",
        ]
        # lines are 1-indexed in expand; questions window covers 2..9
        res = expand_composite_sub_questions(
            lines,
            question_numbers=[57, 58, 59, 60],
            questions_range=(2, 9),
            answer_range=(10, 10),
            original_question_type="reading_expression",
            has_declared_options=False,
        )
        by = {s.question_number: s for s in res.sub_questions}
        assert 59 in by
        s59 = by[59]
        # stem must stop before the page-break block
        body = "\n".join(lines[s59.stem_start - 1 : s59.stem_end])
        assert "---" not in body
        assert "8 / 12" not in body
        assert "moved to Italy" in body


class TestForeignMaterialExclusion:
    """U26-40 material 不得吞并 U21-25 听力表格。"""

    def test_binder_marks_foreign_material_exclude(self):
        import json
        from pathlib import Path

        from app.domains.source.manifest_annotation import bind_units_from_manifest

        pkg = Path(r"D:\Project\AITutor-X\e2e_run\lineage_t2\t2_7_package")
        man = json.loads((pkg / "paper.manifest.json").read_text(encoding="utf-8"))
        lines = (pkg / "paper.md").read_text(encoding="utf-8").splitlines()
        bound = bind_units_from_manifest(man, lines, source_content_sha256="x")
        u26 = next(b for b in bound if b.unit_id == "U26-40")
        # U21-25 material_lines=[97,115] overlaps U26-40 material [93,138]
        assert u26.material_exclude_ranges, "expected foreign exclude ranges"
        # the listening form window must be excluded
        assert any(a <= 97 and b >= 115 for a, b in u26.material_exclude_ranges), (
            u26.material_exclude_ranges
        )
        # material_shared must carry exclude_line_ranges for the resolver
        excl = u26.material_shared.get("exclude_line_ranges")
        assert excl, u26.material_shared.keys()
        assert any(a <= 97 and b >= 115 for a, b in (tuple(x) for x in excl))
