"""Formal preprocessing package import (Owner Round 2, option b).

Identity contract (hard):
- documents.original_sha256  = SHA256(original PDF/DOCX raw bytes) ONLY
- source_content_sha256      = SHA256(source Markdown raw bytes), stored in
                               DocumentSourceVersion.source_meta / input_identity

Fail-closed: any missing piece or hash mismatch raises PreprocessingImportError.
Never calls NativeTextProvider. Never falls back to another source path.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ocr.preprocessing_provider import PreprocessingTextExtractor
from app.domains.source.seal import SealService
from app.domains.task.service import TaskService
from app.models.source import Document
from app.repositories.source_repository import SourceRepository

_ALLOWED_ORIGINAL_EXTENSIONS = {".pdf", ".docx"}


class PreprocessingImportError(Exception):
    """Preprocessing package rejected. Message is the failure reason."""

    def __init__(self, reason: str, *, stage: str) -> None:
        super().__init__(f"[{stage}] {reason}")
        self.reason = reason
        self.stage = stage


@dataclass(frozen=True)
class PreprocessingPackage:
    original_bytes: bytes
    original_name: str
    source_md: bytes
    manifest: dict


@dataclass(frozen=True)
class PreprocessingImportResult:
    document: Document
    source_version_id: str
    original_sha256: str
    source_content_sha256: str
    task_id: str | None
    is_new: bool


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_package_path(package_dir: Path, relative_name: str) -> Path:
    """Resolve a manifest-declared relative name inside package_dir.

    Rejects absolute paths and any path that escapes package_dir.
    """
    if not relative_name or not str(relative_name).strip():
        raise PreprocessingImportError(
            "declared source filename is empty", stage="load"
        )
    name = str(relative_name).strip()
    if Path(name).is_absolute() or name.startswith(("/", "\\")) or (len(name) > 1 and name[1] == ":"):
        raise PreprocessingImportError(
            "declared source filename must be relative to package dir", stage="load"
        )
    candidate = (package_dir / name).resolve()
    root = package_dir.resolve()
    if not candidate.is_relative_to(root):
        raise PreprocessingImportError(
            "declared source filename escapes package dir", stage="load"
        )
    return candidate


def _resolve_source_markdown(package_dir: Path, manifest: dict) -> Path:
    """Select the source markdown with fail-closed rules (B1-R2-FIX-01).

    Rules:
    1. If manifest declares source_file / source_markdown, that path is
       authoritative. Missing / unreadable / invalid → explicit error.
       Never fall back to another *.md in the package.
    2. If undeclared, auto-discover only when exactly one *.md exists.
       Zero or multiple candidates → explicit error (no sort-pick).
    """
    declared = manifest.get("source_file") or manifest.get("source_markdown")
    if declared:
        source_path = _safe_package_path(package_dir, str(declared))
        if not source_path.exists():
            raise PreprocessingImportError(
                f"declared source markdown not found: {Path(str(declared)).name}",
                stage="load",
            )
        if not source_path.is_file():
            raise PreprocessingImportError(
                f"declared source markdown is not a file: {Path(str(declared)).name}",
                stage="load",
            )
        return source_path

    md_files = sorted(p for p in package_dir.glob("*.md") if p.is_file())
    if not md_files:
        raise PreprocessingImportError(
            "source markdown missing or unreadable", stage="load"
        )
    if len(md_files) > 1:
        names = ", ".join(p.name for p in md_files)
        raise PreprocessingImportError(
            f"multiple candidate source markdown files, cannot choose uniquely: {names}",
            stage="load",
        )
    return md_files[0]


def load_package_from_dir(package_dir: Path) -> PreprocessingPackage:
    """Load a directory-style preprocessing package.

    Expected files (names may vary; manifest is authoritative):
    - *.manifest.json  (required)
    - source markdown referenced by manifest.source_file or *.md
    - original PDF/DOCX referenced by manifest.original_file or package files
    """
    if not package_dir.is_dir():
        raise PreprocessingImportError(
            f"package dir not found: {package_dir}", stage="load"
        )

    manifests = sorted(package_dir.glob("*.manifest.json"))
    if not manifests:
        # also accept manifest.json
        single = package_dir / "manifest.json"
        if single.exists():
            manifests = [single]
        else:
            raise PreprocessingImportError(
                "preprocessing manifest missing (*.manifest.json)", stage="load"
            )
    manifest_path = manifests[0]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PreprocessingImportError(
            f"manifest is not valid JSON: {exc}", stage="load"
        ) from exc

    # source markdown — fail-closed selection (B1-R2-FIX-01).
    # Declared name is authoritative: never substitute another .md.
    # Undeclared: auto-discover only when the candidate set is exactly one.
    source_path = _resolve_source_markdown(package_dir, manifest)

    # original file
    orig_name = manifest.get("original_file") or manifest.get("original_document")
    original_path = (package_dir / orig_name) if orig_name else None
    if original_path is None or not original_path.exists():
        candidates = [
            p
            for p in package_dir.iterdir()
            if p.suffix.lower() in _ALLOWED_ORIGINAL_EXTENSIONS
        ]
        if not candidates:
            raise PreprocessingImportError(
                "original PDF/DOCX missing in package", stage="load"
            )
        original_path = candidates[0]

    try:
        source_md = source_path.read_bytes()
    except Exception as exc:
        raise PreprocessingImportError(
            f"source markdown unreadable: {exc}", stage="load"
        ) from exc

    try:
        original_bytes = original_path.read_bytes()
    except Exception as exc:
        raise PreprocessingImportError(
            f"original file unreadable: {exc}", stage="load"
        ) from exc

    return PreprocessingPackage(
        original_bytes=original_bytes,
        original_name=original_path.name,
        source_md=source_md,
        manifest=manifest,
    )


class PreprocessingImportService:
    """Formal entry: accepted preprocessing package → V3 Source pipeline."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._source_repo = SourceRepository(session)
        self._task_service = TaskService(session)
        self._seal = SealService(session)

    async def import_package(
        self,
        *,
        package: PreprocessingPackage,
        created_by: str | None = None,
    ) -> PreprocessingImportResult:
        self._verify_package_identity(package)

        original_sha256 = _sha256(package.original_bytes)
        source_content_sha256 = _sha256(package.source_md)

        existing = await self._source_repo.find_document_by_sha256(original_sha256)
        is_new = existing is None

        # Persist artifacts so the worker can re-open them without re-upload.
        import_dir = Path("data/imports")
        import_dir.mkdir(parents=True, exist_ok=True)
        orig_ext = Path(package.original_name).suffix.lower()
        original_path = import_dir / f"{original_sha256}{orig_ext}"
        if not original_path.exists():
            original_path.write_bytes(package.original_bytes)
        md_path = import_dir / f"{original_sha256}.source.md"
        md_path.write_bytes(package.source_md)

        # Seal with preprocessing extractor. SealService derives Document from
        # original file bytes → original_sha256 stays the original-document identity.
        extractor = PreprocessingTextExtractor(
            package.source_md,
            manifest_meta={
                "manifest_keys": sorted(package.manifest.keys()),
                "source_content_sha256": source_content_sha256,
                "original_sha256": original_sha256,
            },
        )
        version = await self._seal.seal_document(
            file_bytes=package.original_bytes,
            file_name=package.original_name,
            file_type=orig_ext.lstrip("."),
            role="preprocessing",
            provider="preprocessing",
            extractor=extractor.extract,
        )
        await self._session.flush()

        document = await self._source_repo.find_document_by_sha256(original_sha256)
        if document is None:
            raise PreprocessingImportError(
                "document was not created during seal", stage="persist"
            )

        # Record identity split in document upload_meta (no schema change).
        meta = dict(document.upload_meta or {})
        meta["source_mode"] = "preprocessing"
        meta["source_content_sha256"] = source_content_sha256
        meta["source_md_path"] = str(md_path)
        meta["preprocessing_manifest"] = {
            "identity_version": package.manifest.get("identity_version"),
            "has_source_file": bool(package.manifest.get("source_file")),
        }
        document.upload_meta = meta

        task = await self._task_service.enqueue(
            task_type="document_ingest",
            task_params={
                "document_id": str(document.id),
                "original_sha256": original_sha256,
                "file_name": package.original_name,
                "file_path": str(original_path),
                "file_type": orig_ext.lstrip("."),
                "source_mode": "preprocessing",
                "source_content_sha256": source_content_sha256,
                "source_md_path": str(md_path),
                "source_version_id": str(version.id),
                "role": "preprocessing",
                "seal_provider": "preprocessing",
            },
            created_by=created_by or "admin",
        )

        return PreprocessingImportResult(
            document=document,
            source_version_id=str(version.id),
            original_sha256=original_sha256,
            source_content_sha256=source_content_sha256,
            task_id=str(task.id) if task else None,
            is_new=is_new,
        )

    def _verify_package_identity(self, package: PreprocessingPackage) -> None:
        """Fail-closed identity checks. No silent repair, no native fallback.

        Also enforces Interface Scope identity_version via the sole authority
        `enforce_interface_scope` (boundary.py) — same rule set as runner path.
        """
        if not package.original_bytes:
            raise PreprocessingImportError(
                "original file empty", stage="identity"
            )
        ext = Path(package.original_name).suffix.lower()
        if ext not in _ALLOWED_ORIGINAL_EXTENSIONS:
            raise PreprocessingImportError(
                f"unsupported original type: {ext!r}",
                stage="identity",
            )
        if not package.source_md:
            raise PreprocessingImportError(
                "source markdown empty or unreadable", stage="identity"
            )

        computed_src = _sha256(package.source_md)
        claimed_src = package.manifest.get("source_content_sha256")
        if claimed_src is None:
            raise PreprocessingImportError(
                "manifest missing source_content_sha256", stage="identity"
            )
        if claimed_src != computed_src:
            raise PreprocessingImportError(
                "source_content_sha256 mismatch "
                f"(claimed={claimed_src} computed={computed_src})",
                stage="identity",
            )

        # Interface Scope membership (identity_version == 2 / "2").
        # Sole authority: scripts.preprocessing_consumer.boundary.enforce_interface_scope
        self._verify_interface_scope(claimed_src, package.manifest)

        # If manifest declares original identity, it must match.
        claimed_orig = package.manifest.get("original_sha256") or package.manifest.get(
            "original_content_sha256"
        )
        if claimed_orig is not None:
            computed_orig = _sha256(package.original_bytes)
            if claimed_orig != computed_orig:
                raise PreprocessingImportError(
                    "original_sha256 mismatch "
                    f"(claimed={claimed_orig} computed={computed_orig})",
                    stage="identity",
                )

    @staticmethod
    def _verify_interface_scope(claimed_src: str, manifest: dict) -> None:
        """Defer identity_version membership to the sole Interface Scope authority."""
        # Import late so test environments without scripts path still load.
        import sys
        from pathlib import Path as _P

        backend_root = _P(__file__).resolve().parents[2]
        if str(backend_root) not in sys.path:
            sys.path.insert(0, str(backend_root))
        from scripts.preprocessing_consumer.boundary import enforce_interface_scope

        identity_version = manifest.get("identity_version")
        decision = enforce_interface_scope(claimed_src, identity_version)
        if not decision.accepted:
            raise PreprocessingImportError(
                f"interface scope rejected: {decision.code}: {decision.reason}",
                stage="identity",
            )
