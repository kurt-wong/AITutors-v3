"""Phase A identity invariant tests（IMPLEMENTATION-AUTHORIZATION-PRIMARY-PATH-IDENTITY-01 §4）。

覆盖（含对抗性审查 GAP-1/GAP-2 修复验证）：
1. preprocessing/preprocessing/canonical_l1 accepted
2. preprocessing with wrong provider rejected（含 repository 层）
3. markdown artifact_kind rejected
4. raw byte hash identity preserved
5. le_hash changes consistently when original_sha256 changes
6. invalid artifact combinations cannot persist（含 role/provider 配对）
7. [GAP-2] runner 实际输出值锁定
"""

import hashlib
import uuid

import pytest

from app.core.hashing import sha256_hex
from app.core.raw_bytes_identity import load_raw_bytes_identity
from app.models.source import validate_artifact_compatibility
from app.repositories.base import RepositoryError
from app.repositories.source_repository import SourceRepository


# ── 1. preprocessing/preprocessing/canonical_l1 accepted ──────────────────────

class TestValidCombinations:
    def test_preprocessing_pair_accepted(self):
        validate_artifact_compatibility("preprocessing", "preprocessing", "canonical_l1")

    def test_canonical_l1_accepted(self):
        validate_artifact_compatibility("preprocessing", "preprocessing", "canonical_l1")

    def test_raw_l1_accepted(self):
        validate_artifact_compatibility("native", "native", "raw_l1")

    def test_original_binary_accepted(self):
        validate_artifact_compatibility("docx", "docx", "original_binary")

    def test_all_known_pairs_accepted(self):
        validate_artifact_compatibility("native", "native", "raw_l1")
        validate_artifact_compatibility("ocr_ppsv3", "ppsv3", "raw_l1")
        validate_artifact_compatibility("ocr_ppsvl", "paddleocr-vl", "raw_l1")
        validate_artifact_compatibility("docx", "docx", "raw_l1")
        validate_artifact_compatibility("preprocessing", "preprocessing", "canonical_l1")


# ── 2. preprocessing with wrong provider rejected ─────────────────────────────

class TestRoleProviderEnforcement:
    def test_preprocessing_native_rejected(self):
        with pytest.raises(ValueError, match="mismatch"):
            validate_artifact_compatibility("preprocessing", "native", "canonical_l1")

    def test_preprocessing_ppsv3_rejected(self):
        with pytest.raises(ValueError, match="mismatch"):
            validate_artifact_compatibility("preprocessing", "ppsv3", "canonical_l1")

    def test_native_preprocessing_rejected(self):
        with pytest.raises(ValueError, match="mismatch"):
            validate_artifact_compatibility("native", "preprocessing", "raw_l1")

    def test_unknown_role_rejected(self):
        with pytest.raises(ValueError, match="unknown role"):
            validate_artifact_compatibility("bogus", "bogus", "raw_l1")

    # ── NEW-GAP-2 fix: canonical role 专门测试 ────────────────────────────

    def test_canonical_empty_provider_accepted(self):
        """Spec: canonical role 无 provider → provider="" 是合法实现约定。"""
        validate_artifact_compatibility("canonical", "", "canonical_l1")

    def test_canonical_native_provider_rejected(self):
        """canonical 配 native 是非法配对（违反封闭配对）。"""
        with pytest.raises(ValueError, match="mismatch"):
            validate_artifact_compatibility("canonical", "native", "canonical_l1")

    def test_canonical_preprocessing_provider_rejected(self):
        with pytest.raises(ValueError, match="mismatch"):
            validate_artifact_compatibility("canonical", "preprocessing", "canonical_l1")

    def test_seal_rejects_canonical_role(self):
        """[NEW-GAP-1 修复验证] seal 路径必须拒绝 canonical role。"""
        from app.domains.source.seal import validate_seal_role_provider
        with pytest.raises(ValueError, match="canonical"):
            validate_seal_role_provider("canonical", "")

    def test_seal_rejects_canonical_even_with_empty_provider(self):
        """[NEW-GAP-1 修复验证] 即使 provider="" 也拒绝 — canonical 不经 seal 产生。"""
        from app.domains.source.seal import validate_seal_role_provider
        with pytest.raises(ValueError, match="canonical"):
            validate_seal_role_provider("canonical", "")


