# -*- coding: utf-8 -*-
"""B3a — escaped-dot Question Identity Compatibility（确定性格式兼容）。

`21\\. xxx` 与 `21. xxx` 在 Question entry recognition 层等价 → question_number=21。
源文不变；不改 Unit Type / Question Type / composite 语义。
"""
import re

import pytest

from app.domains.resolver.match_normalization import (
    is_question_start,
    normalize_text,
)
from app.domains.resolver.resolver import _ENTRY_RE


# ═══════════════════════════════════════════════════════════════
# A. escaped-dot 与普通格式等价
# ═══════════════════════════════════════════════════════════════

class TestEscapedDotEqualsPlain:
    @pytest.mark.parametrize("qn", ["1", "7", "11", "21", "24", "40", "42", "44", "121"])
    def test_plain_and_escaped_same_identity(self, qn):
        plain = f"{qn}. 题干正文"
        escaped = f"{qn}\\. 题干正文"
        assert is_question_start(normalize_text(plain)) == qn
        assert is_question_start(normalize_text(escaped)) == qn

    def test_escaped_with_fullwidth_dot(self):
        assert is_question_start(normalize_text("21\\. 题干")) == "21"

    def test_geography_real_forms(self):
        """地理卷实测行（缩略）。"""
        for line, qn in [
            ("1\\. 与 “卡西尼号” 探测的天体系统级别相同的是", "1"),
            ("21\\. 2015 年北京市常住人口增长的主要特点是", "21"),
            ("24\\. 甲类车位主要集中分布于", "24"),
            ("40\\. 辽宁省承接产业转移的优势区位条件有", "40"),
            ("42\\. 对图中景物的合理解释是", "42"),
            ("44\\. 该实验探究的环境问题是", "44"),
        ]:
            assert is_question_start(normalize_text(line)) == qn, line


# ═══════════════════════════════════════════════════════════════
# B. 不应扩大误匹配
# ═══════════════════════════════════════════════════════════════

class TestNoOverMatch:
    @pytest.mark.parametrize("line", [
        "21\\xxx 题干",       # 转义后不是点
        "21\\",               # 转义无分隔
        "x21\\. 题干",        # 非行首
        "用了1个苹果",         # 正文数字
        "21xx 题干",
    ])
    def test_invalid_forms_not_question_start(self, line):
        assert is_question_start(normalize_text(line)) is None, line

    def test_121_is_121_not_21(self):
        """121\\. 不得被截成 21。"""
        assert is_question_start(normalize_text("121\\. 题干")) == "121"

    def test_entry_re_121_not_21(self):
        hits = [m.group(1) for m in _ENTRY_RE.finditer("121\\. A")]
        assert "21" not in hits
        assert "121" in hits


# ═══════════════════════════════════════════════════════════════
# C. 已有普通格式回归
# ═══════════════════════════════════════════════════════════════

class TestExistingFormatsUnchanged:
    @pytest.mark.parametrize("line,qn", [
        ("1. 题干", "1"),
        ("2. 题干", "2"),
        ("10. 题干", "10"),
        ("30. 题干", "30"),
        ("21．题干", "21"),
        ("21、题干", "21"),
        ("21:题干", "21"),
        ("21 题干", "21"),
        ("21", "21"),
    ])
    def test_plain_formats_still_match(self, line, qn):
        assert is_question_start(normalize_text(line)) == qn

    @pytest.mark.parametrize("line", [
        "为什么选A",
        "本题共10分",
        "①②③",
    ])
    def test_non_entry_still_none(self, line):
        assert is_question_start(normalize_text(line)) is None


# ═══════════════════════════════════════════════════════════════
# _ENTRY_RE 行内条目（answer 同行多题等）
# ═══════════════════════════════════════════════════════════════

class TestEntryReEscapedDot:
    def test_inline_escaped_entry(self):
        assert [m.group(1) for m in _ENTRY_RE.finditer("27\\. A")] == ["27"]

    def test_inline_plain_entry(self):
        assert [m.group(1) for m in _ENTRY_RE.finditer("27. A")] == ["27"]

    def test_mixed_line(self):
        nums = [m.group(1) for m in _ENTRY_RE.finditer("21\\. A 22. B 23\\. C")]
        assert nums == ["21", "22", "23"]

    def test_no_false_positive_on_xxx(self):
        assert list(_ENTRY_RE.finditer("21\\xxx")) == []
