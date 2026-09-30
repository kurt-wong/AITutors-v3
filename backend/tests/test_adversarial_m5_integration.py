"""M5 Consumer Gate — 集成级攻击测试。

覆盖 M5 fail-closed implementation invariant 的攻击面：
1. Manifest 攻击（6 种）
2. IR 攻击（6 种）
3. 双轴组合穷举
4. Stale IR 攻击
5. Missing IR 攻击
6. Path 攻击
7. 绕过 M5 攻击（mock/spy 证明 semantic consumer 不被调用）
8. Identity VERIFIED ≠ 整体成功
"""
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.identity_gate import (
    GATE_BLOCK,
    GATE_PASS,
    evaluate_identity_gate,
)
from app.core.identity_verifier import verify_identity
from app.core.ir_identity import IRReadError, read_ir_identity
from app.core.manifest_identity import ManifestReadError, read_manifest_identity
from app.core.raw_bytes_identity import load_raw_bytes_identity


SHA_A = "a" * 64
SHA_B = "b" * 64


def _real_sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _write_manifest(tmp_path: Path, sha_value) -> Path:
    """写入 manifest JSON。sha_value 可以是 str / None / 缺失。"""
    manifest_path = tmp_path / "manifest.json"
    data = {}
    if sha_value is not None:
        data["source_content_sha256"] = sha_value
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    return manifest_path


def _write_ir(tmp_path: Path, sha_value) -> Path:
    """写入 IR JSON。sha_value 可以是 str / None / 缺失。"""
    ir_path = tmp_path / "ir.json"
    data = {}
    if sha_value is not None:
        data["source_content_sha256"] = sha_value
    ir_path.write_text(json.dumps(data), encoding="utf-8")
    return ir_path


def _write_source(tmp_path: Path, content: bytes) -> Path:
    source_path = tmp_path / "source.md"
    source_path.write_bytes(content)
    return source_path