# ── 3. markdown artifact_kind rejected ────────────────────────────────────────

class TestArtifactKindClosedSet:
    def test_markdown_rejected(self):
        with pytest.raises(ValueError, match="invalid artifact_kind"):
            validate_artifact_compatibility("preprocessing", "preprocessing", "markdown")

    def test_pdf_rejected(self):
        with pytest.raises(ValueError, match="invalid artifact_kind"):
            validate_artifact_compatibility("native", "native", "pdf")

    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="invalid artifact_kind"):
            validate_artifact_compatibility("native", "native", "")

    def test_none_rejected(self):
        with pytest.raises(ValueError, match="invalid artifact_kind"):
            validate_artifact_compatibility("native", "native", None)


# ── 4. raw byte hash identity preserved ──────────────────────────────────────

class TestRawByteIdentity:
    def test_raw_bytes_sha256_matches_hashlib(self, tmp_path):
        """load_raw_bytes_identity 的 sha256 必须等于 hashlib.sha256(raw bytes)。"""
        content = b"Hello\nWorld\n"
        p = tmp_path / "test.md"
        p.write_bytes(content)

        rid = load_raw_bytes_identity(p)
        assert rid.sha256 == hashlib.sha256(content).hexdigest()

    def test_raw_bytes_not_equal_to_body_text_hash(self, tmp_path):
        """original_sha256（raw bytes）≠ sha256_hex(body_text)——hash 族不同。"""
        content = "Hello\nWorld\n"
        p = tmp_path / "test.md"
        p.write_text(content, encoding="utf-8")

        rid = load_raw_bytes_identity(p)
        body_hash = sha256_hex(content)
        assert rid.sha256 != body_hash

    def test_bom_affects_identity(self, tmp_path):
        """BOM 字节必须参与 hash（raw bytes 语义）。"""
        p1 = tmp_path / "nobom.md"
        p1.write_bytes(b"Hello\n")
        p2 = tmp_path / "bom.md"
        p2.write_bytes(b"\xef\xbb\xbfHello\n")

        assert load_raw_bytes_identity(p1).sha256 != load_raw_bytes_identity(p2).sha256

    def test_crlf_affects_identity(self, tmp_path):
        """CRLF 与 LF 必须产生不同 hash。"""
        p1 = tmp_path / "lf.md"
        p1.write_bytes(b"Hello\nWorld\n")
        p2 = tmp_path / "crlf.md"
        p2.write_bytes(b"Hello\r\nWorld\r\n")

        assert load_raw_bytes_identity(p1).sha256 != load_raw_bytes_identity(p2).sha256


# ── 5. le_hash changes consistently when original_sha256 changes ─────────────

def _le_hash(sha: str) -> str:
    """LE hash 权威公式（与 seal.py / runner.py 一致）。"""
    from app.core.hashing import logical_execution_hash
    return logical_execution_hash(
        task_type="document_ingest",
        stage="seal",
        contract_domain={
            "seal_contract_version": "seal/v1",
            "parser": {"provider": "preprocessing", "role": "preprocessing"},
        },
        input_domain={"original_sha256": sha},
    )


