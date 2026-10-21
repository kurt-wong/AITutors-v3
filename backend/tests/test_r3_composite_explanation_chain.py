# -*- coding: utf-8 -*-
"""R3-C: composite explanation full chain — annotation → targets → resolver → IR → compiled_roles."""
from __future__ import annotations

import uuid

from app.domains.compile.ir import IRBuilder
from app.domains.compile.compiler import Compiler
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.reference import extract_targets
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000c1")


def _mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


class TestCompositeExplanationChain:
    """R3-C: explanation goes from payload to compiled roles for composites."""

    def _composite_payload(self):
        return {"semantic_units": [{
            "unit_id": "U1-2",
            "unit_type": "composite_unit",
            "question_number_range": "1-2",
            "original_question_type": "reading",
            "shared_components": {"material": {"role": "material", "start_marker": {}}},
            "sub_questions": [
                {"unit_id": "U1-2.sub1", "unit_type": "standalone_unit",
                 "question_number": "1",
                 "content": {
                     "stem": {"question_label": "1", "question_search_lines": [4, 4]},
                     "options": [{"label": "A", "question_label": "1"},
                                  {"label": "B", "question_label": "1"},
                                  {"label": "C", "question_label": "1"},
                                  {"label": "D", "question_label": "1"}],
                     "answer": {"answer_zone": "answer_table", "question_label": "1",
                                 "answer_lines": [12, 12]},
                 }},
                {"unit_id": "U1-2.sub2", "unit_type": "standalone_unit",
                 "question_number": "2",
                 "content": {
                     "stem": {"question_label": "2", "question_search_lines": [8, 8]},
                     "options": [{"label": "A", "question_label": "2"},
                                  {"label": "B", "question_label": "2"},
                                  {"label": "C", "question_label": "2"},
                                  {"label": "D", "question_label": "2"}],
                     "answer": {"answer_zone": "answer_table", "question_label": "2",
                                 "answer_lines": [13, 13]},
                 }},
            ],
            "content": {
                "explanation": {
                    "role": "explanation",
                    "question_label": "",
                    "explanation_zone": "inline_explanation",
                    "explanation_lines": [15, 16],
                },
            },
        }]}

    def test_extract_targets_includes_composite_explanation(self):
        """extract_targets must produce explanation target for composite parent."""
        targets = extract_targets(self._composite_payload())
        expl_targets = [t for t in targets if t.role == "explanation"]
        assert len(expl_targets) == 1, f"expected 1 explanation target, got {expl_targets}"
        t = expl_targets[0]
        assert t.unit_id == "U1-2"
        assert t.target_id == "U1-2.explanation"
        assert t.evidence_lines == (15, 16)

    def test_resolver_resolves_composite_explanation(self):
        """Resolver must produce sp-U1-2.explanation span."""
        lines = _mk(
            "阅读材料。",           # L1
            "材料内容第一段。",      # L2
            "材料内容第二段。",      # L3
            "1. 第一题。",          # L4
            "A. 甲",               # L5
            "B. 乙",               # L6
            "C. 丙",               # L7
            "2. 第二题。",          # L8
            "A. 甲",               # L9
            "B. 乙",               # L10
            "C. 丙",               # L11
            "【答案】",             # L12
            "1. A",                # L13
            "2. B",                # L14
            "【解析】",             # L15
            "两题均考查阅读理解。",   # L16
        )
        payload = self._composite_payload()
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
        span_ids = {s.span_id for s in run.resolved_spans}
        assert "sp-U1-2.explanation" in span_ids, f"explanation span missing: {span_ids}"
        expl = next(s for s in run.resolved_spans if s.span_id == "sp-U1-2.explanation")
        assert "P1L015" in expl.line_refs or "P1L016" in expl.line_refs

    def test_ir_content_includes_explanation(self):
        """IR node content must have explanation item with span_id."""
        from app.domains.compile.ir import IRBuilder
        from app.domains.compile.compiler import Compiler
        lines = _mk(
            "阅读材料。", "材料内容第一段。", "材料内容第二段。",
            "1. 第一题。", "A. 甲", "B. 乙", "C. 丙",
            "2. 第二题。", "A. 甲", "B. 乙", "C. 丙",
            "【答案】", "1. A", "2. B",
            "【解析】", "两题均考查阅读理解。",
        )
        payload = self._composite_payload()
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
        ir = IRBuilder.build(run, payload, SVID, uuid.uuid4())
        # Find U1-2 node
        for node in ir.units:
            if node.unit_id == "U1-2":
                roles = {c.role for c in node.content}
                assert "explanation" in roles, f"IR content missing explanation: {roles}"
                expl_item = next(c for c in node.content if c.role == "explanation")
                assert expl_item.span_id == "sp-U1-2.explanation"
                assert not expl_item.unsupported
                break
        else:
            raise AssertionError("U1-2 not found in IR units")
