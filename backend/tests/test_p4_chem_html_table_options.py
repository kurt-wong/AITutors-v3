# -*- coding: utf-8 -*-
"""P4 — Chemistry HTML-table option extraction regression.

Covers Q9/Q19/Q24/Q25 A-D (16 option assertions), source span + cell= evidence
binding, Q24 LaTeX fidelity, Q25 multi-column, and a hard assertion that no
option span may bind to page-footer / section-header lines (Rule A guard).

Truth is taken from the real preprocessing artifact (chem paper.md L51/145/199/204).
"""
import uuid

import pytest

from app.domains.compile.compiler import _slice_span
from app.domains.resolver.resolver import (
    SourceResolver,
    _html_table_option_cells,
    _PAGE_FOOTER_RE,
    _SECTION_HDR_RE,
)
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000a")

# ---- real source lines from chem paper.md (L51/145/199/204) ----
# Q9: horizontal layout, label+text in row0 cells, images in row1
Q9_TABLE = (
    "<table border=1 style='margin: auto; word-wrap: break-word;'>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>A. 青铜器皿</td>"
    "<td style='text-align: center; word-wrap: break-word;'>B. 陶瓷</td>"
    "<td style='text-align: center; word-wrap: break-word;'>C. 丝绸</td>"
    "<td style='text-align: center; word-wrap: break-word;'>D. 中草药</td></tr>"
    "<tr><td style='text-align: center; word-wrap: break-word;'><img src=\"x1.jpg\" /></td>"
    "<td style='text-align: center; word-wrap: break-word;'><img src=\"x2.jpg\" /></td>"
    "<td style='text-align: center; word-wrap: break-word;'><img src=\"x3.jpg\" /></td>"
    "<td style='text-align: center; word-wrap: break-word;'><img src=\"x4.jpg\" /></td></tr>"
    "</table>"
)

# Q19: column-oriented, bare A-D labels in header row
Q19_TABLE = (
    "<table border=1 style='margin: auto; word-wrap: break-word;'>"
    "<tr><td style='text-align: center; word-wrap: break-word;'></td>"
    "<td style='text-align: center; word-wrap: break-word;'>A</td>"
    "<td style='text-align: center; word-wrap: break-word;'>B</td>"
    "<td style='text-align: center; word-wrap: break-word;'>C</td>"
    "<td style='text-align: center; word-wrap: break-word;'>D</td></tr>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>t / °C</td>"
    "<td style='text-align: center; word-wrap: break-word;'>10</td>"
    "<td style='text-align: center; word-wrap: break-word;'>10</td>"
    "<td style='text-align: center; word-wrap: break-word;'>40</td>"
    "<td style='text-align: center; word-wrap: break-word;'>40</td></tr>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>c( $ H_{2}SO_{4} $) / (mol ·  $ L^{-1} $)</td>"
    "<td style='text-align: center; word-wrap: break-word;'>1</td>"
    "<td style='text-align: center; word-wrap: break-word;'>3</td>"
    "<td style='text-align: center; word-wrap: break-word;'>1</td>"
    "<td style='text-align: center; word-wrap: break-word;'>3</td></tr>"
    "</table>"
)

# Q24: horizontal, figure placeholders row0 + A-D text row1 (LaTeX in D)
Q24_TABLE = (
    "<table border=1 style='margin: auto; word-wrap: break-word;'>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>[ $ F_{4} $]</td>"
    "<td style='text-align: center; word-wrap: break-word;'>[ $ F_{3} $]</td>"
    "<td style='text-align: center; word-wrap: break-word;'>[ $ F_{5} $]</td>"
    "<td style='text-align: center; word-wrap: break-word;'>[ $ F_{2} $]</td></tr>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>A. 收集氯气</td>"
    "<td style='text-align: center; word-wrap: break-word;'>B. 除去水中泥沙</td>"
    "<td style='text-align: center; word-wrap: break-word;'>C. 分离乙醇和水</td>"
    "<td style='text-align: center; word-wrap: break-word;'>D. 配制100 mL 0.1 mol·L $ ^{-1} $ NaCl溶液</td></tr>"
    "</table>"
)

