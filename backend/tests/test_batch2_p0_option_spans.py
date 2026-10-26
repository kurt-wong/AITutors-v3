# -*- coding: utf-8 -*-
"""BATCH2-P0 span regression locks — four student-visible option fixes.

Locked shapes (source windows inlined so the test is machine-portable):
  chem Q23  C must NOT absorb D's ionic equation (L194)
  phys Q17  D must NOT absorb U18-20 shared material (L201)
  chem Q20  D keeps legal continuation 「还原反应」 (L159), no fake E
  mae  Q25  A/B/C/D split to char ranges 9/8/6/4, no section header

These are regression guards only — they lock already-verified behaviour
and must not become an open-ended acceptance suite.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domains.resolver.resolver import SourceResolver  # noqa: E402
from app.domains.resolver.span import SourceLineView  # noqa: E402

SVID = uuid.UUID("00000000-0000-0000-0000-000000000011")

# --- inlined source windows (verbatim from t179 packages) ---
# chem Q23: lines 186-196
CHEM_Q23 = (
    "23. 下列反应的离子方程式书写不正确的是",
    "",
    "A．金属钠与水： $ 2Na + 2H_{2}O = 2Na^{+} + 2OH^{-} + H_{2}\\uparrow $",
    "",
    "B．氯化钠溶液与硝酸银溶液：",
    "",
    "C．稀盐酸与碳酸钙： $ CaCO_{3}+2H^{+}=Ca^{2+}+CO_{2}\\uparrow+H_{2}O $",
    "",
    " $  \\mathrm{H}^{+} + \\mathrm{SO}_{4}^{2-} + \\mathrm{Ba}^{2+} + \\mathrm{OH}^{-} = \\mathrm{H}_{2}\\mathrm{O} + \\mathrm{BaSO}_{4} \\downarrow  $",
    "",
    "24. 下列实验装置或操作与实验目的 $ \\underset{\\cdot}{不}\\underset{\\cdot}{相}\\underset{\\cdot}{符} $的是",
)

# chem Q20: lines 149-162
CHEM_Q20 = (
    "20. 硫在自然界的循环过程如右图所示。下列说法中， $ \\underset{\\cdot}{不}\\underset{\\cdot}{正}\\underset{\\cdot}{确} $的是",
    "",
    "A. 火山喷发、森林火灾会产生SO $ _{2} $",
    "",
    "B. 氢、氧两种元素没有参与硫的",
    "",
    "C. 工厂产生的烟气应经脱硫处理后再排放",
    "",
    "D. 硫在自然界的循环过程中，涉及了氧",
    "",
    "还原反应",
    "",
    "21. 下列行为 $ \\underset{\\cdot}{不}\\underset{\\cdot}{符}\\underset{\\cdot}{合} $安全要求的是",
    "",
)

# phys Q17 + U18-20 material: lines 191-235
PHYS_Q17 = (
    "17. 小明家住在第16层。他放学后，乘坐竖直电梯从第1层直达第16层。假设电梯刚起动时做加速运动，中间一段时间内做匀速运动，最后一段时间内做减速运动。在电梯上升过程中，下列说法中正确的是",
    "",
    "A. 电梯加速运动时，小明处于失重状态",
    "",
    "B. 电梯加速运动时，小明处于超重状态",
    "",
    "C. 电梯匀速运动时，小明处于失重状态",
    "",
    "D. 电梯匀速运动时，小明处于超重状态",
    "",
    "请阅读下述文字，完成第18题、第19题、第20题如图9所示，在光滑水平面上，一质量为 m 的物体，在水平恒力 F 的作用下，以初速度  $ v_0 $ 做匀加速直线运动，经过时间 t 位移为 x，速度达到  $ v_t $。",
    "",
    "18. 在时间 t 内，物体运动的加速度等于",
    "",
    "A.  $ v_t - v_0 $ B.  $ v_0 - v_t $",
    "",
    "C.  $ \\frac{v_0 + v_t}{t} $ D.  $ \\frac{v_t - v_0}{t} $",
    "",
    "",
    "",
    "",
    "",
    '<div style="text-align: center;"><img src="../../_imgs/x/img.jpg" alt="Image" width="25%" /></div>',
    "",
    "",
    '<div style="text-align: center;">图9</div>',
    "",
    "",
    "19.力对物体的作用在空间上累积的效果可以用力 F 与位移 x 的乘积表示，即 Fx。根据牛顿第二定律，物体的加速度  $ a = \\frac{F}{m} $；物体做匀加速运动，满足  $ v_t^2 - v_0^2 = 2ax $。可得，Fx 等于",
    "",
    "A.  $ \\frac{1}{2}mv_t^2 - \\frac{1}{2}mv_0^2 $ B.  $ \\frac{1}{2}mv_0^2 + \\frac{1}{2}mv_t^2 $",
    "",
    "---",
    "",
    "C.  $ \\frac{1}{2}mv_{0}^{2} $ D.  $ \\frac{1}{2}mv_{t}^{2} $",
    "",
    "20.与力对物体的作用在空间上累积的效果类似，力对物体的作用在时间上也有累积效果，可以用力 F 和时间 t 的乘积表示，即 Ft。根据上述情境，Ft 等于",
    "",
    "A.  $ mv_{t} - mv_{0} $ B.  $ mv_{0} + mv_{t} $",
    "",
    "C.  $ mv_{0} $ D.  $ mv_{t} $",
    "",
    "## 第二部分 非选择题（共40分）",
    "",
    "## 二、 填空题（本题共3小题。每小题4分，共12分）",
)

# mae Q25: lines 140-160
MAE_Q25 = (
    "",
    "A. ①  B. ②  C. ③  D. ④",
    "",
    "25. 我国古代数学名著《续古摘奇算法》（杨辉）一书中有关于三阶幻方的问题：将 1，2，3，4，5，6，7，8，9 分别填入  $ 3 \\times 3 $ 的方格中，使得每一行，每一列及对角线上的三个数的和都相等（如图所示），我们规定：只要两个幻方的对应位置（如每行第一列的方格）中的数字不全相同，就称为不同的幻方，那么所有不同的三阶幻方的个数是（）",
    "",
    '<div style="text-align: center;"><img src="../../_imgs/x/img1.jpg" alt="Image" width="14%" /></div>',
    "",
    "",
    "---",
    "",
    '<div style="text-align: center;"><img src="../../_imgs/x/img2.jpg" alt="Image" width="16%" /></div>',
    "",
    "",
    "A. 9 B. 8 C. 6 D. 4",
    "",
    "### 二. 解答题（每小题5分，共25分）",
    "",
    "26. 已知  $ \\theta \\in (\\frac{\\pi}{2}, \\pi) $，且  $ \\sin \\theta = \\frac{3}{5} $.",
    "",
    "（Ⅰ） $ \\tan\\theta= $___；",
    "",
)


def _lines(texts, start_line=1):
    return tuple(
        SourceLineView(f"P1L{i + start_line:03d}", t, i + start_line, 1, i + start_line)
        for i, t in enumerate(texts)
    )


def _resolve(lines, unit_id, qn, labels="ABCD"):
    res = SourceResolver(source_version_id=SVID, lines=lines)
    payload = {
        "semantic_units": [{
            "unit_id": unit_id,
            "unit_type": "standalone_question",
            "question_number": qn,
            "content": {
                "stem": {"question_label": qn},
                "options": [{"label": x} for x in labels],
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": qn,
                    "answer_completeness": "full",
                },
            },
        }]
    }
    return res.resolve(payload)


def _opt_spans(run, unit_id):
    by = {}
    for s in run.resolved_spans:
        if s.span_id.startswith(f"sp-{unit_id}.option."):
            by[s.span_id.rsplit(".", 1)[-1]] = s
    return by


def _span_text(lines, span):
    by_ref = {l.line_ref: l.text for l in lines}
    refs = list(span.line_refs)
    if span.granularity == "line_character" and span.start_offset is not None:
        raw = by_ref.get(refs[0], "")
        return raw[span.start_offset:span.end_offset]
    return "\n".join(by_ref.get(r, "") for r in refs)


class TestBatch2P0OptionSpans:
    """Lock the four P0 student-visible option fixes."""

    def test_q23_C_does_not_absorb_D_equation(self):
        """Chem Q23: C=L192 only; D=L194 keeps the BaSO4 equation."""
        # CHEM_Q23 starts at source L186 → L192 is index 6, L194 is index 8
        lines = _lines(CHEM_Q23, 186)
        run = _resolve(lines, "Q23", "23")
        spans = _opt_spans(run, "Q23")
        c_refs = list(spans["C"].line_refs)
        d_refs = list(spans["D"].line_refs)
        assert c_refs == ["P1L192"], f"C must be L192 only, got {c_refs}"
        assert d_refs == ["P1L194"], f"D must be L194 only, got {d_refs}"
        c_txt = _span_text(lines, spans["C"])
        d_txt = _span_text(lines, spans["D"])
        assert "BaSO" not in c_txt and "mathrm{H}" not in c_txt, (
            f"C absorbed D's equation: {c_txt!r}"
        )
        assert "BaSO" in d_txt or "mathrm" in d_txt, f"D lost its equation: {d_txt!r}"

    def test_q17_D_does_not_absorb_shared_material(self):
        """Phys Q17: D=L199 only; never pulls U18-20 material L201."""
        # PHYS_Q17 starts at source L191 → L199 is index 8, L201 is index 10
        lines = _lines(PHYS_Q17, 191)
        run = _resolve(lines, "Q17", "17")
        spans = _opt_spans(run, "Q17")
        d_refs = list(spans["D"].line_refs)
        assert d_refs == ["P1L199"], f"D must be L199 only, got {d_refs}"
        d_txt = _span_text(lines, spans["D"])
        assert "请阅读" not in d_txt and "完成第18" not in d_txt, (
            f"D absorbed U18-20 material: {d_txt!r}"
        )

    def test_q20_D_keeps_legal_continuation_no_E(self):
        """Chem Q20: D spans L157+L159 (还原反应); no option E is created."""
        # CHEM_Q20 starts at source L149 → L157 is index 8, L159 is index 10
        lines = _lines(CHEM_Q20, 149)
        run = _resolve(lines, "Q20", "20")
        spans = _opt_spans(run, "Q20")
        assert "E" not in spans, f"fake option E appeared: {list(spans)}"
        d_refs = list(spans["D"].line_refs)
        assert d_refs == ["P1L157", "P1L159"], f"D must span L157+L159, got {d_refs}"
        d_txt = _span_text(lines, spans["D"])
        assert "还原反应" in d_txt, f"D lost continuation: {d_txt!r}"

    def test_q25_four_short_options_split_by_char_range(self):
        """MAE Q25: A/B/C/D → 9/8/6/4 as separate char spans; no section header."""
        # MAE_Q25 starts at source L140 → L153 is index 13, L155 is index 15
        lines = _lines(MAE_Q25, 140)
        run = _resolve(lines, "Q25", "25")
        spans = _opt_spans(run, "Q25")
        expected = {"A": "9", "B": "8", "C": "6", "D": "4"}
        for lab, exp in expected.items():
            assert lab in spans, f"missing option {lab}"
            s = spans[lab]
            assert s.granularity == "line_character", (
                f"{lab} must be line_character, got {s.granularity}"
            )
            got = _span_text(lines, s).strip()
            assert got == exp, f"{lab} should be {exp!r}, got {got!r}"
        # no section header leaked into any option
        for lab, s in spans.items():
            t = _span_text(lines, s)
            assert "解答题" not in t and "###" not in t, f"{lab} absorbed header: {t!r}"
        # four distinct texts
        texts = {_span_text(lines, s).strip() for s in spans.values()}
        assert len(texts) == 4, f"options not distinct: {texts}"
