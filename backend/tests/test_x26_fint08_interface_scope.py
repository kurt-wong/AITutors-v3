"""X2.6 — F-INT-08 / F-INT-01 Runtime Identity Boundary Correction 行为测试。

任务目标（唯一）::

    preprocessing → V3/X 的实际运行入口，在接受输入进入 V3 pipeline 之前，
    强制确认该输入属于当前 Frozen Contract v0.2 Interface Scope，即
    identity_version == 2。

强制矩阵（任务书 §5）::

    valid identity + identity_version=2      → PASS
    valid identity + identity_version=1      → FAIL   （核心）
    valid identity + identity_version=3      → FAIL   （核心）
    valid identity + missing version         → FAIL
    missing identity                         → FAIL
    invalid SHA / identity mismatch          → FAIL

不变量（任务书 §2）::

    identity_version = 2      → PASS
    identity_version = 1      → FAIL
    identity_version = 3      → FAIL
    identity_version missing  → FAIL
    invalid identity          → FAIL

禁止（任务书 §2）::

    version != 2  →  默认当成 v2           禁止
    version != 2  →  fallback → 继续运行    禁止

矩阵用例的构造原则（关键）::

    「valid identity + identity_version=N」必须让 M1–M5 **全部通过**（含匹配的
    resolver IR，使 semantic=AVAILABLE），这样拒绝只能来自 Interface Scope 闸门，
    才构成对 F-INT-08 的有效证明。否则会先因 `semantic_pending` 被 M5 阻断，
    那证明的是另一件事。

样本标记（任务书 §11）::

    CONSTRUCTED / ADVERSARIAL — 本文件全部 version 1 / 3 / missing 用例均为
    **构造/对抗样本**。真实 Papers corpus 实测 `identity_version` 分布只有
    {2, 缺失}，**不存在** version 1 或 3 的样本，因此**不得**声称
    「真实 corpus 已覆盖 version 1/3」。真实语料用例（TestRealCorpusTargeted）
    只验证：v2 子集仍被接受、缺失子集仍被拒绝，并显式断言语料中 version 1/3
    样本数为 0。

Admission 落库需要 PostgreSQL 会话，不在本文件覆盖；端到端止于 Gate 纯函数段。
"""

from __future__ import annotations

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
    CODE_MALFORMED_IDENTITY,
    CODE_MISSING_IDENTITY,
    CODE_MISSING_IDENTITY_VERSION,
    CODE_OUT_OF_SCOPE_IDENTITY_VERSION,
    enforce_interface_scope,
    normalize_interface_identity,
)
from scripts.preprocessing_consumer.runner_b2 import (
    _run_full_chain,
    _verify_identity_boundary,
    run_corpus,
)

SOURCE_BYTES = b"synthetic source bytes for F-INT-08 matrix\nline two\n"
SHA_OK = hashlib.sha256(SOURCE_BYTES).hexdigest()
SHA_OTHER = hashlib.sha256(b"different bytes").hexdigest()

_OMIT = object()

# 真实语料根（= kurt-wong/Aitutors-preprocessing 的本地检出）
_PAPERS_ROOT = Path(r"D:\Project\Papers")

_BACKEND = Path(__file__).resolve().parents[1]


# ═══════════════════════════════════════════════════════════════
# fixture helpers（合成 / 对抗构造）
# ═══════════════════════════════════════════════════════════════


def _write_source(tmp_path: Path, content: bytes = SOURCE_BYTES) -> Path:
    p = tmp_path / "source.md"
    p.write_bytes(content)
    return p


def _write_manifest(
    tmp_path: Path,
    *,
    sha: object = _OMIT,
    identity_version: object = _OMIT,
    name: str = "test.manifest.json",
) -> Path:
    """写 manifest fixture。`_OMIT` = 不写该键（= Producer 未声明）。"""
    m: dict = {"source_file": "", "units": []}
    if sha is not _OMIT:
        m["source_content_sha256"] = sha
    if identity_version is not _OMIT:
        m["identity_version"] = identity_version
    p = tmp_path / name
    p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    return p


def _write_ir(tmp_path: Path, sha: str, name: str = "test.ir.json") -> Path:
    """写匹配的 resolver IR，使 M4/M5 达到 VERIFIED + AVAILABLE（= PASS）。"""
    p = tmp_path / name
    p.write_text(
        json.dumps({"source_content_sha256": sha}, ensure_ascii=False),
        encoding="utf-8",
    )
    return p


