"""Consumer Identity Verification — M1 Manifest Reader。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §4.2
- PREPROCESSING-V3-CONTRACT-v0.2 §5.6.1 (G-15)

职责边界：
- 仅从 manifest JSON 中提取 source_content_sha256 字段。
- 不读 source bytes、不计算 sha256、不访问 IR、不做 mismatch 判断。
- path/source_file 不参与 identity（DEC-031 原则 1）。

行为规范（冻结）：
- sha 字段不存在 → source_content_sha256 = None
- sha 字段为空字符串 → source_content_sha256 = None
- sha 字段为 null → source_content_sha256 = None
- sha 字段非 64 位小写 hex → 抛 ManifestReadError
- 文件不存在 / JSON 解析失败 → 抛 ManifestReadError
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

MANIFEST_IDENTITY_VERSION = "1.0.0"

_SHA256_LOWER_HEX_RE = re.compile(r"\A[0-9a-f]{64}\Z")


class ManifestReadError(Exception):
    """Manifest 文件读取失败或字段格式非法。"""


@dataclass(frozen=True)
class ManifestIdentity:
    """Manifest 中声明的 source content 身份。

    source_content_sha256: 64-char lowercase hex, or None if absent/empty.
    不包含 path/source_file — path 是 locator，不是 identity（DEC-031 原则 1）。
    """
    source_content_sha256: str | None


def read_manifest_identity(manifest_path: Path) -> ManifestIdentity:
    """从 manifest JSON 中提取 source_content_sha256。

    实现约束（M1 设计冻结）：
    - 只读 JSON 中的 source_content_sha256 顶层字段。
    - 不读 source bytes、不计算 sha256、不访问 IR。
    - sha 字段不存在 / 为空 / 为 null → 返回 None。
    - sha 字段非 64 位小写 hex → 抛 ManifestReadError。

    Raises:
        ManifestReadError: 文件不存在 / JSON 解析失败 / sha 格式非法。
    """
    if not manifest_path.exists():
        raise ManifestReadError(f"manifest 文件不存在: {manifest_path}")

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        raise ManifestReadError(f"JSON 解析失败: {manifest_path} — {e}") from e

    if not isinstance(raw, dict):
        raise ManifestReadError(f"manifest 不是 JSON object: {manifest_path}")

    sha = raw.get("source_content_sha256")

    # 缺失 / 空字符串 / null → None（旧文件未回填）
    if sha is None or sha == "":
        return ManifestIdentity(source_content_sha256=None)

    if not isinstance(sha, str) or not _SHA256_LOWER_HEX_RE.match(sha):
        raise ManifestReadError(
            f"source_content_sha256 格式非法（期望 64 位小写 hex）: {sha!r}"
        )

    return ManifestIdentity(source_content_sha256=sha)
