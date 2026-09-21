"""Source Evidence structural consistency tests.

Gate span-overlap consistency check: answer span must not fall into
explanation/question structural regions. This is contract self-consistency
(span set intersection), NOT NLP semantic understanding.

Architecture:
- Resolver uses deterministic header grammar (H-3) to partition structural regions
- Region map frozen into ResolvedRun.structural_regions (consistency evidence,
  NOT semantic truth)
- Gate verifies answer span does not overlap other structural regions
- Overlap -> auto_allowed=False -> pending_review (not terminal rejected)
"""

import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import (
    ResolvedRun,
    SourceLineView,
    SourceRegion,
)

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f1")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a1")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _single_lines(answer_text="A"):
    # Header must match is_answer_header grammar: exact token "答案" (Chinese)
    return _mk(
        "1. which fruit",
        "A. apple", "B. banana", "C. car", "D. table",
        "答案",
        f"1. {answer_text}",
    )


def _single_payload(ctype="single_choice"):
    return {"semantic_units": [
        {"unit_id": "Q1", "unit_type": "standalone_unit", "original_question_type": ctype,
         "content": {"stem": {"question_label": "1"},
                     "options": [{"label": l} for l in "ABCD"],
                     "answer": {"answer_zone": "answer_table", "question_label": "1"}}}]}


def _pipeline(lines, payload, root_unit_id="Q1"):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    lines_by_ref = {l.line_ref: l for l in lines}
    compiled = Compiler(spans, lines_by_ref).compile(ir)
    root = next(u for u in ir.units if u.unit_id == root_unit_id)
    return root, ir, compiled, run


class TestSemanticRegionsProduction:
    """Verify Resolver produces structural_regions map."""

    def test_resolver_produces_question_region(self):
        lines = _single_lines("A")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_single_payload())
        assert run.structural_regions, "Resolver should produce structural_regions"
        roles = {r.role for r in run.structural_regions}
        assert "question" in roles, f"Should have question region, got {roles}"

    def test_resolver_produces_answer_region(self):
        lines = _single_lines("A")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_single_payload())
        roles = {r.role for r in run.structural_regions}
        assert "answer" in roles, f"Should have answer region, got {roles}"

    def test_answer_region_excludes_question_lines(self):
        lines = _single_lines("A")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_single_payload())
        q_region = next(r for r in run.structural_regions if r.role == "question")
        a_region = next(r for r in run.structural_regions if r.role == "answer")
        overlap = set(q_region.line_refs) & set(a_region.line_refs)
        assert not overlap, f"question/answer regions should not overlap, got {overlap}"

    def test_no_explanation_header_no_explanation_region(self):
        lines = _single_lines("A")
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(_single_payload())
        roles = {r.role for r in run.structural_regions}
        assert "explanation" not in roles, "No explanation header -> no explanation region"


class TestRoleProvenanceContract:
    """Verify Gate role-provenance: answer span must not overlap other role regions."""

    def _make_overlapping_run(self, explanation_lines):
        lines = _single_lines("A")
        root, ir, compiled, base_run = _pipeline(lines, _single_payload())
        answer_span = next(s for s in base_run.resolved_spans if s.role == "answer")
        overlap_region = SourceRegion(
            role="explanation",
            start_seq=0,
            end_seq=999,
            line_refs=tuple(explanation_lines),
        )
        new_run = ResolvedRun(
            source_version_id=base_run.source_version_id,
            resolved_spans=base_run.resolved_spans,
            unresolved_references=base_run.unresolved_references,
            resolved_relations=base_run.resolved_relations,
            unresolved_relations=base_run.unresolved_relations,
            structural_regions=base_run.structural_regions + (overlap_region,),
        )
        return root, ir, compiled, new_run, answer_span

    def test_answer_overlapping_explanation_region_pending(self):
        """answer span overlaps explanation region -> pending_review."""
        lines = _single_lines("A")
        root0, ir0, compiled0, base_run = _pipeline(lines, _single_payload())
        ans_span = next(s for s in base_run.resolved_spans if s.role == "answer")
        root, ir, compiled, run, _ = self._make_overlapping_run(
            explanation_lines=list(ans_span.line_refs) + ["P1L008"],
        )
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        assert d["decision"] == "pending_review", (
            f"answer cap explanation != empty -> pending_review, got {d['decision']}"
        )
        reasons = " ".join(d["reasons"])
        assert "role provenance" in reasons or "overlaps" in reasons, (
            f"reasons should mention role provenance, got: {reasons}"
        )

    def test_answer_overlapping_question_region_pending(self):
        """answer span overlaps question region -> pending_review."""
        lines = _single_lines("A")
        root, ir, compiled, base_run = _pipeline(lines, _single_payload())
        answer_span = next(s for s in base_run.resolved_spans if s.role == "answer")
        overlap_region = SourceRegion(
            role="question",
            start_seq=0,
            end_seq=999,
            line_refs=answer_span.line_refs,
        )
        new_run = ResolvedRun(
            source_version_id=base_run.source_version_id,
            resolved_spans=base_run.resolved_spans,
            unresolved_references=base_run.unresolved_references,
            resolved_relations=base_run.resolved_relations,
            unresolved_relations=base_run.unresolved_relations,
            structural_regions=base_run.structural_regions + (overlap_region,),
        )
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=new_run)
        assert d["decision"] == "pending_review", (
            f"answer cap question != empty -> pending_review, got {d['decision']}"
        )

    def test_no_overlap_auto_approve(self):
        """No overlap -> normal auto_approve."""
        lines = _single_lines("A")
        root, ir, compiled, run = _pipeline(lines, _single_payload())
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        assert d["decision"] == "auto_approve", (
            f"No overlap should auto_approve, got {d['decision']}"
        )

    def test_cross_role_overlap_fail_closed(self):
        """answer_lines overlap explanation_lines -> fail closed."""
        lines = _single_lines("A")
        root0, ir0, compiled0, base_run = _pipeline(lines, _single_payload())
        ans_span = next(s for s in base_run.resolved_spans if s.role == "answer")
        root, ir, compiled, run, _ = self._make_overlapping_run(
            explanation_lines=list(ans_span.line_refs),
        )
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        assert d["decision"] != "auto_approve", "Overlap must never auto_approve"
        assert d["decision"] == "pending_review", f"Should pending_review, got {d['decision']}"


