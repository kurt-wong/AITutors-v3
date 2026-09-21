"""M.3 Boundary Tests — Question/Unit Canonical Vocabulary Invariants.

Owner D1 (FINALIZED) + 2026-09-20 Concept Correction:
  Question Type != Unit Type (orthogonal dimensions)
  Unit Type = {standalone_unit, composite_unit} ONLY
  Question Type = {single_choice, multiple_choice, ...} exam types
  standalone_question / composite_question = NOT legal canonical vocabulary

These tests verify canonical invariants, NOT mapping existence.
"""

import inspect


class TestUnitTypeCanonicalClosedSet:
    """B1 - Canonical Unit-Type closed set (Owner D1 Decision 1)."""

    def test_unit_types_contains_only_canonical_values(self):
        """UNIT_TYPES frozenset must be exactly {standalone_unit, composite_unit}."""
        from app.domains.gate import UNIT_TYPES

        assert UNIT_TYPES == frozenset({"standalone_unit", "composite_unit"}), (
            f"UNIT_TYPES must be {{standalone_unit, composite_unit}} per Owner D1, "
            f"got {UNIT_TYPES}"
        )

    def test_standalone_unit_is_legal_unit_type(self):
        """standalone_unit in UNIT_TYPES."""
        from app.domains.gate import UNIT_TYPES

        assert "standalone_unit" in UNIT_TYPES

    def test_composite_unit_is_legal_unit_type(self):
        """composite_unit in UNIT_TYPES."""
        from app.domains.gate import UNIT_TYPES

        assert "composite_unit" in UNIT_TYPES

    def test_standalone_question_is_not_legal_unit_type(self):
        """B2 - standalone_question not in UNIT_TYPES (forbidden by Owner D1)."""
        from app.domains.gate import UNIT_TYPES

        assert "standalone_question" not in UNIT_TYPES, (
            "standalone_question is NOT a legal canonical Unit Type per Owner D1"
        )

    def test_composite_question_is_not_legal_unit_type(self):
        """B2 - composite_question not in UNIT_TYPES (forbidden by Owner D1)."""
        from app.domains.gate import UNIT_TYPES

        assert "composite_question" not in UNIT_TYPES, (
            "composite_question is NOT a legal canonical Unit Type per Owner D1"
        )


class TestQuestionTypeCanonicalClosedSet:
    """B2 - Question-Type domain does not contain structural tokens."""

    def test_canonical_types_contains_exam_types(self):
        """CANONICAL_TYPES must contain exam question types."""
        from app.domains.compile import CANONICAL_TYPES

        assert "single_choice" in CANONICAL_TYPES
        assert "multiple_choice" in CANONICAL_TYPES
        assert "true_false" in CANONICAL_TYPES

    def test_standalone_question_is_not_question_type(self):
        """standalone_question not in CANONICAL_TYPES (not an exam type)."""
        from app.domains.compile import CANONICAL_TYPES

        assert "standalone_question" not in CANONICAL_TYPES, (
            "standalone_question is NOT a legal Question Type per Owner D1"
        )

    def test_composite_question_is_not_question_type(self):
        """composite_question not in CANONICAL_TYPES (not an exam type)."""
        from app.domains.compile import CANONICAL_TYPES

        assert "composite_question" not in CANONICAL_TYPES, (
            "composite_question is NOT a legal Question Type per Owner D1"
        )

    def test_unit_type_values_not_in_question_type_domain(self):
        """B3 - Unit Type values must not appear in Question Type domain."""
        from app.domains.compile import CANONICAL_TYPES

        assert "standalone_unit" not in CANONICAL_TYPES
        assert "composite_unit" not in CANONICAL_TYPES, (
            "Unit Type values must not be Question Types (orthogonal dimensions)"
        )


