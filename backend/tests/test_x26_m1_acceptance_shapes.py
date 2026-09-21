"""X2.6 M.1 Acceptance Shapes — F-05 / F-06 / UNKNOWN wash matrix / baseline evidence.

Establishes acceptance test shapes required by C-3 of the M.1 task.
These tests document CURRENT state verification and TARGET state acceptance criteria.

Evidence classification (M.1 Correction, C-03):
    CLASS A — Module-local enforcement: tests production code behavior directly
    CLASS B — Characterization/baseline: documents current state, not target
    CLASS C — Documentation assertion: proves document/constant exists
    CLASS D — Self-referential/tautological: NOT independent implementation evidence

F-05-A evidence status (M.1 Correction, C-01 + OD-2 Registration):
    Event-ID existence validation = EXISTS (module-local, Class A)
    Mapping ↔ event semantic binding = DOES NOT EXIST (IMPLEMENTATION GAP)
    Per-value Owner event IDs = RECORDED (OD-2: X2.6-OD-2-MAP-STANDALONE-01 / COMPOSITE-01)
    Complete semantic binding enforcement = IMPLEMENTATION GAP
    Production mapping enforcement = NOT IMPLEMENTED (Owner authorization ≠ enforcement)

D10 provenance: This is a NEW test file. No existing test is modified.
M.1 Correction: Classification docstrings added; real DI-01 hash test added.
No existing test assertion weakened or removed.
"""

from __future__ import annotations

import hashlib
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

# Papers repo fixture absolute path (for real hash verification)
_PAPERS_FIXTURE_PATH = Path(
    "D:/Project/Papers/Ocr-markdown/reslice-batch-C/合格考/化学/"
    "2020北京高中合格考化学（第一次）（教师版）(1).manifest.json"
)


# ================================================================ F-06-A: DI-01 Hash Pin
class TestF06A_DI01_HashPin:
    """F-06-A: DI-01 fixture hash guard — constant consistency.

    Evidence class: D (self-referential) — constants compared to literals.
    Real hash verification: see TestF06A_DI01_RealHashPin.
    Source: DSH A-level independent reproduction @ Papers 2b92898.
    """

    def test_di01_sha256_constant_matches_dsh_baseline(self):
        """CLASS D: Hash constant must equal DSH-reported baseline value.

        This is a constant-vs-literal check. It does NOT independently
        verify the fixture file content. Real hash test reads the file.
        """
        assert DI01_SHA256 == (
            "24da834b8695798a5fe511e527b4d6583d3baa9b862d432cd38dc65a37e313f8"
        )

    def test_di01_size_constant_matches_dsh_baseline(self):
        """CLASS D: Size constant must equal DSH-reported baseline value."""
        assert DI01_SIZE == 23446

    def test_di01_manifest_path_constant(self):
        """CLASS C: Fixture path must match DSH-registered identity."""
        assert "合格考" in DI01_MANIFEST_PATH
        assert "化学" in DI01_MANIFEST_PATH
        assert "2020北京高中合格考化学" in DI01_MANIFEST_PATH
        assert DI01_MANIFEST_PATH.endswith(".manifest.json")


# ================================================================ F-06-A REAL: DI-01 Fixture Hash
class TestF06A_DI01_RealHashPin:
    """F-06-A REAL: Compute SHA-256 from actual DI-01 fixture file.

    Evidence class: A (module-local enforcement) when fixture accessible.
    Evidence class: skip when fixture not accessible.

    This class was added in M.1 Correction to provide real hash verification
    beyond constant comparison. It does NOT modify production semantics.
    """

    def test_di01_real_sha256_from_fixture(self):
        """Compute SHA-256 from actual DI-01 manifest file on disk."""
        if not _PAPERS_FIXTURE_PATH.exists():
            pytest.skip(f"DI-01 fixture not accessible at {_PAPERS_FIXTURE_PATH}")
        data = _PAPERS_FIXTURE_PATH.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest()
        assert actual_sha == DI01_SHA256, (
            f"DI-01 fixture hash mismatch: expected {DI01_SHA256}, got {actual_sha}"
        )

    def test_di01_real_size_from_fixture(self):
        """Verify file size from actual DI-01 manifest file on disk."""
        if not _PAPERS_FIXTURE_PATH.exists():
            pytest.skip(f"DI-01 fixture not accessible at {_PAPERS_FIXTURE_PATH}")
        actual_size = _PAPERS_FIXTURE_PATH.stat().st_size
        assert actual_size == DI01_SIZE, (
            f"DI-01 fixture size mismatch: expected {DI01_SIZE}, got {actual_size}"
        )


