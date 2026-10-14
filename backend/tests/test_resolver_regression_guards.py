# -*- coding: utf-8 -*-
"""GEO-SUBQ 回归护栏 — is_question_start / _LABEL_RE 放宽后的误识别锁定。

覆盖：
- OCR 分隔符 `·`/`，` 后紧跟数字 → 拒绝（科学计数法 / 数据点）
- 传统分隔符 `.`/`．`/`、`/`:` 既有语义 → 保留（中文题号）
- 小数点 `7.5` → 拒绝
- 化学 Q11/Q12 区域边界 → 不吞题
"""
import pytest

from app.domains.resolver.match_normalization import (
    is_question_start,
    normalize_text,
)
from app.domains.resolver.resolver import (
    _LABEL_RE,
    _find_paren_question_entry_col,
    _find_question_entry_col,
    _line_has_paren_question_entry,
)


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
# C. 传统分隔符既有语义（`．` / `.` / `、` / `:`）
# ═══════════════════════════════════════════════════════════════

class TestTraditionalSeparatorsPreserved:
    """`．`（中文句号）与 `.` 等传统分隔符必须保持既有题号识别语义。"""

    @pytest.mark.parametrize("line,qn", [
        ("12．2017年，我国科学家……", "12"),
        ("11. 原电池是化学电源的雏形……", "11"),
        ("1．下列说法正确的是", "1"),
        ("3、下列各组物质中", "3"),
        ("5:关于力的说法", "5"),
        ("42．该实验探究的环境问题是", "42"),
    ])
    def test_traditional_separators_still_work(self, line, qn):
        assert is_question_start(normalize_text(line)) == qn, line

    def test_chinese_fullstop_not_folded_to_ascii(self):
        """`．` 折叠保护：normalize_text 后仍保留 `．`，不折为 `.`。"""
        normalized = normalize_text("12．2017年")
        assert "．" in normalized, f"`．` should be preserved, got: {normalized!r}"


# ═══════════════════════════════════════════════════════════════
# D. 化学 Q11/Q12 区域边界（不得吞题）
# ═══════════════════════════════════════════════════════════════

class TestQ11Q12Boundary:
    """Q11 的 question region 必须在 Q12 开始处结束，不得因 Q12 被误判/漏判而吞掉 Q11。"""

    Q11_LINE = "11. 原电池是化学电源的雏形，其构造如图所示。下列关于原电池的说法正确的是"
    Q12_LINE = "12．2017年，我国科学家实现了二氧化碳高稳定性加氢合成甲醇，在二氧化碳的碳资源化利用方面取得突破性进展。"

    def test_q11_recognized(self):
        assert is_question_start(normalize_text(self.Q11_LINE)) == "11"

    def test_q12_recognized(self):
        assert is_question_start(normalize_text(self.Q12_LINE)) == "12"

    def test_q12_does_not_swallow_q11(self):
        """Q12 前一行是 Q11 正文（非题号开头），不得被 Q12 吞并。"""
        q11_body = "该装置将化学能转化为电能，Zn 为负极"
        assert is_question_start(normalize_text(q11_body)) is None

    def test_q11_q12_both_present(self):
        """两题都必须被识别为独立题号入口。"""
        q11 = is_question_start(normalize_text(self.Q11_LINE))
        q12 = is_question_start(normalize_text(self.Q12_LINE))
        assert q11 == "11"
        assert q12 == "12"
        assert q11 != q12


# ═══════════════════════════════════════════════════════════════
# E. 选项紧贴形式（_LABEL_RE 放宽后）
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


# ═══════════════════════════════════════════════════════════════
# F. MATH 括号题号（E2E-007B Fix A：仅入口定位，不进 is_question_start）
# ═══════════════════════════════════════════════════════════════

class TestMathParenQuestionNumberBounded:
    """括号式顶层题号只在声明窗口入口路径识别。

    共享谓词 is_question_start 必须继续拒绝 `(n)` —— PHY/CHEM 小问标记
    `（1）` 不得被当成顶层题号去截断题干（DSH_QUESTION_NUMBER_MECHANISM_AUDIT）。
    """

    @pytest.mark.parametrize("line", [
        "(1) 已知集合  $ A = \\{1,4,5\\} $",
        "（3）《北京2022年冬奥会》纪念邮票",
        "(12) 题干正文",
    ])
    def test_shared_predicate_rejects_paren(self, line):
        assert is_question_start(normalize_text(line)) is None, line

    @pytest.mark.parametrize("line,qn", [
        ("(1) 已知集合  $ A = \\{1,4,5\\} $", "1"),
        ("（3）《北京2022年冬奥会》纪念邮票", "3"),
        ("(12) 题干正文", "12"),
        ("(1)题干紧贴", "1"),
    ])
    def test_paren_entry_helper_matches_declared_qn(self, line, qn):
        assert _line_has_paren_question_entry(line, qn), line

    @pytest.mark.parametrize("line,qn", [
        ("(1) 已知集合", "2"),          # 声明 qn 不符
        ("(1, -1) 坐标向量", "1"),      # 逗号后数字 → 数值
        ("(1.5) 小数", "1"),
        ("(A) 选项标签", "1"),
        ("23. 下列说法正确的是", "23"),  # 数字形态，不应走括号 helper
    ])
    def test_paren_entry_helper_rejects(self, line, qn):
        assert not _line_has_paren_question_entry(line, qn), line

    def test_paren_entry_col(self):
        assert _find_paren_question_entry_col("(1) 题干", "1") == 0
        assert _find_paren_question_entry_col("(1) 题干", "2") is None
        assert _find_question_entry_col("(1) 题干", "1") == 0


