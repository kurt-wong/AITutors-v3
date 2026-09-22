"""X2.6 F-RBC-01 — Interface Identity Version 类型鲁棒性（runtime robustness correction）。

根因（F-RBC-01）::

    identity_version not in _INTERFACE_IDENTITY_VERSIONS      # = {2, "2"}

set 成员判定要调 `hash(x)`。对 unhashable 取值（list / dict / set / bytearray）
Python **不**返回 False，而是抛 `TypeError: unhashable type: ...`。而
`enforce_interface_scope()` 只捕获 `BoundaryViolation`，故该 `TypeError` 会穿透
boundary decision layer，使 `run_corpus()` 整体异常中止。

目标行为（任务书 §3）::

    2      → PASS              "2"  → PASS
    1      → BLOCK             3    → BLOCK
    "1"    → BLOCK             "3"  → BLOCK
    None   → BLOCK / MISSING_IDENTITY_VERSION
    []     → BLOCK / BoundaryViolation（不得 TypeError）
    {}     → BLOCK / BoundaryViolation（不得 TypeError）
    True   → BLOCK             False → BLOCK
    2.0    → **保持既有行为不改**（F-RBC-05 独立裁量，本任务不得收紧）

CONSTRUCTED / ADVERSARIAL 标记：本文件全部 `[]` / `{}` / `True` / `False` /
`2.0` / 复数等取值均为**构造对抗样本**。真实 Papers corpus 的 manifest 里没有
`identity_version = []` 或 `{}`（JSON 层可表达，但 Producer 未产出过），故**不得**
声称真实语料已覆盖这些形态——真实语料部分只验证「既有正常结果没有变化」。

本任务边界（§8）：**只**处理 F-RBC-01。F-INT-02…07、F-RBC-02…06 一律不动。
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.identity_gate import GATE_BLOCK, GATE_PASS
from scripts.preprocessing_consumer.boundary import (
    CODE_MALFORMED_IDENTITY_VERSION,
    CODE_MISSING_IDENTITY_VERSION,
    CODE_OUT_OF_SCOPE_IDENTITY_VERSION,
    BoundaryViolation,
    enforce_interface_scope,
    normalize_interface_identity,
)
from scripts.preprocessing_consumer import runner as runner_v1
from scripts.preprocessing_consumer import runner_b2

SOURCE_BYTES = b"synthetic source bytes for F-RBC-01\nline two\n"
SHA_OK = hashlib.sha256(SOURCE_BYTES).hexdigest()

_OMIT = object()

# 真实语料根（= kurt-wong/Aitutors-preprocessing 的本地检出）——只读
_PAPERS_ROOT = Path(r"D:\Project\Papers")

_BACKEND = Path(__file__).resolve().parents[1]


# ═══════════════════════════════════════════════════════════════
# fixture helpers（合成 / 对抗构造）
# ═══════════════════════════════════════════════════════════════


def _write_source(tmp_path: Path) -> Path:
    p = tmp_path / "source.md"
    p.write_bytes(SOURCE_BYTES)
    return p


def _write_manifest(
    tmp_path: Path,
    *,
    sha: object = _OMIT,
    identity_version: object = _OMIT,
    name: str = "test.manifest.json",
    source_file: str = "",
) -> Path:
    """写 manifest fixture。`_OMIT` = 不写该键（= Producer 未声明）。

    取值原样写入 JSON，**不**做任何转换（`[]` 就是 `[]`，不是 `"[]"`）。
    """
    m: dict = {"source_file": source_file, "units": []}
    if sha is not _OMIT:
        m["source_content_sha256"] = sha
    if identity_version is not _OMIT:
        m["identity_version"] = identity_version
    p = tmp_path / name
    p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    return p


def _write_ir(tmp_path: Path, sha: str) -> Path:
    """写匹配的 resolver IR，使 M4/M5 达到 VERIFIED + AVAILABLE（= PASS）。

    这样拒绝原因**只能**来自 Interface Scope 闸门，而不是 `semantic_pending`。
    """
    p = tmp_path / "test.ir.json"
    p.write_text(
        json.dumps({"source_content_sha256": sha}, ensure_ascii=False),
        encoding="utf-8",
    )
    return p


# ═══════════════════════════════════════════════════════════════
# §6.1 / §6.2  list / dict → BoundaryViolation，绝不 TypeError
# ═══════════════════════════════════════════════════════════════


class TestUnhashableIdentityVersionForms:
    """CONSTRUCTED / ADVERSARIAL — unhashable `identity_version` 必须 fail-closed。"""

    def test_list_raises_boundary_violation_not_type_error(self):
        """§6.1 — `normalize_interface_identity(SHA_OK, [])` → `BoundaryViolation`。"""
        with pytest.raises(BoundaryViolation) as exc_info:
            normalize_interface_identity(SHA_OK, [])

        assert exc_info.value.code == CODE_MALFORMED_IDENTITY_VERSION
        assert not isinstance(exc_info.value, TypeError)

    def test_dict_raises_boundary_violation_not_type_error(self):
        """§6.2 — `normalize_interface_identity(SHA_OK, {})` → `BoundaryViolation`。"""
        with pytest.raises(BoundaryViolation) as exc_info:
            normalize_interface_identity(SHA_OK, {})

        assert exc_info.value.code == CODE_MALFORMED_IDENTITY_VERSION
        assert not isinstance(exc_info.value, TypeError)

    @pytest.mark.parametrize(
        "bad_version",
        [
            pytest.param([], id="list"),
            pytest.param({}, id="dict"),
            pytest.param([2], id="list-of-2"),
            pytest.param({"v": 2}, id="dict-of-v2"),
            pytest.param([{"nested": 1}], id="list-of-dict"),
            pytest.param(set(), id="set"),
            pytest.param(bytearray(b"x"), id="bytearray"),
            pytest.param(tuple(), id="tuple"),
            pytest.param(object(), id="custom-object"),
        ],
    )
    def test_any_unhashable_or_nonscalar_form_is_a_boundary_violation(self, bad_version):
        """形态闸门按**类型**判定，与是否为空 / 是否可序列化无关。"""
        with pytest.raises(BoundaryViolation) as exc_info:
            normalize_interface_identity(SHA_OK, bad_version)

        assert exc_info.value.code == CODE_MALFORMED_IDENTITY_VERSION

    @pytest.mark.parametrize(
        "bad_version",
        [
            pytest.param([], id="list"),
            pytest.param({}, id="dict"),
            pytest.param([2], id="list-of-2"),
            pytest.param({"v": 2}, id="dict-of-v2"),
        ],
    )
    def test_enforce_decision_rejects_json_unhashable_forms(self, bad_version):
        """§6.1/§6.2 — 经唯一接入点：`accepted == False` + 稳定边界错误码。"""
        decision = enforce_interface_scope(SHA_OK, bad_version)

        assert decision.accepted is False
        assert decision.code == CODE_MALFORMED_IDENTITY_VERSION
        assert decision.identity is None
        assert decision.reason.startswith(
            f"interface_scope_rejected: {CODE_MALFORMED_IDENTITY_VERSION}"
        )

    @pytest.mark.parametrize(
        "bad_version",
        [pytest.param([], id="list"), pytest.param({}, id="dict")],
    )
    def test_enforce_interface_scope_never_raises_for_unhashable_input(self, bad_version):
        """决策层契约：任何输入都返回决策形状，**不**上抛（含 TypeError）。"""
        decision = enforce_interface_scope(SHA_OK, bad_version)  # 不应抛
        assert isinstance(decision.accepted, bool)


# ═══════════════════════════════════════════════════════════════
# §6.3  Boolean
# ═══════════════════════════════════════════════════════════════


class TestBooleanIdentityVersion:
    """CONSTRUCTED / ADVERSARIAL — bool 不得因 int 继承关系被误接受。"""

    @pytest.mark.parametrize("bad_version", [True, False], ids=["true", "false"])
    def test_bool_blocks(self, bad_version):
        """§6.3 — `True` / `False` → BLOCK。"""
        with pytest.raises(BoundaryViolation) as exc_info:
            normalize_interface_identity(SHA_OK, bad_version)

        assert exc_info.value.code == CODE_OUT_OF_SCOPE_IDENTITY_VERSION

        decision = enforce_interface_scope(SHA_OK, bad_version)
        assert decision.accepted is False
        assert decision.identity is None

    @pytest.mark.parametrize("bad_version", [True, False], ids=["true", "false"])
    def test_bool_blocks_at_runtime_boundary(self, tmp_path, bad_version):
        """§6.3 — 经真实 runtime 边界 `_verify_identity_boundary` 同样阻断。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version=bad_version)
        ir = _write_ir(tmp_path, SHA_OK)

        result = runner_b2._verify_identity_boundary(manifest, source, ir)

        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "VERIFIED"  # M1–M5 已通过 → 拒绝只能来自闸门
        assert result["interface_scope"]["accepted"] is False
        assert CODE_OUT_OF_SCOPE_IDENTITY_VERSION in result["mismatches"]


