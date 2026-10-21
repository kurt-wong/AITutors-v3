# -*- coding: utf-8 -*-
"""P0-R3 regression: role_region overlap MUST block auto_approve.

Owner 2026-10 ruling: fabricated / wrong-region provenance cannot pass Gate.
This file previously locked "diagnostic-only, auto still allowed" — that was
the defect. It now locks the correct authority level:

  answer span overlapping question/stem or explanation region
    -> auto_allowed=False -> pending_review (not terminal rejected)

Also locks: value-only answers (no source line_refs) cannot auto_approve.
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


class TestRoleRegionBlocksAuto:
    def test_overlap_blocks_auto_pending_review(self):
        """P0-R3 core: overlap -> pending_review, diagnostic retained."""
        lines = _single_lines("A")
        root0, ir0, compiled0, base_run = _pipeline(lines, _single_payload())
        answer_span = next(s for s in base_run.resolved_spans if s.role == "answer")
        overlap_region = SourceRegion(
            role="explanation",
            start_seq=0,
            end_seq=999,
            line_refs=tuple(answer_span.line_refs) + ("P1L008",),
        )
        new_run = ResolvedRun(
            source_version_id=base_run.source_version_id,
            resolved_spans=base_run.resolved_spans,
            unresolved_references=base_run.unresolved_references,
            resolved_relations=base_run.resolved_relations,
            unresolved_relations=base_run.unresolved_relations,
            structural_regions=base_run.structural_regions + (overlap_region,),
        )
        d = evaluate(root=root0, ir=ir0, compiled=compiled0, resolved_run=new_run)
        assert d["decision"] == "pending_review", (
            f"role_region overlap must block auto, got {d['decision']}"
        )
        prov = d["layers"]["provenance"]
        assert prov["auto_allowed"] is False
        diags = prov.get("role_region_diagnostics") or []
        assert any("overlaps" in x for x in diags), (
            f"diagnostic reason must be retained, got {diags}"
        )

    def test_question_region_overlap_blocks_auto(self):
        lines = _single_lines("A")
        root0, ir0, compiled0, base_run = _pipeline(lines, _single_payload())
        answer_span = next(s for s in base_run.resolved_spans if s.role == "answer")
        overlap_region = SourceRegion(
            role="question", start_seq=0, end_seq=999,
            line_refs=tuple(answer_span.line_refs),
        )
        new_run = ResolvedRun(
            source_version_id=base_run.source_version_id,
            resolved_spans=base_run.resolved_spans,
            unresolved_references=base_run.unresolved_references,
            resolved_relations=base_run.resolved_relations,
            unresolved_relations=base_run.unresolved_relations,
            structural_regions=base_run.structural_regions + (overlap_region,),
        )
        d = evaluate(root=root0, ir=ir0, compiled=compiled0, resolved_run=new_run)
        assert d["decision"] == "pending_review"
        assert d["layers"]["provenance"]["auto_allowed"] is False

    def test_byte_proven_still_blocks_auto(self):
        """Byte-proven blocker remains: contextual resolution -> pending."""
        lines = _single_lines("A")
        root0, ir0, compiled0, base_run = _pipeline(lines, _single_payload())
        bad = []
        for s in base_run.resolved_spans:
            if s.role == "answer":
                bad.append(type(s)(
                    span_id=s.span_id, source_version_id=s.source_version_id,
                    role=s.role, start_line_ref=s.start_line_ref,
                    end_line_ref=s.end_line_ref, line_refs=s.line_refs,
                    granularity=s.granularity, start_offset=s.start_offset,
                    end_offset=s.end_offset, text_hash=s.text_hash,
                    resolution_status="contextual", evidence=s.evidence,
                ))
            else:
                bad.append(s)
        run2 = ResolvedRun(
            source_version_id=base_run.source_version_id,
            resolved_spans=tuple(bad),
            unresolved_references=base_run.unresolved_references,
            resolved_relations=base_run.resolved_relations,
            unresolved_relations=base_run.unresolved_relations,
            structural_regions=base_run.structural_regions,
        )
        d = evaluate(root=root0, ir=ir0, compiled=compiled0, resolved_run=run2)
        assert d["decision"] == "pending_review"
        assert any("byte-proven" in r for r in d["reasons"])

    def test_non_strict_auto_still_pending(self):
        """P1 boundary unchanged: short_answer is not auto."""
        lines = _mk("1. short answer?", "答案", "1. some text")
        payload = {"semantic_units": [
            {"unit_id": "Q1", "unit_type": "standalone_unit",
             "original_question_type": "short_answer",
             "content": {"stem": {"question_label": "1"},
                         "answer": {"answer_zone": "answer_table", "question_label": "1"}}}]}
        root, ir, compiled, run = _pipeline(lines, payload)
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        assert d["decision"] == "pending_review"
        assert any("not strict-auto" in r for r in d["reasons"])

    def test_value_only_answer_not_auto(self):
        """P0-R3: answer_value without source line_refs cannot auto_approve."""
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            "1. B",
        )
        payload = {"semantic_units": [
            {"unit_id": "Q1", "unit_type": "standalone_unit",
             "original_question_type": "single_choice",
             "content": {
                 "stem": {"question_label": "1"},
                 "options": [{"label": l} for l in "ABCD"],
                 "answer": {
                     "answer_zone": "answer_table",
                     "question_label": "1",
                     "answer_value": "B",
                 },
             }}]}
        root, ir, compiled, run = _pipeline(lines, payload)
        d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        assert d["decision"] == "pending_review", (
            f"value-only answer must not auto_approve, got {d['decision']}"
        )
        assert d["layers"]["provenance"]["auto_allowed"] is False
        # Must NOT fabricate question-region line_refs
        ans_span = next(s for s in run.resolved_spans if s.role == "answer")
        assert "P1L001" not in ans_span.line_refs, (
            f"value-only must not fabricate P1L001, got {ans_span.line_refs}"
        )
