"""Phase I-4: Evidence-aware diagnostic 测试。"""

from __future__ import annotations

import pytest

from app.domains.resolver.evidence import (
    EvidenceCandidate,
    EvidenceReport,
    SpanEvidence,
    analyze_evidence,
    format_evidence_report,
    score_candidate,
)
from app.domains.resolver.span import SourceLineView


def _make_line(ref: str, text: str, seq: int = 1, page: int = 1) -> SourceLineView:
    return SourceLineView(line_ref=ref, text=text, seq=seq, page_no=page)


def _make_span(
    ref: str,
    text: str,
    seq: int = 0,
    font: str | None = "Helvetica",
    size: float | None = 12.0,
    flags: int | None = 0,
    bbox: dict | None = None,
) -> SpanEvidence:
    return SpanEvidence(
        line_ref=ref, seq=seq, text=text, font=font, size=size, flags=flags, bbox=bbox
    )


class TestSpanEvidence:
    def test_bold_flag(self):
        span = _make_span("P1L001", "1", flags=32)
        assert span.is_bold is True

    def test_not_bold(self):
        span = _make_span("P1L001", "1", flags=0)
        assert span.is_bold is False

    def test_superscript_flag(self):
        span = _make_span("P1L001", "2", flags=1)
        assert span.is_superscript is True

    def test_bbox_area(self):
        span = _make_span("P1L001", "1", bbox={"x0": 0, "y0": 0, "x1": 10, "y1": 10})
        assert span.bbox_area == 100.0

    def test_bbox_area_none(self):
        span = _make_span("P1L001", "1", bbox=None)
        assert span.bbox_area is None

    def test_bbox_area_missing_keys(self):
        span = _make_span("P1L001", "1", bbox={"x0": 0})
        assert span.bbox_area is None


class TestScoreCandidate:
    def test_isolated_span_scores_higher(self):
        """孤立 span 行比多 span 行分数高。"""
        line = _make_line("P1L001", "1")
        isolated = (_make_span("P1L001", "1"),)
        multi = (
            _make_span("P1L001", "1"),
            _make_span("P1L001", "."),
            _make_span("P1L001", " "),
            _make_span("P1L001", "A"),
            _make_span("P1L001", "B"),
        )
        c1 = score_candidate(line, isolated, "1", "exact")
        c2 = score_candidate(line, multi, "1", "exact")
        assert c1.evidence_score > c2.evidence_score

    def test_exact_text_match_scores_highest(self):
        """line text 精确等于 marker → 最高分。"""
        line_exact = _make_line("P1L001", "1")
        line_prefix = _make_line("P1L002", "1. A")
        spans = (_make_span("P1L001", "1"),)
        c1 = score_candidate(line_exact, spans, "1", "exact")
        c2 = score_candidate(line_prefix, spans, "1", "exact")
        assert c1.evidence_score > c2.evidence_score

    def test_bold_scores_higher(self):
        """粗体 span 比非粗体分数高。"""
        line = _make_line("P1L001", "1")
        bold_spans = (_make_span("P1L001", "1", flags=32),)
        normal_spans = (_make_span("P1L001", "1", flags=0),)
        c1 = score_candidate(line, bold_spans, "1", "exact")
        c2 = score_candidate(line, normal_spans, "1", "exact")
        assert c1.evidence_score > c2.evidence_score

    def test_small_bbox_scores_higher(self):
        """小 bbox 面积比大 bbox 分数高。"""
        line = _make_line("P1L001", "1")
        small = (_make_span("P1L001", "1", bbox={"x0": 0, "y0": 0, "x1": 10, "y1": 10}),)
        large = (_make_span("P1L001", "1", bbox={"x0": 0, "y0": 0, "x1": 200, "y1": 200}),)
        c1 = score_candidate(line, small, "1", "exact")
        c2 = score_candidate(line, large, "1", "exact")
        assert c1.evidence_score > c2.evidence_score

    def test_empty_spans_fallback(self):
        """无 spans → 仍能评分（fallback 到 line-level）。"""
        line = _make_line("P1L001", "1")
        c = score_candidate(line, (), "1", "exact")
        assert c.span_count == 0
        assert c.is_isolated is False
        assert c.evidence_score > 0  # exact_text_match 仍给分

    def test_score_reasons_recorded(self):
        """评分原因被记录。"""
        line = _make_line("P1L001", "1")
        spans = (_make_span("P1L001", "1", flags=32, bbox={"x0": 0, "y0": 0, "x1": 5, "y1": 5}),)
        c = score_candidate(line, spans, "1", "exact")
        assert "isolated_span" in c.score_reasons
        assert "exact_text_match" in c.score_reasons
        assert "bold" in c.score_reasons
        assert "small_bbox" in c.score_reasons


