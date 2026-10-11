# -*- coding: utf-8 -*-
"""GEO-SUBQ 回归护栏 — is_question_start / _LABEL_RE 放宽后的误识别锁定。

仅针对本轮正则扩展增加断言，不改生产代码逻辑（除非测试暴露实际回归）。
"""
import re

import pytest

from app.domains.resolver.match_normalization import (
    is_question_start,
    normalize_text,
)
from app.domains.resolver.resolver import _LABEL_RE


# ═══════════════════════════════════════════════════════════════
# A. 必须拒绝识别为题号（科学计数法 / 数据点 / 小数点）
# ═══════════════════════════════════════════════════════════════

class TestRejectNumericFalsePositives:
    """数字后紧跟分隔符再跟数字 → 不是题号，是数值表达。"""

    @pytest.mark.parametrize("line", [
        "2·10^3 是科学计数法",
        "2，3 两个数据点",
        "7.5级地震",
    ])
    def test_not_question_start(self, line):
        assert is_question_start(normalize_text(line)) is None, line


# ═══════════════════════════════════════════════════════════════
# B. 合法 OCR 变体必须继续识别
# ═══════════════════════════════════════════════════════════════

class TestLegalOcrVariants:
    @pytest.mark.parametrize("line,qn", [
        ("15·船队途经非洲西海岸……", "15"),
        ("20，图5中序号代表的地质作用……", "20"),
    ])
    def test_ocr_separator_variants(self, line, qn):
        assert is_question_start(normalize_text(line)) == qn, line


# ═══════════════════════════════════════════════════════════════
# C. 选项紧贴形式（_LABEL_RE 放宽后）
# ═══════════════════════════════════════════════════════════════

class TestCompactOptionLabels:
    def test_glued_labels_all_found(self):
        """A.①②③B.①②④C.①②③D.②③④ — 四个标签都要命中。"""
        text = "A.①②③B.①②④C.①②③D.②③④"
        letters = [m.group(1).upper() for m in _LABEL_RE.finditer(text)]
        assert letters == ["A", "B", "C", "D"], letters

    def test_circled_prefix_label(self):
        """②B.减小 — 圈号紧贴选项标签不误挡。"""
        text = "②B.减小"
        letters = [m.group(1).upper() for m in _LABEL_RE.finditer(text)]
        assert "B" in letters, letters

    def test_cjk_glue_still_blocked(self):
        """对A项 / 则A. — 汉字紧贴大写不得误配。"""
        assert list(_LABEL_RE.finditer("对A项")) == []
        assert list(_LABEL_RE.finditer("则A. 正确")) == []