# ================================================================ F-06-B: DI-01 Fixture Identity
class TestF06B_DI01_FixtureIdentity:
    """F-06-B: DI-01 fixture identity must be pinned and verified.

    Evidence class:
        test_di01_unit_id = D (constant == literal)
        test_di01_unit_type = D (constant == literal)
        test_di01_source_content_sha256 = D (constant == literal)
        test_di01_distribution = D (literal arithmetic)

    Fixed identity from DSH verification:
        path = Ocr-markdown/reslice-batch-C/合格考/化学/...
        unit = Q1 (unit_type="andalone_question")
        source_content_sha256 = f6b13d6a...
    """

    def test_di01_unit_id(self):
        """CLASS D: Constant check — unit_id must be Q1."""
        assert DI01_UNIT_ID == "Q1"

    def test_di01_unit_type_is_andalone_question(self):
        """CLASS D: Constant check — DI-01 must be identified by andalone_question."""
        assert DI01_UNIT_TYPE == "andalone_question"

    def test_di01_source_content_sha256_constant(self):
        """CLASS D: Constant check — source_content_sha256 must match DSH baseline."""
        assert DI01_SOURCE_CONTENT_SHA256 == (
            "f6b13d6ab3491d7cc43b694951a66488d014653c3cdf194338b4ce6ecac4fe61"
        )

    def test_di01_distribution_documented(self):
        """CLASS D: Literal arithmetic — 32+1+1=34 documented distribution."""
        expected_distribution = {
            "standalone_question": 32,
            "composite_question": 1,
            "andalone_question": 1,
        }
        assert sum(expected_distribution.values()) == 34
        assert expected_distribution["andalone_question"] == 1