# ═══════════════════════════════════════════════════════════════
# §6.4  合法行为保持 + §6.5  2.0 既有行为保持
# ═══════════════════════════════════════════════════════════════


class TestLegalBehaviourUnchanged:
    """§6.4 — 合法取值与既有越界/缺失行为不得回归。"""

    @pytest.mark.parametrize("good_version", [2, "2"], ids=["int-2", "str-2"])
    def test_version_2_forms_pass(self, tmp_path, good_version):
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version=good_version)
        ir = _write_ir(tmp_path, SHA_OK)

        result = runner_b2._verify_identity_boundary(manifest, source, ir)

        assert result["gate"] == GATE_PASS
        assert result["interface_scope"]["accepted"] is True
        assert result["interface_scope"]["code"] is None

        decision = enforce_interface_scope(SHA_OK, good_version)
        assert decision.accepted is True

    @pytest.mark.parametrize(
        "bad_version,expected_code",
        [
            pytest.param(1, CODE_OUT_OF_SCOPE_IDENTITY_VERSION, id="int-1"),
            pytest.param(3, CODE_OUT_OF_SCOPE_IDENTITY_VERSION, id="int-3"),
            pytest.param("1", CODE_OUT_OF_SCOPE_IDENTITY_VERSION, id="str-1"),
            pytest.param("3", CODE_OUT_OF_SCOPE_IDENTITY_VERSION, id="str-3"),
            pytest.param(None, CODE_MISSING_IDENTITY_VERSION, id="null"),
            pytest.param(_OMIT, CODE_MISSING_IDENTITY_VERSION, id="missing"),
        ],
    )
    def test_out_of_scope_and_missing_unchanged(
        self, tmp_path, bad_version, expected_code
    ):
        source = _write_source(tmp_path)
        manifest = _write_manifest(
            tmp_path,
            sha=SHA_OK,
            **({} if bad_version is _OMIT else {"identity_version": bad_version}),
        )
        ir = _write_ir(tmp_path, SHA_OK)

        result = runner_b2._verify_identity_boundary(manifest, source, ir)

        assert result["gate"] == GATE_BLOCK
        assert result["interface_scope"]["code"] == expected_code


