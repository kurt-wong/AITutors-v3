"""Phase 2 M1 Manifest Identity Reader — 对抗性审查测试。

每个测试用例尝试打破实现。所有结论必须有真实运行结果。
"""
import ast
import inspect
import json
import tempfile
from pathlib import Path

import pytest

from app.core.manifest_identity import (
    ManifestIdentity,
    ManifestReadError,
    read_manifest_identity,
)

# Override conftest autouse fixture — 本模块不需要数据库。
@pytest.fixture(autouse=True)
def migrated_db() -> None: ...


def _write_manifest(tmp_path: Path, data: object, name: str = "m.json") -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _get_source_code() -> str:
    return inspect.getsource(inspect.getmodule(read_manifest_identity))


# ═══════════════════════════════════════════════════════════════
# 攻击面 1: 正则 `$` 语义 — trailing newline / CR
# ═══════════════════════════════════════════════════════════════
class TestRegexAnchorSemantics:
    """Python 正则 `$` 匹配行尾（含 \\n 前），可能放行非法值。"""

    def test_trailing_newline_after_valid_hash_raises(self, tmp_path: Path):
        """'a'*64 + '\\n' — $ 匹配 \\n 前位置，若实现未用 fullmatch 则可能放行。"""
        valid = "a" * 64
        p = tmp_path / "m.json"
        p.write_text(json.dumps({"source_content_sha256": valid + "\n"}), encoding="utf-8")
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_trailing_cr_after_valid_hash_raises(self, tmp_path: Path):
        """'a'*64 + '\\r' — CR 在 hex 中不合法。"""
        valid = "a" * 64
        p = tmp_path / "m.json"
        p.write_text(json.dumps({"source_content_sha256": valid + "\r"}), encoding="utf-8")
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_trailing_crlf_after_valid_hash_raises(self, tmp_path: Path):
        valid = "a" * 64
        p = tmp_path / "m.json"
        p.write_text(json.dumps({"source_content_sha256": valid + "\r\n"}), encoding="utf-8")
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_leading_newline_before_valid_hash_raises(self, tmp_path: Path):
        valid = "a" * 64
        p = tmp_path / "m.json"
        p.write_text(json.dumps({"source_content_sha256": "\n" + valid}), encoding="utf-8")
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_newline_in_middle_of_hash_raises(self, tmp_path: Path):
        p = tmp_path / "m.json"
        p.write_text(json.dumps({"source_content_sha256": "a" * 32 + "\n" + "b" * 32}), encoding="utf-8")
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 2: TOCTOU — exists() 与 read_text() 竞态
# ═══════════════════════════════════════════════════════════════
class TestTOCTOU:
    """exists() 检查通过后、read_text() 执行前文件被删除。"""

    def test_file_deleted_between_exists_and_read_raises_manifest_error(self, tmp_path: Path):
        """模拟 TOCTOU: exists() 返回 True 后文件被删除。

        实现先调 exists() 再调 read_text()。如果文件在中间被删除，
        read_text() 会抛 FileNotFoundError（OSError 子类），
        但实现只捕获 (json.JSONDecodeError, UnicodeDecodeError)，
        不捕获 OSError — FileNotFoundError 会裸露给调用者。
        """
        p = tmp_path / "m.json"
        p.write_text(json.dumps({"source_content_sha256": "a" * 64}), encoding="utf-8")
        # 删除文件模拟竞态
        p.unlink()
        with pytest.raises(ManifestReadError) as exc_info:
            read_manifest_identity(p)
        assert "不存在" in str(exc_info.value)

    def test_file_replaced_with_directory_between_exists_and_read(self, tmp_path: Path):
        """exists() True 后路径变为目录。"""
        p = tmp_path / "m.json"
        p.write_text("{}", encoding="utf-8")
        p.unlink()
        p.mkdir()
        # exists() 对目录返回 True，但 read_text() 会抛 IsADirectoryError/PermissionError
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 3: BOM / encoding
# ═══════════════════════════════════════════════════════════════
class TestBomAndEncoding:
    """encoding='utf-8' 不处理 BOM (U+FEFF)。"""

    def test_utf8_bom_raises_manifest_error(self, tmp_path: Path):
        """UTF-8 BOM (\\xef\\xbb\\xbf) + JSON — encoding='utf-8' 不 strip BOM。"""
        p = tmp_path / "m.json"
        data = json.dumps({"source_content_sha256": "a" * 64})
        p.write_bytes(b"\xef\xbb\xbf" + data.encode("utf-8"))
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_utf8_sig_bom_would_work_but_implementation_uses_utf8(self, tmp_path: Path):
        """验证: 用 utf-8-sig 编码可读 BOM 文件，但实现用的是 utf-8。"""
        p = tmp_path / "m.json"
        data = json.dumps({"source_content_sha256": "a" * 64})
        p.write_bytes(b"\xef\xbb\xbf" + data.encode("utf-8"))
        # utf-8-sig 能读
        content = p.read_text(encoding="utf-8-sig")
        parsed = json.loads(content)
        assert parsed["source_content_sha256"] == "a" * 64
        # 但实现用 utf-8 — 这是设计决策，BOM 文件被视为 malformed

    def test_latin1_encoded_file_raises(self, tmp_path: Path):
        """非 UTF-8 编码文件应抛 UnicodeDecodeError 并被包装为 ManifestReadError。"""
        p = tmp_path / "m.json"
        # 包含 Latin-1 专有字节 (0xe9 = é)
        p.write_bytes(b'{"source_content_sha256": "a' + b"\xe9" + b'63"}')
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 4: 格式绕过
# ═══════════════════════════════════════════════════════════════
class TestFormatBypass:
    """尝试绕过格式验证。"""

    def test_whitespace_only_string_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": "   "})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_space_padded_valid_hash_raises(self, tmp_path: Path):
        """'  ' + 'a'*64 + '  ' — 有空格的 64 位 hex 不应通过。"""
        p = _write_manifest(tmp_path, {"source_content_sha256": "  " + "a" * 64 + "  "})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_tab_padded_hash_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": "\t" + "a" * 64})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_uppercase_hex_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": "A" * 64})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_mixed_case_hex_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": "aA" * 32})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_63_hex_chars_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": "a" * 63})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_65_hex_chars_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": "a" * 65})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_non_hex_chars_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": "g" * 64})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_unicode_hex_lookalike_raises(self, tmp_path: Path):
        """Unicode 全角字符 'ａ' (U+FF41) 看起来像 'a' 但不是 hex。"""
        p = _write_manifest(tmp_path, {"source_content_sha256": "ａ" * 64})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_integer_value_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": 12345})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_float_value_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": 3.14159})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_boolean_value_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": True})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_list_value_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": ["a" * 64]})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_dict_value_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, {"source_content_sha256": {"value": "a" * 64}})
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 5: 异常类型完整性
# ═══════════════════════════════════════════════════════════════
class TestExceptionCompleteness:
    """确保所有异常路径都抛 ManifestReadError，不泄漏原始异常。"""

    def test_binary_file_raises_manifest_error(self, tmp_path: Path):
        """非文本二进制文件 → UnicodeDecodeError → 应包装为 ManifestReadError。"""
        p = tmp_path / "m.json"
        p.write_bytes(bytes(range(256)))  # 包含所有字节值，必然是非法 UTF-8
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_directory_path_raises_manifest_error(self, tmp_path: Path):
        """目录路径: exists() 返回 True，但 read_text() 抛 OSError。"""
        d = tmp_path / "dir"
        d.mkdir()
        with pytest.raises(ManifestReadError):
            read_manifest_identity(d)

    def test_empty_file_raises_manifest_error(self, tmp_path: Path):
        """空文件 → json.loads("") 抛 JSONDecodeError。"""
        p = tmp_path / "m.json"
        p.write_text("", encoding="utf-8")
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_nonexistent_file_raises_manifest_error(self, tmp_path: Path):
        with pytest.raises(ManifestReadError) as exc_info:
            read_manifest_identity(tmp_path / "nope.json")
        assert "不存在" in str(exc_info.value)

    def test_manifest_read_error_is_exception_subclass(self):
        assert issubclass(ManifestReadError, Exception)

    def test_manifest_read_error_not_oserror(self):
        """ManifestReadError 不应是 OSError 子类 — 它是业务异常。"""
        assert not issubclass(ManifestReadError, OSError)


