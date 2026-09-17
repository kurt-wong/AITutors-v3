"""M3 IR Identity Reader — 单元测试。"""
import json
from pathlib import Path

import pytest

from app.core.ir_identity import IRIdentity, IRReadError, read_ir_identity


@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest autouse fixture — 本模块不需要数据库。"""


def _write_ir(tmp_path: Path, data: object) -> Path:
    p = tmp_path / "resolver_ir.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


class TestNormalRead:
    def test_reads_valid_sha256(self, tmp_path: Path):
        valid = "a" * 64
        p = _write_ir(tmp_path, {"source_content_sha256": valid, "version": "3.0"})
        result = read_ir_identity(p)
        assert result.source_content_sha256 == valid

    def test_returns_frozen_dataclass(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "b" * 64})
        result = read_ir_identity(p)
        assert isinstance(result, IRIdentity)
        with pytest.raises(AttributeError):
            result.source_content_sha256 = "x" * 64  # type: ignore[misc]

    def test_sha_is_lowercase_64_hex(self, tmp_path: Path):
        valid = "0123456789abcdef" * 4
        p = _write_ir(tmp_path, {"source_content_sha256": valid})
        result = read_ir_identity(p)
        assert result.source_content_sha256 is not None
        assert len(result.source_content_sha256) == 64
        assert result.source_content_sha256 == result.source_content_sha256.lower()


class TestMissingHash:
    def test_missing_field_returns_none(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"version": "3.0", "units": []})
        result = read_ir_identity(p)
        assert result.source_content_sha256 is None

    def test_empty_string_returns_none(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": ""})
        result = read_ir_identity(p)
        assert result.source_content_sha256 is None

    def test_null_value_returns_none(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": None})
        result = read_ir_identity(p)
        assert result.source_content_sha256 is None


class TestMalformedIR:
    def test_file_not_found_returns_none(self, tmp_path: Path):
        """Design v1.1 §4.4: IR missing → source_sha256=None, 不抛异常。"""
        result = read_ir_identity(tmp_path / "nope.json")
        assert result.source_content_sha256 is None

    def test_invalid_json_raises(self, tmp_path: Path):
        p = tmp_path / "resolver_ir.json"
        p.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_non_dict_json_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, ["list", "not", "dict"])
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_uppercase_hex_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "A" * 64})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_short_hex_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "a" * 63})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_long_hex_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "a" * 65})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_non_hex_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "z" * 64})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_non_string_value_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": 12345})
        with pytest.raises(IRReadError):
            read_ir_identity(p)


class TestExtraFields:
    def test_extra_fields_ignored(self, tmp_path: Path):
        valid = "c" * 64
        p = _write_ir(tmp_path, {
            "source_content_sha256": valid,
            "version": "3.0",
            "units": [{"type": "paragraph", "content": "hello"}],
            "metadata": {"producer": "v3", "nested": {"deep": True}},
        })
        result = read_ir_identity(p)
        assert result.source_content_sha256 == valid

    def test_nested_units_do_not_affect_identity(self, tmp_path: Path):
        p = _write_ir(tmp_path, {
            "units": [
                {"source_content_sha256": "d" * 64},
                {"source_content_sha256": "e" * 64},
            ],
        })
        result = read_ir_identity(p)
        assert result.source_content_sha256 is None


class TestPathNotIdentity:
    def test_ir_identity_has_no_path_field(self):
        fields = [f.name for f in IRIdentity.__dataclass_fields__.values()]
        assert "path" not in fields
        assert "filename" not in fields
        assert "ir_path" not in fields

    def test_source_file_in_ir_is_ignored(self, tmp_path: Path):
        p = _write_ir(tmp_path, {
            "source_file": "/some/path/to/source.md",
            "source_path": "relative/path.md",
        })
        result = read_ir_identity(p)
        assert result.source_content_sha256 is None
