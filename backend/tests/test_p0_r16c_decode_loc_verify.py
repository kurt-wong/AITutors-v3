"""R16c-FIX: decode_loc must not self-prove ownership.

DSH R16c counterexamples (all must reject):
  range-answer-mismatch  ['19-23 DABCA']  qn19  cell:D  text:A  → unknown / verify False
  entry-cell-mismatch    ['19. D']        qn19  cell:Z  text:Z  → unknown / verify False
  range-no-letters       ['19-23']        qn19  cell:Z  text:Z  → unknown / verify False

Positive controls (must still match):
  range-consistent       ['19-23 DABCA']  qn19  cell:D  text:D  → match
  entry-cell-consistent  ['19. D']        qn19  cell:D  text:D  → match
  compact / table / real entry                                     → match
"""
from __future__ import annotations

from app.domains.gate.binding_fact import (
    _classify,
    _fact_from_mapping,
    derive_binding_fact,
    verify_binding_fact,
)

SVID = "00000000-0000-0000-0000-00000000c001"


# ── DSH R16c three counterexamples ────────────────────────────────────


def test_range_answer_mismatch_rejected():
    """cell:D + text:A on '19-23 DABCA' — answer body contradicts cell."""
    own = _classify(["19-23 DABCA"], "19", "qn:19|cell:D", answer_text="A")
    assert own == "unknown", f"expected unknown, got {own}"

    fact = derive_binding_fact(
        span_id="sp-rm",
        source_version_id=SVID,
        unit_id="Q19",
        question_number="19",
        source_lines=["19-23 DABCA"],
        answer_text="A",
        decode_loc="qn:19|cell:D",
    )
    assert fact.ownership == "unknown", fact.ownership
    assert verify_binding_fact(fact) is False, (
        "fact with cell:D + text:A must fail verification"
    )


def test_entry_cell_mismatch_rejected():
    """cell:Z on '19. D' — source letter is D, not Z."""
    own = _classify(["19. D"], "19", "qn:19|cell:Z", answer_text="Z")
    assert own == "unknown", f"expected unknown, got {own}"

    fact = derive_binding_fact(
        span_id="sp-em",
        source_version_id=SVID,
        unit_id="Q19",
        question_number="19",
        source_lines=["19. D"],
        answer_text="Z",
        decode_loc="qn:19|cell:Z",
    )
    assert fact.ownership == "unknown", fact.ownership
    assert verify_binding_fact(fact) is False, (
        "fact with entry '19. D' + cell:Z must fail verification"
    )


def test_range_no_letters_rejected():
    """'19-23' without letters cannot prove any qn→answer mapping."""
    own = _classify(["19-23"], "19", "qn:19|cell:Z", answer_text="Z")
    assert own == "unknown", f"expected unknown, got {own}"

    fact = derive_binding_fact(
        span_id="sp-rn",
        source_version_id=SVID,
        unit_id="Q19",
        question_number="19",
        source_lines=["19-23"],
        answer_text="Z",
        decode_loc="qn:19|cell:Z",
    )
    assert fact.ownership == "unknown", fact.ownership
    assert verify_binding_fact(fact) is False, (
        "fact over letter-less range must fail verification"
    )


# ── positive controls ─────────────────────────────────────────────────


def test_range_consistent_accepted():
    own = _classify(["19-23 DABCA"], "19", "qn:19|cell:D", answer_text="D")
    assert own == "match", own

    fact = derive_binding_fact(
        span_id="sp-rc",
        source_version_id=SVID,
        unit_id="Q19",
        question_number="19",
        source_lines=["19-23 DABCA"],
        answer_text="D",
        decode_loc="qn:19|cell:D",
    )
    assert fact.ownership == "match", fact.ownership
    assert verify_binding_fact(fact) is True


def test_entry_cell_consistent_accepted():
    own = _classify(["19. D"], "19", "qn:19|cell:D", answer_text="D")
    assert own == "match", own

    fact = derive_binding_fact(
        span_id="sp-ec",
        source_version_id=SVID,
        unit_id="Q19",
        question_number="19",
        source_lines=["19. D"],
        answer_text="D",
        decode_loc="qn:19|cell:D",
    )
    assert fact.ownership == "match"
    assert verify_binding_fact(fact) is True


def test_range_letter_mismatch_rejected():
    """qn21 maps to B in '19-23 DABCA'; claiming cell:D must fail."""
    own = _classify(["19-23 DABCA"], "21", "qn:21|cell:D", answer_text="D")
    assert own == "unknown", own


def test_range_q21_correct_letter_accepted():
    own = _classify(["19-23 DABCA"], "21", "qn:21|cell:B", answer_text="B")
    assert own == "match", own


def test_real_entry_without_cell_accepted():
    """No cell claim → entry classifier is the authority."""
    fact = derive_binding_fact(
        span_id="sp-re",
        source_version_id=SVID,
        unit_id="Q1",
        question_number="1",
        source_lines=["1. A"],
        answer_text="A",
    )
    assert fact.ownership == "match"
    assert verify_binding_fact(fact) is True