# Q25: row-oriented, col0=label, content spans col1+col2
Q25_TABLE = (
    "<table border=1 style='margin: auto; word-wrap: break-word;'>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>选项</td>"
    "<td style='text-align: center; word-wrap: break-word;'>实验操作及现象</td>"
    "<td style='text-align: center; word-wrap: break-word;'>推理或结论</td></tr>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>A</td>"
    "<td style='text-align: center; word-wrap: break-word;'>向KI-淀粉溶液中滴入氯水，溶液变成蓝色</td>"
    "<td style='text-align: center; word-wrap: break-word;'>$ I^{-} $的还原性强于 $ Cl^{-} $</td></tr>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>B</td>"
    "<td style='text-align: center; word-wrap: break-word;'>向某溶液中加入 $ BaCl_{2} $溶液，有白色沉淀生成</td>"
    "<td style='text-align: center; word-wrap: break-word;'>该溶液中一定含有 $ SO_{4}^{2-} $</td></tr>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>C</td>"
    "<td style='text-align: center; word-wrap: break-word;'>取少量 $ Na_{2}O_{2} $粉末放在脱脂棉上，再将1滴水滴到 $ Na_{2}O_{2} $上，脱脂棉燃烧</td>"
    "<td style='text-align: center; word-wrap: break-word;'>$ Na_{2}O_{2} $与水的反应是放热反应</td></tr>"
    "<tr><td style='text-align: center; word-wrap: break-word;'>D</td>"
    "<td style='text-align: center; word-wrap: break-word;'>向某溶液中加入NaOH溶液，生成的白色絮状沉淀迅速变成灰绿色，最后变成红褐色</td>"
    "<td style='text-align: center; word-wrap: break-word;'>该溶液中一定含有 $ Fe^{2+} $</td></tr>"
    "</table>"
)

# ---- expected clean option text (cell= evidence, label stripped) ----
Q9_EXPECTED = {
    "A": "青铜器皿", "B": "陶瓷", "C": "丝绸", "D": "中草药",
}
Q19_EXPECTED = {
    "A": "10 1", "B": "10 3", "C": "40 1", "D": "40 3",
}
Q24_EXPECTED = {
    "A": "收集氯气", "B": "除去水中泥沙", "C": "分离乙醇和水",
    "D": "配制100 mL 0.1 mol·L $ ^{-1} $ NaCl溶液",
}
Q25_EXPECTED = {
    "A": "向KI-淀粉溶液中滴入氯水，溶液变成蓝色 $ I^{-} $的还原性强于 $ Cl^{-} $",
    "B": "向某溶液中加入 $ BaCl_{2} $溶液，有白色沉淀生成 该溶液中一定含有 $ SO_{4}^{2-} $",
    "C": "取少量 $ Na_{2}O_{2} $粉末放在脱脂棉上，再将1滴水滴到 $ Na_{2}O_{2} $上，脱脂棉燃烧 $ Na_{2}O_{2} $与水的反应是放热反应",
    "D": "向某溶液中加入NaOH溶液，生成的白色絮状沉淀迅速变成灰绿色，最后变成红褐色 该溶液中一定含有 $ Fe^{2+} $",
}


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(qn: str):
    return {
        "semantic_units": [{
            "unit_id": f"Q{qn}",
            "unit_type": "standalone_unit",
            "question_number": qn,
            "content": {
                "stem": {"role": "stem", "question_label": qn},
                "options": [{"role": "option", "label": x} for x in "ABCD"],
                "answer": {
                    "role": "answer", "answer_zone": "inline_answer",
                    "question_label": qn,
                },
            },
        }]
    }


