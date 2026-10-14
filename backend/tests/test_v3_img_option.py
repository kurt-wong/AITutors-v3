# -*- coding: utf-8 -*-
"""V3-IMG-OPTION-001 — image-option structure consumption in the V3 resolver.

Two real shapes:
  GEO Q8  — labels inline / in `<div>` wrappers, each followed by an `<img>` body.
  PHY Q12 — option region is `<img>` rows only; labels sit in a caption row
            (`A B C 2/11 D`) and map positionally to the figure order.

Fail-closed preserved: truncated labels / missing caption / count mismatch
must stay incomplete, never fabricate options.
"""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-000000000011")


def mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def resolver(lines, figures=()):
    return SourceResolver(source_version_id=SVID, lines=lines, figures=figures)


def _geo_q8_lines():
    """GEO Q8 real shape: A. plain, B./C./D. in divs, each followed by <img>."""
    return mk(
        "8. 图中表示天气系统的是（）",                          # L1
        "A.",                                                   # L2
        "---",                                                  # L3
        '<div style="text-align: center;"><img src="a.jpg" alt="Image" /></div>',  # L4
        "",                                                     # L5
        '<div style="text-align: center;">B.</div>',            # L6
        "",                                                     # L7
        '<div style="text-align: center;"><img src="b.jpg" alt="Image" /></div>',  # L8
        "",                                                     # L9
        '<div style="text-align: center;">C.</div>',            # L10
        "",                                                     # L11
        '<div style="text-align: center;"><img src="c.jpg" alt="Image" /></div>',  # L12
        "",                                                     # L13
        '<div style="text-align: center;">D.</div>',            # L14
        "",                                                     # L15
        '<div style="text-align: center;"><img src="d.jpg" alt="Image" /></div>',  # L16
    )


def _phy_q12_lines():
    """PHY Q12 real shape: four <img> option bodies + label caption row."""
    return mk(
        "12. 在图7所示的四幅图中，正确标明方向的是",              # L1
        "",                                                     # L2
        '<div style="text-align: center;"><img src="pA.jpg" /></div>',  # L3
        "",                                                     # L4
        "",                                                     # L5
        '<div style="text-align: center;"><img src="pB.jpg" /></div>',  # L6
        "",                                                     # L7
        "",                                                     # L8
        '<div style="text-align: center;"><img src="pC.jpg" /></div>',  # L9
        "",                                                     # L10
        "",                                                     # L11
        '<div style="text-align: center;"><img src="pD.jpg" /></div>',  # L12
        "",                                                     # L13
        "A B C 2/11 D",                                         # L14 caption
        '<div style="text-align: center;">图7</div>',           # L15
    )


def _payload(qn="8", labels=("A", "B", "C", "D")):
    return {
        "semantic_units": [
            {
                "unit_id": f"Q{qn}",
                "unit_type": "standalone_question",
                "question_number": qn,
                "content": {
                    "stem": {"question_label": qn},
                    "options": [{"label": lab} for lab in labels],
                    "answer": {"answer_zone": "inline_answer", "question_label": qn},
                },
            }
        ]
    }


def _opt_refs(run, unit="Q8"):
    out = {}
    for s in run.resolved_spans:
        if s.span_id.startswith(f"sp-{unit}.option."):
            lab = s.span_id.rsplit(".", 1)[-1]
            out[lab] = list(s.line_refs)
    return out


def _opt_unresolved(run, unit="Q8"):
    out = {}
    for u in run.unresolved_references:
        rid = getattr(u, "reference_id", "") or getattr(u, "target_id", "")
        if rid.startswith(f"ref-{unit}.option.") or rid.startswith(f"{unit}.option."):
            lab = rid.rsplit(".", 1)[-1]
            out[lab] = getattr(u, "reason", None) or getattr(u, "status", None)
    return out