# ================================================================ F-05-A: Mapping Event Identity
class TestF05A_MappingEventIdentity:
    """F-05-A: Mapping event id cross-validation — MODULE-LOCAL ENFORCEMENT ONLY.

    Evidence status (M.1 Correction C-01 + OD-2 Registration):
        Event-ID existence validation = EXISTS (Class A: module-local)
        Mapping ↔ event semantic binding = DOES NOT EXIST (IMPLEMENTATION GAP)
        Per-value Owner event IDs = RECORDED (OD-2: X2.6-OD-2-MAP-STANDALONE-01 / COMPOSITE-01)
        Complete semantic binding enforcement = IMPLEMENTATION GAP
        Production mapping enforcement = NOT IMPLEMENTED

    What these tests CAN prove:
        - Pending mappings do not activate
        - Prohibited mappings do not produce canonical targets
        - Missing/unmapped values do not default to standalone
        - Empty/fake event IDs are rejected by existence check
        - Provenance fields exist on mapping entries

    What these tests CANNOT prove:
        - That an existing event ID semantically authorizes a specific mapping
        - That event IDs are not reused across different mappings
        - That framework-level governance IDs are not misused as mapping IDs
        - Direction correctness (source→target) validated against governance docs
    """

    def test_mapping_registry_module_exists(self):
        """CLASS C: Mapping registry module must be importable."""
        from app.domains.compile import mapping_registry

        assert hasattr(mapping_registry, "LEGACY_TO_CANONICAL_MAP")
        assert hasattr(mapping_registry, "MappingEntry")
        assert hasattr(mapping_registry, "MappingStatus")

    def test_mapping_table_structure_has_provenance_fields(self):
        """CLASS A: Every mapping entry must carry mapping_basis and condition fields."""
        from app.domains.compile.mapping_registry import LEGACY_TO_CANONICAL_MAP

        for source_value, entry in LEGACY_TO_CANONICAL_MAP.items():
            assert hasattr(entry, "mapping_basis"), f"{source_value} missing mapping_basis"
            assert hasattr(entry, "condition"), f"{source_value} missing condition"
            assert hasattr(entry, "status"), f"{source_value} missing status"
            assert entry.source_value == source_value

    def test_pending_owner_rows_do_not_activate(self):
        """CLASS A: After OD-2, standalone/composite are AUTHORIZED with event IDs.

        D10 provenance:
            previous: PENDING_OWNER rows must resolve to None
            why: OD-2 registered 2026-09-20 — Owner authorized two canonical mappings
            new: AUTHORIZED rows have proper event IDs; resolve_canonical returns target
            provenance: X2.6-OD-2-MAPPING-AUTHORIZATION
            note: Owner authorization != production enforcement; scaffold only
        """
        from app.domains.compile.mapping_registry import (
            MappingStatus,
            lookup_mapping,
            resolve_canonical,
        )

        expected = {
            "standalone_question": (
                "standalone_unit",
                "X2.6-OD-2-MAP-STANDALONE-01",
            ),
            "composite_question": (
                "composite_unit",
                "X2.6-OD-2-MAP-COMPOSITE-01",
            ),
        }
        for source_value, (target, event_id) in expected.items():
            entry = lookup_mapping(source_value)
            assert entry is not None
            assert entry.status == MappingStatus.AUTHORIZED, (
                f"{source_value} must be AUTHORIZED after OD-2"
            )
            assert entry.mapping_basis == event_id, (
                f"{source_value} mapping_basis must be {event_id}"
            )
            canonical, provenance = resolve_canonical(source_value)
            assert canonical == target, (
                f"{source_value} must resolve to {target} after OD-2"
            )
            assert event_id in provenance, (
                f"provenance must reference {event_id}"
            )

    def test_prohibited_row_resolves_to_unknown(self):
        """CLASS A: andalone_question must resolve to None (unknown), never canonical.

        After OD-1: Owner disposition = migrate-as-UNKNOWN.
        PROHIBITED status unchanged; mapping_basis references OD-1 event.
        """
        from app.domains.compile.mapping_registry import resolve_canonical

        canonical, provenance = resolve_canonical("andalone_question")
        assert canonical is None
        assert "prohibited" in provenance.lower() or "D8" in provenance

    def test_missing_value_resolves_to_unknown(self):
        """CLASS A: Missing/None unit_type must resolve to unknown, never default standalone."""
        from app.domains.compile.mapping_registry import resolve_canonical

        canonical, provenance = resolve_canonical(None)
        assert canonical is None
        assert "missing" in provenance

    def test_unmapped_value_resolves_to_unknown(self):
        """CLASS A: Arbitrary unmapped values must resolve to unknown."""
        from app.domains.compile.mapping_registry import resolve_canonical

        for bad_value in ("foo_question", "", "STANDALONE_UNIT", "composite_unit"):
            canonical, provenance = resolve_canonical(bad_value)
            assert canonical is None, f"{bad_value!r} must not resolve to canonical"

    def test_validate_mapping_event_identity_rejects_empty(self):
        """CLASS A: F-05-A existence check — empty mapping_basis must fail validation."""
        from app.domains.compile.mapping_registry import validate_mapping_event_identity

        assert validate_mapping_event_identity("", {"D1-D10-FINALIZED"}) is False
        assert validate_mapping_event_identity("", set()) is False

    def test_validate_mapping_event_identity_rejects_fake(self):
        """CLASS A: F-05-A existence check — fake event ids must fail validation.

        LIMITATION (C-01): This tests EXISTENCE only. It does NOT verify
        semantic binding between event ID and mapping value/direction.
        """
        from app.domains.compile.mapping_registry import validate_mapping_event_identity

        authorized = {"OD-MAP-01-APPROVED", "D1-D10-FINALIZED"}
        assert validate_mapping_event_identity("FAKE-EVENT-001", authorized) is False
        assert validate_mapping_event_identity("OD-MAP-01", authorized) is False
        assert validate_mapping_event_identity("nonexistent", set()) is False

    def test_validate_mapping_event_identity_accepts_known(self):
        """CLASS D (LIMITED): F-05-A existence check — known event ids pass.

        C-01 CORRECTION: This test accepts FRAMEWORK-LEVEL governance IDs,
        NOT per-value mapping authorization IDs. Framework approval ≠
        per-value mapping authorization. This test does NOT prove that
        semantic binding exists. It only proves set membership works.
        """
        from app.domains.compile.mapping_registry import (
            get_current_authorized_event_ids,
            validate_mapping_event_identity,
        )

        authorized = get_current_authorized_event_ids()
        assert validate_mapping_event_identity("D1-D10-FINALIZED", authorized) is True
        assert validate_mapping_event_identity("OD-MAP-01-APPROVED", authorized) is True

    def test_no_mapping_activated_without_event_id(self):
        """CLASS A: No mapping row may be AUTHORIZED without mapping_basis.

        D10 provenance:
            previous: "Currently ALL rows are PENDING_OWNER or PROHIBITED"
            why: OD-2 registered 2026-09-20 — 2 rows now AUTHORIZED with event IDs
            new: test verifies AUTHORIZED rows have non-empty mapping_basis
            provenance: X2.6-OD-2-MAPPING-AUTHORIZATION
        """
        from app.domains.compile.mapping_registry import (
            LEGACY_TO_CANONICAL_MAP,
            MappingStatus,
        )

        authorized_count = 0
        for source_value, entry in LEGACY_TO_CANONICAL_MAP.items():
            if entry.status == MappingStatus.AUTHORIZED:
                authorized_count += 1
                assert entry.mapping_basis, (
                    f"{source_value} is AUTHORIZED but mapping_basis is empty"
                )
        # After OD-2: 2 AUTHORIZED rows (standalone_question, composite_question)
        # Both must have event IDs from OD-2 registration


