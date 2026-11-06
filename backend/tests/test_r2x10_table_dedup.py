# -*- coding: utf-8 -*-
"""R2X-10 P-2 判据单测（DSH 复核口径）。

正例 7（可见三表类，真实单元格夹具来自 r2x 包，覆盖率与 DSH 数字对表）：
  math_2021_sh_chun Q10（2 块）、bio_2022_yi Q4/Q11、chem_2020_tj Q8、
  chem_2022_yi Q4、phy_2022_yi Q5/Q9
反例 2（stem 无表、extra 唯一表通道，覆盖 0.00——区段互斥会误杀的那两条）：
  chem_2020_tj Q5/Q6
另：Q17 漂移图（img 块排除）、块粒度全有全无、审计字段不静默丢、阈值边界。
"""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.domains.resolver.table_dedup import (
    TableBlock,
    classify_extra_table_block,
    extract_cells,
    iter_table_blocks,
)

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f2")


def _blk(cells, has_img=False):
    cells = tuple(cells)
    return TableBlock(
        start_seq=1, end_seq=1, cells=cells, has_img=has_img, has_text=any(cells)
    )


def _mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _resolve(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)


# ---------------- 真实夹具（r2x 包提取：EXPANSION_R2_R2X10_FIXTURES.json） ----------------

MATH_Q10_STEM = [
    "A运动", "B运动", "C运动", "D运动", "E运动",
    "7点-8点", "8点-9点", "9点-10点", "10点-11点", "11点-12点",
    "30分钟", "20分钟", "40分钟", "30分钟", "30分钟",
]
MATH_Q10_EXTRA_2X5 = MATH_Q10_STEM[:10]
MATH_Q10_EXTRA_1X5 = MATH_Q10_STEM[10:]

BIO_Q4_STEM = [
    "实验组", "①", "②", "③", "④", "⑤",
    "底物", "+", "+", "+", "+", "+",
    "RNA组分", "+", "+", "-", "+", "-",
    "蛋白质组分", "+", "-", "+", "-", "+",
    "低浓度$Mg^{2+}$", "+", "+", "+", "-", "-",
    "高浓度$Mg^{2+}$", "-", "-", "-", "+", "+",
    "产物", "+", "-", "-", "+", "-",
]

BIO_Q11_STEM = [
    "碳源", "细胞干重（g/L）", "S产量（g/L）",
    "葡萄糖", "3.12", "0.15",
    "淀粉", "0.01", "0.00",
    "制糖废液", "230", "0.18",
]
BIO_Q11_EXTRA = list(BIO_Q11_STEM)
BIO_Q11_EXTRA[10] = "2.30"  # 答案区副本；PDF 正确值 2.30（题区 230 为丢点重打）

CHEM_Q8_STEM = [
    "最高价氧化物的水化物", "X", "Y", "Z", "W",
    "分子式", "", "", "$H_{3}ZO_{4}$", "",
    "0.1mol·L$^{-1}$溶液对应的pH(25℃)", "1.00", "13.00", "1.57", "0.70",
]
CHEM_Q8_EXTRA = [
    "元素", "X", "Y", "Z", "W",
    "最高价氧化物的水化物", "", "", "$H_{3}ZO_{4}$", "",
    "0.1mol·$L^{-1}$溶液对应的pH(25℃)", "1.00", "13.00", "1.57", "0.70",
]

CHEM22_Q4_STEM = [
    "", "实验操作", "现象", "结论",
    "A", "向NaBr溶液中滴加过量氯水，再加入淀粉KI溶液", "先变橙色，后变蓝色", "氧化性",
    "B", "向蔗糖溶液中滴加稀硫酸", "无砖红色沉淀", "蔗糖未发生水解",
    "C", "石蜡油加强热", "溶液红棕色变无色", "气体中含有不饱和烃",
    "D", "加热试管中的聚氯乙烯薄膜碎片", "试管口润湿的蓝色石蕊试纸变红", "氯乙烯加聚是可逆反应",
]
CHEM22_Q4_EXTRA = list(CHEM22_Q4_STEM)
CHEM22_Q4_EXTRA[19] = "氯乙烯加聚可逆反应"

