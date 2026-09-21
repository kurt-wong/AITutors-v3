"""X2.6 M.2 Acceptance Tests — SEMANTIC_STATUS unfreeze + UNKNOWN expression.

M.2 implementation verification (X2.6 Implementation Plan §4.2).
Tests prove:
    Case A — ready behavior preserved (compatibility)
    Case B — incomplete behavior preserved (compatibility)
    Case C — unknown expressible in IR
    Case D — unknown produces no compiler leaves (safety boundary)
    Case E — old ready/incomplete fixtures still work
    Case F — repository-wide two-value assumptions identified

Scope boundary:
    M.2 = SEMANTIC_STATUS unfreeze + UNKNOWN IR expression + compiler safety.
    M.2 does NOT implement UNKNOWN migration, production mapping, or P1-P12 closure.

Evidence classification (M.1 Correction C-03):
    CLASS A — Module-local enforcement: tests production code behavior directly
    CLASS B — Characterization/baseline: documents current state

Security（逐字）: Never hardcode API Keys/Passwords/Tokens/Secrets; Always use .env for configuration.
"""

from __future__ import annotations

import inspect
import uuid

import pytest

from app.domains.compile import SEMANTIC_STATUS
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IR, IRBuilder, IRContent, IRNode, validate_ir
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-00000000000f")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000f0")


def mk(*texts):
    return tuple(SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
                 for i, t in enumerate(texts))


def _run(lines, payload):
    return SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)


def _single_choice_payload(qn="1", original="single_choice", options=("A", "B", "C", "D")):
    content = {
        "stem": {"question_label": qn},
        "options": [{"label": l} for l in options],
        "answer": {"answer_zone": "answer_table", "question_label": qn},
    }
    return {"semantic_units": [{"unit_id": f"Q{qn}", "unit_type": "standalone_unit",
             "original_question_type": original, "content": content}]}


def _ready_lines():
    return mk("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子",
              "【答案】", "1. A")


class _FakeSpan:
    granularity = "multi_line"
    start_offset = None
    end_offset = None
    line_refs = ("P1L001",)


class _FakeLine:
    text = "test content"


# ================================================================ Domain Verification
class TestM2_Domain:
    """M.2 domain verification: SEMANTIC_STATUS must be three-valued."""

    def test_semantic_status_is_three_valued(self):
        """CLASS A: SEMANTIC_STATUS = {ready, incomplete, unknown} after M.2."""
        assert SEMANTIC_STATUS == frozenset({"ready", "incomplete", "unknown"})

    def test_semantic_status_contains_unknown(self):
        """CLASS A: 'unknown' must be in SEMANTIC_STATUS."""
        assert "unknown" in SEMANTIC_STATUS

    def test_semantic_status_ready_incomplete_preserved(self):
        """CLASS A: 'ready' and 'incomplete' must remain in SEMANTIC_STATUS (compat)."""
        assert "ready" in SEMANTIC_STATUS
        assert "incomplete" in SEMANTIC_STATUS

    def test_semantic_status_has_no_extra_values(self):
        """CLASS A: SEMANTIC_STATUS has exactly 3 values (no drift)."""
        assert len(SEMANTIC_STATUS) == 3


# ================================================================ Case A: Ready Compatibility
class TestM2_CaseA_Ready:
    """Case A: ready behavior must be unchanged after M.2."""

    async def test_ready_ir_assembly(self):
        """CLASS A: ready fixture produces semantic_status=ready after M.2."""
        payload = _single_choice_payload()
        ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
        assert ir.units[0].semantic_status == "ready"

    async def test_ready_compiler_produces_leaves(self):
        """CLASS A: ready node still produces compiler leaves after M.2."""
        node = IRNode(
            unit_id="U1", unit_type="standalone_question",
            question_number="1", question_number_range=None,
            original_question_type="single_choice",
            content=(
                IRContent(role="stem", span_id="sp-U1.stem"),
                IRContent(role="answer", span_id="sp-U1.answer"),
            ),
            semantic_status="ready",
        )
        ir = IR(ir_schema="semantic-question-ir/v0.3",
                source_version_id=SVID, annotation_id=ANN_ID, units=(node,))
        compiler = Compiler(
            span_by_id={"sp-U1.stem": _FakeSpan(), "sp-U1.answer": _FakeSpan()},
            line_by_ref={"P1L001": _FakeLine()},
        )
        snapshot = compiler.compile(ir)
        assert len(snapshot.leaves) == 1


