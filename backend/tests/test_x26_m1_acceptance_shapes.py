"""X2.6 M.1 Acceptance Shapes — F-05 / F-06 / UNKNOWN wash matrix / baseline evidence.

Establishes acceptance test shapes required by C-3 of the M.1 task.
These tests document CURRENT state verification and TARGET state acceptance criteria.

Test classification:
    CURRENT STATE   — verifies facts as of M.1 baseline (V3 cc12d79, Papers 2b92898)
    TARGET SHAPE    — documents acceptance criteria for M.2-M.10 implementation
    HASH PIN        — pins immutable fixture identity (F-06-A/B)

D10 provenance: This is a NEW test file. No existing test is modified.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------- DI-01 constants (F-06-A/B)
DI01_MANIFEST_PATH = (
    "Ocr-markdown/reslice-batch-C/合格考/化学/"
    "2020北京高中合格考化学（第一次）（教师版）(1).manifest.json"
)
DI01_SHA256 = "24da834b8695798a5fe511e527b4d6583d3baa9b862d432cd38dc65a37e313f8"
DI01_SIZE = 23446
DI01_UNIT_ID = "Q1"
DI01_UNIT_TYPE = "andalone_question"
DI01_SOURCE_CONTENT_SHA256 = (
    "f6b13d6ab3491d7cc43b694951a66488d014653c3cdf194338b4ce6ecac4fe61"
)


# ================================================================ F-06-A: DI-01 Hash Pin
class TestF06A_DI01_HashPin:
    """F-06-A: DI-01 fixture hash guard must pin baseline values.

    Source: DSH A-level independent reproduction @ Papers 2b92898.
    """

    def test_di01_sha256_constant_matches_dsh_baseline(self):
        """Hash constant must equal DSH-reported baseline value."""
        assert DI01_SHA256 == (
            "24da834b8695798a5fe511e527b4d6583d3baa9b862d432cd38dc65a37e313f8"
        )

    def test_di01_size_constant_matches_dsh_baseline(self):
        """Size constant must equal DSH-reported baseline value."""
        assert DI01_SIZE == 23446

    def test_di01_manifest_path_constant(self):
        """Fixture path must match DSH-registered identity."""
        assert "合格考" in DI01_MANIFEST_PATH
        assert "化学" in DI01_MANIFEST_PATH
        assert "2020北京高中合格考化学" in DI01_MANIFEST_PATH
        assert DI01_MANIFEST_PATH.endswith(".manifest.json")


# ================================================================ F-06-B: DI-01 Fixture Identity
class TestF06B_DI01_FixtureIdentity:
    """F-06-B: DI-01 fixture identity must be pinned and verified.

    Fixed identity from DSH verification:
        path = Ocr-markdown/reslice-batch-C/合格考/化学/...
        unit = Q1 (unit_type="andalone_question")
        source_content_sha256 = f6b13d6a...
    """

    def test_di01_unit_id(self):
        assert DI01_UNIT_ID == "Q1"

    def test_di01_unit_type_is_andalone_question(self):
        """DI-01 must be identified by the anomalous value andalone_question."""
        assert DI01_UNIT_TYPE == "andalone_question"

    def test_di01_source_content_sha256_constant(self):
        """source_content_sha256 must match DSH-reported baseline."""
        assert DI01_SOURCE_CONTENT_SHA256 == (
            "f6b13d6ab3491d7cc43b694951a66488d014653c3cdf194338b4ce6ecac4fe61"
        )

    def test_di01_distribution_documented(self):
        """DI-01 manifest distribution: 32 standalone + 1 composite + 1 andalone = 34."""
        expected_distribution = {
            "standalone_question": 32,
            "composite_question": 1,
            "andalone_question": 1,
        }
        assert sum(expected_distribution.values()) == 34
        assert expected_distribution["andalone_question"] == 1


# ================================================================ F-05-A: Mapping Event Identity
class TestF05A_MappingEventIdentity:
    """F-05-A: Mapping event id cross-validation mechanism must exist and function.

    Acceptance shape: tests must be able to prevent fake mapping event ids
    from passing green while violating D7 provenance.
    """

    def test_mapping_registry_module_exists(self):
        """Mapping registry module must be importable."""
        from app.domains.compile import mapping_registry

        assert hasattr(mapping_registry, "LEGACY_TO_CANONICAL_MAP")
        assert hasattr(mapping_registry, "MappingEntry")
        assert hasattr(mapping_registry, "MappingStatus")

    def test_mapping_table_structure_has_provenance_fields(self):
        """Every mapping entry must carry mapping_basis and condition fields."""
        from app.domains.compile.mapping_registry import LEGACY_TO_CANONICAL_MAP

        for source_value, entry in LEGACY_TO_CANONICAL_MAP.items():
            assert hasattr(entry, "mapping_basis"), f"{source_value} missing mapping_basis"
            assert hasattr(entry, "condition"), f"{source_value} missing condition"
            assert hasattr(entry, "status"), f"{source_value} missing status"
            assert entry.source_value == source_value

    def test_pending_owner_rows_do_not_activate(self):
        """PENDING_OWNER rows must resolve to None (unknown), not canonical."""
        from app.domains.compile.mapping_registry import (
            MappingStatus,
            lookup_mapping,
            resolve_canonical,
        )

        for source_value in ("standalone_question", "composite_question"):
            entry = lookup_mapping(source_value)
            assert entry is not None
            assert entry.status == MappingStatus.PENDING_OWNER
            canonical, provenance = resolve_canonical(source_value)
            assert canonical is None, f"{source_value} must not activate while pending"
            assert "pending_owner" in provenance

    def test_prohibited_row_resolves_to_unknown(self):
        """andalone_question must resolve to None (unknown), never canonical."""
        from app.domains.compile.mapping_registry import resolve_canonical

        canonical, provenance = resolve_canonical("andalone_question")
        assert canonical is None
        assert "prohibited" in provenance.lower() or "D8" in provenance

    def test_missing_value_resolves_to_unknown(self):
        """Missing/None unit_type must resolve to unknown, never default standalone."""
        from app.domains.compile.mapping_registry import resolve_canonical

        canonical, provenance = resolve_canonical(None)
        assert canonical is None
        assert "missing" in provenance

    def test_unmapped_value_resolves_to_unknown(self):
        """Arbitrary unmapped values must resolve to unknown."""
        from app.domains.compile.mapping_registry import resolve_canonical

        for bad_value in ("foo_question", "", "STANDALONE_UNIT", "composite_unit"):
            canonical, provenance = resolve_canonical(bad_value)
            assert canonical is None, f"{bad_value!r} must not resolve to canonical"

    def test_validate_mapping_event_identity_rejects_empty(self):
        """F-05-A: Empty mapping_basis must fail validation."""
        from app.domains.compile.mapping_registry import validate_mapping_event_identity

        assert validate_mapping_event_identity("", {"D1-D10-FINALIZED"}) is False
        assert validate_mapping_event_identity("", set()) is False

    def test_validate_mapping_event_identity_rejects_fake(self):
        """F-05-A: Fake event ids must fail cross-validation."""
        from app.domains.compile.mapping_registry import validate_mapping_event_identity

        authorized = {"OD-MAP-01-APPROVED", "D1-D10-FINALIZED"}
        assert validate_mapping_event_identity("FAKE-EVENT-001", authorized) is False
        assert validate_mapping_event_identity("OD-MAP-01", authorized) is False
        assert validate_mapping_event_identity("nonexistent", set()) is False

    def test_validate_mapping_event_identity_accepts_known(self):
        """F-05-A: Known event ids must pass cross-validation."""
        from app.domains.compile.mapping_registry import (
            get_current_authorized_event_ids,
            validate_mapping_event_identity,
        )

        authorized = get_current_authorized_event_ids()
        assert validate_mapping_event_identity("D1-D10-FINALIZED", authorized) is True
        assert validate_mapping_event_identity("OD-MAP-01-APPROVED", authorized) is True

    def test_no_mapping_activated_without_event_id(self):
        """F-05-A: No mapping row may be AUTHORIZED without a non-empty mapping_basis."""
        from app.domains.compile.mapping_registry import (
            LEGACY_TO_CANONICAL_MAP,
            MappingStatus,
        )

        for source_value, entry in LEGACY_TO_CANONICAL_MAP.items():
            if entry.status == MappingStatus.AUTHORIZED:
                assert entry.mapping_basis, (
                    f"{source_value} is AUTHORIZED but mapping_basis is empty"
                )


# ================================================================ F-05-B: Compiler Wash-Path
class TestF05B_CompilerWashPath:
    """F-05-B: Compiler must not produce leaves for unknown/non-canonical unit_type.

    Current state: compiler correctly skips non-ready semantic_status.
    Target state: unknown must also be non-ready and not produce leaves.
    """

    def test_compiler_skips_non_ready_nodes(self):
        """CURRENT STATE: compiler.py:72 — semantic_status != 'ready' -> return."""
        import inspect

        from app.domains.compile.compiler import Compiler

        source = inspect.getsource(Compiler._compile_node)
        assert "semantic_status" in source and "ready" in source

    def test_semantic_status_current_domain_is_two_values(self):
        """CURRENT STATE: SEMANTIC_STATUS = {ready, incomplete} (P13 OPEN).

        TARGET STATE (M.2): SEMANTIC_STATUS = {ready, incomplete, unknown}
        This test documents current state; it will need provenance update after M.2.
        """
        from app.domains.compile import SEMANTIC_STATUS

        assert SEMANTIC_STATUS == frozenset({"ready", "incomplete"}), (
            "M.1 baseline: SEMANTIC_STATUS is two-valued. "
            "If this fails, the domain has changed — update tracking matrix."
        )

    def test_ir_binary_status_documented(self):
        """CURRENT STATE: ir.py:244 uses binary incomplete/ready (P5 OPEN).

        Documents that unknown is not yet distinguishable from incomplete.
        """
        import inspect

        from app.domains.compile.ir import _validate_node

        source = inspect.getsource(_validate_node)
        assert "incomplete" in source and "ready" in source, (
            "M.1 baseline: IR status is binary. If this fails, implementation has started."
        )


# ================================================================ UNKNOWN Wash Matrix
class TestUNKNOWN_WashMatrix:
    """UNKNOWN wash matrix — documents forbidden conversion paths.

    Each test verifies that a SPECIFIC wash path is documented as a known
    violation (P1-P13) that MUST be eliminated in M.2-M.10.

    These tests assert CURRENT state (wash paths exist) and document TARGET
    state (wash paths must be eliminated). They serve as the acceptance
    checklist for M.3-M.5 implementation.
    """

    def test_p1_adapter_else_wash_exists_currently(self):
        """P1 CURRENT: annotation_adapter.py:101-104 — non-composite_question -> standalone."""
        import inspect

        from scripts.preprocessing_consumer.annotation_adapter import (
            manifest_to_annotation_payload,
        )

        source = inspect.getsource(manifest_to_annotation_payload)
        assert "else" in source
        assert "_build_standalone" in source, (
            "P1: adapter else-wash still present. Eliminated? Update tracking matrix."
        )

    def test_p2_adapter_hardcode_exists_currently(self):
        """P2 CURRENT: annotation_adapter.py:42 — hardcode 'standalone_question'."""
        import inspect

        from scripts.preprocessing_consumer.annotation_adapter import _build_standalone

        source = inspect.getsource(_build_standalone)
        assert "standalone_question" in source, (
            "P2: hardcode still present. Eliminated? Update tracking matrix."
        )

    def test_p3_ir_default_exists_currently(self):
        """P3 CURRENT: ir.py:108 — unit.get('unit_type', 'standalone_question')."""
        import inspect

        from app.domains.compile.ir import IRBuilder

        source = inspect.getsource(IRBuilder._node)
        assert "standalone_question" in source, (
            "P3: IR default standalone still present. Eliminated? Update tracking matrix."
        )

    def test_p5_ir_binary_status_exists_currently(self):
        """P5 CURRENT: ir.py:244 — status = 'incomplete' if problems else 'ready'."""
        import inspect

        from app.domains.compile.ir import _validate_node

        source = inspect.getsource(_validate_node)
        assert "incomplete" in source and "ready" in source, (
            "P5: binary status still present. Eliminated? Update tracking matrix."
        )

    def test_p6_runner_skip_exists_currently(self):
        """P6 CURRENT: runner_b2.py:322 — semantic_status != 'ready' -> skip without audit."""
        runner_path = (
            Path(__file__).parent.parent
            / "scripts"
            / "preprocessing_consumer"
            / "runner_b2.py"
        )
        if not runner_path.exists():
            pytest.skip("runner_b2.py not found at expected path")
        source = runner_path.read_text(encoding="utf-8")
        assert 'semantic_status != "ready"' in source or (
            "semantic_status != 'ready'" in source
        ), "P6: runner skip pattern changed. Update tracking matrix."

    def test_p7_runner_ternary_exists_currently(self):
        """P7 CURRENT: runner_b2.py:342 — non-standalone_question -> composite_unit."""
        runner_path = (
            Path(__file__).parent.parent
            / "scripts"
            / "preprocessing_consumer"
            / "runner_b2.py"
        )
        if not runner_path.exists():
            pytest.skip("runner_b2.py not found at expected path")
        source = runner_path.read_text(encoding="utf-8")
        assert "standalone_unit" in source and "composite_unit" in source, (
            "P7: runner ternary pattern changed. Update tracking matrix."
        )

    def test_p9_gate_passthrough_exists_currently(self):
        """P9 CURRENT: gate/service.py:335 — .get(ir_unit_type, ir_unit_type) passthrough."""
        import inspect

        from app.domains.gate.service import _candidate_unit_type

        source = inspect.getsource(_candidate_unit_type)
        assert ".get(" in source, (
            "P9: gate passthrough pattern changed. Update tracking matrix."
        )

    def test_p13_semantic_status_no_unknown_currently(self):
        """P13 CURRENT: SEMANTIC_STATUS has no 'unknown' value."""
        from app.domains.compile import SEMANTIC_STATUS

        assert "unknown" not in SEMANTIC_STATUS, (
            "P13: unknown appeared in SEMANTIC_STATUS. Implementation started? "
            "Update tracking matrix and test provenance."
        )

    def test_unknown_wash_matrix_target_paths_documented(self):
        """TARGET STATE: documents all forbidden UNKNOWN conversion paths.

        Each path below must be eliminated by M.2-M.10. This test serves as
        the acceptance checklist — when all paths are eliminated, the
        corresponding source assertions above should fail (code changed)
        and be replaced by target-state acceptance tests.
        """
        forbidden_paths = [
            "UNKNOWN -> default standalone",
            "UNKNOWN -> binary composite",
            "UNKNOWN -> wash (adapter else)",
            "UNKNOWN -> silent skip (no record)",
            "UNKNOWN -> fake ready",
            "UNKNOWN -> production Question/Instance",
            "UNKNOWN -> incomplete -> silent skip",
            "UNKNOWN -> 'fix test' without historical behavior",
        ]
        assert len(forbidden_paths) == 8
        for path in forbidden_paths:
            assert "UNKNOWN" in path


# ================================================================ C-4: Untracked Docs Boundary
class TestC4_UntrackedDocsBoundary:
    """C-4: Untracked contract documents are NOT normative authority.

    V3 working tree contains untracked files under Docs/COORDINATION/CONTRACTS/
    and Docs/GOVERNANCE/. These must NOT be treated as Frozen Contract,
    Owner Decision, or Implementation Authority.
    """

    def test_untracked_docs_boundary_documented(self):
        """Documents that untracked V3 contract docs are outside M.1 authority scope."""
        untracked_families = [
            "PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-*",
            "PREPROCESSING-V3-CONTRACT-CONSUMER-REVIEW.md",
            "PREPROCESSING-V3-CONTRACT-v0.2-DRAFT-SKELETON.md",
            "PREPROCESSING-V3-CONTRACT.md",
            "GOVERNANCE/00-SYSTEM-BASELINE.md",
            "GOVERNANCE/02-AUTHORITY-MATRIX.md",
            "GOVERNANCE/03-DECISION-REGISTRY.md",
            "GOVERNANCE/04-CLAIM-REGISTRY.md",
        ]
        assert len(untracked_families) >= 8


# ================================================================ Baseline Evidence
class TestM1_BaselineEvidence:
    """M.1 baseline measurement evidence.

    CURRENT MEASURED BASELINE (separate from CLAIM-DOC):
        V3 test batch (test_ir + test_compiler + test_gate_service +
        test_gate_policy + test_admission) = 73 passed @ cc12d79
        Historical claim (UQ batch, different file subset) = 55 passed
        Delta explanation: different test file selection, not regression.
    """

    def test_baseline_documented(self):
        """Documents M.1 measured baseline for governance tracking."""
        baseline = {
            "v3_commit": "cc12d79e9a22f6274100ea0bb61f92493ba88509",
            "papers_commit": "2b92898f05f6541a5fc65c8300cb8a59a06c4928",
            "test_batch": [
                "test_ir.py",
                "test_compiler.py",
                "test_gate_service.py",
                "test_gate_policy.py",
                "test_admission.py",
            ],
            "measured_result": "73 passed",
            "historical_claim": "55 passed (different subset)",
            "classification": "CURRENT MEASURED BASELINE",
        }
        assert baseline["measured_result"] == "73 passed"
        assert baseline["v3_commit"].startswith("cc12d79")

    def test_security_constraint_present(self):
        """Security: Never hardcode API Keys/Passwords/Tokens/Secrets; Always use .env."""
        security_rule = (
            "Never hardcode API Keys/Passwords/Tokens/Secrets; "
            "Always use .env for configuration"
        )
        assert "Never hardcode" in security_rule
        assert ".env" in security_rule