class TestRoleProvenanceE2ERegression:
    """End-to-end regression: EXPLANATION_REGION corpus all pending_review."""

    def test_explanation_region_targets_all_non_strict_auto(self):
        """49 EXPLANATION_REGION targets are all non-strict-auto (fail-closed via grammar-None).

        Type dist: short_answer(41), reading(3), vocabulary_fill(2),
        cloze(1), reading_expression(1), essay(1). None in STRICT_AUTO_TYPES.
        """
        import json
        from pathlib import Path

        corpus_path = Path(__file__).parent.parent / "Docs" / "V3_SPEC" / "gate_c_invalid_binding_corpus.json"
        if not corpus_path.exists():
            pytest.skip("Corpus file not found")

        with open(corpus_path, "r", encoding="utf-8") as f:
            corpus = json.load(f)

        explanation_targets = [
            t for t in corpus["targets"]
            if t.get("invalid_reason") == "EXPLANATION_REGION"
        ]
        assert len(explanation_targets) == 49, (
            f"EXPLANATION_REGION should have 49 targets, got {len(explanation_targets)}"
        )

        strict_auto_v2 = ("single_choice", "multiple_choice", "true_false")
        for t in explanation_targets:
            qt = t.get("original_question_type", "")
            assert qt not in strict_auto_v2, (
                f"EXPLANATION_REGION target should not be strict-auto, got {qt}"
            )

    def test_strict_auto_answer_token_contract_enforced(self):
        """BUG-V3-044 FIXED：AnswerTokenContract 封闭 Evidence Admission Boundary。

        旧实现 `verify(sc, "【解答】A", labels) is True`（记录为 unclosed
        boundary）。用户裁决 2026-09-13 采用 Q-A 白名单：剥除题号前缀后，
        答案文本必须完全落在允许形态内，否则 None → pending_review。
        本测试从「记录缺陷」反转为「锁死修复」。
        """
        from app.domains.gate.grammar import verify

        # 合法 token 形态仍通过
        assert verify("single_choice", "A", ("A", "B", "C", "D")) is True
        assert verify("single_choice", "1. A", ("A", "B", "C", "D")) is True
        assert verify("single_choice", "（A）", ("A", "B", "C", "D")) is True
        assert verify("single_choice", "A、", ("A", "B", "C", "D")) is True

        # 解释性前缀 / 非 token 正文 → None（不得 auto）
        for polluted in (
            "【解答】A",
            "【考点】A",
            "参见教材A册第三章",
            "见解析A页",
            "正确答案为A",
            "1. 【考点】本题考查词义辨析。【解答】A",
        ):
            assert verify("single_choice", polluted, ("A", "B", "C", "D")) is None, (
                f"AnswerTokenContract must reject non-token answer text: {polluted!r}"
            )


