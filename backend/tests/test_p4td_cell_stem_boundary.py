# -*- coding: utf-8 -*-
"""P4-TD-01 — "cell" option kind must participate in stem boundary detection.

Without this, Q19/Q25 stems absorb footer/section lines because _stem_span
only recognized ("ok","content","inline") as option starts.
"""
import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000a")

Q19_TABLE = (
    "<table border=1><tr><td></td><td>A</td><td>B</td><td>C</td><td>D</td></tr>"
    "<tr><td>t / °C</td><td>10</td><td>10</td><td>40</td><td>40</td></tr>"
    "<tr><td>c</td><td>1</td><td>3</td><td>1</td><td>3</td></tr></table>"
)
Q25_TABLE = (
    "<table border=1><tr><td>选项</td><td>实验操作及现象</td><td>推理或结论</td></tr>"
    "<tr><td>A</td><td>向KI-淀粉溶液中滴入氯水，溶液变成蓝色</td>"
    "<td>$ I^{-} $的还原性强于 $ Cl^{-} $</td></tr>"
    "<tr><td>B</td><td>向某溶液中加入 $ BaCl_{2} $溶液</td>"
    "<td>含有 $ SO_{4}^{2-} $</td></tr>"
    "<tr><td>C</td><td>取少量 $ Na_{2}O_{2} $粉末</td><td>放热反应</td></tr>"
    "<tr><td>D</td><td>加入NaOH溶液</td><td>含有 $ Fe^{2+} $</td></tr></table>"
)
Q9_TABLE = (
    "<table border=1>"
    "<tr><td>A. 青铜器皿</td><td>B. 陶瓷</td><td>C. 丝绸</td><td>D. 中草药</td></tr>"
    "<tr><td><img/></td><td><img/></td><td><img/></td><td><img/></td></tr></table>"
)
Q24_TABLE = (
    "<table border=1>"
    "<tr><td>[ $ F_{4} $]</td><td>[ $ F_{3} $]</td><td>[ $ F_{5} $]</td><td>[ $ F_{2} $]</td></tr>"
    "<tr><td>A. 收集氯气</td><td>B. 除去水中泥沙</td><td>C. 分离乙醇和水</td>"
    "<td>D. 配制100 mL 0.1 mol·L $ ^{-1} $ NaCl溶液</td></tr></table>"
)


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(qn):
    return {
        "semantic_units": [{
            "unit_id": f"Q{qn}",
            "unit_type": "standalone_unit",
            "question_number": str(qn),
            "content": {
                "stem": {"role": "stem", "question_label": str(qn)},
                "options": [{"role": "option", "label": x} for x in "ABCD"],
                "answer": {
                    "role": "answer", "answer_zone": "inline_answer",
                    "question_label": str(qn),
                },
            },
        }]
    }


def _resolve(qn, *lines):
    views = _mk(*lines)
    return SourceResolver(source_version_id=SVID, lines=views).resolve(_payload(qn))


class TestCellKindStemBoundary:
    """P4-TD-01: "cell" options must bound the stem span."""

    def test_q19_stem_excludes_table_and_footer(self):
        lines = _mk(
            "19\\. 控制变量是科学研究的重要方法。相同质量的铁粉与足量稀硫酸分别在下列条件下发生反应，其中反应速率最快的是",
            "", Q19_TABLE, "",
            "化学试卷 第2页（共8页）",
            "", "20\\. 下一题",
        )
        run = _resolve("19", *[l.text for l in lines])
        stem = next(s for s in run.resolved_spans if s.role == "stem")
        # stem must end before table (P1L003)
        assert "P1L003" not in stem.line_refs, f"stem includes table: {stem.line_refs}"
        assert "P1L005" not in stem.line_refs, f"stem includes footer: {stem.line_refs}"
        assert "P1L007" not in stem.line_refs, f"stem includes next: {stem.line_refs}"
        # stem is only the stem line (and possibly the blank line before table)
        assert all(int(r[4:]) <= 2 for r in stem.line_refs), stem.line_refs

    def test_q25_stem_excludes_table_and_section(self):
        lines = _mk(
            "25\\. 下列“推理或结论”与“实验操作及现象”不相符的一组是",
            "", Q25_TABLE, "",
            "第二部分 非选择题（共50分）",
            "", "26\\. 下一题",
        )
        run = _resolve("25", *[l.text for l in lines])
        stem = next(s for s in run.resolved_spans if s.role == "stem")
        assert "P1L003" not in stem.line_refs, f"stem includes table: {stem.line_refs}"
        assert "P1L005" not in stem.line_refs, f"stem includes section: {stem.line_refs}"
        assert "P1L007" not in stem.line_refs, f"stem includes next: {stem.line_refs}"
        assert all(int(r[4:]) <= 2 for r in stem.line_refs), stem.line_refs

    def test_q9_stem_boundary_unchanged(self):
        """Q9 stem boundary must not change (no regression)."""
        lines = _mk(
            "9\\. 丝绸之路贸易中的下列商品，主要成分属于合金的是",
            "", Q9_TABLE, "",
            "化学试卷 第2页（共8页）",
        )
        run = _resolve("9", *[l.text for l in lines])
        stem = next(s for s in run.resolved_spans if s.role == "stem")
        assert "P1L003" not in stem.line_refs, f"stem includes table: {stem.line_refs}"
        assert "P1L005" not in stem.line_refs, f"stem includes footer: {stem.line_refs}"
        assert all(int(r[4:]) <= 2 for r in stem.line_refs), stem.line_refs

    def test_q24_stem_boundary_unchanged(self):
        """Q24 stem boundary must not change (no regression)."""
        lines = _mk(
            "24\\. 下列实验装置或操作与实验目的不相符的是",
            "", Q24_TABLE, "",
            "化学试卷 第2页（共8页）",
        )
        run = _resolve("24", *[l.text for l in lines])
        stem = next(s for s in run.resolved_spans if s.role == "stem")
        assert "P1L003" not in stem.line_refs, f"stem includes table: {stem.line_refs}"
        assert "P1L005" not in stem.line_refs, f"stem includes footer: {stem.line_refs}"
        assert all(int(r[4:]) <= 2 for r in stem.line_refs), stem.line_refs


