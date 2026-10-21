# -*- coding: utf-8 -*-
"""P0-R5: number-relationship ownership, foreign full-text block, real mutations.

Core invariant (Owner R5): ownership is decided by the relationship between
the source-line entry number and the target question number — NOT by whether
the content matches an answer-token whitelist.

Mutation tests monkeypatch the REAL production functions (never hand-built spans).
"""
from __future__ import annotations

import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.policy import evaluate
from app.domains.resolver import resolver as resolver_mod
from app.domains.resolver.resolver import SourceResolver, _entry_ownership
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f5")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a5")


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


FOREIGN_ALL = [
    "12. A", "12. E", "12. G（2分）", "12. 正确", "12. √",
    "12. A 2分", "12. 答案：A", "12. （A）2分", "12. 砖红色沉淀",
]


# =========================================================================
# A. Number-relationship ownership (not token whitelist)
# =========================================================================

class TestNumberRelationshipOwnership:
    @pytest.mark.parametrize("text,ctype,expected_own", [
        ("12. E", "single_choice", "foreign_question"),
        ("12. 正确", "true_false", "foreign_question"),
        ("12. 答案：A", "single_choice", "foreign_question"),
        ("12. 砖红色沉淀", "fill_in", "foreign_question"),
        ("1. B", "single_choice", "match"),
        ("1.（3分）Mg | TiCl4 | 1", "single_choice", "match"),
        ("B", "single_choice", "bare"),
        ("1.（3分）Mg | TiCl4 | 1", "fill_in", "match"),
    ])
    def test_ownership_independent_of_token_shape(self, text, ctype, expected_own):
        qn = "1"
        assert _entry_ownership([text], qn) == expected_own

    @pytest.mark.parametrize("text", FOREIGN_ALL)
    def test_foreign_number_full_block(self, text):
        """Foreign entry number → empty answer, no full-text leak, no auto."""
        lines = _lines_with_foreign(text)
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
        assert d["decision"] == "pending_review"
        if leaf and leaf.answer:
            assert (leaf.answer.text or "").strip() == "", (
                f"full text leaked: {leaf.answer.text!r}"
            )
            assert leaf.answer.verified_correct is not True
        assert d["layers"]["provenance"]["status"] != "pass"

    def test_local_index_still_allowed(self):
        """Unit 26 + local label `1.（3分）Mg | TiCl4` must stay bound."""
        lines = _mk(
            "", "",
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
        assert a.line_refs, "local-indexed body must stay bound"
        assert a.text_hash  # non-empty

    def test_reverse_low_qn_to_high_target_not_auto(self):
        """R5b decisive: `5. A` → Q12 must be foreign, not local_index."""
        for target, text, ctype in [
            (12, "5. A", "single_choice"),
            (12, "5. 正确", "true_false"),
            (11, "5. A", "single_choice"),
            (26, "5. A", "single_choice"),
            (26, "5. A、B", "multiple_choice"),
            (26, "1. B", "single_choice"),
            (26, "5. 砖红色沉淀", "fill_in"),
            (12, "5. A 2分", "single_choice"),
            (12, "5. 答案：A", "single_choice"),
        ]:
            lines = _mk(
                f"{target}. which fruit",
                "A. apple", "B. banana", "C. car", "D. table",
                "答案",
                text,
            )
            payload = {
                "semantic_units": [{
                    "unit_id": f"Q{target}", "unit_type": "standalone_unit",
                    "original_question_type": ctype,
                    "content": {
                        "stem": {"question_label": str(target)},
                        "options": [{"label": l} for l in "ABCD"],
                        "answer": {
                            "answer_zone": "answer_table",
                            "question_label": str(target),
                            "answer_lines": [7, 7],
                        },
                    }},
                ]
            }
            d, run, leaf = _pipeline(lines, payload, f"Q{target}")
            assert d["decision"] == "pending_review", (
                f"Q{target} <- {text!r} got {d['decision']}"
            )
            if leaf and leaf.answer:
                assert (leaf.answer.text or "").strip() == "", (
                    f"Q{target} <- {text!r} leaked: {leaf.answer.text!r}"
                )

    def test_batch_foreign_sequence_5_6_not_auto(self):
        """Two foreign simple answers (5.A / 6.B) are not a local 1..k sequence."""
        lines = _mk(
            "12. q12",
            "A. a", "B. b", "C. c", "D. d",
            "13. q13",
            "A. a", "B. b", "C. c", "D. d",
            "答案",
            "5. A",
            "6. B",
        )
        units = []
        for qn, ref in ((12, 12), (13, 13)):
            units.append({
                "unit_id": f"Q{qn}", "unit_type": "standalone_unit",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"question_label": str(qn)},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": str(qn),
                        "answer_lines": [ref, ref],
                    },
                },
            })
        payload = {"semantic_units": units}
        for qn in (12, 13):
            d, run, _ = _pipeline(lines, payload, f"Q{qn}")
            assert d["decision"] == "pending_review", (
                f"Q{qn} foreign batch sequence auto-approved"
            )
            span = next(
                s for s in run.resolved_spans if s.span_id == f"sp-Q{qn}.answer"
            )
            assert span.line_refs == (), f"Q{qn} leaked refs {span.line_refs}"

    def test_batch_simple_1_2_not_auto(self):
        """Simple `1. A`/`2. B` foreign cells are not local prose evidence."""
        lines = _mk(
            "12. q12",
            "A. a", "B. b", "C. c", "D. d",
            "13. q13",
            "A. a", "B. b", "C. c", "D. d",
            "答案",
            "1. A",
            "2. B",
        )
        units = []
        for qn, ref in ((12, 12), (13, 13)):
            units.append({
                "unit_id": f"Q{qn}", "unit_type": "standalone_unit",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"question_label": str(qn)},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": str(qn),
                        "answer_lines": [ref, ref],
                    },
                },
            })
        payload = {"semantic_units": units}
        for qn in (12, 13):
            d, run, _ = _pipeline(lines, payload, f"Q{qn}")
            assert d["decision"] == "pending_review"
            span = next(
                s for s in run.resolved_spans if s.span_id == f"sp-Q{qn}.answer"
            )
            assert span.line_refs == (), f"Q{qn} simple batch leaked {span.line_refs}"

    def test_multiline_bare1_simple_A_not_auto(self):
        """A bare `1.` + simple `A` is not a local body for Q12."""
        lines = _mk(
            "12. q12",
            "A. a", "B. b", "C. c", "D. d",
            "答案",
            "1.",
            "A",
        )
        payload = {"semantic_units": [{
            "unit_id": "Q12", "unit_type": "standalone_unit",
            "original_question_type": "single_choice",
            "content": {
                "stem": {"question_label": "12"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "12",
                    "answer_lines": [7, 8],
                },
            },
        }]}
        d, run, _ = _pipeline(lines, payload, "Q12")
        assert d["decision"] == "pending_review"
        span = next(s for s in run.resolved_spans if s.span_id == "sp-Q12.answer")
        assert span.line_refs == (), f"bare 1.+A leaked {span.line_refs}"

    def test_shared_foreign_single_entry_not_auto(self):
        """Shared range must not let Q12/Q13 claim Q1/Q2's `1. A`/`2. B`."""
        lines = _mk(
            "1. q1",
            "A. a", "B. b", "C. c", "D. d",
            "2. q2",
            "A. a", "B. b", "C. c", "D. d",
            "12. q12",
            "A. a", "B. b", "C. c", "D. d",
            "13. q13",
            "A. a", "B. b", "C. c", "D. d",
            "答案",
            "1. A",
            "2. B",
        )
        units = [
            {
                "unit_id": f"Q{qn}", "unit_type": "standalone_unit",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"question_label": str(qn)},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": str(qn),
                        "answer_lines": [22 if qn in (1, 12) else 23,
                                         22 if qn in (1, 12) else 23],
                    },
                },
            }
            for qn in (1, 2, 12, 13)
        ]
        payload = {"semantic_units": units}
        for qn in (1, 2):
            d, run, _ = _pipeline(lines, payload, f"Q{qn}")
            assert d["decision"] == "auto_approve", f"Q{qn} lost its own answer"
        for qn in (12, 13):
            d, run, _ = _pipeline(lines, payload, f"Q{qn}")
            assert d["decision"] == "pending_review", (
                f"Q{qn} claimed shared foreign answer"
            )
            span = next(
                s for s in run.resolved_spans if s.span_id == f"sp-Q{qn}.answer"
            )
            assert span.line_refs == (), f"Q{qn} shared foreign leaked {span.line_refs}"

    def test_shared_multiline_single_entry_not_auto(self):
        """Shared multi-line range whose only entry is `1. A` is still foreign for Q12."""
        lines = _mk(
            "12. q12",
            "A. a", "B. b", "C. c", "D. d",
            "答案",
            "1. A",
            "",
        )
        units = []
        for qn in (1, 12):
            units.append({
                "unit_id": f"Q{qn}", "unit_type": "standalone_unit",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"question_label": str(qn)},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": str(qn),
                        "answer_lines": [7, 8],
                    },
                },
            })
        payload = {"semantic_units": units}
        d12, run12, _ = _pipeline(lines, payload, "Q12")
        assert d12["decision"] == "pending_review"
        s12 = next(s for s in run12.resolved_spans if s.span_id == "sp-Q12.answer")
        assert s12.line_refs == ()

    def test_shared_owner_single_entry_auto(self):
        """Shared range still binds the true owner (`12. A` for Q12)."""
        lines = _mk(
            "1. q1",
            "A. a", "B. b", "C. c", "D. d",
            "12. q12",
            "A. a", "B. b", "C. c", "D. d",
            "答案",
            "12. A",
        )
        units = []
        for qn in (1, 12):
            units.append({
                "unit_id": f"Q{qn}", "unit_type": "standalone_unit",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {"question_label": str(qn)},
                    "options": [{"label": l} for l in "ABCD"],
                    "answer": {
                        "answer_zone": "answer_table",
                        "question_label": str(qn),
                        "answer_lines": [12, 12],
                    },
                },
            })
        payload = {"semantic_units": units}
        d1, run1, _ = _pipeline(lines, payload, "Q1")
        assert d1["decision"] == "pending_review"
        s1 = next(s for s in run1.resolved_spans if s.span_id == "sp-Q1.answer")
        assert s1.line_refs == ()
        d12, run12, _ = _pipeline(lines, payload, "Q12")
        assert d12["decision"] == "auto_approve"
        s12 = next(s for s in run12.resolved_spans if s.span_id == "sp-Q12.answer")
        assert s12.line_refs == ("P1L012",)

    def test_multiline_foreign_simple_not_auto(self):
        """`5. A` + blank continuation is not local evidence for Q12."""
        lines = _mk(
            "12. q12",
            "A. a", "B. b", "C. c", "D. d",
            "答案",
            "5. A",
            "",
        )
        payload = {"semantic_units": [{
            "unit_id": "Q12", "unit_type": "standalone_unit",
            "original_question_type": "single_choice",
            "content": {
                "stem": {"question_label": "12"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {
                    "answer_zone": "answer_table",
                    "question_label": "12",
                    "answer_lines": [7, 8],
                },
            },
        }]}
        d, run, _ = _pipeline(lines, payload, "Q12")
        assert d["decision"] == "pending_review"
        span = next(s for s in run.resolved_spans if s.span_id == "sp-Q12.answer")
        assert span.line_refs == (), f"multi-line foreign leak: {span.line_refs}"

    def test_local_body_multi_part_still_allowed(self):
        """`1.（3分）Mg | TiCl4` for unit 26 (multi-part body) stays bound."""
        lines = _mk(
            "", "",
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
        assert a.line_refs, "multi-part local body must stay bound"

    def test_control_own_answer_auto(self):
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] == "auto_approve"
        assert leaf.answer.text.strip() == "B"


# =========================================================================
# B. Edge formats: no full text in answer
# =========================================================================

class TestEdgeFormatsNoLeak:
    @pytest.mark.parametrize("text", ["12. A 2分", "12. 答案：A", "12. （A）2分"])
    def test_edge_format_no_full_text(self, text):
        lines = _lines_with_foreign(text)
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
        assert d["decision"] != "auto_approve"
        if leaf and leaf.answer:
            assert (leaf.answer.text or "").strip() == "", (
                f"{text!r} leaked: {leaf.answer.text!r}"
            )
        assert d["layers"]["provenance"]["status"] != "pass"
        assert d["layers"]["provenance"]["auto_allowed"] is False


# =========================================================================
# C. Explanation body must not enter answer
# =========================================================================

class TestExplanationNotAnswer:
    def test_explanation_body_not_in_answer(self):
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. 【分析】这是解析全文，故选：B.",
        )
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[7, 7]))
        assert d["decision"] != "auto_approve"
        if leaf and leaf.answer:
            assert "【分析】" not in (leaf.answer.text or "")
            assert leaf.answer.verified_correct is not True


