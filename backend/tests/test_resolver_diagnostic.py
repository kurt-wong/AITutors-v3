"""Diagnostic Layer 测试（Phase I-2C-2）。"""

from __future__ import annotations

import uuid

from app.domains.resolver.diagnostic import (
    CandidateLine,
    DiagnosticReport,
    MatchAttempt,
    UnresolvedDiagnostic,
    classify_unresolved,
    diagnose_unresolved,
    format_diagnostic_report,
    _attempt_match,
    _find_candidate_lines,
)
from app.domains.resolver.span import (
    ResolvedRun,
    SourceLineView,
    UnresolvedReference,
)


def _make_lines(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(line_ref=f"P1L{i:03d}", text=t, seq=i, page_no=1, line_no_in_page=i)
        for i, t in enumerate(texts, 1)
    )


class TestMatchAttempt:
    def test_exact_found(self):
        lines = _make_lines("hello world", "foo bar")
        attempts = _attempt_match("hello", lines)
        exact = next(a for a in attempts if a.method == "exact")
        assert exact.result == "found"
        assert exact.hit_count == 1

    def test_exact_not_found(self):
        lines = _make_lines("hello world", "foo bar")
        attempts = _attempt_match("xyz", lines)
        exact = next(a for a in attempts if a.method == "exact")
        assert exact.result == "not_found"
        assert exact.hit_count == 0

    def test_exact_multiple(self):
        lines = _make_lines("hello world", "say hello", "hello again")
        attempts = _attempt_match("hello", lines)
        exact = next(a for a in attempts if a.method == "exact")
        assert exact.result == "multiple_matches"
        assert exact.hit_count == 3

    def test_normalized_found(self):
        lines = _make_lines("ＨＥＬＬＯ world")  # full-width
        attempts = _attempt_match("HELLO", lines)
        norm = next(a for a in attempts if a.method == "normalized")
        assert norm.result == "found"

    def test_fuzzy_found(self):
        lines = _make_lines("hello  world")  # double space
        attempts = _attempt_match("hello world", lines)
        fuzzy = next(a for a in attempts if a.method == "fuzzy")
        assert fuzzy.result == "found"


class TestCandidateLines:
    def test_partial_match(self):
        lines = _make_lines("sinα=1/2", "cosβ=√3/2", "unrelated text")
        candidates = _find_candidate_lines("sinα=1/2", lines)
        assert len(candidates) > 0
        assert candidates[0].line_ref == "P1L001"

    def test_no_match(self):
        lines = _make_lines("hello", "world")
        candidates = _find_candidate_lines("xyz123", lines)
        assert len(candidates) == 0

    def test_overlap_threshold(self):
        lines = _make_lines("abc", "def")
        candidates = _find_candidate_lines("abc", lines)
        assert len(candidates) > 0


class TestClassifyUnresolved:
    def test_marker_not_found(self):
        ref = UnresolvedReference("ref-1", "stem", "missing", ("not found",))
        attempts = (
            MatchAttempt("exact", "not_found", 0),
            MatchAttempt("normalized", "not_found", 0),
            MatchAttempt("fuzzy", "not_found", 0),
        )
        result = classify_unresolved(ref, attempts, ())
        assert result == "marker_not_found"

    def test_marker_fragmented(self):
        ref = UnresolvedReference("ref-1", "stem", "missing", ("not found",))
        attempts = (
            MatchAttempt("exact", "not_found", 0),
            MatchAttempt("normalized", "not_found", 0),
            MatchAttempt("fuzzy", "not_found", 0),
        )
        candidates = (CandidateLine("P1L001", "sin", "partial", 3),)
        result = classify_unresolved(ref, attempts, candidates)
        assert result == "marker_fragmented"

    def test_marker_ambiguous(self):
        ref = UnresolvedReference("ref-1", "stem", "ambiguous", ("multiple",))
        attempts = (
            MatchAttempt("exact", "multiple_matches", 2, ("P1L001", "P1L002")),
            MatchAttempt("normalized", "not_found", 0),
            MatchAttempt("fuzzy", "not_found", 0),
        )
        result = classify_unresolved(ref, attempts, ())
        assert result == "marker_ambiguous"

    def test_grammar_mismatch(self):
        ref = UnresolvedReference("ref-1", "answer", "missing", ("header not found",))
        attempts = ()
        result = classify_unresolved(ref, attempts, ())
        assert result == "grammar_mismatch"


class TestDiagnoseUnresolved:
    def test_empty_unresolved(self):
        svid = uuid.uuid4()
        run = ResolvedRun(source_version_id=svid)
        lines = _make_lines("hello")
        report = diagnose_unresolved(run, lines)
        assert report.total_unresolved == 0
        assert report.by_classification == {}

    def test_with_unresolved(self):
        svid = uuid.uuid4()
        ref = UnresolvedReference("ref-1", "stem", "missing", ("not found",))
        run = ResolvedRun(
            source_version_id=svid,
            unresolved_references=(ref,),
        )
        lines = _make_lines("hello world", "foo bar")
        report = diagnose_unresolved(run, lines)
        assert report.total_unresolved == 1
        assert report.by_role.get("stem") == 1

    def test_format_report(self):
        svid = uuid.uuid4()
        ref = UnresolvedReference("ref-1", "stem", "missing", ("not found",))
        run = ResolvedRun(
            source_version_id=svid,
            unresolved_references=(ref,),
        )
        lines = _make_lines("hello")
        report = diagnose_unresolved(run, lines)
        formatted = format_diagnostic_report(report)
        assert "source_version_id" in formatted
        assert "total_unresolved" in formatted
        assert "diagnostics" in formatted
        assert len(formatted["diagnostics"]) == 1
