"""Consumer Identity Verification — M3 IR Identity Reader。

设计依据：
- PREPROCESSING-V3-CONSUMER-IDENTITY-VERIFICATION-DESIGN-v1.1.md §4.4
- PREPROCESSING-V3-CONTRACT-v0.2 §5.6.1 (G-15)

职责边界：
- 仅从 IR 文件中提取声明的 source_content_sha256 / source_sha256。
- 不读 source bytes、不计算 hash、不做验证、不做 identity 判定。
- IR 不是 Identity Authority — 身份唯一来源 = SHA256(raw source bytes)。

行为规范（Design v1.1 §4.4 冻结）：
- IR 不存在 → source_content_sha256 = None（Semantic Pending 正常态，不抛异常）
- IR 存在但无 sha 字段 → source_content_sha256 = None
- IR 存在但 sha 非 64 位小写 hex → 抛 IRReadError
- IR JSON 解析失败 → 抛 IRReadError

batch resolver IR 格式（实际生产数据）：
- 顶层: {ir_version, files: [{file, ir: {source_sha256,...}, disposition, qc_verdict}]}
- 条目定位规则（Phase 2.5 locator closure）：
  1. source_sha 优先：若提供 source_sha，按 ir.source_sha256 精确匹配（唯一命中）
  2. path fallback：source_sha 缺失或无匹配时，按 file 路径字符串匹配
  3. 均未命中 → None（fail-closed for semantic）
- path 仅用于定位，不参与 identity 判定
- source_content_sha256 仍是跨系统内容身份唯一权威
- 单文档 IR 格式: {source_content_sha256: ...} 或 {source_sha256: ...}

禁止（防回归）：
- hashlib / sha256_hex / canonical_json — 不计算 hash
- read_bytes — 不读取 source bytes
- hashing 模块 — 不复用 v3 hash family
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

IR_IDENTITY_VERSION = "1.2.0"
_SHA256_LOWER_HEX_RE = re.compile(r"\A[0-9a-f]{64}\Z")


class IRReadError(Exception):
    """IR 文件存在但读取失败或字段格式非法。"""


@dataclass(frozen=True)
class IRIdentity:
    source_content_sha256: str | None


def _extract_sha(value) -> str | None:
    """从 JSON 值中提取 sha 字段。缺失/空 → None；格式非法 → 抛 IRReadError。"""
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not _SHA256_LOWER_HEX_RE.match(value):
        raise IRReadError(
            f"source sha 格式非法（期望 64 位小写 hex）: {value!r}"
        )
    return value


def _read_batch_entry(
    raw: dict,
    source_file: str | None,
    source_sha: str | None = None,
) -> IRIdentity:
    """从 batch resolver IR 中提取指定文档的 source sha。

    定位规则（Phase 2.5 locator closure）：
    1. source_sha 优先：按 ir.source_sha256 精确匹配（确定性内容关联）
    2. path fallback：按 file 路径字符串匹配
    3. 均未命中 → None

    path 仅用于定位，不参与 identity 判定。
    """
    files = raw.get("files")
    if not isinstance(files, list):
        return IRIdentity(source_content_sha256=None)

    # 策略 1：按 source_sha 匹配 ir.source_sha256（确定性内容关联）
    if source_sha is not None:
        sha_matches = []
        for entry in files:
            if not isinstance(entry, dict):
                continue
            ir_data = entry.get("ir")
            if not isinstance(ir_data, dict):
                continue
            if ir_data.get("source_sha256") == source_sha:
                sha_matches.append(entry)
        if len(sha_matches) == 1:
            sha = _extract_sha(sha_matches[0]["ir"].get("source_sha256"))
            return IRIdentity(source_content_sha256=sha)
        # 0 匹配 → fall through to path；>1 匹配 → fall through（fail-closed）

    # 策略 2：按 source_file 路径匹配（fallback）
    if source_file is not None:
        for entry in files:
            if not isinstance(entry, dict):
                continue
            entry_file = entry.get("file", "")
            if entry_file != source_file:
                continue
            ir_data = entry.get("ir")
            if not isinstance(ir_data, dict):
                continue
            sha = _extract_sha(ir_data.get("source_sha256"))
            return IRIdentity(source_content_sha256=sha)

    # 策略 3：无 source_file / source_sha 参数时的 positional fallback
    if source_file is None and source_sha is None:
        for entry in files:
            if not isinstance(entry, dict):
                continue
            ir_data = entry.get("ir")
            if not isinstance(ir_data, dict):
                continue
            sha = _extract_sha(ir_data.get("source_sha256"))
            return IRIdentity(source_content_sha256=sha)

    return IRIdentity(source_content_sha256=None)


def _read_single_doc(raw: dict) -> IRIdentity:
    """从单文档 IR 中提取 source sha。兼容两种字段名。"""
    sha = _extract_sha(raw.get("source_content_sha256"))
    if sha is None:
        sha = _extract_sha(raw.get("source_sha256"))
    return IRIdentity(source_content_sha256=sha)


def read_ir_identity(
    ir_path: Path,
    source_file: str | None = None,
    source_sha: str | None = None,
) -> IRIdentity:
    """从 IR 文件中读取声明的 source_content_sha256。

    仅提取，不计算，不验证。

    Args:
        ir_path: IR JSON 文件路径（单文档 IR 或 batch resolver IR）。
        source_file: 目标文档的 source_file 路径。batch 格式时用于 path fallback。
        source_sha: 目标文档的 computed SHA256（来自 M2）。batch 格式时
            优先用于按 ir.source_sha256 匹配（确定性内容关联）。

    Returns:
        IRIdentity(source_content_sha256=...)。IR 不存在 → None。

    Raises:
        IRReadError: IR 存在但 JSON 解析失败或 sha 字段格式非法。
    """
    # Design v1.1 §4.4: IR 不存在 → None（Semantic Pending 正常态，不抛异常）
    if not ir_path.exists():
        return IRIdentity(source_content_sha256=None)

    try:
        raw = json.loads(ir_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        raise IRReadError(f"IR 解析失败: {ir_path} — {e}") from e

    if not isinstance(raw, dict):
        raise IRReadError(f"IR 顶层不是 JSON object: {ir_path}")

    # batch resolver IR 格式检测
    if "files" in raw:
        return _read_batch_entry(raw, source_file, source_sha)

    # 单文档 IR 格式
    return _read_single_doc(raw)
