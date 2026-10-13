# -*- coding: utf-8 -*-
"""U44-46 Phase 2 — options_range tightening regression tests.

Covers:
- Q44/Q45/Q46 A-D complete
- Q46 exact content (stem/options/answer) with L408 exclusion
- Boundary: options_range only tightens, never expands
- options_range=None preserves current behavior
"""
import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000a")

# Real Geography source lines for U44-46
Q44_STEM = "44\\. 该实验探究的环境问题是"
Q44_OPT1 = "A. 全球变暖 B. 酸雨危害"
Q44_OPT2 = "C. 水土流失 D，物种减少"
Q45_STEM = "45\\. 甲装置实验条件不变，学生对乙装置的操作与观察到的现象对应正确的是"
Q45_A = "A. 减小水量— b 中的水比 a 中的浑浊"
Q45_B = "B，压实泥土— b 中的水比 a 中的浑浊"
Q45_C = "C．加大坡度— b 中的水比 a 中的清澄"
Q45_D = "D．铺设草皮— b 中的水比 a 中的清澄"
Q46_STEM = "46\\. 治理该环境问题的有效措施是"
Q46_OPT = "A. 改善气候 B. 恢复植被 C. 生态移民 D. 陡坡开荒"
Q46_POLLUTION = "A．①②③B．①②④C①③④D．②③④"  # L408 — must NOT enter options


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(qn, opts_range=None, search_lines=None):
    stem = {"role": "stem", "question_label": str(qn)}
    if search_lines:
        stem["question_search_lines"] = list(search_lines)
    content = {
        "stem": stem,
        "options": [{"role": "option", "label": x, "question_label": str(qn)} for x in "ABCD"],
        "answer": {"role": "answer", "answer_zone": "inline_answer", "question_label": str(qn)},
    }
    if opts_range is not None:
        content["options_range"] = list(opts_range)
    return {
        "semantic_units": [{
            "unit_id": f"Q{qn}",
            "unit_type": "standalone_unit",
            "question_number": str(qn),
            "content": content,
        }]
    }


def _resolve(qn, lines, opts_range=None, search_lines=None):
    views = _mk(*lines)
    run = SourceResolver(source_version_id=SVID, lines=views).resolve(
        _payload(qn, opts_range, search_lines))
    line_map = {v.line_ref: v for v in views}
    out = {}
    for s in run.resolved_spans:
        if s.role != "option":
            continue
        lab = s.span_id.rsplit(".", 1)[-1]
        text = line_map[s.start_line_ref].text[s.start_offset:s.end_offset]
        out[lab] = (text, s)
    return out, run


class TestQ44Complete:
    """Q44: A-D complete with fullwidth comma variant."""

    def test_q44_abcd(self):
        lines = [Q44_STEM, "", Q44_OPT1, "", Q44_OPT2]
        opts, _ = _resolve(44, lines, opts_range=(1, 5))
        assert set(opts) == {"A", "B", "C", "D"}, f"got {set(opts)}"
        assert "全球变暖" in opts["A"][0]
        assert "酸雨危害" in opts["B"][0]
        assert "水土流失" in opts["C"][0]
        assert "物种减少" in opts["D"][0]


class TestQ45Complete:
    """Q45: A-D complete with fullwidth comma/period variants."""

    def test_q45_abcd(self):
        lines = [Q45_STEM, "", Q45_A, "", Q45_B, "", Q45_C, "", Q45_D]
        opts, _ = _resolve(45, lines, opts_range=(1, 9))
        assert set(opts) == {"A", "B", "C", "D"}, f"got {set(opts)}"
        assert "减小水量" in opts["A"][0]
        assert "压实泥土" in opts["B"][0]
        assert "加大坡度" in opts["C"][0]
        assert "铺设草皮" in opts["D"][0]


