"""Consumer Boundary Closure — M1–M5 真实 V3 Consumer Boundary 验证。

验证目标：
1. M5 BLOCK → 下游 semantic consumption 完全不执行（Cases A–F）
2. Stale IR → VERIFIED + PENDING → BLOCK
3. Missing IR → VERIFIED + PENDING → BLOCK
4. Invalid Manifest → FAILED → BLOCK
5. Path attack: same bytes + different path = same identity
6. Path attack: different bytes + same path → BLOCK
7. Real pipeline: manifest → source → IR → M1–M5 → gate

所有测试基于 _verify_identity_boundary（runner_b2 中的完整 M1→M5 链）。
BLOCK 下游证明通过 mock/spy call counter 实现。
"""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.identity_gate import GATE_BLOCK, GATE_PASS, evaluate_identity_gate
from app.core.identity_verifier import verify_identity
from scripts.preprocessing_consumer.runner_b2 import (
    _run_full_chain,
    _verify_identity_boundary,
)

# ─── 常量 ───
SHA_A = hashlib.sha256(b"content A").hexdigest()
SHA_B = hashlib.sha256(b"content B").hexdigest()
SHA_C = hashlib.sha256(b"content C").hexdigest()


# ─── 构造辅助 ───

def _write_source(tmp_path: Path, content: bytes, name: str = "source.md") -> Path:
    p = tmp_path / name
    p.write_bytes(content)
    return p


def _write_manifest(tmp_path: Path, source_sha: str | None,
                    source_file: str | None = None,
                    identity_version: object = 2) -> Path:
    """写一个 manifest fixture。

    `identity_version` 默认 2（Frozen Contract v0.2 Interface Scope 字段口径）。
    本文件验证的是 M1–M5 **身份真实性**轴；F-INT-08 之后 Interface Scope
    （`identity_version == 2`）是与之 **AND** 的第二轴，故「合法 identity」的
    fixture 必须同时声明版本 2，否则会被集成边界正确拒绝——那属 F-INT-08 自身
    用例，见 `test_x26_fint08_interface_scope.py`。传 `None` 构造「未声明版本」输入。
    """
    m: dict = {"source_file": source_file or "", "units": []}
    if source_sha is not None:
        m["source_content_sha256"] = source_sha
    if identity_version is not None:
        m["identity_version"] = identity_version
    p = tmp_path / "test.manifest.json"
    p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    return p


def _write_ir(tmp_path: Path, ir_sha: str | None,
              source_file: str | None = None) -> Path:
    """写一个单文档 IR 文件。"""
    ir: dict = {}
    if ir_sha is not None:
        ir["source_content_sha256"] = ir_sha
    p = tmp_path / "test.ir.json"
    p.write_text(json.dumps(ir, ensure_ascii=False), encoding="utf-8")
    return p


def _write_batch_ir(tmp_path: Path, entries: list[dict]) -> Path:
    """写一个 batch resolver IR 文件。"""
    data = {"ir_version": "resolver-ir-0.1", "files": entries}
    p = tmp_path / "resolver_ir.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


# ═══════════════════════════════════════════════════════════════
# A. M5 BLOCK → 下游完全不执行（Cases A–F）
# ═══════════════════════════════════════════════════════════════