class TestIRCanonicalVocabulary:
    """B1 - IR outputs canonical Unit Type vocabulary."""

    def test_ir_builder_uses_canonical_vocabulary(self):
        """IRBuilder._node must use standalone_unit, not standalone_question."""
        from app.domains.compile.ir import IRBuilder

        source = inspect.getsource(IRBuilder._node)
        assert "standalone_unit" in source, (
            "IRBuilder must use canonical 'standalone_unit'"
        )
        assert "standalone_question" not in source, (
            "IRBuilder must NOT use legacy 'standalone_question'"
        )

    def test_ir_node_accepts_canonical_unit_type(self):
        """IRNode can be constructed with canonical Unit Type."""
        from app.domains.compile.ir import IRNode

        node = IRNode(
            unit_id="Q1",
            unit_type="standalone_unit",
            question_number="1",
            question_number_range=None,
            original_question_type="single_choice",
        )
        assert node.unit_type == "standalone_unit"

    def test_semantic_status_domain_separate_from_unit_type(self):
        """SEMANTIC_STATUS is a third dimension, not Unit Type."""
        from app.domains.compile import SEMANTIC_STATUS

        assert "standalone_unit" not in SEMANTIC_STATUS
        assert "composite_unit" not in SEMANTIC_STATUS
        assert "standalone_question" not in SEMANTIC_STATUS
        assert "ready" in SEMANTIC_STATUS
        assert "incomplete" in SEMANTIC_STATUS
        assert "unknown" in SEMANTIC_STATUS


class TestGateReceivesCanonicalVocabulary:
    """B6 - Gate receives canonical vocabulary from IR."""

    def test_gate_unit_types_definition_matches_d1(self):
        """Gate UNIT_TYPES definition matches Owner D1 closed set."""
        from app.domains.gate import UNIT_TYPES

        expected = frozenset({"standalone_unit", "composite_unit"})
        assert UNIT_TYPES == expected

    def test_gate_mapping_registry_not_imported_by_production(self):
        """mapping_registry is governance scaffold, not production enforcement."""
        import app.domains.gate.service as gate_service

        source = inspect.getsource(gate_service)
        assert "from app.domains.compile.mapping_registry" not in source, (
            "Gate service should NOT import mapping_registry (governance scaffold only)"
        )


class TestGateRuntimeBoundaryEnforcement:
    """Runtime Gate boundary — _candidate_unit_type fail-closed (M.3 F-M3-01)."""

    def test_canonical_standalone_unit_passes(self):
        """standalone_unit → allowed (returns as-is)."""
        from app.domains.gate.service import _candidate_unit_type

        assert _candidate_unit_type("standalone_unit") == "standalone_unit"

    def test_canonical_composite_unit_passes(self):
        """composite_unit → allowed (returns as-is)."""
        from app.domains.gate.service import _candidate_unit_type

        assert _candidate_unit_type("composite_unit") == "composite_unit"

    def test_standalone_question_rejected(self):
        """standalone_question → ValueError (not silent repair to standalone_unit)."""
        import pytest

        from app.domains.gate.service import _candidate_unit_type

        with pytest.raises(ValueError, match="non-canonical unit_type"):
            _candidate_unit_type("standalone_question")

    def test_composite_question_rejected(self):
        """composite_question → ValueError (not silent passthrough)."""
        import pytest

        from app.domains.gate.service import _candidate_unit_type

        with pytest.raises(ValueError, match="non-canonical unit_type"):
            _candidate_unit_type("composite_question")

    def test_garbage_string_rejected(self):
        """garbage_string → ValueError (not silent passthrough)."""
        import pytest

        from app.domains.gate.service import _candidate_unit_type

        with pytest.raises(ValueError, match="non-canonical unit_type"):
            _candidate_unit_type("garbage_string_xyz")

    def test_none_rejected(self):
        """None → ValueError (not silent passthrough)."""
        import pytest

        from app.domains.gate.service import _candidate_unit_type

        with pytest.raises(ValueError, match="non-canonical unit_type"):
            _candidate_unit_type(None)

    def test_empty_string_rejected(self):
        """Empty string → ValueError."""
        import pytest

        from app.domains.gate.service import _candidate_unit_type

        with pytest.raises(ValueError, match="non-canonical unit_type"):
            _candidate_unit_type("")

    def test_no_silent_repair_mapping_exists(self):
        """_IR_TO_CANDIDATE_UNIT_TYPE dict must not exist in gate/service.py."""
        import app.domains.gate.service as gate_service

        assert not hasattr(gate_service, "_IR_TO_CANDIDATE_UNIT_TYPE"), (
            "_IR_TO_CANDIDATE_UNIT_TYPE must be deleted (M.3: no runtime mapping)"
        )

    def test_no_silent_passthrough_in_source(self):
        """gate/service.py must not contain silent passthrough pattern .get(ir_unit_type, ir_unit_type)."""
        import app.domains.gate.service as gate_service

        source = inspect.getsource(gate_service)
        assert ".get(ir_unit_type, ir_unit_type)" not in source, (
            "Silent passthrough pattern must be removed from gate/service.py"
        )