class TestQ46Exact:
    """Q46: exact content with L408 exclusion."""

    def test_q46_abcd_from_l406(self):
        lines = [Q46_STEM, "", Q46_OPT, "", Q46_POLLUTION, "", "47\\. 下一题"]
        opts, _ = _resolve(46, lines, opts_range=(1, 3))
        assert set(opts) == {"A", "B", "C", "D"}, f"got {set(opts)}"
        assert opts["A"][0].strip() == "改善气候", f"A: {opts['A'][0]!r}"
        assert opts["B"][0].strip() == "恢复植被", f"B: {opts['B'][0]!r}"
        assert opts["C"][0].strip() == "生态移民", f"C: {opts['C'][0]!r}"
        assert opts["D"][0].strip() == "陡坡开荒", f"D: {opts['D'][0]!r}"

    def test_q46_l408_not_in_options(self):
        lines = [Q46_STEM, "", Q46_OPT, "", Q46_POLLUTION, "", "47\\. 下一题"]
        opts, _ = _resolve(46, lines, opts_range=(1, 3))
        for lab, (text, span) in opts.items():
            assert "①" not in text, f"Q46.{lab} contains ① from L408: {text!r}"
            assert "②" not in text, f"Q46.{lab} contains ② from L408: {text!r}"
            assert span.start_line_ref == "P1L003", f"Q46.{lab} on {span.start_line_ref}"

    def test_q46_stem_clean(self):
        lines = [Q46_STEM, "", Q46_OPT, "", Q46_POLLUTION, "", "47\\. 下一题"]
        _, run = _resolve(46, lines, opts_range=(1, 3))
        stem = next(s for s in run.resolved_spans if s.role == "stem")
        assert "P1L005" not in stem.line_refs, f"stem includes L5: {stem.line_refs}"
        assert "P1L003" not in stem.line_refs, f"stem includes options: {stem.line_refs}"


class TestBoundaryRegression:
    """options_range only tightens, never expands."""

    def test_tighten_excludes_pollution(self):
        """options_range < region_upper → tighten, exclude L5."""
        lines = [Q46_STEM, "", Q46_OPT, "", Q46_POLLUTION, "", "47\\. 下一题"]
        opts, _ = _resolve(46, lines, opts_range=(1, 3))
        for lab, (text, span) in opts.items():
            assert span.start_line_ref != "P1L005", f"{lab} on L5!"

    def test_no_expand_when_wider(self):
        """options_range wider than region_upper → does NOT expand."""
        lines = [Q46_STEM, "", Q46_OPT, "", Q46_POLLUTION, "", "47\\. 下一题"]
        opts, run = _resolve(46, lines, opts_range=(1, 100))
        # Should still show current behavior (ambiguous from L5) — NOT expanded
        unresolved = {u.reference_id.rsplit(".", 1)[-1] for u in run.unresolved_references
                      if u.role == "option"}
        # Either options found (if HTML table path) or ambiguous/incomplete (current)
        # Key: must NOT have found L5 as a valid option
        for lab, (text, span) in opts.items():
            assert "①" not in text, f"expanded! {lab}: {text!r}"

    def test_none_preserves_current_behavior(self):
        """options_range=None → current behavior (L5 causes ambiguity)."""
        lines = [Q46_STEM, "", Q46_OPT, "", Q46_POLLUTION, "", "47\\. 下一题"]
        opts, run = _resolve(46, lines, opts_range=None)
        unresolved = {u.reference_id.rsplit(".", 1)[-1]: u.resolution_status
                      for u in run.unresolved_references if u.role == "option"}
        # Without options_range, L5 pollutes → A ambiguous or B/C/D incomplete
        # This is the CURRENT behavior that we must preserve
        assert opts == {} or "A" in unresolved or all(
            lab in unresolved for lab in "ABCD"
        ), f"unexpected clean resolve without options_range: opts={set(opts)}"

    def test_standalone_none_unchanged(self):
        """Standalone without options_range: normal inline options still work."""
        lines = ["1\\. stem", "A. 1 B. 2 C. 3 D. 4"]
        opts, _ = _resolve(1, lines, opts_range=None)
        assert set(opts) == {"A", "B", "C", "D"}, f"got {set(opts)}"
        assert opts["A"][0].strip() == "1"
        assert opts["B"][0].strip() == "2"


class TestQ44Q45WithRange:
    """Q44/Q45 with their real options_range values."""

    def test_q44_with_range(self):
        """Q44: options_range=[1,5] covers stem+options, no pollution."""
        lines = [Q44_STEM, "", Q44_OPT1, "", Q44_OPT2, "", "45\\. next"]
        opts, _ = _resolve(44, lines, opts_range=(1, 5))
        assert set(opts) == {"A", "B", "C", "D"}

    def test_q45_with_range(self):
        """Q45: options_range=[1,9] covers stem+options."""
        lines = [Q45_STEM, "", Q45_A, "", Q45_B, "", Q45_C, "", Q45_D]
        opts, _ = _resolve(45, lines, opts_range=(1, 9))
        assert set(opts) == {"A", "B", "C", "D"}