class TestBlockDownstreamNotExecuted:
    """M5 BLOCK 时，Compiler/Gate/Admission/Materialization 均不得被调用。"""

    def _run_with_block(self, gate_decision: dict) -> dict:
        """用 BLOCK gate_decision 运行 _run_full_chain。"""
        manifest = MagicMock()
        manifest.units = []
        source_lines = []
        source_path = Path("fake.md")

        import asyncio
        result = asyncio.run(
            _run_full_chain(
                MagicMock(), manifest, source_lines, source_path,
                gate_decision=gate_decision,
            )
        )
        return result

    def test_case_a_identity_failed_blocks_downstream(self):
        """Case A: Identity FAILED → BLOCK → 下游不执行。"""
        gate = {
            "gate": "BLOCK", "identity_state": "FAILED",
            "semantic_state": None, "reason": "identity_verification_failed",
            "mismatches": ("computed_manifest_mismatch",),
        }
        result = self._run_with_block(gate)

        assert result["status"] == "identity_blocked"
        assert result["downstream_executed"] is False
        assert result["identity_gate"]["gate"] == "BLOCK"

    def test_case_b_verified_pending_blocks_downstream(self):
        """Case B: VERIFIED + PENDING → BLOCK → 下游不执行。核心不变量。"""
        gate = {
            "gate": "BLOCK", "identity_state": "VERIFIED",
            "semantic_state": "PENDING", "reason": "semantic_pending",
            "mismatches": [],
        }
        result = self._run_with_block(gate)

        assert result["status"] == "identity_blocked"
        assert result["downstream_executed"] is False

    def test_case_c_manifest_mismatch_blocks_downstream(self):
        """Case C: Manifest SHA mismatch → BLOCK → 下游不执行。"""
        gate = {
            "gate": "BLOCK", "identity_state": "FAILED",
            "semantic_state": None, "reason": "identity_verification_failed",
            "mismatches": ("computed_manifest_mismatch",),
        }
        result = self._run_with_block(gate)

        assert result["status"] == "identity_blocked"
        assert result["downstream_executed"] is False

    def test_case_d_missing_ir_blocks_downstream(self):
        """Case D: IR missing → PENDING → BLOCK → 下游不执行。"""
        gate = {
            "gate": "BLOCK", "identity_state": "VERIFIED",
            "semantic_state": "PENDING", "reason": "semantic_pending",
            "mismatches": [],
        }
        result = self._run_with_block(gate)

        assert result["status"] == "identity_blocked"
        assert result["downstream_executed"] is False

    def test_case_e_stale_ir_blocks_downstream(self):
        """Case E: IR stale/mismatch → PENDING → BLOCK → 下游不执行。"""
        gate = {
            "gate": "BLOCK", "identity_state": "VERIFIED",
            "semantic_state": "PENDING", "reason": "semantic_pending",
            "mismatches": [],
        }
        result = self._run_with_block(gate)

        assert result["status"] == "identity_blocked"
        assert result["downstream_executed"] is False

    def test_case_f_malformed_ir_blocks_downstream(self):
        """Case F: IR malformed → BLOCK → 下游不执行。"""
        gate = {
            "gate": "BLOCK", "identity_state": "FAILED",
            "semantic_state": None, "reason": "ir_read_error: parse failed",
            "mismatches": ("ir_read_error",),
        }
        result = self._run_with_block(gate)

        assert result["status"] == "identity_blocked"
        assert result["downstream_executed"] is False

    def test_pass_allows_downstream(self):
        """VERIFIED + AVAILABLE → PASS → 允许下游执行（非 identity_blocked）。"""
        gate = {
            "gate": "PASS", "identity_state": "VERIFIED",
            "semantic_state": "AVAILABLE",
            "reason": "identity_verified_semantic_available",
            "mismatches": [],
        }
        manifest = MagicMock()
        manifest.units = []
        source_lines = []
        source_path = Path("fake.md")

        import asyncio
        result = asyncio.run(
            _run_full_chain(
                MagicMock(), manifest, source_lines, source_path,
                gate_decision=gate,
            )
        )
        assert result.get("status") != "identity_blocked"

    def test_blocked_result_has_no_semantic_fields(self):
        """BLOCK 结果不含 compiled_leaves / gate_results 等 semantic 字段。"""
        gate = {
            "gate": "BLOCK", "identity_state": "VERIFIED",
            "semantic_state": "PENDING", "reason": "semantic_pending",
            "mismatches": [],
        }
        result = self._run_with_block(gate)

        assert "compiled_leaves" not in result
        assert "gate_results" not in result
        assert "total_units" not in result


# ═══════════════════════════════════════════════════════════════
# B. 真实 pipeline: _verify_identity_boundary
# ═══════════════════════════════════════════════════════════════

