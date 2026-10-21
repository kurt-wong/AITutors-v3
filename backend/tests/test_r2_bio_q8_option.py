# -*- coding: utf-8 -*-
"""R2 Fix D: option-pattern content in extra_lines goes to options, not stem."""
from __future__ import annotations

import uuid

from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f2")


def _mk(*texts: str) -> tuple[SourceLineView, ...]:
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _resolve(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)


class TestBIOQ8OptionRole:
    """Fix D: D option in extra_lines classified as option, not stem."""

    def test_d_option_detected_in_extras(self):
        """BIO Q8: "D. $O_2$" in extra_lines → label D with evidence_lines."""
        lines = [
            "8. 若判定运动员在运动时肌肉细胞是否进行了无氧呼吸",  # L1  stem
            "A. 乳酸 B. ADP C. CO2",                           # L2  options (declared)
            "",                                                # L3
            "D. $O_2$",                                        # L4  extra (option pattern!)
        ]
        man = {"units": [{
            "unit_id": "Q8", "unit_type": "standalone_question",
            "question_numbers": [8], "original_question_type": "single_choice",
            "stem_lines": [1, 1], "options_lines": [2, 2],
            "extra_lines": [4, 4], "answer_lines": [4, 4],
            "options": [
                {"label": "A", "start_line": 2, "end_line": 2},
                {"label": "B", "start_line": 2, "end_line": 2},
                {"label": "C", "start_line": 2, "end_line": 2},
            ],
        }]}
        bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="a" * 64, manifest_identity_version=2)
        u = payload["semantic_units"][0]
        opts = u["content"].get("options", [])
        labels = [o["label"] for o in opts]
        assert "D" in labels, f"D not in options: {labels}"
        # R3-D: D has evidence_lines pointing to L4 (not options_range expansion)
        d_opt = next(o for o in opts if o["label"] == "D")
        assert d_opt.get("evidence_lines") == [4, 4], f"D missing evidence_lines: {d_opt}"
        # options_range is NOT expanded (stays at declared [2,2])
        opt_range = u["content"].get("options_range")
        assert opt_range == [2, 2], f"options_range should stay [2,2]: {opt_range}"

    def test_d_option_not_in_stem(self):
        """Option-pattern lines must NOT enter stem via extra union."""
        lines = _mk(
            "8. stem text",                      # L1
            "A. 乳酸 B. ADP C. CO2",             # L2
            "",
            "D. $O_2$",                          # L4 (option pattern)
        )
        payload = {"semantic_units": [{
            "unit_id": "Q8", "unit_type": "standalone_question",
            "question_number": "8",
            "content": {
                "stem": {"question_label": "8",
                          "question_search_lines": [1, 1],
                          "stem_lines": [1, 1],
                          "extra_lines": [4, 4]},
                "options": [{"label": l, "question_label": "8"} for l in "ABCD"],
                "options_range": [1, 4],
                "answer": {"answer_zone": "answer_table", "question_label": "8",
                            "answer_lines": [4, 4]},
            },
        }]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q8.stem")
        refs = list(stem.line_refs)
        assert "P1L001" in refs
        assert "P1L004" not in refs, f"option D leaked into stem: {refs}"

    def test_non_option_extra_still_in_stem(self):
        """Non-option-pattern extras (images, continuation) stay in stem."""
        lines = _mk(
            "8. stem text",                      # L1
            "A. 乳酸 B. ADP C. CO2",             # L2
            "",
            "<img pic>",                         # L4 (image - not option pattern)
            "continuation text",                 # L5 (not option pattern)
        )
        payload = {"semantic_units": [{
            "unit_id": "Q8", "unit_type": "standalone_question",
            "question_number": "8",
            "content": {
                "stem": {"question_label": "8",
                          "question_search_lines": [1, 1],
                          "stem_lines": [1, 1],
                          "extra_lines": [4, 5]},
                "options": [{"label": l, "question_label": "8"} for l in "ABC"],
                "answer": {"answer_zone": "answer_table", "question_label": "8",
                            "answer_lines": [5, 5]},
            },
        }]}
        run = _resolve(lines, payload)
        stem = next(s for s in run.resolved_spans if s.span_id == "sp-Q8.stem")
        refs = list(stem.line_refs)
        assert "P1L004" in refs, f"image extra lost: {refs}"
        assert "P1L005" in refs, f"continuation extra lost: {refs}"
