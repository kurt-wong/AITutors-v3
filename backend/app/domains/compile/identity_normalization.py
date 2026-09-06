"""20 §7.3 identity normalization（段 F，F3）——只服务 dedup/occurrence/identity 键。

与段 E `match_normalization`（定位匹配用）**物理分离、禁共享实现**。本模块绝不用来
生成展示/compiled 文本（红线 3）：normalized text 不得当作 compiled stem。

保守 pipeline（顺序固定，BUG：order 未冻结 → 采用下面最小确定性实现，不冒充 Frozen）：
NFKC → 全半角折叠 → 空白/换行折叠 → 中英文标点归一 → LaTeX 数学环境内空白/换行折叠
（符号等价不做，BUG-V3-015）→ 行首题号/选项前缀剥离。
"""

from __future__ import annotations

import re
import unicodedata

from app.core.hashing import sha256_hex

IDENTITY_NORMALIZATION_VERSION = "identity-norm/v1"

_PUNCT = str.maketrans(
    {"，": ",", "。": ".", "？": "?", "！": "!", "：": ":", "；": ";",
     "（": "(", "）": ")", "～": "~", "、": ",", "％": "%"}
)
_WS_RE = re.compile(r"\s+")
_LEAD_NUM_RE = re.compile(r"^\d{1,3}\s*[.．、:)]*\s*")
_LEAD_OPT_RE = re.compile(r"^[A-Ha-h]\s*[.．、:)]*\s*")
_MATH_ENV_RE = re.compile(r"\$[^$]*\$|\\\[.*?\\\]", re.S)


def _fold_full_width(text: str) -> str:
    out = []
    for ch in text:
        code = ord(ch)
        out.append(chr(code - 0xFEE0) if 0xFF01 <= code <= 0xFF5E else ch)
    return "".join(out)


def _fold_math_whitespace(text: str) -> str:
    """LaTeX 数学环境内空白/换行折叠（M1 子集；符号等价延后 BUG-V3-015）。"""

    def _sub(m):
        return re.sub(r"\s+", "", m.group(0))

    return _MATH_ENV_RE.sub(_sub, text)


def normalize_identity(text: str) -> str:
    """identity 用归一化（不做 NFKC 之外的 Unicode 语义判断；只统一 identity 外观差异）。"""
    nfkc = unicodedata.normalize("NFKC", text)
    folded = _fold_full_width(nfkc)
    punct = folded.translate(_PUNCT)
    math = _fold_math_whitespace(punct)
    collapsed = _WS_RE.sub(" ", math).strip()
    return _LEAD_NUM_RE.sub("", collapsed)


def strip_option_label(text: str) -> str:
    """选项文本剥离行首 label（A. / A、…），供选项 identity 成分（label 单独入键）。"""
    n = normalize_identity(text)
    return _LEAD_OPT_RE.sub("", n)


def identity_hash(canonical_input: object) -> str:
    """identity 键 hash = canonical JSON SHA256（段 A hashing.sha256_hex）。"""
    return sha256_hex(canonical_input)