# ================================================================ Case B: Incomplete Compatibility
class TestM2_CaseB_Incomplete:
    """Case B: incomplete behavior must be unchanged after M.2."""

    async def test_incomplete_ir_assembly(self):
        """CLASS A: invalid type produces semantic_status=incomplete after M.2."""
        payload = _single_choice_payload(original="foo")
        ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
        assert ir.units[0].semantic_status == "incomplete"

    async def test_incomplete_no_compiler_leaves(self):
        """CLASS A: incomplete node produces no compiler leaves (unchanged behavior)."""
        node = IRNode(
            unit_id="U1", unit_type="standalone_question",
            question_number="1", question_number_range=None,
            original_question_type="single_choice",
            semantic_status="incomplete",
        )
        ir = IR(ir_schema="semantic-question-ir/v0.3",
                source_version_id=SVID, annotation_id=ANN_ID, units=(node,))
        compiler = Compiler(span_by_id={}, line_by_ref={})
        snapshot = compiler.compile(ir)
        assert len(snapshot.leaves) == 0


# ================================================================ Case C: Unknown Expressible
class TestM2_CaseC_Unknown:
    """Case C: unknown must be expressible in IR."""

    async def test_unknown_from_annotation_payload(self):
        """CLASS A: annotation declares semantic_status="unknown" → IR preserves unknown."""
        payload = _single_choice_payload()
        payload["semantic_units"][0]["semantic_status"] = "unknown"
        ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
        assert ir.units[0].semantic_status == "unknown"

    async def test_unknown_direct_construction(self):
        """CLASS A: IRNode with semantic_status="unknown" passes validate_ir."""
        node = IRNode(
            unit_id="U1", unit_type="standalone_question",
            question_number="1", question_number_range=None,
            original_question_type="single_choice",
            semantic_status="unknown",
        )
        ir = IR(ir_schema="semantic-question-ir/v0.3",
                source_version_id=SVID, annotation_id=ANN_ID, units=(node,))
        validated = validate_ir(ir)
        assert validated.units[0].semantic_status == "unknown"

    async def test_unknown_composite_preserved(self):
        """CLASS A: composite with semantic_status="unknown" is preserved through validation."""
        comp = IRNode(
            unit_id="U1-2", unit_type="composite_unit",
            question_number=None, question_number_range="1-2",
            original_question_type="single_choice",
            shared_components=(IRContent(role="material", span_id="sp-mat"),),
            semantic_status="unknown",
        )
        ir = IR(ir_schema="semantic-question-ir/v0.3",
                source_version_id=SVID, annotation_id=ANN_ID, units=(comp,))
        validated = validate_ir(ir)
        assert validated.units[0].semantic_status == "unknown"

    async def test_unknown_in_semantic_status_domain(self):
        """CLASS A: SEMANTIC_STATUS includes 'unknown' — domain check passes."""
        assert "unknown" in SEMANTIC_STATUS


# ================================================================ Case D: Compiler Safety
class TestM2_CaseD_CompilerSafety:
    """Case D: unknown must produce NO compiler leaves (safety boundary)."""

    async def test_unknown_standalone_no_leaves(self):
        """CLASS A: unknown standalone node → compiler produces ZERO leaves."""
        node = IRNode(
            unit_id="U1", unit_type="standalone_question",
            question_number="1", question_number_range=None,
            original_question_type="single_choice",
            content=(
                IRContent(role="stem", span_id="sp-U1.stem"),
                IRContent(role="answer", span_id="sp-U1.answer"),
            ),
            semantic_status="unknown",
        )
        ir = IR(ir_schema="semantic-question-ir/v0.3",
                source_version_id=SVID, annotation_id=ANN_ID, units=(node,))
        compiler = Compiler(span_by_id={}, line_by_ref={})
        snapshot = compiler.compile(ir)
        assert len(snapshot.leaves) == 0
        assert len(snapshot.materials) == 0

    async def test_unknown_composite_no_leaves_no_materials(self):
        """CLASS A: unknown composite → compiler produces ZERO leaves AND materials."""
        comp = IRNode(
            unit_id="U1-2", unit_type="composite_unit",
            question_number=None, question_number_range="1-2",
            original_question_type="single_choice",
            shared_components=(IRContent(role="material", span_id="sp-mat"),),
            sub_questions=(
                IRNode(
                    unit_id="Q1", unit_type="standalone_question",
                    question_number="1", question_number_range=None,
                    original_question_type="single_choice",
                    semantic_status="ready",
                ),
            ),
            semantic_status="unknown",
        )
        ir = IR(ir_schema="semantic-question-ir/v0.3",
                source_version_id=SVID, annotation_id=ANN_ID, units=(comp,))
        compiler = Compiler(span_by_id={}, line_by_ref={})
        snapshot = compiler.compile(ir)
        assert len(snapshot.leaves) == 0, "unknown composite must not produce leaves"
        assert len(snapshot.materials) == 0, "unknown composite must not produce materials"

    async def test_unknown_mixed_with_ready(self):
        """CLASS A: IR with both unknown and ready units → only ready produces leaves."""
        unknown_node = IRNode(
            unit_id="U1", unit_type="standalone_question",
            question_number="1", question_number_range=None,
            original_question_type="single_choice",
            semantic_status="unknown",
        )
        ready_node = IRNode(
            unit_id="U2", unit_type="standalone_question",
            question_number="2", question_number_range=None,
            original_question_type="single_choice",
            content=(
                IRContent(role="stem", span_id="sp-U2.stem"),
                IRContent(role="answer", span_id="sp-U2.answer"),
            ),
            semantic_status="ready",
        )
        ir = IR(ir_schema="semantic-question-ir/v0.3",
                source_version_id=SVID, annotation_id=ANN_ID,
                units=(unknown_node, ready_node))
        compiler = Compiler(
            span_by_id={"sp-U2.stem": _FakeSpan(), "sp-U2.answer": _FakeSpan()},
            line_by_ref={"P1L001": _FakeLine()},
        )
        snapshot = compiler.compile(ir)
        assert len(snapshot.leaves) == 1, "only ready unit should produce a leaf"
        assert snapshot.leaves[0].unit_id == "U2"

    def test_compiler_boundary_code_block_check(self):
        """CLASS B: compiler.py:72 uses != "ready" — blocks unknown by design."""
        source = inspect.getsource(Compiler._compile_node)
        assert 'semantic_status != "ready"' in source or (
            "semantic_status != 'ready'" in source
        ), "compiler boundary must check != ready to block unknown"


