# -*- coding: utf-8 -*-
"""E2E-009R2: U45-48 shared-material marker must be uniquely locatable.

EN 2018 reading B: material starts at `## B`, which substring-matches
`## Beauty…` / `## Blocks…` / `## Big Feed…`. The old first-non-empty-line
marker became ambiguous → IR incomplete → composite vanished with no
candidate row.
"""
from __future__ import annotations

from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)
from app.domains.source.subq_expand import expand_composite_sub_questions

_LINES = [
    "",  # 0
    "## A",  # 1
    "Passage A text about Glasgow",
    "1. Q1 stem",
    "A. a B. b C. c D. d",
    "2. Q2 stem",
    "A. a B. b C. c D. d",
    "## Beauty and the Beast",  # 7 — shares prefix `## B`
    "## Blocks Workshops",
    "## Big Feed",
    "## B",  # 10 — U45-48 material head
    "## Travelling Alone in Toronto",  # 11 — unique
    "Passage B body line",
    "45. What is Toronto?",
    "A. a B. b C. c D. d",
    "46. Why travel alone?",
    "A. a B. b C. c D. d",
    "1 A 2 B 45 C 46 D",
]


def _manifest():
    return {
        "identity_version": 2,
        "source_content_sha256": "a" * 64,
        "units": [
            {
                "unit_id": "U45-48",
                "unit_type": "composite_question",
                "question_numbers": [45, 46],
                "original_question_type": "reading",
                "material_lines": [10, 12],
                "questions_lines": [10, 17],
                "options_lines": [14, 17],
                "answer_lines": [18, 18],
                "options": [
                    {"label": "A", "start_line": 14, "end_line": 14},
                    {"label": "B", "start_line": 14, "end_line": 14},
                    {"label": "C", "start_line": 14, "end_line": 14},
                    {"label": "D", "start_line": 14, "end_line": 14},
                ],
            }
        ],
    }


class TestU4548MaterialMarker:
    def test_marker_is_unique_not_short_heading(self):
        bound = bind_units_from_manifest(_manifest(), _LINES, source_content_sha256="a" * 64)
        bu = bound[0]
        assert bu.material_shared, "material_shared missing"
        marker = bu.material_shared["start_marker"]["text"]
        # must NOT be the ambiguous short heading
        assert marker != "## B", marker
        # must uniquely locate
        hits = sum(1 for line in _LINES if marker in line)
        assert hits == 1, (marker, hits)

    def test_composite_still_expands_and_is_traceable(self):
        r = expand_composite_sub_questions(
            _LINES,
            question_numbers=[45, 46],
            questions_range=(13, 17),
            answer_range=(18, 18),
            original_question_type="reading",
            has_declared_options=True,
        )
        assert r.unit_reason is None
        assert [s.question_number for s in r.sub_questions] == [45, 46]

    def test_declared_composite_never_silent_when_material_unlocatable(self):
        """If material marker cannot uniquely locate, bind must still emit a
        marker dict so the unit fails with a resolver/IR reason — not vanish."""
        lines = list(_LINES)
        # every material line ambiguous
        lines[10] = "## B"
        lines[11] = "## B"
        lines[12] = "## B"
        bound = bind_units_from_manifest(
            {
                **_manifest(),
                "units": [
                    {
                        **_manifest()["units"][0],
                        "material_lines": [10, 12],
                    }
                ],
            },
            lines,
            source_content_sha256="a" * 64,
        )
        bu = bound[0]
        # still has a declared marker (fallback) — resolver will report ambiguous
        assert bu.material_shared.get("start_marker", {}).get("text")
        # payload carries the composite + subs (terminal later at IR, with reason)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="a" * 64, manifest_identity_version=2
        )
        unit = payload["semantic_units"][0]
        assert unit["unit_id"] == "U45-48"
        assert unit.get("shared_components") or unit.get("content", {}).get("material")
        assert unit.get("sub_questions")
