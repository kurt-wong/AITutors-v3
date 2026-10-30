"""B3-2/B3-3 入口契约测试（Owner 2026-10-29：preprocessing-only）。

证明：
- 原始文件导入被显式拒绝（不再创建 document_ingest / LLM 重切旁路）。
- executor._annotation_stage 缺契约参数显式失败（EntryContractError），不再静默走 LLM 重切。
- preprocessing 重复导入幂等（不重复建 Task）；同原件异内容显式冲突；身份缺失 fail-closed。
- 全程 NativeTextProvider 零调用。
"""

from __future__ import annotations

import hashlib
import uuid

import pytest
from sqlalchemy import func, select, text

from app.ai.ocr.preprocessing_provider import PreprocessingTextExtractor
from app.domains.source.import_service import DocumentImportService, ImportError_
from app.domains.source.preprocessing_import import (
    PreprocessingImportError,
    PreprocessingImportService,
    PreprocessingPackage,
)
from app.domains.task.executor import EntryContractError, TaskExecutor

MD_BODY = "# 试卷\n\n1. 题干\nA. 选项A\nB. 选项B\n"
PDF_BYTES = b"%PDF-1.4 b3-entry-original-bytes"


def _pkg(
    md: bytes | None = None,
    manifest: dict | None = None,
    pdf: bytes | None = None,
) -> PreprocessingPackage:
    body = MD_BODY.encode("utf-8") if md is None else md
    if manifest is None:
        manifest = {
            "source_content_sha256": hashlib.sha256(body).hexdigest(),
            "identity_version": 2,
        }
    return PreprocessingPackage(
        original_bytes=PDF_BYTES if pdf is None else pdf,
        original_name="exam.pdf",
        source_md=body,
        manifest=manifest,
    )


async def _async_return(value):
    return value


async def _boom(msg):
    raise AssertionError(msg)


class TestRawImportEntryBlocked:
    @pytest.mark.asyncio
    async def test_new_raw_file_rejected(self, session):
        from app.models.runtime import Task
        from app.models.source import Document

        n_docs_before = (
            await session.execute(select(func.count()).select_from(Document))
        ).scalar()
        n_tasks_before = (
            await session.execute(select(func.count()).select_from(Task))
        ).scalar()

        svc = DocumentImportService(session)
        with pytest.raises(ImportError_) as ei:
            await svc.import_file(
                file_bytes=PDF_BYTES + b"-raw-block", file_name="exam.pdf"
            )
        assert "explicit-entry policy" in str(ei.value)
        assert "no silent reroute" in str(ei.value)

        n_docs_after = (
            await session.execute(select(func.count()).select_from(Document))
        ).scalar()
        n_tasks_after = (
            await session.execute(select(func.count()).select_from(Task))
        ).scalar()
        assert n_docs_after == n_docs_before, "raw import must not create Document"
        assert n_tasks_after == n_tasks_before, "raw import must not create Task"

    @pytest.mark.asyncio
    async def test_existing_document_idempotent_readonly(self, session):
        svc = DocumentImportService(session)
        sha = hashlib.sha256(PDF_BYTES).hexdigest()
        fake = object.__new__(type("D", (), {"original_sha256": sha}))

        async def _find(*a, **k):
            return fake

        svc._source_repo.find_document_by_sha256 = _find  # type: ignore[method-assign]

        async def _enqueue(*a, **k):
            raise AssertionError("enqueue must not be called")

        svc._task_service.enqueue = _enqueue  # type: ignore[method-assign]
        doc, task, is_new = await svc.import_file(
            file_bytes=PDF_BYTES, file_name="exam.pdf"
        )
        assert doc is fake
        assert task is None
        assert is_new is False


