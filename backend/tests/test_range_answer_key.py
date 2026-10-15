# -*- coding: utf-8 -*-
"""E2E-010R1: range-style answer keys must split per question."""
from __future__ import annotations

from app.domains.resolver.resolver import decode_range_answer_key


class TestRangeAnswerKey:
    def test_single_range_dabca(self):
        raw = "19-23 DABCA 24-28 BDCDA 29-33 BCBDC 34-38 ABDAC"
        assert decode_range_answer_key(raw, "19") == (raw.index("D"), raw.index("D") + 1, "D")
        assert decode_range_answer_key(raw, "20")[2] == "A"
        assert decode_range_answer_key(raw, "23")[2] == "A"
        assert decode_range_answer_key(raw, "24")[2] == "B"
        assert decode_range_answer_key(raw, "38")[2] == "C"

    def test_multi_range_reading(self):
        raw = "39-41 ADC 42-45 ADBB 46-49 AACD 50-53 BACD"
        assert decode_range_answer_key(raw, "39")[2] == "A"
        assert decode_range_answer_key(raw, "41")[2] == "C"
        assert decode_range_answer_key(raw, "42")[2] == "A"
        assert decode_range_answer_key(raw, "45")[2] == "B"
        assert decode_range_answer_key(raw, "50")[2] == "B"
        assert decode_range_answer_key(raw, "53")[2] == "D"

    def test_compact_fgdae_not_range(self):
        # compact key handled elsewhere; range decoder must not mis-read it
        assert decode_range_answer_key("FGDAE", "54") is None

    def test_length_mismatch_fail_closed(self):
        assert decode_range_answer_key("19-23 DABC", "19") is None  # 4 letters, 5 qns
        assert decode_range_answer_key("19-23 DABCAA", "19") is None

    def test_qn_outside_range(self):
        assert decode_range_answer_key("19-23 DABCA", "24") is None

    def test_no_whole_block_repeat(self):
        """Each qn gets a distinct single letter, not the full key."""
        raw = "19-23 DABCA"
        seen = [decode_range_answer_key(raw, str(n))[2] for n in range(19, 24)]
        assert seen == ["D", "A", "B", "C", "A"]
        assert len(set(seen)) >= 2  # not all the same full string

    def test_glued_range_no_space(self):
        """E2E-011: real corpus `21-23DBC` — letters glued to range end."""
        raw = "阅读：21-23DBC 24-27ABBD 28-31CBDC 32-35CBAA 36-40ADCGF"
        assert decode_range_answer_key(raw, "21")[2] == "D"
        assert decode_range_answer_key(raw, "22")[2] == "B"
        assert decode_range_answer_key(raw, "23")[2] == "C"
        assert decode_range_answer_key(raw, "24")[2] == "A"
        assert decode_range_answer_key(raw, "27")[2] == "D"
        assert decode_range_answer_key(raw, "36")[2] == "A"
        assert decode_range_answer_key(raw, "39")[2] == "G"
        assert decode_range_answer_key(raw, "40")[2] == "F"

    def test_glued_multi_range_chain(self):
        """`11-15BABCC16-20BACBC` — consecutive glued ranges on one line."""
        raw = "11-15BABCC16-20BACBC"
        assert decode_range_answer_key(raw, "11")[2] == "B"
        assert decode_range_answer_key(raw, "15")[2] == "C"
        assert decode_range_answer_key(raw, "16")[2] == "B"
        assert decode_range_answer_key(raw, "20")[2] == "C"

    def test_glued_length_mismatch_fail_closed(self):
        assert decode_range_answer_key("21-23DB", "21") is None  # 2 letters, 3 qns

    def test_colon_separator_halfwidth(self):
        """E2E-012: real corpus `56—59:CBBA` — colon between range and letters."""
        raw = "56—59:CBBA 60—63:ACBC 64—67:CBCD 68—71:CBAD 72—75:DAAC"
        assert decode_range_answer_key(raw, "56")[2] == "C"
        assert decode_range_answer_key(raw, "57")[2] == "B"
        assert decode_range_answer_key(raw, "59")[2] == "A"
        assert decode_range_answer_key(raw, "60")[2] == "A"
        assert decode_range_answer_key(raw, "75")[2] == "C"

    def test_colon_separator_fullwidth(self):
        """E2E-012: real corpus `36—40：ABCBA` — fullwidth colon separator."""
        raw = "36—40：ABCBA 41—45:DACDB 46—50:BCADD 51—55:CABAC"
        assert decode_range_answer_key(raw, "36")[2] == "A"
        assert decode_range_answer_key(raw, "40")[2] == "A"
        assert decode_range_answer_key(raw, "41")[2] == "D"
        assert decode_range_answer_key(raw, "55")[2] == "C"
