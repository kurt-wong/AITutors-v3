"""Negative acceptance for formal preprocessing import (Owner Round 2).

Must prove: missing manifest / hash mismatch / unreadable md / incompatible
structure all FAIL EXPLICITLY and never call NativeTextProvider.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.ai.ocr.preprocessing_provider import PreprocessingTextExtractor
from app.domains.source.preprocessing_import import (
    PreprocessingImportError,
    PreprocessingPackage,
    PreprocessingImportService,
)


PDF_BYTES = b"%PDF-1.4 fake-original-bytes-for-identity"
MD_BODY = "# 试卷\n\n1. 题干\nA. 选项A\nB. 选项B\n"


def _pkg(
    *,
    original: bytes = PDF_BYTES,
    md: bytes = MD_BODY.encode("utf-8"),
    manifest: dict | None = None,
) -> PreprocessingPackage:
    if manifest is None:
        manifest = {
            "source_content_sha256": hashlib.sha256(md).hexdigest(),
        }
    return PreprocessingPackage(
        original_bytes=original,
        original_name="paper.pdf",
        source_md=md,
        manifest=manifest,
    )


class TestIdentityVerification:
    def test_rejects_missing_source_content_sha256(self):
        pkg = _pkg(manifest={})
        with pytest.raises(PreprocessingImportError) as ei:
            PreprocessingImportService._verify_package_identity(
                PreprocessingImportService.__new__(PreprocessingImportService),
                pkg,
            )
        assert ei.value.stage == "identity"
        assert "source_content_sha256" in ei.value.reason

    def test_rejects_source_hash_mismatch(self):
        pkg = _pkg(manifest={"source_content_sha256": "0" * 64})
        with pytest.raises(PreprocessingImportError) as ei:
            PreprocessingImportService._verify_package_identity(
                PreprocessingImportService.__new__(PreprocessingImportService),
                pkg,
            )
        assert ei.value.stage == "identity"
        assert "mismatch" in ei.value.reason

    def test_rejects_empty_source_md(self):
        pkg = _pkg(md=b"", manifest={"source_content_sha256": hashlib.sha256(b"").hexdigest()})
        with pytest.raises(PreprocessingImportError) as ei:
            PreprocessingImportService._verify_package_identity(
                PreprocessingImportService.__new__(PreprocessingImportService),
                pkg,
            )
        assert ei.value.stage == "identity"
        assert "empty" in ei.value.reason.lower()

    def test_rejects_original_hash_mismatch_when_declared(self):
        md = MD_BODY.encode("utf-8")
        pkg = _pkg(
            md=md,
            manifest={
                "source_content_sha256": hashlib.sha256(md).hexdigest(),
                "original_sha256": "a" * 64,
            },
        )
        with pytest.raises(PreprocessingImportError) as ei:
            PreprocessingImportService._verify_package_identity(
                PreprocessingImportService.__new__(PreprocessingImportService),
                pkg,
            )
        assert "original_sha256 mismatch" in ei.value.reason

    def test_rejects_bad_original_extension(self):
        pkg = _pkg()
        pkg = PreprocessingPackage(
            original_bytes=PDF_BYTES,
            original_name="paper.txt",
            source_md=pkg.source_md,
            manifest=pkg.manifest,
        )
        with pytest.raises(PreprocessingImportError) as ei:
            PreprocessingImportService._verify_package_identity(
                PreprocessingImportService.__new__(PreprocessingImportService),
                pkg,
            )
        assert ei.value.stage == "identity"

    def test_accepts_valid_identity(self):
        pkg = _pkg()
        # Should not raise
        PreprocessingImportService._verify_package_identity(
            PreprocessingImportService.__new__(PreprocessingImportService),
            pkg,
        )


class TestExtractorFailClosed:
    def test_rejects_empty_markdown(self):
        with pytest.raises(ValueError, match="empty"):
            PreprocessingTextExtractor(b"")

    def test_records_source_content_sha256(self):
        md = MD_BODY.encode("utf-8")
        ex = PreprocessingTextExtractor(md)
        assert ex.source_content_sha256 == hashlib.sha256(md).hexdigest()

    @pytest.mark.asyncio
    async def test_extractor_does_not_use_native_path(self):
        """Extractor ignores original bytes and never touches PDF parsers."""
        md = MD_BODY.encode("utf-8")
        ex = PreprocessingTextExtractor(md, manifest_meta={"k": "v"})
        result = await ex.extract(b"%PDF-fake")
        assert result.provider == "preprocessing"
        assert result.source_meta["source_mode"] == "preprocessing"
        assert result.source_meta["source_content_sha256"] == hashlib.sha256(md).hexdigest()
        assert all(line.text.strip() for line in result.lines)


class TestPackageLoad:
    def test_missing_manifest(self, tmp_path: Path):
        from app.domains.source.preprocessing_import import load_package_from_dir

        with pytest.raises(PreprocessingImportError) as ei:
            load_package_from_dir(tmp_path)
        assert ei.value.stage == "load"
        assert "manifest" in ei.value.reason.lower()

    def test_missing_source_md(self, tmp_path: Path):
        from app.domains.source.preprocessing_import import load_package_from_dir

        (tmp_path / "m.manifest.json").write_text(
            '{"source_content_sha256": "x"}', encoding="utf-8"
        )
        (tmp_path / "a.pdf").write_bytes(PDF_BYTES)
        with pytest.raises(PreprocessingImportError) as ei:
            load_package_from_dir(tmp_path)
        assert ei.value.stage == "load"
        assert "markdown" in ei.value.reason.lower()

    def test_missing_original(self, tmp_path: Path):
        from app.domains.source.preprocessing_import import load_package_from_dir

        md = MD_BODY.encode("utf-8")
        (tmp_path / "m.manifest.json").write_text(
            '{"source_content_sha256": "%s"}' % hashlib.sha256(md).hexdigest(),
            encoding="utf-8",
        )
        (tmp_path / "a.md").write_bytes(md)
        with pytest.raises(PreprocessingImportError) as ei:
            load_package_from_dir(tmp_path)
        assert ei.value.stage == "load"
        assert "original" in ei.value.reason.lower()