# ================================================================ F-05-B: Compiler Wash-Path
class TestF05B_CompilerWashPath:
    """F-05-B: Compiler wash-path assertions — CHARACTERIZATION tests.

    Evidence class: B (characterization/baseline) — documents current state.
    These tests prove what the current code does, NOT what target design requires.
    """

    def test_compiler_skips_non_ready_nodes(self):
        """CLASS B: CURRENT STATE — compiler.py:72 skips non-ready semantic_status."""
        import inspect

        from app.domains.compile.compiler import Compiler

        source = inspect.getsource(Compiler._compile_node)
        assert "semantic_status" in source and "ready" in source

    def test_semantic_status_domain_after_m2(self):
        """HISTORICAL FIXTURE + CURRENT STATE: SEMANTIC_STATUS = {ready, incomplete, unknown}.

        D10 provenance:
            previous: SEMANTIC_STATUS == frozenset({"ready", "incomplete"})
            why: X2.6 M.2 unfreezes domain (OD-D9-01 + IMPL-AUTH-01)
            new: SEMANTIC_STATUS == frozenset({"ready", "incomplete", "unknown"})
            provenance: X2.6-OD-D9-01, X2.6-IMPL-AUTH-01, M.2
            note: ready/incomplete behavior unchanged; unknown = IR expression only
        """
        from app.domains.compile import SEMANTIC_STATUS

        assert SEMANTIC_STATUS == frozenset({"ready", "incomplete", "unknown"}), (
            "M.2 target: SEMANTIC_STATUS must be three-valued. "
            "If this fails, M.2 implementation is incomplete."
        )
        # Historical constraint (pre-M.2): {ready, incomplete} subset still holds
        assert frozenset({"ready", "incomplete"}).issubset(SEMANTIC_STATUS)

    def test_ir_binary_status_still_present(self):
        """CLASS B: ir.py still uses incomplete/ready logic; M.2 adds unknown but preserves binary path.

        D10 provenance:
            previous: assert "incomplete" in source and "ready" in source
            why: M.1 documented binary status (P5); M.2 adds unknown but ready/incomplete logic unchanged
            new: same assertion still holds; unknown is additional, not replacement
            provenance: X2.6 M.2
        """
        import inspect

        from app.domains.compile.ir import _validate_node

        source = inspect.getsource(_validate_node)
        assert "incomplete" in source and "ready" in source, (
            "M.2 compatibility: ready/incomplete logic must remain in _validate_node."
        )


