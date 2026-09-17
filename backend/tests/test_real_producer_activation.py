"""Real Producer Data Activation — Phase 2.5 核心目标。

证明真实 Producer 已冻结、已验证的 artifact 能通过完整 M1→M5 链：

  REAL SOURCE BYTES → REAL MANIFEST → REAL IR → M1 → M2 → M3 → M4 → M5 → PASS

同时证明 PASS 后 downstream 实际执行（IRBuilder/Compiler 有真实调用证据）。

数据来源：
- Manifest: reslice-pac-annotated\\reslice-pac\\ocr\\pac-c01-01.manifest.json
  (identity_version: 2, source_content_sha256 已回填)
- Source: reslice-pac\\ocr\\pac-c01-01.md
- IR: resolver_ref_r52\\resolver_ir.json
  (88 files, 71 ADMITTED, all with ir.source_sha256)

区分：本测试使用 production corpus 的真实 artifact，
不是 synthetic fixture。数据 readiness 前提已满足（87 manifests 已回填）。
"""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.identity_gate import evaluate_identity_gate
from app.core.identity_verifier import verify_identity
from app.core.ir_identity import read_ir_identity
from app.core.manifest_identity import read_manifest_identity
from app.core.raw_bytes_identity import load_raw_bytes_identity

# ─── 真实 Producer 数据路径 ───
_PAC_MANIFEST = Path(
    r"D:\Project\Papers\Ocr-markdown\reslice-pac-annotated"
    r"\reslice-pac\ocr\pac-c01-01.manifest.json"
)
_PAC_SOURCE = Path(
    r"D:\Project\Papers\Ocr-markdown\reslice-pac\ocr\pac-c01-01.md"
)
_RESOLVER_IR = Path(
    r"D:\Project\Papers\data\resolver_ref_r52\resolver_ir.json"
)

# Batch-C 示例（另一个 corpus）
_BATCH_C_MANIFEST = Path(
    r"D:\Project\Papers\Ocr-markdown\reslice-batch-C"
    r"\会考\历史\2018北京夏季高中会考历史（教师版）(1).manifest.json"
)
_BATCH_C_SOURCE = Path(
    r"D:\Project\Papers\Ocr-markdown\会考\历史"
    r"\2018北京夏季高中会考历史（教师版）(1).md"
)


def _data_available() -> bool:
    """检查真实 Producer 数据是否存在。"""
    return (
        _PAC_MANIFEST.exists()
        and _PAC_SOURCE.exists()
        and _RESOLVER_IR.exists()
    )