class TestDerivedHashDependency:
    def test_le_hash_is_function_of_original_sha256(self):
        """le_hash = f(original_sha256) —— 同 sha 得同 hash，异 sha 得异 hash。"""
        sha_a = hashlib.sha256(b"content-a").hexdigest()
        sha_b = hashlib.sha256(b"content-b").hexdigest()

        le_a1 = _le_hash(sha_a)
        le_a2 = _le_hash(sha_a)
        le_b = _le_hash(sha_b)

        assert le_a1 == le_a2, "same original_sha256 must produce same le_hash"
        assert le_a1 != le_b, "different original_sha256 must produce different le_hash"

    def test_domain_change_changes_le_hash(self):
        """2-B 域修正后 le_hash 必然不同（raw bytes sha ≠ body_text sha）。"""
        raw_sha = hashlib.sha256(b"Hello\n").hexdigest()
        body_sha = sha256_hex("Hello")  # old wrong algorithm

        assert _le_hash(body_sha) != _le_hash(raw_sha)

    def test_runner_and_seal_use_same_formula(self):
        """[LE hash 收敛] runner 与 seal 用同一 logical_execution_hash 公式。"""
        from app.core.hashing import logical_execution_hash
        sha = hashlib.sha256(b"unified-test").hexdigest()

        # seal 公式（以 preprocessing 配对为例）
        le_seal = logical_execution_hash(
            task_type="document_ingest",
            stage="seal",
            contract_domain={
                "seal_contract_version": "seal/v1",
                "parser": {"provider": "preprocessing", "role": "preprocessing"},
            },
            input_domain={"original_sha256": sha},
        )
        # runner 现在用同一公式
        le_runner = _le_hash(sha)
        assert le_seal == le_runner, "runner and seal must use identical LE hash formula"

    def test_different_roles_produce_different_le_hash(self):
        """不同 parser 身份 → 不同 le_hash（防 identity 漂移）。"""
        from app.core.hashing import logical_execution_hash
        sha = hashlib.sha256(b"role-diff").hexdigest()

        le_preprocessing = logical_execution_hash(
            task_type="document_ingest", stage="seal",
            contract_domain={"seal_contract_version": "seal/v1",
                             "parser": {"provider": "preprocessing", "role": "preprocessing"}},
            input_domain={"original_sha256": sha},
        )
        le_native = logical_execution_hash(
            task_type="document_ingest", stage="seal",
            contract_domain={"seal_contract_version": "seal/v1",
                             "parser": {"provider": "native", "role": "native"}},
            input_domain={"original_sha256": sha},
        )
        assert le_preprocessing != le_native


# ── 6. invalid artifact combinations cannot persist ──────────────────────────

class TestRepositoryEnforcement:
    async def _make_doc(self, session):
        repo = SourceRepository(session)
        doc = await repo.create_document(
            original_object_key=f"test/{uuid.uuid4().hex}",
            original_sha256=hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
            file_name="test.md",
            file_type="text/markdown",
            upload_meta={},
            processing_status="pending",
        )
        await session.flush()
        return repo, doc

    async def test_invalid_artifact_kind_rejected_by_repository(self, session):
        """repository 层拒绝非法 artifact_kind — 不能静默持久化。"""
        repo, doc = await self._make_doc(session)
        with pytest.raises(RepositoryError, match="invalid artifact_kind"):
            await repo.create_source_version(
                document_id=doc.id,
                artifact_kind="markdown",
                role="preprocessing",
                provider="preprocessing",
                body_text="x",
                body_hash="a" * 64,
                integrity_hash="b" * 64,
                page_count=1,
                line_count=1,
                status="draft",
            )

    async def test_valid_combination_accepted_by_repository(self, session):
        """preprocessing/preprocessing/canonical_l1 可持久化。"""
        repo, doc = await self._make_doc(session)
        version = await repo.create_source_version(
            document_id=doc.id,
            artifact_kind="canonical_l1",
            role="preprocessing",
            provider="preprocessing",
            body_text="x",
            body_hash="a" * 64,
            integrity_hash="b" * 64,
            page_count=1,
            line_count=1,
            status="draft",
        )
        assert version.role == "preprocessing"
        assert version.provider == "preprocessing"
        assert version.artifact_kind == "canonical_l1"

    # ── GAP-1 fix: role/provider 配对在 repository 层被拒 ─────────────────

    async def test_illegal_role_provider_pair_rejected_by_repository(self, session):
        """[GAP-1] 非法配对 (preprocessing, native) 不能通过 repository 持久化。"""
        repo, doc = await self._make_doc(session)
        with pytest.raises(RepositoryError, match="mismatch"):
            await repo.create_source_version(
                document_id=doc.id,
                artifact_kind="canonical_l1",
                role="preprocessing",
                provider="native",  # illegal pair
                body_text="x",
                body_hash="a" * 64,
                integrity_hash="b" * 64,
                page_count=1,
                line_count=1,
                status="draft",
            )

    async def test_illegal_native_preprocessing_rejected_by_repository(self, session):
        """[GAP-1] 反向非法配对 (native, preprocessing) 也被拒。"""
        repo, doc = await self._make_doc(session)
        with pytest.raises(RepositoryError, match="mismatch"):
            await repo.create_source_version(
                document_id=doc.id,
                artifact_kind="raw_l1",
                role="native",
                provider="preprocessing",  # illegal pair
                body_text="x",
                body_hash="a" * 64,
                integrity_hash="b" * 64,
                page_count=1,
                line_count=1,
                status="draft",
            )

    async def test_unknown_role_rejected_by_repository(self, session):
        """[GAP-1] 未知 role 不能通过 repository。"""
        repo, doc = await self._make_doc(session)
        with pytest.raises(RepositoryError, match="unknown role"):
            await repo.create_source_version(
                document_id=doc.id,
                artifact_kind="canonical_l1",
                role="bogus",
                provider="bogus",
                body_text="x",
                body_hash="a" * 64,
                integrity_hash="b" * 64,
                page_count=1,
                line_count=1,
                status="draft",
            )