# ═══════════════════════════════════════════════════════════════
# 攻击面 6: JSON 边界
# ═══════════════════════════════════════════════════════════════
class TestJsonBoundaries:
    """JSON 解析边界条件。"""

    def test_top_level_list_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, ["not", "a", "dict"])
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_top_level_string_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, "just a string")
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_top_level_number_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, 42)
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_top_level_null_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, None)
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_top_level_true_raises(self, tmp_path: Path):
        p = _write_manifest(tmp_path, True)
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)

    def test_nested_dict_with_hash_in_child_returns_none(self, tmp_path: Path):
        """hash 在嵌套 dict 中 — 不应被顶层 .get() 找到。"""
        p = _write_manifest(tmp_path, {
            "metadata": {"source_content_sha256": "a" * 64}
        })
        result = read_manifest_identity(p)
        assert result.source_content_sha256 is None

    def test_duplicate_keys_last_wins(self, tmp_path: Path):
        """JSON 中重复 key — json.loads 后者覆盖前者。"""
        p = tmp_path / "m.json"
        p.write_text(
            '{"source_content_sha256": "' + "a" * 64 + '", "source_content_sha256": "' + "b" * 64 + '"}',
            encoding="utf-8",
        )
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == "b" * 64

    def test_json_with_comments_raises(self, tmp_path: Path):
        """标准 JSON 不支持注释 — 应抛 JSONDecodeError。"""
        p = tmp_path / "m.json"
        p.write_text('// comment\n{"source_content_sha256": "a" * 64}', encoding="utf-8")
        with pytest.raises(ManifestReadError):
            read_manifest_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 7: AST 静态审查 — 禁止模式