class TestFloatTwoPointZeroPreserved:
    """§6.5 — `2.0` 的**既有**行为不得因本修复改变（F-RBC-05 独立裁量）。"""

    def test_python_set_membership_premise_is_pinned(self):
        """钉住修改前判定所依赖的 Python 语义，便于 DSH 独立核对行为差异。

        修改前的判定就是 `identity_version not in {2, "2"}`：hash 相同且 `==` 为真
        者一律命中。故 `2.0`（**保留**接受）与 `2+0j`（本闸门改为形态拒绝，见
        `test_complex_form_is_now_rejected_as_malformed`）在修改前**都会**被接受。
        """
        assert (2.0 in {2, "2"}) is True
        assert (2 + 0j in {2, "2"}) is True

    def test_2_point_0_still_accepted_unchanged(self, tmp_path):
        """`2.0` 仍被接受 —— 与修复前逐值等价，未借 F-RBC-01 收紧为 BLOCK。"""
        decision = enforce_interface_scope(SHA_OK, 2.0)
        assert decision.accepted is True
        assert decision.identity is not None
        assert decision.identity.identity_version == "2"

        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version=2.0)
        ir = _write_ir(tmp_path, SHA_OK)
        result = runner_b2._verify_identity_boundary(manifest, source, ir)
        assert result["gate"] == GATE_PASS

    def test_complex_form_is_now_rejected_as_malformed(self):
        """`2+0j` 现按**非法形态**拒绝（不再是数值相等命中）。

        这是形态白名单的**已披露副作用**：`complex` 不是 JSON 标量，Producer manifest
        无法表达它，只可能由直接 Python 调用传入。若 Owner 认为它应继续等同于 `2`，
        属独立 Contract / Owner Decision（同 F-RBC-05），不在本任务自行裁定。
        """
        with pytest.raises(BoundaryViolation) as exc_info:
            normalize_interface_identity(SHA_OK, 2 + 0j)
        assert exc_info.value.code == CODE_MALFORMED_IDENTITY_VERSION


