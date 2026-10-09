# -*- coding: utf-8 -*-
"""Task A — option content-span assertions (content interval, not shell count)."""
from __future__ import annotations
import sys, uuid

sys.path.insert(0, r"D:\Project\AITutors-v3\backend")

from app.domains.compile.compiler import _slice_span
from app.domains.resolver.resolver import SourceResolver, _option_content_bounds
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000a")


def _mk(*texts):
    return tuple(SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1) for i, t in enumerate(texts))


def _resolve_option_texts(payload, lines):
    views = _mk(*lines)
    run = SourceResolver(source_version_id=SVID, lines=views).resolve(payload)
    line_map = {v.line_ref: v for v in views}
    out = {}
    for s in run.resolved_spans:
        if s.role != "option":
            continue
        lab = s.span_id.rsplit(".", 1)[-1]
        out[lab] = _slice_span(s, line_map)
    return out


def _payload(unit_id, qn):
    return {
        "semantic_units": [{
            "unit_id": unit_id,
            "unit_type": "standalone_unit",
            "question_number": qn,
            "content": {
                "stem": {"role": "stem", "question_label": qn},
                "options": [{"role": "option", "label": x} for x in "ABCD"],
                "answer": {"role": "answer", "answer_zone": "inline_answer", "question_label": qn},
            },
        }]
    }


class TestContentBounds:
    def test_math_q1_single_line(self):
        line = "A. 1 B. 2 C.  $ \\pi $ D.  $ 2\\pi $"
        for lab, expect in [("A", "1"), ("B", "2")]:
            b = _option_content_bounds(line, lab)
            assert line[b[0]:b[1]].strip() == expect, (lab, line[b[0]:b[1]])

    def test_q4_digit_glue(self):
        line = "C. 关于直线 y=x 对称 2D. 关于直线 y= -x 对称"
        bC = _option_content_bounds(line, "C")
        bD = _option_content_bounds(line, "D")
        assert line[bC[0]:bC[1]].strip() == "关于直线 y=x 对称", line[bC[0]:bC[1]]
        assert line[bD[0]:bD[1]].strip() == "关于直线 y= -x 对称", line[bD[0]:bD[1]]

    def test_space_sep(self):
        line = "D 麦哲伦"
        b = _option_content_bounds(line, "D")
        assert line[b[0]:b[1]].strip() == "麦哲伦"


class TestE2EContentSpan:
    def test_math_q1_content_intervals(self):
        d = _resolve_option_texts(_payload("Q1", "1"), [
            "1. 函数  $ y=3\\sin x+2 $ 的最小正周期是（）",
            "A. 1 B. 2 C.  $ \\pi $ D.  $ 2\\pi $",
        ])
        assert set(d) == {"A", "B", "C", "D"}
        assert d["A"].strip() == "1", d["A"]
        assert d["B"].strip() == "2", d["B"]
        assert "pi" in d["C"].replace("\\", "") or "π" in d["C"], d["C"]
        assert "B." not in d["A"], d["A"]
        assert "A." not in d["A"]

    def test_labels_A_to_D_no_dup(self):
        d = _resolve_option_texts(_payload("Q1", "1"), [
            "1. stem",
            "A. 1 B. 2 C. 3 D. 4",
        ])
        labels = list(d)
        assert labels == ["A", "B", "C", "D"], labels
        assert len(labels) == len(set(labels))

    def test_math_q4_cross_line(self):
        d = _resolve_option_texts(_payload("Q4", "4"), [
            "4. 在同一直角坐标系 xOy 中，函数 y=cosx 与 y= -cosx 的图象之间的关系是（）",
            "A. 关于 x 轴对称 B. 关于 y 轴对称",
            "C. 关于直线 y=x 对称 2D. 关于直线 y= -x 对称",
        ])
        assert d["A"].strip() == "关于 x 轴对称", d["A"]
        assert d["B"].strip() == "关于 y 轴对称", d["B"]
        assert d["C"].strip() == "关于直线 y=x 对称", d["C"]
        assert d["D"].strip() == "关于直线 y= -x 对称", d["D"]
        assert "2D." not in d["C"]
        assert "B." not in d["A"]

    def test_q17_H_not_injected(self):
        d = _resolve_option_texts(_payload("Q17", "17"), [
            "17. 下列电子式正确的是",
            "A. Cl: Cl",
            "B. H: O: H",
            "C. Na: Cl:",
            "D. H: N: H",
        ])
        labels = list(d)
        assert set(labels) <= {"A", "B", "C", "D"}, labels
        assert "O" in d["B"] or ":" in d["B"], d["B"]
        assert "H:" not in d["B"] or d["B"].strip().startswith("H") is False or "O" in d["B"]