def _resolve_options(qn, *lines):
    views = _mk(*lines)
    run = SourceResolver(source_version_id=SVID, lines=views).resolve(_payload(qn))
    line_map = {v.line_ref: v for v in views}
    out = {}
    for s in run.resolved_spans:
        if s.role != "option":
            continue
        lab = s.span_id.rsplit(".", 1)[-1]
        out[lab] = (_slice_span(s, line_map), s)
    return out


# =====================================================================
# 1. HTML table cell extraction (16 option assertions)
# =====================================================================

class TestHtmlTableCellExtraction:
    """A-D extracted from each table layout with clean cell text."""

    def test_q9_horizontal_abcd(self):
        cells = _html_table_option_cells(Q9_TABLE)
        for lab, expected in Q9_EXPECTED.items():
            assert lab in cells, f"Q9.{lab} missing"
            _, _, clean = cells[lab]
            assert clean == expected, f"Q9.{lab}: {clean!r} != {expected!r}"

    def test_q19_column_oriented_abcd(self):
        cells = _html_table_option_cells(Q19_TABLE)
        for lab, expected in Q19_EXPECTED.items():
            assert lab in cells, f"Q19.{lab} missing"
            _, _, clean = cells[lab]
            assert clean == expected, f"Q19.{lab}: {clean!r} != {expected!r}"

    def test_q24_horizontal_latex_abcd(self):
        cells = _html_table_option_cells(Q24_TABLE)
        for lab, expected in Q24_EXPECTED.items():
            assert lab in cells, f"Q24.{lab} missing"
            _, _, clean = cells[lab]
            assert clean == expected, f"Q24.{lab}: {clean!r} != {expected!r}"

    def test_q25_row_oriented_multicol_abcd(self):
        cells = _html_table_option_cells(Q25_TABLE)
        for lab, expected in Q25_EXPECTED.items():
            assert lab in cells, f"Q25.{lab} missing"
            _, _, clean = cells[lab]
            assert clean == expected, f"Q25.{lab}: {clean!r} != {expected!r}"

    def test_abcd_order_preserved(self):
        """All four tables yield labels A-D (order of declaration preserved)."""
        for name, table in [("Q9", Q9_TABLE), ("Q19", Q19_TABLE),
                             ("Q24", Q24_TABLE), ("Q25", Q25_TABLE)]:
            cells = _html_table_option_cells(table)
            assert set(cells) == {"A", "B", "C", "D"}, f"{name}: {set(cells)}"

    def test_no_html_markup_in_clean_text(self):
        """HTML tags stripped from every option's clean text."""
        for name, table in [("Q9", Q9_TABLE), ("Q19", Q19_TABLE),
                             ("Q24", Q24_TABLE), ("Q25", Q25_TABLE)]:
            cells = _html_table_option_cells(table)
            for lab, (_, _, clean) in cells.items():
                assert "<" not in clean and ">" not in clean, \
                    f"{name}.{lab} has HTML: {clean!r}"
                assert "td" not in clean.lower() or "td" in clean.lower(), clean  # sanity

    def test_q24_latex_fidelity(self):
        """LaTeX math environments survive HTML extraction unchanged."""
        cells = _html_table_option_cells(Q24_TABLE)
        d = cells["D"][2]
        assert "$ ^{-1} $" in d, d
        assert "0.1 mol·L" in d, d
        # figure placeholders from row0 must NOT appear in option text
        for lab in "ABCD":
            assert "F_{" not in cells[lab][2], f"{lab} leaked figure placeholder"

    def test_q25_multicol_joins_two_cells(self):
        """Q25 option content = col1 + col2 (not truncated to one cell)."""
        cells = _html_table_option_cells(Q25_TABLE)
        a = cells["A"][2]
        assert "向KI-淀粉溶液中滴入氯水" in a, a
        assert "还原性强于" in a, a  # second column present
        assert "$ I^{-} $" in a and "$ Cl^{-} $" in a, a