def _boundary_rejects(tmp_path: Path, identity_version: object) -> dict:
    """构造「除 identity_version 外一切合法」的输入，跑真实 runtime 边界。"""
    source = _write_source(tmp_path)
    manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version=identity_version)
    ir = _write_ir(tmp_path, SHA_OK)
    return _verify_identity_boundary(manifest, source, ir)


# ═══════════════════════════════════════════════════════════════
# §5 强制行为矩阵
# ═══════════════════════════════════════════════════════════════


class TestBehaviorMatrix:
    """任务书 §5 矩阵：经**真实 runtime 边界** `_verify_identity_boundary` 断言。"""

    def test_valid_identity_and_version_2_passes(self, tmp_path):
        """valid identity + identity_version=2 → PASS。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version=2)
        ir = _write_ir(tmp_path, SHA_OK)

        result = _verify_identity_boundary(manifest, source, ir)

        assert result["gate"] == GATE_PASS
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "AVAILABLE"
        assert result["interface_scope"]["accepted"] is True
        assert result["interface_scope"]["code"] is None

    def test_valid_identity_and_version_2_as_string_passes(self, tmp_path):
        """合法身份 + str "2" → PASS（corpus 中 int/str 两种编码表达同一事实）。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version="2")
        ir = _write_ir(tmp_path, SHA_OK)

        result = _verify_identity_boundary(manifest, source, ir)

        assert result["gate"] == GATE_PASS
        assert result["interface_scope"]["accepted"] is True

    def test_valid_identity_and_version_1_must_fail(self, tmp_path):
        """CONSTRUCTED / ADVERSARIAL — 合法 SHA + 完整 identity + version=1 → MUST FAIL。

        本 Finding 的核心用例之一：M1–M5 全绿，除 `identity_version` 外一切合法，
        故拒绝**只能**来自 Interface Scope 闸门。
        """
        result = _boundary_rejects(tmp_path, 1)

        # 先证明 M1–M5 确实通过了（否则证明的不是本 Finding）
        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "AVAILABLE"

        assert result["gate"] == GATE_BLOCK
        assert result["interface_scope"]["accepted"] is False
        assert result["interface_scope"]["code"] == CODE_OUT_OF_SCOPE_IDENTITY_VERSION
        assert CODE_OUT_OF_SCOPE_IDENTITY_VERSION in result["mismatches"]

    def test_valid_identity_and_version_3_must_fail(self, tmp_path):
        """CONSTRUCTED / ADVERSARIAL — 合法 SHA + 完整 identity + version=3 → MUST FAIL。

        本 Finding 的核心用例之一：M1–M5 全绿，除 `identity_version` 外一切合法。
        """
        result = _boundary_rejects(tmp_path, 3)

        assert result["identity_state"] == "VERIFIED"
        assert result["semantic_state"] == "AVAILABLE"

        assert result["gate"] == GATE_BLOCK
        assert result["interface_scope"]["accepted"] is False
        assert result["interface_scope"]["code"] == CODE_OUT_OF_SCOPE_IDENTITY_VERSION
        assert CODE_OUT_OF_SCOPE_IDENTITY_VERSION in result["mismatches"]

    @pytest.mark.parametrize("bad_version", [0, 1, 3, 4, -1, "1", "3", "v2", "02"])
    def test_any_out_of_scope_version_fails(self, tmp_path, bad_version):
        """CONSTRUCTED / ADVERSARIAL — 白名单外 `identity_version` 取值一律拒绝。"""
        result = _boundary_rejects(tmp_path, bad_version)

        assert result["gate"] == GATE_BLOCK
        assert result["interface_scope"]["code"] == CODE_OUT_OF_SCOPE_IDENTITY_VERSION

    def test_valid_identity_and_missing_version_fails(self, tmp_path):
        """CONSTRUCTED / ADVERSARIAL — 合法身份 + 未声明 identity_version → FAIL。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK)  # 不写 identity_version
        ir = _write_ir(tmp_path, SHA_OK)

        result = _verify_identity_boundary(manifest, source, ir)

        assert result["identity_state"] == "VERIFIED"
        assert result["gate"] == GATE_BLOCK
        assert result["interface_scope"]["code"] == CODE_MISSING_IDENTITY_VERSION

    def test_valid_identity_and_null_version_fails(self, tmp_path):
        """CONSTRUCTED / ADVERSARIAL — 合法身份 + `identity_version: null` → FAIL。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OK, identity_version=None)
        ir = _write_ir(tmp_path, SHA_OK)

        result = _verify_identity_boundary(manifest, source, ir)

        assert result["gate"] == GATE_BLOCK
        assert result["interface_scope"]["code"] == CODE_MISSING_IDENTITY_VERSION

    def test_missing_identity_fails(self, tmp_path):
        """missing identity → FAIL。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, identity_version=2)  # 不写 sha
        ir = _write_ir(tmp_path, SHA_OK)

        result = _verify_identity_boundary(manifest, source, ir)

        assert result["gate"] == GATE_BLOCK
        assert result["interface_scope"]["code"] == CODE_MISSING_IDENTITY

    def test_identity_mismatch_fails(self, tmp_path):
        """invalid SHA / identity mismatch → FAIL（实算字节 ≠ 声明值）。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha=SHA_OTHER, identity_version=2)
        ir = _write_ir(tmp_path, SHA_OTHER)

        result = _verify_identity_boundary(manifest, source, ir)

        assert result["gate"] == GATE_BLOCK
        assert result["identity_state"] == "FAILED"

    def test_malformed_identity_fails(self, tmp_path):
        """格式非法的 `source_content_sha256` → FAIL（M1 读取层即拒绝）。"""
        source = _write_source(tmp_path)
        manifest = _write_manifest(tmp_path, sha="NOT-A-SHA256", identity_version=2)

        result = _verify_identity_boundary(manifest, source, None)

        assert result["gate"] == GATE_BLOCK
        assert result["reason"].startswith("manifest_read_error")

    def test_malformed_identity_rejected_by_authority(self):
        """同一事实由边界权威以 `MALFORMED_IDENTITY` 拒绝（判定只有一套）。"""
        decision = enforce_interface_scope("NOT-A-SHA256", 2)

        assert decision.accepted is False
        assert decision.code == CODE_MALFORMED_IDENTITY


