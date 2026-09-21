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
