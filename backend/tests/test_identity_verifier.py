"""Consumer Identity Verification — M4 Identity Verifier 单元测试。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §4.5
- D4=(b) interface-only（DESIGN-v1.1 §4.5）

约束：
- M4 是纯函数：零 IO、零异常、零副作用。
- Identity State 判定依据：computed vs manifest。IR 禁止参与。
- Semantic State 独立于 Identity State。
- identity=FAILED 时 semantic=None。
"""

import dataclasses

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

# conftest migrated_db override — 纯单元测试，无 DB 依赖
@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest autouse fixture — 本模块不需要数据库。"""


# ─── 测试常量（独立于实现）───

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


# ─── 基本组合真值表 ───


class TestTruthTable:
    """全部 3×3×3=27 组合的真值表验证。手工预期，不依赖实现。"""

    # computed=A, manifest=A, ir=A → VERIFIED / AVAILABLE
    def test_aaa(self) -> None:
        r = verify_identity(SHA_A, SHA_A, SHA_A)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.identity.mismatches == ()
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_AVAILABLE
        assert r.semantic.reason is None

    # computed=A, manifest=A, ir=B → VERIFIED / PENDING (ir_manifest_mismatch)
    def test_aab(self) -> None:
        r = verify_identity(SHA_A, SHA_A, SHA_B)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.identity.mismatches == ()
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_PENDING
        assert r.semantic.reason == REASON_IR_MANIFEST_MISMATCH

    # computed=A, manifest=A, ir=None → VERIFIED / PENDING (ir_absent)
    def test_aa_none(self) -> None:
        r = verify_identity(SHA_A, SHA_A, None)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.identity.mismatches == ()
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_PENDING
        assert r.semantic.reason == REASON_IR_ABSENT

    # computed=A, manifest=B, ir=A → FAILED (computed_manifest_mismatch)
    def test_aba(self) -> None:
        r = verify_identity(SHA_A, SHA_B, SHA_A)
        assert r.identity.value == IDENTITY_FAILED
        assert r.identity.mismatches == (REASON_COMPUTED_MANIFEST_MISMATCH,)
        assert r.semantic is None

    # computed=A, manifest=B, ir=B → FAILED
    # IR == Manifest，但 Identity 仍然 FAILED（权威攻击）
    def test_abb(self) -> None:
        r = verify_identity(SHA_A, SHA_B, SHA_B)
        assert r.identity.value == IDENTITY_FAILED
        assert r.identity.mismatches == (REASON_COMPUTED_MANIFEST_MISMATCH,)
        assert r.semantic is None

    # computed=A, manifest=B, ir=C → FAILED
    def test_abc(self) -> None:
        r = verify_identity(SHA_A, SHA_B, SHA_C)
        assert r.identity.value == IDENTITY_FAILED
        assert r.semantic is None

    # computed=A, manifest=B, ir=None → FAILED
    def test_ab_none(self) -> None:
        r = verify_identity(SHA_A, SHA_B, None)
        assert r.identity.value == IDENTITY_FAILED
        assert r.semantic is None

    # computed=A, manifest=None, ir=A → FAILED (manifest_sha_missing)
    def test_none_a(self) -> None:
        r = verify_identity(SHA_A, None, SHA_A)
        assert r.identity.value == IDENTITY_FAILED
        assert r.identity.mismatches == (REASON_MANIFEST_SHA_MISSING,)
        assert r.semantic is None

    # computed=A, manifest=None, ir=B → FAILED
    def test_none_b(self) -> None:
        r = verify_identity(SHA_A, None, SHA_B)
        assert r.identity.value == IDENTITY_FAILED
        assert r.identity.mismatches == (REASON_MANIFEST_SHA_MISSING,)
        assert r.semantic is None

    # computed=A, manifest=None, ir=None → FAILED
    def test_none_none(self) -> None:
        r = verify_identity(SHA_A, None, None)
        assert r.identity.value == IDENTITY_FAILED
        assert r.identity.mismatches == (REASON_MANIFEST_SHA_MISSING,)
        assert r.semantic is None


# ─── Authority Boundary（本轮最重要的攻击面）───


class TestAuthorityBoundary:
    """IR 必须不能影响 Identity State。"""

    def test_ir_equals_manifest_but_raw_differs_fails(self) -> None:
        """IR == Manifest != Raw → 必须 FAILED。IR 不能「救回」身份。"""
        r = verify_identity(SHA_A, SHA_B, SHA_B)
        assert r.identity.value == IDENTITY_FAILED

    def test_raw_equals_manifest_but_ir_differs_verifies(self) -> None:
        """Raw == Manifest != IR → Identity VERIFIED, Semantic PENDING。"""
        r = verify_identity(SHA_A, SHA_A, SHA_B)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_PENDING

    def test_ir_sha_not_used_in_identity_check(self) -> None:
        """Identity State 的 mismatches 中不得包含 IR 相关 reason。"""
        r = verify_identity(SHA_A, SHA_B, SHA_A)
        assert r.identity.value == IDENTITY_FAILED
        for reason in r.identity.mismatches:
            assert "ir" not in reason.lower()

    def test_all_three_different_fails(self) -> None:
        """Raw != Manifest != IR → FAILED。"""
        r = verify_identity(SHA_A, SHA_B, SHA_C)
        assert r.identity.value == IDENTITY_FAILED


# ─── Semantic State 正交性 ───


class TestSemanticOrthogonality:
    """Semantic State 不影响 Identity State。"""

    def test_semantic_available_when_all_match(self) -> None:
        r = verify_identity(SHA_A, SHA_A, SHA_A)
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_AVAILABLE
        assert r.semantic.reason is None

    def test_semantic_pending_ir_absent(self) -> None:
        r = verify_identity(SHA_A, SHA_A, None)
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_PENDING
        assert r.semantic.reason == REASON_IR_ABSENT

    def test_semantic_pending_ir_mismatch(self) -> None:
        r = verify_identity(SHA_A, SHA_A, SHA_B)
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_PENDING
        assert r.semantic.reason == REASON_IR_MANIFEST_MISMATCH

    def test_semantic_none_when_identity_fails(self) -> None:
        """identity=FAILED 时 semantic 必须为 None。"""
        for manifest, ir in [(SHA_B, SHA_A), (SHA_B, SHA_B), (None, SHA_A), (None, None)]:
            r = verify_identity(SHA_A, manifest, ir)
            assert r.identity.value == IDENTITY_FAILED
            assert r.semantic is None


# ─── 数据类型约束 ───


class TestDataTypes:
    def test_identity_state_frozen(self) -> None:
        s = IdentityState(IDENTITY_VERIFIED, ())
        with pytest.raises(AttributeError):
            s.value = IDENTITY_FAILED  # type: ignore[misc]

    def test_semantic_state_frozen(self) -> None:
        s = SemanticState(SEMANTIC_PENDING, REASON_IR_ABSENT)
        with pytest.raises(AttributeError):
            s.value = SEMANTIC_AVAILABLE  # type: ignore[misc]

    def test_verification_result_frozen(self) -> None:
        r = verify_identity(SHA_A, SHA_A, SHA_A)
        with pytest.raises(AttributeError):
            r.identity = IdentityState(IDENTITY_FAILED, ())  # type: ignore[misc]

    def test_identity_state_fields(self) -> None:
        names = {f.name for f in dataclasses.fields(IdentityState)}
        assert names == {"value", "mismatches"}

    def test_semantic_state_fields(self) -> None:
        names = {f.name for f in dataclasses.fields(SemanticState)}
        assert names == {"value", "reason"}

    def test_verification_result_fields(self) -> None:
        names = {f.name for f in dataclasses.fields(VerificationResult)}
        assert names == {"identity", "semantic"}

    def test_identity_state_no_path_field(self) -> None:
        names = {f.name for f in dataclasses.fields(IdentityState)}
        assert "path" not in names
        assert "source_file" not in names
        assert "bytes_source" not in names

    def test_mismatches_is_tuple_not_list(self) -> None:
        """frozen dataclass 内 mutable list 违反不可变性。tuple 确保深冻结。"""
        r = verify_identity(SHA_A, SHA_B, SHA_A)
        assert isinstance(r.identity.mismatches, tuple)

    def test_verifier_no_exception_for_any_input(self) -> None:
        """M4 是纯函数，不抛异常。各种边界输入都应返回 VerificationResult。"""
        for computed in [SHA_A, "", "x"]:
            for manifest in [SHA_A, SHA_B, None, ""]:
                for ir in [SHA_A, SHA_B, None, ""]:
                    r = verify_identity(computed, manifest, ir)
                    assert isinstance(r, VerificationResult)
                    assert r.identity.value in (IDENTITY_VERIFIED, IDENTITY_FAILED)
                    if r.semantic is not None:
                        assert r.semantic.value in (SEMANTIC_AVAILABLE, SEMANTIC_PENDING)
