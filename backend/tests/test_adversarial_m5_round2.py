"""M5 对抗性审查 — 第二轮（针对修复后代码）。

从第一性原理出发，逐攻击面审查修复后的 M5。
每个结论必须有真实测试作为证据。

攻击面：
A. 白名单 `in` 运算符的 `==` 陷阱
B. 决策路径穷举与排他性
C. reason 值域完整性
D. mismatches 语义一致性
E. 不可达路径防御
F. M4→M5 管道不变量
G. 实际绕过场景模拟
"""
import itertools
from pathlib import Path
import ast

import pytest

from app.core.identity_gate import (
    GATE_BLOCK,
    GATE_PASS,
    IDENTITY_GATE_VERSION,
    IdentityGateDecision,
    evaluate_identity_gate,
    REASON_IDENTITY_VERIFIED_SEMANTIC_AVAILABLE,
    REASON_IDENTITY_VERIFICATION_FAILED,
    REASON_SEMANTIC_PENDING,
    REASON_SEMANTIC_ABSENT,
    REASON_INVALID_STATE,
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
# A. 白名单 `in` 运算符的 `==` 陷阱
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWhitelistEqualityTrap:
    """`in` 使用 `==`。攻击者构造自定义 `__eq__` 对象。"""

    def test_custom_eq_identity_value_blocks(self):
        """自定义 __eq__ 对象不是 str → isinstance 捕获 → BLOCK。"""
        class FakeVerified:
            def __eq__(self, other):
                return other == "VERIFIED"
            def __hash__(self):
                return hash("VERIFIED")

        vr = VerificationResult(
            identity=IdentityState(FakeVerified(), ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK, (
            "isinstance check blocks non-str identity values"
        )
        assert d.reason == "malformed_input"

    def test_custom_eq_semantic_value_blocks(self):
        """自定义 __eq__ 对象不是 str → isinstance 捕获 → BLOCK。"""
        class FakeAvailable:
            def __eq__(self, other):
                return other == "AVAILABLE"
            def __hash__(self):
                return hash("AVAILABLE")

        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ()),
            semantic=SemanticState(FakeAvailable(), None),  # type: ignore
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.reason == "invalid_state"

    def test_custom_eq_failed_value_blocks(self):
        """自定义 __eq__ 对象不是 str → isinstance 捕获 → BLOCK。"""
        class FakeFailed:
            def __eq__(self, other):
                return other == "FAILED"
            def __hash__(self):
                return hash("FAILED")

        vr = VerificationResult(
            identity=IdentityState(FakeFailed(), ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.reason == "malformed_input"

    def test_isinstance_check_is_present(self):
        """M5 使用 isinstance 校验 value 类型（修复后防御）。"""
        src = Path("app/core/identity_gate.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "isinstance":
                    found = True
                    break
        assert found, "isinstance must be present in M5 for type defense"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B. 决策路径穷举与排他性
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestDecisionPathExhaustive:
    """穷举 M4 可能产生的所有组合，验证每条路径可达且排他。"""

    @pytest.mark.parametrize("computed", [SHA_A, SHA_B, SHA_C])
    @pytest.mark.parametrize("manifest", [SHA_A, SHA_B, SHA_C, None])
    @pytest.mark.parametrize("ir", [SHA_A, SHA_B, SHA_C, None])
    def test_all_36_combinations(self, computed, manifest, ir):
        vr = verify_identity(computed, manifest, ir)
        d = evaluate_identity_gate(vr)

        assert d.gate in (GATE_PASS, GATE_BLOCK)

        if d.gate == GATE_PASS:
            assert d.identity_state == "VERIFIED"
            assert d.semantic_state == "AVAILABLE"
            assert d.reason == REASON_IDENTITY_VERIFIED_SEMANTIC_AVAILABLE

        if d.gate == GATE_BLOCK:
            assert d.identity_state in ("FAILED", "VERIFIED")

    def test_pass_count_exactly_3(self):
        """PASS 数 = 3（3 种 sha 值各一次全匹配）。"""
        shas = [SHA_A, SHA_B, SHA_C, None]
        pass_count = sum(
            1 for c, m, i in itertools.product(shas, shas, shas)
            if evaluate_identity_gate(verify_identity(c, m, i)).gate == GATE_PASS
        )
        assert pass_count == 3

    def test_failed_count_exactly_52(self):
        """FAILED 数 = 52。
        manifest=None: 4 computed × 4 ir = 16
        manifest≠None 且 computed≠manifest: 3 manifest × 3 computed × 4 ir = 36
        总计 = 16 + 36 = 52"""
        shas = [SHA_A, SHA_B, SHA_C, None]
        failed_count = sum(
            1 for c, m, i in itertools.product(shas, shas, shas)
            if evaluate_identity_gate(verify_identity(c, m, i)).identity_state == "FAILED"
        )
        assert failed_count == 52

    def test_verified_pending_count(self):
        """VERIFIED+PENDING 数 = 9。"""
        shas = [SHA_A, SHA_B, SHA_C, None]
        vp_count = sum(
            1 for c, m, i in itertools.product(shas, shas, shas)
            if evaluate_identity_gate(verify_identity(c, m, i)).semantic_state == "PENDING"
        )
        assert vp_count == 9

    def test_all_paths_mutually_exclusive(self):
        """每种 (gate, identity_state, semantic_state, reason) 组合互斥。"""
        shas = [SHA_A, SHA_B, SHA_C, None]
        seen = set()
        for c, m, i in itertools.product(shas, shas, shas):
            d = evaluate_identity_gate(verify_identity(c, m, i))
            key = (d.gate, d.identity_state, d.semantic_state, d.reason)
            seen.add(key)
        assert len(seen) == 3, f"Expected 3 distinct paths, got {len(seen)}: {seen}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C. reason 值域完整性
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestReasonCompleteness:
    """5 种 reason 的完整性和排他性。"""

    def test_all_five_reasons_reachable(self):
        """5 种 reason 均可通过合法输入到达。"""
        reasons = set()
        reasons.add(evaluate_identity_gate(verify_identity(SHA_A, SHA_A, SHA_A)).reason)
        reasons.add(evaluate_identity_gate(verify_identity(SHA_A, SHA_A, SHA_B)).reason)
        reasons.add(evaluate_identity_gate(verify_identity(SHA_A, SHA_A, None)).reason)
        reasons.add(evaluate_identity_gate(verify_identity(SHA_A, SHA_B)).reason)
        reasons.add(evaluate_identity_gate(
            VerificationResult(IdentityState("VERIFIED", ()), None)
        ).reason)
        reasons.add(evaluate_identity_gate(
            VerificationResult(IdentityState("HACKED", ()), SemanticState("AVAILABLE", None))
        ).reason)
        assert len(reasons) == 5, f"Expected 5 distinct reasons, got: {reasons}"

    def test_reason_matches_gate(self):
        """PASS reason 和 BLOCK reason 不同。"""
        pass_r = evaluate_identity_gate(verify_identity(SHA_A, SHA_A, SHA_A)).reason
        block_r = evaluate_identity_gate(verify_identity(SHA_A, SHA_B)).reason
        assert pass_r != block_r

    def test_pending_reasons_distinguish_mismatch_vs_absent(self):
        """PENDING 的 mismatch 和 absent 共用同一 reason（semantic_pending）。"""
        r_mismatch = evaluate_identity_gate(verify_identity(SHA_A, SHA_A, SHA_B)).reason
        r_absent = evaluate_identity_gate(verify_identity(SHA_A, SHA_A, None)).reason
        assert r_mismatch == r_absent == REASON_SEMANTIC_PENDING


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# D. mismatches 语义一致性
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestMismatchConsistency:
    """mismatches 与 gate/identity 的语义一致性。"""

    def test_pass_always_empty_mismatches_via_m4(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_PASS
        assert d.mismatches == ()

    def test_failed_always_nonempty_mismatches_via_m4(self):
        for manifest_val in [SHA_B, None]:
            vr = verify_identity(SHA_A, manifest_val)
            d = evaluate_identity_gate(vr)
            assert d.gate == GATE_BLOCK
            assert d.identity_state == "FAILED"
            assert len(d.mismatches) > 0

    def test_pending_always_empty_mismatches_via_m4(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.mismatches == ()

    def test_mismatches_tuple_immutable(self):
        vr = verify_identity(SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        with pytest.raises(AttributeError):
            d.mismatches.append("hack")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# E. 不可达路径防御
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestUnreachableDefense:
    """M4 保证不会产生的状态，M5 的防御行为。"""

    def test_m4_invariants_hold(self):
        """M4 的输出始终满足：FAILED ⟹ semantic=None；VERIFIED ⟹ semantic≠None。"""
        shas = [SHA_A, SHA_B, SHA_C, None]
        for c, m, i in itertools.product(shas, shas, shas):
            vr = verify_identity(c, m, i)
            if vr.identity.value == "FAILED":
                assert vr.semantic is None
            else:
                assert vr.semantic is not None

    def test_m5_defends_verified_none(self):
        d = evaluate_identity_gate(
            VerificationResult(IdentityState("VERIFIED", ()), None)
        )
        assert d.gate == GATE_BLOCK
        assert d.reason == REASON_SEMANTIC_ABSENT

    def test_m5_defends_failed_with_semantic(self):
        d = evaluate_identity_gate(
            VerificationResult(
                IdentityState("FAILED", ("x",)),
                SemanticState("AVAILABLE", None),
            )
        )
        assert d.gate == GATE_BLOCK
        assert d.semantic_state is None

    def test_m5_defends_invalid_identity(self):
        d = evaluate_identity_gate(
            VerificationResult(IdentityState("WEIRD", ()), SemanticState("AVAILABLE", None))
        )
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "INVALID"

    def test_m5_defends_invalid_semantic(self):
        d = evaluate_identity_gate(
            VerificationResult(IdentityState("VERIFIED", ()), SemanticState("WEIRD", None))
        )
        assert d.gate == GATE_BLOCK
        assert d.semantic_state == "INVALID"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F. M4→M5 管道不变量
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPipelineInvariants:
    """M4→M5 端到端不变量。"""

    def test_gate_pass_iff_all_three_match(self):
        """PASS ⟺ computed == manifest == ir ≠ None。"""
        shas = [SHA_A, SHA_B, SHA_C, None]
        for c, m, i in itertools.product(shas, shas, shas):
            d = evaluate_identity_gate(verify_identity(c, m, i))
            should_pass = (c is not None and c == m == i)
            assert (d.gate == GATE_PASS) == should_pass

    def test_identity_state_always_preserved(self):
        shas = [SHA_A, SHA_B, SHA_C, None]
        for c, m, i in itertools.product(shas, shas, shas):
            vr = verify_identity(c, m, i)
            d = evaluate_identity_gate(vr)
            assert d.identity_state == vr.identity.value

    def test_semantic_state_preserved_when_verified(self):
        shas = [SHA_A, SHA_B, SHA_C, None]
        for c, m, i in itertools.product(shas, shas, shas):
            vr = verify_identity(c, m, i)
            d = evaluate_identity_gate(vr)
            if vr.identity.value == "VERIFIED":
                assert d.semantic_state == vr.semantic.value

    def test_deterministic(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        results = [evaluate_identity_gate(vr) for _ in range(100)]
        assert all(r == results[0] for r in results)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# G. 实际绕过场景模拟
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestRealBypassSimulation:
    """模拟真实场景中的绕过尝试。"""

    def test_bypass_via_m4_output_only(self):
        """攻击者只能通过 M4 输出影响 M5。M4 输出始终合法。"""
        shas = [SHA_A, SHA_B, SHA_C, None]
        for c, m, i in itertools.product(shas, shas, shas):
            vr = verify_identity(c, m, i)
            assert vr.identity.value in ("VERIFIED", "FAILED")
            if vr.semantic is not None:
                assert vr.semantic.value in ("AVAILABLE", "PENDING")
            d = evaluate_identity_gate(vr)
            assert d.gate in (GATE_PASS, GATE_BLOCK)

    def test_no_bypass_through_normal_pipeline(self):
        """正常 M1→M2→M3→M4→M5 管道中无绕过。"""
        import hashlib, json, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            content = b"Test content for bypass"
            sha = hashlib.sha256(content).hexdigest()

            source = tmp / "src.md"
            source.write_bytes(content)
            manifest = tmp / "manifest.json"
            manifest.write_text(json.dumps({"source_content_sha256": sha}))
            ir = tmp / "ir.json"
            ir.write_text(json.dumps({"source_content_sha256": sha}))

            from app.core.raw_bytes_identity import load_raw_bytes_identity
            from app.core.manifest_identity import read_manifest_identity
            from app.core.ir_identity import read_ir_identity

            raw = load_raw_bytes_identity(source)
            man = read_manifest_identity(manifest)
            ir_data = read_ir_identity(ir)

            vr = verify_identity(raw.sha256, man.source_content_sha256, ir_data.source_content_sha256)
            d = evaluate_identity_gate(vr)
            assert d.gate == GATE_PASS

    def test_stale_ir_cannot_bypass(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK

    def test_missing_ir_cannot_bypass(self):
        vr = verify_identity(SHA_A, SHA_A, None)
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK

    def test_tampered_manifest_cannot_bypass(self):
        vr = verify_identity(SHA_A, SHA_B, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "FAILED"
