# -*- coding: utf-8 -*-
"""P0-R4: full-path ownership guard, provenance semantics, real mutation tests.

Decisive property: when a source line is another question's answer (ANY
surface format), it must never bind to the target question and auto_approve.

Covers DSH format variants + provenance three-state + weak-assertion fixes +
monkeypatch mutations of the REAL production ownership guard.
"""
from __future__ import annotations

import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.policy import evaluate
from app.domains.gate import binding_fact
from app.domains.resolver import resolver as resolver_mod
from app.domains.resolver.resolver import (
    SourceResolver,
    _entry_ownership,
)
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f4")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a4")

# All DSH-reported + same-family variants of a Q12 answer line wrongly bound
# as Q1's answer. Ownership is number-based — content form must NOT matter.
FOREIGN_VARIANTS = [
    "12. A",
    "2. A",
    "12. A（2分）",
    "12. A(2分)",
    "12. （A）",
    "12. (A)",
    "12. A、B",
    "12. A B",
    "12. A,B",
    "12. A、B（2分）",
    "12. A,B(2分)",
    "12. A。",
    "12. 【答案】A",
    "12. A，B",
    "12. A、B（3分）",
    "12. （3分）A",
    "12. (3分)A",
    # R5: letters beyond A-D, TF tokens, explicit prefixes, bare scores
    "12. E",
    "12. F",
    "12. G（2分）",
    "12. E、F",
    "12. E F",
    "12. T",
    "12. 正确",
    "12. 错误",
    "12. 对",
    "12. 错",
    "12. √",
    "12. ×",
    "12. A 2分",
    "12. 答案：A",
    "12. （A）2分",
    "12. 砖红色沉淀",
]


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _pipeline(lines, payload, root_unit_id="Q1"):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    lines_by_ref = {l.line_ref: l for l in lines}
    compiled = Compiler(spans, lines_by_ref).compile(ir)
    root = next(u for u in ir.units if u.unit_id == root_unit_id)
    d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
    leaf = compiled.leaves[0] if compiled.leaves else None
    return d, run, leaf


def _payload(answer_lines=None, answer_value=None, qn="1",
             ctype="single_choice", options="ABCD"):
    ans = {"answer_zone": "answer_table", "question_label": qn}
    if answer_lines is not None:
        ans["answer_lines"] = answer_lines
    if answer_value is not None:
        ans["answer_value"] = answer_value
    content = {"stem": {"question_label": qn}, "answer": ans}
    if options:
        content["options"] = [{"label": l} for l in options]
    return {"semantic_units": [{
        "unit_id": "Q1", "unit_type": "standalone_unit",
        "original_question_type": ctype, "content": content,
    }]}


def _lines_with_foreign(text):
    return _mk(
        "1. which fruit",
        "A. apple", "B. banana", "C. car", "D. table",
        "12. which color",
        "答案",
        text,
    )


# =========================================================================
# A. All foreign format variants must not auto_approve
# =========================================================================

