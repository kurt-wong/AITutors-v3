"""M5 对抗性审查 — str subclass / __eq__ 边界 hardening (Phase 2.5 P1)。

攻击面：
A. str subclass 自定义 __eq__ 绕过白名单
B. str subclass 自定义 __hash__ 配合
C. 非 str 类型伪装
D. normalize 后输出字段纯度
E. AST 静态审计：确认 _normalize_str 存在且被调用
"""

import ast
from pathlib import Path

import pytest

from app.core.identity_gate import (
    GATE_BLOCK,
    GATE_PASS,
    IdentityGateDecision,
    evaluate_identity_gate,
)
from app.core.identity_verifier import (
    IdentityState,
    SemanticState,
    VerificationResult,
)

SHA_A = "a" * 64


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# A. str subclass 自定义 __eq__ 绕过白名单
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestStrSubclassEqualityBypass:
    """str subclass 通过 isinstance 检查后，用自定义 __eq__ 绕过白名单。"""

    def test_str_subclass_fake_verified_blocks(self):
        """str subclass 内容为 'HACKED' 但 __eq__ 声称等于 'VERIFIED' → BLOCK。"""

        class EvilVerified(str):
            def __eq__(self, other):
                return other == "VERIFIED"

            def __hash__(self):
                return hash("VERIFIED")

        vr = VerificationResult(
            identity=IdentityState(EvilVerified("HACKED"), ()),
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        # normalize 后值为 "HACKED"，不在白名单 → BLOCK (invalid_state)
        assert d.gate == GATE_BLOCK
        assert d.reason == "invalid_state"

    def test_str_subclass_fake_failed_blocks(self):
        """str subclass 内容为 'HACKED' 但 __eq__ 声称等于 'FAILED' → BLOCK。"""

        class EvilFailed(str):
            def __eq__(self, other):
                return other == "FAILED"

            def __hash__(self):
                return hash("FAILED")

        vr = VerificationResult(
            identity=IdentityState(EvilFailed("HACKED"), ()),
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.reason == "invalid_state"

    def test_str_subclass_fake_available_blocks(self):
        """str subclass semantic 值为 'HACKED' 但 __eq__ 声称等于 'AVAILABLE' → BLOCK。"""

        class EvilAvailable(str):
            def __eq__(self, other):
                return other == "AVAILABLE"

            def __hash__(self):
                return hash("AVAILABLE")

        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ()),
            semantic=SemanticState(EvilAvailable("HACKED"), None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.reason == "invalid_state"

    def test_str_subclass_fake_pending_blocks(self):
        """str subclass semantic 值为 'HACKED' 但 __eq__ 声称等于 'PENDING' → BLOCK。"""

        class EvilPending(str):
            def __eq__(self, other):
                return other == "PENDING"

            def __hash__(self):
                return hash("PENDING")

        vr = VerificationResult(
            identity=IdentityState("VERIFIED", ()),
            semantic=SemanticState(EvilPending("HACKED"), None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.reason == "invalid_state"

    def test_str_subclass_empty_string_blocks(self):
        """str subclass 空字符串 → normalize 后为空 → 不在白名单 → BLOCK。"""

        class EvilEmpty(str):
            def __eq__(self, other):
                return True  # 声称等于任何值

            def __hash__(self):
                return 0

        vr = VerificationResult(
            identity=IdentityState(EvilEmpty(""), ()),
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B. str subclass 合法值仍正常工作
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestStrSubclassLegitimate:
    """str subclass 携带合法值时，normalize 后仍能正确判定。"""

    def test_str_subclass_verified_available_passes(self):
        """str subclass 值为 'VERIFIED'/'AVAILABLE' → normalize 后 → PASS。"""

        class MyStr(str):
            pass

        vr = VerificationResult(
            identity=IdentityState(MyStr("VERIFIED"), ()),
            semantic=SemanticState(MyStr("AVAILABLE"), None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_PASS
        assert d.identity_state == "VERIFIED"
        assert d.semantic_state == "AVAILABLE"

    def test_str_subclass_verified_pending_blocks(self):
        """str subclass 值为 'VERIFIED'/'PENDING' → normalize 后 → BLOCK。"""

        class MyStr(str):
            pass

        vr = VerificationResult(
            identity=IdentityState(MyStr("VERIFIED"), ()),
            semantic=SemanticState(MyStr("PENDING"), None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.reason == "semantic_pending"

    def test_str_subclass_failed_blocks(self):
        """str subclass 值为 'FAILED' → normalize 后 → BLOCK。"""

        class MyStr(str):
            pass

        vr = VerificationResult(
            identity=IdentityState(MyStr("FAILED"), ("mismatch",)),
            semantic=None,
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "FAILED"

    def test_output_fields_are_plain_str(self):
        """normalize 后输出字段必须是 plain str，不是 str subclass。"""

        class MyStr(str):
            pass

        vr = VerificationResult(
            identity=IdentityState(MyStr("VERIFIED"), ()),
            semantic=SemanticState(MyStr("AVAILABLE"), None),
        )
        d = evaluate_identity_gate(vr)
        assert type(d.gate) is str
        assert type(d.identity_state) is str
        assert type(d.semantic_state) is str
        assert type(d.reason) is str


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C. 非 str 类型伪装（已有防御的回归确认）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestNonStrPretend:
    """非 str 类型通过自定义 __eq__ 伪装 → isinstance 捕获 → BLOCK。"""

    def test_int_pretending_verified_blocks(self):
        class FakeInt(int):
            def __eq__(self, other):
                return other == "VERIFIED"

        vr = VerificationResult(
            identity=IdentityState(FakeInt(1), ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK

    def test_bytes_pretending_verified_blocks(self):
        class FakeBytes(bytes):
            def __eq__(self, other):
                return other == "VERIFIED"

        vr = VerificationResult(
            identity=IdentityState(FakeBytes(b"x"), ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK

    def test_none_pretending_verified_blocks(self):
        vr = VerificationResult(
            identity=IdentityState(None, ()),  # type: ignore
            semantic=SemanticState("AVAILABLE", None),
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# D. AST 静态审计
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestASTAudit:
    """AST 审计：确认 _normalize_str 函数存在且被 evaluate_identity_gate 调用。"""

    def _get_source(self) -> str:
        return Path("app/core/identity_gate.py").read_text(encoding="utf-8")

    def test_normalize_str_function_exists(self):
        src = self._get_source()
        tree = ast.parse(src)
        funcs = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert "_normalize_str" in funcs, "_normalize_str must exist in M5"

    def test_normalize_str_called_in_evaluate(self):
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "evaluate_identity_gate":
                calls = [
                    n for n in ast.walk(node)
                    if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name)
                    and n.func.id == "_normalize_str"
                ]
                assert len(calls) >= 2, (
                    "_normalize_str must be called at least twice "
                    "(identity + semantic)"
                )
                return
        assert False, "evaluate_identity_gate function not found"

    def test_no_direct_in_without_normalize(self):
        """白名单 `in` 检查必须在 _normalize_str 之后。"""
        src = self._get_source()
        # 简单文本检查：normalize 后才出现 not in _VALID_
        normalize_pos = src.find("_normalize_str(getattr")
        identity_check_pos = src.find("not in _VALID_IDENTITY_VALUES")
        semantic_check_pos = src.find("not in _VALID_SEMANTIC_VALUES")
        assert normalize_pos < identity_check_pos, (
            "_normalize_str must be called before identity whitelist check"
        )
        assert normalize_pos < semantic_check_pos, (
            "_normalize_str must be called before semantic whitelist check"
        )