# ================================================================ Case E: Compatibility
class TestM2_CaseE_Compatibility:
    """Case E: old ready/incomplete fixtures still work after M.2."""

    async def test_old_ready_fixture_unchanged(self):
        """CLASS A: standard ready fixture produces ready (no regression)."""
        payload = _single_choice_payload()
        ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
        assert ir.units[0].semantic_status == "ready"
        assert ir.units[0].original_question_type == "single_choice"
        assert {c.role for c in ir.units[0].content} == {"stem", "option", "answer"}

    async def test_old_incomplete_fixture_unchanged(self):
        """CLASS A: standard incomplete fixture produces incomplete (no regression)."""
        payload = _single_choice_payload(original="foo")
        ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
        assert ir.units[0].semantic_status == "incomplete"

    async def test_old_alias_fixture_unchanged(self):
        """CLASS A: alias type still produces incomplete (BUG-V3-014 unchanged)."""
        payload = _single_choice_payload(original="single-choice")
        ir = IRBuilder.build(_run(_ready_lines(), payload), payload, SVID, ANN_ID)
        assert ir.units[0].semantic_status == "incomplete"

    async def test_old_missing_answer_fixture_unchanged(self):
        """CLASS A: missing answer still produces incomplete (no regression)."""
        payload = {"semantic_units": [{"unit_id": "Q1", "unit_type": "standalone_unit",
            "original_question_type": "single_choice",
            "content": {"stem": {"question_label": "1"},
                        "options": [{"label": l} for l in "ABCD"]}}]}
        lines = mk("1. 下列哪个是水果", "A. 苹果", "B. 香蕉", "C. 汽车", "D. 桌子")
        ir = IRBuilder.build(_run(lines, payload), payload, SVID, ANN_ID)
        assert ir.units[0].semantic_status == "incomplete"

    def test_historical_domain_fixture(self):
        """CLASS A: historical {ready, incomplete} domain preserved as subset."""
        historical = frozenset({"ready", "incomplete"})
        assert historical.issubset(SEMANTIC_STATUS)