class TestGeoQ8HtmlLabelImageBody:
    def test_html_wrapped_labels_bind_image_bodies(self):
        lines = _geo_q8_lines()
        run = resolver(lines).resolve(_payload("8"))
        refs = _opt_refs(run, "Q8")
        assert set(refs) == {"A", "B", "C", "D"}
        # each option binds its own image row (positional label→image)
        assert refs["A"] == ["P1L004"]
        assert refs["B"] == ["P1L008"]
        assert refs["C"] == ["P1L012"]
        assert refs["D"] == ["P1L016"]

    def test_option_image_refs_preserved(self):
        lines = _geo_q8_lines()
        run = resolver(lines).resolve(_payload("8"))
        by_ref = {l.line_ref: l.text for l in lines}
        for lab, img in [("A", "a.jpg"), ("B", "b.jpg"), ("C", "c.jpg"), ("D", "d.jpg")]:
            refs = _opt_refs(run, "Q8")[lab]
            text = by_ref[refs[0]]
            assert img in text, f"option {lab} must keep its own image ref"

    def test_truncated_d_label_stays_incomplete(self):
        raw = [l.text for l in _geo_q8_lines()]
        raw[13] = ""  # wipe `<div>D.</div>`
        run = resolver(mk(*raw)).resolve(_payload("8"))
        unres = _opt_unresolved(run, "Q8")
        assert "D" in unres
        assert "D" not in _opt_refs(run, "Q8")


class TestPhyQ12ImageOnlyPositional:
    def test_image_only_options_bind_by_caption_order(self):
        lines = _phy_q12_lines()
        run = resolver(lines).resolve(_payload("12"))
        refs = _opt_refs(run, "Q12")
        assert set(refs) == {"A", "B", "C", "D"}
        assert refs["A"] == ["P1L003"]
        assert refs["B"] == ["P1L006"]
        assert refs["C"] == ["P1L009"]
        assert refs["D"] == ["P1L012"]

    def test_caption_image_refs_stay_distinct(self):
        lines = _phy_q12_lines()
        run = resolver(lines).resolve(_payload("12"))
        by_ref = {l.line_ref: l.text for l in lines}
        for lab, img in [("A", "pA.jpg"), ("B", "pB.jpg"), ("C", "pC.jpg"), ("D", "pD.jpg")]:
            assert img in by_ref[_opt_refs(run, "Q12")[lab][0]]

    def test_no_caption_row_stays_incomplete(self):
        raw = [l.text for l in _phy_q12_lines()]
        raw[13] = "图7"  # wipe the A B C D caption
        run = resolver(mk(*raw)).resolve(_payload("12"))
        unres = _opt_unresolved(run, "Q12")
        assert set(unres) == {"A", "B", "C", "D"}

    def test_count_mismatch_stays_incomplete(self):
        raw = [l.text for l in _phy_q12_lines()]
        raw[11] = ""  # drop D image — 3 images vs 4 labels
        run = resolver(mk(*raw)).resolve(_payload("12"))
        unres = _opt_unresolved(run, "Q12")
        assert set(unres) == {"A", "B", "C", "D"}


class TestTextOptionRegression:
    def test_plain_text_options_unchanged(self):
        lines = mk(
            "1. 下列哪个是水果",
            "A. 苹果",
            "B. 香蕉",
            "C. 汽车",
            "D. 桌子",
        )
        run = resolver(lines).resolve(_payload("1"))
        refs = _opt_refs(run, "Q1")
        assert refs == {
            "A": ["P1L002"],
            "B": ["P1L003"],
            "C": ["P1L004"],
            "D": ["P1L005"],
        }

    def test_inline_options_on_one_line_unchanged(self):
        lines = mk(
            "7. 生成时，东京正值（）",
            "A. 凌晨 B. 正午 C. 下午 D. 傍晚",
        )
        run = resolver(lines).resolve(_payload("7"))
        refs = _opt_refs(run, "Q7")
        assert set(refs) == {"A", "B", "C", "D"}
