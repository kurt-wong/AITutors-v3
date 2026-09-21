"""BUG-V3-044 修复对抗性审查。

纪律：每个断言必须是可执行的真实测试；不为通过而放宽断言；
发现缺陷则让测试失败并如实报告，不做自我合理化。

维度：
  A1 正则正确性 / VERBOSE 模式 / 全角字符
  A2 真实 pipeline 传给 verify() 的实际文本 vs 实验假设
  A3 污染文本绕过尝试
  A4 覆盖率测量方法学（char-span 语义）
  A5 multiple_choice 覆盖
  A6 true_false 不变性
  A7 下游集成（policy → admission 路径）
  A8 既有测试是否被削弱
"""

from __future__ import annotations

import re
import uuid

import pytest

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate import STRICT_AUTO_TYPES
from app.domains.gate import grammar as g
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView

SVID = uuid.UUID("00000000-0000-0000-0000-0000000000f3")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a3")
L = ("A", "B", "C", "D")


def _mk(*texts):
    return tuple(
        SourceLineView(f"P1L{i + 1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


def _payload(ctype="single_choice"):
    return {
        "semantic_units": [
            {
                "unit_id": "Q1",
                "unit_type": "standalone_unit",
                "original_question_type": ctype,
                "content": {
                    "stem": {"question_label": "1"},
                    "options": [{"label": x} for x in "ABCD"],
                    "answer": {"answer_zone": "answer_table", "question_label": "1"},
                },
            }
        ]
    }


def _pipeline(lines, payload, root_unit_id="Q1"):
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    lines_by_ref = {l.line_ref: l for l in lines}
    compiled = Compiler(spans, lines_by_ref).compile(ir)
    root = next(u for u in ir.units if u.unit_id == root_unit_id)
    return root, ir, compiled, run


# ===========================================================================
# A2 — 真实 pipeline 传给 verify() 的实际文本
# ===========================================================================

class TestA2ActualTextReachingGrammar:
    """抓取真实 pipeline 中 grammar 收到的字符串，验证实验假设是否成立。"""

    def _capture_verify_input(self, answer_region_line: str) -> tuple[str, str]:
        """跑完整 pipeline，返回 (grammar 收到的原文, decision)。"""
        captured: list[str] = []

        import app.domains.gate.policy as policy_mod
        original = policy_mod.verify

        def spy(ctype, answer_text, labels=()):
            captured.append(answer_text)
            return original(ctype, answer_text, labels)

        policy_mod.verify = spy
        try:
            lines = _mk(
                "1. which fruit",
                "A. apple", "B. banana", "C. car", "D. table",
                "答案",
                answer_region_line,
            )
            root, ir, compiled, run = _pipeline(lines, _payload())
            d = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)
        finally:
            policy_mod.verify = original

        assert captured, "grammar.verify 未被调用——pipeline 路径可能断裂"
        return captured[0], d["decision"]

    def test_a2_grammar_receives_qn_prefixed_span_not_bare_token(self):
        """E 从题号条目起点切片 → grammar 必然收到带题号前缀的文本。"""
        text, decision = self._capture_verify_input("1. A")
        assert text.startswith("1."), (
            f"实验假设「grammar 收到带题号前缀的文本」不成立，实际收到 {text!r}"
        )
        assert decision == "auto_approve"

    def test_a2_clean_answer_strips_exactly_one_qn_prefix(self):
        """_clean_answer 必须剥掉题号且不多剥。"""
        assert g._clean_answer("1. A") == "A"
        assert g._clean_answer("12. 【答案】D") == "【答案】D"
        assert g._clean_answer("1.A") == "A"
        # 不应把答案里的数字误当题号剥掉
        assert g._clean_answer("1. 2A") == "2A"

    def test_a2_multi_entry_line_char_span_stops_at_next_entry(self):
        """同行多题答案：char span 应止于下一 qn 条目，不是整行。

        断言真正的属性：span 不含下一题号，且 decision 正确。
        （切片 `raw[start:nxt_start]` 天然含分隔空白，故不断言精确字面量。）
        """
        text, decision = self._capture_verify_input("1. A 2. B 3. C")
        assert "2." not in text and "3." not in text, (
            f"char span 应止于下一 qn 前，实际 {text!r} 含后续题号"
        )
        assert text.rstrip().endswith("A"), f"span 应止于本题答案 A，实际 {text!r}"
        assert decision == "auto_approve"


# ===========================================================================
# A1 — 正则正确性
# ===========================================================================

class TestA1RegexCorrectness:

    def test_a1_verbose_mode_does_not_eat_literal_spaces_in_patterns(self):
        """re.VERBOSE 会忽略模式里的空白；确认 \\s* 与字符类未被误伤。"""
        assert g.verify("single_choice", "【答案】 D", L) is True
        assert g.verify("single_choice", "（3分） D", L) is True
        # 【答案】内部空白不是冻结 token
        assert g.verify("single_choice", "【答 案】D", L) is None

    def test_a1_fullwidth_letters_not_accepted(self):
        """全角 Ａ (U+FF21) 不在 [A-Za-z] 内。旧实现同样不接受 → 非回归。"""
        assert g.verify("single_choice", "Ａ", L) is None
        assert g.verify("single_choice", "【答案】Ａ", L) is None

    def test_a1_halfwidth_and_fullwidth_parens_both_work(self):
        assert g.verify("single_choice", "（A）", L) is True
        assert g.verify("single_choice", "(A)", L) is True
        assert g.verify("single_choice", "（A)", L) is None
        assert g.verify("single_choice", "(A）", L) is None

    def test_a1_score_prefix_requires_digit_and_ge(self):
        assert g.verify("single_choice", "（3分）D", L) is True
        assert g.verify("single_choice", "（20分）D", L) is True
        assert g.verify("single_choice", "（A分）D", L) is None
        assert g.verify("single_choice", "（3）D", L) is None

    def test_a1_period_suffix_covers_three_variants_only(self):
        assert g.verify("single_choice", "D。", L) is True   # U+3002
        assert g.verify("single_choice", "D.", L) is True    # ASCII
        assert g.verify("single_choice", "D．", L) is True   # U+FF0E
        assert g.verify("single_choice", "D，", L) is None
        assert g.verify("single_choice", "D、", L) is True   # 顿号是既有允许后缀
        assert g.verify("single_choice", "D；", L) is None
        assert g.verify("single_choice", "D：", L) is None

    def test_a1_regex_is_anchored_no_partial_match(self):
        """全串锚定：任何前后缀都必须拒。"""
        for polluted in (
            "xA", "Ax", "【答案】Ax", "x【答案】A",
            "（3分）Ax", "（33分分）D", "【答案】AB",
        ):
            assert g.verify("single_choice", polluted, L) is None, polluted


# ===========================================================================
# A3 — 绕过尝试
# ===========================================================================

class TestA3BypassAttempts:

    @pytest.mark.parametrize("text", [
        "【解答】A", "【考点】A", "【分析】A", "【点评】A", "【详解】A",
        "【答案】A【解答】B",
        "参见教材A册第三章", "见解析A页", "正确答案为A", "略A",
        "答案是A", "选A", "应选A", "故A正确", "A项正确",
    ])
    def test_a3_cjk_prose_with_single_letter_rejected(self, text):
        assert g.verify("single_choice", text, L) is None, text

    def test_a3_zero_width_space_not_stripped_fails_closed(self):
        """U+200B 不被 str.strip() 去除 → 白名单不匹配 → None（fail-closed）。"""
        assert g.verify("single_choice", "A​", L) is None

    def test_a3_leading_trailing_whitespace_tolerated(self):
        assert g.verify("single_choice", "\n【答案】D\n", L) is True
        assert g.verify("single_choice", "  A  ", L) is True

    def test_a3_letter_inside_prose_not_extracted_anymore(self):
        """旧实现会从这些抽字母；新实现必须 None。"""
        for t in ("本题选A", "正确选项是A", "由题意得A", "A为正确答案",
                  "参考答案A", "标准答案A"):
            assert g.verify("single_choice", t, L) is None, t

    def test_a3_multiple_choice_prose_rejected(self):
        for t in ("【分析】（1）概括文章内容、鉴赏文章艺术特色。",
                  "A 区适合摆放蔬菜水果；B 区适合摆放服装。",
                  "（1）B；C；D；E （2）正丁烷、异丁烷"):
            assert g.verify("multiple_choice", t, L) is None, t


# ===========================================================================
# A5 — multiple_choice
# ===========================================================================

class TestA5MultipleChoice:

    def test_a5_mc_still_accepts_common_forms(self):
        for t in ("ABD", "1. ABD", "A、C", "1. C、A", "A C B", "AAB",
                  "A, C", "1. A, C", "AB D"):
            assert g.verify("multiple_choice", t, L) is True, t

    def test_a5_mc_accepts_answer_marker_and_score_prefix(self):
        assert g.verify("multiple_choice", "【答案】AB", L) is True
        assert g.verify("multiple_choice", "（3分）AB", L) is True

    def test_a5_mc_rejects_trailing_prose_after_marker(self):
        assert g.verify("multiple_choice", "【答案】AB详见解析", L) is None
        assert g.verify("multiple_choice", "（3分）AB（A有误）", L) is None

    def test_a5_mc_letter_outside_labels_rejected(self):
        assert g.verify("multiple_choice", "AE", L) is None
        assert g.verify("multiple_choice", "ABE", L) is None

    def test_a5_mc_empty_and_no_letters(self):
        assert g.verify("multiple_choice", "", L) is None
        assert g.verify("multiple_choice", "不确定", L) is None
        assert g.verify("multiple_choice", "、，", L) is None


# ===========================================================================
# A6 — true_false 不变性
# ===========================================================================

class TestA6TrueFalseInvariance:

    @pytest.mark.parametrize("t", ["对", "错", "T", "t", "F", "正确", "错误",
                                    "是", "否", "√", "✓", "×", "✗"])
    def test_a6_canonical_tokens_still_pass(self, t):
        assert g.verify("true_false", f"1. {t}", ()) is True

    @pytest.mark.parametrize("t", ["【解答】对", "【考点】正确", "答案是对",
                                    "【答案】对", "（2分）对", "对。详见解析"])
    def test_a6_polluted_true_false_rejected(self, t):
        assert g.verify("true_false", t, ()) is None

    def test_a6_true_false_not_affected_by_sc_whitelist(self):
        assert g.verify("true_false", "对", ()) is True
        assert g.verify("single_choice", "对", L) is None


# ===========================================================================
# A7 — 下游集成
# ===========================================================================

class TestA7DownstreamIntegration:

    def _run(self, answer_line: str, ctype="single_choice"):
        lines = _mk(
            "1. which fruit",
            "A. apple", "B. banana", "C. car", "D. table",
            "答案",
            answer_line,
        )
        root, ir, compiled, run = _pipeline(lines, _payload(ctype))
        return evaluate(root=root, ir=ir, compiled=compiled, resolved_run=run)

    def test_a7_policy_decision_follows_new_grammar(self):
        assert self._run("1. A")["decision"] == "auto_approve"
        assert self._run("1. 【解答】A")["decision"] == "pending_review"
        assert self._run("1. 参见教材A册第三章")["decision"] == "pending_review"
        assert self._run("1. 【答案】D")["decision"] == "auto_approve"

    def test_a7_pending_review_reason_is_grammar_not_rejected(self):
        d = self._run("1. 【解答】A")
        assert d["decision"] == "pending_review"
        assert "answer not expressible as canonical value" in " ".join(d["reasons"])
        assert d["layers"]["structural"]["status"] != "fail"
        assert d["layers"]["semantic"]["status"] != "fail"
        assert d["layers"]["provenance"]["status"] != "fail"

    def test_a7_auto_not_granted_for_polluted_answer(self):
        d = self._run("1. 【解答】A")
        assert d["decision"] != "auto_approve"

    def test_a7_non_strict_auto_types_unaffected_end_to_end(self):
        d = self._run("1. A", ctype="short_answer")
        assert d["decision"] == "pending_review"


# ===========================================================================
# A4 — 覆盖率测量方法学：用真实 char-span 语义重扫语料
# ===========================================================================

CORPUS = "D:/Project/Papers/Ocr-markdown"


def _is_answer_header(s: str) -> bool:
    n = s.strip()
    if n.startswith("【答案】"):
        suf = n[len("【答案】"):]
        return suf == "" or bool(re.match(r"^[\d\s\-—–~～,，、.．]*$", suf))
    return n in ("答案", "参考答案") or n.startswith("答案:") or n.startswith("答案：")


# 与 E 的条目起点同界（题号 token + 分隔）
_ENTRY_START = re.compile(r"(?<!\d)(\d{1,3})\s*[.．、:)]\s*")


class TestA4CoverageMethodology:
    """A4：用 Resolver 真实 char-span 语义（切到下一 qn 前）重扫语料，
    检验此前基于「行内全部剩余文本」的测量是否高估了回归。"""

    def test_a4_char_span_semantics_scan(self):
        import glob
        from collections import Counter

        files = [f for f in glob.glob(f"{CORPUS}/**/*.md", recursive=True)
                 if "_imgs" not in f and "README" not in f]
        assert files, f"语料未找到: {CORPUS}"

        c: Counter = Counter()
        regress_examples: list[str] = []

        for md in files:
            try:
                lines = open(md, encoding="utf-8").read().splitlines()
            except Exception:
                continue
            hdr = next((i for i, l in enumerate(lines) if _is_answer_header(l)), None)
            if hdr is None:
                continue
            for raw in lines[hdr + 1:]:
                s = raw.strip()
                if (s.startswith("【详解】") or s in ("详解", "解析", "解答")
                        or s.startswith("详解:") or s.startswith("解析:")
                        or s.startswith("【解析】")):
                    break
                # 复刻 E 的 char-span：从本 qn 条目起点切到下一 qn 条目起点（或行尾）
                m = _ENTRY_START.search(raw)
                if not m:
                    continue
                start = m.start()
                nxt = _ENTRY_START.search(raw, m.end())
                end = nxt.start() if nxt else len(raw)
                span_text = raw[start:end]          # ← grammar 真正收到的文本

                c["entries"] += 1
                old_letters = tuple(
                    x.upper() for x in re.findall(r"[A-Za-z]", g._clean_answer(span_text))
                )
                old_sc = len(old_letters) == 1
                new_sc = g.verify("single_choice", span_text, "ABCDEF") is True
                old_mc = bool(old_letters) and set(old_letters) <= set("ABCDEF")
                new_mc = g.verify("multiple_choice", span_text, "ABCDEF") is True

                if old_sc and new_sc:
                    c["sc_keep"] += 1
                elif old_sc and not new_sc:
                    c["sc_regress"] += 1
                    if len(regress_examples) < 40:
                        regress_examples.append(span_text)
                if old_mc and new_mc:
                    c["mc_keep"] += 1
                elif old_mc and not new_mc:
                    c["mc_regress"] += 1

        print("\n===== A4 char-span 语义重扫 =====")
        print(f"条目总数              : {c['entries']}")
        print(f"single_choice 保持通过: {c['sc_keep']}")
        print(f"single_choice 回归拒收: {c['sc_regress']}")
        print(f"multiple_choice 保持  : {c['mc_keep']}")
        print(f"multiple_choice 回归  : {c['mc_regress']}")
        print("--- sc 回归样例 ---")
        for t in regress_examples[:20]:
            print(f"   {t!r}")

        # 审查断言：回归样例中不得出现「整串恰好是合法 token 形态」的条目
        legal_form = re.compile(
            r"^(?:【答案】\s*[A-Za-z]|[（(]\s*\d+\s*分\s*[）)]\s*[A-Za-z]"
            r"|[A-Za-z](?:、|[。．.])?|[（(][A-Za-z][）)])$"
        )
        wrongly_rejected = [
            t for t in regress_examples
            if legal_form.match(g._clean_answer(t))
        ]
        assert not wrongly_rejected, (
            f"char-span 语义下仍有合法 token 被拒: {wrongly_rejected[:10]}"
        )
        assert c["entries"] > 100, f"扫描条目过少（{c['entries']}），语料可能未正确加载"


# ===========================================================================
# A8 — 既有测试是否被削弱
# ===========================================================================

class TestA8NoTestWeakening:

    def test_a8_three_state_contract_unchanged(self):
        """verify 只返回 True 或 None，永不 False（grammar 不判 terminal）。"""
        samples = ["A", "1. A", "【解答】A", "参见教材A册第三章", "", "   ",
                   "AB", "（3分）D", "【答案】D"]
        for t in samples:
            for ctype in ("single_choice", "multiple_choice", "true_false"):
                r = g.verify(ctype, t, L)
                assert r in (True, None), f"{ctype} {t!r} 返回了 {r!r}"

    def test_a8_strict_auto_domain_unchanged(self):
        assert STRICT_AUTO_TYPES == frozenset(
            {"single_choice", "multiple_choice", "true_false"}
        )

    def test_a8_option_letters_removed_not_mere_alias(self):
        """缺陷源头必须真正移除，不能只是改名保留。"""
        assert not hasattr(g, "_option_letters"), (
            "_option_letters 仍存在——缺陷源未真正移除"
        )

    def test_a8_non_strict_auto_always_none(self):
        from app.domains.compile import CANONICAL_TYPES
        for ctype in sorted(CANONICAL_TYPES - STRICT_AUTO_TYPES):
            for t in ("A", "【解答】A", "参见教材A册第三章"):
                assert g.verify(ctype, t, L) is None, ctype