class TestEvidencePromotionNegative:
    """C-3: Evidence Promotion Negative Tests.

    Prove that structurally valid addresses with wrong evidence cannot be
    promoted to validated evidence. Each test constructs a scenario where
    the address resolves correctly but the evidence identity is wrong.
    """

    def test_answer_span_in_explanation_region_rejected(self):
        """Answer span pointing at explanation region -> pending_review."""
        lines = _single_lines("A")
        root, ir, compiled, base_run = _pipeline(lines, _single_payload())
        answer_span = next(s for s in base_run.resolved_spans if s.role == "answer")

        # Construct: explanation region covers the answer span's lines
        bad_region = SourceRegion(
            role="explanation",
            start_seq=0,
            end_seq=999,
            line_refs=answer_span.line_refs,
        )
        bad_run = ResolvedRun(
            source_version_id=base_run.source_version_id,
            resolved_spans=base_run.resolved_spans,
            unresolved_references=base_run.unresolved_references,
            resolved_relations=base_run.resolved_relations,
            unresolved_relations=base_run.unresolved_relations,
            structural_regions=base_run.structural_regions + (bad_region,),
        )
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=bad_run)
        assert d["decision"] == "pending_review"

    def test_answer_span_in_question_region_rejected(self):
        """Answer span pointing at question region -> pending_review."""
        lines = _single_lines("A")
        root, ir, compiled, base_run = _pipeline(lines, _single_payload())
        answer_span = next(s for s in base_run.resolved_spans if s.role == "answer")

        bad_region = SourceRegion(
            role="question",
            start_seq=0,
            end_seq=999,
            line_refs=answer_span.line_refs,
        )
        bad_run = ResolvedRun(
            source_version_id=base_run.source_version_id,
            resolved_spans=base_run.resolved_spans,
            unresolved_references=base_run.unresolved_references,
            resolved_relations=base_run.resolved_relations,
            unresolved_relations=base_run.unresolved_relations,
            structural_regions=base_run.structural_regions + (bad_region,),
        )
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=bad_run)
        assert d["decision"] == "pending_review"

    def test_non_strict_auto_always_pending(self):
        """Non-strict-auto type with any answer content -> pending_review.

        Proves grammar-None path: even if answer text looks like a valid option,
        non-strict-auto types cannot auto_approve.
        """
        lines = _single_lines("A")
        payload = _single_payload("short_answer")
        root, ir, compiled, run = _pipeline(lines, payload)
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        assert d["decision"] == "pending_review", (
            f"short_answer should pending_review, got {d['decision']}"
        )

    def test_text_hash_mismatch_rejected(self):
        """Evidence text_hash mismatch -> rejected (terminal)."""
        import dataclasses

        lines = _single_lines("A")
        root, ir, compiled, run = _pipeline(lines, _single_payload())

        # Tamper with compiled answer text_hash
        leaf = compiled.leaves[0]
        tampered_answer = dataclasses.replace(
            leaf.answer,
            text_hash="0" * 64,  # invalid hash
        )
        tampered_leaf = dataclasses.replace(leaf, answer=tampered_answer)
        tampered_snap = dataclasses.replace(
            compiled,
            leaves=(tampered_leaf,),
        )
        d = evaluate(root=root, ir=ir, compiled=tampered_snap, resolved_run=run)
        assert d["decision"] == "rejected", (
            f"text_hash mismatch should reject, got {d['decision']}"
        )

    def test_missing_span_not_traceable_rejected(self):
        """Answer span not in ResolvedRun -> rejected (structural failure)."""
        import dataclasses

        lines = _single_lines("A")
        root, ir, compiled, run = _pipeline(lines, _single_payload())

        # Remove answer span from resolved run
        filtered_spans = tuple(
            s for s in run.resolved_spans if s.role != "answer"
        )
        empty_run = dataclasses.replace(run, resolved_spans=filtered_spans)
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=empty_run)
        assert d["decision"] == "rejected", (
            f"missing answer span should reject, got {d['decision']}"
        )

    def test_legal_region_illegal_role_rejected(self):
        """Legal answer region content claimed as explanation role -> pending_review.

        Attack: answer region contains valid-looking text, but the claim binds
        it as explanation. Structural consistency catches this because the
        answer span would overlap the explanation structural region.
        """
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. A",
            "解析",
            "1. Because apple is a fruit",
        )
        payload = _single_payload()
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)

        # Verify structural regions are produced
        assert run.structural_regions
        roles = {r.role for r in run.structural_regions}
        assert "answer" in roles
        assert "explanation" in roles

        # Answer span and explanation region should be disjoint
        ans_spans = [s for s in run.resolved_spans if s.role == "answer"]
        expl_region = next(
            (r for r in run.structural_regions if r.role == "explanation"), None
        )
        if ans_spans and expl_region:
            overlap = set(ans_spans[0].line_refs) & set(expl_region.line_refs)
            assert not overlap, (
                f"answer span should not overlap explanation region, got {overlap}"
            )

    def test_cross_version_provenance_mismatch_rejected(self):
        """Span from one version, hash from another -> rejected.

        Attack: answer span references source_v1 lines, but text_hash matches
        source_v2 content. text_hash integrity check must catch this.
        """
        import dataclasses
        import hashlib

        lines = _single_lines("A")
        root, ir, compiled, run = _pipeline(lines, _single_payload())

        # Tamper: set text_hash to hash of different content
        fake_hash = hashlib.sha256("B".encode("utf-8")).hexdigest()
        leaf = compiled.leaves[0]
        tampered_answer = dataclasses.replace(
            leaf.answer,
            text_hash=fake_hash,  # hash of "B" but text is "A"
        )
        tampered_leaf = dataclasses.replace(leaf, answer=tampered_answer)
        tampered_snap = dataclasses.replace(
            compiled,
            leaves=(tampered_leaf,),
        )
        d = evaluate(root=root, ir=ir, compiled=tampered_snap, resolved_run=run)
        assert d["decision"] == "rejected", (
            f"cross-version hash mismatch should reject, got {d['decision']}"
        )
        reasons = " ".join(d["reasons"])
        assert "text_hash mismatch" in reasons or "evidence broken" in reasons
