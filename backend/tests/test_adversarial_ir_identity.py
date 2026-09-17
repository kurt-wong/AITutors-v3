"""M3 IR Identity Reader — 对抗性审查测试。

攻击面：正则锚点、TOCTOU、BOM、格式绕过、异常完整性、JSON 边界、AST 静态审查、值保真。
"""
import ast
import inspect
import json
from pathlib import Path

import pytest

from app.core.ir_identity import IRIdentity, IRReadError, read_ir_identity


@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest autouse fixture — 本模块不需要数据库。"""


def _write_ir(tmp_path: Path, data: object, name: str = "resolver_ir.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _get_source_code() -> str:
    return inspect.getsource(inspect.getmodule(read_ir_identity))


# ═══════════════════════════════════════════════════════════════
# 攻击面 1: 正则锚点语义
# ═══════════════════════════════════════════════════════════════
class TestRegexAnchorSemantics:
    def test_trailing_newline_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "a" * 64 + "\n"})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_trailing_cr_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "a" * 64 + "\r"})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_trailing_crlf_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "a" * 64 + "\r\n"})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_leading_newline_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "\n" + "a" * 64})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_newline_in_middle_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "a" * 32 + "\n" + "b" * 32})
        with pytest.raises(IRReadError):
            read_ir_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 2: TOCTOU
# ═══════════════════════════════════════════════════════════════
class TestTOCTOU:
    def test_file_deleted_between_exists_and_read(self, tmp_path: Path):
        """文件已删除 → exists()=False → 返回 None（Design v1.1 §4.4）。"""
        p = _write_ir(tmp_path, {"source_content_sha256": "a" * 64})
        p.unlink()
        result = read_ir_identity(p)
        assert result.source_content_sha256 is None

    def test_file_replaced_with_directory(self, tmp_path: Path):
        p = _write_ir(tmp_path, {})
        p.unlink()
        p.mkdir()
        with pytest.raises(IRReadError):
            read_ir_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 3: BOM / encoding
# ═══════════════════════════════════════════════════════════════
class TestBomAndEncoding:
    def test_utf8_bom_raises(self, tmp_path: Path):
        p = tmp_path / "resolver_ir.json"
        data = json.dumps({"source_content_sha256": "a" * 64})
        p.write_bytes(b"\xef\xbb\xbf" + data.encode("utf-8"))
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_binary_file_raises(self, tmp_path: Path):
        p = tmp_path / "resolver_ir.json"
        p.write_bytes(bytes(range(256)))
        with pytest.raises(IRReadError):
            read_ir_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 4: 格式绕过
# ═══════════════════════════════════════════════════════════════
class TestFormatBypass:
    def test_whitespace_only_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "   "})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_space_padded_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "  " + "a" * 64 + "  "})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_tab_padded_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "\t" + "a" * 64})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_uppercase_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "A" * 64})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_mixed_case_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "aA" * 32})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_non_hex_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "g" * 64})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_unicode_lookalike_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": "ａ" * 64})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_integer_value_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": 12345})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_float_value_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": 3.14})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_bool_value_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": True})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_list_value_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": ["a" * 64]})
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_dict_value_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"source_content_sha256": {"v": "a" * 64}})
        with pytest.raises(IRReadError):
            read_ir_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 5: 异常完整性
# ═══════════════════════════════════════════════════════════════
class TestExceptionCompleteness:
    def test_empty_file_raises(self, tmp_path: Path):
        p = tmp_path / "resolver_ir.json"
        p.write_text("", encoding="utf-8")
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_directory_raises(self, tmp_path: Path):
        d = tmp_path / "dir"
        d.mkdir()
        with pytest.raises(IRReadError):
            read_ir_identity(d)

    def test_nonexistent_returns_none(self, tmp_path: Path):
        """Design v1.1 §4.4: IR missing → None, 不抛异常。"""
        result = read_ir_identity(tmp_path / "nope.json")
        assert result.source_content_sha256 is None

    def test_ir_read_error_is_exception(self):
        assert issubclass(IRReadError, Exception)

    def test_ir_read_error_not_oserror(self):
        assert not issubclass(IRReadError, OSError)


# ═══════════════════════════════════════════════════════════════
# 攻击面 6: JSON 边界
# ═══════════════════════════════════════════════════════════════
class TestJsonBoundaries:
    def test_top_level_list_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, [1, 2, 3])
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_top_level_string_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, "string")
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_top_level_number_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, 42)
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_top_level_null_raises(self, tmp_path: Path):
        p = _write_ir(tmp_path, None)
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_nested_sha_returns_none(self, tmp_path: Path):
        p = _write_ir(tmp_path, {"meta": {"source_content_sha256": "a" * 64}})
        result = read_ir_identity(p)
        assert result.source_content_sha256 is None

    def test_duplicate_keys_last_wins(self, tmp_path: Path):
        p = tmp_path / "resolver_ir.json"
        p.write_text(
            '{"source_content_sha256": "' + "a" * 64 + '", "source_content_sha256": "' + "b" * 64 + '"}',
            encoding="utf-8",
        )
        result = read_ir_identity(p)
        assert result.source_content_sha256 == "b" * 64

    def test_json_comments_raises(self, tmp_path: Path):
        p = tmp_path / "resolver_ir.json"
        p.write_text('// c\n{"source_content_sha256": "a" * 64}', encoding="utf-8")
        with pytest.raises(IRReadError):
            read_ir_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 7: AST 静态审查
# ═══════════════════════════════════════════════════════════════
class TestSourceCodeAudit:
    def _get_ast(self) -> ast.Module:
        return ast.parse(_get_source_code())

    def _get_calls(self, tree: ast.Module) -> list[str]:
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    names.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    names.append(node.func.attr)
        return names

    def _get_imports(self, tree: ast.Module) -> list[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def test_no_hashlib_import(self):
        assert "hashlib" not in self._get_imports(self._get_ast())

    def test_no_hashlib_sha256_call(self):
        assert "sha256" not in self._get_calls(self._get_ast())

    def test_no_read_bytes_call(self):
        assert "read_bytes" not in self._get_calls(self._get_ast())

    def test_no_hashing_module_import(self):
        imports = self._get_imports(self._get_ast())
        assert not any("hashing" in imp for imp in imports)

    def test_no_canonical_json_call(self):
        assert "canonical_json" not in self._get_calls(self._get_ast())

    def test_no_sha256_hex_call(self):
        assert "sha256_hex" not in self._get_calls(self._get_ast())

    def test_no_verification_status_return(self):
        tree = self._get_ast()
        for forbidden in ["PASS", "FAIL", "FAILED", "VERIFIED"]:
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and node.value is not None:
                    if isinstance(node.value, ast.Constant) and node.value.value == forbidden:
                        pytest.fail(f"返回了验证状态: {forbidden}")

    def test_uses_read_text(self):
        assert "read_text" in self._get_calls(self._get_ast())

    def test_ir_identity_frozen(self):
        assert IRIdentity.__dataclass_params__.frozen is True

    def test_ir_identity_only_sha_field(self):
        fields = [f.name for f in IRIdentity.__dataclass_fields__.values()]
        assert fields == ["source_content_sha256"]


# ═══════════════════════════════════════════════════════════════
# 攻击面 8: 值保真
# ═══════════════════════════════════════════════════════════════
class TestFieldValuePreservation:
    def test_exact_value_preserved(self, tmp_path: Path):
        valid = "a" * 64
        p = _write_ir(tmp_path, {"source_content_sha256": valid})
        assert read_ir_identity(p).source_content_sha256 == valid

    def test_all_zeros_preserved(self, tmp_path: Path):
        valid = "0" * 64
        p = _write_ir(tmp_path, {"source_content_sha256": valid})
        assert read_ir_identity(p).source_content_sha256 == valid

    def test_all_f_preserved(self, tmp_path: Path):
        valid = "f" * 64
        p = _write_ir(tmp_path, {"source_content_sha256": valid})
        assert read_ir_identity(p).source_content_sha256 == valid

    def test_mixed_hex_preserved(self, tmp_path: Path):
        valid = "0123456789abcdef" * 4
        p = _write_ir(tmp_path, {"source_content_sha256": valid})
        assert read_ir_identity(p).source_content_sha256 == valid