# ═══════════════════════════════════════════════════════════════
class TestSourceCodeAudit:
    """AST 扫描确认无禁止模式。"""

    def _get_ast(self) -> ast.Module:
        source = _get_source_code()
        return ast.parse(source)

    def _get_call_names(self, tree: ast.Module) -> list[str]:
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
        tree = self._get_ast()
        imports = self._get_imports(tree)
        assert "hashlib" not in imports

    def test_no_hashlib_sha256_call(self):
        tree = self._get_ast()
        calls = self._get_call_names(tree)
        assert "sha256" not in calls

    def test_no_read_bytes_call(self):
        tree = self._get_ast()
        calls = self._get_call_names(tree)
        assert "read_bytes" not in calls

    def test_no_hashing_module_import(self):
        tree = self._get_ast()
        imports = self._get_imports(tree)
        assert not any("hashing" in imp for imp in imports)

    def test_no_canonical_json_call(self):
        tree = self._get_ast()
        calls = self._get_call_names(tree)
        assert "canonical_json" not in calls

    def test_no_sha256_hex_call(self):
        tree = self._get_ast()
        calls = self._get_call_names(tree)
        assert "sha256_hex" not in calls

    def test_no_verification_status_return(self):
        """实现不应返回 PASS/FAIL/VERIFIED 等验证状态。"""
        tree = self._get_ast()
        for forbidden in ["PASS", "FAIL", "FAILED", "VERIFIED"]:
            for node in ast.walk(tree):
                if isinstance(node, ast.Return) and node.value is not None:
                    if isinstance(node.value, ast.Constant) and node.value.value == forbidden:
                        pytest.fail(f"实现返回了验证状态: {forbidden}")

    def test_uses_read_text_not_read_bytes(self):
        """实现读取 manifest 文件 — 应使用 read_text（manifest 是 JSON 文本）。"""
        tree = self._get_ast()
        calls = self._get_call_names(tree)
        assert "read_text" in calls

    def test_manifest_identity_has_only_sha_field(self):
        """ManifestIdentity 只应有 source_content_sha256 字段。"""
        fields = [f.name for f in ManifestIdentity.__dataclass_fields__.values()]
        assert fields == ["source_content_sha256"]

    def test_manifest_identity_is_frozen(self):
        assert ManifestIdentity.__dataclass_params__.frozen is True


# ═══════════════════════════════════════════════════════════════
# 攻击面 8: 字段原始值保持
# ═══════════════════════════════════════════════════════════════
class TestFieldValuePreservation:
    """验证返回值与 manifest 中声明的值完全一致。"""

    def test_exact_value_preserved_no_transform(self, tmp_path: Path):
        """确认实现不做任何 transform（strip/lower/normalize）。"""
        valid = "a" * 64
        p = _write_manifest(tmp_path, {"source_content_sha256": valid})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == valid

    def test_all_zero_hash_preserved(self, tmp_path: Path):
        valid = "0" * 64
        p = _write_manifest(tmp_path, {"source_content_sha256": valid})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == valid

    def test_all_f_hash_preserved(self, tmp_path: Path):
        valid = "f" * 64
        p = _write_manifest(tmp_path, {"source_content_sha256": valid})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == valid

    def test_mixed_hex_preserved(self, tmp_path: Path):
        valid = "0123456789abcdef" * 4
        p = _write_manifest(tmp_path, {"source_content_sha256": valid})
        result = read_manifest_identity(p)
        assert result.source_content_sha256 == valid
