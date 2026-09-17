"""M5 对抗性审查 — 第一轮。

从第一性原理出发，逐攻击面审查 M5 identity_gate.py。
每个结论必须有真实测试作为证据。

攻击面：
A. 纯函数审计（AST）
B. 类型混淆攻击（identity.value / semantic.value 非法值）
C. 手动构造 VerificationResult 边界
D. mismatches 传播正确性
E. reason 字段语义精确性
F. M5 不可达状态防御
G. 组合爆炸验证
H. M5 与 M4 集成正确性
"""
import ast
import dataclasses
import importlib
import itertools
import sys
from pathlib import Path

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
SHA_C = "c" * 64


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# A. 纯函数审计（AST）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPureFunctionAudit:
    """AST 级审计：M5 必须是纯函数。"""

    def _get_ast(self):
        src = Path("app/core/identity_gate.py").read_text(encoding="utf-8")
        return ast.parse(src)

    def test_no_hashlib_import(self):
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "hashlib" not in alias.name, f"hashlib import found: {alias.name}"

    def test_no_pathlib_import(self):
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "pathlib" not in alias.name
            if isinstance(node, ast.ImportFrom):
                assert node.module != "pathlib"

    def test_no_io_calls(self):
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    assert func.attr not in ("open", "read", "write", "read_text", "write_text", "read_bytes", "write_bytes"), \
                        f"IO call found: {func.attr}"

    def test_no_raise_statement(self):
        tree = self._get_ast()
        for node in ast.walk(tree):
            assert not isinstance(node, ast.Raise), "raise statement found in M5"

    def test_no_try_except(self):
        tree = self._get_ast()
        for node in ast.walk(tree):
            assert not isinstance(node, ast.Try), "try/except found in M5"

    def test_only_allowed_imports(self):
        tree = self._get_ast()
        allowed = {"dataclasses"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root in allowed, f"Unexpected import: {alias.name}"

    def test_no_mutable_globals(self):
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                            pytest.fail(f"Mutable global found: {target.id}")

    def test_function_signature(self):
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "evaluate_identity_gate":
                args = [a.arg for a in node.args.args]
                assert args == ["verification"], f"Unexpected args: {args}"
                return
        pytest.fail("evaluate_identity_gate not found")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B. 类型混淆攻击
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTypeConfusionAttack:
    """identity.value / semantic.value 使用 == 比较，Python == 有类型陷阱。
    修复后：M5 添加白名单校验，非法值 → BLOCK。"""

    def test_true_equals_one_not_failed(self):
        """True 不是 str → isinstance 捕获 → BLOCK (malformed_input)。"""
        vr = VerificationResult(
            identity=IdentityState(True, ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "INVALID"
        assert d.reason == "malformed_input"

    def test_one_as_identity_value_not_failed(self):
        """1 == True，但 1 不在 {VERIFIED, FAILED} 内 → BLOCK。"""
        vr = VerificationResult(
            identity=IdentityState(1, ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "INVALID"

    def test_hacked_identity_value_blocks(self):
        """"HACKED" 不在 {VERIFIED, FAILED} 内 → BLOCK。"""
        vr = VerificationResult(
            identity=IdentityState("HACKED", ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "INVALID"
        assert d.reason == "invalid_state"

    def test_hacked_semantic_value_blocks(self):
        """"HACKED" 不在 {AVAILABLE, PENDING} 内 → BLOCK。"""
        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ()),
            semantic=SemanticState("HACKED", None),  # type: ignore
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.semantic_state == "INVALID"
        assert d.reason == "invalid_state"

    def test_empty_string_identity_blocks(self):
        """空字符串不在 {VERIFIED, FAILED} 内 → BLOCK。"""
        vr = VerificationResult(
            identity=IdentityState("", ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "INVALID"

    def test_none_as_identity_value_blocks(self):
        """None 不在 {VERIFIED, FAILED} 内 → BLOCK。"""
        vr = VerificationResult(
            identity=IdentityState(None, ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "INVALID"

    def test_integer_semantic_value_blocks(self):
        """semantic.value = 0 不在 {AVAILABLE, PENDING} 内 → BLOCK。"""
        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ()),
            semantic=SemanticState(0, None),  # type: ignore
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.semantic_state == "INVALID"

    def test_verified_lowercase_blocks(self):
        """"verified"（小写）不在白名单内 → BLOCK。"""
        vr = VerificationResult(
            identity=IdentityState("verified", ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "INVALID"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C. 手动构造 VerificationResult 边界
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestManualConstructionBoundary:
    """绕过 M4，直接构造 VerificationResult 传入 M5。"""

    def test_verified_none_semantic_blocks(self):
        """VERIFIED + semantic=None → BLOCK（防御性路径）。"""
        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ()),
            semantic=None,
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "VERIFIED"
        assert d.semantic_state is None

    def test_verified_none_reason_is_precise(self):
        """VERIFIED + None 的 reason 是 'semantic_absent'，精确反映 semantic 为 None。"""
        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ()),
            semantic=None,
        )
        d = evaluate_identity_gate(vr)
        assert d.reason == "semantic_absent", (
            "M5 uses 'semantic_absent' reason when semantic is None — "
            "reason is semantically precise"
        )

    def test_failed_with_nonempty_mismatches(self):
        """FAILED + mismatches 传播。"""
        vr = VerificationResult(
            identity=IdentityState("FAILED", ("custom_reason",)),
            semantic=None,
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.mismatches == ("custom_reason",)

    def test_verified_available_with_mismatches(self):
        """VERIFIED + AVAILABLE + mismatches 非空 → PASS 但 mismatches 仍传播。"""
        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ("should_be_empty",)),
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_PASS
        assert d.mismatches == ("should_be_empty",), (
            "M5 propagates mismatches even on PASS — VERIFIED with non-empty mismatches still passes"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# D. mismatches 传播正确性
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestMismatchPropagation:
    """验证 mismatches 从 M4 正确传播到 M5。"""

    def test_failed_propagates_mismatches(self):
        vr = verify_identity(SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.mismatches == ("computed_manifest_mismatch",)

    def test_manifest_missing_propagates_mismatches(self):
        vr = verify_identity(SHA_A, None)
        d = evaluate_identity_gate(vr)
        assert d.mismatches == ("manifest_sha_missing",)

    def test_verified_available_empty_mismatches(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        d = evaluate_identity_gate(vr)
        assert d.mismatches == ()

    def test_verified_pending_empty_mismatches(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.mismatches == ()

    def test_mismatches_is_tuple_not_list(self):
        vr = verify_identity(SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert isinstance(d.mismatches, tuple)

    def test_mismatches_identity_reference(self):
        """M5 直接传递 identity.mismatches 引用，不复制。验证等值性。"""
        vr = verify_identity(SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.mismatches == vr.identity.mismatches


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# E. reason 字段语义精确性
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestReasonPrecision:
    """每个决策路径的 reason 必须精确反映实际状态。"""

    def test_pass_reason(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        d = evaluate_identity_gate(vr)
        assert d.reason == "identity_verified_semantic_available"

    def test_block_pending_mismatch_reason(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.reason == "semantic_pending"

    def test_block_pending_absent_reason(self):
        vr = verify_identity(SHA_A, SHA_A, None)
        d = evaluate_identity_gate(vr)
        assert d.reason == "semantic_pending"

    def test_block_failed_reason(self):
        vr = verify_identity(SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.reason == "identity_verification_failed"

    def test_reasons_are_distinct(self):
        """五种 reason 互不相同。"""
        reasons = set()
        test_cases = [
            verify_identity(SHA_A, SHA_A, SHA_A),      # pass
            verify_identity(SHA_A, SHA_A, SHA_B),       # pending
            verify_identity(SHA_A, SHA_B),              # failed
            VerificationResult(IdentityState("VERIFIED", ()), None),  # absent
            VerificationResult(IdentityState("HACKED", ()), SemanticState("AVAILABLE", None)),  # invalid
        ]
        for vr in test_cases:
            d = evaluate_identity_gate(vr)
            reasons.add(d.reason)
        assert len(reasons) == 5

    def test_reason_never_empty(self):
        """任何输入组合的 reason 都不为空。"""
        import itertools
        shas = [SHA_A, SHA_B, None]
        for computed, manifest, ir in itertools.product([SHA_A, SHA_B], shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            assert d.reason, f"Empty reason for computed={computed}, manifest={manifest}, ir={ir}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F. M5 不可达状态防御
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestUnreachableStateDefense:
    """M4 保证的状态之外，M5 的防御行为。"""

    def test_m4_never_produces_verified_none(self):
        """M4 的 VERIFIED 分支总是设置 semantic，不会是 None。"""
        for ir_val in [SHA_A, SHA_B, None]:
            vr = verify_identity(SHA_A, SHA_A, ir_val)
            assert vr.semantic is not None
            assert vr.identity.value == "VERIFIED"

    def test_m4_never_produces_failed_with_semantic(self):
        """M4 的 FAILED 分支总是 semantic=None。"""
        for manifest_val in [SHA_B, None]:
            vr = verify_identity(SHA_A, manifest_val)
            assert vr.semantic is None
            assert vr.identity.value == "FAILED"

    def test_m5_defends_against_verified_none(self):
        """手动构造 VERIFIED+None → BLOCK（防御路径可达）。"""
        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ()),
            semantic=None,
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK

    def test_m5_defends_against_failed_with_semantic(self):
        """手动构造 FAILED+PENDING → 仍然 BLOCK（FAILED 优先）。"""
        vr = VerificationResult(
            identity=IdentityState("FAILED", ("x",)),
            semantic=SemanticState("PENDING", "y"),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "FAILED"
        assert d.semantic_state is None

    def test_failed_takes_priority_over_semantic(self):
        """FAILED + AVAILABLE → BLOCK（FAILED 优先于 semantic）。"""
        vr = VerificationResult(
            identity=IdentityState("FAILED", ("x",)),
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.semantic_state is None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# G. 组合爆炸验证
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestCombinatorialExplosion:
    """穷举 M4 可能产生的所有组合，验证 M5 输出。"""

    @pytest.mark.parametrize("computed", [SHA_A, SHA_B])
    @pytest.mark.parametrize("manifest", [SHA_A, SHA_B, None])
    @pytest.mark.parametrize("ir", [SHA_A, SHA_B, SHA_C, None])
    def test_all_m4_outputs_m5_correct(self, computed, manifest, ir):
        vr = verify_identity(computed, manifest, ir)
        d = evaluate_identity_gate(vr)

        if vr.identity.value == "FAILED":
            assert d.gate == GATE_BLOCK
            assert d.identity_state == "FAILED"
            assert d.semantic_state is None
        elif vr.semantic.value == "PENDING":
            assert d.gate == GATE_BLOCK
            assert d.identity_state == "VERIFIED"
            assert d.semantic_state == "PENDING"
        elif vr.semantic.value == "AVAILABLE":
            assert d.gate == GATE_PASS
            assert d.identity_state == "VERIFIED"
            assert d.semantic_state == "AVAILABLE"
        else:
            pytest.fail(f"Unexpected semantic value: {vr.semantic.value}")

    def test_pass_exactly_when_all_three_match(self):
        """PASS 当且仅当 computed == manifest == ir（且三者均非 None）。"""
        import itertools
        shas = [SHA_A, SHA_B, SHA_C, None]
        pass_count = 0
        for computed, manifest, ir in itertools.product(shas, shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            if d.gate == GATE_PASS:
                pass_count += 1
                assert computed == manifest == ir
                assert computed is not None
        assert pass_count == 3

    def test_block_count(self):
        """BLOCK 的数量 = 总组合数 - PASS 数。"""
        import itertools
        shas = [SHA_A, SHA_B, SHA_C, None]
        total = 0
        block_count = 0
        for computed, manifest, ir in itertools.product(shas, shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            total += 1
            if d.gate == GATE_BLOCK:
                block_count += 1
        assert total == 64
        assert block_count == 64 - 3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# H. M5 与 M4 集成正确性
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestM4M5Integration:
    """M4→M5 管道的端到端验证。"""

    def test_identity_state_preserved(self):
        """M5 的 identity_state 必须与 M4 的 identity.value 一致。"""
        import itertools
        shas = [SHA_A, SHA_B, None]
        for computed, manifest, ir in itertools.product([SHA_A, SHA_B], shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            assert d.identity_state == vr.identity.value

    def test_semantic_state_preserved_when_verified(self):
        """M5 的 semantic_state 必须与 M4 的 semantic.value 一致（VERIFIED 时）。"""
        import itertools
        shas = [SHA_A, SHA_B, None]
        for computed, manifest, ir in itertools.product([SHA_A, SHA_B], shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            if vr.identity.value == "VERIFIED":
                assert d.semantic_state == vr.semantic.value

    def test_semantic_state_none_when_failed(self):
        """FAILED 时 M5 强制 semantic_state=None。"""
        import itertools
        shas = [SHA_A, SHA_B, None]
        for computed, manifest, ir in itertools.product([SHA_A, SHA_B], shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            if vr.identity.value == "FAILED":
                assert d.semantic_state is None

    def test_gate_pass_iff_verified_and_available(self):
        """gate=PASS 当且仅当 identity=VERIFIED 且 semantic=AVAILABLE。"""
        import itertools
        shas = [SHA_A, SHA_B, SHA_C, None]
        for computed, manifest, ir in itertools.product(shas, shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            should_pass = (
                vr.identity.value == "VERIFIED"
                and vr.semantic is not None
                and vr.semantic.value == "AVAILABLE"
            )
            assert (d.gate == GATE_PASS) == should_pass, (
                f"Gate mismatch: computed={computed}, manifest={manifest}, ir={ir}, "
                f"identity={vr.identity.value}, semantic={vr.semantic}, gate={d.gate}"
            )

    def test_deterministic_across_calls(self):
        """相同输入，多次调用结果完全一致。"""
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        results = [evaluate_identity_gate(vr) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_no_state_leak_between_calls(self):
        """连续调用不同输入，不互相影响。"""
        d1 = evaluate_identity_gate(verify_identity(SHA_A, SHA_A, SHA_A))
        d2 = evaluate_identity_gate(verify_identity(SHA_A, SHA_B))
        d3 = evaluate_identity_gate(verify_identity(SHA_A, SHA_A, None))

        assert d1.gate == GATE_PASS
        assert d2.gate == GATE_BLOCK
        assert d3.gate == GATE_BLOCK
        assert d1.gate == GATE_PASS
        assert d1.semantic_state == "AVAILABLE"