# =====================================================================
# 2. End-to-end resolve: span + cell= evidence binding
# =====================================================================

class TestOptionSpanEvidenceBinding:
    """Source span and cell= evidence must both be correct (P2-R lesson)."""

    @pytest.mark.parametrize("qn,table,expected", [
        ("9", Q9_TABLE, Q9_EXPECTED),
        ("19", Q19_TABLE, Q19_EXPECTED),
        ("24", Q24_TABLE, Q24_EXPECTED),
        ("25", Q25_TABLE, Q25_EXPECTED),
    ])
    def test_resolved_text_matches_expected(self, qn, table, expected):
        opts = _resolve_options(qn, f"{qn}\\. stem text", "", table)
        for lab, exp in expected.items():
            assert lab in opts, f"Q{qn}.{lab} unresolved"
            text, span = opts[lab]
            assert text.strip() == exp, f"Q{qn}.{lab}: {text!r} != {exp!r}"

    @pytest.mark.parametrize("qn,table", [
        ("9", Q9_TABLE), ("19", Q19_TABLE),
        ("24", Q24_TABLE), ("25", Q25_TABLE),
    ])
    def test_cell_evidence_present(self, qn, table):
        """Every resolved option carries cell= evidence with clean text."""
        opts = _resolve_options(qn, f"{qn}\\. stem", "", table)
        for lab, (text, span) in opts.items():
            cell_ev = [e for e in span.evidence if e.startswith("cell=")]
            assert cell_ev, f"Q{qn}.{lab} missing cell= evidence: {span.evidence}"
            assert cell_ev[0][5:] == text.strip(), \
                f"Q{qn}.{lab} cell= mismatch: {cell_ev[0][5:]!r} vs {text!r}"

    @pytest.mark.parametrize("qn,table", [
        ("9", Q9_TABLE), ("19", Q19_TABLE),
        ("24", Q24_TABLE), ("25", Q25_TABLE),
    ])
    def test_span_points_to_table_line(self, qn, table):
        """Char span must be on the table line, offsets within raw length."""
        views = _mk(f"{qn}\\. stem", "", table)
        run = SourceResolver(source_version_id=SVID, lines=views).resolve(_payload(qn))
        for s in run.resolved_spans:
            if s.role != "option":
                continue
            assert s.start_line_ref == "P1L003", f"{s.span_id} on {s.start_line_ref}"
            assert s.granularity == "line_character", s.granularity
            assert s.start_offset is not None and s.end_offset is not None
            raw_len = len(table)
            assert 0 <= s.start_offset < s.end_offset <= raw_len, \
                f"{s.span_id} [{s.start_offset},{s.end_offset}) vs len={raw_len}"

    def test_q9_span_covers_cell_content(self):
        """Q9 option A span raw slice contains the expected content."""
        opts = _resolve_options("9", "9\\. stem", "", Q9_TABLE)
        text, span = opts["A"]
        raw_slice = Q9_TABLE[span.start_offset:span.end_offset]
        assert "青铜器皿" in raw_slice, raw_slice

    def test_q25_span_covers_both_cols(self):
        """Q25 option A span raw slice spans col1..col2 region."""
        opts = _resolve_options("25", "25\\. stem", "", Q25_TABLE)
        text, span = opts["A"]
        raw_slice = Q25_TABLE[span.start_offset:span.end_offset]
        assert "向KI-淀粉溶液" in raw_slice, raw_slice[:80]
        assert "还原性强于" in raw_slice, raw_slice[-80:]


# =====================================================================
# 3. Rule A hard assertion: no option may bind footer / section header
# =====================================================================