# ═══════════════════════════════════════════════════════════════
# §2 禁止静默强制转换（No Silent Repair）
# ═══════════════════════════════════════════════════════════════


class TestNoSilentCoercion:
    """禁止 `version != 2 → 当成 v2`，禁止 `version != 2 → fallback → 继续运行`。"""

    @pytest.mark.parametrize("bad_version", [1, 3])
    def test_out_of_scope_version_is_not_coerced_to_2(self, bad_version):
        """authority 对越界版本**不产出** canonical `identity_version="2"`。"""
        decision = enforce_interface_scope(SHA_OK, bad_version)

        assert decision.accepted is False
        assert decision.identity is None  # 不产出任何「已归一化」身份
        assert decision.code == CODE_OUT_OF_SCOPE_IDENTITY_VERSION

    @pytest.mark.parametrize("bad_version", [1, 3])
    def test_authority_raises_rather_than_defaulting(self, bad_version):
        """fail-loud 权威 `normalize_interface_identity` 直接上抛，不给默认值。"""
        with pytest.raises(Exception) as e:
            normalize_interface_identity(SHA_OK, bad_version)
        assert e.value.code == CODE_OUT_OF_SCOPE_IDENTITY_VERSION

    def test_missing_version_is_not_defaulted_to_2(self):
        """未声明版本不得被默认为 2。"""
        decision = enforce_interface_scope(SHA_OK, None)

        assert decision.accepted is False
        assert decision.identity is None
        assert decision.code == CODE_MISSING_IDENTITY_VERSION

    def test_producer_declaration_is_preserved_verbatim(self, tmp_path):
        """§9 Provenance：拒绝时仍保留 Producer 原始声明值，不改写、不清洗。"""
        result = _boundary_rejects(tmp_path, 1)

        assert result["interface_scope"]["declared_identity_version"] == 1

    def test_accepted_identity_carries_canonical_version_2(self):
        """仅接受路径产出 canonical `identity_version == "2"`。"""
        decision = enforce_interface_scope(SHA_OK, 2)

        assert decision.accepted is True
        assert decision.identity is not None
        assert decision.identity.identity_version == "2"
        assert decision.identity.source_content_sha256 == SHA_OK


# ═══════════════════════════════════════════════════════════════
# §6 失败发生在边界（不是 V3 内部补救）
# ═══════════════════════════════════════════════════════════════