def test_compact_key_accepted():
    own = _classify(
        ["FGDAE"], "3", "qn:3|cell:D|qns:1,2,3,4,5", answer_text="D"
    )
    assert own == "match", own


def test_compact_without_qns_rejected():
    own = _classify(["FGDAE"], "3", "qn:3|cell:D", answer_text="D")
    assert own == "unknown", own


def test_table_cell_accepted():
    own = _classify(
        ["<table><tr><td>1</td><td>B</td></tr></table>"],
        "1",
        "qn:1|cell:B",
        answer_text="B",
    )
    assert own == "match", own


def test_table_cell_value_mismatch_rejected():
    own = _classify(
        ["<table><tr><td>1</td><td>B</td></tr></table>"],
        "1",
        "qn:1|cell:Z",
        answer_text="Z",
    )
    assert own == "unknown", own


# ── integrity / tamper ────────────────────────────────────────────────


def test_qn999_cell_z_rejected():
    own = _classify(["1. A"], "19", "qn:999|cell:Z", answer_text="Z")
    assert own == "unknown", own

    fact = derive_binding_fact(
        span_id="sp-x",
        source_version_id=SVID,
        unit_id="Q19",
        question_number="19",
        source_lines=["1. A"],
        answer_text="Z",
        decode_loc="qn:999|cell:Z",
    )
    assert fact.ownership == "unknown", fact.ownership
    assert verify_binding_fact(fact) is False, (
        "forged qn:999|cell:Z must fail verification"
    )


def test_fact_verify_rejects_forged_dloc_upgrade():
    """derive from real entry, then tamper decode_loc + ownership → verify False."""
    fact = derive_binding_fact(
        span_id="sp-y",
        source_version_id=SVID,
        unit_id="Q1",
        question_number="1",
        source_lines=["1. A"],
        answer_text="A",
    )
    assert fact.ownership == "match"

    forged = fact.to_payload()
    forged["decode_loc"] = "qn:999|cell:Z"
    forged["ownership"] = "match"
    f2 = _fact_from_mapping(forged)
    assert f2 is not None
    assert verify_binding_fact(f2) is False, (
        "tampered decode_loc must fail HMAC + source verification"
    )


def test_conflicting_cells_rejected():
    own = _classify(
        ["19-23 DABCA"], "19", "qn:19|cell:D|cell:B", answer_text="D"
    )
    assert own == "unknown", own


def test_answer_text_cell_inconsistency_rejected_by_verify():
    """Even a well-formed fact with text≠cell must fail verify."""
    fact = derive_binding_fact(
        span_id="sp-tc",
        source_version_id=SVID,
        unit_id="Q19",
        question_number="19",
        source_lines=["19-23 DABCA"],
        answer_text="D",
        decode_loc="qn:19|cell:D",
    )
    assert verify_binding_fact(fact) is True

    tampered = fact.to_payload()
    tampered["answer_text"] = "A"
    # answer_text_hash no longer matches → must reject
    f2 = _fact_from_mapping(tampered)
    assert f2 is not None
    assert verify_binding_fact(f2) is False

# ── R2-4: tighten answer token verification ──────────────────────────


def test_chemical_formula_not_answer_token():
    """cell=T + text='TiCl4': T is first letter of formula, NOT answer token."""
    own = _classify(["1. TiCl4"], "1", "qn:1|cell:T", answer_text="TiCl4")
    assert own == "unknown", f"TiCl4 must not match cell:T, got {own}"
    fact = derive_binding_fact(
        span_id="sp-chem", source_version_id=SVID, unit_id="Q1",
        question_number="1", source_lines=["1. TiCl4"],
        answer_text="TiCl4", decode_loc="qn:1|cell:T",
    )
    assert fact.ownership == "unknown"
    assert verify_binding_fact(fact) is False


def test_full_range_string_not_answer_token():
    """cell=D + text='DABCA': DABCA is full range key, NOT individual letter."""
    own = _classify(["19-23 DABCA"], "19", "qn:19|cell:D", answer_text="DABCA")
    assert own == "unknown", f"DABCA must not match cell:D, got {own}"
    fact = derive_binding_fact(
        span_id="sp-range", source_version_id=SVID, unit_id="Q19",
        question_number="19", source_lines=["19-23 DABCA"],
        answer_text="DABCA", decode_loc="qn:19|cell:D",
    )
    assert fact.ownership == "unknown"
    assert verify_binding_fact(fact) is False


def test_single_letter_answer_token_accepted():
    """cell=D + text='D': single letter IS the answer token."""
    own = _classify(["19-23 DABCA"], "19", "qn:19|cell:D", answer_text="D")
    assert own == "match", own


def test_entry_prefix_answer_token_accepted():
    """cell=B + text='1. B': entry prefix stripped, B is the token."""
    own = _classify(["1. B"], "1", "qn:1|cell:B", answer_text="1. B")
    assert own == "match", own
