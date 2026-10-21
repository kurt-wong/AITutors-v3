"""R2-2: Manifest formal entry — discriminative boundary tests.

Real formal path: load_manifest -> manifest_to_annotation_payload
-> SourceResolver.resolve.

Field mapping in the formal adapter (annotation_adapter._leaf_content):
  - questions_lines -> stem question_search_lines (preferred stem window)
  - stem_lines -> question_search_lines (fallback when questions_lines missing)
  - answer_lines -> answer.answer_lines (answer evidence range)
  - options_lines -> content.options_range (option search window)
  - options (ManifestOption list) -> option labels

Discriminative interference: decoy content OUTSIDE declared ranges that
would be picked up if declarations were ignored. Wrong values MUST fail
the test.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.binding_fact import get_registry
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

_BACKEND = Path(__file__).resolve().parents[1]
_SCRIPTS = _BACKEND / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from preprocessing_consumer.manifest_reader import (  # noqa: E402
    Manifest,
    ManifestOption,
    ManifestUnit,
    load_manifest,
)
from preprocessing_consumer.annotation_adapter import (  # noqa: E402
    manifest_to_annotation_payload,
)

SVID = uuid.UUID("00000000-0000-0000-0000-00000000d002")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-00000000a002")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


@pytest.fixture(autouse=True)
def _clean_registry():
    get_registry().clear()
    yield
    get_registry().clear()


def _make_manifest(units: list[dict]) -> Manifest:
    """Build a Manifest from dicts for controlled formal-entry tests."""
    manifest_units = []
    for u in units:
        opts = None
        if u.get("options"):
            opts = tuple(
                ManifestOption(
                    label=opt["label"],
                    start_line=opt["start_line"],
                    end_line=opt["end_line"],
                )
                for opt in u["options"]
            )
        manifest_units.append(ManifestUnit(
            unit_id=u["unit_id"],
            unit_type=u.get("unit_type", "standalone_question"),
            question_numbers=tuple(u.get("question_numbers", [])),
            original_question_type=u.get("original_question_type", "single_choice"),
            section=u.get("section"),
            printed_number=u.get("printed_number"),
            stem_lines=tuple(u["stem_lines"]) if u.get("stem_lines") else None,
            options_lines=tuple(u["options_lines"]) if u.get("options_lines") else None,
            options=opts,
            extra_lines=tuple(u["extra_lines"]) if u.get("extra_lines") else None,
            answer_lines=tuple(u["answer_lines"]) if u.get("answer_lines") else None,
            explanation_lines=tuple(u["explanation_lines"]) if u.get("explanation_lines") else None,
            material_lines=tuple(u["material_lines"]) if u.get("material_lines") else None,
            questions_lines=tuple(u["questions_lines"]) if u.get("questions_lines") else None,
            answer_evidence_type=u.get("answer_evidence_type"),
            answer_evidence_lines=tuple(u["answer_evidence_lines"]) if u.get("answer_evidence_lines") else None,
            answer_evidence_value=u.get("answer_evidence_value"),
        ))
    return Manifest(
        source_file="test.md", model="test", prompt_version="test",
        validation_issues=[], warnings=[], units=manifest_units,
        source_content_sha256="0" * 64, identity_version="v1",
        sections=[], subject="test", grade="test", grade_source=None,
    )


class TestFormalEntryDeclaredRanges:
    """Formal path must consume declared ranges with discriminative power."""

    def test_answer_lines_boundary_discriminative(self):
        """Decoy answer OUTSIDE declared answer_lines must NOT be picked up.

        Source:
          line 1:  1. What is 2+2?
          line 2-5: A. 3 / B. 4 / C. 5 / D. 6
          line 6:  答案
          line 7:  1. A              <-- declared answer_lines=[7,7], CORRECT
          line 8:  1. Z              <-- DECOY outside declared range
          line 9:  详解: answer is Z   <-- DECOY

        If resolver ignores answer_lines and rescans, it may find "Z".
        Test asserts answer == "A" (from declared range).
        """
        lines = _mk(
            "1. What is 2+2?", "A. 3", "B. 4", "C. 5", "D. 6",
            "答案",
            "1. A",              # line 7: declared
            "1. Z",              # line 8: DECOY
            "详解: The answer is Z (wrong decoy).",  # line 9: DECOY
        )
        manifest = _make_manifest([{
            "unit_id": "Q1",
            "question_numbers": [1],
            "original_question_type": "single_choice",
            "questions_lines": [1, 5],  # adapter maps this to question_search_lines
            "answer_lines": [7, 7],
            "answer_evidence_type": "answer_table",
            "answer_evidence_value": "A",
            "options": [
                {"label": "A", "start_line": 2, "end_line": 2},
                {"label": "B", "start_line": 3, "end_line": 3},
                {"label": "C", "start_line": 4, "end_line": 4},
                {"label": "D", "start_line": 5, "end_line": 5},
            ],
        }])
        payload_meta = manifest_to_annotation_payload(manifest)

        # Verify the adapter DID map answer_lines into the payload
        units = payload_meta.get("semantic_units") or []
        assert len(units) == 1
        ans = units[0].get("content", {}).get("answer", {})
        assert ans.get("answer_lines") == [7, 7], (
            f"adapter must map answer_lines, got {ans.get('answer_lines')}"
        )

        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload_meta)

        answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
        assert answer_spans, "answer must resolve"
        for s in answer_spans:
            assert all(r == "P1L007" for r in s.line_refs), (
                f"answer escaped declared answer_lines[7,7]: "
                f"{s.line_refs} {s.evidence}"
            )

        # Compiled answer must be "A", not decoy "Z"
        ir = IRBuilder.build(run, payload_meta, SVID, ANN_ID)
        spans = {s.span_id: s for s in run.resolved_spans}
        compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
        for leaf in compiled.leaves:
            if leaf.answer is not None:
                assert leaf.answer.candidate_text.strip() == "A", (
                    f"answer must be 'A' (declared line 7), "
                    f"got {leaf.answer.candidate_text!r}"
                )

    def test_questions_lines_boundary_discriminative(self):
        """Same-QN decoy INSIDE search area but OUTSIDE declared window.

        R4 fix: decoy is in the natural question search area (between
        question start and answer header) but outside the declared
        question_search_lines=[1,3]. Without the window constraint, the
        resolver fails (ambiguous/no stem or wrong stem). With it, it picks line 1.

        Source:
          line 1:  1. What is 2+2?       <- declared stem (correct)
          line 2:  A. 3
          line 3:  B. 4
          line 4:  1. DECOY: What is 9+9? <- SAME-QN, in search area,
          line 5:  C. 5                       outside declared window [1,3]
          line 6:  D. 6
          line 7:  \u7b54\u6848
          line 8:  1. A
        """
        lines = _mk(
            "1. What is 2+2?",
            "A. 3",
            "B. 4",
            "1. DECOY: What is 9+9?",
            "C. 5",
            "D. 6",
            "\u7b54\u6848",
            "1. A",
        )
        manifest = _make_manifest([{
            "unit_id": "Q1",
            "question_numbers": [1],
            "original_question_type": "single_choice",
            "questions_lines": [1, 3],
            "answer_lines": [8, 8],
            "answer_evidence_type": "answer_table",
            "answer_evidence_value": "A",
            "options": [
                {"label": "A", "start_line": 2, "end_line": 2},
                {"label": "B", "start_line": 3, "end_line": 3},
                {"label": "C", "start_line": 5, "end_line": 5},
                {"label": "D", "start_line": 6, "end_line": 6},
            ],
        }])
        payload_meta = manifest_to_annotation_payload(manifest)

        stem = payload_meta["semantic_units"][0]["content"]["stem"]
        assert stem.get("question_search_lines") == [1, 3], (
            f"adapter must map questions_lines, got {stem.get('question_search_lines')}"
        )

        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload_meta)

        stem_spans = [s for s in run.resolved_spans if s.role == "stem"]
        assert stem_spans, "stem must resolve"
        for s in stem_spans:
            for ref in s.line_refs:
                seq = int(ref.replace("P1L", ""))
                assert 1 <= seq <= 3, (
                    f"stem escaped declared window[1,3], picked up "
                    f"line {seq} (same-QN decoy): {s.line_refs} {s.evidence}"
                )

    def test_answer_value_without_lines_no_rescan(self):
        """answer_evidence_value with no answer_lines: value-only bind.

        Source has a decoy answer on line 6 that must NOT be picked up.
        """
        lines = _mk(
            "1. What is 2+2?",
            "A. 3", "B. 4", "C. 5", "D. 6",
            "答案: Z",          # line 6: DECOY answer
        )
        manifest = _make_manifest([{
            "unit_id": "Q1",
            "question_numbers": [1],
            "original_question_type": "single_choice",
            "questions_lines": [1, 5],
            "answer_evidence_type": "answer_table",
            "answer_evidence_value": "B",
            "options": [
                {"label": "A", "start_line": 2, "end_line": 2},
                {"label": "B", "start_line": 3, "end_line": 3},
                {"label": "C", "start_line": 4, "end_line": 4},
                {"label": "D", "start_line": 5, "end_line": 5},
            ],
        }])
        payload_meta = manifest_to_annotation_payload(manifest)
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload_meta)

        answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
        assert run.resolved_spans, "resolve must produce spans"
        all_refs = [ref for s in answer_spans for ref in (s.line_refs or [])]
        assert "P1L006" not in all_refs, (
            f"answer_value path rescanned decoy line 6: {all_refs}"
        )
        for s in answer_spans:
            if s.line_refs:
                for ref in s.line_refs:
                    seq = int(ref.replace("P1L", ""))
                    assert seq != 6, (
                        f"answer_value path rescanned decoy line 6: "
                        f"{s.evidence} {s.line_refs}"
                    )

    def test_missing_declared_ranges_fails_closed(self):
        """No answer_lines and no answer_value: must NOT silently rescan.

        Source has a tempting "答案: B" that must not be auto-picked-up.
        """
        lines = _mk(
            "1. What is 2+2?",
            "A. 3", "B. 4", "C. 5", "D. 6",
            "答案: B",          # line 6: tempting for rescan
        )
        manifest = _make_manifest([{
            "unit_id": "Q1",
            "question_numbers": [1],
            "original_question_type": "single_choice",
            "questions_lines": [1, 5],
            # NO answer_lines, NO answer_evidence_value
            "options": [
                {"label": "A", "start_line": 2, "end_line": 2},
                {"label": "B", "start_line": 3, "end_line": 3},
                {"label": "C", "start_line": 4, "end_line": 4},
                {"label": "D", "start_line": 5, "end_line": 5},
            ],
        }])
        payload_meta = manifest_to_annotation_payload(manifest)
        run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload_meta)

        answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
        assert run.resolved_spans, "resolve must produce spans"
        all_refs = [ref for s in answer_spans for ref in (s.line_refs or [])]
        assert "P1L006" not in all_refs, (
            f"answer silently rescanned undeclared line 6: {all_refs}"
        )
        for s in answer_spans:
            if s.line_refs:
                for ref in s.line_refs:
                    seq = int(ref.replace("P1L", ""))
                    assert seq != 6, (
                        f"answer silently rescanned undeclared line 6: "
                        f"{s.evidence} {s.line_refs}"
                    )

    def test_formal_entry_load_manifest_to_resolve_end_to_end(self):
        """Real load_manifest (from JSON file) -> adapter -> resolve.

        Exercises the REAL load_manifest code path (JSON parsing, field
        mapping) and verifies the full formal chain.
        """
        import tempfile

        manifest_dict = {
            "source_file": "test.md",
            "model": "test",
            "prompt_version": "test",
            "validation_issues": [],
            "warnings": [],
            "source_content_sha256": "0" * 64,
            "identity_version": "v1",
            "sections": [],
            "subject": "test",
            "grade": "test",
            "units": [{
                "unit_id": "Q1",
                "unit_type": "standalone_question",
                "question_numbers": [1],
                "original_question_type": "single_choice",
                "printed_number": "1",
                "questions_lines": [1, 5],
                "options": [
                    {"label": "A", "start_line": 2, "end_line": 2},
                    {"label": "B", "start_line": 3, "end_line": 3},
                    {"label": "C", "start_line": 4, "end_line": 4},
                    {"label": "D", "start_line": 5, "end_line": 5},
                ],
                "answer_lines": [7, 7],
                "answer_evidence": {
                    "type": "answer_table",
                    "lines": [7, 7],
                    "value": "B",
                },
            }],
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".manifest.json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(manifest_dict, f, ensure_ascii=False)
            tmp_path = Path(f.name)

        try:
            # REAL load_manifest from JSON
            manifest = load_manifest(tmp_path)
            assert len(manifest.units) == 1
            u = manifest.units[0]
            assert u.unit_id == "Q1"
            assert u.answer_evidence_value == "B", (
                f"load_manifest must map answer_evidence.value, "
                f"got {u.answer_evidence_value}"
            )
            assert u.answer_lines == (7, 7)

            lines = _mk(
                "1. What is 2+2?",
                "A. 3", "B. 4", "C. 5", "D. 6",
                "答案",
                "1. B",
                "1. DECOY",  # outside declared range
            )
            payload_meta = manifest_to_annotation_payload(manifest)
            run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload_meta)

            answer_spans = [s for s in run.resolved_spans if s.role == "answer"]
            assert answer_spans
            for s in answer_spans:
                assert all(r == "P1L007" for r in s.line_refs), (
                    f"answer escaped declared lines: {s.line_refs}"
                )

            # Compiled answer must be "B"
            ir = IRBuilder.build(run, payload_meta, SVID, ANN_ID)
            spans = {s.span_id: s for s in run.resolved_spans}
            compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)
            for leaf in compiled.leaves:
                if leaf.answer is not None:
                    assert leaf.answer.candidate_text.strip() == "B", (
                        f"expected 'B', got {leaf.answer.candidate_text!r}"
                    )
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_adapter_field_mapping_documented(self):
        """Formal adapter field mapping: questions_lines takes priority.

        When BOTH questions_lines and stem_lines are present,
        questions_lines wins (no ambiguity).
        """
        m = _make_manifest([{
            "unit_id": "Q1",
            "question_numbers": [1],
            "original_question_type": "single_choice",
            "questions_lines": [1, 5],
            "stem_lines": [6, 7],       # different — must NOT override
            "options_lines": [2, 5],
            "answer_lines": [7, 7],
            "answer_evidence_value": "A",
            "options": [
                {"label": "A", "start_line": 2, "end_line": 2},
                {"label": "B", "start_line": 3, "end_line": 3},
            ],
        }])
        payload = manifest_to_annotation_payload(m)
        unit = payload["semantic_units"][0]
        stem = unit["content"]["stem"]
        ans = unit["content"]["answer"]

        # questions_lines takes priority
        assert stem.get("question_search_lines") == [1, 5], (
            f"questions_lines must take priority, got {stem.get('question_search_lines')}"
        )
        # answer_lines is mapped
        assert ans.get("answer_lines") == [7, 7]
        # options_lines is mapped
        assert unit["content"].get("options_range") == [2, 5]

    def test_stem_lines_fallback_when_questions_lines_missing(self):
        """R4: stem_lines fallback must work when questions_lines is None.

        questions_lines=None, stem_lines=[1,5] -> question_search_lines=[1,5]
        """
        m = _make_manifest([{
            "unit_id": "Q1",
            "question_numbers": [1],
            "original_question_type": "single_choice",
            "questions_lines": None,    # MISSING
            "stem_lines": [1, 5],       # fallback source
            "options_lines": [2, 5],
            "answer_lines": [7, 7],
            "answer_evidence_value": "A",
            "options": [
                {"label": "A", "start_line": 2, "end_line": 2},
                {"label": "B", "start_line": 3, "end_line": 3},
            ],
        }])
        payload = manifest_to_annotation_payload(m)
        unit = payload["semantic_units"][0]
        stem = unit["content"]["stem"]

        # CRITICAL: stem_lines must be used as fallback
        assert stem.get("question_search_lines") == [1, 5], (
            f"stem_lines fallback must map to question_search_lines when "
            f"questions_lines is None, got {stem.get('question_search_lines')}"
        )