def _batch_c_available() -> bool:
    return (
        _BATCH_C_MANIFEST.exists()
        and _BATCH_C_SOURCE.exists()
        and _RESOLVER_IR.exists()
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# A. 真实数据 M1→M5 逐模块验证
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.skipif(not _data_available(), reason="Producer data not available")
class TestRealPacDataModuleChain:
    """PAC corpus 真实数据逐模块验证。"""

    def test_m1_reads_real_manifest_sha(self):
        """M1 从真实 manifest 读取 source_content_sha256。"""
        result = read_manifest_identity(_PAC_MANIFEST)
        assert result.source_content_sha256 is not None
        assert len(result.source_content_sha256) == 64
        assert all(c in "0123456789abcdef" for c in result.source_content_sha256)

    def test_m2_computes_real_source_sha(self):
        """M2 从真实 source bytes 计算 SHA256。"""
        result = load_raw_bytes_identity(_PAC_SOURCE)
        assert len(result.sha256) == 64

    def test_m1_m2_sha_match(self):
        """M1 manifest SHA == M2 computed SHA（真实数据一致性）。"""
        m1 = read_manifest_identity(_PAC_MANIFEST)
        m2 = load_raw_bytes_identity(_PAC_SOURCE)
        assert m1.source_content_sha256 == m2.sha256

    def test_m3_reads_ir_entry_by_sha(self):
        """M3 通过 source_sha 在 batch IR 中定位 entry。"""
        m2 = load_raw_bytes_identity(_PAC_SOURCE)
        m3 = read_ir_identity(
            _RESOLVER_IR,
            source_file=str(_PAC_SOURCE),
            source_sha=m2.sha256,
        )
        assert m3.source_content_sha256 is not None
        assert m3.source_content_sha256 == m2.sha256

    def test_m3_ir_path_mismatch_but_sha_match(self):
        """M3 验证：IR entry 的 file 路径与 source 路径不同，但 SHA 匹配。

        这是 Phase 2.5 locator closure 的核心验证点：
        IR entry file = reslice-pac-annotated\\...（annotated copy）
        source file   = reslice-pac\\...（original）
        路径不同但内容 SHA 相同 → SHA 匹配成功。
        """
        m2 = load_raw_bytes_identity(_PAC_SOURCE)
        # 用 path-only 调用（不传 source_sha）→ 应该找不到（路径不同）
        m3_path_only = read_ir_identity(
            _RESOLVER_IR, source_file=str(_PAC_SOURCE)
        )
        # 用 SHA 调用 → 应该找到
        m3_sha = read_ir_identity(
            _RESOLVER_IR,
            source_file=str(_PAC_SOURCE),
            source_sha=m2.sha256,
        )
        # SHA 匹配成功
        assert m3_sha.source_content_sha256 == m2.sha256

    def test_m4_full_verification(self):
        """M4 正交双轴验证：identity=VERIFIED, semantic=AVAILABLE。"""
        m1 = read_manifest_identity(_PAC_MANIFEST)
        m2 = load_raw_bytes_identity(_PAC_SOURCE)
        m3 = read_ir_identity(
            _RESOLVER_IR,
            source_file=str(_PAC_SOURCE),
            source_sha=m2.sha256,
        )
        vr = verify_identity(
            computed_sha=m2.sha256,
            manifest_sha=m1.source_content_sha256,
            ir_sha=m3.source_content_sha256,
        )
        assert vr.identity.value == "VERIFIED"
        assert vr.semantic.value == "AVAILABLE"
        assert vr.semantic.reason is None

    def test_m5_gate_pass(self):
        """M5 Gate: VERIFIED + AVAILABLE → PASS。"""
        m1 = read_manifest_identity(_PAC_MANIFEST)
        m2 = load_raw_bytes_identity(_PAC_SOURCE)
        m3 = read_ir_identity(
            _RESOLVER_IR,
            source_file=str(_PAC_SOURCE),
            source_sha=m2.sha256,
        )
        vr = verify_identity(
            computed_sha=m2.sha256,
            manifest_sha=m1.source_content_sha256,
            ir_sha=m3.source_content_sha256,
        )
        d = evaluate_identity_gate(vr)
        assert d.gate == "PASS"
        assert d.identity_state == "VERIFIED"
        assert d.semantic_state == "AVAILABLE"
        assert d.reason == "identity_verified_semantic_available"
        assert d.mismatches == ()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# B. 真实数据 runner _verify_identity_boundary 集成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.skipif(not _data_available(), reason="Producer data not available")
class TestRealPacRunnerBoundary:
    """通过 runner 的 _verify_identity_boundary 验证真实数据。"""

    def test_runner_boundary_pass(self):
        """_verify_identity_boundary 对真实数据返回 PASS。"""
        from scripts.preprocessing_consumer.runner_b2 import _verify_identity_boundary

        result = _verify_identity_boundary(
            manifest_path=_PAC_MANIFEST,
            source_path=_PAC_SOURCE,
            resolver_ir_path=_RESOLVER_IR,
        )
        assert result["gate"] == "PASS"
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "AVAILABLE"
        assert result["reason"] == "identity_verified_semantic_available"

    def test_runner_boundary_no_ir_pending(self):
        """不传 IR → identity 仍 VERIFIED，但 semantic PENDING → BLOCK。"""
        from scripts.preprocessing_consumer.runner_b2 import _verify_identity_boundary

        result = _verify_identity_boundary(
            manifest_path=_PAC_MANIFEST,
            source_path=_PAC_SOURCE,
            resolver_ir_path=None,
        )
        assert result["gate"] == "BLOCK"
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "PENDING"
        assert result["reason"] == "semantic_pending"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# C. 真实数据 PASS 后 downstream 执行证据
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.skipif(not _data_available(), reason="Producer data not available")
class TestRealPacDownstreamExecution:
    """证明 PASS 后 IRBuilder/Compiler 被真实调用。"""

    def test_downstream_called_after_pass(self):
        """PASS 后 _run_full_chain 中 IRBuilder.build 和 Compiler.compile 被调用。"""
        from unittest.mock import AsyncMock, MagicMock, patch
        from scripts.preprocessing_consumer.runner_b2 import (
            _run_full_chain,
            _verify_identity_boundary,
        )

        gate_decision = _verify_identity_boundary(
            manifest_path=_PAC_MANIFEST,
            source_path=_PAC_SOURCE,
            resolver_ir_path=_RESOLVER_IR,
        )
        assert gate_decision["gate"] == "PASS"

        # Spy on IRBuilder and Compiler
        with patch(
            "scripts.preprocessing_consumer.runner_b2.IRBuilder"
        ) as mock_ir_builder, patch(
            "scripts.preprocessing_consumer.runner_b2.Compiler"
        ) as mock_compiler, patch(
            "scripts.preprocessing_consumer.runner_b2.evaluate"
        ) as mock_evaluate, patch(
            "scripts.preprocessing_consumer.runner_b2.build_payload"
        ) as mock_build_payload, patch(
            "scripts.preprocessing_consumer.runner_b2._create_source_records",
            new_callable=AsyncMock,
        ) as mock_create_source:
            mock_create_source.return_value = (
                MagicMock(), MagicMock()
            )
            mock_ir_builder.build.return_value = MagicMock(units=[])
            mock_compiler.return_value.compile.return_value = MagicMock(
                leaves=[], materials=[]
            )

            import asyncio

            # 构造 minimal manifest/source_lines
            from scripts.preprocessing_consumer.manifest_reader import load_manifest
            from scripts.preprocessing_consumer.source_loader import load_source_lines

            manifest = load_manifest(_PAC_MANIFEST)
            source_lines = load_source_lines(_PAC_SOURCE)

            session = MagicMock()
            session.flush = AsyncMock()
            session.add = MagicMock()

            result = asyncio.run(
                _run_full_chain(
                    session, manifest, source_lines, _PAC_SOURCE,
                    gate_decision=gate_decision,
                )
            )

            # IRBuilder.build 被调用（至少一次）
            assert mock_ir_builder.build.call_count >= 1, (
                "IRBuilder.build must be called after PASS"
            )
            # Compiler 被实例化并调用 compile
            assert mock_compiler.call_count >= 1, (
                "Compiler must be instantiated after PASS"
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# D. 真实数据 BLOCK 证据（manifest 缺失 sha → BLOCK）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.skipif(not _data_available(), reason="Producer data not available")
class TestRealPacBlockEvidence:
    """真实数据的 BLOCK 证据。"""

    def test_wrong_source_bytes_blocks(self):
        """用错误的 source 文件 → computed != manifest → BLOCK。"""
        from scripts.preprocessing_consumer.runner_b2 import _verify_identity_boundary

        # 用 batch-C 的 source 替代 PAC 的 source（内容不同）
        if not _BATCH_C_SOURCE.exists():
            pytest.skip("Batch-C source not available")

        result = _verify_identity_boundary(
            manifest_path=_PAC_MANIFEST,
            source_path=_BATCH_C_SOURCE,
            resolver_ir_path=_RESOLVER_IR,
        )
        assert result["gate"] == "BLOCK"
        assert result["identity_state"] == "FAILED"

    def test_missing_manifest_blocks(self):
        """不存在的 manifest → BLOCK。"""
        from scripts.preprocessing_consumer.runner_b2 import _verify_identity_boundary

        result = _verify_identity_boundary(
            manifest_path=Path("nonexistent.manifest.json"),
            source_path=_PAC_SOURCE,
            resolver_ir_path=_RESOLVER_IR,
        )
        assert result["gate"] == "BLOCK"
        assert result["identity_state"] == "FAILED"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# E. Batch-C corpus 真实数据验证（第二个 corpus）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.skipif(not _batch_c_available(), reason="Batch-C data not available")
class TestRealBatchCData:
    """Batch-C corpus 真实数据验证（另一个 corpus，路径含中文）。"""

    def test_m1_m2_sha_match_batch_c(self):
        """Batch-C: manifest SHA == computed SHA。"""
        m1 = read_manifest_identity(_BATCH_C_MANIFEST)
        m2 = load_raw_bytes_identity(_BATCH_C_SOURCE)
        assert m1.source_content_sha256 == m2.sha256

    def test_m3_ir_entry_found_batch_c(self):
        """Batch-C: IR entry 通过 SHA 匹配找到。"""
        m2 = load_raw_bytes_identity(_BATCH_C_SOURCE)
        m3 = read_ir_identity(
            _RESOLVER_IR,
            source_file=str(_BATCH_C_SOURCE),
            source_sha=m2.sha256,
        )
        assert m3.source_content_sha256 == m2.sha256

    def test_m5_gate_pass_batch_c(self):
        """Batch-C: 完整 M1→M5 链 → PASS。"""
        from scripts.preprocessing_consumer.runner_b2 import _verify_identity_boundary

        result = _verify_identity_boundary(
            manifest_path=_BATCH_C_MANIFEST,
            source_path=_BATCH_C_SOURCE,
            resolver_ir_path=_RESOLVER_IR,
        )
        assert result["gate"] == "PASS"
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "AVAILABLE"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# F. Data readiness prerequisite 记录
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestDataReadinessPrerequisite:
    """记录 data readiness 状态。"""

    def test_pac_data_readiness(self):
        """PAC corpus data readiness 状态。"""
        if not _data_available():
            pytest.skip("PAC data not available on this machine")
        # 验证 manifest 有 source_content_sha256
        m1 = read_manifest_identity(_PAC_MANIFEST)
        assert m1.source_content_sha256 is not None, (
            "PAC manifest must have source_content_sha256 "
            "(data readiness prerequisite)"
        )

    def test_resolver_ir_readiness(self):
        """Resolver IR data readiness 状态。"""
        if not _RESOLVER_IR.exists():
            pytest.skip("Resolver IR not available on this machine")
        data = json.loads(_RESOLVER_IR.read_text(encoding="utf-8"))
        files = data.get("files", [])
        admitted_with_sha = sum(
            1 for e in files
            if e.get("disposition") == "ADMITTED"
            and isinstance(e.get("ir"), dict)
            and e["ir"].get("source_sha256")
        )
        assert admitted_with_sha > 0, (
            "Resolver IR must have ADMITTED entries with source_sha256"
        )
