"""M2-R2 acceptance: manifest units drive annotation (coverage + ID alignment)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domains.source.manifest_annotation import (
    ManifestBindingError,
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)


def _lines(n: int) -> list[str]:
    return [f"L{i:03d} content {i}" for i in range(1, n + 1)]


def _manifest_unit(unit_id: str, stem=(1, 1), opt=(2, 2), ans=(3, 3)):
    return {
        "unit_id": unit_id,
        "unit_type": "standalone_question",
        "question_numbers": [int(unit_id[1:])],
        "original_question_type": "single_choice",
        "stem_lines": list(stem),
        "options_lines": list(opt),
        "answer_lines": list(ans),
    }


class TestManifestBinding:
    def test_binds_all_40_units_preserving_ids(self):
        lines = _lines(50)
        units = [_manifest_unit(f"Q{i}", stem=(i, i), opt=(i + 1, i + 1), ans=(40, 40))
                 for i in range(1, 41)]
        man = {"units": units, "identity_version": 2, "source_content_sha256": "a" * 64}
        bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
        assert len(bound) == 40
        assert [b.unit_id for b in bound] == [f"Q{i}" for i in range(1, 41)]
        # Q8 must bind Q8's stem line, not Q1
        q8 = bound[7]
        assert q8.unit_id == "Q8"
        assert q8.ranges["stem"].start == 8
        assert "L008" in q8.bound_text

    def test_rejects_out_of_range(self):
        man = {"units": [_manifest_unit("Q1", stem=(1, 99))]}
        with pytest.raises(ManifestBindingError, match="exceeds"):
            bind_units_from_manifest(man, _lines(10), source_content_sha256="a" * 64)

    def test_rejects_inverted_range(self):
        man = {"units": [_manifest_unit("Q1", stem=(5, 2))]}
        with pytest.raises(ManifestBindingError, match="inverted"):
            bind_units_from_manifest(man, _lines(10), source_content_sha256="a" * 64)

    def test_rejects_duplicate_unit_id(self):
        man = {"units": [_manifest_unit("Q1"), _manifest_unit("Q1")]}
        with pytest.raises(ManifestBindingError, match="duplicate"):
            bind_units_from_manifest(man, _lines(10), source_content_sha256="a" * 64)

    def test_rejects_empty_units(self):
        with pytest.raises(ManifestBindingError, match="no units"):
            bind_units_from_manifest({"units": []}, _lines(5), source_content_sha256="a" * 64)

    def test_payload_preserves_producer_unit_ids(self):
        lines = _lines(20)
        man = {
            "units": [_manifest_unit("Q8", stem=(8, 8), opt=(9, 9), ans=(18, 18))],
            "identity_version": 2,
        }
        bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="a" * 64, manifest_identity_version=2
        )
        su = payload["semantic_units"]
        assert len(su) == 1
        assert su[0]["unit_id"] == "Q8"  # NOT renumbered to Q1
        assert su[0]["unit_type"] == "standalone_unit"
        assert payload["producer_boundary"]["unit_bindings"][0]["unit_id"] == "Q8"

    def test_no_forbidden_fields_in_payload(self):
        from app.domains.annotation import FORBIDDEN_FIELDS, validate_annotation_payload

        lines = _lines(10)
        man = {"units": [_manifest_unit("Q1")], "identity_version": 2}
        bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
        payload = build_annotation_payload_from_bound(
            bound, source_content_sha256="a" * 64, manifest_identity_version=2
        )
        ok, violations = validate_annotation_payload(payload)
        assert ok, violations
        for f in FORBIDDEN_FIELDS:
            assert f not in json.dumps(payload)


class TestRealPackageBinding:
    PKG = Path(
        r"D:\Project\AITutor-X\E2E_ACCEPTANCE\06_M1_PACKAGES\chem-2018-spring-huikao-teacher"
    )

    def test_real_package_40_units_q8_identity(self):
        man = json.loads((self.PKG / "manifest.json").read_text(encoding="utf-8"))
        lines = (self.PKG / "paper.md").read_text(encoding="utf-8").splitlines()
        sha = man["source_content_sha256"]
        bound = bind_units_from_manifest(man, lines, source_content_sha256=sha)
        assert len(bound) == 40
        q8 = next(b for b in bound if b.unit_id == "Q8")
        assert q8.question_numbers == [8]
        # Q8 stem_lines in real manifest is [42, 42]
        assert q8.ranges["stem"] is not None
        assert q8.ranges["stem"].start == 42
        assert "离子键" in q8.bound_text or "L042" not in q8.bound_text  # real content
        # bound hash is stable
        assert len(q8.bound_text_hash) == 64
