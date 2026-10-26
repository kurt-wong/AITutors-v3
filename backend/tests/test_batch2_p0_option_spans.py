# -*- coding: utf-8 -*-
"""BATCH2-P0 span regression locks — four student-visible option fixes.

Locked shapes (source lines from t179 packages):
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

import pytest

sys.path.insert(0, r"D:\Project\AITutors-v3\backend")

from app.domains.resolver.resolver import SourceResolver  # noqa: E402
from app.domains.resolver.span import SourceLineView  # noqa: E402

SVID = uuid.UUID("00000000-0000-0000-0000-000000000011")

CHEM = Path(
    r"D:\Project\AITutor-X\e2e_run\t179_packages\chemistry\paper.md"
).read_text(encoding="utf-8").splitlines()
PHYS = Path(
    r"D:\Project\AITutor-X\e2e_run\t179_packages\physics\paper.md"
).read_text(encoding="utf-8").splitlines()
MAE = Path(
    r"D:\Project\AITutor-X\e2e_run\t179_packages\math_v27_ae\paper.md"
).read_text(encoding="utf-8").splitlines()


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
        lines = _lines(CHEM[185:196], 186)
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
        lines = _lines(PHYS[190:235], 191)
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
        lines = _lines(CHEM[148:162], 149)
        run = _resolve(lines, "Q20", "20")
        spans = _opt_spans(run, "Q20")
        assert "E" not in spans, f"fake option E appeared: {list(spans)}"
        d_refs = list(spans["D"].line_refs)
        assert d_refs == ["P1L157", "P1L159"], f"D must span L157+L159, got {d_refs}"
        d_txt = _span_text(lines, spans["D"])
        assert "还原反应" in d_txt, f"D lost continuation: {d_txt!r}"

    def test_q25_four_short_options_split_by_char_range(self):
        """MAE Q25: A/B/C/D → 9/8/6/4 as separate char spans; no section header."""
        lines = _lines(MAE[139:160], 140)
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