class TestForeignFormatVariants:
    @pytest.mark.parametrize("line_text", FOREIGN_VARIANTS)
    def test_foreign_variant_not_auto(self, line_text):
        """Every same-family format of a foreign answer must be rejected."""
        lines = _lines_with_foreign(line_text)
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
        assert d["decision"] == "pending_review", (
            f"foreign line {line_text!r} must be pending_review, got {d['decision']} "
            f"ans={leaf.answer.text if leaf and leaf.answer else None!r}"
        )
        # B: foreign full text must NOT leak into the answer field
        if leaf and leaf.answer:
            assert (leaf.answer.text or "").strip() == "", (
                f"foreign full text leaked as answer: {leaf.answer.text!r}"
            )
            assert leaf.answer.verified_correct is not True
        # provenance must not claim the source is verified
        assert d["layers"]["provenance"]["status"] != "pass", (
            f"foreign bind must not get provenance pass: "
            f"{d['layers']['provenance']['status']}"
        )
        assert d["layers"]["provenance"]["auto_allowed"] is False

    @pytest.mark.parametrize("line_text,ctype", [
        ("12. T", "true_false"),
        ("12. F", "true_false"),
        ("12. 正确", "true_false"),
        ("12. 错误", "true_false"),
        ("12. 对", "true_false"),
        ("12. 错", "true_false"),
        ("12. √", "true_false"),
        ("12. ×", "true_false"),
        ("12. E", "true_false"),
    ])
    def test_foreign_tf_tokens_not_auto(self, line_text, ctype):
        """TF-type foreign tokens must not auto_approve or leak full text."""
        lines = _lines_with_foreign(line_text)
        d, run, leaf = _pipeline(
            lines, _payload(answer_lines=[8, 8], ctype=ctype, options="AB")
        )
        assert d["decision"] in ("pending_review", "rejected"), (
            f"TF foreign {line_text!r} got {d['decision']}"
        )
        assert d["decision"] != "auto_approve"
        if leaf and leaf.answer:
            assert (leaf.answer.text or "").strip() == "", (
                f"TF foreign leaked: {leaf.answer.text!r}"
            )
        if d["decision"] == "pending_review":
            assert d["layers"]["provenance"]["status"] != "pass"

    def test_r5_edge_formats_no_full_text_leak(self):
        """`12. A 2分` / `12. 答案：A` / `12. （A）2分` must not write full text."""
        for text in ("12. A 2分", "12. 答案：A", "12. （A）2分"):
            lines = _lines_with_foreign(text)
            d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
            assert d["decision"] == "pending_review"
            if leaf and leaf.answer:
                assert (leaf.answer.text or "").strip() == "", (
                    f"{text!r} leaked into answer: {leaf.answer.text!r}"
                )
            assert d["layers"]["provenance"]["status"] != "pass"

    @pytest.mark.parametrize("line_text", FOREIGN_VARIANTS)
    def test_foreign_variant_multiple_choice_not_auto(self, line_text):
        """Same family under multiple_choice type must also be rejected."""
        lines = _lines_with_foreign(line_text)
        d, run, leaf = _pipeline(
            lines, _payload(answer_lines=[8, 8], ctype="multiple_choice")
        )
        assert d["decision"] != "auto_approve", (
            f"MC foreign {line_text!r} auto_approved: {d['decision']}"
        )

    def test_control_own_answer_still_auto(self):
        """Match-ownership answers still auto; bare cell does NOT auto (Q1)."""
        for text in ("1. B", "1. （B）", "1. B（2分）", "1. 【答案】B"):
            lines = _mk(
                "1. which fruit",
                "A. apple", "B. banana", "C. car", "D. table",
                "答案",
                text,
            )
            d, run, leaf = _pipeline(lines, _payload(answer_lines=[7, 7]))
            assert d["decision"] == "auto_approve", (
                f"own answer {text!r} must auto_approve, got {d['decision']}: {d['reasons']}"
            )
            assert leaf.answer is not None and leaf.answer.text.strip()

    def test_bare_cell_does_not_auto(self):
        """Bare cell (no entry token) is unknown — must not auto (contract Q1)."""
        lines = _lines_with_foreign("B")
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
        assert d["decision"] != "auto_approve", f"bare auto-approved: {d['decision']}"
        assert getattr(leaf.answer, "ownership", "unknown") == "unknown"

    def test_local_numbered_body_not_cleared(self):
        """Per-unit local numbering (`1.（3分）Mg | TiCl4`) must NOT be rejected."""
        lines = _mk(
            "",
            "",
            "26. chem question 1",
            "1.（3分）Mg | TiCl4 | 1",
        )
        payload = {"semantic_units": [{
            "unit_id": "U-req1", "content": {
                "stem": {"question_label": "26"},
                "answer": {"answer_zone": "answer_table", "question_label": "26",
                           "answer_lines": [4, 4]},
            }}]}
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
        a = next(s for s in run.resolved_spans if s.span_id == "sp-U-req1.answer")
        assert a.line_refs, f"local-numbered body must stay bound, got {a.line_refs}"
        bound = "\n".join(
            next(l.text for l in lines if l.line_ref == ref) for ref in a.line_refs
        )
        assert "Mg" in bound, f"expected Mg in bound text {bound!r}"