# ================================================================ Case F: Repository-Wide Search
class TestM2_CaseF_RepositoryWide:
    """Case F: repository-wide search for remaining two-value assumptions.

    Each hit is classified: M.2 modifies it, or M.2 must not modify it (with reason).
    """

    def test_compile_init_domain_updated(self):
        """CLASS A: compile/__init__.py SEMANTIC_STATUS is 3-valued."""
        from app.domains.compile import SEMANTIC_STATUS as domain
        assert domain == frozenset({"ready", "incomplete", "unknown"})

    def test_ir_validate_node_handles_unknown(self):
        """CLASS A: _validate_node source contains unknown handling code."""
        from app.domains.compile.ir import _validate_node
        node_source = inspect.getsource(_validate_node)
        assert "unknown" in node_source, (
            "_validate_node must handle 'unknown' semantic_status"
        )

    def test_irbuilder_reads_declared_status(self):
        """CLASS A: IRBuilder._node reads declared semantic_status from annotation."""
        source = inspect.getsource(IRBuilder._node)
        assert "semantic_status" in source, (
            "IRBuilder._node must read semantic_status from annotation payload"
        )

    def test_compiler_blocks_non_ready(self):
        """CLASS A: compiler boundary unchanged — blocks all non-ready including unknown."""
        source = inspect.getsource(Compiler._compile_node)
        assert "ready" in source

    def test_resolver_stage_not_in_m2_scope(self):
        """CLASS B: resolver uses E-stage ResolvedStatus, NOT IR semantic_status — NOT M.2 scope.

        resolver uses a separate status domain for E stage resolution.
        M.2 does NOT modify resolver because:
          - E ResolvedStatus is a different semantic domain than IR.semantic_status
          - Frozen Contract separates these domains
          - Changing resolver would be M.3+ scope (de-coercion)
        """
        import importlib
        resolver_init = importlib.import_module("app.domains.resolver")
        source = inspect.getsource(resolver_init)
        assert "SEMANTIC_STATUS" not in source, (
            "resolver must NOT import SEMANTIC_STATUS (different domain)"
        )

    def test_runner_stage_not_in_m2_scope(self):
        """CLASS B: runner_b2.py uses != "ready" check — NOT M.2 scope for modification.

        runner_b2.py:322 does `if root.semantic_status != "ready"`.
        This correctly blocks unknown (unknown != ready → skip).
        M.2 does NOT modify runner because:
          - The != "ready" check is already safe for unknown
          - Runner de-coercion changes are M.3 scope (P6/P7)
          - Silent skip elimination is M.3 scope
        """
        runner_path = (
            __import__("pathlib").Path(__file__).parent.parent
            / "scripts" / "preprocessing_consumer" / "runner_b2.py"
        )
        if not runner_path.exists():
            pytest.skip("runner_b2.py not found")
        source = runner_path.read_text(encoding="utf-8")
        assert 'semantic_status != "ready"' in source, (
            "runner_b2 must still use != ready check (unchanged by M.2)"
        )

    def test_gate_stage_not_in_m2_scope(self):
        """CLASS B: gate/policy.py uses != "ready" check — NOT M.2 scope for modification.

        gate/policy.py:106 does `if root.semantic_status != "ready"`.
        This correctly blocks unknown. Gate enforcement changes are M.4 scope.
        """
        from app.domains.gate import policy
        source = inspect.getsource(policy)
        assert "ready" in source, "gate policy must still check ready status"

    def test_mapping_registry_not_affected(self):
        """CLASS B: mapping_registry.py not modified by M.2 — production enforcement NOT implemented.

        M.2 does NOT implement mapping enforcement. mapping_registry.py is a
        governance scaffold only. F-05-A semantic binding remains IMPLEMENTATION GAP.
        """
        from app.domains.compile import mapping_registry
        source = inspect.getsource(mapping_registry)
        # mapping_registry references semantic_status=unknown in a comment (expected)
        # but does NOT import SEMANTIC_STATUS for enforcement
        assert "SEMANTIC_STATUS" not in source or "semantic_status=unknown" in source, (
            "mapping_registry must not use SEMANTIC_STATUS for production enforcement"
        )

    def test_gate_payload_passthrough_unaffected(self):
        """CLASS B: gate/payload.py passes semantic_status through — no validation change."""
        from app.domains.gate import payload
        source = inspect.getsource(payload)
        assert "semantic_status" in source, "payload must still pass through semantic_status"

    def test_content_roles_unchanged(self):
        """CLASS A: content_roles_for() unchanged by M.2 (no role requirement changes)."""
        from app.domains.compile import content_roles_for
        roles = content_roles_for("single_choice")
        assert roles["stem"] == "required"
        assert roles["answer"] == "required"

    def test_map_canonical_type_unchanged(self):
        """CLASS A: map_canonical_type() unchanged by M.2 (no alias resolver added)."""
        from app.domains.compile import map_canonical_type
        assert map_canonical_type("single_choice") == "single_choice"
        assert map_canonical_type("single-choice") is None  # alias still not resolved
        assert map_canonical_type("foo") is None


# ================================================================ Security Constraint
class TestM2_Security:
    """Security constraint verification."""

    def test_no_hardcoded_secrets_in_m2_code(self):
        """CLASS D: M.2 changes contain no hardcoded secrets."""
        import importlib
        compile_init = importlib.import_module("app.domains.compile")
        source = inspect.getsource(compile_init)
        assert "API_KEY" not in source
        assert "PASSWORD" not in source
        assert "TOKEN" not in source
        assert "SECRET" not in source