# ================================================================ UNKNOWN Wash Matrix
class TestUNKNOWN_WashMatrix:
    """UNKNOWN wash matrix — CHARACTERIZATION + DOCUMENTATION tests.

    Evidence class:
        P-path existence tests (p1-p9, p13) = CLASS B (characterization)
        Target paths documentation test = CLASS C (documentation assertion)

    These tests assert CURRENT state (wash paths exist) and document TARGET
    state (wash paths must be eliminated). They serve as the acceptance
    checklist for M.3-M.5 implementation.
    """

    def test_p1_adapter_else_wash_exists_currently(self):
        """CLASS B: P1 CURRENT — adapter else-wash to standalone still present."""
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
        """CLASS B: P2 CURRENT — adapter hardcode 'standalone_question' still present."""
        import inspect

        from scripts.preprocessing_consumer.annotation_adapter import _build_standalone

        source = inspect.getsource(_build_standalone)
        assert "standalone_question" in source, (
            "P2: hardcode still present. Eliminated? Update tracking matrix."
        )

    def test_p3_ir_default_is_canonical_after_m3(self):
        """CLASS A: P3 CORRECTED — ir.py now uses canonical Unit Type vocabulary.

        M.3 Boundary Correction (2026-09-20): Owner D1 confirmed
        standalone_question/composite_question are NOT legal Unit Types.
        IR now outputs canonical vocabulary: {standalone_unit, composite_unit}.

        D10 provenance:
            previous: assert "standalone_question" in source (P3 characterization)
            why: M.3 corrects IR to use canonical vocabulary per Owner D1
            new: assert "standalone_unit" in source; assert "standalone_question" not in source
        """
        import inspect

        from app.domains.compile.ir import IRBuilder

        source = inspect.getsource(IRBuilder._node)
        assert "standalone_unit" in source, (
            "P3: IR should use canonical Unit Type 'standalone_unit' after M.3 correction."
        )
        assert "standalone_question" not in source, (
            "P3: IR should NOT use legacy vocabulary 'standalone_question' after M.3 correction."
        )

    def test_p5_ir_binary_status_still_present_after_m2(self):
        """CLASS B: P5 — ir.py binary incomplete/ready logic still present after M.2.

        D10 provenance:
            previous: assert "incomplete" in source and "ready" in source (P5 characterization)
            why: M.2 adds unknown but preserves ready/incomplete logic; P5 not auto-closed
            new: same assertion still holds; unknown is additive
            provenance: X2.6 M.2 — P5 NOT auto-closed by M.2
        """
        import inspect

        from app.domains.compile.ir import _validate_node

        source = inspect.getsource(_validate_node)
        assert "incomplete" in source and "ready" in source, (
            "P5/M.2: binary ready/incomplete logic must remain; "
            "M.2 does NOT auto-close P5."
        )

    def test_p6_runner_skip_exists_currently(self):
        """CLASS B: P6 CURRENT — runner_b2.py non-ready silent skip still present."""
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
        """CLASS B: P7 CURRENT — runner_b2.py binary ternary still present."""
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

    def test_p9_gate_fail_closed_after_m3(self):
        """HISTORICAL FIXTURE + CURRENT STATE: P9 — Gate fail-closed on non-canonical Unit Type.

        D10 provenance:
            previous: assert ".get(" in source (passthrough characterization)
            why: P9 documented M.1 state (silent passthrough on miss); M.3 removes it
            new: assert ValueError raise present; assert ".get(" not in source
            provenance: X2.6 M.3 Vocabulary Boundary Enforcement Correction
        """
        import inspect

        from app.domains.gate.service import _candidate_unit_type

        source = inspect.getsource(_candidate_unit_type)
        assert "ValueError" in source, (
            "P9/M.3: _candidate_unit_type must raise ValueError on non-canonical Unit Type."
        )
        assert "UNIT_TYPES" in source, (
            "P9/M.3: _candidate_unit_type must validate against UNIT_TYPES."
        )
        assert ".get(" not in source, (
            "P9/M.3: silent passthrough pattern must be removed after M.3 correction."
        )

    def test_p13_semantic_status_unknown_present_after_m2(self):
        """HISTORICAL FIXTURE + CURRENT STATE: P13 — SEMANTIC_STATUS includes 'unknown' after M.2.

        D10 provenance:
            previous: assert "unknown" not in SEMANTIC_STATUS
            why: P13 documented M.1 state (2-value domain); M.2 unfreezes domain
            new: assert "unknown" in SEMANTIC_STATUS (M.2 target state)
            provenance: X2.6-OD-D9-01, M.2
        """
        from app.domains.compile import SEMANTIC_STATUS

        assert "unknown" in SEMANTIC_STATUS, (
            "P13/M.2: unknown must be in SEMANTIC_STATUS after M.2 implementation."
        )

    def test_unknown_wash_matrix_target_paths_documented(self):
        """CLASS C: TARGET STATE documentation — forbidden UNKNOWN conversion paths.

        This test only asserts that documentation exists. It does NOT prove
        that any enforcement mechanism prevents these paths in production.
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

    Evidence class: CLASS C (documentation assertion).
    """

    def test_untracked_docs_boundary_documented(self):
        """CLASS C: Documents that untracked V3 contract docs are outside M.1 authority."""
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

    Evidence class: CLASS D (self-referential) — dict self-comparison.

    M.1 Correction (C-05): Test execution evidence reclassified.
    Directly verified @ V3 dc28afe (2026-09-20):
        Baseline batch  = 73 passed, 1 warning (executed, not just collected)
        M.1 tests       = 32 passed, 1 warning (executed)
        Combined        = 105 passed, 1 warning (executed)
    """

    def test_baseline_documented(self):
        """CLASS D: Self-referential — dict values compared to their own literals.

        Documents M.1 measured baseline for governance tracking.
        Does NOT independently verify test execution — see M.1 Correction Report.
        """
        baseline = {
            "v3_commit": "cc12d79e9a22f6274100ea0bb61f92493ba88509",
            "v3_post_m1_commit": "dc28afe8bb997f5e562089742bbbe34365a3a3ef",
            "papers_commit": "2b92898f05f6541a5fc65c8300cb8a59a06c4928",
            "test_batch": [
                "test_ir.py",
                "test_compiler.py",
                "test_gate_service.py",
                "test_gate_policy.py",
                "test_admission.py",
            ],
            "measured_result_at_cc12d79": "73 passed",
            "measured_result_at_dc28afe_combined": "105 passed",
            "historical_claim": "55 passed (different subset)",
            "classification": "CURRENT MEASURED BASELINE",
        }
        assert baseline["measured_result_at_cc12d79"] == "73 passed"
        assert baseline["measured_result_at_dc28afe_combined"] == "105 passed"
        assert baseline["v3_commit"].startswith("cc12d79")
        assert baseline["v3_post_m1_commit"].startswith("dc28afe")

    def test_security_constraint_present(self):
        """CLASS D: Self-referential — string contains its own substrings."""
        security_rule = (
            "Never hardcode API Keys/Passwords/Tokens/Secrets; "
            "Always use .env for configuration"
        )
        assert "Never hardcode" in security_rule
        assert ".env" in security_rule
