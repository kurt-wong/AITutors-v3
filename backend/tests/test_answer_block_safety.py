# -*- coding: utf-8 -*-
"""E2E-014 answer-binding safety.

Two independent defects fixed together:
  1. Multi-line answer blocks with LOCAL numbering (1., 2., …) must NOT be
     copied whole into every unit when the unit uses GLOBAL numbering (86-95).
  2. Entry-style answer keys (`21\\. C`) must have the `N.` / `N\\.` prefix
     stripped at binding time so the stored answer text is just `C`.
"""
from __future__ import annotations

import hashlib
import uuid

from app.domains.resolver.resolver import (
    SourceResolver,
    _ENTRY_RE,
    _entry_content_bounds,
    _block_entry_nums,
)
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000b1")


def _mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _resolve(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)


# ===========================================================================
# A. Local-numbering block must not be copied into global-numbered units
# ===========================================================================

class TestLocalNumberingBlockNotCopied:
    """Q86-95 pattern: answer_lines = [local 1-10 block], unit qn = 86."""

    BLOCK_LINES = (
        "1. achievements 6. persuaded",
        "2. progress 7. impressed",
        "3. deserved",
        "8. responsible",
        "4. satisfaction 9. journey",
        "5. prepare 10. courage",
    )

    def _payload(self, qn: str, lines_range):
        return {"semantic_units": [{
            "unit_id": f"Q{qn}",
            "content": {
                "stem": {"question_label": qn},
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": qn,
                    "answer_lines": list(lines_range),
                },
            },
        }]}

    def test_block_with_local_numbering_not_copied_to_qn86(self):
        # P1L001 blank (so P1L002 convention holds for empty-answer span),
        # stems, then the shared answer block at P1L004-P1L009.
        lines = _mk(
            "",                           # P1L001
            "86. spell the word",          # P1L002 — careful: NOT blank!
            "",                           # P1L003
            *self.BLOCK_LINES,            # P1L004-P1L009
        )
        # Re-mk so P1L002 is blank (conventional OCR layout).
        lines = _mk(
            "",
            "",
            "86. spell the word",
            *self.BLOCK_LINES,
        )
        run = _resolve(lines, self._payload("86", (4, 9)))
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q86.answer")
        block_text = "\n".join(self.BLOCK_LINES)
        # Must NOT be the whole block.
        assert a.text_hash != _sha(block_text), (
            "whole answer block was copied to unit 86"
        )
        # Must be an empty (absent) answer — fail-closed, not wrong data.
        assert a.text_hash == _sha(""), f"expected empty answer, got hash {a.text_hash}"
        # Evidence records why.
        ev = " | ".join(a.evidence)
        assert "local numbering" in ev
        # Span exists → question/unit preserved for human verification.
        assert a.resolution_status == "exact"
        assert a.line_refs == ("P1L002",)

    def test_block_with_local_numbering_not_copied_to_qn90(self):
        lines = _mk(
            "",
            "",
            "90. spell the word",
            *self.BLOCK_LINES,
        )
        run = _resolve(lines, self._payload("90", (4, 9)))
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q90.answer")
        assert a.text_hash == _sha("")

    def test_legitimate_bare_qn_multiline_body_still_binds_block(self):
        """B3c-A: bare `1.` + multi-line body IS the unit's whole answer."""
        lines = _mk(
            "",
            "",
            "1. 计算题题干",
            "1.",              # bare entry — body on subsequent lines
            "【考点】代数",
            "【分析】略",
            "【解答】过程",
            "故选A",
        )
        payload = {"semantic_units": [{
            "unit_id": "Q1",
            "content": {
                "stem": {"question_label": "1"},
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "1",
                    "answer_lines": [4, 8],
                },
            },
        }]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.answer")
        # Whole range bound (B3c-A full-range).
        assert a.line_refs == ("P1L004", "P1L005", "P1L006", "P1L007", "P1L008")

    def test_no_local_numbering_whole_block_ok(self):
        """A multi-line answer with no entry numbers is one answer — keep block."""
        lines = _mk(
            "",
            "",
            "86. essay question",
            "The answer is long",
            "and continues here",
            "and ends here",
        )
        run = _resolve(lines, self._payload("86", (4, 6)))
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q86.answer")
        assert a.line_refs == ("P1L004", "P1L005", "P1L006")

    def test_single_line_local_numbering_not_copied(self):
        """Single-line evidence with local entries for OTHER qns must not bind."""
        lines = _mk(
            "",
            "",
            "99. question ninety-nine",
            "1.C 2.B 3.C 4.D",
        )
        run = _resolve(lines, self._payload("99", (4, 4)))
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q99.answer")
        # Not the whole line.
        assert a.text_hash != _sha("1.C 2.B 3.C 4.D")
        assert a.text_hash == _sha("")