class TestExecutorEntryContract:
    @pytest.mark.asyncio
    async def test_missing_or_unknown_mode_raises(self):
        ex = object.__new__(TaskExecutor)
        for params in ({}, {"source_mode": "llm"}, {"source_mode": "preprocessing"}):
            with pytest.raises(EntryContractError) as ei:
                await TaskExecutor._annotation_stage(  # type: ignore[arg-type]
                    ex, None, None, params
                )
            msg = str(ei.value)
            assert (
                "explicit source_mode" in msg
                or "unknown source_mode" in msg
                or "manifest_path" in msg
            )

    @pytest.mark.asyncio
    async def test_absence_inference_disabled(self):
        """缺 source_mode 一律失败，不得静默落到 native/LLM（缺席推断禁止）。"""
        ex = object.__new__(TaskExecutor)

        async def _boom(*a, **k):
            raise AssertionError("native path must not be inferred")

        ex._annotation_native_llm = _boom  # type: ignore[method-assign]
        with pytest.raises(EntryContractError):
            await TaskExecutor._annotation_stage(  # type: ignore[arg-type]
                ex, None, None, {"file_path": "x.pdf"}
            )

    @pytest.mark.asyncio
    async def test_explicit_native_delegates_to_native_path(self):
        ex = object.__new__(TaskExecutor)
        sentinel = object()
        called = {}

        async def _fake_native(task_id, version, params):
            called["yes"] = params
            return sentinel

        ex._annotation_native_llm = _fake_native  # type: ignore[method-assign]
        params = {"source_mode": "native"}
        out = await TaskExecutor._annotation_stage(  # type: ignore[arg-type]
            ex, None, None, params
        )
        assert out is sentinel
        assert called["yes"] is params

    @pytest.mark.asyncio
    async def test_good_params_delegate_to_manifest_binding(self, tmp_path):
        ex = object.__new__(TaskExecutor)
        sentinel = object()
        called = {}

        async def _fake_bind(task_id, version, params):
            called["yes"] = params
            return sentinel

        ex._annotation_from_manifest_units = _fake_bind  # type: ignore[method-assign]
        mf = tmp_path / "manifest.json"
        mf.write_text("{}", encoding="utf-8")
        params = {"source_mode": "preprocessing", "manifest_path": str(mf)}
        out = await TaskExecutor._annotation_stage(  # type: ignore[arg-type]
            ex, None, None, params
        )
        assert out is sentinel
        assert called["yes"] is params


class TestIdempotencyAndConflict:
    @pytest.mark.asyncio
    async def test_reimport_same_package_no_second_task(self, session):
        from app.models.runtime import Task

        n_before = (
            await session.execute(
                select(func.count())
                .select_from(Task)
                .where(Task.task_type == "document_ingest")
            )
        ).scalar()
        svc = PreprocessingImportService(session)
        uniq = b"-idem-" + uuid.uuid4().hex.encode()
        r1 = await svc.import_package(
            package=_pkg(pdf=PDF_BYTES + uniq), created_by="test"
        )
        await session.commit()
        assert r1.task_id is not None and r1.is_new is True

        r2 = await svc.import_package(
            package=_pkg(pdf=PDF_BYTES + uniq), created_by="test"
        )
        await session.commit()
        assert r2.is_new is False
        assert r2.task_id is None, "idempotent re-import must not enqueue a second task"

        n_after = (
            await session.execute(
                select(func.count())
                .select_from(Task)
                .where(Task.task_type == "document_ingest")
            )
        ).scalar()
        assert n_after == n_before + 1, "exactly one task across two imports"

    @pytest.mark.asyncio
    async def test_reimport_different_md_is_explicit_conflict(self, session):
        svc = PreprocessingImportService(session)
        uniq = b"-conf-" + uuid.uuid4().hex.encode()
        await svc.import_package(
            package=_pkg(pdf=PDF_BYTES + uniq), created_by="test"
        )
        await session.commit()

        md2 = (MD_BODY + "\n2. 另一题\n").encode("utf-8")
        with pytest.raises(PreprocessingImportError) as ei:
            await svc.import_package(
                package=_pkg(md=md2, pdf=PDF_BYTES + uniq), created_by="test"
            )
        assert ei.value.stage == "identity"
        assert "conflict" in ei.value.reason

    @pytest.mark.asyncio
    async def test_existing_without_stored_sha_failclosed(self, session):
        svc = PreprocessingImportService(session)
        uniq = b"-nosha-" + uuid.uuid4().hex.encode()
        r1 = await svc.import_package(
            package=_pkg(pdf=PDF_BYTES + uniq), created_by="test"
        )
        await session.commit()
        # 擦掉已存的 source_content_sha256，模拟身份记录缺失 → fail-closed
        doc = r1.document
        meta = dict(doc.upload_meta or {})
        meta.pop("source_content_sha256", None)
        doc.upload_meta = meta
        await session.commit()

        with pytest.raises(PreprocessingImportError) as ei:
            await svc.import_package(
                package=_pkg(pdf=PDF_BYTES + uniq), created_by="test"
            )
        assert ei.value.stage == "identity"
        assert "fail-closed" in ei.value.reason


class TestNativeTextProviderZeroCall:
    @pytest.mark.asyncio
    async def test_no_native_provider_on_preprocessing_path(self, monkeypatch, session):
        import app.ai.ocr.providers as providers

        class _Bomb:
            def __init__(self, *a, **k):
                raise AssertionError("NativeTextProvider must not be constructed")

        monkeypatch.setattr(providers, "NativeTextProvider", _Bomb)

        pkg = _pkg()
        PreprocessingImportService._verify_package_identity(
            PreprocessingImportService.__new__(PreprocessingImportService), pkg
        )
        text = await PreprocessingTextExtractor(pkg.source_md, manifest_meta={}).extract(
            pkg.original_bytes
        )
        assert getattr(text, "provider", None) == "preprocessing"
        assert text.lines, "preprocessing extractor must yield lines without native path"

        svc = DocumentImportService(session)

        async def _find(*a, **k):
            return None

        svc._source_repo.find_document_by_sha256 = _find  # type: ignore[method-assign]
        with pytest.raises(ImportError_):
            await svc.import_file(
                file_bytes=PDF_BYTES + b"-raw-zerocall", file_name="exam.pdf"
            )