class TestAnalyzeEvidence:
    def test_single_candidate_unique(self):
        """只有一个候选 → unique_with_evidence = True。"""
        lines = (_make_line("P1L001", "1"),)
        spans = {"P1L001": (_make_span("P1L001", "1"),)}
        report = analyze_evidence("Q1.stem", "1", lines, spans)
        assert report.total_candidates == 1
        assert report.unique_with_evidence is True
        assert report.top_candidate is not None

    def test_multiple_candidates_ranked(self):
        """多个候选按 score 降序排列。"""
        lines = (
            _make_line("P1L001", "1. A. B", seq=1),
            _make_line("P1L002", "1", seq=2),
            _make_line("P1L003", "第1题", seq=3),
        )
        spans = {
            "P1L001": (
                _make_span("P1L001", "1"),
                _make_span("P1L001", "."),
                _make_span("P1L001", " A"),
            ),
            "P1L002": (_make_span("P1L002", "1"),),
            "P1L003": (_make_span("P1L003", "第1题"),),
        }
        report = analyze_evidence("Q1.stem", "1", lines, spans)
        assert report.total_candidates == 3
        # P1L002 应该排第一（isolated + exact_text_match）
        assert report.candidates[0].line_ref == "P1L002"

    def test_evidence_gap_determines_uniqueness(self):
        """top 和 second 分差 > 0.2 → unique。"""
        lines = (
            _make_line("P1L001", "1", seq=1),
            _make_line("P1L002", "1. A. B. C. D", seq=2),
        )
        spans = {
            "P1L001": (_make_span("P1L001", "1", flags=32),),  # bold + isolated
            "P1L002": (
                _make_span("P1L002", "1"),
                _make_span("P1L002", "."),
                _make_span("P1L002", " A"),
                _make_span("P1L002", "."),
                _make_span("P1L002", " B"),
            ),
        }
        report = analyze_evidence("Q1.stem", "1", lines, spans)
        assert report.total_candidates == 2
        # P1L001: isolated(0.3) + few_spans(0.1) + small_bbox(?) + bold(0.1) + exact(0.35)
        # P1L002: no isolated, no bold, no exact
        assert report.unique_with_evidence is True

    def test_no_candidates(self):
        """无匹配 → empty report。"""
        lines = (_make_line("P1L001", "hello"),)
        spans: dict[str, tuple[SpanEvidence, ...]] = {}
        report = analyze_evidence("Q1.stem", "1", lines, spans)
        assert report.total_candidates == 0
        assert report.top_candidate is None
        assert report.unique_with_evidence is False

    def test_empty_marker_returns_no_candidates(self):
        """空 marker 不得匹配所有行（§10.6 防御边界）。"""
        lines = (
            _make_line("P1L001", "hello", seq=1),
            _make_line("P1L002", "world", seq=2),
            _make_line("P1L003", "3", seq=3),
        )
        spans = {
            "P1L001": (_make_span("P1L001", "hello"),),
            "P1L002": (_make_span("P1L002", "world"),),
            "P1L003": (_make_span("P1L003", "3"),),
        }
        report = analyze_evidence("Q1.stem", "", lines, spans)
        assert report.total_candidates == 0
        assert report.top_candidate is None
        assert report.unique_with_evidence is False

    def test_whitespace_marker_returns_no_candidates(self):
        """纯空白 marker 同样不得匹配任何行。"""
        lines = (_make_line("P1L001", "hello"),)
        spans = {"P1L001": (_make_span("P1L001", "hello"),)}
        report = analyze_evidence("Q1.stem", "   ", lines, spans)
        assert report.total_candidates == 0

    def test_normalized_match(self):
        """全角字符 normalized match。"""
        lines = (_make_line("P1L001", "１"),)  # 全角 1
        spans = {"P1L001": (_make_span("P1L001", "１"),)}
        report = analyze_evidence("Q1.stem", "1", lines, spans)
        assert report.total_candidates >= 1


class TestFormatEvidenceReport:
    def test_serializable(self):
        """format_evidence_report 返回 JSON-compatible dict。"""
        lines = (_make_line("P1L001", "1"),)
        spans = {"P1L001": (_make_span("P1L001", "1"),)}
        report = analyze_evidence("Q1.stem", "1", lines, spans)
        d = format_evidence_report(report)
        assert d["reference_id"] == "Q1.stem"
        assert d["marker"] == "1"
        assert d["total_candidates"] == 1
        assert d["unique_with_evidence"] is True
        assert d["top_candidate"]["line_ref"] == "P1L001"
        assert len(d["candidates"]) == 1

    def test_empty_report_serializable(self):
        lines = (_make_line("P1L001", "hello"),)
        spans: dict[str, tuple[SpanEvidence, ...]] = {}
        report = analyze_evidence("Q1.stem", "1", lines, spans)
        d = format_evidence_report(report)
        assert d["total_candidates"] == 0
        assert d["top_candidate"] is None
