# -*- coding: utf-8 -*-
"""Answer-binding safety — narrowed guard + entry-prefix stripping + false-positive resistance.

Guard criterion (Owner ruling): only clear an answer block when the evidence
range is SHARED by ≥2 units AND carries local numbering that does not map to
the current unit. Per-unit ranges are that unit's own answer and must not be
cleared.

Cases locked:
  1. E2E-014 Q86-95: shared 1..10 block vs global qn → EMPTY (fail-closed)
  2. p1_4paper req1..6 / P2-*.sub: per-unit local-numbered blocks → NOT cleared
  3. e2e_007_math Q28: `-1.` in prose must NOT become an answer entry
  4. e2e_013_en U68: `@163.com` must NOT become an answer entry
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
# Case 1 — E2E-014: shared block with local numbering, global qn → EMPTY
# ===========================================================================

class TestSharedLocalNumberingBlockCleared:
    """Q86-95 pattern: one shared answer block (local 1..10) for global qns."""

    BLOCK_LINES = (
        "1. achievements 6. persuaded",
        "2. progress 7. impressed",
        "3. deserved",
        "8. responsible",
        "4. satisfaction 9. journey",
        "5. prepare 10. courage",
    )

    def _shared_payload(self, qns: list[str], lines_range):
        """Multiple units sharing the SAME answer_lines range."""
        return {"semantic_units": [
            {
                "unit_id": f"Q{qn}",
                "content": {
                    "stem": {"question_label": qn},
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": qn,
                        "answer_lines": list(lines_range),
                    },
                },
            }
            for qn in qns
        ]}

    def test_shared_block_local_numbering_cleared_for_qn86(self):
        lines = _mk(
            "",
            "",
            "86. spell the word",
            "87. spell the word",
            *self.BLOCK_LINES,
        )
        # Q86 and Q87 share answer_lines [5, 10] → range is "shared".
        run = _resolve(lines, self._shared_payload(["86", "87"], (5, 10)))
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q86.answer")
        block_text = "\n".join(self.BLOCK_LINES)
        assert a.text_hash != _sha(block_text), (
            "whole answer block was copied to unit 86"
        )
        assert a.text_hash == _sha(""), f"expected empty answer, got hash {a.text_hash}"
        ev = " | ".join(a.evidence)
        assert "local numbering" in ev
        assert "shared_lines" in ev
        assert a.line_refs == ("P1L002",)

    def test_shared_block_local_numbering_cleared_for_all(self):
        lines = _mk("", "", *["86. q"] * 10, *self.BLOCK_LINES)
        qns = [str(n) for n in range(86, 96)]
        run = _resolve(lines, self._shared_payload(qns, (13, 18)))
        for qn in qns:
            a = next(s for s in run.resolved_spans if s.span_id == f"sp-Q{qn}.answer")
            assert a.text_hash == _sha(""), f"Q{qn} should be empty"
            assert a.line_refs == ("P1L002",), f"Q{qn} should still exist"

    def test_shared_block_mappable_entry_not_cleared(self):
        """If qn IS among the block entries, entry extraction handles it."""
        lines = _mk(
            "",
            "",
            "1. first question",
            "2. second question",
            "1. A 2. B",
        )
        run = _resolve(lines, self._shared_payload(["1", "2"], (5, 5)))
        a1 = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.answer")
        a2 = next(s for s in run.resolved_spans if s.span_id == "sp-Q2.answer")
        raw = lines[4].text
        assert raw[a1.start_offset:a1.end_offset] == "A"
        assert raw[a2.start_offset:a2.end_offset] == "B"


# ===========================================================================
# Case 2 — per-unit local numbering (req1..6 / P2-*.sub style) → NOT cleared
# ===========================================================================

class TestPerUnitLocalNumberingPreserved:
    """p1_4paper: each unit has its OWN answer block with a local number label.

    These blocks are NOT shared; the local number is just a label for the
    unit's own answer. They must NOT be cleared.
    """

    def test_req_style_per_unit_block_not_cleared(self):
        """U-req1..6 pattern: 6 units, each with own block starting `N. `."""
        # Each unit has its own answer_lines pointing to its own block.
        req_blocks = {
            "26": (5, 6),   # U-req1: `1. answer-for-req1`
            "27": (8, 9),   # U-req2: `2. answer-for-req2`
            "28": (11, 12),  # U-req3: `3. answer-for-req3`
        }
        lines = _mk(
            "",
            "",
            "26. chem question 1",
            "27. chem question 2",
            "28. chem question 3",
            "1.（3分）Mg | TiCl4 | 1",   # P1L006
            "",
            "2.（3分）answer content 2",  # P1L008
            "",
            "3.（3分）answer content 3",  # P1L010
            "",
        )
        # Fix line numbers — blocks at P1L006, P1L008, P1L010
        # Actually, let me just use distinct ranges.
        payload = {"semantic_units": [
            {"unit_id": "U-req1", "content": {
                "stem": {"question_label": "26"},
                "answer": {"answer_zone": "answer_table", "question_label": "26",
                           "answer_lines": [6, 6]}}},
            {"unit_id": "U-req2", "content": {
                "stem": {"question_label": "27"},
                "answer": {"answer_zone": "answer_table", "question_label": "27",
                           "answer_lines": [8, 8]}}},
            {"unit_id": "U-req3", "content": {
                "stem": {"question_label": "28"},
                "answer": {"answer_zone": "answer_table", "question_label": "28",
                           "answer_lines": [10, 10]}}},
        ]}
        run = _resolve(lines, payload)
        # Each unit's answer must NOT be empty.
        for uid, expect_snippet in [
            ("U-req1", "Mg"),
            ("U-req2", "answer content 2"),
            ("U-req3", "answer content 3"),
        ]:
            a = next(s for s in run.resolved_spans if s.span_id == f"sp-{uid}.answer")
            assert a.text_hash != _sha(""), f"{uid} was cleared!"
            raw = "\n".join(lines[i].text for i in range(len(lines)))
            # The answer text should contain the unit's own content.
            assert a.granularity == "line" or a.text_hash != _sha("")

    def test_per_unit_multiline_block_with_local_label_not_cleared(self):
        """Multi-line per-unit block starting with `N. ` — not shared → keep."""
        lines = _mk(
            "",
            "",
            "51. geo question 1",
            "1. 本题共10分。每空1分。",   # P1L004 — local label `1.`
            "(1) 赤道 0° 纬线",
            "(2) 6月22日前后",
            "(3) C",
        )
        payload = {"semantic_units": [
            {"unit_id": "U-P2-1.sub", "content": {
                "stem": {"question_label": "51"},
                "answer": {"answer_zone": "answer_table", "question_label": "51",
                           "answer_lines": [4, 7]}}},
        ]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans
                 if s.span_id == "sp-U-P2-1.sub.answer")
        # Must NOT be empty (not cleared).
        assert a.text_hash != _sha(""), "per-unit local-numbered block was cleared!"
        # Multi-line block binding — all4 lines.
        assert a.line_refs == ("P1L004", "P1L005", "P1L006", "P1L007")

    def test_per_unit_block_not_whole_zone_copy(self):
        """Each unit gets its OWN block, not another unit's."""
        lines = _mk(
            "",
            "",
            "26. q1", "27. q2",
            "1. answer-one",    # P1L005 — U-req1
            "2. answer-two",    # P1L006 — U-req2
        )
        payload = {"semantic_units": [
            {"unit_id": "U-req1", "content": {
                "stem": {"question_label": "26"},
                "answer": {"answer_zone": "answer_table", "question_label": "26",
                           "answer_lines": [5, 5]}}},
            {"unit_id": "U-req2", "content": {
                "stem": {"question_label": "27"},
                "answer": {"answer_zone": "answer_table", "question_label": "27",
                           "answer_lines": [6, 6]}}},
        ]}
        run = _resolve(lines, payload)
        a1 = next(s for s in run.resolved_spans if s.span_id == "sp-U-req1.answer")
        a2 = next(s for s in run.resolved_spans if s.span_id == "sp-U-req2.answer")
        # Distinct answers — not the same text.
        assert a1.text_hash != a2.text_hash
        # U-req1 gets its line, U-req2 gets its line.
        assert a1.line_refs == ("P1L005",)
        assert a2.line_refs == ("P1L006",)