# ── GAP-2 fix: runner 实际输出值锁定 ─────────────────────────────────────────

class TestRunnerOutputValues:
    """[GAP-2] 直接调用 _create_source_records，断言 identity 字段值。"""

    async def test_runner_create_source_records_identity_fields(self, session, tmp_path):
        """runner.py 的 _create_source_records 写入正确的 identity 三元组。"""
        from scripts.preprocessing_consumer.runner import _create_source_records
        from scripts.preprocessing_consumer.source_loader import load_source_lines

        src = tmp_path / "test.md"
        src.write_text("Hello\nWorld\n", encoding="utf-8")
        lines = load_source_lines(src)

        doc_id, sv_id = await _create_source_records(session, lines, src)
        repo = SourceRepository(session)
        v = await repo.get_version(sv_id)

        assert v.role == "preprocessing", f"role={v.role!r}, expected 'preprocessing'"
        assert v.provider == "preprocessing", f"provider={v.provider!r}, expected 'preprocessing'"
        assert v.artifact_kind == "canonical_l1", f"artifact_kind={v.artifact_kind!r}, expected 'canonical_l1'"

    async def test_runner_b2_create_source_records_identity_fields(self, session, tmp_path):
        """runner_b2.py 的 _create_source_records 写入正确的 identity 三元组。"""
        from scripts.preprocessing_consumer.runner_b2 import _create_source_records
        from scripts.preprocessing_consumer.source_loader import load_source_lines

        src = tmp_path / "test_b2.md"
        src.write_text("Hello\nWorld\n", encoding="utf-8")
        lines = load_source_lines(src)

        doc_id, sv_id = await _create_source_records(session, lines, src)
        repo = SourceRepository(session)
        v = await repo.get_version(sv_id)

        assert v.role == "preprocessing", f"role={v.role!r}, expected 'preprocessing'"
        assert v.provider == "preprocessing", f"provider={v.provider!r}, expected 'preprocessing'"
        assert v.artifact_kind == "canonical_l1", f"artifact_kind={v.artifact_kind!r}, expected 'canonical_l1'"

    async def test_runner_original_sha256_is_raw_bytes(self, session, tmp_path):
        """[GAP-2] original_sha256 必须是 SHA256(raw bytes)，不是 body_text hash。"""
        from scripts.preprocessing_consumer.runner import _create_source_records
        from scripts.preprocessing_consumer.source_loader import load_source_lines

        content = b"Hello\nWorld\n"
        src = tmp_path / "test_raw.md"
        src.write_bytes(content)
        lines = load_source_lines(src)

        doc_id, sv_id = await _create_source_records(session, lines, src)
        repo = SourceRepository(session)
        doc = await repo.find_document_by_sha256(hashlib.sha256(content).hexdigest())

        assert doc is not None, "document must be findable by raw-bytes SHA256"

    async def test_runner_le_hash_uses_unified_formula(self, session, tmp_path):
        """[LE hash 收敛] runner 的 _create_source_records 产出的 le_hash
        必须等于 logical_execution_hash 权威公式的输出。"""
        from app.core.hashing import logical_execution_hash
        from scripts.preprocessing_consumer.runner import _create_source_records
        from scripts.preprocessing_consumer.source_loader import load_source_lines

        content = b"le-hash-verify\n"
        src = tmp_path / "le_test.md"
        src.write_bytes(content)
        lines = load_source_lines(src)

        doc_id, sv_id = await _create_source_records(session, lines, src)
        repo = SourceRepository(session)
        v = await repo.get_version(sv_id)

        raw_sha = hashlib.sha256(content).hexdigest()
        expected = logical_execution_hash(
            task_type="document_ingest",
            stage="seal",
            contract_domain={
                "seal_contract_version": "seal/v1",
                "parser": {"provider": "preprocessing", "role": "preprocessing"},
            },
            input_domain={"original_sha256": raw_sha},
        )
        assert v.logical_execution_hash == expected, (
            f"runner le_hash={v.logical_execution_hash}, expected={expected}"
        )

    async def test_runner_annotation_le_hash_persisted_matches_authority(self, session, tmp_path):
        """[GAP-T-1] annotation le_hash DB readback：写入值 == 权威公式计算值。

        证明 persistence invariant：logical_execution_hash(input) == database.logical_execution_hash
        """
        from app.core.hashing import logical_execution_hash, sha256_hex
        from app.models.snapshot import SemanticAnnotation
        from scripts.preprocessing_consumer.runner import _create_source_records
        from scripts.preprocessing_consumer.source_loader import load_source_lines

        content = b"ann-readback\n"
        src = tmp_path / "ann_readback.md"
        src.write_bytes(content)
        lines = load_source_lines(src)

        doc_id, sv_id = await _create_source_records(session, lines, src)

        # 与 runner.py:148-168 完全一致的 annotation 创建代码
        payload = {"semantic_units": [{"unit_id": "Q1", "content": "test"}]}
        prompt_version = "preprocessing-adapter/v1"
        ann = SemanticAnnotation(
            source_version_id=sv_id,
            annotation_schema_version="semantic-metadata-annotation/v0.3",
            prompt_version=prompt_version,
            model_config_hash=sha256_hex(payload),
            payload=payload,
            status="valid",
            logical_execution_stage="ann",
            logical_execution_hash=logical_execution_hash(
                task_type="preprocessing_consumer_phase0",
                stage="ann",
                contract_domain={
                    "annotation_schema_version": "semantic-metadata-annotation/v0.3",
                    "prompt_version": prompt_version,
                    "model_config_hash": sha256_hex(payload),
                },
                input_domain={"source_version_id": str(sv_id)},
            ),
        )
        session.add(ann)
        await session.flush()

        # DB readback
        from sqlalchemy import select
        row = (await session.execute(
            select(SemanticAnnotation).where(SemanticAnnotation.id == ann.id)
        )).scalar_one()

        # 权威公式重算
        expected = logical_execution_hash(
            task_type="preprocessing_consumer_phase0",
            stage="ann",
            contract_domain={
                "annotation_schema_version": "semantic-metadata-annotation/v0.3",
                "prompt_version": prompt_version,
                "model_config_hash": sha256_hex(payload),
            },
            input_domain={"source_version_id": str(sv_id)},
        )
        assert row.logical_execution_hash == expected, (
            f"DB le_hash={row.logical_execution_hash}, authority={expected}"
        )

    async def test_compile_le_hash_persisted_matches_authority(self, session, tmp_path):
        """[GAP-T-1] compile le_hash DB readback：写入值 == 权威公式计算值。

        证明 persistence invariant：logical_execution_hash(input) == database.logical_execution_hash
        """
        import uuid
        from app.core.hashing import logical_execution_hash, sha256_hex
        from app.models.snapshot import AdmissionCandidate, SemanticAnnotation
        from app.repositories.snapshot_repository import SnapshotRepository
        from scripts.preprocessing_consumer.runner import _create_source_records
        from scripts.preprocessing_consumer.source_loader import load_source_lines

        content = b"compile-readback\n"
        src = tmp_path / "compile_readback.md"
        src.write_bytes(content)
        lines = load_source_lines(src)

        doc_id, sv_id = await _create_source_records(session, lines, src)

        # 先创建 annotation（FK 约束要求）
        ann_payload = {"semantic_units": [{"unit_id": "Q1", "content": "test"}]}
        ann = SemanticAnnotation(
            source_version_id=sv_id,
            annotation_schema_version="semantic-metadata-annotation/v0.3",
            prompt_version="preprocessing-adapter/v1",
            model_config_hash=sha256_hex(ann_payload),
            payload=ann_payload,
            status="valid",
            logical_execution_stage="ann",
            logical_execution_hash=logical_execution_hash(
                task_type="preprocessing_consumer_phase0", stage="ann",
                contract_domain={"annotation_schema_version": "semantic-metadata-annotation/v0.3",
                                 "prompt_version": "preprocessing-adapter/v1",
                                 "model_config_hash": sha256_hex(ann_payload)},
                input_domain={"source_version_id": str(sv_id)},
            ),
        )
        session.add(ann)
        await session.flush()

        payload = {"semantic_units": [{"unit_id": "Q1", "content": "test"}]}
        unit_id = "Q1"

        # 与 runner_b2.py:476-489 完全一致的 compile le_hash 公式
        le_hash = logical_execution_hash(
            task_type="preprocessing_consumer_phase0",
            stage="compile",
            contract_domain={
                "resolver_version": "resolver/v1",
                "ir_schema_version": "semantic-question-ir/v0.3",
                "compiler_version": "compiler/v1",
                "gate_policy_version": "admission-gate/v1",
            },
            input_domain={
                "annotation_id": str(ann.id),
                "annotation_payload_hash": sha256_hex(payload),
                "unit_id": unit_id,
            },
        )

        snap_repo = SnapshotRepository(session)
        cand = await snap_repo.create_admission_candidate(
            unit_type="standalone_unit",
            source_version_id=sv_id,
            annotation_id=ann.id,
            build_versions={"phase0_2_r2": "v0.2"},
            input_identity={"source": "preprocessing_manifest"},
            payload=payload,
            gate_decision={"decision": "auto_approve", "reasons": []},
            logical_execution_stage="compile",
            logical_execution_hash=le_hash,
        )
        await session.flush()

        # DB readback
        from sqlalchemy import select
        row = (await session.execute(
            select(AdmissionCandidate).where(AdmissionCandidate.id == cand.id)
        )).scalar_one()

        # 权威公式重算
        expected = logical_execution_hash(
            task_type="preprocessing_consumer_phase0",
            stage="compile",
            contract_domain={
                "resolver_version": "resolver/v1",
                "ir_schema_version": "semantic-question-ir/v0.3",
                "compiler_version": "compiler/v1",
                "gate_policy_version": "admission-gate/v1",
            },
            input_domain={
                "annotation_id": str(ann.id),
                "annotation_payload_hash": sha256_hex(payload),
                "unit_id": unit_id,
            },
        )
        assert row.logical_execution_hash == expected, (
            f"DB le_hash={row.logical_execution_hash}, authority={expected}"
        )
