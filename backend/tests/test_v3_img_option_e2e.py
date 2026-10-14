# -*- coding: utf-8 -*-
"""V3-IMG-OPTION-001 end-to-end — resolver → IR → compiler on real source shapes.

Uses the actual GEO Q8 / PHY Q12 markdown structures (not fixtures invented
for the unit tests). Proves option labels, order, and image refs survive
into CompiledLeaf.options text.
"""
from __future__ import annotations

import uuid

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-000000000021")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-000000000022")


def mk(*texts: str):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _geo_q8_real_lines():
    """GEO Q8 excerpt from 2018北京夏季高中会考地理 — real OCR markdown."""
    return mk(
        "北京时间2017年8月20日14时，热带风暴“天鸽”在西北太平洋洋面上生成，之后逐渐演变为强台风在我国东南沿海登陆。据此完成下面小题。",
        "7. “天鸽” 生成时，东京（东九区）正值（）",
        "A. 凌晨 B. 正午 C. 下午 D. 傍晚",
        "8. 图中表示“天鸽”天气系统的是（）",
        "A.",
        "---",
        '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考地理（教师版）(1)/img_in_image_box_114_100_392_229.jpg" alt="Image" width="23%" /></div>',
        "",
        "",
        '<div style="text-align: center;">B.</div>',
        "",
        "",
        '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考地理（教师版）(1)/img_in_image_box_638_91_857_228.jpg" alt="Image" width="18%" /></div>',
        "",
        "",
        '<div style="text-align: center;">C.</div>',
        "",
        "",
        '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考地理（教师版）(1)/img_in_image_box_142_249_303_384.jpg" alt="Image" width="13%" /></div>',
        "",
        "",
        '<div style="text-align: center;">D.</div>',
        "",
        "",
        '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考地理（教师版）(1)/img_in_image_box_629_250_788_392.jpg" alt="Image" width="13%" /></div>',
        "【答案】",
        "8. C",
    )


def _phy_q12_real_lines():
    """PHY Q12 excerpt from 2018北京夏季高中会考物理 — real OCR markdown."""
    return mk(
        "12. 在图7所示的四幅图中，正确标明了带正电的粒子所受洛伦兹力 f 方向的是",
        "",
        '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考物理（教师版）(1)/img_in_image_box_72_1439_218_1534.jpg" alt="Image" width="12%" /></div>',
        "",
        "",
        '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考物理（教师版）(1)/img_in_image_box_271_1438_419_1532.jpg" alt="Image" width="12%" /></div>',
        "",
        "",
        '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考物理（教师版）(1)/img_in_image_box_460_1441_596_1525.jpg" alt="Image" width="11%" /></div>',
        "",
        "",
        '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考物理（教师版）(1)/img_in_image_box_661_1441_799_1524.jpg" alt="Image" width="11%" /></div>',
        "",
        "A B C 2/11 D",
        '<div style="text-align: center;">图7</div>',
        "【答案】",
        "12. B",
    )


def _payload(qn: str, unit_id: str | None = None):
    uid = unit_id or f"Q{qn}"
    return {
        "semantic_units": [
            {
                "unit_id": uid,
                "unit_type": "standalone_unit",
                "question_number": qn,
                "original_question_type": "single_choice",
                "content": {
                    "stem": {
                        "role": "stem",
                        "question_label": qn,
                    },
                    "options": [
                        {"role": "option", "label": lab, "question_label": qn}
                        for lab in ("A", "B", "C", "D")
                    ],
                    "answer": {
                        "role": "answer",
                        "question_label": qn,
                        "answer_zone": "inline_answer",
                    },
                },
            }
        ]
    }


def _compile(run, payload, lines):
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    line_by_ref = {l.line_ref: l for l in lines}
    span_by_id = {s.span_id: s for s in run.resolved_spans}
    snap = Compiler(span_by_id, line_by_ref).compile(ir)
    return ir, snap


class TestGeoQ8EndToEnd:
    def test_image_options_compile_with_refs_and_order(self):
        lines = _geo_q8_real_lines()
        payload = _payload("8")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
        ir, snap = _compile(run, payload, lines)
        leaves = [l for l in snap.leaves if l.question_number == "8"]
        assert len(leaves) == 1, f"IR status={[u.semantic_status for u in ir.units]}"
        leaf = leaves[0]
        labels = [o.label for o in leaf.options]
        assert labels == ["A", "B", "C", "D"]
        # each option text keeps its own image file — no cross-wiring
        texts = {o.label: o.text for o in leaf.options}
        assert "img_in_image_box_114_100_392_229" in texts["A"]
        assert "img_in_image_box_638_91_857_228" in texts["B"]
        assert "img_in_image_box_142_249_303_384" in texts["C"]
        assert "img_in_image_box_629_250_788_392" in texts["D"]
        # no image appears under two labels
        imgs = []
        for t in texts.values():
            for part in t.split("img_"):
                if part.startswith("in_image_box_"):
                    imgs.append(part.split('"')[0].split("'")[0])
        assert len(imgs) == len(set(imgs)) == 4

    def test_stem_survives_compile(self):
        lines = _geo_q8_real_lines()
        payload = _payload("8")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
        _, snap = _compile(run, payload, lines)
        leaf = next(l for l in snap.leaves if l.question_number == "8")
        assert "天鸽" in leaf.stem.text


class TestPhyQ12EndToEnd:
    def test_positional_image_options_compile(self):
        lines = _phy_q12_real_lines()
        payload = _payload("12")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
        ir, snap = _compile(run, payload, lines)
        leaves = [l for l in snap.leaves if l.question_number == "12"]
        assert len(leaves) == 1, (
            f"IR status={[u.semantic_status for u in ir.units]} "
            f"unresolved={[u for u in run.unresolved_references]}"
        )
        leaf = leaves[0]
        assert [o.label for o in leaf.options] == ["A", "B", "C", "D"]
        texts = {o.label: o.text for o in leaf.options}
        assert "img_in_image_box_72_1439_218_1534" in texts["A"]
        assert "img_in_image_box_271_1438_419_1532" in texts["B"]
        assert "img_in_image_box_460_1441_596_1525" in texts["C"]
        assert "img_in_image_box_661_1441_799_1524" in texts["D"]

    def test_no_label_caption_leaves_incomplete(self):
        raw = [l.text for l in _phy_q12_real_lines()]
        raw[13] = "图7"  # wipe `A B C 2/11 D`
        lines = mk(*raw)
        payload = _payload("12")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
        ir, _ = _compile(run, payload, lines)
        assert ir.units[0].semantic_status != "ready"
        assert not [s for s in run.resolved_spans if ".option." in s.span_id]


class TestTextOptionRegressionE2E:
    def test_text_options_still_compile(self):
        lines = mk(
            "1. 下列哪个是水果",
            "A. 苹果",
            "B. 香蕉",
            "C. 汽车",
            "D. 桌子",
            "【答案】",
            "1. A",
        )
        payload = _payload("1")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
        ir, snap = _compile(run, payload, lines)
        leaves = [l for l in snap.leaves if l.question_number == "1"]
        assert len(leaves) == 1
        assert [o.label for o in leaves[0].options] == ["A", "B", "C", "D"]
        assert leaves[0].options[0].text.strip() in ("苹果", "A. 苹果", "A.苹果")
