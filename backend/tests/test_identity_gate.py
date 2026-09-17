"""M5 Identity Gate — 单元测试。

覆盖：
- Truth Table（5 种组合）
- VERIFIED + PENDING = BLOCK（最高优先级不变量）
- 数据类型验证
- 纯函数性验证
"""
import pytest

from app.core.identity_gate import (
    GATE_BLOCK,
    GATE_PASS,
    IDENTITY_GATE_VERSION,
    IdentityGateDecision,
    evaluate_identity_gate,
)
from app.core.identity_verifier import (
    IdentityState,
    SemanticState,
    VerificationResult,
    verify_identity,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


class TestTruthTable:
    """M5 Truth Table — Owner Phase 2-M5 指令。"""

    def test_verified_available_pass(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_PASS
        assert decision.identity_state == "VERIFIED"
        assert decision.semantic_state == "AVAILABLE"
        assert decision.reason == "identity_verified_semantic_available"
        assert decision.mismatches == ()

    def test_verified_pending_block(self):
        """VERIFIED + PENDING = BLOCK — 最高优先级不变量。"""
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "VERIFIED"
        assert decision.semantic_state == "PENDING"
        assert decision.reason == "semantic_pending"

    def test_verified_pending_ir_absent_block(self):
        """VERIFIED + PENDING (ir_absent) = BLOCK。"""
        vr = verify_identity(SHA_A, SHA_A, None)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "VERIFIED"
        assert decision.semantic_state == "PENDING"

    def test_failed_none_block(self):
        vr = verify_identity(SHA_A, SHA_B)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "FAILED"
        assert decision.semantic_state is None
        assert decision.reason == "identity_verification_failed"

    def test_failed_manifest_missing_block(self):
        vr = verify_identity(SHA_A, None)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "FAILED"
        assert decision.semantic_state is None


class TestHighestPriorityInvariant:
    """VERIFIED + PENDING 必须 BLOCK — 专项测试。"""

    @pytest.mark.parametrize("ir_val", [SHA_B, None])
    def test_verified_pending_always_blocks(self, ir_val):
        vr = verify_identity(SHA_A, SHA_A, ir_val)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK, (
            f"VERIFIED+PENDING must BLOCK, got {decision.gate} with ir={ir_val!r}"
        )

    def test_only_pass_when_semantic_available(self):
        """唯一 PASS 条件：VERIFIED + AVAILABLE。"""
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_PASS
        assert decision.semantic_state == "AVAILABLE"


class TestDataTypes:
    """IdentityGateDecision 数据类型验证。"""

    def test_frozen_dataclass(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        decision = evaluate_identity_gate(vr)
        with pytest.raises(AttributeError):
            decision.gate = "HACKED"

    def test_mismatches_is_tuple(self):
        vr = verify_identity(SHA_A, SHA_B)
        decision = evaluate_identity_gate(vr)
        assert isinstance(decision.mismatches, tuple)

    def test_semantic_state_none_when_failed(self):
        vr = verify_identity(SHA_A, SHA_B)
        decision = evaluate_identity_gate(vr)
        assert decision.semantic_state is None

    def test_fields_present(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        decision = evaluate_identity_gate(vr)
        assert hasattr(decision, "gate")
        assert hasattr(decision, "identity_state")
        assert hasattr(decision, "semantic_state")
        assert hasattr(decision, "reason")
        assert hasattr(decision, "mismatches")

    def test_no_path_fields(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        decision = evaluate_identity_gate(vr)
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(decision)}
        assert "path" not in field_names
        assert "file" not in field_names
        assert "source" not in field_names


class TestPureFunction:
    """M5 是纯函数。"""

    def test_deterministic(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        results = [evaluate_identity_gate(vr) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_no_exception_for_all_m4_outputs(self):
        """M4 的所有合法输出都不会导致 M5 抛异常。"""
        import itertools
        shas = [SHA_A, SHA_B, None]
        for computed, manifest, ir in itertools.product([SHA_A, SHA_B], shas, shas):
            vr = verify_identity(computed, manifest, ir)
            decision = evaluate_identity_gate(vr)
            assert decision.gate in (GATE_PASS, GATE_BLOCK)

    def test_version_constant(self):
        assert IDENTITY_GATE_VERSION == "1.1.0"

    def test_gate_constants(self):
        assert GATE_PASS == "PASS"
        assert GATE_BLOCK == "BLOCK"