class TestExecutorCanonicalVocabulary:
    """Executor prompt uses canonical Unit Type vocabulary (M.3 F-M3-02)."""

    def test_prompt_unit_type_enum_is_canonical(self):
        """Annotation prompt declares unit_type ∈ {standalone_unit, composite_unit}."""
        from app.domains.task.executor import _ANNOTATION_PROMPT_PREFIX

        assert '"standalone_unit"' in _ANNOTATION_PROMPT_PREFIX, (
            "Executor prompt must declare standalone_unit as canonical Unit Type"
        )
        assert '"composite_unit"' in _ANNOTATION_PROMPT_PREFIX, (
            "Executor prompt must declare composite_unit as canonical Unit Type"
        )
        assert "standalone_question" not in _ANNOTATION_PROMPT_PREFIX, (
            "Executor prompt must NOT declare standalone_question as V3 Unit Type"
        )
        assert "composite_question" not in _ANNOTATION_PROMPT_PREFIX, (
            "Executor prompt must NOT declare composite_question as V3 Unit Type"
        )

    def test_prompt_example_uses_canonical_vocabulary(self):
        """Annotation prompt example JSON uses standalone_unit, not standalone_question."""
        from app.domains.task.executor import _ANNOTATION_PROMPT_PREFIX

        assert '"unit_type": "standalone_unit"' in _ANNOTATION_PROMPT_PREFIX, (
            "Executor prompt example must use canonical standalone_unit"
        )
        assert '"unit_type": "standalone_question"' not in _ANNOTATION_PROMPT_PREFIX, (
            "Executor prompt example must NOT use legacy standalone_question"
        )

    def test_prompt_question_type_separate_from_unit_type(self):
        """Prompt keeps Question Type (original_question_type) separate from Unit Type."""
        from app.domains.task.executor import _ANNOTATION_PROMPT_PREFIX

        assert "original_question_type" in _ANNOTATION_PROMPT_PREFIX, (
            "Prompt must declare original_question_type (Question Type dimension)"
        )
        assert "single_choice" in _ANNOTATION_PROMPT_PREFIX, (
            "Prompt must declare exam types in original_question_type"
        )


class TestWorkerCanonicalVocabulary:
    """Worker mock annotation uses canonical Unit Type vocabulary (M.3 F-M3-03)."""

    def test_mock_annotation_uses_canonical_unit_type(self):
        """Worker _MOCK_ANNOTATION uses standalone_unit, not standalone_question."""
        import json

        from app.worker.__main__ import _MOCK_ANNOTATION

        data = json.loads(_MOCK_ANNOTATION)
        units = data["semantic_units"]
        assert len(units) > 0
        for unit in units:
            assert unit["unit_type"] == "standalone_unit", (
                f"Worker mock unit_type={unit['unit_type']!r} must be canonical "
                f"'standalone_unit' (M.3 F-M3-03)"
            )
            assert unit["unit_type"] not in ("standalone_question", "composite_question"), (
                f"Worker mock must not use legacy vocabulary: {unit['unit_type']!r}"
            )

    def test_mock_annotation_source_no_legacy_vocabulary(self):
        """Worker __main__.py source does not contain standalone_question."""
        import app.worker.__main__ as worker_main

        source = inspect.getsource(worker_main)
        assert "standalone_question" not in source, (
            "Worker __main__.py must not contain legacy 'standalone_question' "
            "in production default data (M.3 F-M3-03)"
        )
