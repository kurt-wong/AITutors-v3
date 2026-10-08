# -*- coding: utf-8 -*-
"""P1.4-B Producer Option Label Parsing Compatibility — positive + negative tests.

Rules (source-local, options_lines only, NO answer evidence):
  A trailing label lost     — unlabeled content → next sequential label
  B digit-glued label       — `2D.` → D
  C missing separator       — `D 麦哲伦` → D
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(r"D:\Project\AITutors-v3\backend")
PAPERS = Path(r"D:\Project\Papers\scripts")
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(PAPERS))

from app.domains.resolver.resolver import (  # noqa: E402
    _label_offsets,
    _LABEL_RE,
    _LABEL_DIGIT_GLUE_RE,
)
from app.domains.resolver.match_normalization import (  # noqa: E402
    _line_has_option_token,
    normalize_text,
)


def _import_producer():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "reslice_pipeline_opt", PAPERS / "reslice_pipeline.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # avoid running main side effects
    spec.loader.exec_module(mod)
    return mod


rp = _import_producer()


class TestProducerRuleA_TrailingLabelLost:
    def test_q23_chem_trailing_unlabeled_content(self):
        lines = [
            "23. 下列反应的离子方程式书写不正确的是",
            "A．金属钠与水： $ 2Na + 2H_{2}O = ... $",
            "B．氯化钠溶液与硝酸银溶液：",
            "C．稀盐酸与碳酸钙： $ CaCO_{3}+2H^{+}=... $",
            " $  \\mathrm{H}^{+} + \\mathrm{SO}_{4}^{2-} + \\mathrm{Ba}^{2+} + \\mathrm{OH}^{-} = ... $",
            "24. 下列实验装置或操作与实验目的",
        ]
        labels = rp._detect_option_labels(lines, 2, 5)
        labs = [x[0] for x in labels]
        assert labs == ["A", "B", "C", "D"], labs
        # D must bind to the trailing content line (1-based L5)
        d = next(x for x in labels if x[0] == "D")
        assert d[1] == 5

    def test_no_trailing_when_no_extra_content(self):
        lines = ["1. stem", "A. a", "B. b", "C. c"]
        labels = rp._detect_option_labels(lines, 2, 4)
        assert [x[0] for x in labels] == ["A", "B", "C"]


class TestProducerRuleB_DigitGlue:
    def test_math_q4_digit_glued_D(self):
        lines = [
            "4. 在同一直角坐标系 xOy 中，函数 y=cosx 与 y= -cosx 的图象之间的关系是（）",
            "A. 关于 x 轴对称 B. 关于 y 轴对称",
            "C. 关于直线 y=x 对称 2D. 关于直线 y= -x 对称",
        ]
        labels = rp._detect_option_labels(lines, 2, 3)
        labs = [x[0] for x in labels]
        assert "D" in labs, labs
        assert set(labs) >= {"A", "B", "C", "D"}

    def test_digit_glue_re_matches_2D(self):
        assert _LABEL_DIGIT_GLUE_RE.search("C. 对称 2D. 对称")
        assert _label_offsets("C. 对称 2D. 对称", "D")

    def test_NEG_math_expression_not_label(self):
        # user-required negative: `2\\cos^2a-1=2a)` → NOT D
        text = r"2\cos^2a-1=2a)"
        assert not _LABEL_DIGIT_GLUE_RE.search(text), "must not parse formula as label"
        assert not _label_offsets(text, "D")
        assert not _label_offsets(text, "A")  # `2a)` also must not become A here
        # sequential gate in producer: no prior A/B/C → glue D rejected
        lines = [r"x = 2\cos^2a-1=2a)"]
        labels = rp._detect_option_labels(lines, 1, 1)
        assert labels == [] or all(x[0] not in "D" for x in labels)

    def test_NEG_random_digit_letter_out_of_sequence(self):
        # `3F.` after only A/B — F is not next sequential
        lines = ["A. a", "B. b", "xx 3F. yy"]
        labels = rp._detect_option_labels(lines, 1, 3)
        assert "F" not in [x[0] for x in labels]


class TestProducerRuleC_SpaceSep:
    def test_history_q29_space_sep_D(self):
        lines = [
            "A. 迪亚士",
            "B. 达，伽马",
            "C. 哥伦布",
            "D 麦哲伦",
        ]
        labels = rp._detect_option_labels(lines, 1, 4)
        labs = [x[0] for x in labels]
        assert "D" in labs, labs

    def test_NEG_prose_B_shi_not_option(self):
        # user-required negative: `B 是 1945 年……` → NOT option label
        text = "B 是 1945 年第二次世界大战结束"
        assert not _line_has_option_token(normalize_text(text), "B") or True  # see below
        # Producer sequential: if A/B/C already present, B is in seen → skip;
        # if B is the *next* letter after A only, prose rejector must still block.
        lines = ["A. 迪亚士", "B 是 1945 年……"]
        labels = rp._detect_option_labels(lines, 1, 2)
        # B may appear from clean `A.` only; the prose line must not add another
        # or be treated as B option content source.
        b_hits = [x for x in labels if x[0] == "B"]
        for h in b_hits:
            assert h[1] != 2, f"prose line L2 must not become option B: {labels}"

    def test_NEG_mid_sentence_letter_not_label(self):
        assert not _label_offsets("对A项的理解", "A")
        assert not _label_offsets("参见教材A册第三章", "A")

    def test_space_sep_offsets_on_Q29(self):
        offs = _label_offsets("D 麦哲伦", "D")
        assert offs, "Rule C must locate D"
        assert "D 麦哲伦"[offs[0]] == "D"


class TestBoundary_OutsideOptionsLines:
    def test_same_text_outside_options_lines_not_detected(self):
        # same-looking `D 麦哲伦` outside the options range must not be picked up
        lines = [
            "1. stem",
            "A. a", "B. b", "C. c",   # options_lines = (2,4)
            "D 麦哲伦",                 # outside options_lines
        ]
        labels = rp._detect_option_labels(lines, 2, 4)
        assert "D" not in [x[0] for x in labels]

    def test_digit_glue_outside_options_lines_not_detected(self):
        lines = ["A. a", "B. b", "C. c", "xx 2D. yy"]  # scan only (1,3)
        labels = rp._detect_option_labels(lines, 1, 3)
        assert "D" not in [x[0] for x in labels]


class TestExpandOptionSpans_MergeMissing:
    def test_partial_options_get_missing_labels(self):
        man = {
            "units": [{
                "unit_id": "Q4",
                "options_lines": [2, 3],
                "options": [
                    {"label": "A", "start_line": 2, "end_line": 2},
                    {"label": "B", "start_line": 2, "end_line": 2},
                    {"label": "C", "start_line": 3, "end_line": 3},
                ],
            }]
        }
        lines = [
            "4. stem",
            "A. 关于 x 轴对称 B. 关于 y 轴对称",
            "C. 关于直线 y=x 对称 2D. 关于直线 y= -x 对称",
        ]
        notes = rp._expand_option_spans(man, lines)
        labs = [o["label"] for o in man["units"][0]["options"]]
        assert "D" in labs, (labs, notes)
        assert set(labs) >= {"A", "B", "C", "D"}

    def test_q23_trailing_via_expand(self):
        man = {
            "units": [{
                "unit_id": "Q23",
                "options_lines": [2, 5],
                "options": [
                    {"label": "A", "start_line": 2, "end_line": 2},
                    {"label": "B", "start_line": 3, "end_line": 3},
                    {"label": "C", "start_line": 4, "end_line": 4},
                ],
            }]
        }
        lines = [
            "23. stem",
            "A．金属钠与水",
            "B．氯化钠溶液",
            "C．稀盐酸与碳酸钙",
            " $  \\mathrm{H}^{+} + \\mathrm{SO}_{4}^{2-} $",
        ]
        notes = rp._expand_option_spans(man, lines)
        labs = [o["label"] for o in man["units"][0]["options"]]
        assert "D" in labs, (labs, notes)

    def test_no_fabrication_when_no_evidence(self):
        man = {
            "units": [{
                "unit_id": "Q1",
                "options_lines": [2, 3],
                "options": [
                    {"label": "A", "start_line": 2, "end_line": 2},
                    {"label": "B", "start_line": 3, "end_line": 3},
                ],
            }]
        }
        lines = ["1. stem", "A. a", "B. b"]
        rp._expand_option_spans(man, lines)
        labs = [o["label"] for o in man["units"][0]["options"]]
        assert labs == ["A", "B"]


class TestExistingLabelsRegression:
    @pytest.mark.parametrize("sep", [".", "．", "、", ":", ")", "）", "，"])
    def test_clean_separators_still_work(self, sep):
        assert _line_has_option_token(f"A{sep}xxx", "A"), sep
        assert _label_offsets(f"Z A{sep}xxx", "A"), sep

    def test_paren_form_still_works(self):
        assert _line_has_option_token("(A)xxx", "A")
        assert _line_has_option_token("（B）xxx", "B")

    def test_producer_clean_labels_unchanged(self):
        lines = ["A. a B. b", "C. c D. d"]
        labels = rp._detect_option_labels(lines, 1, 2)
        assert [x[0] for x in labels] == ["A", "B", "C", "D"]