PHY_Q5_STEM = [
    "测量序号", "$B_x/\\muT$", "$B_y/\\muT$", "$B_z/\\muT$",
    "1", "0", "21", "-45", "2", "0", "-20", "-46",
    "3", "21", "0", "-45", "4", "-21", "0", "-45",
]
PHY_Q9_STEM = [
    "t/s", "0", "1", "2", "3", "4", "5", "6",
    "x/m", "0", "507", "1094", "1759", "2505", "3329", "4233",
]

CHEM_Q5_EXTRA = [
    "", "饱和NaCl溶液", "", "",
    "配制5000mL0.1000mol.L$^{-1}$Na$_{2}$CO$_{3}$溶液", "除去Cl$_{2}$中的HCl",
    "蒸馏用冷凝管", "盛装Na$_{2}$SiO$_{3}$溶液的试剂瓶", "A", "B", "C", "D",
]
CHEM_Q6_EXTRA = [
    "", "待检验物质", "所用试剂",
    "A", "海水中的碘元素", "淀粉溶液",
    "B", "$SO_{2}$气体", "澄清石灰水",
    "C", "溶液中的$Cu^{2+}$", "氨水",
    "D", "溶液中的$NH_{4}^{+}$", "NaOH溶液",
]


class TestCriterionRealFixtures:
    """7 正例：重复块整块去；覆盖率与 DSH 对表。"""

    def test_math_q10_both_fragments_dropped(self):
        for cells in (MATH_Q10_EXTRA_2X5, MATH_Q10_EXTRA_1X5):
            d = classify_extra_table_block(_blk(cells), MATH_Q10_STEM)
            assert d.action == "drop", d
            assert d.reason == "duplicate_of_stem"
            assert d.coverage == 1.0
            assert d.uncovered_cells == ()

    def test_bio_q4_full_retypeset_dropped(self):
        d = classify_extra_table_block(_blk(BIO_Q4_STEM), BIO_Q4_STEM)
        assert d.action == "drop" and d.coverage == 1.0

    def test_bio_q11_dot_loss_audited(self):
        """0.9167 ≥ 0.75 → drop；未覆盖单元格 2.30 进审计（不静默丢）。"""
        d = classify_extra_table_block(_blk(BIO_Q11_EXTRA), BIO_Q11_STEM)
        assert d.action == "drop", d
        assert abs(d.coverage - 11 / 12) < 1e-9
        assert d.uncovered_cells == ("2.30",)

    def test_chem_q8_row_misaligned_dropped(self):
        """行错位（元素 顶替 分子式）仍 ≥0.75 → drop。
        注：本实现 13/15≈0.8667；DSH 手算 0.83（单元格切分归一差异），两者同判。"""
        d = classify_extra_table_block(_blk(CHEM_Q8_EXTRA), CHEM_Q8_STEM)
        assert d.action == "drop", d
        assert abs(d.coverage - 13 / 15) < 1e-9
        assert set(d.uncovered_cells) == {"元素", "0.1mol·$L^{-1}$溶液对应的pH(25℃)"}

    def test_chem22_q4_partial_reword_dropped(self):
        d = classify_extra_table_block(_blk(CHEM22_Q4_EXTRA), CHEM22_Q4_STEM)
        assert d.action == "drop", d
        assert abs(d.coverage - 0.95) < 1e-9
        assert d.uncovered_cells == ("氯乙烯加聚可逆反应",)

    def test_phy_q5_and_q9_exact_dropped(self):
        for stem, extra in ((PHY_Q5_STEM, PHY_Q5_STEM), (PHY_Q9_STEM, PHY_Q9_STEM)):
            d = classify_extra_table_block(_blk(extra), stem)
            assert d.action == "drop" and d.coverage == 1.0


class TestNegativeControls:
    """反例：chem_2020_tj Q5/Q6——stem 无表，extra 是唯一表通道，必须保留。"""

    def test_chem_q5_img_block_kept(self):
        d = classify_extra_table_block(_blk(CHEM_Q5_EXTRA, has_img=True), [])
        assert d.action == "keep"
        assert d.reason == "img_block"

    def test_chem_q6_unique_channel_kept(self):
        d = classify_extra_table_block(_blk(CHEM_Q6_EXTRA), [])
        assert d.action == "keep"
        assert d.reason == "no_stem_table"
        assert d.coverage == 0.0

    def test_q17_style_img_only_table_kept(self):
        """图行 strip 后是空单元格——文本级去重会误判 DUP；img 规则兜底。"""
        blk = _blk(["", "", "", ""], has_img=True)
        d = classify_extra_table_block(blk, ["", "", "", ""])  # 完全“相同”也不去
        assert d.action == "keep"
        assert d.reason == "img_block"

    def test_empty_text_block_without_img_kept(self):
        d = classify_extra_table_block(_blk(["", ""]), ["", ""])
        assert d.action == "keep"
        assert d.reason == "no_text_cells"


