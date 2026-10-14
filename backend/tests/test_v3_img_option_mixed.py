# -*- coding: utf-8 -*-
"""DSH §7.1 risk — `_locate_image_only_options` wholesale replacement.

Reproduce the mixed-option hazard: some labels already bound to text, others
need image rows; options window happens to carry exactly N `<img>` rows and a
caption row lists all N labels. The current code replaces the whole `found`
map, which would clobber correct text bindings.
"""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-000000000031")


def mk(*texts: str):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(qn="1"):
    return {
        "semantic_units": [
            {
                "unit_id": f"Q{qn}",
                "unit_type": "standalone_question",
                "question_number": qn,
                "content": {
                    "stem": {"question_label": qn},
                    "options": [{"label": lab} for lab in ("A", "B", "C", "D")],
                    "answer": {"answer_zone": "inline_answer", "question_label": qn},
                },
            }
        ]
    }


def _opt_refs(run, unit="Q1"):
    out = {}
    for s in run.resolved_spans:
        if s.span_id.startswith(f"sp-{unit}.option."):
            out[s.span_id.rsplit(".", 1)[-1]] = list(s.line_refs)
    return out


class TestMixedTextImageWholesaleReplace:
    def test_resolved_text_options_survive_image_only_fallback(self):
        """A/B are text and must NOT be clobbered by positional image mapping.

        Layout: A./B. text, then 4 `<img>` rows (2 option bodies + 2 figures),
        then a caption `A B C D`. Image count (4) == label count (4), caption
        lists all labels — the exact trigger DSH flagged.
        """
        lines = mk(
            "1. 下列说法正确的是",                                          # L1
            "A. 苹果",                                                       # L2 text option A
            "B. 香蕉",                                                       # L3 text option B
            '<div><img src="fig_intro.jpg" /></div>',                        # L4 figure (not option)
            '<div><img src="fig_extra.jpg" /></div>',                        # L5 figure (not option)
            '<div><img src="opt_c.jpg" /></div>',                            # L6 option C body
            '<div><img src="opt_d.jpg" /></div>',                            # L7 option D body
            "A B C 2/11 D",                                                  # L8 caption
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("1"))
        refs = _opt_refs(run, "Q1")
        # A and B must keep their text rows — never rebound to figures
        assert refs.get("A") == ["P1L002"], f"A clobbered: {refs.get('A')}"
        assert refs.get("B") == ["P1L003"], f"B clobbered: {refs.get('B')}"
        # C and D may bind their own image rows (or stay incomplete) but must
        # not be assigned the intro/extra figures
        for lab, bad in [("C", "fig_intro"), ("D", "fig_extra")]:
            if lab in refs:
                joined = refs[lab]
                assert joined != ["P1L004"] or lab != "C"
                assert joined != ["P1L005"] or lab != "D"

    def test_all_image_options_still_bind_positionally(self):
        """Pure image-option case (PHY Q12 shape) must keep working."""
        lines = mk(
            "12. 四幅图中正确的是",
            '<div><img src="pA.jpg" /></div>',
            '<div><img src="pB.jpg" /></div>',
            '<div><img src="pC.jpg" /></div>',
            '<div><img src="pD.jpg" /></div>',
            "A B C 2/11 D",
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("12"))
        refs = _opt_refs(run, "Q12")
        assert refs["A"] == ["P1L002"]
        assert refs["B"] == ["P1L003"]
        assert refs["C"] == ["P1L004"]
        assert refs["D"] == ["P1L005"]

    def test_stem_figure_does_not_count_as_option_image(self):
        """Stem illustration + 3 option images must not fake a 4-image match."""
        lines = mk(
            "1. 如图所示",
            '<div><img src="stem_fig.jpg" /></div>',                         # stem figure
            "A. 甲",
            "B. 乙",
            "C. 丙",
            '<div><img src="opt_d.jpg" /></div>',                            # only D is an image
            "A B C D",
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("1"))
        refs = _opt_refs(run, "Q1")
        assert refs.get("A") == ["P1L003"]
        assert refs.get("B") == ["P1L004"]
        assert refs.get("C") == ["P1L005"]
        # D may bind opt_d.jpg; A/B/C must never become stem_fig
        for lab in ("A", "B", "C"):
            assert refs.get(lab) != ["P1L002"]