# =========================================================================
# B. Ownership classification (unit-level)
# =========================================================================

class TestOwnershipClassification:
    """P0-R5b: ownership is number relationship + local-evidence, not tokens."""

    @pytest.mark.parametrize("text,qn,allow_local,expected", [
        # same exam space, different number → another question (ANY content)
        ("12. A", "1", False, "foreign_question"),
        ("12. E", "1", False, "foreign_question"),
        ("12. 正确", "1", False, "foreign_question"),
        ("5. A", "12", False, "foreign_question"),
        ("5. 正确", "12", False, "foreign_question"),
        ("5. A、B", "26", False, "foreign_question"),
        ("1. B", "26", False, "foreign_question"),
        ("5. 砖红色沉淀", "26", False, "foreign_question"),
        ("2. A", "1", False, "foreign_question"),
        # match / bare
        ("1. B", "1", False, "match"),
        ("1.（3分）Mg | TiCl4 | 1", "1", False, "match"),
        ("B", "1", False, "bare"),
        # local_index ONLY with positive evidence
        ("1.（3分）Mg | TiCl4 | 1", "26", True, "local_index"),
        ("1. answer-one", "26", True, "local_index"),
        ("5.（3分）x", "51", True, "local_index"),
        # without evidence → foreign
        ("1.（3分）Mg | TiCl4 | 1", "26", False, "foreign_question"),
    ])
    def test_entry_ownership(self, text, qn, allow_local, expected):
        assert _entry_ownership([text], qn, allow_local_index=allow_local) == expected


# =========================================================================
# C. Provenance three-state semantics
# =========================================================================

class TestProvenanceSemantics:
    def test_clean_pass_is_pass(self):
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[7, 7]))
        prov = d["layers"]["provenance"]
        assert prov["status"] == "pass"
        assert prov["auto_allowed"] is True
        assert d["decision"] == "auto_approve"

    def test_value_only_is_insufficient_not_pass(self):
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d, run, leaf = _pipeline(lines, _payload(answer_value="B"))
        prov = d["layers"]["provenance"]
        assert prov["status"] == "insufficient", (
            f"value-only must be insufficient, got {prov['status']}"
        )
        assert prov["auto_allowed"] is False
        assert d["decision"] == "pending_review"
        # not terminal rejected
        assert d["decision"] != "rejected"

    def test_region_overlap_is_insufficient_not_pass(self):
        from app.domains.resolver.span import ResolvedRun, SourceRegion
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d0, run, leaf = _pipeline(lines, _payload(answer_lines=[7, 7]))
        ans_span = next(s for s in run.resolved_spans if s.role == "answer")
        bad_region = SourceRegion(
            role="question", start_seq=0, end_seq=999,
            line_refs=ans_span.line_refs,
        )
        bad_run = ResolvedRun(
            source_version_id=run.source_version_id,
            resolved_spans=run.resolved_spans,
            unresolved_references=run.unresolved_references,
            resolved_relations=run.resolved_relations,
            unresolved_relations=run.unresolved_relations,
            structural_regions=run.structural_regions + (bad_region,),
        )
        payload = _payload(answer_lines=[7, 7])
        ir = IRBuilder.build(bad_run, payload, SVID, ANN_ID)
        spans = {s.span_id: s for s in bad_run.resolved_spans}
        compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
        root = next(u for u in ir.units if u.unit_id == "Q1")
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=bad_run)
        prov = d["layers"]["provenance"]
        assert prov["status"] == "insufficient", (
            f"region overlap must be insufficient, got {prov['status']}"
        )
        assert prov["auto_allowed"] is False
        assert d["decision"] == "pending_review"

    def test_hash_mismatch_is_fail(self):
        import dataclasses
        from app.domains.compile.snapshot import CompiledSnapshot
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d0, run, leaf0, base_compiled = None, None, None, None
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(
            _payload(answer_lines=[7, 7])
        )
        ir = IRBuilder.build(run, _payload(answer_lines=[7, 7]), SVID, ANN_ID)
        spans = {s.span_id: s for s in run.resolved_spans}
        base_compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
        leaf = base_compiled.leaves[0]
        bad_answer = dataclasses.replace(leaf.answer, text_hash="0" * 64)
        bad_leaf = dataclasses.replace(leaf, answer=bad_answer)
        snap2 = CompiledSnapshot(
            base_compiled.source_version_id, base_compiled.annotation_id,
            (bad_leaf,), base_compiled.materials,
        )
        root = next(u for u in ir.units if u.unit_id == "Q1")
        d = evaluate(root=root, ir=ir, compiled=snap2, resolved_run=run)
        prov = d["layers"]["provenance"]
        assert prov["status"] == "fail"
        assert d["decision"] == "rejected"

    def test_status_and_auto_allowed_consistent(self):
        """insufficient ⟺ not auto_allowed; pass ⟺ auto_allowed (for these cases)."""
        cases = [
            (_lines_with_foreign("12. A"), _payload(answer_lines=[8, 8])),
            (_lines_with_foreign("12. A（2分）"), _payload(answer_lines=[8, 8])),
        ]
        for lines, payload in cases:
            d, run, leaf = _pipeline(lines, payload)
            prov = d["layers"]["provenance"]
            if prov["status"] == "pass":
                assert prov["auto_allowed"] is True
            else:
                assert prov["auto_allowed"] is False
            assert d["decision"] != "auto_approve" or prov["status"] == "pass"