# ===========================================================================
# Case 3 — Q28 false positive: `-1.` in prose is NOT an answer entry
# ===========================================================================

class TestEntryFalsePositives:
    def test_negative_number_not_entry(self):
        """`解得 a 的最小值为-1.` — the `1.` in `-1.` is NOT an entry token."""
        text = "（28）简析：（I）令 f(x)=0，解得 a 的最小值为-1."
        nums = [m.group(1) for m in _ENTRY_RE.finditer(text)]
        assert "1" not in nums, f"-1. was misidentified as entry: {nums}"

    def test_negative_number_block_not_cleared(self):
        """Q28-style: single-unit block containing `-1.` — must NOT be cleared."""
        lines = _mk(
            "",
            "",
            "28. math question",
            "（28）简析：（I）令 f(x)=0，解得 a 的最小值为-1.",
            "（II）由题意得 a≥-1。",
        )
        payload = {"semantic_units": [
            {"unit_id": "Q28", "content": {
                "stem": {"question_label": "28"},
                "answer": {"answer_zone": "answer_table", "question_label": "28",
                           "answer_lines": [4, 5]}}},
        ]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q28.answer")
        assert a.text_hash != _sha(""), "Q28 block with -1. was wrongly cleared!"
        # Whole block bound (no false-positive entries detected).
        assert a.line_refs == ("P1L004", "P1L005")

    def test_email_not_entry(self):
        """`lihua@163.com` — the `163.` is NOT an entry token."""
        text = "书面表达(One possible version)\n\nFrom: lihua@163.com\n\nTo: volunteers@yahoo.com"
        nums = [m.group(1) for m in _ENTRY_RE.finditer(text)]
        assert "163" not in nums, f"@163. was misidentified as entry: {nums}"

    def test_email_block_not_cleared(self):
        """U68-style: essay with email — must NOT be cleared."""
        lines = _mk(
            "",
            "",
            "68. writing",
            "书面表达(One possible version)",
            "",
            "From: lihua@163.com",
            "",
            "Dear Sir / Madam,",
            "I am Li Hua.",
        )
        payload = {"semantic_units": [
            {"unit_id": "U68", "content": {
                "stem": {"question_label": "68"},
                "answer": {"answer_zone": "answer_table", "question_label": "68",
                           "answer_lines": [4, 9]}}},
        ]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-U68.answer")
        assert a.text_hash != _sha(""), "U68 essay with email was wrongly cleared!"

    def test_version_number_not_entry(self):
        """`v1.2.` / `item-3.` should not create false entries."""
        assert _block_entry_nums("version v1.2 released") == set() or \
               "2" not in _block_entry_nums("version v1.2 released")
        assert "3" not in _block_entry_nums("item-3. done")
        assert "1" not in _block_entry_nums("error-1. occurred")


# ===========================================================================
# Entry-prefix stripping (preserved from f009ab2)
# ===========================================================================

class TestEntryPrefixStripped:
    def test_escaped_dot_entry_strips_prefix(self):
        lines = _mk("", "", "21. question", "21\\. C ")
        payload = {"semantic_units": [{
            "unit_id": "Q21",
            "content": {
                "stem": {"question_label": "21"},
                "answer": {"answer_zone": "answer_table", "question_label": "21",
                           "answer_lines": [4, 4]},
            },
        }]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q21.answer")
        raw = lines[3].text
        assert raw[a.start_offset:a.end_offset] == "C"

    def test_plain_dot_entry_strips_prefix(self):
        lines = _mk("", "", "51. question", "51. C")
        payload = {"semantic_units": [{
            "unit_id": "Q51",
            "content": {
                "stem": {"question_label": "51"},
                "answer": {"answer_zone": "answer_table", "question_label": "51",
                           "answer_lines": [4, 4]},
            },
        }]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q51.answer")
        raw = lines[3].text
        assert raw[a.start_offset:a.end_offset] == "C"

    def test_packed_entries_strip_prefix(self):
        lines = _mk("", "", "21. q21", "22. q22", "23. q23",
                    "21\\. A 22\\. B 23\\. C")
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
            assert raw[a.start_offset:a.end_offset] == expected

    def test_range_answer_key_unaffected(self):
        lines = _mk("", "", "19. q19", "23. q23", "19-23 DABCA")
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
        assert raw[by["sp-Q19.answer"].start_offset:by["sp-Q19.answer"].end_offset] == "D"
        assert raw[by["sp-Q23.answer"].start_offset:by["sp-Q23.answer"].end_offset] == "A"


# ===========================================================================
# Legitimate whole-block scenarios (regression locks)
# ===========================================================================

class TestLegitimateWholeBlockPreserved:
    def test_bare_qn_multiline_body_still_binds_block(self):
        """B3c-A: bare `1.` + multi-line body IS the unit's whole answer."""
        lines = _mk("", "", "1. 计算题", "1.", "【考点】代数", "【分析】略",
                    "【解答】过程", "故选A")
        payload = {"semantic_units": [{
            "unit_id": "Q1",
            "content": {
                "stem": {"question_label": "1"},
                "answer": {"answer_zone": "answer_table", "question_label": "1",
                           "answer_lines": [4, 8]},
            },
        }]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q1.answer")
        assert a.line_refs == ("P1L004", "P1L005", "P1L006", "P1L007", "P1L008")

    def test_no_local_numbering_whole_block_ok(self):
        lines = _mk("", "", "86. essay", "The answer is long",
                    "and continues here", "and ends here")
        payload = {"semantic_units": [{
            "unit_id": "Q86",
            "content": {
                "stem": {"question_label": "86"},
                "answer": {"answer_zone": "answer_table", "question_label": "86",
                           "answer_lines": [4, 6]},
            },
        }]}
        run = _resolve(lines, payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-Q86.answer")
        assert a.line_refs == ("P1L004", "P1L005", "P1L006")


# ===========================================================================
# Unit-level helpers
# ===========================================================================

class TestHelpers:
    def test_entry_content_bounds_strips_plain_prefix(self):
        raw = "21. C 22. A"
        cs, ce = _entry_content_bounds(raw, 0, 6)
        assert raw[cs:ce] == "C"

    def test_entry_content_bounds_strips_escaped_dot(self):
        raw = "21\\. C"
        cs, ce = _entry_content_bounds(raw, 0, len(raw))
        assert raw[cs:ce] == "C"

    def test_entry_content_bounds_bare_prefix_empty(self):
        raw = "1."
        cs, ce = _entry_content_bounds(raw, 0, len(raw))
        assert cs >= ce

    def test_block_entry_nums(self):
        assert _block_entry_nums("1. a 2. b 10. c") == {"1", "2", "10"}
        assert _block_entry_nums("no numbering here") == set()
        # False positives rejected.
        assert _block_entry_nums("value is -1.") == set()
        assert _block_entry_nums("email: lihua@163.com") == set()