class TestFailureOccursAtBoundary:
    """`identity_version != 2` 必须在进入 IR/Compiler/Gate **之前**失败。"""

    @pytest.mark.parametrize("bad_version", [1, 3, _OMIT])
    def test_gate_blocks_and_downstream_never_runs(self, tmp_path, bad_version):
        """CONSTRUCTED / ADVERSARIAL — 边界拒绝后 IRBuilder/Compiler/Gate 零调用。"""
        source = _write_source(tmp_path)
        manifest_path = _write_manifest(
            tmp_path,
            sha=SHA_OK,
            **({} if bad_version is _OMIT else {"identity_version": bad_version}),
        )
        ir = _write_ir(tmp_path, SHA_OK)

        gate_decision = _verify_identity_boundary(manifest_path, source, ir)
        assert gate_decision["gate"] == GATE_BLOCK
        assert gate_decision["identity_state"] == "VERIFIED"  # M1–M5 已通过

        from scripts.preprocessing_consumer.manifest_reader import load_manifest

        manifest = load_manifest(manifest_path)

        with patch(
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
            result = asyncio.run(
                _run_full_chain(
                    MagicMock(), manifest, [], source,
                    gate_decision=gate_decision,
                )
            )

        assert result["status"] == "identity_blocked"
        assert result["downstream_executed"] is False
        # §6 证明：V3 semantic consumption **完全未执行**
        assert mock_create.call_count == 0
        assert mock_ir.call_count == 0
        assert mock_compiler.call_count == 0
        assert mock_evaluate.call_count == 0
        assert mock_payload.call_count == 0

    @pytest.mark.parametrize("bad_version", [1, 3])
    def test_real_runner_rejects_before_any_v3_consumption(self, tmp_path, bad_version):
        """CONSTRUCTED / ADVERSARIAL — 经**真实** `run_corpus` 入口证明边界优先。"""
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
            asyncio.run(run_corpus(corpus, out, resolver_ir_path=ir))

        report = json.loads(out.read_text(encoding="utf-8"))
        paper = report["papers"][0]["result"]
        assert report["summary"]["identity_blocked"] == 1
        assert report["summary"]["completed"] == 0
        assert paper["downstream_executed"] is False
        # 拒绝原因必须是 Interface Scope 而非身份真实性失败
        assert paper["identity_gate"]["identity_state"] == "VERIFIED"
        assert paper["identity_gate"]["interface_scope"]["code"] == (
            CODE_OUT_OF_SCOPE_IDENTITY_VERSION
        )
        assert mock_chain.call_count == 0
        assert mock_create.call_count == 0
        assert mock_ir.call_count == 0
        assert mock_compiler.call_count == 0
        assert mock_evaluate.call_count == 0
        assert mock_payload.call_count == 0

    def test_boundary_module_does_not_import_v3_pipeline(self):
        """`boundary.py` 不 import IR/Compiler/Gate/Admission —— 属 Interface Boundary 判定。"""
        src = (_BACKEND / "scripts" / "preprocessing_consumer" / "boundary.py")
        import_lines = [
            ln for ln in src.read_text(encoding="utf-8").splitlines()
            if ln.startswith(("import ", "from "))
        ]
        for ln in import_lines:
            for forbidden in (
                "compile.ir", "compiler", "domains.gate", "admission",
                "mapping_registry",
            ):
                assert forbidden not in ln, f"boundary.py must not import {forbidden}: {ln}"

    def test_enforcement_is_not_reimplemented_inside_app(self):
        """判定不得在 V3 IR / Compiler / Gate（或任何 app 域）内重复实现。"""
        hits = []
        for p in (_BACKEND / "app").rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            if "enforce_interface_scope" in text or "normalize_interface_identity" in text:
                hits.append(str(p.relative_to(_BACKEND)))
        assert hits == [], f"second identity validation system detected: {hits}"


# ═══════════════════════════════════════════════════════════════
# F-INT-01 单一接入点 / 单一权威
# ═══════════════════════════════════════════════════════════════


class TestSingleAuthorityEntry:
    """一个 boundary authority → 所有 runtime runner 入口 → 统一执行。"""

    def _read(self, rel: str) -> str:
        return (_BACKEND / rel).read_text(encoding="utf-8")

    def test_both_runtime_runners_call_the_single_entry_point(self):
        """runner_b2 与 runner.py 均接入 `enforce_interface_scope`（无 bypass）。"""
        for rel in (
            "scripts/preprocessing_consumer/runner_b2.py",
            "scripts/preprocessing_consumer/runner.py",
        ):
            assert "enforce_interface_scope" in self._read(rel), rel

    def test_normalize_interface_identity_has_one_production_call_site(self):
        """判定逻辑只有一处调用（`enforce_interface_scope` 内），无平行实现。"""
        call_sites = []
        for p in sorted((_BACKEND / "scripts").rglob("*.py")):
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if line.strip().startswith(("def ", "#", "*", '"', "'")):
                    continue  # 定义行 / 注释 / docstring
                if "normalize_interface_identity(" in line:
                    call_sites.append(f"{p.name}:{i}")
        assert len(call_sites) == 1, f"single authority call site required: {call_sites}"
        assert call_sites[0].startswith("boundary.py:"), call_sites

    def test_interface_scope_gate_runs_before_semantic_consumption_in_runner_b2(self):
        """源码顺序：边界闸门先于 `_run_full_chain`（IR/Compiler/Gate 在其内）。"""
        src = self._read("scripts/preprocessing_consumer/runner_b2.py")
        assert src.index("gate_decision = _verify_identity_boundary(") < (
            src.index("r = await _run_full_chain(")
        )

    def test_interface_scope_gate_runs_before_gate_service_in_runner(self):
        """源码顺序：边界闸门先于 Track A 的生产 `GateService.run`。"""
        src = self._read("scripts/preprocessing_consumer/runner.py")
        assert src.index("scope = enforce_interface_scope(") < src.index("ta = await _track_a(")


# ═══════════════════════════════════════════════════════════════
# §11 Real Corpus 针对性验证（真实语料 ≠ 构造样本，分开报告）
# ═══════════════════════════════════════════════════════════════


@pytest.mark.skipif(
    not _PAPERS_ROOT.exists(),
    reason="Papers corpus not available on this machine",
)
class TestRealCorpusTargeted:
    """真实 Papers corpus：只验证 v2 子集被接受、缺失子集被拒绝。

    **不**声称真实语料覆盖 version 1/3 —— 实测语料中该类样本数为 0
    （见 `test_corpus_contains_no_version_1_or_3_samples`）。version 1/3 的
    覆盖由 TestBehaviorMatrix 的 `CONSTRUCTED / ADVERSARIAL` 用例承担。
    """

    def _iter_manifests(self):
        for p in sorted(_PAPERS_ROOT.rglob("*.manifest.json")):
            if ".pytest_work" in p.parts or "_archive" in p.parts:
                continue
            yield p

    def test_corpus_contains_no_version_1_or_3_samples(self):
        """真实语料中 `identity_version ∈ {1,3}` 样本数为 0 —— 不伪造覆盖。"""
        offenders = []
        for p in self._iter_manifests():
            raw = json.loads(p.read_text(encoding="utf-8"))
            v = raw.get("identity_version") if isinstance(raw, dict) else None
            if v in (1, 3, "1", "3"):
                offenders.append(str(p))
        assert offenders == [], (
            "unexpected real-corpus version 1/3 samples; report them as real "
            f"corpus evidence instead of constructed: {offenders[:5]}"
        )

    def test_real_corpus_version_2_subset_is_accepted(self):
        """真实语料中声明 `identity_version == 2` 的 manifest 全部通过边界。"""
        accepted = 0
        rejected = []
        for p in self._iter_manifests():
            raw = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                continue
            if raw.get("identity_version") not in (2, "2"):
                continue
            decision = enforce_interface_scope(
                raw.get("source_content_sha256"), raw.get("identity_version")
            )
            if decision.accepted:
                accepted += 1
            else:
                rejected.append((str(p), decision.code))
        assert accepted > 0, "expected an identity_version=2 subset in the real corpus"
        assert rejected == [], f"v2 manifests must pass the boundary: {rejected[:5]}"

    def test_real_corpus_undeclared_version_subset_is_rejected(self):
        """真实语料中未声明 `identity_version` 的 manifest 全部被拒绝（不默认为 2）。"""
        rejected = 0
        wrongly_accepted = []
        for p in self._iter_manifests():
            raw = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                continue
            if raw.get("identity_version") in (2, "2"):
                continue
            decision = enforce_interface_scope(
                raw.get("source_content_sha256"), raw.get("identity_version")
            )
            if decision.accepted:
                wrongly_accepted.append(str(p))
            else:
                rejected += 1
                assert decision.code in (
                    CODE_MISSING_IDENTITY,
                    CODE_MISSING_IDENTITY_VERSION,
                    CODE_MALFORMED_IDENTITY,
                ), decision.code
        assert wrongly_accepted == [], (
            f"undeclared identity_version must never pass: {wrongly_accepted[:5]}"
        )
        assert rejected > 0