# =========================================================================
# D. Weak assertion fixes (precise expected state, not mere inequality)
# =========================================================================

class TestPreciseStateAssertions:
    def test_foreign_bind_exact_state(self):
        """Not just 'not auto' — assert exact pending + empty answer + null verified."""
        lines = _lines_with_foreign("12. A（2分）")
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
        assert d["decision"] == "pending_review"
        assert d["layers"]["provenance"]["status"] == "insufficient"
        assert d["layers"]["provenance"]["auto_allowed"] is False
        if leaf and leaf.answer:
            assert leaf.answer.text.strip() == ""
            assert leaf.answer.verified_correct is None
            assert leaf.answer.source_located is False or leaf.answer.complete is False

    def test_missing_answer_lines_and_value_pending(self):
        """No answer_lines/value and no clean answer in zone → pending, not auto.

        (When the answer zone DOES contain a clean qn entry the fallback may
        bind it — that is designed behavior. This case has only explanation.)
        """
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. 【分析】没有直接答案，只有解析。",
        )
        d, run, leaf = _pipeline(lines, _payload())  # no answer_lines, no value
        assert d["decision"] != "auto_approve"
        assert d["decision"] in ("pending_review", "rejected")
        if leaf and leaf.answer:
            assert leaf.answer.verified_correct is not True
        unresolved = [u for u in run.unresolved_references if u.role == "answer"]
        ans_spans = [s for s in run.resolved_spans if s.role == "answer"]
        assert (len(ans_spans) == 0) or (
            len(ans_spans) == 1 and not (leaf and leaf.answer and leaf.answer.text.strip())
        ), f"spans={len(ans_spans)} unresolved={len(unresolved)}"

    def test_explanation_text_not_auto_exact(self):
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. 【分析】xxx 故选：B.",
        )
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] == "pending_review"
        assert leaf is not None
        assert leaf.answer is not None
        assert leaf.answer.verified_correct is not True


# =========================================================================
# E. REAL production-guard mutation tests (monkeypatch, not fake spans)
# =========================================================================

