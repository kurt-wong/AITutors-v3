"""Allowed-Answer Grammar（段 G，20 §8.4 / DISPLAY_CONTRACT §0.2，纯函数）。

strict-auto 前置 DoD：对 answer 声明允许 token 集与规范化做**确定性格式校验**。
本模块**不判"哪个选项对"**——正确性由教师版答案区（E 定位 + F 编译）提供；grammar
只验"答案能否被该 canonical type 表达为确定格式"（20 §8.3 五条件之一，必要不充分）。

返回约定：`True` = 通过该 type 的 grammar；`None` = 不适用 / 无法确定性表达（不自动，
pending_review）。grammar 失败永不判 rejected——结构/语义明确矛盾才 terminal（policy.py
Admission 层职责，P0-G-002）。

开放范围（用户裁决 2026-09-06，BUG-V3-023）：single_choice / multiple_choice /
true_false；其余 canonical type（fill_in/short_answer/essay/共享选项池等）→ None。
"""

from __future__ import annotations

import re

from app.domains.gate import STRICT_AUTO_TYPES

# DISPLAY_CONTRACT §0.2 true_false canonical 映射（禁 true/false/A/B 作 canonical 值）。
_TRUE_TOKENS = frozenset({"T", "t", "正确", "对", "是", "√", "✓"})
_FALSE_TOKENS = frozenset({"F", "f", "错误", "错", "否", "×", "✗"})

# E answer char-span 从 qn 条目起点切片（20 §5.5），raw answer text 常以题号开头
# （如 "1. A"）；grammar 先剥离该题号前缀再读答案 token（与 E `_ENTRY_RE` 同界）。
_LEAD_QN_RE = re.compile(r"^\s*[0-9]{1,3}\s*[.．、:)]*\s*")
_TRAIL_NOISE_RE = re.compile(r"[。．,，、\s]+$")
_LETTER_RE = re.compile(r"[A-Za-z]")


def _clean_answer(answer_text: str) -> str:
    """剥离题号前缀 + 头尾空白（仅作格式识别，不做 identity normalization）。"""
    if not answer_text:
        return ""
    return _LEAD_QN_RE.sub("", answer_text).strip()


def _option_letters(answer_text: str) -> tuple[str, ...]:
    """抽取出现在答案文本中的 ASCII 字母（题号前缀剥离后；选项标签均单大写）。"""
    return tuple(m.group(0).upper() for m in _LETTER_RE.finditer(answer_text))


def _verify_true_false(token: str) -> bool | None:
    """DISPLAY_CONTRACT §0.2：对/错/是/否/√/× → T/F ∈ {T,F}；A/B/其他 → None。"""
    t = _TRAIL_NOISE_RE.sub("", token).strip()
    if t in _TRUE_TOKENS or t in _FALSE_TOKENS:
        return True
    return None


def verify(
    canonical_type: str,
    answer_text: str,
    resolved_option_labels: object = (),
) -> bool | None:
    """Allowed-Answer Grammar 单 leaf 判定。

    - single_choice   → 恰一个字母 ∈ resolved labels。
    - multiple_choice → 非空字母集 ⊆ resolved labels（乱序/重复容忍，canonical 需合法）。
    - true_false      → 剥题号后映射 ∈ {T,F}（A/B → None，用户裁决）。
    - 其它 / 无法表达 → None（不开放，pending_review）。
    """
    if canonical_type not in STRICT_AUTO_TYPES:
        return None

    cleaned = _clean_answer(answer_text)

    if canonical_type == "true_false":
        return _verify_true_false(cleaned)

    labels = {str(lb).strip().upper() for lb in resolved_option_labels if lb}
    letters = _option_letters(cleaned)

    if canonical_type == "single_choice":
        if len(letters) != 1:
            return None
        return True if letters[0] in labels else None

    # multiple_choice
    if not letters:
        return None
    return True if set(letters) <= labels else None