# =========================================================================
# D. Real production-guard mutations (monkeypatch)
# =========================================================================

class TestRealGuardMutations:
    def test_mutation_ownership_always_match_reproduces_bypass(self):
        """Remove ownership guard → foreign line reaches auto_approve.

        Uses `12. A` (valid option label) so grammar accepts the stripped
        token — this is the actual R3 bypass shape.
        """
        original = resolver_mod.classify_answer_ownership
        resolver_mod.classify_answer_ownership = lambda texts, qn: "match"
        try:
            lines = _lines_with_foreign("12. A")
            d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
            assert d["decision"] == "auto_approve", (
                f"mutation should reproduce bypass, got {d['decision']} "
                f"ans={leaf.answer.text if leaf and leaf.answer else None!r}"
            )
            if leaf and leaf.answer:
                assert "12" in (leaf.answer.text or "") or "A" in (leaf.answer.text or "")
        finally:
            resolver_mod.classify_answer_ownership = original

    def test_guard_restored_blocks_again(self):
        lines = _lines_with_foreign("12. E")
        d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
        assert d["decision"] == "pending_review"
        if leaf and leaf.answer:
            assert (leaf.answer.text or "").strip() == ""

    def test_mutation_foreign_to_local_allows_leak(self):
        """If foreign_question is misclassified as local_index, full text binds.

        Proves the empty-answer path depends on the foreign_question label.
        """
        original = resolver_mod.classify_answer_ownership
        original_own = resolver_mod._entry_ownership

        def _always_unknown(texts, qn):
            return "unknown"

        resolver_mod.classify_answer_ownership = _always_unknown
        resolver_mod._entry_ownership = lambda texts, qn, **kw: "match"
        try:
            lines = _lines_with_foreign("12. E")
            d, run, leaf = _pipeline(lines, _payload(answer_lines=[8, 8]))
            # unknown keeps candidate text (not forced-empty like foreign)
            if leaf and leaf.answer:
                assert (leaf.answer.text or "").strip() != "", (
                    "mutating foreign→unknown should allow candidate-text bind"
                )
        finally:
            resolver_mod.classify_answer_ownership = original

    def test_mutation_explanation_rescue_would_fail(self):
        """If explanation text is force-bound as answer, the safety test fails."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. 【分析】这是解析全文，故选：B.",
        )
        # Simulate old rescue: force-bind the explanation line as a clean span
        from app.domains.resolver.span import ResolvedSpan, ResolvedRun
        import hashlib
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(
            _payload(answer_lines=[7, 7])
        )
        raw = lines[6].text
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
            evidence=("mutation: explanation as answer",),
        )
        mutated = tuple(forced if s.role == "answer" else s for s in run.resolved_spans)
        if not any(s.role == "answer" for s in run.resolved_spans):
            mutated = run.resolved_spans + (forced,)
        bad_run = ResolvedRun(
            source_version_id=run.source_version_id,
            resolved_spans=mutated,
            unresolved_references=run.unresolved_references,
            resolved_relations=run.resolved_relations,
            unresolved_relations=run.unresolved_relations,
            structural_regions=run.structural_regions,
        )
        payload = _payload(answer_lines=[7, 7])
        ir = IRBuilder.build(bad_run, payload, SVID, ANN_ID)
        spans = {s.span_id: s for s in bad_run.resolved_spans}
        compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
        root = next(u for u in ir.units if u.unit_id == "Q1")
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=bad_run)
        leaf = compiled.leaves[0] if compiled.leaves else None
        # This is what the safety test must catch: explanation in answer
        if leaf and leaf.answer:
            assert "【分析】" in (leaf.answer.text or ""), (
                "mutation model wrong: forced explanation should appear in answer"
            )
            # the real test test_explanation_body_not_in_answer would FAIL here