# ═══════════════════════════════════════════════════════════════
# G. 单行多选项内容边界（_LABEL_RE 含前导括号，独立于 Fix A）
# ═══════════════════════════════════════════════════════════════

class TestSingleLineOptionContentBounds:
    """`(A) x (B) y` 切分后，上一选项正文不得吞入下一标签的左括号。"""

    def test_label_re_includes_leading_paren_in_token(self):
        text = "(A) 1 (B) 2 (C) 3"
        spans = [(m.start(), m.end(), m.group(1)) for m in _LABEL_RE.finditer(text)]
        assert [s[2] for s in spans] == ["A", "B", "C"]
        # token start must sit on '(' so content end stops before it
        assert spans[0][0] == 0
        assert spans[1][0] == 6  # '(' of (B)

    def test_option_content_excludes_next_label_paren(self):
        from app.domains.resolver.resolver import _option_content_bounds

        text = "(A)  $ \\{1,2,3\\} $ (B)  $ \\{1,2,3,4\\} $ (C)  X (D)  Y"
        bounds = {
            lab: _option_content_bounds(text, lab, boundary_labels=set("ABCD"))
            for lab in "ABCD"
        }
        assert bounds["A"] is not None
        a = text[bounds["A"][0] : bounds["A"][1]]
        assert not a.rstrip().endswith("("), a
        b = text[bounds["B"][0] : bounds["B"][1]]
        assert not b.rstrip().endswith("("), b

    def test_non_paren_forms_unchanged(self):
        text = "A. 甲 B. 乙 C. 丙"
        spans = [(m.start(), m.group(1)) for m in _LABEL_RE.finditer(text)]
        assert [s[1] for s in spans] == ["A", "B", "C"]


# ═══════════════════════════════════════════════════════════════
# H. 题干上下界断言（E2E-007B KHH2 Q21–Q28 过度捕获）
# ═══════════════════════════════════════════════════════════════

class TestStemDeclaredBoundary:
    """下界：声明入口可定位；上界：stem 不跨下一题声明起点。"""

    def _resolve_khh2_like(self):
        """Minimal two-question payload: option-less fill-ins with paren entries."""
        from app.domains.resolver.resolver import SourceLineView, SourceResolver

        lines_raw = [
            "## 二、 填空题",
            "（21）第一题题干 ___.",
            "",
            "（22）第二题题干 ___.",
            "",
            "---",
            "# 参考答案",
        ]
        lines = tuple(
            SourceLineView(
                line_ref=f"P1L{i:03d}", text=t, seq=i, page_no=1, line_no_in_page=i
            )
            for i, t in enumerate(lines_raw, start=1)
        )
        payload = {
            "semantic_units": [
                {
                    "unit_id": "Q21",
                    "unit_type": "standalone_unit",
                    "question_number": "21",
                    "content": {
                        "stem": {
                            "role": "stem",
                            "question_label": "21",
                            "question_search_lines": [2, 2],
                            "stem_lines": [2, 2],
                        },
                        "answer": {
                            "role": "answer",
                            "question_label": "21",
                            "answer_zone": "answer_lines",
                            "evidence_lines": [7, 7],
                        },
                    },
                },
                {
                    "unit_id": "Q22",
                    "unit_type": "standalone_unit",
                    "question_number": "22",
                    "content": {
                        "stem": {
                            "role": "stem",
                            "question_label": "22",
                            "question_search_lines": [4, 4],
                            "stem_lines": [4, 4],
                        },
                        "answer": {
                            "role": "answer",
                            "question_label": "22",
                            "answer_zone": "answer_lines",
                            "evidence_lines": [7, 7],
                        },
                    },
                },
            ]
        }
        resolved = SourceResolver(
            source_version_id="00000000-0000-0000-0000-000000000002",
            lines=lines,
            figures=(),
        ).resolve(payload)
        return lines_raw, resolved

    def test_lower_bound_entry_located(self):
        _lines, resolved = self._resolve_khh2_like()
        stem_ids = [s.span_id for s in resolved.resolved_spans if s.role == "stem"]
        assert "sp-Q21.stem" in stem_ids, stem_ids
        assert "sp-Q22.stem" in stem_ids, stem_ids

    def test_upper_bound_stem_does_not_cross_next_declared_start(self):
        lines_raw, resolved = self._resolve_khh2_like()
        by_id = {s.span_id: s for s in resolved.resolved_spans}
        q21 = by_id["sp-Q21.stem"]
        # Q21 must not include L4 (Q22's declared start)
        assert "P1L004" not in q21.line_refs, q21.line_refs
        # and must not swallow the pad / answer header
        assert "P1L006" not in q21.line_refs
        assert "P1L007" not in q21.line_refs
        # Q21 content is its own line only
        assert q21.line_refs[0] == "P1L002"

    def test_q22_stem_not_empty_and_not_answer(self):
        _lines, resolved = self._resolve_khh2_like()
        by_id = {s.span_id: s for s in resolved.resolved_spans}
        q22 = by_id["sp-Q22.stem"]
        assert q22.line_refs[0] == "P1L004"
        assert "P1L007" not in q22.line_refs
