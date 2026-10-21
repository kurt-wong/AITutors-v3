# -*- coding: utf-8 -*-
"""P0-R3 adversarial answer-binding tests (Owner acceptance cases).

Three independent acceptance gates (must all hold):
1. Wrong-question-number binding cannot auto_approve through the real chain.
2. Correct answer_value + fabricated line_refs fails provenance / is marked unlocated.
3. Unreliable answers are not presented as trusted standard answers.

Also covers: answer_lines/answer_value conflict, stem/explanation as answer,
normal single/multi/fill/short still works, and mutation checks.
"""
from __future__ import annotations

import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f3")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a3")


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
    return root, ir, compiled, run


def _payload(qn="1", unit_id="Q1", ctype="single_choice",
             answer_lines=None, answer_value=None, options="ABCD"):
    ans = {"answer_zone": "answer_table", "question_label": qn}
    if answer_lines is not None:
        ans["answer_lines"] = answer_lines
    if answer_value is not None:
        ans["answer_value"] = answer_value
    content = {
        "stem": {"question_label": qn},
        "answer": ans,
    }
    if options:
        content["options"] = [{"label": l} for l in options]
    return {"semantic_units": [{
        "unit_id": unit_id,
        "unit_type": "standalone_unit",
        "original_question_type": ctype,
        "content": content,
    }]}


def _base_lines():
    return _mk(
        "1. which fruit",
        "A. apple", "B. banana", "C. car", "D. table",
        "答案",
    )


def _eval(lines, payload, root_unit_id="Q1"):
    root, ir, compiled, run = _pipeline(lines, payload, root_unit_id)
    d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
    leaf = compiled.leaves[0] if compiled.leaves else None
    return d, run, leaf


# =========================================================================
# Acceptance gate 1: wrong-question-number binding
# =========================================================================

class TestWrongQuestionNumberBinding:
    def test_q1_bound_to_12A_not_auto(self):
        """DSH case 1: Q1 answer_lines -> line `12. A` must NOT auto_approve."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "12. A",
        )
        d, run, leaf = _eval(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] != "auto_approve", (
            f"Q1 bound to `12. A` must not auto_approve, got {d['decision']}"
        )
        # Must not store `12. A` (or its stripped `A`) as Q1's trusted answer
        if leaf and leaf.answer:
            assert leaf.answer.text.strip() not in ("12. A", "A", "12.A"), (
                f"foreign answer must not be bound as Q1 answer, got {leaf.answer.text!r}"
            )

    def test_q1_bound_to_2A_not_auto(self):
        """DSH case 2: Q1 answer_lines -> line `2. A` must NOT auto_approve."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "2. A",
        )
        d, run, leaf = _eval(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] != "auto_approve"
        if leaf and leaf.answer:
            assert leaf.answer.text.strip() not in ("2. A", "A", "2.A")

    def test_conflicting_answer_value_not_silent(self):
        """DSH case 3: answer_lines=`12. A` + answer_value="B" — no silent pick."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "12. A",
        )
        d, run, leaf = _eval(
            lines, _payload(answer_lines=[7, 7], answer_value="B")
        )
        assert d["decision"] != "auto_approve"
        # Must not silently accept either "12. A" or "B" as a located answer
        if leaf and leaf.answer:
            assert leaf.answer.source_located is False or leaf.answer.text.strip() == "", (
                f"conflict must not produce a source-located answer, got "
                f"text={leaf.answer.text!r} located={leaf.answer.source_located}"
            )

    def test_correct_binding_still_auto(self):
        """Control: Q1 answer_lines -> `1. B` must still auto_approve."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d, run, leaf = _eval(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] == "auto_approve", (
            f"correct binding must still auto_approve, got {d['decision']}: {d['reasons']}"
        )
        assert leaf.answer.text.strip() == "B"


# =========================================================================
# Acceptance gate 2: fabricated provenance
# =========================================================================