def _run_full_chain(source_path: Path, manifest_path: Path, ir_path: Path | None):
    """模拟完整链路：M2 → M1 → M3 → M4 → M5。"""
    raw = load_raw_bytes_identity(source_path)
    manifest = read_manifest_identity(manifest_path)
    ir_sha = None
    if ir_path is not None and ir_path.exists():
        ir = read_ir_identity(ir_path)
        ir_sha = ir.source_content_sha256
    vr = verify_identity(raw.sha256, manifest.source_content_sha256, ir_sha)
    decision = evaluate_identity_gate(vr)
    return vr, decision


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Manifest 攻击
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestManifestAttacks:
    """Manifest 层的 6 种攻击场景。"""

    def test_manifest_sha_correct_pass(self, tmp_path):
        content = b"Hello World"
        source = _write_source(tmp_path, content)
        manifest = _write_manifest(tmp_path, _real_sha(content))
        ir = _write_ir(tmp_path, _real_sha(content))
        _, decision = _run_full_chain(source, manifest, ir)
        assert decision.gate == GATE_PASS

    def test_manifest_missing_raises(self, tmp_path):
        """Manifest 文件不存在 → ManifestReadError。"""
        with pytest.raises(ManifestReadError):
            read_manifest_identity(tmp_path / "nonexistent.json")

    def test_manifest_sha_null_block(self, tmp_path):
        """Manifest sha = null → M4 FAILED → M5 BLOCK。"""
        content = b"Hello"
        vr = verify_identity(_real_sha(content), None, None)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "FAILED"
        assert decision.semantic_state is None

    def test_manifest_sha_empty_string_block(self, tmp_path):
        """Manifest sha = "" → M1 转为 None → M4 FAILED → M5 BLOCK。"""
        content = b"Hello"
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps({"source_content_sha256": ""}), encoding="utf-8")
        manifest = read_manifest_identity(manifest_path)
        assert manifest.source_content_sha256 is None
        vr = verify_identity(_real_sha(content), manifest.source_content_sha256, None)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK

    def test_manifest_sha_invalid_raises(self, tmp_path):
        """Manifest sha 非 64-char hex → ManifestReadError。"""
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(
            json.dumps({"source_content_sha256": "not-a-valid-sha"}), encoding="utf-8"
        )
        with pytest.raises(ManifestReadError):
            read_manifest_identity(manifest_path)

    def test_manifest_sha_mismatch_block(self, tmp_path):
        """Manifest sha ≠ raw bytes sha → FAILED → BLOCK。"""
        content = b"Actual Content"
        vr = verify_identity(_real_sha(content), SHA_B, None)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "FAILED"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. IR 攻击
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestIRAttacks:
    """IR 层的 6 种攻击场景。"""

    def test_ir_missing_block(self):
        """IR 缺失 → VERIFIED + PENDING → BLOCK。"""
        vr = verify_identity(SHA_A, SHA_A, None)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "VERIFIED"
        assert decision.semantic_state == "PENDING"

    def test_ir_consistent_pass(self):
        """IR sha 与 Manifest 一致 → VERIFIED + AVAILABLE → PASS。"""
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_PASS

    def test_ir_inconsistent_block(self):
        """IR sha 与 Manifest 不一致 → VERIFIED + PENDING → BLOCK。"""
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK
        assert decision.semantic_state == "PENDING"

    def test_ir_identity_missing_block(self, tmp_path):
        """IR 文件存在但无 source_content_sha256 字段 → None → PENDING → BLOCK。"""
        ir_path = tmp_path / "ir.json"
        ir_path.write_text(json.dumps({"other_field": "value"}), encoding="utf-8")
        ir = read_ir_identity(ir_path)
        assert ir.source_content_sha256 is None
        vr = verify_identity(SHA_A, SHA_A, ir.source_content_sha256)
        decision = evaluate_identity_gate(vr)
        assert decision.gate == GATE_BLOCK

    def test_ir_malformed_raises(self, tmp_path):
        """IR 文件存在但 JSON 解析失败 → IRReadError。"""
        ir_path = tmp_path / "ir.json"
        ir_path.write_text("not valid json {{{", encoding="utf-8")
        with pytest.raises(IRReadError):
            read_ir_identity(ir_path)

    def test_ir_wrong_type_raises(self, tmp_path):
        """IR sha 字段为错误类型（int）→ IRReadError。"""
        ir_path = tmp_path / "ir.json"
        ir_path.write_text(json.dumps({"source_content_sha256": 12345}), encoding="utf-8")
        with pytest.raises(IRReadError):
            read_ir_identity(ir_path)

    def test_ir_sha_uppercase_raises(self, tmp_path):
        """IR sha 为大写 hex → IRReadError。"""
        ir_path = tmp_path / "ir.json"
        ir_path.write_text(
            json.dumps({"source_content_sha256": SHA_A.upper()}), encoding="utf-8"
        )
        with pytest.raises(IRReadError):
            read_ir_identity(ir_path)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 双轴组合穷举
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestDualAxisCombinations:
    """穷举 4 种合法组合 + 证明 semantic 不能反向改变 identity。"""

    def test_verified_available(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        d = evaluate_identity_gate(vr)
        assert (d.identity_state, d.semantic_state, d.gate) == ("VERIFIED", "AVAILABLE", GATE_PASS)

    def test_verified_pending_mismatch(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert (d.identity_state, d.semantic_state, d.gate) == ("VERIFIED", "PENDING", GATE_BLOCK)

    def test_verified_pending_absent(self):
        vr = verify_identity(SHA_A, SHA_A, None)
        d = evaluate_identity_gate(vr)
        assert (d.identity_state, d.semantic_state, d.gate) == ("VERIFIED", "PENDING", GATE_BLOCK)

    def test_failed_none(self):
        vr = verify_identity(SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert (d.identity_state, d.semantic_state, d.gate) == ("FAILED", None, GATE_BLOCK)

    def test_failed_manifest_none(self):
        vr = verify_identity(SHA_A, None)
        d = evaluate_identity_gate(vr)
        assert (d.identity_state, d.semantic_state, d.gate) == ("FAILED", None, GATE_BLOCK)

    def test_semantic_cannot_reverse_identity(self):
        """Semantic 状态永远不能反向改变 Identity。"""
        for ir_val in [SHA_A, SHA_B, None]:
            vr = verify_identity(SHA_A, SHA_A, ir_val)
            assert vr.identity.value == "VERIFIED", f"IR={ir_val!r} changed identity!"

        for ir_val in [SHA_A, SHA_B, None]:
            vr = verify_identity(SHA_A, SHA_B, ir_val)
            d = evaluate_identity_gate(vr)
            assert d.identity_state == "FAILED"
            assert d.gate == GATE_BLOCK


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Stale IR 攻击
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestStaleIRAttack:
    """Stale IR：raw bytes = A, manifest = SHA(A), IR = source identity B。"""

    def test_stale_ir_full_chain(self, tmp_path):
        content_v2 = b"Updated content v2"
        sha_v2 = _real_sha(content_v2)
        source = _write_source(tmp_path, content_v2)
        manifest = _write_manifest(tmp_path, sha_v2)
        ir = _write_ir(tmp_path, SHA_B)  # stale IR

        vr, decision = _run_full_chain(source, manifest, ir)

        assert vr.identity.value == "VERIFIED"
        assert vr.semantic.value == "PENDING"
        assert vr.semantic.reason == "ir_manifest_mismatch"
        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "VERIFIED"
        assert decision.semantic_state == "PENDING"

    def test_stale_ir_does_not_enter_semantic_consumption(self, tmp_path):
        """Stale IR 时 M5 BLOCK，semantic consumer 不被调用。"""
        mock_semantic_consumer = MagicMock()
        content = b"Current content"
        sha = _real_sha(content)
        vr = verify_identity(sha, sha, SHA_B)  # stale IR
        decision = evaluate_identity_gate(vr)

        if decision.gate == GATE_PASS:
            mock_semantic_consumer(vr)

        mock_semantic_consumer.assert_not_called()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Missing IR 攻击
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestMissingIRAttack:
    """Missing IR：raw bytes = A, manifest = SHA(A), IR = missing。"""

    def test_missing_ir_full_chain(self, tmp_path):
        content = b"Content without IR"
        sha = _real_sha(content)
        vr = verify_identity(sha, sha, None)
        decision = evaluate_identity_gate(vr)

        assert vr.identity.value == "VERIFIED"
        assert vr.semantic.value == "PENDING"
        assert vr.semantic.reason == "ir_absent"
        assert decision.gate == GATE_BLOCK

    def test_missing_ir_cannot_continue_because_identity_verified(self):
        """不能因为 Identity VERIFIED 就继续。"""
        mock_admission = MagicMock()
        vr = verify_identity(SHA_A, SHA_A, None)
        decision = evaluate_identity_gate(vr)

        if decision.gate == GATE_PASS:
            mock_admission(vr)

        mock_admission.assert_not_called()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Path 攻击
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPathAttack:
    """Path 非身份原则的运行时验证。"""

    def test_same_bytes_different_path_same_identity(self, tmp_path):
        """same bytes + different path → 同一 identity。"""
        content = b"Shared content"
        sha = _real_sha(content)

        path_a = tmp_path / "file_a.md"
        path_a.write_bytes(content)
        path_b = tmp_path / "subdir" / "file_b.md"
        path_b.parent.mkdir()
        path_b.write_bytes(content)

        raw_a = load_raw_bytes_identity(path_a)
        raw_b = load_raw_bytes_identity(path_b)

        assert raw_a.sha256 == raw_b.sha256, "Same bytes must produce same SHA"
        assert raw_a.sha256 == sha

    def test_different_bytes_same_path_unchanged_name_failed(self, tmp_path):
        """different bytes + path/name unchanged → SHA mismatch → FAILED。"""
        content_v1 = b"Original content"
        sha_v1 = _real_sha(content_v1)

        source = tmp_path / "source.md"
        source.write_bytes(content_v1)
        manifest = _write_manifest(tmp_path, sha_v1)

        # 文件被替换成不同内容（path 不变）
        source.write_bytes(b"Tampered content!")

        raw = load_raw_bytes_identity(source)
        vr = verify_identity(raw.sha256, sha_v1, None)
        decision = evaluate_identity_gate(vr)

        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "FAILED"
        assert "computed_manifest_mismatch" in decision.mismatches

    def test_path_swap_attack_full_chain(self, tmp_path):
        """Path swap：manifest 指向的文件被替换成不同内容。"""
        original = b"Legitimate content"
        tampered = b"Malicious replacement"
        sha_original = _real_sha(original)

        source = tmp_path / "source.md"
        source.write_bytes(original)
        manifest = _write_manifest(tmp_path, sha_original)
        ir = _write_ir(tmp_path, sha_original)

        # 攻击者替换文件内容
        source.write_bytes(tampered)

        raw = load_raw_bytes_identity(source)
        manifest_data = read_manifest_identity(manifest)
        ir_data = read_ir_identity(ir)

        vr = verify_identity(
            raw.sha256, manifest_data.source_content_sha256, ir_data.source_content_sha256
        )
        decision = evaluate_identity_gate(vr)

        assert decision.gate == GATE_BLOCK
        assert decision.identity_state == "FAILED"
        assert vr.semantic is None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 绕过 M5 攻击
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestBypassM5Attack:
    """证明 M5 是不可绕过的 Semantic Consumption Boundary。"""

    def test_semantic_consumer_not_called_when_pending(self):
        """VERIFIED + PENDING 时 semantic consumer 的 call count = 0。"""
        call_count = 0

        def mock_semantic_consumer(vr):
            nonlocal call_count
            call_count += 1

        vr = verify_identity(SHA_A, SHA_A, SHA_B)  # VERIFIED + PENDING
        decision = evaluate_identity_gate(vr)

        if decision.gate == GATE_PASS:
            mock_semantic_consumer(vr)

        assert call_count == 0, "Semantic consumer must NOT be called when PENDING"

    def test_semantic_consumer_not_called_when_failed(self):
        """FAILED 时 semantic consumer 的 call count = 0。"""
        call_count = 0

        def mock_semantic_consumer(vr):
            nonlocal call_count
            call_count += 1

        vr = verify_identity(SHA_A, SHA_B)  # FAILED
        decision = evaluate_identity_gate(vr)

        if decision.gate == GATE_PASS:
            mock_semantic_consumer(vr)

        assert call_count == 0

    def test_semantic_consumer_called_only_when_available(self):
        """只有 AVAILABLE 时 semantic consumer 被调用一次。"""
        call_count = 0

        def mock_semantic_consumer(vr):
            nonlocal call_count
            call_count += 1

        vr = verify_identity(SHA_A, SHA_A, SHA_A)  # VERIFIED + AVAILABLE
        decision = evaluate_identity_gate(vr)

        if decision.gate == GATE_PASS:
            mock_semantic_consumer(vr)

        assert call_count == 1

    def test_gate_boundary_is_binary(self):
        """M5 输出只有 PASS / BLOCK 两态，没有中间态。"""
        import itertools
        shas = [SHA_A, SHA_B, None]
        for computed, manifest, ir in itertools.product([SHA_A, SHA_B], shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            assert d.gate in (GATE_PASS, GATE_BLOCK)

    def test_only_bypass_is_reaching_m5_pass(self):
        """M5 是唯一的放行边界——如果 gate=PASS，说明 VERIFIED+AVAILABLE。"""
        import itertools
        shas = [SHA_A, SHA_B, None]
        for computed, manifest, ir in itertools.product([SHA_A, SHA_B], shas, shas):
            vr = verify_identity(computed, manifest, ir)
            d = evaluate_identity_gate(vr)
            if d.gate == GATE_PASS:
                assert d.identity_state == "VERIFIED"
                assert d.semantic_state == "AVAILABLE"

    def test_mock_pipeline_proves_no_bypass(self):
        """Mock 完整 pipeline，证明 M5 在 M4 和 semantic consumer 之间。"""
        pipeline_log = []

        def mock_m4(computed, manifest, ir):
            pipeline_log.append("m4")
            return verify_identity(computed, manifest, ir)

        def mock_m5(vr):
            pipeline_log.append("m5")
            return evaluate_identity_gate(vr)

        def mock_semantic_consumer(decision):
            pipeline_log.append("semantic_consumer")
            return "consumed"

        # VERIFIED + PENDING
        vr = mock_m4(SHA_A, SHA_A, SHA_B)
        decision = mock_m5(vr)
        if decision.gate == GATE_PASS:
            mock_semantic_consumer(decision)

        assert pipeline_log == ["m4", "m5"], (
            f"Pipeline must stop at M5 when BLOCK, got: {pipeline_log}"
        )

    def test_mock_pipeline_pass_when_available(self):
        """VERIFIED + AVAILABLE 时 pipeline 完整走完。"""
        pipeline_log = []

        def mock_m4(computed, manifest, ir):
            pipeline_log.append("m4")
            return verify_identity(computed, manifest, ir)

        def mock_m5(vr):
            pipeline_log.append("m5")
            return evaluate_identity_gate(vr)

        def mock_semantic_consumer(decision):
            pipeline_log.append("semantic_consumer")
            return "consumed"

        vr = mock_m4(SHA_A, SHA_A, SHA_A)
        decision = mock_m5(vr)
        if decision.gate == GATE_PASS:
            mock_semantic_consumer(decision)

        assert pipeline_log == ["m4", "m5", "semantic_consumer"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. Identity VERIFIED ≠ 整体成功
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestIdentityVerifiedNotOverallSuccess:
    """VERIFIED + PENDING 最多只能表示身份确认，不得报告整体成功。"""

    def test_verified_pending_is_not_overall_success(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_B)
        d = evaluate_identity_gate(vr)
        assert d.identity_state == "VERIFIED"
        assert d.gate == GATE_BLOCK
        assert d.reason == "semantic_pending"

    def test_verified_available_is_overall_success(self):
        vr = verify_identity(SHA_A, SHA_A, SHA_A)
        d = evaluate_identity_gate(vr)
        assert d.identity_state == "VERIFIED"
        assert d.gate == GATE_PASS
        assert d.reason == "identity_verified_semantic_available"

    def test_verified_pending_reports_distinct_states(self):
        """VERIFIED + PENDING 必须清楚区分 identity 和 semantic。"""
        vr = verify_identity(SHA_A, SHA_A, None)
        d = evaluate_identity_gate(vr)
        assert d.identity_state == "VERIFIED"
        assert d.semantic_state == "PENDING"
        assert d.gate == GATE_BLOCK
        assert d.reason == "semantic_pending"
        assert d.reason != "identity_verification_failed"
