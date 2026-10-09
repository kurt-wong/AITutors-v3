"""B1-R2-FIX-01 — load_package_from_dir source selection contract tests.

Cases:
  A. manifest source_file=REAL.md missing, dir has aaa_other.md → must FAIL
  B. no declared source_file, multiple *.md → must FAIL (no sort-pick)
  C. declared source_file exists, other *.md present → must load declared only
  D. declared source_file missing, no other *.md → must FAIL

These tests encode the REQUIRED post-fix behavior.
Pre-fix: A and B are expected to expose the silent-substitution defect.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domains.source.preprocessing_import import (
    PreprocessingImportError,
    load_package_from_dir,
)


PDF = b"%PDF-1.4 fake-original"


def write_pkg(
    tmp: Path,
    *,
    manifest: dict | None,
    files: dict[str, bytes],
) -> Path:
    d = tmp / "pkg"
    d.mkdir()
    if manifest is not None:
        (d / "m.manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
    for name, data in files.items():
        (d / name).write_bytes(data)
    return d


class TestSourceFileSelection:
    def test_A_declared_missing_with_other_md_must_fail(self, tmp_path: Path):
        """A: declared REAL.md missing, aaa_other.md present → FAIL, no substitute."""
        d = write_pkg(
            tmp_path,
            manifest={"source_file": "REAL.md"},
            files={
                "aaa_other.md": b"# other\n",
                "paper.pdf": PDF,
            },
        )
        with pytest.raises(PreprocessingImportError) as ei:
            load_package_from_dir(d)
        # Must fail; must NOT return aaa_other.md content
        assert ei.value.stage == "load"
        msg = str(ei.value).lower()
        assert "real.md" in msg or "declared" in msg or "missing" in msg

    def test_B_undeclared_multiple_md_must_fail(self, tmp_path: Path):
        """B: no declared source, two *.md → FAIL, no sorted-pick."""
        d = write_pkg(
            tmp_path,
            manifest={"source_content_sha256": "0" * 64},
            files={
                "a.md": b"# a\n",
                "b.md": b"# b\n",
                "paper.pdf": PDF,
            },
        )
        with pytest.raises(PreprocessingImportError) as ei:
            load_package_from_dir(d)
        assert ei.value.stage == "load"
        msg = str(ei.value).lower()
        assert "multiple" in msg or "ambiguous" in msg or "unique" in msg

    def test_C_declared_exists_loads_only_declared(self, tmp_path: Path):
        """C: declared file exists alongside others → load declared only."""
        declared = "# DECLARED SOURCE MARKER\n"
        d = write_pkg(
            tmp_path,
            manifest={
                "source_file": "chosen.md",
                "source_content_sha256": "x",
            },
            files={
                "aaa_first.md": b"# SHOULD NOT BE LOADED\n",
                "chosen.md": declared.encode("utf-8"),
                "paper.pdf": PDF,
            },
        )
        pkg = load_package_from_dir(d)
        assert pkg.source_md == declared.encode("utf-8")
        assert b"SHOULD NOT BE LOADED" not in pkg.source_md

    def test_D_declared_missing_no_other_md_must_fail(self, tmp_path: Path):
        """D: declared missing and no other md → FAIL."""
        d = write_pkg(
            tmp_path,
            manifest={"source_file": "REAL.md"},
            files={"paper.pdf": PDF},
        )
        with pytest.raises(PreprocessingImportError) as ei:
            load_package_from_dir(d)
        assert ei.value.stage == "load"
        assert "markdown" in str(ei.value).lower() or "real.md" in str(ei.value)

    def test_undeclared_single_md_allowed(self, tmp_path: Path):
        """Undeclared + exactly one *.md → allowed auto-discovery."""
        d = write_pkg(
            tmp_path,
            manifest={"source_content_sha256": "x"},
            files={
                "only.md": b"# only\n",
                "paper.pdf": PDF,
            },
        )
        pkg = load_package_from_dir(d)
        assert pkg.source_md == b"# only\n"

    def test_path_traversal_rejected(self, tmp_path: Path):
        """Declared source_file escaping package dir must fail."""
        outside = tmp_path / "outside.md"
        outside.write_bytes(b"# outside\n")
        d = write_pkg(
            tmp_path,
            manifest={"source_file": "../outside.md"},
            files={"paper.pdf": PDF},
        )
        with pytest.raises(PreprocessingImportError) as ei:
            load_package_from_dir(d)
        assert ei.value.stage == "load"
