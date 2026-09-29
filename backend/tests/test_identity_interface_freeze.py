"""M1–M5 冻结接口名钉扎（DESIGN-v1.1 §4.2–§4.6 / D2=b interface reference only）。

只钉「冻结签名是否存在且可调用」，不重测行为（行为见各 M 单元/对抗测试）。
实现落点 = `app/core/`（SYSTEM-BASELINE 登记）；Design 文内路径为 interface reference。
"""

from inspect import signature

import pytest


@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest — 纯接口检查，无 DB。"""


class TestFrozenInterfaceNames:
    def test_m1_read_manifest_identity(self):
        from app.core.manifest_identity import read_manifest_identity

        params = list(signature(read_manifest_identity).parameters)
        assert params == ["manifest_path"]

    def test_m2_load_raw_bytes_alias(self):
        from app.core.raw_bytes_identity import load_raw_bytes, load_raw_bytes_identity

        assert load_raw_bytes is load_raw_bytes_identity
        params = list(signature(load_raw_bytes).parameters)
        assert params == ["source_path"]

    def test_m3_read_ir_identity(self):
        from app.core.ir_identity import read_ir_identity

        params = list(signature(read_ir_identity).parameters)
        assert params[0] == "ir_path"

    def test_m4_verify_identity(self):
        from app.core.identity_verifier import verify_identity

        params = list(signature(verify_identity).parameters)
        assert params == ["computed_sha", "manifest_sha", "ir_sha"]

    def test_m5_evaluate_identity_alias(self):
        from app.core.identity_gate import evaluate_identity, evaluate_identity_gate

        assert evaluate_identity is evaluate_identity_gate
        params = list(signature(evaluate_identity).parameters)
        assert params == ["verification"]


class TestFrozenValueDomain:
    """状态码白名单（§4.7）：identity ∈ {VERIFIED,FAILED}；semantic ∈ {AVAILABLE,PENDING}。"""

    def test_identity_state_domain(self):
        from app.core.identity_verifier import (
            IDENTITY_FAILED,
            IDENTITY_VERIFIED,
            verify_identity,
        )

        sha = "a" * 64
        assert IDENTITY_VERIFIED == "VERIFIED"
        assert IDENTITY_FAILED == "FAILED"
        for computed, manifest, ir in (
            (sha, sha, sha),
            (sha, sha, None),
            (sha, "b" * 64, sha),
            (sha, None, sha),
        ):
            r = verify_identity(computed, manifest, ir)
            assert r.identity.value in ("VERIFIED", "FAILED")
            if r.semantic is not None:
                assert r.semantic.value in ("AVAILABLE", "PENDING")
            else:
                assert r.identity.value == "FAILED"


class TestM5FailClosedNoBypass:
    """用户点名的 M5 面：未验证 fail-closed / 缺失不猜测 / 无新绕过路径。"""

    def test_unverified_identity_fail_closed(self):
        from app.core.identity_gate import GATE_BLOCK, evaluate_identity
        from app.core.identity_verifier import verify_identity

        d = evaluate_identity(verify_identity("a" * 64, "b" * 64))
        assert d.gate == GATE_BLOCK

    def test_missing_identity_no_guess(self):
        from app.core.identity_gate import GATE_BLOCK, evaluate_identity

        for bad in (None, object(), "not-a-result"):
            assert evaluate_identity(bad).gate == GATE_BLOCK

    def test_no_second_gate_entrypoint(self):
        """M5 唯一入口 = evaluate_identity(_gate)；禁止平行 gate 实现。"""
        import app.core.identity_gate as mod

        callables = [
            n
            for n in dir(mod)
            if n.startswith("evaluate") and callable(getattr(mod, n))
        ]
        # 允许冻结别名 evaluate_identity + 实现名 evaluate_identity_gate
        assert set(callables) <= {"evaluate_identity", "evaluate_identity_gate"}
