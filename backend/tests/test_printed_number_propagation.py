# -*- coding: utf-8 -*-
"""P1 — printed_number → question_label_printed propagation for basis=shift units.

Covers:
- Shift basis: printed=N, global=M (N≠M) → stem uses printed for source matching
- Keep basis: printed==global → behavior unchanged
- Missing printed_number → fallback to global (existing behavior)
"""
import pytest

from app.domains.resolver.reference import extract_targets
from app.domains.resolver.resolver import _line_has_question_entry


# ═══════════════════════════════════════════════════════════════
# A. Shift basis: printed_number reaches ResolveTarget
# ═══════════════════════════════════════════════════════════════

class TestShiftBasisPropagation:
    """printed=1..6, global=26..31 → question_label_printed set correctly."""

    @pytest.mark.parametrize("printed,global_qn", [
        (1, 26), (2, 27), (3, 28), (4, 29), (5, 30), (6, 31),
    ])
    def test_shift_basis_printed_reaches_target(self, printed, global_qn):
        payload = {"semantic_units": [{
            "unit_id": f"U-req{printed}",
            "content": {"stem": {
                "role": "stem",
                "question_label": str(global_qn),
                "question_label_printed": str(printed),
            }},
        }]}
        targets = extract_targets(payload)
        stem_targets = [t for t in targets if t.kind == "question_label"]
        assert len(stem_targets) == 1
        assert stem_targets[0].question_label_printed == str(printed)
        assert stem_targets[0].question_number == str(global_qn)

    def test_resolver_prefers_printed_over_global(self):
        """search_qn = question_label_printed or qn — printed wins."""
        payload = {"semantic_units": [{
            "unit_id": "U-req1",
            "content": {"stem": {
                "role": "stem",
                "question_label": "26",
                "question_label_printed": "1",
            }},
        }]}
        t = next(iter(extract_targets(payload)))
        # Simulate resolver line 608
        search_qn = t.question_label_printed or t.question_number
        assert search_qn == "1"

    def test_source_entry_match_with_printed(self):
        """Source line '1. (3分)C919...' matches printed=1, not global=26."""
        source_line = "1. （3分）中国首款完全自主知识产权民用客机C919"
        assert _line_has_question_entry(source_line, "1")
        assert not _line_has_question_entry(source_line, "26")

    @pytest.mark.parametrize("printed,global_qn,source_line", [
        ("1", "26", "1. （3分）C919钛合金"),
        ("2", "27", "2. （3分）Mg与稀硫酸"),
        ("3", "28", "3. （3分）某反应"),
        ("4", "29", "4. （3分）某溶液"),
        ("5", "30", "5. （3分）某实验"),
        ("6", "31", "6. （3分）某元素"),
    ])
    def test_all_six_shift_units_match(self, printed, global_qn, source_line):
        assert _line_has_question_entry(source_line, printed), source_line
        assert not _line_has_question_entry(source_line, global_qn), source_line


# ═══════════════════════════════════════════════════════════════
# B. Keep basis: printed == global → unchanged
# ═══════════════════════════════════════════════════════════════

class TestKeepBasisUnchanged:
    @pytest.mark.parametrize("qn", ["1", "9", "19", "24", "25"])
    def test_keep_basis_printed_equals_global(self, qn):
        payload = {"semantic_units": [{
            "unit_id": f"Q{qn}",
            "content": {"stem": {
                "role": "stem",
                "question_label": qn,
                "question_label_printed": qn,
            }},
        }]}
        t = next(iter(extract_targets(payload)))
        search_qn = t.question_label_printed or t.question_number
        assert search_qn == qn

    def test_keep_basis_no_printed_falls_back(self):
        """When printed_number is absent, falls back to global qn."""
        payload = {"semantic_units": [{
            "unit_id": "Q1",
            "content": {"stem": {
                "role": "stem",
                "question_label": "1",
            }},
        }]}
        t = next(iter(extract_targets(payload)))
        assert t.question_label_printed is None
        search_qn = t.question_label_printed or t.question_number
        assert search_qn == "1"


# ═══════════════════════════════════════════════════════════════
# C. Missing printed-number → fallback unchanged
# ═══════════════════════════════════════════════════════════════

class TestMissingPrintedFallback:
    def test_no_printed_uses_global(self):
        """Without question_label_printed, resolver uses question_label."""
        payload = {"semantic_units": [{
            "unit_id": "Q9",
            "content": {"stem": {
                "role": "stem",
                "question_label": "9",
            }},
        }]}
        t = next(iter(extract_targets(payload)))
        assert t.question_label_printed is None
        assert (t.question_label_printed or t.question_number) == "9"

    def test_empty_string_printed_falls_back(self):
        """question_label_printed = '' should not override."""
        payload = {"semantic_units": [{
            "unit_id": "Q1",
            "content": {"stem": {
                "role": "stem",
                "question_label": "1",
                "question_label_printed": "",
            }},
        }]}
        t = next(iter(extract_targets(payload)))
        # "" is falsy — `or` falls back to question_number
        assert (t.question_label_printed or t.question_number) == "1"
