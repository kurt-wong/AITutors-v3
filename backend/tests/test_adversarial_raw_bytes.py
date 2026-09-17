"""对抗性审查 — Phase 1 Raw Bytes Identity Layer。

目标：攻击实现的每个薄弱点。每个结论必须有真实测试证据。
不降低标准，不自我合理化，不推测。
"""

import ast
import hashlib
import os
import stat
import sys
from pathlib import Path

import pytest

from app.core.raw_bytes_identity import RawBytesIdentity, load_raw_bytes_identity

# conftest migrated_db override
@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest autouse fixture."""


# ══════════════════════════════════════════════════════════════
# 攻击面 1：哈希正确性 — 对照已知 SHA-256 常量，非自证
# ══════════════════════════════════════════════════════════════

class TestHashCorrectnessAgainstKnownConstants:
    """已有测试用 hashlib.sha256(data).hexdigest() 自证 — 循环论证。
    此处用公开已知的 SHA-256 常量独立验证。"""

    def test_empty_file_hash_matches_rfc_constants(self, tmp_path: Path) -> None:
        """SHA256(b"") = e3b0c442... 是公开已知常量。
        若实现有任何 text normalization（如 strip），空文件结果会不同。"""
        p = tmp_path / "empty.bin"
        p.write_bytes(b"")
        result = load_raw_bytes_identity(p)
        # SHA-256 of empty input — well-known constant
        assert result.sha256 == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_single_byte_hash_matches_known(self, tmp_path: Path) -> None:
        """SHA256(b"a") = ca978112... 公开已知常量。"""
        p = tmp_path / "single.bin"
        p.write_bytes(b"a")
        result = load_raw_bytes_identity(p)
        assert result.sha256 == "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"

    def test_cross_check_with_file_digest(self, tmp_path: Path) -> None:
        """Python 3.11+ hashlib.file_digest — 独立读取路径，验证一致性。"""
        if sys.version_info < (3, 11):
            pytest.skip("hashlib.file_digest requires Python 3.11+")
        data = b"cross-check-data-\x00\xff\xfe"
        p = tmp_path / "cross.bin"
        p.write_bytes(data)
        result = load_raw_bytes_identity(p)
        with open(p, "rb") as f:
            file_digest = hashlib.file_digest(f, "sha256").hexdigest()
        assert result.sha256 == file_digest


# ══════════════════════════════════════════════════════════════
# 攻击面 2：路径类型攻击 — 目录、权限、特殊路径
# ══════════════════════════════════════════════════════════════

class TestPathAttacks:
    def test_directory_path_raises_oserror(self, tmp_path: Path) -> None:
        """read_bytes() 在目录上应抛 OSError 子类。
        Windows: PermissionError; POSIX: IsADirectoryError。两者都是 OSError 子类。"""
        with pytest.raises(OSError):
            load_raw_bytes_identity(tmp_path)

    def test_nonexistent_path_raises_filenotfound(self, tmp_path: Path) -> None:
        """FileNotFoundError 是 OSError 子类，docstring 声明正确。"""
        with pytest.raises(FileNotFoundError):
            load_raw_bytes_identity(tmp_path / "no_such_file.md")

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission test")
    def test_permission_denied_raises_oserror(self, tmp_path: Path) -> None:
        """chmod 000 的文件应抛 PermissionError（OSError 子类）。"""
        p = tmp_path / "noperm.bin"
        p.write_bytes(b"secret")
        os.chmod(p, 0)
        try:
            with pytest.raises(PermissionError):
                load_raw_bytes_identity(p)
        finally:
            os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)

    def test_unicode_filename(self, tmp_path: Path) -> None:
        """文件名含中文/emoji，不影响 sha256 计算。"""
        p = tmp_path / "试卷-2024-化学-🧬.md"
        data = "你好世界".encode("utf-8")
        p.write_bytes(data)
        result = load_raw_bytes_identity(p)
        assert result.sha256 == hashlib.sha256(data).hexdigest()
        assert "试卷" in result.bytes_source


# ══════════════════════════════════════════════════════════════
# 攻击面 3：bytes_source 作为 locator 的行为验证
# ══════════════════════════════════════════════════════════════

class TestBytesSourceAsLocator:
    def test_relative_vs_absolute_path_same_sha_different_source(self, tmp_path: Path) -> None:
        """同一文件，relative path vs absolute path → sha 相同，bytes_source 不同。
        这验证了 path 是 locator 不是 identity。"""
        data = b"locator-test-data"
        p = tmp_path / "loc.md"
        p.write_bytes(data)

        abs_result = load_raw_bytes_identity(p)
        # 用 chdir 测 relative path
        old_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            rel_result = load_raw_bytes_identity(Path("loc.md"))
        finally:
            os.chdir(old_cwd)

        assert abs_result.sha256 == rel_result.sha256
        assert abs_result.bytes_source != rel_result.bytes_source

    def test_bytes_source_stores_exact_path_string(self, tmp_path: Path) -> None:
        """bytes_source = str(source_path) — 精确保留传入的 path 表示。"""
        p = tmp_path / "exact.md"
        p.write_bytes(b"exact")
        result = load_raw_bytes_identity(p)
        assert result.bytes_source == str(p)

    def test_bytes_source_not_used_for_hashing(self, tmp_path: Path) -> None:
        """bytes_source 改变不影响 sha256 — 同内容不同路径，sha 相同。"""
        data = b"same-content-different-path"
        p1 = tmp_path / "path_a" / "file.md"
        p2 = tmp_path / "path_b" / "file.md"
        p1.parent.mkdir()
        p2.parent.mkdir()
        p1.write_bytes(data)
        p2.write_bytes(data)

        r1 = load_raw_bytes_identity(p1)
        r2 = load_raw_bytes_identity(p2)

        assert r1.sha256 == r2.sha256
        assert r1.bytes_source != r2.bytes_source


# ══════════════════════════════════════════════════════════════
# 攻击面 4：read_text vs read_bytes 真实分歧 — 加强验证
# ══════════════════════════════════════════════════════════════

class TestTextVsBytesDivergence:
    def test_latin1_vs_utf8_interpretation_same_bytes(self, tmp_path: Path) -> None:
        """同一 raw bytes，若被 read_text(encoding='latin-1') 再 encode('utf-8')，
        会产生不同 bytes → 不同 sha。实现必须用 read_bytes() 绕过编码。"""
        raw = b"\xe4\xbd\xa0\xe5\xa5\xbd"  # "你好" in UTF-8
        p = tmp_path / "enc.md"
        p.write_bytes(raw)

        result = load_raw_bytes_identity(p)
        # read_bytes sha
        assert result.sha256 == hashlib.sha256(raw).hexdigest()
        # If someone did read_text("latin-1").encode("utf-8") — DIFFERENT
        wrong = raw.decode("latin-1").encode("utf-8")
        wrong_sha = hashlib.sha256(wrong).hexdigest()
        assert result.sha256 != wrong_sha  # 确认分歧存在，实现走对了路

    def test_null_bytes_preserved(self, tmp_path: Path) -> None:
        """Null bytes 在 read_text 中可能被截断或报错。read_bytes 必须保真。"""
        raw = b"before\x00middle\x00after"
        p = tmp_path / "null.md"
        p.write_bytes(raw)
        result = load_raw_bytes_identity(p)
        assert result.sha256 == hashlib.sha256(raw).hexdigest()

    def test_all_byte_values_0_to_255(self, tmp_path: Path) -> None:
        """全部 256 种字节值 — 极端保真测试。"""
        raw = bytes(range(256))
        p = tmp_path / "all256.bin"
        p.write_bytes(raw)
        result = load_raw_bytes_identity(p)
        assert result.sha256 == hashlib.sha256(raw).hexdigest()

    def test_utf16_bom_bytes(self, tmp_path: Path) -> None:
        """UTF-16 LE BOM (FF FE) — read_text 会解码并丢 BOM，read_bytes 保真。"""
        raw = b"\xff\xfeH\x00e\x00l\x00l\x00o\x00"  # "Hello" in UTF-16 LE with BOM
        p = tmp_path / "utf16.md"
        p.write_bytes(raw)
        result = load_raw_bytes_identity(p)
        assert result.sha256 == hashlib.sha256(raw).hexdigest()
        # If someone did read_text("utf-16") → "Hello" → encode("utf-8") → different bytes
        wrong = "Hello".encode("utf-8")
        wrong_sha = hashlib.sha256(wrong).hexdigest()
        assert result.sha256 != wrong_sha


# ══════════════════════════════════════════════════════════════
# 攻击面 5：dataclass 不变性与类型契约
# ══════════════════════════════════════════════════════════════

class TestDataclassContract:
    def test_frozen_dataclass_rejects_mutation(self, tmp_path: Path) -> None:
        p = tmp_path / "frozen.md"
        p.write_bytes(b"frozen")
        result = load_raw_bytes_identity(p)
        with pytest.raises(AttributeError):
            result.sha256 = "hacked"
        with pytest.raises(AttributeError):
            result.bytes_source = "hacked"

    def test_sha256_field_is_exactly_64_lowercase_hex(self, tmp_path: Path) -> None:
        p = tmp_path / "hex.md"
        p.write_bytes(b"hex-check")
        result = load_raw_bytes_identity(p)
        assert len(result.sha256) == 64
        assert all(c in "0123456789abcdef" for c in result.sha256)

    def test_bytes_source_is_string_type(self, tmp_path: Path) -> None:
        p = tmp_path / "type.md"
        p.write_bytes(b"type")
        result = load_raw_bytes_identity(p)
        assert isinstance(result.bytes_source, str)
        assert isinstance(result.sha256, str)


# ══════════════════════════════════════════════════════════════
# 攻击面 6：实现源码审查 — 禁止模式扫描
# ══════════════════════════════════════════════════════════════

class TestSourceCodeAudit:
    """静态审查：实现源码不得包含禁止模式。"""

    def _get_source(self) -> str:
        import app.core.raw_bytes_identity as mod
        import inspect
        return inspect.getsource(mod)

    def _get_ast(self):
        import ast
        return ast.parse(self._get_source())

    def test_no_read_text_in_source(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr != "read_text", \
                        f"read_text() 调用发现于 line {node.lineno}"

    def test_no_splitlines_in_source(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr != "splitlines", \
                        f"splitlines() 调用发现于 line {node.lineno}"

    def test_no_strip_in_source(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in ("strip", "lstrip", "rstrip"), \
                        f"strip() 调用发现于 line {node.lineno}"

    def test_no_import_from_hashing_module(self) -> None:
        tree = self._get_ast()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module != "app.core.hashing", \
                    f"禁止 import from app.core.hashing 于 line {node.lineno}"
                assert node.module != ".hashing", \
                    f"禁止 import from .hashing 于 line {node.lineno}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "hashing" not in alias.name, \
                        f"禁止 import hashing 于 line {node.lineno}"

    def test_no_canonical_json_usage(self) -> None:
        """AST 扫描：代码中不得有 canonical_json / sha256_hex 的实际调用或 import。
        docstring 中的提及不算（那是禁止说明）。"""
        tree = self._get_ast()
        for node in ast.walk(tree):
            # 检查 import 语句
            if isinstance(node, ast.ImportFrom):
                names = [a.name for a in node.names]
                assert "canonical_json" not in names
                assert "sha256_hex" not in names
            # 检查函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in ("canonical_json", "sha256_hex")
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in ("canonical_json", "sha256_hex")

    def test_uses_read_bytes_not_read_text(self) -> None:
        src = self._get_source()
        assert "read_bytes" in src, "实现必须使用 read_bytes()"

    def test_uses_hashlib_sha256_directly(self) -> None:
        src = self._get_source()
        assert "hashlib.sha256" in src, "实现必须直接使用 hashlib.sha256"
