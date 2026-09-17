"""M3 IR Identity Reader — 第二轮对抗性审查。

针对已有 52 测试未覆盖的攻击面：
JSON Unicode 转义、NaN/Infinity、深层嵌套、dataclass 隐藏字段、
模块级状态、异常信息泄漏、M1/M3 一致性。
"""
import dataclasses
import json
import sys
from pathlib import Path

import pytest

from app.core.ir_identity import IRIdentity, IRReadError, read_ir_identity
from app.core.manifest_identity import ManifestIdentity, ManifestReadError, read_manifest_identity


@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest autouse fixture — 本模块不需要数据库。"""


def _write(tmp_path: Path, content: str, name: str = "ir.json") -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def _write_json(tmp_path: Path, data: object, name: str = "ir.json") -> Path:
    return _write(tmp_path, json.dumps(data), name)


# ═══════════════════════════════════════════════════════════════
# 攻击面 A: JSON Unicode 转义绕过
# ═══════════════════════════════════════════════════════════════
class TestJsonUnicodeEscape:
    """JSON \\uXXXX 转义在 parse 后变为普通字符 — 验证实现处理的是 decode 后的值。"""

    def test_unicode_escape_decodes_to_valid_hex(self, tmp_path: Path):
        """'\\u0061' 解码为 'a' — 如果 64 个 \\u0061 解码后是 'a'*64，应被接受。"""
        escaped = "".join("\\u0061" for _ in range(64))
        p = _write(tmp_path, '{"source_content_sha256": "' + escaped + '"}')
        result = read_ir_identity(p)
        assert result.source_content_sha256 == "a" * 64

    def test_unicode_escape_uppercase_hex_rejected(self, tmp_path: Path):
        """'\\u0041' 解码为 'A' — 大写 hex 应被拒绝。"""
        escaped = "".join("\\u0041" for _ in range(64))
        p = _write(tmp_path, '{"source_content_sha256": "' + escaped + '"}')
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_unicode_escape_non_hex_rejected(self, tmp_path: Path):
        """'\\u0067' 解码为 'g' — 非 hex 应被拒绝。"""
        escaped = "".join("\\u0067" for _ in range(64))
        p = _write(tmp_path, '{"source_content_sha256": "' + escaped + '"}')
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_mixed_escape_and_literal(self, tmp_path: Path):
        """部分转义 + 部分字面量 — 解码后应一致处理。"""
        # 32 个 literal 'a' + 32 个 b ('b')
        mixed = "a" * 32 + "".join("\\u0062" for _ in range(32))
        p = _write(tmp_path, '{"source_content_sha256": "' + mixed + '"}')
        result = read_ir_identity(p)
        assert result.source_content_sha256 == "a" * 32 + "b" * 32

    def test_unicode_escape_newline_rejected(self, tmp_path: Path):
        """'\\u000a' 解码为 newline — 应被拒绝。"""
        escaped = "a" * 63 + "\\u000a"
        p = _write(tmp_path, '{"source_content_sha256": "' + escaped + '"}')
        with pytest.raises(IRReadError):
            read_ir_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 B: JSON NaN / Infinity
# ═══════════════════════════════════════════════════════════════
class TestJsonNonStandardValues:
    """JSON 规范不允许 NaN/Infinity，但 Python json.loads 默认接受。"""

    def test_nan_value_raises(self, tmp_path: Path):
        p = _write(tmp_path, '{"source_content_sha256": NaN}')
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_infinity_value_raises(self, tmp_path: Path):
        p = _write(tmp_path, '{"source_content_sha256": Infinity}')
        with pytest.raises(IRReadError):
            read_ir_identity(p)

    def test_negative_infinity_value_raises(self, tmp_path: Path):
        p = _write(tmp_path, '{"source_content_sha256": -Infinity}')
        with pytest.raises(IRReadError):
            read_ir_identity(p)


# ═══════════════════════════════════════════════════════════════
# 攻击面 C: 深层嵌套 JSON
# ═══════════════════════════════════════════════════════════════
class TestDeepNesting:
    """深层嵌套 JSON — 不应导致栈溢出或意外行为。"""

    def test_100_level_nesting_returns_none(self, tmp_path: Path):
        """100 层嵌套，source_content_sha256 在最深层 — 顶层 get 应返回 None。"""
        inner: dict = {"source_content_sha256": "a" * 64}
        for _ in range(100):
            inner = {"nested": inner}
        p = _write_json(tmp_path, inner)
        result = read_ir_identity(p)
        assert result.source_content_sha256 is None

    def test_1000_level_nesting_raises_or_returns_none(self, tmp_path: Path):
        """1000 层嵌套 — json.loads 可能 RecursionError，应包装为 IRReadError。"""
        inner: dict = {"v": 1}
        for _ in range(1000):
            inner = {"nested": inner}
        p = _write_json(tmp_path, inner)
        try:
            result = read_ir_identity(p)
            assert result.source_content_sha256 is None
        except RecursionError:
            pytest.fail("RecursionError 未被 IRReadError 捕获 — 实现缺陷")


# ═══════════════════════════════════════════════════════════════
# 攻击面 D: dataclass 隐藏字段
# ═══════════════════════════════════════════════════════════════
class TestHiddenDataclassFields:
    """dataclass 自动生成的隐藏字段不应被误认为业务字段。"""

    def test_no_dict_leak_of_internal_fields(self, tmp_path: Path):
        p = _write_json(tmp_path, {"source_content_sha256": "a" * 64})
        result = read_ir_identity(p)
        # __dict__ 应只包含声明的字段
        assert set(result.__dict__.keys()) == {"source_content_sha256"}

    def test_slots_if_defined_matches_declared(self, tmp_path: Path):
        """如果 dataclass 使用 __slots__，应与声明字段一致。"""
        if hasattr(IRIdentity, "__slots__"):
            assert set(IRIdentity.__slots__) == {"source_content_sha256"}
        # 没有 __slots__ 也可以 — frozen dataclass 默认用 __dict__

    def test_weakref_not_in_declared_fields(self):
        """__weakref__ 不应在 dataclass 声明字段中。"""
        field_names = {f.name for f in dataclasses.fields(IRIdentity)}
        assert "__weakref__" not in field_names

    def test_dataclass_fields_count_is_exactly_one(self):
        assert len(dataclasses.fields(IRIdentity)) == 1

    def test_dataclass_equality(self, tmp_path: Path):
        """两个相同 sha 的 IRIdentity 应相等。"""
        p1 = _write_json(tmp_path, {"source_content_sha256": "a" * 64}, name="a.json")
        p2 = _write_json(tmp_path, {"source_content_sha256": "a" * 64}, name="b.json")
        r1 = read_ir_identity(p1)
        r2 = read_ir_identity(p2)
        assert r1 == r2

    def test_dataclass_inequality_different_sha(self, tmp_path: Path):
        p1 = _write_json(tmp_path, {"source_content_sha256": "a" * 64}, name="a.json")
        p2 = _write_json(tmp_path, {"source_content_sha256": "b" * 64}, name="b.json")
        assert read_ir_identity(p1) != read_ir_identity(p2)


# ═══════════════════════════════════════════════════════════════
# 攻击面 E: 模块级状态
# ═══════════════════════════════════════════════════════════════
class TestModuleState:
    """模块级变量不应可变或被意外修改。"""

    def test_regex_is_compiled_at_module_level(self):
        """正则应在模块级预编译 — 不应在函数内每次重新编译。"""
        import app.core.ir_identity as mod
        assert hasattr(mod, "_SHA256_LOWER_HEX_RE")
        import re
        assert isinstance(mod._SHA256_LOWER_HEX_RE, re.Pattern)

    def test_version_is_string_constant(self):
        import app.core.ir_identity as mod
        assert isinstance(mod.IR_IDENTITY_VERSION, str)

    def test_no_module_level_mutable_state(self):
        """模块不应有可变的全局状态（list/dict/set）。"""
        import app.core.ir_identity as mod
        for name, value in vars(mod).items():
            if name.startswith("_"):
                continue
            if isinstance(value, (list, dict, set)):
                pytest.fail(f"模块级可变状态: {name} = {type(value).__name__}")


# ═══════════════════════════════════════════════════════════════
# 攻击面 F: 异常信息内容
# ═══════════════════════════════════════════════════════════════
class TestExceptionMessageContent:
    """异常信息应包含诊断上下文，但不泄漏无关系统信息。"""

    def test_not_found_returns_none(self, tmp_path: Path):
        """Design v1.1 §4.4: IR missing → None, 不抛异常。"""
        result = read_ir_identity(tmp_path / "missing_ir.json")
        assert result.source_content_sha256 is None

    def test_invalid_format_message_contains_value(self, tmp_path: Path):
        p = _write_json(tmp_path, {"source_content_sha256": "not_a_hash"})
        with pytest.raises(IRReadError) as exc_info:
            read_ir_identity(p)
        assert "not_a_hash" in str(exc_info.value)

    def test_invalid_format_message_contains_expectation(self, tmp_path: Path):
        p = _write_json(tmp_path, {"source_content_sha256": "short"})
        with pytest.raises(IRReadError) as exc_info:
            read_ir_identity(p)
        assert "64" in str(exc_info.value)

    def test_ir_read_error_message_is_str(self, tmp_path: Path):
        p = _write_json(tmp_path, {"source_content_sha256": "bad"})
        with pytest.raises(IRReadError) as exc_info:
            read_ir_identity(p)
        assert isinstance(str(exc_info.value), str)


# ═══════════════════════════════════════════════════════════════
# 攻击面 G: M1/M3 一致性
# ═══════════════════════════════════════════════════════════════
class TestM1M3Consistency:
    """M1 (manifest) 和 M3 (IR) 应对相同输入产生相同行为。"""

    def _make_both(self, tmp_path: Path, data: object) -> tuple[Path, Path]:
        ir = _write_json(tmp_path, data, name="ir.json")
        mf = _write_json(tmp_path, data, name="manifest.json")
        return ir, mf

    def test_valid_sha_both_accept(self, tmp_path: Path):
        ir, mf = self._make_both(tmp_path, {"source_content_sha256": "a" * 64})
        assert read_ir_identity(ir).source_content_sha256 == "a" * 64
        assert read_manifest_identity(mf).source_content_sha256 == "a" * 64

    def test_missing_sha_both_return_none(self, tmp_path: Path):
        ir, mf = self._make_both(tmp_path, {"other": "field"})
        assert read_ir_identity(ir).source_content_sha256 is None
        assert read_manifest_identity(mf).source_content_sha256 is None

    def test_uppercase_both_reject(self, tmp_path: Path):
        ir, mf = self._make_both(tmp_path, {"source_content_sha256": "A" * 64})
        with pytest.raises(IRReadError):
            read_ir_identity(ir)
        with pytest.raises(ManifestReadError):
            read_manifest_identity(mf)

    def test_trailing_newline_both_reject(self, tmp_path: Path):
        ir, mf = self._make_both(tmp_path, {"source_content_sha256": "a" * 64 + "\n"})
        with pytest.raises(IRReadError):
            read_ir_identity(ir)
        with pytest.raises(ManifestReadError):
            read_manifest_identity(mf)

    def test_non_dict_both_reject(self, tmp_path: Path):
        ir, mf = self._make_both(tmp_path, [1, 2, 3])
        with pytest.raises(IRReadError):
            read_ir_identity(ir)
        with pytest.raises(ManifestReadError):
            read_manifest_identity(mf)

    def test_directory_both_reject(self, tmp_path: Path):
        d_ir = tmp_path / "ir_dir"
        d_ir.mkdir()
        d_mf = tmp_path / "mf_dir"
        d_mf.mkdir()
        with pytest.raises(IRReadError):
            read_ir_identity(d_ir)
        with pytest.raises(ManifestReadError):
            read_manifest_identity(d_mf)

    def test_bom_both_reject(self, tmp_path: Path):
        data = json.dumps({"source_content_sha256": "a" * 64}).encode("utf-8")
        ir = tmp_path / "ir.json"
        ir.write_bytes(b"\xef\xbb\xbf" + data)
        mf = tmp_path / "mf.json"
        mf.write_bytes(b"\xef\xbb\xbf" + data)
        with pytest.raises(IRReadError):
            read_ir_identity(ir)
        with pytest.raises(ManifestReadError):
            read_manifest_identity(mf)

    def test_error_types_are_distinct(self):
        """M1 和 M3 的异常类型必须不同 — 调用者需区分来源。"""
        assert IRReadError is not ManifestReadError
        assert not issubclass(IRReadError, ManifestReadError)
        assert not issubclass(ManifestReadError, IRReadError)

    def test_identity_types_are_distinct(self):
        assert IRIdentity is not ManifestIdentity

    def test_both_frozen(self):
        assert IRIdentity.__dataclass_params__.frozen is True
        assert ManifestIdentity.__dataclass_params__.frozen is True
