"""Consumer Identity Verification — M2 Raw Bytes Identity Layer 黄金测试。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §2.2
- Identity 来源唯一：SHA256(raw bytes)。
  禁止：read_text() / splitlines() / strip() / canonical_json / sha256_hex()

覆盖：
1. CRLF 保真 — CRLF 与 LF 是不同 bytes，不同 sha256
2. trailing newline 保真 — 有/无尾部换行是不同 bytes，不同 sha256
3. unicode bytes — 多字节字符按原始 bytes 计算
4. text hash != bytes hash — read_text+splitlines 与 read_bytes 的 hash 必须不同（FACT-031 风险面）
"""

import hashlib
from pathlib import Path

import pytest

from app.core.raw_bytes_identity import RawBytesIdentity, load_raw_bytes_identity


# ── conftest migrated_db override ────────────────────────────────────────────
# 纯单元测试，无 DB 依赖；override session-scoped autouse fixture 以避免连库。

@pytest.fixture(autouse=True)
def migrated_db() -> None:
    """Override conftest autouse fixture — 本模块不需要数据库。"""


# ── helpers ──────────────────────────────────────────────────────────────────

def _write(tmp_path: Path, name: str, data: bytes) -> Path:
    p = tmp_path / name
    p.write_bytes(data)
    return p


# ── CRLF 保真 ─────────────────────────────────────────────────────────────────

def test_crlf_and_lf_produce_different_sha(tmp_path: Path) -> None:
    """CRLF (\\r\\n) 与 LF (\\n) 是不同的 source bytes，必须得出不同 sha256。"""
    lf = _write(tmp_path, "lf.md", b"line1\nline2\n")
    crlf = _write(tmp_path, "crlf.md", b"line1\r\nline2\r\n")

    id_lf = load_raw_bytes_identity(lf)
    id_crlf = load_raw_bytes_identity(crlf)

    assert id_lf.sha256 != id_crlf.sha256


def test_crlf_exact_hash_matches_raw_bytes(tmp_path: Path) -> None:
    """sha256 必须等于直接 hashlib.sha256(file.read_bytes()) 的结果。"""
    content = b"hello\r\nworld\r\n"
    p = _write(tmp_path, "exact.md", content)

    id_ = load_raw_bytes_identity(p)
    assert id_.sha256 == hashlib.sha256(content).hexdigest()


# ── trailing newline 保真 ─────────────────────────────────────────────────────

def test_trailing_newline_changes_hash(tmp_path: Path) -> None:
    """有/无尾部换行是不同的 source bytes。"""
    with_nl = _write(tmp_path, "with_nl.md", b"content\n")
    without_nl = _write(tmp_path, "no_nl.md", b"content")

    id_with = load_raw_bytes_identity(with_nl)
    id_without = load_raw_bytes_identity(without_nl)

    assert id_with.sha256 != id_without.sha256


# ── unicode bytes ─────────────────────────────────────────────────────────────

def test_unicode_bytes_hashed_as_raw_bytes(tmp_path: Path) -> None:
    """多字节 unicode 按原始 bytes 计算，不经 text normalization。"""
    content = "中文内容\nEnglish\nemoji: 🎓\n".encode("utf-8")
    p = _write(tmp_path, "unicode.md", content)

    id_ = load_raw_bytes_identity(p)
    assert id_.sha256 == hashlib.sha256(content).hexdigest()


def test_bom_preserved(tmp_path: Path) -> None:
    """BOM (\\xef\\xbb\\xbf) 是原始 bytes 的一部分，必须保留在 hash 输入中。"""
    with_bom = _write(tmp_path, "bom.md", b"\xef\xbb\xbfcontent\n")
    without_bom = _write(tmp_path, "nobom.md", b"content\n")

    id_bom = load_raw_bytes_identity(with_bom)
    id_nobom = load_raw_bytes_identity(without_bom)

    assert id_bom.sha256 != id_nobom.sha256


# ── text hash != bytes hash（核心风险面）──────────────────────────────────────

def test_text_hash_differs_from_bytes_hash(tmp_path: Path) -> None:
    """read_text()+splitlines() 得出的 hash 与 read_bytes() 的 hash 必须不同。

    这是 FACT-031 记录的风险面：text 读取会丢 CRLF/trailing newline 等信息，
    导致 hash drift。本测试确保 raw bytes 路径与 text 路径的结果不同。
    """
    content = b"line1\r\nline2\r\n"
    p = _write(tmp_path, "drift.md", content)

    # raw bytes 路径（正确）
    id_bytes = load_raw_bytes_identity(p)

    # text 路径（错误方式，用于对比）
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()
    joined = "\n".join(lines)
    hash_text = hashlib.sha256(joined.encode("utf-8")).hexdigest()

    assert id_bytes.sha256 != hash_text


# ── RawBytesIdentity 结构 ─────────────────────────────────────────────────────

def test_returns_frozen_dataclass(tmp_path: Path) -> None:
    p = _write(tmp_path, "simple.md", b"data\n")
    id_ = load_raw_bytes_identity(p)

    assert isinstance(id_, RawBytesIdentity)
    assert id_.bytes_source == str(p)
    assert len(id_.sha256) == 64
    assert id_.sha256 == id_.sha256.lower()


def test_sha256_is_lowercase_64_hex(tmp_path: Path) -> None:
    p = _write(tmp_path, "hex.md", b"anything\n")
    id_ = load_raw_bytes_identity(p)

    int(id_.sha256, 16)  # 确认是合法 hex
    assert all(c in "0123456789abcdef" for c in id_.sha256)


# ── 错误路径 ──────────────────────────────────────────────────────────────────

def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_raw_bytes_identity(tmp_path / "nonexistent.md")


# ── 禁止路径验证（防回归）─────────────────────────────────────────────────────

def test_does_not_use_text_path_for_hashing(tmp_path: Path) -> None:
    """确保实现没有 read_text()/splitlines() 参与 hash 计算。

    方法：构造一个 read_text 路径会丢信息的文件（CRLF + trailing newline），
    验证 hash 精确等于原始 bytes 的 sha256。
    """
    content = b"A\r\nB\r\n"  # read_text 会丢 \r，splitlines 会丢 trailing \n
    p = _write(tmp_path, "trap.md", content)

    id_ = load_raw_bytes_identity(p)
    assert id_.sha256 == hashlib.sha256(content).hexdigest()
