"""Batch IR Locator 对抗性审查 (Phase 2.5 P3)。

从第一性原理审查 batch IR entry 的确定性定位规则。

核心不变量：
- path 仅用于定位，不参与 identity 判定
- source_content_sha256 是跨系统内容身份唯一权威
- locator 无法可靠解析时必须保持 fail-closed
- 任何 path normalization 都不能改变 source_content_sha256

攻击面：
A. path separator difference
B. absolute / relative difference
C. path mutation
D. same path + different content
E. same content + different path
F. ambiguous locator（多个 entry 同 SHA）
G. locator 完全无法解析
"""

import json
from pathlib import Path

import pytest

from app.core.identity_gate import GATE_BLOCK, GATE_PASS
from app.core.ir_identity import (
    IRIdentity,
    IRReadError,
    read_ir_identity,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def _write_batch_ir(tmp_path: Path, entries: list[dict]) -> Path:
    """写入 batch resolver IR JSON。"""
    ir_path = tmp_path / "resolver_ir.json"
    ir_data = {"ir_version": "resolver-ir-0.1", "files": entries}
    ir_path.write_text(json.dumps(ir_data, ensure_ascii=False), encoding="utf-8")
    return ir_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# A. path separator difference
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPathSeparatorDifference:
    """Windows \\ 与 POSIX / 分隔符差异。"""

    def test_backslash_vs_forward_slash_sha_match(self, tmp_path):
        """IR 用 \\，调用用 / → SHA 匹配仍成功。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "D:\\Project\\Papers\\doc.md",
             "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="D:/Project/Papers/doc.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 == SHA_A

    def test_forward_slash_vs_backslash_sha_match(self, tmp_path):
        """IR 用 /，调用用 \\ → SHA 匹配仍成功。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "D:/Project/Papers/doc.md",
             "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="D:\\Project\\Papers\\doc.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 == SHA_A


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B. absolute / relative difference
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAbsoluteRelativeDifference:
    """绝对路径 vs 相对路径差异。"""

    def test_absolute_ir_relative_caller_sha_match(self, tmp_path):
        """IR 用绝对路径，调用用相对路径 → SHA 匹配。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "D:\\Project\\Papers\\Ocr-markdown\\doc.md",
             "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="./doc.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 == SHA_A

    def test_relative_ir_absolute_caller_sha_match(self, tmp_path):
        """IR 用相对路径，调用用绝对路径 → SHA 匹配。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "doc.md",
             "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="D:\\Project\\Papers\\doc.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 == SHA_A


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C. path mutation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPathMutation:
    """路径被篡改但 SHA 不变 → SHA 匹配仍正确。"""

    def test_mutated_path_sha_still_matches(self, tmp_path):
        """IR path 被改为完全不同的路径 → SHA 匹配绕过 path。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "D:\\Evil\\fake\\path.md",
             "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="D:\\Project\\Papers\\real.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 == SHA_A

    def test_empty_path_sha_still_matches(self, tmp_path):
        """IR path 为空字符串 → SHA 匹配绕过。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "",
             "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="D:\\Project\\Papers\\real.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 == SHA_A


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# D. same path + different content
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestSamePathDifferentContent:
    """同 path 不同内容 → SHA 不匹配 → path fallback 找到 entry。"""

    def test_same_path_different_sha_returns_entry_sha(self, tmp_path):
        """IR entry path 匹配但 SHA 不同 → path fallback 找到 entry。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "D:\\Project\\Papers\\doc.md",
             "ir": {"source_sha256": SHA_B},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        # source_sha=SHA_A 不匹配任何 entry；path 匹配但 entry SHA 是 SHA_B
        result = read_ir_identity(
            ir, source_file="D:\\Project\\Papers\\doc.md", source_sha=SHA_A
        )
        # path fallback 找到 entry，返回 entry 声明的 SHA_B
        # M4 随后会发现 ir_sha(SHA_B) != manifest_sha(SHA_A) → PENDING
        assert result.source_content_sha256 == SHA_B


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# E. same content + different path
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestSameContentDifferentPath:
    """同内容不同路径 → SHA 匹配成功。"""

    def test_same_sha_different_path_matches(self, tmp_path):
        """IR entry 与 source 内容相同但路径完全不同 → SHA 匹配。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "D:\\Completely\\Different\\Location\\file.md",
             "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="E:\\Another\\Drive\\file.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 == SHA_A

    def test_same_sha_multiple_entries_only_one_matches(self, tmp_path):
        """多个 entry 中只有一个 SHA 匹配 → 精确命中。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "other1.md", "ir": {"source_sha256": SHA_B},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
            {"file": "target.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
            {"file": "other2.md", "ir": {"source_sha256": SHA_C},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(ir, source_file="whatever.md", source_sha=SHA_A)
        assert result.source_content_sha256 == SHA_A


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F. ambiguous locator
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAmbiguousLocator:
    """多个 entry 具有相同 SHA → SHA 匹配不唯一 → fail-closed。"""

    def test_duplicate_sha_entries_returns_none(self, tmp_path):
        """两个 entry 有相同 SHA → SHA 匹配不唯一 → fall through → None。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "file1.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
            {"file": "file2.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        # SHA 匹配到 2 个 → 不唯一 → fall through
        # path 也不匹配 → None
        result = read_ir_identity(
            ir, source_file="other.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 is None

    def test_duplicate_sha_with_matching_path_uses_path(self, tmp_path):
        """SHA 不唯一但 path 匹配 → path fallback 精确命中。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "file1.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
            {"file": "file2.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="file2.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 == SHA_A


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# G. locator 完全无法解析
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestLocatorUnresolvable:
    """SHA 和 path 都无法匹配 → None（fail-closed for semantic）。"""

    def test_no_sha_no_path_match_returns_none(self, tmp_path):
        ir = _write_batch_ir(tmp_path, [
            {"file": "other.md", "ir": {"source_sha256": SHA_B},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(
            ir, source_file="target.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 is None

    def test_empty_batch_returns_none(self, tmp_path):
        ir = _write_batch_ir(tmp_path, [])
        result = read_ir_identity(
            ir, source_file="target.md", source_sha=SHA_A
        )
        assert result.source_content_sha256 is None

    def test_no_parameters_positional_fallback(self, tmp_path):
        """无 source_file 无 source_sha → positional fallback（向后兼容）。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "file.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(ir)
        assert result.source_content_sha256 == SHA_A

    def test_sha_only_no_path(self, tmp_path):
        """仅提供 source_sha，不提供 source_file → SHA 匹配。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "file.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(ir, source_sha=SHA_A)
        assert result.source_content_sha256 == SHA_A

    def test_path_only_no_sha(self, tmp_path):
        """仅提供 source_file，不提供 source_sha → path 匹配（向后兼容）。"""
        ir = _write_batch_ir(tmp_path, [
            {"file": "file.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(ir, source_file="file.md")
        assert result.source_content_sha256 == SHA_A


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# H. Identity 正交性：locator 结果不改变 identity 判定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestLocatorIdentityOrthogonality:
    """locator 匹配结果只影响 semantic 轴，不影响 identity 轴。"""

    def test_locator_mismatch_does_not_affect_identity(self, tmp_path):
        """locator 找不到 → ir_sha=None → M4 仍正确判定 identity。"""
        from app.core.identity_verifier import verify_identity
        from app.core.identity_gate import evaluate_identity_gate

        ir = _write_batch_ir(tmp_path, [
            {"file": "other.md", "ir": {"source_sha256": SHA_B},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        ir_result = read_ir_identity(
            ir, source_file="target.md", source_sha=SHA_A
        )
        # locator 未命中 → ir_sha=None
        vr = verify_identity(
            computed_sha=SHA_A, manifest_sha=SHA_A,
            ir_sha=ir_result.source_content_sha256,
        )
        # identity 仍为 VERIFIED（computed == manifest）
        assert vr.identity.value == "VERIFIED"
        # semantic 为 PENDING（ir_sha=None）
        assert vr.semantic.value == "PENDING"
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_BLOCK  # VERIFIED + PENDING = BLOCK

    def test_locator_match_enables_available(self, tmp_path):
        """locator 命中 → ir_sha=SHA_A → M4 判定 AVAILABLE。"""
        from app.core.identity_verifier import verify_identity
        from app.core.identity_gate import evaluate_identity_gate

        ir = _write_batch_ir(tmp_path, [
            {"file": "different_path.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        ir_result = read_ir_identity(
            ir, source_file="target.md", source_sha=SHA_A
        )
        vr = verify_identity(
            computed_sha=SHA_A, manifest_sha=SHA_A,
            ir_sha=ir_result.source_content_sha256,
        )
        assert vr.identity.value == "VERIFIED"
        assert vr.semantic.value == "AVAILABLE"
        d = evaluate_identity_gate(vr)
        assert d.gate == GATE_PASS