class TestThresholdAndGranularity:
    def test_threshold_is_inclusive_at_075(self):
        assert classify_extra_table_block(_blk(["a", "b", "c", "X"]), ["a", "b", "c", "d"]).action == "drop"
        assert classify_extra_table_block(_blk(["a", "b", "X", "Y"]), ["a", "b", "c", "d"]).action == "keep"

    def test_block_granularity_all_or_nothing(self):
        """5 行块只有 1 行重复——整块仍一个决策，不产残行。"""
        stem = ["h1", "h2", "r1a", "r1b", "r2a", "r2b", "r3a", "r3b"]
        extra = ["h1", "h2", "r1a", "r1b", "ZZa", "ZZb", "r3a", "r3b"]  # 6/8=0.75
        d = classify_extra_table_block(_blk(extra), stem)
        assert d.action == "drop"
        assert d.block.start_seq == 1 and d.block.end_seq == 1  # 单块单决策
        assert len(d.uncovered_cells) == 2


class TestIterTableBlocks:
    def test_real_single_line_block_parses(self):
        html = (
            "<table border=1><tr><td>A 运动</td><td>B 运动</td></tr>"
            "<tr><td>30 分钟</td><td>20 分钟</td></tr></table>"
        )
        blocks = iter_table_blocks([(1, html)], 1, 1)
        assert len(blocks) == 1
        assert blocks[0].cells == ("A运动", "B运动", "30分钟", "20分钟")
        assert blocks[0].has_text and not blocks[0].has_img

    def test_multiline_block(self):
        blocks = iter_table_blocks(
            [(1, "前文 <table><tr><td>a</td>"), (2, "</tr></table> 后文")], 1, 2
        )
        assert len(blocks) == 1
        assert blocks[0].start_seq == 1 and blocks[0].end_seq == 2
        assert blocks[0].cells == ("a",)

    def test_unclosed_block_not_produced(self):
        blocks = iter_table_blocks([(1, "<table><tr><td>a</td>")], 1, 1)
        assert blocks == []

    def test_extract_cells_ignores_markup(self):
        assert extract_cells(
            "<table><tr><td><div style='x'><img src='p.jpg'/></div></td></tr></table>"
        ) == [""]


class TestResolverIntegration:
    """经 SourceResolver 的端到端行为：重复块不进 stem refs，审计挂 evidence。"""

    def _payload(self, extra_lines, stem_lines=(1, 2)):
        return {"semantic_units": [{
            "unit_id": "Q10", "unit_type": "standalone_question",
            "question_number": "1",
            "content": {
                "stem": {"question_label": "1",
                         "question_search_lines": list(stem_lines),
                         "stem_lines": list(stem_lines),
                         "extra_lines": list(extra_lines)},
                "answer": {"answer_zone": "answer_table", "question_label": "1",
                           "answer_lines": [1, 1], "answer_completeness": "full"},
            },
        }]}

    def test_duplicate_tables_excluded_from_stem(self):
        stem_tbl = (
            "<table><tr><td>A</td><td>B</td></tr>"
            "<tr><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td></tr></table>"
        )
        dup1 = "<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>"
        dup2 = "<table><tr><td>3</td><td>4</td></tr></table>"
        lines = _mk("1. 题干如表所示", stem_tbl, "", dup1, dup2)
        run = _resolve(lines, self._payload((4, 5)))
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q10.stem")
        refs = list(stem.line_refs)
        assert "P1L001" in refs and "P1L002" in refs
        assert "P1L004" not in refs and "P1L005" not in refs, f"重复块混入题干: {refs}"
        tags = [e for e in stem.evidence if e.startswith("table_dedup=")]
        assert len(tags) == 2 and all(":drop:" in t for t in tags), tags

    def test_unique_channel_table_kept(self):
        """chem Q5/Q6 形态：题干无表、extra 是唯一表通道 → 必须保留。"""
        uniq = "<table><tr><td>独有表</td><td>数据</td></tr></table>"
        lines = _mk("1. 题干无表", "", "", uniq)
        run = _resolve(lines, self._payload((4, 4), stem_lines=(1, 1)))
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q10.stem")
        assert "P1L004" in list(stem.line_refs), stem.line_refs
        tags = [e for e in stem.evidence if e.startswith("table_dedup=")]
        assert tags and all(":keep:" in t for t in tags), tags

    def test_img_extra_line_kept(self):
        """Q17 形态：答案区漂移图（img 行）不参与去重，照常并入。"""
        lines = _mk("1. 题干如图", "", "", "<img src='p.jpg'>")
        run = _resolve(lines, self._payload((4, 4), stem_lines=(1, 1)))
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q10.stem")
        assert "P1L004" in list(stem.line_refs), stem.line_refs

    def test_audit_not_silently_dropped(self):
        """bio Q11 形态：drop 的未覆盖单元格必须出现在 evidence（审计字段）。"""
        stem_tbl = (
            "<table><tr><td>碳源</td><td>干重</td></tr>"
            "<tr><td>葡萄糖</td><td>230</td></tr></table>"
        )
        dup = (
            "<table><tr><td>碳源</td><td>干重</td></tr>"
            "<tr><td>葡萄糖</td><td>2.30</td></tr></table>"
        )
        lines = _mk("1. 结果见表", stem_tbl, "", dup)
        run = _resolve(lines, self._payload((4, 4)))
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q10.stem")
        tags = [e for e in stem.evidence if e.startswith("table_dedup=")]
        assert any("uncovered=2.30" in t for t in tags), tags


