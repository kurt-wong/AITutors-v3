# -*- coding: utf-8 -*-
"""E2E-006 — stem contamination after image-option rebind.

Real cases: GEO Q8 stem had trailing `A.` + `---`; Q10 trailing `A.`;
Q32 trailing `---`. After rebind, the original label/pad rows must NOT be
swallowed into the stem.
"""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-000000000041")


def mk(*texts: str):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(qn="8"):
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


def _stem_text(run, lines, unit="Q8"):
    for s in run.resolved_spans:
        if s.span_id == f"sp-{unit}.stem":
            return "\n".join(lines[i - 1] if isinstance(lines[i - 1], str) else lines[i - 1].text
                             for i in range(1, len(lines) + 1)
                             if f"P1L{i:03d}" in s.line_refs)
    return ""


def _stem_refs(run, unit="Q8"):
    for s in run.resolved_spans:
        if s.span_id == f"sp-{unit}.stem":
            return list(s.line_refs)
    return []


class TestQ8StemContamination:
    """GEO Q8 real shape: `A.` / `---` / `<img>` — stem must not eat A./---."""

    def test_stem_excludes_label_and_pad_after_rebind(self):
        lines = mk(
            "8. 图中表示天气系统的是（）",                              # L1
            "A.",                                                   # L2 label
            "---",                                                  # L3 pad
            '<div><img src="a.jpg" /></div>',                        # L4 A body
            '<div>B.</div>',                                        # L5 label
            '<div><img src="b.jpg" /></div>',                        # L6 B body
            '<div>C.</div>',                                        # L7
            '<div><img src="c.jpg" /></div>',                        # L8
            '<div>D.</div>',                                        # L9
            '<div><img src="d.jpg" /></div>',                        # L10
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("8"))
        stem = _stem_text(run, [l.text for l in lines], "Q8")
        assert "图中表示" in stem
        assert "A." not in stem, f"stem leaked label A: {stem!r}"
        assert "---" not in stem, f"stem leaked pad: {stem!r}"
        # stem should be just the question line
        refs = _stem_refs(run, "Q8")
        assert refs == ["P1L001"], f"stem refs={refs}"

    def test_q8_options_still_bind_images(self):
        lines = mk(
            "8. 图中表示天气系统的是（）",
            "A.",
            "---",
            '<div><img src="a.jpg" /></div>',
            '<div>B.</div>',
            '<div><img src="b.jpg" /></div>',
            '<div>C.</div>',
            '<div><img src="c.jpg" /></div>',
            '<div>D.</div>',
            '<div><img src="d.jpg" /></div>',
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("8"))
        by_id = {s.span_id: list(s.line_refs) for s in run.resolved_spans}
        assert by_id["sp-Q8.option.A"] == ["P1L004"]
        assert by_id["sp-Q8.option.B"] == ["P1L006"]
        assert by_id["sp-Q8.option.C"] == ["P1L008"]
        assert by_id["sp-Q8.option.D"] == ["P1L010"]


class TestQ10StemContamination:
    """GEO Q10 shape: trailing `A.` only (no ---)."""

    def test_stem_excludes_trailing_label_only(self):
        lines = mk(
            "10. 茶叶的运动轨迹模拟的是",
            "A.",
            '<div><img src="a.jpg" /></div>',
            '<div>B.</div>',
            '<div><img src="b.jpg" /></div>',
            '<div>C.</div>',
            '<div><img src="c.jpg" /></div>',
            '<div>D.</div>',
            '<div><img src="d.jpg" /></div>',
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("10"))
        stem = _stem_text(run, [l.text for l in lines], "Q10")
        assert "茶叶" in stem
        assert "A." not in stem, f"stem leaked A: {stem!r}"
        assert _stem_refs(run, "Q10") == ["P1L001"]


class TestQ32StemContamination:
    """GEO Q32 shape: trailing `---` only (separator after text options)."""

    def test_stem_excludes_trailing_pad_only(self):
        lines = mk(
            "32. 某地植被类型是",
            "---",
            "A. 热带雨林",
            "B. 常绿阔叶林",
            "C. 针叶林",
            "D. 草原",
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("32"))
        stem = _stem_text(run, [l.text for l in lines], "Q32")
        assert "植被" in stem
        assert "---" not in stem, f"stem leaked pad: {stem!r}"
        assert _stem_refs(run, "Q32") == ["P1L001"]


class TestNoRegression:
    def test_text_options_stem_clean(self):
        lines = mk(
            "1. 下列哪个是水果",
            "A. 苹果",
            "B. 香蕉",
            "C. 汽车",
            "D. 桌子",
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("1"))
        stem = _stem_text(run, [l.text for l in lines], "Q1")
        assert "水果" in stem
        assert "苹果" not in stem
        assert _stem_refs(run, "Q1") == ["P1L001"]

    def test_mixed_text_image_stem_clean(self):
        lines = mk(
            "5. 选择正确项",
            "A. 甲",
            "B. 乙",
            '<div><img src="c.jpg" /></div>',
            '<div>D.</div>',
            '<div><img src="d.jpg" /></div>',
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_payload("5"))
        stem = _stem_text(run, [l.text for l in lines], "Q5")
        assert "选择" in stem
        assert "A." not in stem
        assert "D." not in stem
