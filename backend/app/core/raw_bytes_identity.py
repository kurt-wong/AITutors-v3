"""Consumer Identity Verification — M2 Raw Bytes Identity Layer。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §2.2
- PREPROCESSING-V3-CONTRACT-v0.2 §5.6.1 (G-15)

身份语义：
- Identity 来源唯一：SHA256(raw bytes)。raw bytes = file.read_bytes() 的精确字节序列。
- CRLF / BOM / trailing newline / unicode 多字节字符全部保真。
- path 是 locator，不是 identity（DEC-031 原则 1）。

禁止（防回归）：
- read_text() / splitlines() / strip() — 会丢字节信息（FACT-031）
- app.core.hashing.sha256_hex — canonical_json wrap，V3 logical identity primitive
- 任何 text normalization — 源字节不经规范化
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

RAW_BYTES_IDENTITY_VERSION = "1.0.0"


@dataclass(frozen=True)
class RawBytesIdentity:
    """一个 source file 的 raw bytes 身份。

    bytes_source: 文件路径字符串（locator，非 identity）。
    sha256: SHA256(raw bytes) 的 lowercase 64-char hex（identity key）。
    """
    bytes_source: str
    sha256: str


def load_raw_bytes_identity(source_path: Path) -> RawBytesIdentity:
    """读取源文件的原始 bytes，计算 SHA256，返回身份。

    实现约束（M2 设计冻结）：
    - 必须使用 read_bytes()（保真全部字节：CRLF/BOM/trailing newline/unicode）。
    - 禁止 read_text()（会丢字节信息，FACT-031）。
    - 禁止 sha256_hex()（canonical_json wrap，不同 hash 族）。
    - sha256 = hashlib.sha256(raw_bytes).hexdigest()。

    Raises:
        FileNotFoundError: 源文件不存在。
        OSError: 读取失败。
    """
    raw_bytes = source_path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    return RawBytesIdentity(
        bytes_source=str(source_path),
        sha256=sha256,
    )
