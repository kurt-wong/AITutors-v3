"""M4 对抗性审查第二轮 — 从第一性原理攻击。

攻击面：
A. Authority 不变量穷举 — IR 在所有可能取值下不得影响 Identity
B. 正交性反向攻击 — Semantic 值不得反向影响 Identity
C. Design Spec Case A/B/C 精确验证
D. 数据类型不变量 — frozen dataclass 不允许构造非法状态
E. 字符串比较陷阱 — Python == 的隐藏行为
F. 纯函数性 — 无副作用、无全局状态、确定性
G. Truth table 完备性 — 27 组合全覆盖
H. mismatches 语义精确性
"""

import dataclasses
import hashlib
import inspect

import pytest

from app.core.identity_verifier import (
    IDENTITY_FAILED,
    IDENTITY_VERIFIED,
    REASON_COMPUTED_MANIFEST_MISMATCH,
    REASON_IR_ABSENT,
    REASON_IR_MANIFEST_MISMATCH,
    REASON_MANIFEST_SHA_MISSING,
    SEMANTIC_AVAILABLE,
    SEMANTIC_PENDING,
    IdentityState,
    SemanticState,
    VerificationResult,
    verify_identity,
)


@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest — 纯单元测试。"""


# 独立 SHA 常量（真实 hash，非字面量）
SHA_X = hashlib.sha256(b"content-x").hexdigest()
SHA_Y = hashlib.sha256(b"content-y").hexdigest()
SHA_Z = hashlib.sha256(b"content-z").hexdigest()
SHA_EMPTY = hashlib.sha256(b"").hexdigest()


# ═══════════════════════════════════════════
# A. Authority 不变量穷举
# ═══════════════════════════════════════════


class TestAuthorityInvariantExhaustive:
    """Identity State 只能由 computed 和 manifest 决定。IR 是自由变量。"""

    @pytest.mark.parametrize("computed", [SHA_X, SHA_Y, "", "x", "0" * 64])
    @pytest.mark.parametrize("manifest", [SHA_X, SHA_Y, SHA_Z, None, "", "0" * 64])
    @pytest.mark.parametrize("ir", [SHA_X, SHA_Y, SHA_Z, None, "", "0" * 64, 12345, True, [], {}])
    def test_identity_invariant_under_ir_variation(
        self,
        computed: str,
        manifest: str | None,
        ir: object,
    ) -> None:
        """固定 computed 和 manifest，穷举 ir 所有可能取值。
        Identity State 必须完全不变。"""
        r1 = verify_identity(computed, manifest, SHA_X)  # type: ignore[arg-type]
        r2 = verify_identity(computed, manifest, ir)  # type: ignore[arg-type]
        assert r1.identity.value == r2.identity.value, (
            f"computed={computed!r}, manifest={manifest!r}: "
            f"ir=SHA_X 得到 {r1.identity.value}, ir={ir!r} 得到 {r2.identity.value}"
        )
        assert r1.identity.mismatches == r2.identity.mismatches

    def test_ir_value_cannot_flip_failed_to_verified(self) -> None:
        """穷举 ir 所有类型，不能把 FAILED 翻转为 VERIFIED。"""
        for ir_val in [SHA_X, SHA_Y, None, "", 0, 1, False, True, [], {}, (), b"", b"x", 3.14]:
            r = verify_identity(SHA_X, SHA_Y, ir_val)  # type: ignore[arg-type]
            assert r.identity.value == IDENTITY_FAILED, f"ir={ir_val!r} 翻转了 FAILED"

    def test_ir_value_cannot_flip_verified_to_failed(self) -> None:
        """穷举 ir 所有类型，不能把 VERIFIED 翻转为 FAILED。"""
        for ir_val in [SHA_X, SHA_Y, None, "", 0, 1, False, True, [], {}, (), b"", b"x", 3.14]:
            r = verify_identity(SHA_X, SHA_X, ir_val)  # type: ignore[arg-type]
            assert r.identity.value == IDENTITY_VERIFIED, f"ir={ir_val!r} 翻转了 VERIFIED"

    def test_identity_mismatches_never_contain_ir_information(self) -> None:
        """mismatches 中的任何字符串都不得包含 ir 值或 ir 相关关键词。"""
        ir_secret = "SECRET_IR_VALUE_SHOULD_NOT_LEAK"
        for manifest in [SHA_Y, None]:
            r = verify_identity(SHA_X, manifest, ir_secret)
            for reason in r.identity.mismatches:
                assert "SECRET" not in reason
                assert "ir_" not in reason or reason in (
                    REASON_MANIFEST_SHA_MISSING,
                    REASON_COMPUTED_MANIFEST_MISMATCH,
                )


# ═══════════════════════════════════════════
# B. 正交性反向攻击
# ═══════════════════════════════════════════


class TestOrthogonalityReverseAttack:
    """Semantic State 不得反向影响 Identity State。"""

    def test_semantic_available_never_changes_identity(self) -> None:
        """当 ir==manifest==computed → AVAILABLE，identity 仍由 computed==manifest 决定。"""
        r = verify_identity(SHA_X, SHA_X, SHA_X)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.semantic is not None and r.semantic.value == SEMANTIC_AVAILABLE
        # ir==manifest 但 computed != manifest → 仍 FAILED
        r2 = verify_identity(SHA_Y, SHA_X, SHA_X)
        assert r2.identity.value == IDENTITY_FAILED
        assert r2.semantic is None

    def test_semantic_pending_never_changes_identity(self) -> None:
        """PENDING 状态不影响 identity。"""
        r1 = verify_identity(SHA_X, SHA_X, None)
        assert r1.identity.value == IDENTITY_VERIFIED
        assert r1.semantic is not None and r1.semantic.value == SEMANTIC_PENDING
        r2 = verify_identity(SHA_X, SHA_X, SHA_Y)
        assert r2.identity.value == IDENTITY_VERIFIED
        assert r2.semantic is not None and r2.semantic.value == SEMANTIC_PENDING

    def test_semantic_none_only_when_identity_fails(self) -> None:
        """semantic=None ⟺ identity=FAILED。双向验证。"""
        for computed, manifest in [(SHA_X, SHA_Y), (SHA_X, None), (SHA_X, "")]:
            r = verify_identity(computed, manifest, SHA_X)
            if r.identity.value == IDENTITY_FAILED:
                assert r.semantic is None
        for ir in [SHA_X, None, SHA_Y]:
            r = verify_identity(SHA_X, SHA_X, ir)
            assert r.semantic is not None


# ═══════════════════════════════════════════
# C. Design Spec Case A/B/C 精确验证
# ═══════════════════════════════════════════


class TestDesignSpecCases:
    """Design v1.1 §六 明确要求的三个 case。"""

    def test_case_a_raw_a_manifest_a_ir_b(self) -> None:
        """Case A: Raw=A, Manifest=A, IR=B → Identity=VERIFIED, Semantic=PENDING"""
        r = verify_identity(SHA_X, SHA_X, SHA_Y)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_PENDING
        assert r.semantic.reason == REASON_IR_MANIFEST_MISMATCH

    def test_case_b_raw_a_manifest_b_ir_b(self) -> None:
        """Case B: Raw=A, Manifest=B, IR=B → Identity=FAILED
        即使 IR == Manifest 也不得 VERIFIED。"""
        r = verify_identity(SHA_X, SHA_Y, SHA_Y)
        assert r.identity.value == IDENTITY_FAILED
        assert r.semantic is None
        assert REASON_COMPUTED_MANIFEST_MISMATCH in r.identity.mismatches

    def test_case_c_raw_a_manifest_a_ir_none(self) -> None:
        """Case C: Raw=A, Manifest=A, IR=None → Identity=VERIFIED, Semantic=PENDING"""
        r = verify_identity(SHA_X, SHA_X, None)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_PENDING
        assert r.semantic.reason == REASON_IR_ABSENT


# ═══════════════════════════════════════════
# D. 数据类型不变量
# ═══════════════════════════════════════════


class TestDataTypeInvariants:
    """frozen dataclass 的字段约束和不变量。"""

    def test_identity_state_value_must_be_string(self) -> None:
        s = IdentityState(IDENTITY_VERIFIED, ())
        assert isinstance(s.value, str)
        assert s.value in (IDENTITY_VERIFIED, IDENTITY_FAILED)

    def test_semantic_state_value_must_be_string(self) -> None:
        s = SemanticState(SEMANTIC_AVAILABLE, None)
        assert isinstance(s.value, str)
        assert s.value in (SEMANTIC_AVAILABLE, SEMANTIC_PENDING)

    def test_identity_state_mismatches_is_tuple(self) -> None:
        s = IdentityState(IDENTITY_FAILED, (REASON_MANIFEST_SHA_MISSING,))
        assert isinstance(s.mismatches, tuple)
        assert all(isinstance(m, str) for m in s.mismatches)

    def test_semantic_state_reason_is_str_or_none(self) -> None:
        s1 = SemanticState(SEMANTIC_AVAILABLE, None)
        assert s1.reason is None
        s2 = SemanticState(SEMANTIC_PENDING, REASON_IR_ABSENT)
        assert isinstance(s2.reason, str)

    def test_verification_result_identity_field_type(self) -> None:
        r = verify_identity(SHA_X, SHA_X, SHA_X)
        assert isinstance(r.identity, IdentityState)
        assert r.semantic is None or isinstance(r.semantic, SemanticState)

    def test_no_constructor_can_create_verified_with_semantic_none(self) -> None:
        """verify_identity 永远不会返回 identity=VERIFIED + semantic=None。"""
        for computed in [SHA_X, SHA_Y, "", "x"]:
            for manifest in [SHA_X, SHA_Y, None, ""]:
                for ir in [SHA_X, SHA_Y, None, "", 12345, True, [], {}]:
                    r = verify_identity(computed, manifest, ir)  # type: ignore[arg-type]
                    if r.identity.value == IDENTITY_VERIFIED:
                        assert r.semantic is not None, (
                            f"VERIFIED + semantic=None 违反不变量: "
                            f"computed={computed!r}, manifest={manifest!r}, ir={ir!r}"
                        )

    def test_no_constructor_can_create_failed_with_semantic_not_none(self) -> None:
        """verify_identity 永远不会返回 identity=FAILED + semantic 非 None。"""
        for computed in [SHA_X, SHA_Y, "", "x"]:
            for manifest in [SHA_X, SHA_Y, None, ""]:
                for ir in [SHA_X, SHA_Y, None, "", 12345, True, [], {}]:
                    r = verify_identity(computed, manifest, ir)  # type: ignore[arg-type]
                    if r.identity.value == IDENTITY_FAILED:
                        assert r.semantic is None, (
                            f"FAILED + semantic 非 None 违反不变量: "
                            f"computed={computed!r}, manifest={manifest!r}, ir={ir!r}"
                        )

    def test_identity_state_fields_exact(self) -> None:
        names = {f.name for f in dataclasses.fields(IdentityState)}
        assert names == {"value", "mismatches"}, f"多余字段: {names - {'value', 'mismatches'}}"

    def test_semantic_state_fields_exact(self) -> None:
        names = {f.name for f in dataclasses.fields(SemanticState)}
        assert names == {"value", "reason"}, f"多余字段: {names - {'value', 'reason'}}"

    def test_verification_result_fields_exact(self) -> None:
        names = {f.name for f in dataclasses.fields(VerificationResult)}
        assert names == {"identity", "semantic"}, f"多余字段: {names - {'identity', 'semantic'}}"


# ═══════════════════════════════════════════
# E. 字符串比较陷阱
# ═══════════════════════════════════════════


class TestStringComparisonTraps:
    """Python == 运算符的隐藏行为可能被利用。"""

    def test_bool_true_equals_int_one(self) -> None:
        """True == 1 在 Python 中为 True。但 True != SHA 字符串。"""
        r = verify_identity(SHA_X, True, True)  # type: ignore[arg-type]
        assert r.identity.value == IDENTITY_FAILED

    def test_int_zero_not_equal_empty_string(self) -> None:
        r = verify_identity(0, "", None)  # type: ignore[arg-type]
        assert r.identity.value == IDENTITY_FAILED

    def test_bytes_not_equal_string(self) -> None:
        r = verify_identity(b"abc", "abc", None)  # type: ignore[arg-type]
        assert r.identity.value == IDENTITY_FAILED

    def test_tuple_not_equal_string(self) -> None:
        r = verify_identity(("a",), "a", None)  # type: ignore[arg-type]
        assert r.identity.value == IDENTITY_FAILED

    def test_list_not_equal_string(self) -> None:
        r = verify_identity(["a"], "a", None)  # type: ignore[arg-type]
        assert r.identity.value == IDENTITY_FAILED

    def test_empty_string_equals_empty_string(self) -> None:
        """两个空字符串相等 → VERIFIED。这是 Python == 的正确行为。"""
        r = verify_identity("", "", None)
        assert r.identity.value == IDENTITY_VERIFIED

    def test_same_object_identity(self) -> None:
        sha = SHA_X
        r = verify_identity(sha, sha, None)
        assert r.identity.value == IDENTITY_VERIFIED

    def test_equal_but_different_objects(self) -> None:
        r = verify_identity("a" * 64, "a" * 64, None)
        assert r.identity.value == IDENTITY_VERIFIED


# ═══════════════════════════════════════════
# F. 纯函数性
# ═══════════════════════════════════════════


class TestPurity:
    """M4 必须是纯函数：无副作用、确定性、无状态。"""

    def test_deterministic_output(self) -> None:
        """同一输入多次调用输出完全相同。"""
        inputs = [
            (SHA_X, SHA_X, SHA_X),
            (SHA_X, SHA_Y, SHA_X),
            (SHA_X, None, SHA_X),
            (SHA_X, SHA_X, None),
            (SHA_X, SHA_X, SHA_Y),
            ("", "", None),
            ("x", "y", "z"),
        ]
        for computed, manifest, ir in inputs:
            results = [verify_identity(computed, manifest, ir) for _ in range(10)]
            assert all(r == results[0] for r in results), f"非确定性: {computed}, {manifest}, {ir}"

    def test_no_global_state_modification(self) -> None:
        """调用前后模块级变量不变。"""
        import app.core.identity_verifier as mod
        before = {
            k: v for k, v in vars(mod).items()
            if not k.startswith("_") and not callable(v) and not isinstance(v, type)
        }
        verify_identity(SHA_X, SHA_X, SHA_X)
        verify_identity(SHA_X, SHA_Y, None)
        after = {
            k: v for k, v in vars(mod).items()
            if not k.startswith("_") and not callable(v) and not isinstance(v, type)
        }
        assert before == after

    def test_no_mutable_default_arguments(self) -> None:
        """函数签名中不得有 mutable 默认值。"""
        sig = inspect.signature(verify_identity)
        for name, param in sig.parameters.items():
            if param.default is not inspect.Parameter.empty:
                assert not isinstance(param.default, (list, dict, set)), (
                    f"参数 {name} 使用了 mutable 默认值"
                )

    def test_mismatches_tuple_shared_safely(self) -> None:
        """VERIFIED 时 mismatches 是空 tuple，多个结果共享同一 tuple 不会互相影响。"""
        r1 = verify_identity(SHA_X, SHA_X, SHA_X)
        r2 = verify_identity(SHA_Y, SHA_Y, SHA_Y)
        assert r1.identity.mismatches == r2.identity.mismatches == ()
        assert r1.identity.mismatches is r2.identity.mismatches


# ═══════════════════════════════════════════
# G. Truth table 完备性
# ═══════════════════════════════════════════


class TestTruthTableCompleteness:
    """穷举所有 (computed, manifest, ir) 组合，验证与手工预期一致。"""

    @pytest.mark.parametrize("computed", [SHA_X, SHA_Y])
    @pytest.mark.parametrize("manifest", [SHA_X, SHA_Y, None])
    @pytest.mark.parametrize("ir", [SHA_X, SHA_Y, None])
    def test_exhaustive_2x3x3(
        self,
        computed: str,
        manifest: str | None,
        ir: str | None,
    ) -> None:
        r = verify_identity(computed, manifest, ir)

        # 手工推导 expected（不依赖实现）
        if manifest is None:
            exp_id = IDENTITY_FAILED
            exp_sem = None
            exp_reason_id = REASON_MANIFEST_SHA_MISSING
        elif computed != manifest:
            exp_id = IDENTITY_FAILED
            exp_sem = None
            exp_reason_id = REASON_COMPUTED_MANIFEST_MISMATCH
        else:
            exp_id = IDENTITY_VERIFIED
            if ir is None:
                exp_sem = SEMANTIC_PENDING
                exp_reason_sem = REASON_IR_ABSENT
            elif ir != manifest:
                exp_sem = SEMANTIC_PENDING
                exp_reason_sem = REASON_IR_MANIFEST_MISMATCH
            else:
                exp_sem = SEMANTIC_AVAILABLE
                exp_reason_sem = None

        assert r.identity.value == exp_id, (
            f"computed={computed[:8]}, manifest={manifest[:8] if manifest else None}, "
            f"ir={ir[:8] if ir else None}"
        )
        if exp_id == IDENTITY_FAILED:
            assert r.semantic is None
            assert exp_reason_id in r.identity.mismatches
        else:
            assert r.semantic is not None
            assert r.semantic.value == exp_sem
            assert r.semantic.reason == exp_reason_sem


# ═══════════════════════════════════════════
# H. mismatches 语义精确性
# ═══════════════════════════════════════════


class TestMismatchSemantics:
    """mismatches 内容必须精确反映失败原因。"""

    def test_manifest_missing_reason(self) -> None:
        r = verify_identity(SHA_X, None, SHA_X)
        assert r.identity.mismatches == (REASON_MANIFEST_SHA_MISSING,)
        assert len(r.identity.mismatches) == 1

    def test_mismatch_reason(self) -> None:
        r = verify_identity(SHA_X, SHA_Y, SHA_X)
        assert r.identity.mismatches == (REASON_COMPUTED_MANIFEST_MISMATCH,)
        assert len(r.identity.mismatches) == 1

    def test_verified_mismatches_empty(self) -> None:
        r = verify_identity(SHA_X, SHA_X, SHA_X)
        assert r.identity.mismatches == ()

    def test_failed_mismatches_never_empty(self) -> None:
        """FAILED 时 mismatches 永远不为空。"""
        for computed, manifest in [(SHA_X, SHA_Y), (SHA_X, None), (SHA_X, ""), ("", SHA_X)]:
            r = verify_identity(computed, manifest, None)
            if r.identity.value == IDENTITY_FAILED:
                assert len(r.identity.mismatches) > 0, (
                    f"FAILED 但 mismatches 为空: computed={computed!r}, manifest={manifest!r}"
                )

    def test_semantic_reason_none_only_when_available(self) -> None:
        """semantic.reason=None ⟺ semantic.value=AVAILABLE。"""
        for ir in [SHA_X, SHA_Y, None]:
            r = verify_identity(SHA_X, SHA_X, ir)
            assert r.semantic is not None
            if r.semantic.value == SEMANTIC_AVAILABLE:
                assert r.semantic.reason is None
            else:
                assert r.semantic.reason is not None

    def test_semantic_reason_precise(self) -> None:
        """PENDING 时 reason 必须精确。"""
        r1 = verify_identity(SHA_X, SHA_X, None)
        assert r1.semantic is not None and r1.semantic.reason == REASON_IR_ABSENT

        r2 = verify_identity(SHA_X, SHA_X, SHA_Y)
        assert r2.semantic is not None and r2.semantic.reason == REASON_IR_MANIFEST_MISMATCH