# ═══════════════════════════════════════════════════════════════
# §4.3  fail-closed，无 DEFAULT / FALLBACK / SKIP / COERCE / PASS
# ═══════════════════════════════════════════════════════════════


class TestNoSilentCoercion:
    """CONSTRUCTED / ADVERSARIAL — 非法形态绝不被隐式转换或默认。"""

    @pytest.mark.parametrize(
        "bad_version",
        [pytest.param([], id="list"), pytest.param({}, id="dict")],
    )
    def test_rejected_decision_carries_no_identity(self, bad_version):
        """`[]` 绝不变成 `"[]"` 或 `2`：拒绝时不产出任何 canonical 身份事实。"""
        decision = enforce_interface_scope(SHA_OK, bad_version)
        assert decision.accepted is False
        assert decision.identity is None

    @pytest.mark.parametrize(
        "bad_version",
        [pytest.param([], id="list"), pytest.param({}, id="dict")],
    )
    def test_runner_preserves_declared_value_verbatim(self, tmp_path, bad_version):
        """拒绝记录保留 Producer 声明值 verbatim（provenance），不解释、不改写。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version=bad_version)
        ir = _write_ir(tmp_path, SHA_OK)

        result = runner_b2._verify_identity_boundary(manifest, source, ir)

        assert result["interface_scope"]["declared_identity_version"] == bad_version
        assert result["interface_scope"]["accepted"] is False

    @pytest.mark.parametrize(
        "bad_version",
        [pytest.param([], id="list"), pytest.param({}, id="dict")],
    )
    def test_no_default_to_two_when_form_is_malformed(self, bad_version):
        """形态非法 ≠ 缺失：不会落到 `MISSING_IDENTITY_VERSION`，更不会默认成 2。"""
        decision = enforce_interface_scope(SHA_OK, bad_version)
        assert decision.code == CODE_MALFORMED_IDENTITY_VERSION
        assert decision.code != CODE_MISSING_IDENTITY_VERSION


# ═══════════════════════════════════════════════════════════════
# §7  Runner 级行为验证（不得把 TypeError 传播为 runner 未处理异常）
# ═══════════════════════════════════════════════════════════════


class TestRunnerLevelRobustness:
    """`[]` / `{}` 不得使 runner 异常中止；下游 semantic processing 不得执行。"""

    @pytest.mark.parametrize(
        "bad_version",
        [pytest.param([], id="list"), pytest.param({}, id="dict")],
    )
    def test_runner_b2_boundary_returns_decision_instead_of_raising(
        self, tmp_path, bad_version
    ):
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version=bad_version)
        ir = _write_ir(tmp_path, SHA_OK)

        result = runner_b2._verify_identity_boundary(manifest, source, ir)  # 不应抛

        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "VERIFIED"
        assert result["interface_scope"]["code"] == CODE_MALFORMED_IDENTITY_VERSION
        assert CODE_MALFORMED_IDENTITY_VERSION in result["mismatches"]

    @pytest.mark.parametrize(
        "bad_version",
        [pytest.param([], id="list"), pytest.param({}, id="dict")],
    )
    def test_runner_b2_full_chain_short_circuits(self, tmp_path, bad_version):
        """拒绝后 annotation / IRBuilder / Compiler / Gate / Admission 零调用。"""
        source = _write_source(tmp_path)
        manifest_path = _write_manifest(
            tmp_path, sha=SHA_OK, identity_version=bad_version
        )
        ir = _write_ir(tmp_path, SHA_OK)
        gate_decision = runner_b2._verify_identity_boundary(manifest_path, source, ir)

        from scripts.preprocessing_consumer.manifest_reader import load_manifest

        manifest = load_manifest(manifest_path)

        with patch(
            "scripts.preprocessing_consumer.runner_b2._create_source_records"
        ) as mock_create, patch(
            "scripts.preprocessing_consumer.runner_b2.manifest_to_annotation_payload"
        ) as mock_ann, patch(
            "scripts.preprocessing_consumer.runner_b2.IRBuilder"
        ) as mock_ir, patch(
            "scripts.preprocessing_consumer.runner_b2.Compiler"
        ) as mock_compiler, patch(
            "scripts.preprocessing_consumer.runner_b2.evaluate"
        ) as mock_evaluate, patch(
            "scripts.preprocessing_consumer.runner_b2.build_payload"
        ) as mock_payload:
            result = asyncio.run(
                runner_b2._run_full_chain(
                    MagicMock(), manifest, [], source, gate_decision=gate_decision,
                )
            )

        assert result["status"] == "identity_blocked"
        assert result["downstream_executed"] is False
        assert mock_create.call_count == 0
        assert mock_ann.call_count == 0
        assert mock_ir.call_count == 0
        assert mock_compiler.call_count == 0
        assert mock_evaluate.call_count == 0
        assert mock_payload.call_count == 0

    @pytest.mark.parametrize(
        "bad_version",
        [pytest.param([], id="list"), pytest.param({}, id="dict")],
    )
    def test_runner_b2_run_corpus_survives_and_blocks(self, tmp_path, bad_version):
        """经**真实** `run_corpus` 入口：不中止、记为 Interface Scope 拒绝、下游不跑。"""
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        source = corpus / "source.md"
        source.write_bytes(SOURCE_BYTES)
        (corpus / "p1.manifest.json").write_text(
            json.dumps({
                "source_file": str(source),
                "source_content_sha256": SHA_OK,
                "identity_version": bad_version,
                "units": [],
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        ir = _write_ir(tmp_path, SHA_OK)
        out = tmp_path / "report.json"

        with patch(
            "scripts.preprocessing_consumer.runner_b2._run_full_chain"
        ) as mock_chain, patch(
            "scripts.preprocessing_consumer.runner_b2._create_source_records"
        ) as mock_create, patch(
            "scripts.preprocessing_consumer.runner_b2.IRBuilder"
        ) as mock_ir, patch(
            "scripts.preprocessing_consumer.runner_b2.Compiler"
        ) as mock_compiler, patch(
            "scripts.preprocessing_consumer.runner_b2.evaluate"
        ) as mock_evaluate, patch(
            "scripts.preprocessing_consumer.runner_b2.build_payload"
        ) as mock_payload:
            asyncio.run(runner_b2.run_corpus(corpus, out, resolver_ir_path=ir))

        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["summary"]["identity_blocked"] == 1
        assert report["summary"]["completed"] == 0
        assert report["summary"]["error"] == 0

        paper = report["papers"][0]["result"]
        assert paper["status"] == "identity_blocked"
        assert paper["downstream_executed"] is False
        assert paper["identity_gate"]["interface_scope"]["code"] == (
            CODE_MALFORMED_IDENTITY_VERSION
        )
        assert paper["identity_gate"]["interface_scope"]["declared_identity_version"] == (
            bad_version
        )
        assert mock_chain.call_count == 0
        assert mock_create.call_count == 0
        assert mock_ir.call_count == 0
        assert mock_compiler.call_count == 0
        assert mock_evaluate.call_count == 0
        assert mock_payload.call_count == 0

    @pytest.mark.parametrize(
        "bad_version",
        [pytest.param([], id="list"), pytest.param({}, id="dict")],
    )
    def test_runner_v1_run_corpus_survives_and_blocks(self, tmp_path, bad_version):
        """`runner.py`（Track A 直入生产 GateService 的入口）同样不得中止。"""
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        source = corpus / "source.md"
        source.write_bytes(SOURCE_BYTES)
        (corpus / "p1.manifest.json").write_text(
            json.dumps({
                "source_file": str(source),
                "source_content_sha256": SHA_OK,
                "identity_version": bad_version,
                "units": [],
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        out = tmp_path / "report.json"

        with patch(
            "scripts.preprocessing_consumer.runner._track_a"
        ) as mock_a, patch(
            "scripts.preprocessing_consumer.runner._track_b"
        ) as mock_b:
            asyncio.run(runner_v1.run_corpus(corpus, out))  # 不应抛

        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["interface_scope_blocked"] == 1
        rejected = report["papers"][0]["interface_scope_rejected"]
        assert rejected["accepted"] is False
        assert rejected["code"] == CODE_MALFORMED_IDENTITY_VERSION
        assert rejected["declared_identity_version"] == bad_version
        assert rejected["downstream_executed"] is False
        # Track A（生产 GateService）/ Track B 完全未执行
        assert mock_a.call_count == 0
        assert mock_b.call_count == 0


# ═══════════════════════════════════════════════════════════════
# §4.1  不建立第二套 Interface Scope 规则
# ═══════════════════════════════════════════════════════════════


class TestSingleAuthorityPreserved:
    """形态判定只存在于 `boundary.normalize_interface_identity`，runners 不复制规则。"""

    def test_runners_contain_no_identity_version_comparison(self):
        """AST 断言：两个 runner 内不存在任何对 `identity_version` 的比较/成员判定。"""
        for rel in ("runner.py", "runner_b2.py"):
            src = (_BACKEND / "scripts" / "preprocessing_consumer" / rel).read_text(
                encoding="utf-8"
            )
            tree = ast.parse(src)
            offenders = []
            for node in ast.walk(tree):
                if not isinstance(node, ast.Compare):
                    continue
                segment = ast.get_source_segment(src, node) or ""
                if "identity_version" in segment:
                    offenders.append(segment)
            assert offenders == [], (
                f"{rel} 必须不自行判定 identity_version（唯一权威是 "
                f"boundary.normalize_interface_identity），发现: {offenders}"
            )

    def test_membership_rule_constant_lives_only_in_boundary(self):
        """`_INTERFACE_IDENTITY_VERSIONS` 不得在 boundary.py 之外出现（无平行实现）。"""
        hits = []
        for path in (_BACKEND / "scripts").rglob("*.py"):
            if path.name == "boundary.py":
                continue
            if "_INTERFACE_IDENTITY_VERSIONS" in path.read_text(encoding="utf-8"):
                hits.append(str(path))
        assert hits == [], f"第二套 identity scope 规则出现在: {hits}"

    def test_malformed_form_is_judged_only_inside_normalize(self):
        """形态白名单判定只在权威函数内，决策层不复制、runners 不复制。"""
        src = (_BACKEND / "scripts" / "preprocessing_consumer" / "boundary.py").read_text(
            encoding="utf-8"
        )
        assert src.count("_IDENTITY_VERSION_ACCEPTED_TYPES") == 2  # 定义 + 一处使用

        for rel in ("runner.py", "runner_b2.py"):
            text = (_BACKEND / "scripts" / "preprocessing_consumer" / rel).read_text(
                encoding="utf-8"
            )
            assert "_IDENTITY_VERSION_ACCEPTED_TYPES" not in text
            assert "MALFORMED_IDENTITY_VERSION" not in text


# ═══════════════════════════════════════════════════════════════
# §11  Real Corpus — 只验证「既有正常结果没有变化」（不锚定计数）
# ═══════════════════════════════════════════════════════════════


@pytest.mark.skipif(not _PAPERS_ROOT.exists(), reason="Papers corpus not mounted")
class TestRealCorpusUnchanged:
    """真实语料只读核验。**不**锚定数量（F-RBC-06 未处理）。"""

    def _iter_manifests(self):
        """真实 Producer corpus 迭代器（与 `test_x26_fint08_interface_scope` 同口径）。

        排除 `.pytest_work` / `_archive`：那些是测试 scratch / 归档夹具，**不是**
        Producer corpus。实测 `D:\\Project\\Papers` 下 `*.manifest.json` 共 204 个，
        其中 172 个属真实语料、32 个在 `.pytest_work/` 下。把 scratch 计入会伪造
        「真实语料」结论（那些 manifest 可能缺 `source_content_sha256`）。
        """
        for p in sorted(_PAPERS_ROOT.rglob("*.manifest.json")):
            if ".pytest_work" in p.parts or "_archive" in p.parts:
                continue
            yield p

    def _raw_manifests(self) -> list[dict]:
        out = []
        for p in self._iter_manifests():
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(raw, dict):
                out.append(raw)
        return out

    def test_real_corpus_version_2_inputs_still_accepted(self):
        """声明 `identity_version ∈ {2, "2"}` 的真实输入仍全部通过（不锚定数量）。"""
        accepted = 0
        for raw in self._raw_manifests():
            if raw.get("identity_version") not in (2, "2"):
                continue
            decision = enforce_interface_scope(
                raw.get("source_content_sha256"), raw.get("identity_version")
            )
            assert decision.accepted is True, (
                f"真实语料 identity_version=2 输入被误拒: {raw.get('source_file')}"
            )
            accepted += 1
        assert accepted > 0, "真实语料应存在 identity_version=2 的输入"

    def test_real_corpus_no_type_error_for_any_declared_form(self):
        """真实语料**任何**声明形态都不得使权威上抛非 BoundaryViolation 异常。"""
        for raw in self._raw_manifests():
            decision = enforce_interface_scope(
                raw.get("source_content_sha256"), raw.get("identity_version")
            )
            assert isinstance(decision.accepted, bool)