# ===========================================================================
# B. Entry-style answer keys: strip N. / N\\. prefix at binding
# ===========================================================================

class TestEntryPrefixStripped:
    def test_escaped_dot_entry_strips_prefix(self):
        """`21\\. C ` → `C`  (E2E-014 approved-answer cleanliness)."""
        lines = _mk(
            "",
            "",
            "21. question twenty-one",
            "21\\. C ",
        )
        payload = {"semantic_units": [{
            "unit_id": "Q21",
            "content": {
                "stem": {"question_label": "21"},
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "21",
                    "answer_lines": [4, 4],
                },
            },
        }]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q21.answer")
        raw = lines[3].text
        content = raw[a.start_offset:a.end_offset]
        assert content == "C", f"expected 'C', got {content!r}"

    def test_plain_dot_entry_strips_prefix(self):
        lines = _mk(
            "",
            "",
            "51. question fifty-one",
            "51. C",
        )
        payload = {"semantic_units": [{
            "unit_id": "Q51",
            "content": {
                "stem": {"question_label": "51"},
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "51",
                    "answer_lines": [4, 4],
                },
            },
        }]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q51.answer")
        raw = lines[3].text
        content = raw[a.start_offset:a.end_offset]
        assert content == "C", f"expected 'C', got {content!r}"

    def test_packed_entries_strip_prefix(self):
        """`21\\. A 22\\. B 23\\. C` — each unit gets clean letter."""
        lines = _mk(
            "",
            "",
            "21. q21", "22. q22", "23. q23",
            "21\\. A 22\\. B 23\\. C",
        )
        payload = {"semantic_units": [
            {"unit_id": "Q21", "content": {
                "stem": {"question_label": "21"},
                "answer": {"answer_zone": "answer_table", "question_label": "21",
                           "answer_lines": [6, 6]}}},
            {"unit_id": "Q22", "content": {
                "stem": {"question_label": "22"},
                "answer": {"answer_zone": "answer_table", "question_label": "22",
                           "answer_lines": [6, 6]}}},
            {"unit_id": "Q23", "content": {
                "stem": {"question_label": "23"},
                "answer": {"answer_zone": "answer_table", "question_label": "23",
                           "answer_lines": [6, 6]}}},
        ]}
        run = _resolve(lines, payload)
        by = {s.span_id: s for s in run.resolved_spans}
        raw = lines[5].text
        for qn, expected in [("21", "A"), ("22", "B"), ("23", "C")]:
            a = by[f"sp-Q{qn}.answer"]
            content = raw[a.start_offset:a.end_offset]
            assert content == expected, f"Q{qn}: expected {expected!r}, got {content!r}"

    def test_range_answer_key_unaffected(self):
        """Range keys (`19-23 DABCA`) already bind clean letters — no change."""
        lines = _mk(
            "",
            "",
            "19. q19", "23. q23",
            "19-23 DABCA",
        )
        payload = {"semantic_units": [
            {"unit_id": "Q19", "content": {
                "stem": {"question_label": "19"},
                "answer": {"answer_zone": "answer_table", "question_label": "19",
                           "answer_lines": [5, 5]}}},
            {"unit_id": "Q23", "content": {
                "stem": {"question_label": "23"},
                "answer": {"answer_zone": "answer_table", "question_label": "23",
                           "answer_lines": [5, 5]}}},
        ]}
        run = _resolve(lines, payload)
        by = {s.span_id: s for s in run.resolved_spans}
        raw = lines[4].text
        a19 = by["sp-Q19.answer"]
        a23 = by["sp-Q23.answer"]
        assert raw[a19.start_offset:a19.end_offset] == "D"
        assert raw[a23.start_offset:a23.end_offset] == "A"


# ===========================================================================
# Unit-level helpers
# ===========================================================================

class TestEntryContentBounds:
    def test_strips_plain_prefix(self):
        raw = "21. C 22. A"
        # entry for 21 starts at 0, ends at start of 22
        cs, ce = _entry_content_bounds(raw, 0, 6)
        assert raw[cs:ce] == "C"

    def test_strips_escaped_dot_prefix(self):
        raw = "21\\. C"
        cs, ce = _entry_content_bounds(raw, 0, len(raw))
        assert raw[cs:ce] == "C"

    def test_bare_prefix_empty_content(self):
        raw = "1."
        cs, ce = _entry_content_bounds(raw, 0, len(raw))
        assert cs >= ce  # zero-width → empty content

    def test_block_entry_nums(self):
        assert _block_entry_nums("1. a 2. b 10. c") == {"1", "2", "10"}
        assert _block_entry_nums("no numbering here") == set()