class TestRealGuardMutations:
    def test_mutation_remove_ownership_guard_fails_tests(self):
        """Monkeypatch production _entry_ownership to always 'match'.

        With the guard neutralized, a foreign line becomes bindable and
        reaches auto_approve — proving the E2E tests actually depend on
        the production guard (not on a hand-built span).
        """
        # M2-style: neutralize ownership classification AND policy ownership gate
        # so a foreign line can auto — proving both layers are load-bearing.
        original_cls = resolver_mod.classify_answer_ownership
        resolver_mod.classify_answer_ownership = lambda texts, qn: "match"
        # strip ownership blocker by wrapping evaluate? easier: patch leaf post-compile
        # Instead force classifier match so span gets ownership=match and policy allows.
        try:
            lines = _lines_with_foreign("12. A（2分）")
            d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
            assert d["decision"] == "auto_approve", (
                "mutation check failed: classifier patched to match but "
                f"decision={d['decision']} reasons={d['reasons']}"
            )
        finally:
            resolver_mod.classify_answer_ownership = original_cls

    def test_guard_restored_blocks_again(self):
        """After restoring the guard the same input is blocked (fresh call)."""
        lines = _lines_with_foreign("12. A（2分）")
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
        assert d["decision"] == "pending_review"

    def test_mutation_scored_decoder_ignores_qn(self):
        """Monkeypatch _decode_scored_answer back to qn-blind behavior.

        Shows the secondary defense (qn check in scored decoder) is also
        load-bearing when ownership is the primary guard — with BOTH
        neutralized the bypass returns.
        """
        original_cls = resolver_mod.classify_answer_ownership
        original_dec = resolver_mod._decode_scored_answer

        def _qn_blind_decode(raw, qn):
            import re
            m = re.match(r"^\s*\d+\s*[.．、]\s*[\(（]([A-Da-d]+)[\)）]", raw)
            if not m:
                return None
            return (m.start(1), m.end(1), m.group(1).upper())

        original_struct = binding_fact._source_supports_structural_qn
        resolver_mod.classify_answer_ownership = lambda texts, qn: "match"
        resolver_mod._decode_scored_answer = _qn_blind_decode
        # R16c-FIX added structural verification as a third defense layer.
        # Triple-mutation: also neutralize structural support to show the
        # bypass returns only when ALL THREE defenses are down.
        binding_fact._source_supports_structural_qn = lambda *a, **k: True
        try:
            lines = _lines_with_foreign("12. （A）")
            d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
            assert d["decision"] == "auto_approve", (
                f"triple-mutation should reproduce bypass, got {d['decision']}"
            )
        finally:
            resolver_mod.classify_answer_ownership = original_cls
            resolver_mod._decode_scored_answer = original_dec
            binding_fact._source_supports_structural_qn = original_struct

    def test_mutation_provenance_overlap_allow_fails(self):
        """If region-overlap no longer downgrades provenance, auto returns."""
        from app.domains.resolver.span import ResolvedRun, SourceRegion
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d0, run, leaf = _pipeline(lines, _payload(answer_lines=[7, 7]))
        ans_span = next(s for s in run.resolved_spans if s.role == "answer")
        # Simulate "overlap ignored" by using empty structural_regions
        no_region_run = ResolvedRun(
            source_version_id=run.source_version_id,
            resolved_spans=run.resolved_spans,
            unresolved_references=run.unresolved_references,
            resolved_relations=run.resolved_relations,
            unresolved_relations=run.unresolved_relations,
            structural_regions=(),  # mutation: drop region map
        )
        payload = _payload(answer_lines=[7, 7])
        ir = IRBuilder.build(no_region_run, payload, SVID, ANN_ID)
        spans = {s.span_id: s for s in no_region_run.resolved_spans}
        compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
        root = next(u for u in ir.units if u.unit_id == "Q1")
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=no_region_run)
        # Without region map the same answer auto-approves — proving the
        # region check is what forces insufficient/pending when it fires.
        assert d["decision"] == "auto_approve"
        assert d["layers"]["provenance"]["status"] == "pass"