class TestP2bAnswerLineNotLeaked:
    """R2X-10 P-2b：答案/解析标记行永不并入题干（phy_2020_js Q4 泄漏防线）。"""

    def _payload(self, extra_lines, stem_lines=(1, 1)):
        return {"semantic_units": [{
            "unit_id": "Q4", "unit_type": "standalone_question",
            "question_number": "4",
            "content": {
                "stem": {"question_label": "4",
                         "question_search_lines": list(stem_lines),
                         "stem_lines": list(stem_lines),
                         "extra_lines": list(extra_lines)},
                "answer": {"answer_zone": "answer_table", "question_label": "4",
                           "answer_lines": [1, 1], "answer_completeness": "full"},
            },
        }]}

    def test_answer_marker_line_blocked(self):
        """【答案】A 形态：已发布题干不得带答案（首证 phy_2020_js Q4 L388）。"""
        lines = _mk(
            "4. 物块沿斜面下滑，动能图象是（）",  # L1 stem
            "<img src='fig1.jpg'>",                 # L2 extra（图，仍并入）
            "【答案】A",                            # L3 extra（答案行，必须拦截）
            "<img src='fig2.jpg'>",                 # L4 extra
        )
        run = _resolve(lines, self._payload((2, 4)))
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q4.stem")
        refs = list(stem.line_refs)
        assert "P1L003" not in refs, f"答案行泄漏进题干: {refs}"
        assert "P1L002" in refs and "P1L004" in refs, refs  # 图行不受影响
        tags = [e for e in stem.evidence if e.startswith("extra_line_blocked=")]
        assert any("@L3" in t for t in tags), tags

    def test_explanation_header_blocked(self):
        """【解析】标记行拦截；正文行不在 P-2b 范围（处方=仅标记行）。"""
        lines = _mk(
            "4. 题干", "【解析】", "解析正文",
        )
        run = _resolve(lines, self._payload((2, 3)))
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q4.stem")
        refs = list(stem.line_refs)
        assert "P1L002" not in refs, f"解析标记行泄漏: {refs}"
        assert "P1L003" in refs, "正文行超出 P-2b 处方范围，应保持既有归集行为"

    def test_answer_header_with_value_blocked(self):
        """答案：23 形态（is_answer_header 命中）同样拦截。"""
        lines = _mk("10. 题干", "答案: 23", "")
        run = _resolve(lines, self._payload((2, 2)))
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q4.stem")
        assert "P1L002" not in list(stem.line_refs), stem.line_refs

    def test_body_text_mentioning_answer_not_blocked(self):
        """正文提及「故【答案】为」不误杀（前置汉字使 lookbehind 不命中）。"""
        lines = _mk("10. 题干", "故【答案】为 23 种。", "")
        run = _resolve(lines, self._payload((2, 2)))
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q4.stem")
        assert "P1L002" in list(stem.line_refs), stem.line_refs