# ---------------------------------------------------------------------------
# F-A（B3-2R）：入口契约必须在 Seal/提取/落库之前生效。
# 测试经真实执行入口（run_once / 完整 _process）；spy 挂在执行器实际持有的
# extractor 实例上；断言 provider 调用 0 次且 Document/SourceVersion 零增量。
# ---------------------------------------------------------------------------


class _SpyGateway:
    mode = "mock"

    def authorize(self, *a, **k):  # pragma: no cover - contract fails before this
        raise AssertionError("gateway must not be reached before contract check")


class TestEntryContractBeforeSeal:
    async def _counts(self) -> dict:
        from sqlalchemy import func, select

        from app.db.session import async_session_maker
        from app.models.source import Document, DocumentSourceVersion

        async with async_session_maker() as s:
            docs = (
                await s.execute(select(func.count()).select_from(Document))
            ).scalar()
            vers = (
                await s.execute(
                    select(func.count()).select_from(DocumentSourceVersion)
                )
            ).scalar()
            lines = (
                await s.execute(
                    text(
                        "select count(*) from document_source_lines"
                    )
                )
            ).scalar()
        return {"documents": docs, "versions": vers, "source_lines": lines}

    def _make_executor(self, spy_calls: list):
        from app.ai.ocr.result import OCRLine, OCRResult
        from app.db.session import async_session_maker
        from app.domains.task.executor import TaskExecutor

        async def spy_extract(file_bytes: bytes):
            spy_calls.append(len(file_bytes))
            return OCRResult(
                provider="spy", model="spy", pages=1,
                lines=tuple(OCRLine(text="x", page_no=1) for _ in range(1)),
                source_meta={},
            )

        return TaskExecutor(
            async_session_maker,
            llm_gateway=_SpyGateway(),  # type: ignore[arg-type]
            ocr_extractor=spy_extract,
        )

    async def _enqueue_raw(self, tmp_path, params: dict):
        from app.db.session import async_session_maker
        from app.domains.task.service import TaskService

        pdf = tmp_path / "entry.pdf"
        pdf.write_bytes(b"%PDF-1.4 entry-contract-probe")
        p = dict(params)
        p.setdefault("file_path", str(pdf))
        p.setdefault("file_name", "entry.pdf")
        p.setdefault("file_type", "pdf")
        async with async_session_maker() as s:
            t = await TaskService(s).enqueue(
                task_type="document_ingest", task_params=p
            )
            await s.commit()
            return t.id

    @pytest.mark.asyncio
    async def test_missing_mode_fails_before_seal_no_side_effects(self, tmp_path):
        from app.db.session import async_session_maker
        from app.domains.task.executor import EntryContractError

        before = await self._counts()
        spy: list = []
        ex = self._make_executor(spy)
        task_id = await self._enqueue_raw(tmp_path, {})
        with pytest.raises(EntryContractError) as ei:
            await ex._process(task_id, "w1", "tok")
        assert "explicit source_mode" in str(ei.value)
        assert spy == [], "extractor must not be called before contract rejection"
        after = await self._counts()
        assert after == before, "no Document/SourceVersion/lines may be written"

    @pytest.mark.asyncio
    async def test_unknown_mode_fails_before_seal_no_side_effects(self, tmp_path):
        from app.domains.task.executor import EntryContractError

        before = await self._counts()
        spy: list = []
        ex = self._make_executor(spy)
        task_id = await self._enqueue_raw(tmp_path, {"source_mode": "llm"})
        with pytest.raises(EntryContractError) as ei:
            await ex._process(task_id, "w1", "tok")
        assert "unknown source_mode" in str(ei.value)
        assert spy == []
        assert await self._counts() == before

    @pytest.mark.asyncio
    async def test_preprocessing_without_manifest_fails_before_seal(self, tmp_path):
        from app.domains.task.executor import EntryContractError

        before = await self._counts()
        spy: list = []
        ex = self._make_executor(spy)
        task_id = await self._enqueue_raw(tmp_path, {"source_mode": "preprocessing"})
        with pytest.raises(EntryContractError) as ei:
            await ex._process(task_id, "w1", "tok")
        assert "manifest_path" in str(ei.value)
        assert spy == []
        assert await self._counts() == before

    @pytest.mark.asyncio
    async def test_role_mode_contradiction_fails_before_seal(self, tmp_path):
        from app.domains.task.executor import EntryContractError

        before = await self._counts()
        spy: list = []
        ex = self._make_executor(spy)
        task_id = await self._enqueue_raw(
            tmp_path, {"source_mode": "native", "role": "preprocessing"}
        )
        with pytest.raises(EntryContractError) as ei:
            await ex._process(task_id, "w1", "tok")
        assert "contradiction" in str(ei.value)
        assert spy == []
        assert await self._counts() == before

    @pytest.mark.asyncio
    async def test_seal_provider_contradiction_fails_before_seal(self, tmp_path):
        """F-2 负向：seal_provider 与已校验 source_mode 矛盾 → 入口拒绝。

        矛盾 provider 若进入 seal 会把 provider 计入 LE hash，同一内容可能
        形成不同 Source Version——必须在 seal 之前拒绝。
        """
        from app.domains.task.executor import EntryContractError

        before = await self._counts()
        spy: list = []
        ex = self._make_executor(spy)
        task_id = await self._enqueue_raw(
            tmp_path,
            {"source_mode": "preprocessing", "seal_provider": "native",
             "manifest_path": str(tmp_path / "nope.manifest.json")},
        )
        with pytest.raises(EntryContractError) as ei:
            await ex._process(task_id, "w1", "tok")
        assert "seal_provider/source_mode contradiction" in str(ei.value)
        assert spy == []
        assert await self._counts() == before

        # 对照：seal_provider 缺省时由 mode 派生，不因缺省而拒绝
        # （真正缺 manifest 的拒绝属于既有 precondition，不在本用例断言范围）。

    async def _backdate_own_task(self, task_id) -> None:
        """定向处理本用例数据：把本用例任务回拨 created_at，确保 next_queued_id
        （order by created_at）优先认领它——替代已被禁用的全局清表。只改本行。"""
        from app.db.session import async_session_maker

        async with async_session_maker() as s:
            await s.execute(
                text(
                    "update tasks set created_at = now() - interval '1 day' "
                    "where id = :i"
                ),
                {"i": task_id},
            )
            await s.commit()

    async def _cleanup_own(self, task_id) -> None:
        """定向清理本用例数据（FK 序）：只删本用例创建的 task/claim 行。"""
        from app.db.session import async_session_maker

        async with async_session_maker() as s:
            await s.execute(
                text("delete from task_claims where task_id = :i"), {"i": task_id}
            )
            await s.execute(text("delete from tasks where id = :i"), {"i": task_id})
            await s.commit()

    @pytest.mark.asyncio
    async def test_run_once_marks_failed_with_zero_side_effects(self, tmp_path):
        """真实 run_once 入口：任务显式失败 + provider 零调用 + 零落库。

        F-1（Owner 2026-10-29）：不得以全局清表（DELETE 17 表）换认领确定性。
        只定向处理本用例创建的行；认领顺序用本行 created_at 回拨保证。
        """
        before = await self._counts()
        spy: list = []
        ex = self._make_executor(spy)
        task_id = await self._enqueue_raw(tmp_path, {})
        await self._backdate_own_task(task_id)

        try:
            handled = await ex.run_once(worker_id="w1")
            assert handled is True

            from app.db.session import async_session_maker
            from sqlalchemy import text as _t

            async with async_session_maker() as s:
                status = (
                    await s.execute(
                        _t("select status from tasks where id=:i"), {"i": task_id}
                    )
                ).scalar_one()
                row = (
                    await s.execute(
                        _t(
                            "select outcome, error_type, lease_snapshot "
                            "from task_claims where task_id=:i order by start desc limit 1"
                        ),
                        {"i": task_id},
                    )
                ).mappings().first()
            assert status == "failed"
            assert row["outcome"] == "failed"
            assert row["error_type"] == "validation_error"
            snap = row["lease_snapshot"] or {}
            if isinstance(snap, str):
                import json as _json

                snap = _json.loads(snap)
            assert "explicit source_mode" in snap.get("error_detail", "")
            assert spy == [], "NativeTextProvider/extractor calls must be 0"
            assert await self._counts() == before, "zero committed seal artifacts"
        finally:
            await self._cleanup_own(task_id)

    def test_test_db_identity_is_isolated(self):
        """测试库身份检查：只能是隔离测试库 aitutors_testsuite。"""
        from app.core.config import settings

        url = str(settings.database_url)
        assert "aitutors_testsuite" in url
        assert "aitutors_test" not in url.replace("aitutors_testsuite", "")
        assert not url.rstrip("/").endswith("/aitutors")
