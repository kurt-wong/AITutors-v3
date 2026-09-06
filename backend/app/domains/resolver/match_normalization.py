"""§5.2 匹配归一化（段 E，E2）。只服务「marker.text 定位 source 行/行内片段」。

与 §7.3 identity normalization（Compiler dedup/occurrence/input 身份键）**物理分离、
禁共享实现**：变换集与作用对象不同。本模块不做 LaTeX 等价 / NFKC / 选项前缀剥离
（那是 §7.3 身份键用），不做 text_hash/source_span 归一化（保持 raw，10 §8 2c）。

归一化集合（20 §5.2）：全半角、空白折叠、中英文标点、OCR 转义噪音、题号前后缀。
确定性纯函数；版本化（改规则即须走 Rebuild）。
"""

from __future__ import annotations

import re

MATCH_NORMALIZATION_VERSION = "match-norm/v1"

_WS_RE = re.compile(r"\s+")
_OCR_NOISE = str.maketrans(
    {
        "​": " ",  # zero-width space
        "‌": " ",  # ZWNJ
        "‍": " ",  # ZWJ
        "﻿": " ",  # BOM / ZWNB
        " ": " ",  # NBSP
        "　": " ",  # ideographic space
    }
)


def fold_full_width(ch: str) -> str:
    """全角 ASCII/标点 → 半角（FF01-FF5E），保留其他字符。"""
    code = ord(ch)
    if 0xFF01 <= code <= 0xFF5E:
        return chr(code - 0xFEE0)
    return ch


def normalize_text(text: str) -> str:
    """一行/一个 marker 的匹配用归一化（§5.2）。空白折叠到单空格并 trim。"""
    folded = "".join(fold_full_width(c) for c in text)
    folded = folded.translate(_OCR_NOISE)
    return _WS_RE.sub(" ", folded).strip()


def strip_question_prefix(text: str) -> str:
    """题号前后缀剥离（§5.2）：「1. 」「1、」「11 ．」等行首题号 → 剩余文本。"""
    m = re.match(r"^(\d+)\s*[.．、:]?\s*(.*)$", text)
    if m:
        return m.group(2)
    return text


def is_question_start(normalized_line: str) -> str | None:
    """若行首是题号 token（§5.2 题号前后缀），返回题号串，否则 None。

    仅匹配「行首 digit 后接分隔/空白」，避免正文「用了1个」误判（不以 digit 开头）。
    """
    m = re.match(r"^(\d{1,3})\s*([.．、:]|\s|$)", normalized_line)
    return m.group(1) if m else None


def option_tokens(normalized_line: str, labels: tuple[str, ...]) -> tuple[str, ...]:
    """该行出现的选项标签（按声明顺序，§5.3 option_label）。"""
    return tuple(
        lab for lab in labels if _line_has_option_token(normalized_line, lab)
    )


def _line_has_option_token(normalized_line: str, label: str) -> bool:
    """选项形态匹配（M1 保守）：行首「A.」/「A、」/「(A)」等。禁匹配正文随机大写。"""
    if re.match(rf"^{re.escape(label)}\s*[.．、):）]", normalized_line):
        return True
    if re.match(rf"^[（(]{re.escape(label)}[)）]", normalized_line):
        return True
    return False