class TestFabricatedProvenance:
    def test_value_only_no_fake_line_refs(self):
        """DSH case 4: answer_value without line location is value-only, not P1L001."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d, run, leaf = _eval(lines, _payload(answer_value="B"))
        ans_spans = [s for s in run.resolved_spans if s.role == "answer"]
        assert ans_spans, "answer_value should still bind"
        span = ans_spans[0]
        assert "P1L001" not in span.line_refs, (
            f"must not fabricate P1L001, got {span.line_refs}"
        )
        assert span.resolution_status == "value_only"
        assert d["decision"] != "auto_approve", (
            f"value-only must not auto_approve, got {d['decision']}"
        )
        assert d["layers"]["provenance"]["auto_allowed"] is False

    def test_correct_value_with_stem_line_refs_not_auto(self):
        """Correct value bound into question region -> provenance blocks auto."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        # answer_lines points at stem line (question region)
        d, run, leaf = _eval(lines, _payload(answer_lines=[1, 1], answer_value="B"))
        assert d["decision"] != "auto_approve"
        assert d["layers"]["provenance"]["auto_allowed"] is False

    def test_explanation_region_overlap_not_auto(self):
        """Answer span inside explanation region -> pending, not auto."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
            "解析",
            "1. 【分析】xxx 故选：B.",
        )
        # Force answer_lines into the explanation zone (line 9)
        d, run, leaf = _eval(
            lines,
            _payload(answer_lines=[9, 9], ctype="single_choice"),
        )
        assert d["decision"] != "auto_approve"
        # provenance must flag the overlap when structural regions exist
        diags = d["layers"]["provenance"].get("role_region_diagnostics") or []
        assert diags or d["layers"]["provenance"]["auto_allowed"] is False


# =========================================================================
# Acceptance gate 3: persistence / display safety
# =========================================================================

class TestPersistenceDisplaySafety:
    def test_pending_answer_not_verified_correct(self):
        """Unreliable answers must not carry verified_correct=True in compiled form."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "12. A",
        )
        d, run, leaf = _eval(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] != "auto_approve"
        if leaf and leaf.answer:
            assert leaf.answer.verified_correct is not True
            # Frontend treats verified_correct != true as 待审核
            assert leaf.answer.source_located is False or leaf.answer.complete is False

    def test_stem_as_answer_not_trusted(self):
        """DSH case 5 (BIO-002): stem text as answer -> not trusted standard answer."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "2. which veg",
            "A. carrot", "B. potato",
            "答案",
            "1. B",
        )
        # answer_lines wrongly points at Q2's stem line (line 5)
        d, run, leaf = _eval(lines, _payload(answer_lines=[5, 5]))
        assert d["decision"] != "auto_approve"
        if leaf and leaf.answer:
            assert leaf.answer.verified_correct is not True
            assert "which veg" not in (leaf.answer.text or "")

    def test_explanation_as_answer_not_trusted(self):
        """DSH case 6 (BIO-003): explanation text as answer -> not auto, not verified."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. 【分析】直接利用复数代数形式的乘除运算化简得答案. 【解答】解：xxx 故选：C.",
        )
        d, run, leaf = _eval(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] != "auto_approve"
        if leaf and leaf.answer:
            assert leaf.answer.verified_correct is not True

    def test_answer_value_is_explanation_not_trusted(self):
        """DSH case 7: answer_value is explanation text -> not trusted."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d, run, leaf = _eval(
            lines,
            _payload(answer_value="【分析】直接利用复数代数形式的乘除运算化简得答案. 故选：C."),
        )
        assert d["decision"] != "auto_approve"
        if leaf and leaf.answer:
            assert leaf.answer.verified_correct is not True
            assert leaf.answer.source_located is False


# =========================================================================
# Normal questions must still pass
# =========================================================================

class TestNormalQuestionsStillWork:
    def test_single_choice_correct(self):
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d, run, leaf = _eval(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] == "auto_approve"
        assert leaf.answer.text.strip() == "B"

    def test_multiple_choice_correct(self):
        lines = _mk(
            "1. which fruits",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. AB",
        )
        d, run, leaf = _eval(
            lines, _payload(answer_lines=[7, 7], ctype="multiple_choice")
        )
        assert d["decision"] == "auto_approve"

    def test_true_false_correct(self):
        lines = _mk(
            "1. is fruit?",
            "A. 对", "B. 错",
            "答案",
            "1. 对",
        )
        d, run, leaf = _eval(
            lines,
            _payload(
                qn="1", ctype="true_false", answer_lines=[5, 5],
                options="AB",
            ),
        )
        assert d["decision"] == "auto_approve"

    def test_fill_in_not_auto_but_bound(self):
        """fill_in is not strict-auto but the answer should bind cleanly."""
        lines = _mk(
            "1. 1+1=?",
            "答案",
            "1. 2",
        )
        d, run, leaf = _eval(
            lines,
            _payload(qn="1", ctype="fill_in", answer_lines=[3, 3], options=""),
        )
        assert d["decision"] == "pending_review"
        if leaf and leaf.answer:
            assert "2" in leaf.answer.text
            assert leaf.answer.verified_correct is not True

    def test_short_answer_pending(self):
        lines = _mk(
            "1. explain",
            "答案",
            "1. because reasons",
        )
        d, run, leaf = _eval(
            lines,
            _payload(qn="1", ctype="short_answer", answer_lines=[3, 3], options=""),
        )
        assert d["decision"] == "pending_review"


# =========================================================================
# Mutation checks: reverse the safety behavior and require test failure
# =========================================================================

class TestMutationChecks:
    def test_mutation_allow_foreign_binding_would_fail(self):
        """Mutation check 1: if ownership rejection is removed, gate 1 tests fail.

        Simulates the old fallthrough (bind full foreign line) and asserts the
        resulting decision IS auto_approve — proving our tests would catch it.
        """
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "12. A",
        )
        # Old behavior simulation: bind the foreign line as a char-span answer
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(
            _payload(answer_lines=[7, 7])
        )
        # Force-bind `12. A` the way the old code did (full line)
        from app.domains.resolver.span import ResolvedSpan
        import hashlib
        raw = lines[6].text  # P1L007
        forced = ResolvedSpan(
            span_id="sp-Q1.answer",
            source_version_id=SVID,
            role="answer",
            start_line_ref="P1L007",
            end_line_ref="P1L007",
            line_refs=("P1L007",),
            granularity="line",
            start_offset=None,
            end_offset=None,
            text_hash=hashlib.sha256(raw.encode()).hexdigest(),
            resolution_status="exact",
            evidence=(
                "mutation: foreign full-line bind",
                "ownership=match",  # forged: old path claimed ownership
                "binding_evidence=mutation-forged-match",
            ),
        )
        mutated_spans = tuple(
            forced if s.role == "answer" else s for s in run.resolved_spans
        )
        # If answer span missing (now empty), append forced
        if not any(s.role == "answer" for s in run.resolved_spans):
            mutated_spans = run.resolved_spans + (forced,)
        from app.domains.resolver.span import ResolvedRun
        bad_run = ResolvedRun(
            source_version_id=run.source_version_id,
            resolved_spans=mutated_spans,
            unresolved_references=run.unresolved_references,
            resolved_relations=run.resolved_relations,
            unresolved_relations=run.unresolved_relations,
            structural_regions=run.structural_regions,
        )
        payload = _payload(answer_lines=[7, 7])
        ir = IRBuilder.build(bad_run, payload, SVID, ANN_ID)
        spans = {s.span_id: s for s in bad_run.resolved_spans}
        lines_by_ref = {l.line_ref: l for l in lines}
        compiled = Compiler(spans, lines_by_ref).compile(ir)
        root = next(u for u in ir.units if u.unit_id == "Q1")
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=bad_run)
        # Old behavior WOULD auto_approve (`12. A` -> clean -> `A`)
        assert d["decision"] == "auto_approve", (
            "mutation check: old foreign-bind behavior should reproduce auto_approve; "
            f"got {d['decision']} — if this fails, the mutation model is wrong"
        )

    def test_mutation_fake_line_refs_would_pass_unless_blocked(self):
        """Mutation check 2: fake P1L001 + correct value + exact resolution.

        Without the region/value-only guard this reaches auto_approve.
        """
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(
            _payload(answer_value="B")
        )
        from app.domains.resolver.span import ResolvedSpan, ResolvedRun
        import hashlib
        forced = ResolvedSpan(
            span_id="sp-Q1.answer",
            source_version_id=SVID,
            role="answer",
            start_line_ref="P1L001",
            end_line_ref="P1L001",
            line_refs=("P1L001",),
            granularity="line_character",
            start_offset=0,
            end_offset=1,
            text_hash=hashlib.sha256(b"B").hexdigest(),
            resolution_status="exact",
            evidence=("answer_evidence_value", "cell=B"),
        )
        mutated = tuple(
            forced if s.role == "answer" else s for s in run.resolved_spans
        )
        if not any(s.role == "answer" for s in run.resolved_spans):
            mutated = run.resolved_spans + (forced,)
        # Put P1L001 into question region so region-overlap guard can fire
        from app.domains.resolver.span import SourceRegion
        q_region = SourceRegion(
            role="question", start_seq=0, end_seq=5,
            line_refs=("P1L001", "P1L002", "P1L003", "P1L004", "P1L005"),
        )
        bad_run = ResolvedRun(
            source_version_id=run.source_version_id,
            resolved_spans=mutated,
            unresolved_references=run.unresolved_references,
            resolved_relations=run.resolved_relations,
            unresolved_relations=run.unresolved_relations,
            structural_regions=run.structural_regions + (q_region,),
        )
        payload = _payload(answer_value="B")
        ir = IRBuilder.build(bad_run, payload, SVID, ANN_ID)
        spans = {s.span_id: s for s in bad_run.resolved_spans}
        lines_by_ref = {l.line_ref: l for l in lines}
        compiled = Compiler(spans, lines_by_ref).compile(ir)
        root = next(u for u in ir.units if u.unit_id == "Q1")
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=bad_run)
        # With the P0-R3 region guard this MUST NOT auto_approve
        assert d["decision"] != "auto_approve", (
            "P0-R3: fabricated P1L001 provenance must not auto_approve"
        )
        assert d["layers"]["provenance"]["auto_allowed"] is False