class TestRealPipelineIdentityBoundary:
    """使用 _verify_identity_boundary 做真实 M1→M5 完整链验证。"""

    def test_all_match_pass(self, tmp_path):
        """computed == manifest == ir → PASS。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_A)
        ir = _write_ir(tmp_path, SHA_A)

        result = _verify_identity_boundary(manifest, source, ir)
        assert result["gate"] == GATE_PASS
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "AVAILABLE"

    def test_stale_ir_blocks(self, tmp_path):
        """Stale IR: ir_sha != manifest_sha → VERIFIED + PENDING → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_A)
        ir = _write_ir(tmp_path, SHA_B)

        result = _verify_identity_boundary(manifest, source, ir)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "PENDING"
        assert result["reason"] == "semantic_pending"

    def test_missing_ir_blocks(self, tmp_path):
        """IR missing → PENDING → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_A)

        result = _verify_identity_boundary(manifest, source, None)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "PENDING"
        assert result["reason"] == "semantic_pending"

    def test_manifest_sha_mismatch_blocks(self, tmp_path):
        """Manifest sha != computed sha → FAILED → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_B)

        result = _verify_identity_boundary(manifest, source, None)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "FAILED"
        assert "computed_manifest_mismatch" in result["mismatches"]

    def test_manifest_missing_sha_blocks(self, tmp_path):
        """Manifest 无 sha 字段 → FAILED → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, None)

        result = _verify_identity_boundary(manifest, source, None)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "FAILED"
        assert "manifest_sha_missing" in result["mismatches"]

    def test_source_not_found_blocks(self, tmp_path):
        """Source file 不存在 → BLOCK。"""
        manifest = _write_manifest(tmp_path, SHA_A)
        fake_source = tmp_path / "nonexistent.md"

        result = _verify_identity_boundary(manifest, fake_source, None)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "FAILED"

    def test_manifest_not_found_blocks(self, tmp_path):
        """Manifest file 不存在 → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        fake_manifest = tmp_path / "nonexistent.manifest.json"

        result = _verify_identity_boundary(fake_manifest, source, None)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "FAILED"

    def test_malformed_manifest_blocks(self, tmp_path):
        """Manifest JSON 解析失败 → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        manifest = tmp_path / "bad.manifest.json"
        manifest.write_text("not json {{{", encoding="utf-8")

        result = _verify_identity_boundary(manifest, source, None)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "FAILED"

    def test_batch_ir_with_matching_entry(self, tmp_path):
        """Batch resolver IR 中找到匹配条目 → 正确提取 sha → PASS。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_A)
        batch_ir = _write_batch_ir(tmp_path, [
            {"file": str(source), "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])

        result = _verify_identity_boundary(manifest, source, batch_ir)
        assert result["gate"] == GATE_PASS
        assert result["semantic_state"] == "AVAILABLE"

    def test_batch_ir_with_stale_entry(self, tmp_path):
        """Batch resolver IR 中条目 sha 不匹配 → PENDING → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_A)
        batch_ir = _write_batch_ir(tmp_path, [
            {"file": str(source), "ir": {"source_sha256": SHA_B},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])

        result = _verify_identity_boundary(manifest, source, batch_ir)
        assert result["gate"] == GATE_BLOCK
        assert result["semantic_state"] == "PENDING"

    def test_batch_ir_no_matching_entry(self, tmp_path):
        """Batch resolver IR 中无匹配条目（SHA 与 path 均不匹配）→ PENDING → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_A)
        batch_ir = _write_batch_ir(tmp_path, [
            {"file": "other_file.md", "ir": {"source_sha256": SHA_B},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])

        result = _verify_identity_boundary(manifest, source, batch_ir)
        assert result["gate"] == GATE_BLOCK
        assert result["semantic_state"] == "PENDING"

    def test_batch_ir_sha_match_different_path(self, tmp_path):
        """Phase 2.5: SHA 匹配到 entry 但 path 不同 → 仍能提取 ir_sha → PASS。

        验证 locator closure：source_sha 优先匹配 ir.source_sha256，
        不依赖 path 字符串一致性。
        """
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_A)
        batch_ir = _write_batch_ir(tmp_path, [
            {"file": "D:\\other\\absolute\\path\\file.md",
             "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])

        result = _verify_identity_boundary(manifest, source, batch_ir)
        assert result["gate"] == GATE_PASS
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "AVAILABLE"

    def test_batch_ir_rejected_entry_no_ir(self, tmp_path):
        """Batch IR 中 REJECTED 条目（ir=None）→ PENDING → BLOCK。"""
        source = _write_source(tmp_path, b"content A")
        manifest = _write_manifest(tmp_path, SHA_A)
        batch_ir = _write_batch_ir(tmp_path, [
            {"file": str(source), "ir": None,
             "disposition": "REJECTED_QC_FAIL", "qc_verdict": "FAIL"},
        ])

        result = _verify_identity_boundary(manifest, source, batch_ir)
        assert result["gate"] == GATE_BLOCK
        assert result["semantic_state"] == "PENDING"


# ═══════════════════════════════════════════════════════════════
# C. Path attack
# ═══════════════════════════════════════════════════════════════

class TestPathAttack:
    """path 是 locator，不是 identity。"""

    def test_same_bytes_different_path_same_identity(self, tmp_path):
        """same bytes + different path → identity VERIFIED（由 bytes 决定）。"""
        content = b"same content for both paths"
        sha = hashlib.sha256(content).hexdigest()

        source_a = _write_source(tmp_path, content, "file_a.md")
        source_b = tmp_path / "subdir" / "file_b.md"
        source_b.parent.mkdir()
        source_b.write_bytes(content)

        manifest = _write_manifest(tmp_path, sha)

        result_a = _verify_identity_boundary(manifest, source_a, None)
        result_b = _verify_identity_boundary(manifest, source_b, None)

        # IR missing → BLOCK，但 identity_state 应为 VERIFIED
        assert result_a["identity_state"] == "VERIFIED"
        assert result_b["identity_state"] == "VERIFIED"

    def test_same_bytes_different_path_with_ir_pass(self, tmp_path):
        """same bytes + different path + matching IR → PASS。"""
        content = b"same content for both paths"
        sha = hashlib.sha256(content).hexdigest()

        source_a = _write_source(tmp_path, content, "file_a.md")
        source_b = tmp_path / "other" / "file_b.md"
        source_b.parent.mkdir()
        source_b.write_bytes(content)

        manifest = _write_manifest(tmp_path, sha)
        ir = _write_ir(tmp_path, sha)

        result_a = _verify_identity_boundary(manifest, source_a, ir)
        result_b = _verify_identity_boundary(manifest, source_b, ir)

        assert result_a["gate"] == GATE_PASS
        assert result_b["gate"] == GATE_PASS

    def test_different_bytes_same_path_blocks(self, tmp_path):
        """different bytes + same path → raw SHA mismatch → BLOCK。"""
        source = _write_source(tmp_path, b"original content")
        original_sha = hashlib.sha256(b"original content").hexdigest()
        manifest = _write_manifest(tmp_path, original_sha)

        # 同一路径，内容被篡改
        source.write_bytes(b"TAMPERED content")

        result = _verify_identity_boundary(manifest, source, None)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "FAILED"
        assert "computed_manifest_mismatch" in result["mismatches"]

    def test_path_never_used_as_identity(self, tmp_path):
        """改 path 不改 bytes → identity 不变。"""
        content = b"stable content"
        sha = hashlib.sha256(content).hexdigest()

        source1 = _write_source(tmp_path, content, "original_name.md")
        manifest = _write_manifest(tmp_path, sha)
        ir = _write_ir(tmp_path, sha)

        result1 = _verify_identity_boundary(manifest, source1, ir)
        assert result1["gate"] == GATE_PASS

        # 重命名文件（path 变了，bytes 没变）
        source2 = tmp_path / "renamed_file.md"
        source1.rename(source2)

        result2 = _verify_identity_boundary(manifest, source2, ir)
        assert result2["gate"] == GATE_PASS
        assert result2["identity_state"] == "VERIFIED"


# ═══════════════════════════════════════════════════════════════
# D. M5 defensive — 非法输入不产生异常穿透
# ═══════════════════════════════════════════════════════════════

class TestM5DefensiveInput:
    """M5 对非法输入 fail-closed，不抛异常（Design v1.1 §4.6）。"""

    def test_none_input_blocks(self):
        d = evaluate_identity_gate(None)
        assert d.gate == GATE_BLOCK
        assert d.reason == "malformed_input"

    def test_missing_identity_attr_blocks(self):
        d = evaluate_identity_gate(object())
        assert d.gate == GATE_BLOCK
        assert d.reason == "malformed_input"

    def test_identity_is_none_blocks(self):
        class FakeVR:
            identity = None
            semantic = None
        d = evaluate_identity_gate(FakeVR())
        assert d.gate == GATE_BLOCK
        assert d.reason == "malformed_input"

    def test_identity_value_not_str_blocks(self):
        class FakeIdentity:
            value = 12345
            mismatches = ()
        class FakeVR:
            identity = FakeIdentity()
            semantic = None
        d = evaluate_identity_gate(FakeVR())
        assert d.gate == GATE_BLOCK
        assert d.reason == "malformed_input"

    def test_semantic_value_not_str_blocks(self):
        class FakeVR:
            identity = type("I", (), {"value": "VERIFIED", "mismatches": ()})()
            semantic = type("S", (), {"value": [1, 2], "reason": None})()
        d = evaluate_identity_gate(FakeVR())
        assert d.gate == GATE_BLOCK
        assert d.reason == "invalid_state"

    def test_semantic_value_outside_whitelist_blocks(self):
        class FakeVR:
            identity = type("I", (), {"value": "VERIFIED", "mismatches": ()})()
            semantic = type("S", (), {"value": "HACKED", "reason": None})()
        d = evaluate_identity_gate(FakeVR())
        assert d.gate == GATE_BLOCK
        assert d.reason == "invalid_state"

    def test_identity_value_outside_whitelist_blocks(self):
        class FakeVR:
            identity = type("I", (), {"value": "HACKED", "mismatches": ()})()
            semantic = type("S", (), {"value": "AVAILABLE", "reason": None})()
        d = evaluate_identity_gate(FakeVR())
        assert d.gate == GATE_BLOCK
        assert d.reason == "invalid_state"

    def test_mismatches_wrong_type_does_not_crash(self):
        class FakeVR:
            identity = type("I", (), {"value": "FAILED", "mismatches": "not_a_list"})()
            semantic = None
        d = evaluate_identity_gate(FakeVR())
        assert d.gate == GATE_BLOCK
        assert d.identity_state == "FAILED"


# ═══════════════════════════════════════════════════════════════
# E. M3 batch IR 格式
# ═══════════════════════════════════════════════════════════════

class TestM3BatchIRFormat:
    """M3 支持 batch resolver IR 和单文档 IR 两种格式。"""

    def test_single_doc_format(self, tmp_path):
        from app.core.ir_identity import read_ir_identity
        p = _write_ir(tmp_path, SHA_A)
        result = read_ir_identity(p)
        assert result.source_content_sha256 == SHA_A

    def test_single_doc_source_sha256_field(self, tmp_path):
        from app.core.ir_identity import read_ir_identity
        p = tmp_path / "ir.json"
        p.write_text(json.dumps({"source_sha256": SHA_A}), encoding="utf-8")
        result = read_ir_identity(p)
        assert result.source_content_sha256 == SHA_A

    def test_batch_format(self, tmp_path):
        from app.core.ir_identity import read_ir_identity
        batch = _write_batch_ir(tmp_path, [
            {"file": "test.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(batch, source_file="test.md")
        assert result.source_content_sha256 == SHA_A

    def test_batch_format_no_match(self, tmp_path):
        from app.core.ir_identity import read_ir_identity
        batch = _write_batch_ir(tmp_path, [
            {"file": "other.md", "ir": {"source_sha256": SHA_A},
             "disposition": "ADMITTED", "qc_verdict": "PASS"},
        ])
        result = read_ir_identity(batch, source_file="test.md")
        assert result.source_content_sha256 is None

    def test_batch_format_null_ir(self, tmp_path):
        from app.core.ir_identity import read_ir_identity
        batch = _write_batch_ir(tmp_path, [
            {"file": "test.md", "ir": None,
             "disposition": "REJECTED_QC_FAIL", "qc_verdict": "FAIL"},
        ])
        result = read_ir_identity(batch, source_file="test.md")
        assert result.source_content_sha256 is None

    def test_ir_missing_returns_none(self, tmp_path):
        from app.core.ir_identity import read_ir_identity
        result = read_ir_identity(tmp_path / "nope.json")
        assert result.source_content_sha256 is None

    def test_malformed_json_raises(self, tmp_path):
        from app.core.ir_identity import IRReadError, read_ir_identity
        p = tmp_path / "bad.json"
        p.write_text("not json {{{", encoding="utf-8")
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_invalid_sha_raises(self, tmp_path):
        from app.core.ir_identity import IRReadError, read_ir_identity
        p = _write_ir(tmp_path, "not_a_valid_sha")
        with pytest.raises(IRReadError):
            read_ir_identity(p)


# ═══════════════════════════════════════════════════════════════
# F. Producer IR 不被绕过
# ═══════════════════════════════════════════════════════════════

class TestProducerIRNotBypassed:
    """V3 Consumer 必须使用 Producer IR，不重新生成独立语义 IR。"""

    def test_identity_source_is_raw_bytes_not_ir(self, tmp_path):
        """身份来源 = raw bytes SHA256，非 IR sha。IR 只影响 semantic state。"""
        source = _write_source(tmp_path, b"real content")
        real_sha = hashlib.sha256(b"real content").hexdigest()

        manifest = _write_manifest(tmp_path, real_sha)
        # 合法 hex 但与 manifest sha 不同 → stale IR
        ir = _write_ir(tmp_path, "f" * 64)

        result = _verify_identity_boundary(manifest, source, ir)
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "PENDING"
        assert result["gate"] == GATE_BLOCK

    def test_ir_cannot_override_identity_failure(self, tmp_path):
        """即使 IR sha 匹配 manifest，如果 raw bytes 不匹配 → FAILED。"""
        source = _write_source(tmp_path, b"tampered content")
        claimed_sha = hashlib.sha256(b"original content").hexdigest()

        manifest = _write_manifest(tmp_path, claimed_sha)
        ir = _write_ir(tmp_path, claimed_sha)

        result = _verify_identity_boundary(manifest, source, ir)
        assert result["identity_state"] == "FAILED"
        assert result["gate"] == GATE_BLOCK


# ═══════════════════════════════════════════════════════════════
# G. Spy 验证 — BLOCK 时下游组件零调用（HIGH-1 修复）
# ═══════════════════════════════════════════════════════════════

class TestBlockDownstreamSpyProof:
    """用 spy/call counter 硬证明 BLOCK 时 IRBuilder/Compiler/evaluate/build_payload 零调用。"""

    def _run_with_spy(self, gate_decision: dict):
        """运行 _run_full_chain 并返回 spy 计数。"""
        manifest = MagicMock()
        manifest.units = []
        source_lines = []

        import asyncio
        with patch("scripts.preprocessing_consumer.runner_b2.IRBuilder") as mock_ir, \
             patch("scripts.preprocessing_consumer.runner_b2.Compiler") as mock_compiler, \
             patch("scripts.preprocessing_consumer.runner_b2.evaluate") as mock_evaluate, \
             patch("scripts.preprocessing_consumer.runner_b2.build_payload") as mock_payload:

            result = asyncio.run(
                _run_full_chain(
                    MagicMock(), manifest, source_lines, Path("fake.md"),
                    gate_decision=gate_decision,
                )
            )
            return result, mock_ir, mock_compiler, mock_evaluate, mock_payload

    def test_block_spy_zero_calls_identity_failed(self):
        """Identity FAILED → BLOCK → IRBuilder/Compiler/evaluate/build_payload call_count=0。"""
        gate = {"gate": "BLOCK", "identity_state": "FAILED",
                "semantic_state": None, "reason": "identity_verification_failed",
                "mismatches": ("computed_manifest_mismatch",)}
        result, ir, comp, ev, bp = self._run_with_spy(gate)
        assert result["status"] == "identity_blocked"
        assert ir.call_count == 0
        assert comp.call_count == 0
        assert ev.call_count == 0
        assert bp.call_count == 0

    def test_block_spy_zero_calls_verified_pending(self):
        """VERIFIED + PENDING → BLOCK → spy call_count=0。核心不变量。"""
        gate = {"gate": "BLOCK", "identity_state": "VERIFIED",
                "semantic_state": "PENDING", "reason": "semantic_pending",
                "mismatches": []}
        result, ir, comp, ev, bp = self._run_with_spy(gate)
        assert result["status"] == "identity_blocked"
        assert ir.call_count == 0
        assert comp.call_count == 0
        assert ev.call_count == 0
        assert bp.call_count == 0

    def test_block_spy_zero_calls_manifest_mismatch(self):
        """Manifest SHA mismatch → BLOCK → spy call_count=0。"""
        gate = {"gate": "BLOCK", "identity_state": "FAILED",
                "semantic_state": None, "reason": "identity_verification_failed",
                "mismatches": ("computed_manifest_mismatch",)}
        result, ir, comp, ev, bp = self._run_with_spy(gate)
        assert ir.call_count == 0
        assert comp.call_count == 0

    def test_block_spy_create_source_records_not_called(self):
        """BLOCK 时 _create_source_records 也不应被调用（session 操作完全跳过）。"""
        gate = {"gate": "BLOCK", "identity_state": "VERIFIED",
                "semantic_state": "PENDING", "reason": "semantic_pending",
                "mismatches": []}
        manifest = MagicMock()
        manifest.units = []
        import asyncio
        with patch("scripts.preprocessing_consumer.runner_b2._create_source_records") as mock_create:
            result = asyncio.run(
                _run_full_chain(
                    MagicMock(), manifest, [], Path("fake.md"),
                    gate_decision=gate,
                )
            )
            assert result["status"] == "identity_blocked"
            assert mock_create.call_count == 0


# ═══════════════════════════════════════════════════════════════
# H. IR error 正交性 — IR 读取失败不影响 Identity 判定（HIGH-3 修复）
# ═══════════════════════════════════════════════════════════════

class TestIRErrorOrthogonality:
    """IR 读取失败时，Identity 判定仍由 M4 完成（正交性原则）。"""

    def test_ir_error_identity_still_verified(self, tmp_path):
        """computed==manifest + malformed IR → identity=VERIFIED, semantic=PENDING, BLOCK。"""
        content = b"correct content"
        sha = hashlib.sha256(content).hexdigest()
        source = _write_source(tmp_path, content)
        manifest = _write_manifest(tmp_path, sha)
        bad_ir = tmp_path / "bad.ir.json"
        bad_ir.write_text("not json {{{", encoding="utf-8")

        result = _verify_identity_boundary(manifest, source, bad_ir)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "VERIFIED"  # NOT FAILED
        assert result["semantic_state"] == "PENDING"
        assert "ir_error" in result  # IR error recorded separately

    def test_ir_error_does_not_mask_identity_failure(self, tmp_path):
        """computed!=manifest + malformed IR → identity=FAILED with correct reason。"""
        content = b"actual content"
        wrong_sha = hashlib.sha256(b"claimed content").hexdigest()
        source = _write_source(tmp_path, content)
        manifest = _write_manifest(tmp_path, wrong_sha)
        bad_ir = tmp_path / "bad.ir.json"
        bad_ir.write_text("not json {{{", encoding="utf-8")

        result = _verify_identity_boundary(manifest, source, bad_ir)
        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "FAILED"
        assert "computed_manifest_mismatch" in result["mismatches"]
        assert "ir_error" in result  # IR error still recorded

    def test_ir_error_recorded_in_result(self, tmp_path):
        """IR error 信息作为独立字段记录，不混入 mismatches。"""
        content = b"data"
        sha = hashlib.sha256(content).hexdigest()
        source = _write_source(tmp_path, content)
        manifest = _write_manifest(tmp_path, sha)
        bad_ir = tmp_path / "bad.ir.json"
        bad_ir.write_text("not json {{{", encoding="utf-8")

        result = _verify_identity_boundary(manifest, source, bad_ir)
        assert "ir_error" in result
        assert isinstance(result["ir_error"], str)
        # mismatches 不含 ir_read_error（已由 M4 正确生成）
        assert "ir_read_error" not in result["mismatches"]


# ═══════════════════════════════════════════════════════════════
# I. gate_decision 必填 — 绕过防护（HIGH-2 修复）
# ═══════════════════════════════════════════════════════════════

class TestGateDecisionRequired:
    """gate_decision 是必填参数，调用方无法绕过 identity 验证。"""

    def test_gate_decision_is_required_parameter(self):
        """_run_full_chain 签名中 gate_decision 无默认值。"""
        import inspect
        sig = inspect.signature(_run_full_chain)
        param = sig.parameters["gate_decision"]
        assert param.default is inspect.Parameter.empty, (
            "gate_decision 必须是必填参数，不能有默认值"
        )

    def test_missing_gate_decision_raises_type_error(self):
        """不传 gate_decision → TypeError。"""
        import asyncio
        manifest = MagicMock()
        manifest.units = []
        with pytest.raises(TypeError):
            asyncio.run(
                _run_full_chain(
                    MagicMock(), manifest, [], Path("fake.md"),
                )
            )
