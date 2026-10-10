"""Tests for CR-005 role→artifact_kind enforcement (M1-A)."""
import pytest

from app.models.source import (
    artifact_kind_for_role,
    validate_artifact_compatibility,
)


class TestArtifactKindAuthority:
    def test_preprocessing_maps_canonical_l1(self):
        assert artifact_kind_for_role("preprocessing") == "canonical_l1"

    def test_canonical_maps_canonical_l1(self):
        assert artifact_kind_for_role("canonical") == "canonical_l1"

    def test_native_maps_raw_l1(self):
        assert artifact_kind_for_role("native") == "raw_l1"

    def test_enforcement_accepts_valid_pairs(self):
        validate_artifact_compatibility("preprocessing", "preprocessing", "canonical_l1")
        validate_artifact_compatibility("native", "native", "raw_l1")
        validate_artifact_compatibility("ocr_ppsv3", "ppsv3", "raw_l1")
        validate_artifact_compatibility("ocr_ppsvl", "paddleocr-vl", "raw_l1")
        validate_artifact_compatibility("docx", "docx", "raw_l1")
        validate_artifact_compatibility("docx", "docx", "original_binary")
        validate_artifact_compatibility("canonical", "", "canonical_l1")

    def test_enforcement_rejects_preprocessing_raw_l1(self):
        with pytest.raises(ValueError, match="role/artifact_kind mismatch"):
            validate_artifact_compatibility("preprocessing", "preprocessing", "raw_l1")

    def test_enforcement_rejects_native_canonical_l1(self):
        with pytest.raises(ValueError, match="role/artifact_kind mismatch"):
            validate_artifact_compatibility("native", "native", "canonical_l1")

    def test_enforcement_rejects_ocr_canonical_l1(self):
        with pytest.raises(ValueError, match="role/artifact_kind mismatch"):
            validate_artifact_compatibility("ocr_ppsvl", "paddleocr-vl", "canonical_l1")

    def test_enforcement_rejects_canonical_raw_l1(self):
        with pytest.raises(ValueError, match="role/artifact_kind mismatch"):
            validate_artifact_compatibility("canonical", "", "raw_l1")