class TestRuleAFooterGuard:
    """Option spans must never bind page-footer or section-header lines."""

    def test_footer_re_matches_real_footer(self):
        assert _PAGE_FOOTER_RE.search("化学试卷 第2页（共8页）")
        assert _PAGE_FOOTER_RE.search("第 3 页")
        assert _PAGE_FOOTER_RE.search("共8页")

    def test_section_re_matches_real_header(self):
        assert _SECTION_HDR_RE.match("第二部分 非选择题（共50分）")
        assert _SECTION_HDR_RE.match("第一部分 选择题")

    def test_q19_no_footer_misbinding(self):
        """Q19 with footer line after table: A must NOT bind the footer."""
        lines = _mk(
            "19\\. stem", "",
            Q19_TABLE, "",
            "化学试卷 第2页（共8页）",  # P1L005 footer
            "", "20\\. next question",  # P1L007
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("19"))
        for s in run.resolved_spans:
            if s.role == "option":
                assert s.start_line_ref != "P1L005", \
                    f"{s.span_id} MISBOUND to footer P1L005"
                assert s.start_line_ref != "P1L007", \
                    f"{s.span_id} MISBOUND to next-question P1L007"

    def test_q25_no_section_misbinding(self):
        """Q25 with section header after table: A must NOT bind the header."""
        lines = _mk(
            "25\\. stem", "",
            Q25_TABLE, "",
            "第二部分 非选择题（共50分）",  # P1L005 section header
            "", "26\\. next",
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("25"))
        for s in run.resolved_spans:
            if s.role == "option":
                assert s.start_line_ref != "P1L005", \
                    f"{s.span_id} MISBOUND to section header P1L005"
                assert s.start_line_ref != "P1L007", \
                    f"{s.span_id} MISBOUND to next P1L007"

    def test_fixing_bcd_does_not_sacrifice_a(self):
        """A-D must ALL resolve to the table line — no partial + Rule A fallback."""
        for qn, table in [("19", Q19_TABLE), ("25", Q25_TABLE)]:
            lines = _mk(
                f"{qn}\\. stem", "", table, "",
                "化学试卷 第2页（共8页）", "第二部分 非选择题（共50分）",
                "", "99\\. unrelated",
            )
            run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload(qn))
            labs = {
                s.span_id.rsplit(".", 1)[-1]
                for s in run.resolved_spans if s.role == "option"
            }
            assert labs == {"A", "B", "C", "D"}, f"Q{qn} partial: {labs}"
            for s in run.resolved_spans:
                if s.role == "option":
                    assert s.start_line_ref == "P1L003", \
                        f"{s.span_id} on {s.start_line_ref}, expected table L3"


# =====================================================================
# 4. Figure handling: text-only, positional, no silent image bind
# =====================================================================

class TestFigureHandling:
    """Q9/Q24 images are explicitly NOT bound (figure_refs unsupported).

    Q24 figure order is positional (col0->A), never sorted by F number.
    """

    def test_q9_images_not_in_option_text(self):
        cells = _html_table_option_cells(Q9_TABLE)
        for lab in "ABCD":
            clean = cells[lab][2]
            assert "img" not in clean.lower(), clean
            assert ".jpg" not in clean.lower(), clean

    def test_q24_figures_not_in_option_text(self):
        cells = _html_table_option_cells(Q24_TABLE)
        for lab in "ABCD":
            clean = cells[lab][2]
            assert "F_{" not in clean, clean
            assert "[" not in clean or lab == "D", clean  # D has no bracket

    def test_q24_positional_not_f_number_sorted(self):
        """col0->A, col1->B, col2->C, col3->D regardless of F subscripts."""
        cells = _html_table_option_cells(Q24_TABLE)
        # row0 is [F4, F3, F5, F2] — if sorted by F number order would be
        # F2->A, F3->B, F4->C, F5->D which would scramble A-D.
        # Positional binding gives text from row1 col order.
        assert cells["A"][2] == "收集氯气"       # col0 text, NOT F2's column
        assert cells["B"][2] == "除去水中泥沙"   # col1 text, NOT F3's column
        assert cells["C"][2] == "分离乙醇和水"   # col2 text
        assert cells["D"][2].startswith("配制")  # col3 text