class TestStemContentExclusion:
    """Stem text must not contain table/footer/section content."""

    def test_q19_stem_text_clean(self):
        lines = _mk(
            "19\\. 控制变量是科学研究的重要方法。相同质量的铁粉与足量稀硫酸分别在下列条件下发生反应，其中反应速率最快的是",
            "", Q19_TABLE, "",
            "化学试卷 第2页（共8页）",
            "", "20\\. 下一题",
        )
        run = _resolve("19", *[l.text for l in lines])
        stem = next(s for s in run.resolved_spans if s.role == "stem")
        # reconstruct stem text from line refs
        stem_text = "\n".join(lines[int(r[4:])-1].text for r in stem.line_refs)
        assert "化学试卷" not in stem_text, f"footer in stem: {stem_text!r}"
        assert "<table" not in stem_text, f"table in stem: {stem_text!r}"
        assert "t / °C" not in stem_text, f"table row in stem: {stem_text!r}"

    def test_q25_stem_text_clean(self):
        lines = _mk(
            "25\\. 下列“推理或结论”与“实验操作及现象”不相符的一组是",
            "", Q25_TABLE, "",
            "第二部分 非选择题（共50分）",
            "", "26\\. 下一题",
        )
        run = _resolve("25", *[l.text for l in lines])
        stem = next(s for s in run.resolved_spans if s.role == "stem")
        stem_text = "\n".join(lines[int(r[4:])-1].text for r in stem.line_refs)
        assert "第二部分" not in stem_text, f"section in stem: {stem_text!r}"
        assert "非选择题" not in stem_text, f"section in stem: {stem_text!r}"
        assert "<table" not in stem_text, f"table in stem: {stem_text!r}"
        assert "<td" not in stem_text, f"table cell in stem: {stem_text!r}"
        assert "选项" != stem_text.strip(), f"table header row in stem: {stem_text!r}"


class TestOptionTextSpanConsistency:
    """P2-R lesson: option text and span must both be correct.

    Single-cell (Q9/Q24): raw[start:end] == expected clean text.
    Multi-cell (Q19/Q25): cell= evidence == expected clean text.
    """

    def test_q9_single_cell_raw_slice_matches(self):
        lines = _mk("9\\. stem", "", Q9_TABLE)
        run = _resolve("9", *[l.text for l in lines])
        raw = Q9_TABLE
        expected = {"A": "青铜器皿", "B": "陶瓷", "C": "丝绸", "D": "中草药"}
        for s in run.resolved_spans:
            if s.role != "option":
                continue
            lab = s.span_id.rsplit(".", 1)[-1]
            slice_text = raw[s.start_offset:s.end_offset]
            assert slice_text == expected[lab], \
                f"Q9.{lab}: raw slice {slice_text!r} != {expected[lab]!r}"

    def test_q24_single_cell_raw_slice_matches(self):
        lines = _mk("24\\. stem", "", Q24_TABLE)
        run = _resolve("24", *[l.text for l in lines])
        raw = Q24_TABLE
        expected = {
            "A": "收集氯气", "B": "除去水中泥沙", "C": "分离乙醇和水",
            "D": "配制100 mL 0.1 mol·L $ ^{-1} $ NaCl溶液",
        }
        for s in run.resolved_spans:
            if s.role != "option":
                continue
            lab = s.span_id.rsplit(".", 1)[-1]
            slice_text = raw[s.start_offset:s.end_offset]
            assert slice_text == expected[lab], \
                f"Q24.{lab}: raw slice {slice_text!r} != {expected[lab]!r}"

    def test_q19_multicell_cell_evidence_matches(self):
        lines = _mk("19\\. stem", "", Q19_TABLE)
        run = _resolve("19", *[l.text for l in lines])
        expected = {"A": "10 1", "B": "10 3", "C": "40 1", "D": "40 3"}
        for s in run.resolved_spans:
            if s.role != "option":
                continue
            lab = s.span_id.rsplit(".", 1)[-1]
            cell_ev = [e for e in s.evidence if e.startswith("cell=")]
            assert cell_ev, f"Q19.{lab} missing cell= evidence"
            assert cell_ev[0][5:] == expected[lab], \
                f"Q19.{lab}: cell= {cell_ev[0][5:]!r} != {expected[lab]!r}"

    def test_q25_multicell_cell_evidence_matches(self):
        lines = _mk("25\\. stem", "", Q25_TABLE)
        run = _resolve("25", *[l.text for l in lines])
        expected_a = "向KI-淀粉溶液中滴入氯水，溶液变成蓝色 $ I^{-} $的还原性强于 $ Cl^{-} $"
        for s in run.resolved_spans:
            if s.role != "option":
                continue
            lab = s.span_id.rsplit(".", 1)[-1]
            cell_ev = [e for e in s.evidence if e.startswith("cell=")]
            assert cell_ev, f"Q25.{lab} missing cell= evidence"
            if lab == "A":
                assert cell_ev[0][5:] == expected_a, \
                    f"Q25.A: {cell_ev[0][5:]!r}"
            assert len(cell_ev[0]) > 5, f"Q25.{lab} empty cell= text"
