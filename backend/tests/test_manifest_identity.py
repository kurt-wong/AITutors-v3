"""Consumer Identity Verification — M1 Manifest Reader 黄金测试。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §4.2
- D4=(b) interface-only implementation scope（DESIGN-v1.1 §4.2）；不构成 §1 双轴语义 authority

约束：
- ManifestIdentity 唯一字段 = source_content_sha256
- path/source_file 不参与 identity
- 不读 source bytes、不算 sha256、不访问 IR
"""

import json
from pathlib import Path

import pytest

from app.core.manifest_identity import ManifestIdentity, ManifestReadError, read_manifest_identity

# conftest migrated_db override — 纯单元测试，无 DB 依赖
@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest autouse fixture — 本模块不需要数据库。"""


def _valid_sha() -> str:
    return "a" * 64


def _write_manifest(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "test.manifest.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ─── 正常读取 ───

class TestNormalRead:
    def test_reads_valid_sha256(self, tmp_path: Path) -> None:
        sha = _valid_sha()
        p = _write_manifest(tmp_path, {"source_content_sha256": sha})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == sha

    def test_returns_frozen_dataclass(self, tmp_path: Path) -> None:
        p = _write_manifest(tmp_path, {"source_content_sha256": _valid_sha()})
        result = read_manifest_identity(p)
        assert isinstance(result, ManifestIdentity)
        with pytest.raises(AttributeError):
            result.source_content_sha256 = "b" * 64

    def test_sha_is_lowercase_64_hex(self, tmp_path: Path) -> None:
        sha = "0123456789abcdef" * 4  # 64-char lowercase hex
        p = _write_manifest(tmp_path, {"source_content_sha256": sha})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == sha


# ─── 缺失 hash ───

class TestMissingHash:
    def test_missing_field_returns_none(self, tmp_path: Path) -> None:
        p = _write_manifest(tmp_path, {"source_file": "/some/path.md"})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 is None

    def test_empty_string_returns_none(self, tmp_path: Path) -> None:
        p = _write_manifest(tmp_path, {"source_content_sha256": ""})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 is None

    def test_null_value_returns_none(self, tmp_path: Path) -> None:
        p = _write_manifest(tmp_path, {"source_content_sha256": None})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 is None


# ─── Malformed manifest ───

class TestMalformedManifest:
    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ManifestReadError, match="文件不存在"):
            read_manifest_identity(tmp_path / "nonexistent.json")

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ManifestReadError, match="JSON 解析失败"):
            read_manifest_identity(p)

    def test_non_dict_json_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "array.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(ManifestReadError, match="不是 JSON object"):
            read_manifest_identity(p)

    def test_uppercase_hex_raises(self, tmp_path: Path) -> None:
        sha = "A" * 64  # uppercase
        p = _write_manifest(tmp_path, {"source_content_sha256": sha})
        with pytest.raises(ManifestReadError, match="格式非法"):
            read_manifest_identity(p)

    def test_short_hex_raises(self, tmp_path: Path) -> None:
        p = _write_manifest(tmp_path, {"source_content_sha256": "abc123"})
        with pytest.raises(ManifestReadError, match="格式非法"):
            read_manifest_identity(p)

    def test_non_hex_raises(self, tmp_path: Path) -> None:
        p = _write_manifest(tmp_path, {"source_content_sha256": "z" * 64})
        with pytest.raises(ManifestReadError, match="格式非法"):
            read_manifest_identity(p)

    def test_non_string_value_raises(self, tmp_path: Path) -> None:
        p = _write_manifest(tmp_path, {"source_content_sha256": 12345})
        with pytest.raises(ManifestReadError, match="格式非法"):
            read_manifest_identity(p)


# ─── Extra fields 不影响读取 ───

class TestExtraFields:
    def test_extra_fields_ignored(self, tmp_path: Path) -> None:
        sha = _valid_sha()
        p = _write_manifest(tmp_path, {
            "source_content_sha256": sha,
            "model": "gpt-4",
            "prompt_version": "v3",
            "units": [{"unit_id": "u1", "unit_type": "standalone_question"}],
            "validation_issues": [],
            "warnings": [],
            "unknown_field": "should be ignored",
        })
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == sha

    def test_nested_units_do_not_affect_identity(self, tmp_path: Path) -> None:
        sha = _valid_sha()
        p = _write_manifest(tmp_path, {
            "source_content_sha256": sha,
            "units": [
                {"unit_id": "u1", "question_numbers": [1], "stem_lines": [1, 3]},
                {"unit_id": "u2", "question_numbers": [2], "answer_lines": [4, 5]},
            ],
        })
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == sha


# ─── Path 字段不得参与 identity ───

class TestPathNotIdentity:
    def test_manifest_identity_has_no_path_field(self) -> None:
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(ManifestIdentity)}
        assert "source_file" not in field_names
        assert "path" not in field_names
        assert field_names == {"source_content_sha256"}

    def test_source_file_in_manifest_is_ignored(self, tmp_path: Path) -> None:
        sha = _valid_sha()
        p = _write_manifest(tmp_path, {
            "source_content_sha256": sha,
            "source_file": "/completely/different/path.md",
        })
        result = read_manifest_identity(p)
        # result 只有 source_content_sha256，source_file 不影响
        assert result.source_content_sha256 == sha
        import dataclasses
        assert "source_file" not in {f.name for f in dataclasses.fields(ManifestIdentity)}
