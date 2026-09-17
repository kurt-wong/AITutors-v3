"""Consumer Identity Verification — M4 Identity Verifier 对抗性审查。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §4.5
- Owner: "从第一性原理出发，针对本轮结果开启一轮严格的对抗性审查"

攻击面：
A. 权威等级攻击 — IR 不能影响 Identity
B. 正交性攻击 — Semantic 不能反向影响 Identity
C. 组合完备性 — 参数化全组合穷举
D. 边界输入 — None/empty/uppercase/non-hex/unicode/长度
E. 重复身份语义 — 同 SHA 不同 path 合法
F. 纯函数边界 — AST 静态审计无 IO/异常
G. Frozen dataclass 深度不可变
H. 真实 hash 端到端
"""

import ast
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

# conftest migrated_db override
@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest autouse fixture — 本模块不需要数据库。"""


# ─── 独立测试常量 ───

RAW_SHA = hashlib.sha256(b"raw source content").hexdigest()
MANIFEST_SHA = hashlib.sha256(b"manifest declared content").hexdigest()
IR_SHA = hashlib.sha256(b"ir embedded content").hexdigest()
SAME_SHA = hashlib.sha256(b"same content").hexdigest()
OTHER_SHA = hashlib.sha256(b"different content").hexdigest()


# ═══════════════════════════════════════════
# A. 权威等级攻击
# ═══════════════════════════════════════════


class TestAuthorityAttack:
    """IR == Manifest != Raw → 必须 FAILED。IR 不是身份来源。"""

    def test_ir_manifest_collusion_fails(self) -> None:
        """IR 和 Manifest 串通一致，但 Raw 不同 → 必须 FAILED。"""
        r = verify_identity(RAW_SHA, MANIFEST_SHA, MANIFEST_SHA)
        assert r.identity.value == IDENTITY_FAILED
        assert REASON_COMPUTED_MANIFEST_MISMATCH in r.identity.mismatches

    def test_ir_cannot_rescue_identity(self) -> None:
        """IR 无论设为什么值，都不能让 mismatched identity 变 VERIFIED。"""
        for ir_val in [RAW_SHA, MANIFEST_SHA, IR_SHA, OTHER_SHA, SAME_SHA, None, ""]:
            r = verify_identity(RAW_SHA, MANIFEST_SHA, ir_val)
            assert r.identity.value == IDENTITY_FAILED, f"ir={ir_val!r} 不应改变 identity"

    def test_raw_manifest_match_ir_cannot_break_identity(self) -> None:
        """Raw == Manifest 时，IR 无论设什么，identity 都是 VERIFIED。"""
        for ir_val in [RAW_SHA, IR_SHA, OTHER_SHA, SAME_SHA, None, ""]:
            r = verify_identity(RAW_SHA, RAW_SHA, ir_val)
            assert r.identity.value == IDENTITY_VERIFIED, f"ir={ir_val!r} 不应改变 identity"

    def test_identity_determined_only_by_computed_and_manifest(self) -> None:
        """Identity State 的值只能由 computed 和 manifest 决定。穷举验证。"""
        for computed in [RAW_SHA, OTHER_SHA]:
            for manifest in [RAW_SHA, OTHER_SHA, None]:
                for ir in [RAW_SHA, OTHER_SHA, IR_SHA, None]:
                    r = verify_identity(computed, manifest, ir)
                    if manifest is None:
                        expected = IDENTITY_FAILED
                    elif computed == manifest:
                        expected = IDENTITY_VERIFIED
                    else:
                        expected = IDENTITY_FAILED
                    assert r.identity.value == expected, (
                        f"computed={computed[:8]}, manifest="
                        f"{manifest[:8] if manifest else None}, ir={ir[:8] if ir else None}"
                    )

    def test_identity_mismatches_never_contain_ir_reason(self) -> None:
        """FAILED 时 mismatches 中不得出现任何 IR 相关原因码。"""
        for manifest, ir in [
            (MANIFEST_SHA, RAW_SHA),
            (MANIFEST_SHA, IR_SHA),
            (None, RAW_SHA),
            (None, None),
        ]:
            r = verify_identity(RAW_SHA, manifest, ir)
            if r.identity.value == IDENTITY_FAILED:
                for reason in r.identity.mismatches:
                    assert reason in (
                        REASON_MANIFEST_SHA_MISSING,
                        REASON_COMPUTED_MANIFEST_MISMATCH,
                    ), f"不应出现 IR 相关 reason: {reason}"


# ═══════════════════════════════════════════
# B. 正交性攻击
# ═══════════════════════════════════════════


class TestOrthogonalityAttack:
    """Semantic State 和 Identity State 完全独立。"""

    def test_semantic_state_does_not_affect_identity(self) -> None:
        """无论 semantic 如何，identity 不变。"""
        for ir in [RAW_SHA, IR_SHA, None]:
            r = verify_identity(RAW_SHA, RAW_SHA, ir)
            assert r.identity.value == IDENTITY_VERIFIED
        for ir in [RAW_SHA, IR_SHA, None]:
            r = verify_identity(RAW_SHA, MANIFEST_SHA, ir)
            assert r.identity.value == IDENTITY_FAILED

    def test_semantic_none_when_identity_fails_for_all_combos(self) -> None:
        """identity=FAILED 时 semantic 必须为 None。穷举。"""
        for computed in [RAW_SHA, OTHER_SHA]:
            for manifest in [MANIFEST_SHA, None]:
                for ir in [RAW_SHA, IR_SHA, OTHER_SHA, None]:
                    r = verify_identity(computed, manifest, ir)
                    if r.identity.value == IDENTITY_FAILED:
                        assert r.semantic is None, (
                            f"FAILED 时 semantic 不应为 {r.semantic}"
                        )

    def test_semantic_present_when_identity_verifies(self) -> None:
        """identity=VERIFIED 时 semantic 必须不为 None。"""
        for ir in [RAW_SHA, IR_SHA, OTHER_SHA, None]:
            r = verify_identity(RAW_SHA, RAW_SHA, ir)
            assert r.identity.value == IDENTITY_VERIFIED
            assert r.semantic is not None

    def test_four_state_combinations_exist(self) -> None:
        """正交双轴应产生 4 种合法组合（其中 FAILED+semantic=None）。"""
        r1 = verify_identity(RAW_SHA, RAW_SHA, RAW_SHA)
        assert r1.identity.value == IDENTITY_VERIFIED
        assert r1.semantic is not None and r1.semantic.value == SEMANTIC_AVAILABLE

        r2 = verify_identity(RAW_SHA, RAW_SHA, None)
        assert r2.identity.value == IDENTITY_VERIFIED
        assert r2.semantic is not None and r2.semantic.value == SEMANTIC_PENDING
        assert r2.semantic.reason == REASON_IR_ABSENT

        r3 = verify_identity(RAW_SHA, RAW_SHA, IR_SHA)
        assert r3.identity.value == IDENTITY_VERIFIED
        assert r3.semantic is not None and r3.semantic.value == SEMANTIC_PENDING
        assert r3.semantic.reason == REASON_IR_MANIFEST_MISMATCH

        r4 = verify_identity(RAW_SHA, MANIFEST_SHA, RAW_SHA)
        assert r4.identity.value == IDENTITY_FAILED
        assert r4.semantic is None


# ═══════════════════════════════════════════
# C. 参数化全组合穷举
# ═══════════════════════════════════════════


class TestExhaustiveCombinations:
    """手工真值表：不依赖实现生成 expected。"""

    TRUTH_TABLE = [
        # ── VERIFIED ──
        (RAW_SHA, RAW_SHA, RAW_SHA, IDENTITY_VERIFIED, SEMANTIC_AVAILABLE, None),
        (RAW_SHA, RAW_SHA, IR_SHA, IDENTITY_VERIFIED, SEMANTIC_PENDING, REASON_IR_MANIFEST_MISMATCH),
        (RAW_SHA, RAW_SHA, None, IDENTITY_VERIFIED, SEMANTIC_PENDING, REASON_IR_ABSENT),
        (RAW_SHA, RAW_SHA, OTHER_SHA, IDENTITY_VERIFIED, SEMANTIC_PENDING, REASON_IR_MANIFEST_MISMATCH),
        # ── FAILED (computed != manifest) ──
        (RAW_SHA, MANIFEST_SHA, RAW_SHA, IDENTITY_FAILED, None, None),
        (RAW_SHA, MANIFEST_SHA, MANIFEST_SHA, IDENTITY_FAILED, None, None),
        (RAW_SHA, MANIFEST_SHA, IR_SHA, IDENTITY_FAILED, None, None),
        (RAW_SHA, MANIFEST_SHA, None, IDENTITY_FAILED, None, None),
        (RAW_SHA, OTHER_SHA, RAW_SHA, IDENTITY_FAILED, None, None),
        (RAW_SHA, OTHER_SHA, OTHER_SHA, IDENTITY_FAILED, None, None),
        # ── FAILED (manifest is None) ──
        (RAW_SHA, None, RAW_SHA, IDENTITY_FAILED, None, None),
        (RAW_SHA, None, IR_SHA, IDENTITY_FAILED, None, None),
        (RAW_SHA, None, OTHER_SHA, IDENTITY_FAILED, None, None),
        (RAW_SHA, None, None, IDENTITY_FAILED, None, None),
    ]

    @pytest.mark.parametrize(
        "computed,manifest,ir,exp_id,exp_sem,exp_reason",
        TRUTH_TABLE,
        ids=[
            "all-match", "ir-differs", "ir-absent", "ir-other",
            "manifest-mismatch-ir-raw", "manifest-mismatch-ir-eq-manifest",
            "manifest-mismatch-ir-diff", "manifest-mismatch-ir-none",
            "manifest-other-ir-raw", "manifest-other-ir-other",
            "manifest-none-ir-raw", "manifest-none-ir-ir",
            "manifest-none-ir-other", "manifest-none-ir-none",
        ],
    )
    def test_truth_table(
        self,
        computed: str,
        manifest: str | None,
        ir: str | None,
        exp_id: str,
        exp_sem: str | None,
        exp_reason: str | None,
    ) -> None:
        r = verify_identity(computed, manifest, ir)
        assert r.identity.value == exp_id
        if exp_sem is None:
            assert r.semantic is None
        else:
            assert r.semantic is not None
            assert r.semantic.value == exp_sem
            assert r.semantic.reason == exp_reason

    def test_truth_table_covers_all_identity_semantic_pairs(self) -> None:
        """验证真值表覆盖了所有 4 种 (identity, semantic) 组合。"""
        pairs = set()
        for computed, manifest, ir, exp_id, exp_sem, _ in self.TRUTH_TABLE:
            pairs.add((exp_id, exp_sem))
        assert (IDENTITY_VERIFIED, SEMANTIC_AVAILABLE) in pairs
        assert (IDENTITY_VERIFIED, SEMANTIC_PENDING) in pairs
        assert (IDENTITY_FAILED, None) in pairs


# ═══════════════════════════════════════════
# D. 边界输入
# ═══════════════════════════════════════════


class TestBoundaryInputs:
    """M4 不做格式验证（那是 M1/M3 的职责），但不能崩溃。"""

    def test_empty_string_computed(self) -> None:
        r = verify_identity("", "", None)
        assert isinstance(r, VerificationResult)

    def test_empty_string_manifest(self) -> None:
        r = verify_identity(RAW_SHA, "", None)
        assert r.identity.value == IDENTITY_FAILED

    def test_uppercase_sha_mismatch(self) -> None:
        """大写 SHA 应该和小写 SHA 不匹配（字符串比较）。"""
        r = verify_identity(RAW_SHA, RAW_SHA.upper(), None)
        assert r.identity.value == IDENTITY_FAILED

    def test_uppercase_both_match(self) -> None:
        """两个都大写且相等 → 字符串比较相等 → VERIFIED。M4 不做格式校验。"""
        r = verify_identity(RAW_SHA.upper(), RAW_SHA.upper(), None)
        assert r.identity.value == IDENTITY_VERIFIED

    def test_trailing_newline_mismatch(self) -> None:
        r = verify_identity(RAW_SHA, RAW_SHA + "\n", None)
        assert r.identity.value == IDENTITY_FAILED

    def test_non_hex_string(self) -> None:
        r = verify_identity("z" * 64, "z" * 64, None)
        assert r.identity.value == IDENTITY_VERIFIED  # 字符串比较相等

    def test_wrong_length_mismatch(self) -> None:
        r = verify_identity(RAW_SHA[:32], RAW_SHA, None)
        assert r.identity.value == IDENTITY_FAILED

    def test_unicode_lookalike_mismatch(self) -> None:
        """Unicode lookalike 字符不等于 ASCII。"""
        fake = "а" * 64  # Cyrillic 'а' (U+0430)
        r = verify_identity(RAW_SHA, fake, None)
        assert r.identity.value == IDENTITY_FAILED

    def test_non_string_computed_does_not_crash(self) -> None:
        for bad in [12345, 3.14, [], {}, True]:
            r = verify_identity(bad, None, None)  # type: ignore[arg-type]
            assert r.identity.value == IDENTITY_FAILED

    def test_non_string_manifest_does_not_crash(self) -> None:
        for bad in [12345, 3.14, [], {}, True]:
            r = verify_identity(RAW_SHA, bad, None)  # type: ignore[arg-type]
            assert isinstance(r, VerificationResult)

    def test_non_string_ir_does_not_crash(self) -> None:
        for bad in [12345, 3.14, [], {}, True]:
            r = verify_identity(RAW_SHA, RAW_SHA, bad)  # type: ignore[arg-type]
            assert isinstance(r, VerificationResult)

    def test_none_computed_does_not_crash(self) -> None:
        r = verify_identity(None, None, None)  # type: ignore[arg-type]
        assert r.identity.value == IDENTITY_FAILED

    def test_64_char_boundary_exact(self) -> None:
        """64-char hex 是有效 SHA。63 和 65 都不是（但 M4 只做字符串比较）。"""
        sha64 = "0" * 64
        sha63 = "0" * 63
        sha65 = "0" * 65
        assert verify_identity(sha64, sha64, None).identity.value == IDENTITY_VERIFIED
        assert verify_identity(sha63, sha64, None).identity.value == IDENTITY_FAILED
        assert verify_identity(sha65, sha64, None).identity.value == IDENTITY_FAILED


# ═══════════════════════════════════════════
# E. 重复身份语义 — 同 SHA 不同 path 合法
# ═══════════════════════════════════════════


class TestDuplicateIdentitySemantics:
    """同一内容位于多个 locator 是合法的。M4 不建立 SHA→path 唯一性。"""

    def test_same_sha_from_different_paths_is_verifiable(self) -> None:
        """两个不同 path 的文件内容相同 → 相同 SHA → M4 应正常 VERIFIED。"""
        content = b"identical content from two locations"
        sha = hashlib.sha256(content).hexdigest()
        r = verify_identity(sha, sha, sha)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_AVAILABLE

    def test_no_global_sha_registry(self) -> None:
        """M4 不维护任何模块级 SHA 注册表。"""
        import app.core.identity_verifier as mod
        for name, val in vars(mod).items():
            if name.startswith("_"):
                continue
            if isinstance(val, (set, dict, list)):
                pytest.fail(f"模块级可变状态 {name} = {val!r} 违反纯函数约束")

    def test_verifier_is_stateless_across_calls(self) -> None:
        """同一输入多次调用结果完全一致（无隐藏状态）。"""
        inputs = (RAW_SHA, MANIFEST_SHA, IR_SHA)
        r1 = verify_identity(*inputs)
        r2 = verify_identity(*inputs)
        r3 = verify_identity(*inputs)
        assert r1 == r2 == r3

    def test_no_path_fields_in_any_output_type(self) -> None:
        """VerificationResult / IdentityState / SemanticState 均无 path 字段。"""
        for cls in [IdentityState, SemanticState, VerificationResult]:
            names = {f.name for f in dataclasses.fields(cls)}
            for forbidden in ["path", "source_file", "bytes_source", "locator", "file"]:
                assert forbidden not in names, f"{cls.__name__} 含禁止字段 {forbidden}"


# ═══════════════════════════════════════════
# F. 纯函数边界 — AST 静态审计
# ═══════════════════════════════════════════


class TestPureFunctionAudit:
    """AST 静态审计：验证 M4 无 IO、无异常、无外部依赖。"""

    def _get_source(self) -> str:
        return inspect.getsource(
            __import__("app.core.identity_verifier", fromlist=["verify_identity"])
        )

    def _get_ast(self) -> ast.Module:
        return ast.parse(self._get_source())

    def test_no_import_of_hashlib(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "hashlib" not in alias.name
            if isinstance(node, ast.ImportFrom):
                assert node.module is None or "hashlib" not in node.module

    def test_no_import_of_pathlib(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "pathlib" not in alias.name
            if isinstance(node, ast.ImportFrom):
                assert node.module is None or "pathlib" not in node.module

    def test_no_file_io_calls(self) -> None:
        tree = self._get_ast()
        io_methods = {
            "open", "read_text", "read_bytes", "write_text", "write_bytes",
            "readline", "readlines", "seek", "tell", "close",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in io_methods, f"发现 IO 调用: {node.func.attr}"
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in io_methods, f"发现 IO 调用: {node.func.id}"

    def test_no_raise_statements(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                pytest.fail("M4 不应包含 raise 语句（纯函数不抛异常）")

    def test_no_try_except(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                pytest.fail("M4 不应包含 try/except（纯函数不处理异常）")

    def test_no_global_mutable_state(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        if isinstance(node.value, (ast.Constant, ast.Tuple)):
                            continue
                        if isinstance(node.value, ast.Call):
                            continue
                        if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                            pytest.fail(f"模块级可变状态: {target.id}")

    def test_function_signature_matches_design(self) -> None:
        sig = inspect.signature(verify_identity)
        params = list(sig.parameters.keys())
        assert params == ["computed_sha", "manifest_sha", "ir_sha"]
        assert sig.parameters["manifest_sha"].default is None
        assert sig.parameters["ir_sha"].default is None
        assert sig.parameters["computed_sha"].default is inspect.Parameter.empty

    def test_no_external_module_calls_beyond_dataclasses(self) -> None:
        """M4 不应调用 app.core 下的其他模块。"""
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "app.core" in node.module:
                    pytest.fail(f"M4 不应导入其他 app.core 模块: {node.module}")


# ═══════════════════════════════════════════
# G. Frozen dataclass 深度不可变
# ═══════════════════════════════════════════


class TestDeepImmutability:
    def test_identity_state_deep_frozen(self) -> None:
        s = IdentityState(IDENTITY_VERIFIED, (REASON_IR_ABSENT,))
        with pytest.raises(AttributeError):
            s.value = "hacked"

    def test_semantic_state_deep_frozen(self) -> None:
        s = SemanticState(SEMANTIC_PENDING, REASON_IR_ABSENT)
        with pytest.raises(AttributeError):
            s.value = "hacked"

    def test_verification_result_deep_frozen(self) -> None:
        r = verify_identity(RAW_SHA, RAW_SHA, None)
        with pytest.raises(AttributeError):
            r.identity = IdentityState(IDENTITY_FAILED, ())
        with pytest.raises(AttributeError):
            r.semantic = None

    def test_mismatches_tuple_is_immutable(self) -> None:
        r = verify_identity(RAW_SHA, MANIFEST_SHA, RAW_SHA)
        assert isinstance(r.identity.mismatches, tuple)
        with pytest.raises(AttributeError):
            r.identity.mismatches.append("new")  # type: ignore[attr-defined]
        with pytest.raises(TypeError):
            r.identity.mismatches[0] = "hacked"  # type: ignore[index]

    def test_verification_result_equality(self) -> None:
        r1 = verify_identity(RAW_SHA, RAW_SHA, RAW_SHA)
        r2 = verify_identity(RAW_SHA, RAW_SHA, RAW_SHA)
        assert r1 == r2

    def test_verification_result_inequality(self) -> None:
        r1 = verify_identity(RAW_SHA, RAW_SHA, RAW_SHA)
        r2 = verify_identity(RAW_SHA, RAW_SHA, None)
        assert r1 != r2


# ═══════════════════════════════════════════
# H. 真实 hash 端到端
# ═══════════════════════════════════════════


class TestRealHashEndToEnd:
    """使用真实 hashlib 计算的 SHA 进行端到端验证。"""

    def test_real_sha_all_match(self) -> None:
        content = b"real source file content for testing"
        sha = hashlib.sha256(content).hexdigest()
        r = verify_identity(sha, sha, sha)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_AVAILABLE

    def test_real_sha_content_modified(self) -> None:
        """源内容被篡改 → computed SHA 变化 → FAILED。"""
        original = b"original content"
        tampered = b"tampered content!"
        computed = hashlib.sha256(tampered).hexdigest()
        declared = hashlib.sha256(original).hexdigest()
        r = verify_identity(computed, declared, declared)
        assert r.identity.value == IDENTITY_FAILED

    def test_real_sha_ir_stale(self) -> None:
        """IR 基于旧版本 source → IR SHA 不匹配 → VERIFIED + PENDING。"""
        content = b"current source"
        old_ir_content = b"old source before edit"
        sha = hashlib.sha256(content).hexdigest()
        old_ir_sha = hashlib.sha256(old_ir_content).hexdigest()
        r = verify_identity(sha, sha, old_ir_sha)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_PENDING
        assert r.semantic.reason == REASON_IR_MANIFEST_MISMATCH

    def test_real_sha_manifest_missing(self) -> None:
        sha = hashlib.sha256(b"content").hexdigest()
        r = verify_identity(sha, None, sha)
        assert r.identity.value == IDENTITY_FAILED
        assert REASON_MANIFEST_SHA_MISSING in r.identity.mismatches

    def test_m1_m2_m3_integration_simulation(self) -> None:
        """模拟 M1→M2→M3→M4 完整管线的数据流。"""
        raw_content = b"source file bytes"
        computed = hashlib.sha256(raw_content).hexdigest()
        manifest_declared = computed
        ir_embedded = computed
        r = verify_identity(computed, manifest_declared, ir_embedded)
        assert r.identity.value == IDENTITY_VERIFIED
        assert r.semantic is not None
        assert r.semantic.value == SEMANTIC_AVAILABLE
