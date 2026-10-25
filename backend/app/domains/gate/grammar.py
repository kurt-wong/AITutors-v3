"""Allowed-Answer Grammar（段 G，20 §8.4 / DISPLAY_CONTRACT §0.2，纯函数）。

strict-auto 前置 DoD：对 answer 声明允许 token 集与规范化做**确定性格式校验**。
本模块**不判"哪个选项对"**——正确性由教师版答案区（E 定位 + F 编译）提供；grammar
只验"答案能否被该 canonical type 表达为确定格式"（20 §8.3 五条件之一，必要不充分）。

返回约定：`True` = 通过该 type 的 grammar；`None` = 不适用 / 无法确定性表达（不自动，
pending_review）。grammar 失败永不判 rejected——结构/语义明确矛盾才 terminal（policy.py
Admission 层职责，P0-G-002）。

**题型不构成准入门槛（T20-IMPLEMENT / Owner R1–R2）**：本模块只做「答案表示形式」
校验，**不**因 canonical type 不在某白名单而拒绝。历史 `STRICT_AUTO_TYPES` 门已
移除——auto 与否由原文证据、归属、完整性等 Gate 条件共同决定，题型本身不得
阻止自动发布。choice 类型仍走 AnswerTokenContract（表示合法性）；fill_in 走
五形态；其余文本型答案以「非空源切片」为形式条件。

**AnswerTokenContract（用户裁决 2026-09-13，BUG-V3-044）**：剥除题号前缀后，
single_choice / multiple_choice 的答案文本必须完全落在白名单形态内（裸字母 /
字母+顿号 / 括号字母；多选仅允许字母与既定分隔符）。任何其他字符（汉字说明、
【解答】等标记、多余标点）→ None。此契约封闭了「从任意正文抽取 ASCII 字母」
导致的 Evidence Admission Boundary 缺口，详见 `80_B2B5_CLOSURE.md` §3。

**输入来源契约（2026-09-13 冻结，Gate D §6.2 不变量版）**：`verify()` 的
`answer_text` **必须**是某个 `ResolvedRun` 中 `role=answer` 的 `ResolvedSpan`
所承载的文本切片，且该 span 满足：`granularity` 为字符切片、
`resolution_status ∈ {exact, normalized}`、`text_hash` 与 SealedSource 原文一致
（20 §8.1 Provenance 层已校验）。**禁止**传入裸 source / OCR 文本。
题号前缀属上游边界产物，由 `_clean_answer()` 剥除，**不参与**答案 token
合法性判断。

**生产者不作限定**（Gate D 修正）：该 span 可由 Resolver（Native Path，见
`resolver.py::_answer_span`）或 Adapter（Manifest Path）构造。二者在 20 §5.5 下
同构，本模块不区分、也不需要区分——`ResolvedSpan` 无生产者字段，故写「必须
Resolver 产出」既不可验证又会非法排除整条 Adapter 路径。详见
`81_GATE_D_ADAPTER_BOUNDARY.md` §6。

**本模块不主张语义正确性**：grammar 只保证「答案表示形式对该 canonical type
合法」（representation validity），**不保证**「该答案在语义上是对的」（semantic
correctness）。二者是不同层的性质，不得混同——`80_B2B5_CLOSURE.md` §6.5。
"""

from __future__ import annotations

import re

# DISPLAY_CONTRACT §0.2 true_false canonical 映射（禁 true/false/A/B 作 canonical 值）。
_TRUE_TOKENS = frozenset({"T", "t", "正确", "对", "是", "√", "✓"})
_FALSE_TOKENS = frozenset({"F", "f", "错误", "错", "否", "×", "✗"})

# E answer char-span 从 qn 条目起点切片（20 §5.5），raw answer text 常以题号开头
# （如 "1. A"）；grammar 先剥离该题号前缀再读答案 token（与 E `_ENTRY_RE` 同界）。
# G1 parser compatibility：Markdown escaped-dot 前缀 `1\. C` ≡ `1. C`（B3a 同族）。
# **必须**带分隔符才视为题号前缀（`+` 非 `*`）：`1或2` / `1464` / `0` 是答案值本身，
# 不得被当成题号剥掉（T20-IMPLEMENT）。
_LEAD_QN_RE = re.compile(r"^\s*[0-9]{1,3}\s*(?:\\[.．、:]|[.．、:)])+\s*")
_TRAIL_NOISE_RE = re.compile(r"[。．,，、\s]+$")

# --------------------------------------------------------------------------- #
# AnswerTokenContract（BUG-V3-044，用户裁决 2026-09-13）
#
# 作用域：仅 strict-auto grammar（single_choice / multiple_choice / true_false）。
#        不改变 Evidence Contract，不回退 Evidence Promotion Phase 1。
# 数据流：ValidatedEvidence → QuestionType Contract → AnswerForm Validation
#          → Grammar.verify() → Admission
#
# 输入来源契约（Gate D §6.2 不变量版）：`answer_text` 必须是 ResolvedRun 中
#      role=answer 的 ResolvedSpan 文本切片（granularity=char_span、
#      resolution_status ∈ {exact, normalized}、text_hash 一致），
#      **禁止**裸 source/OCR 文本。生产者可以是 Resolver 或 Adapter——
#      二者在 20 §5.5 下同构，本模块不区分。题号前缀是上游边界产物，
#      不参与 token 判定。
#
# 原则：**白名单，非黑名单**。剥除题号前缀后，剩余文本必须只由答案 token
#      及其允许的分隔符/括号/前缀/后缀构成；出现任何其他字符（汉字说明、
#      解析类【】标记、多余标点）即判「无法确定性表达该题型答案」→ None。
#
# 允许形态（全串锚定，2026-09-13 用户裁决，含真实语料实测扩展）：
#      裸字母 A / A、      括号 （A） / (A)
#      答案标记 【答案】A    分值前缀 （3分）A
#      字母+句号 A。 / A.
#      多选：可选前缀 + 字母（仅既定分隔符隔开）
#
# 明确拒绝：`【分析】…` / `【解答】…` / `【考点】…` 等**解析类**标记及其正文，
#      以及任何「合法 token + 额外正文」的混合形态（如 `（3分）D["…"` ）。
#      `【答案】` 是冻结的答案表头 token（BUG-V3-031），直陈答案；
#      解析类标记之后是解释正文——二者有原则区别，非特判。
#
# 背景：原实现用 `_option_letters()` 从任意文本抽取 ASCII 字母，导致
#      `参见教材A册第三章` 这类恰好含单个字母的正文被判 True 并 auto_approve，
#      Admission 以原文持久化并置 verified_correct=True（doc 74 §6.3）。
#      `_option_letters()` 行为符合其职责，缺陷在于「该输入已是合法 answer
#      evidence」这一前提无 Contract 证明；本契约封闭该前提。
#
# 说明：grammar 三态约定不变——本契约只影响返回 True 还是 None，
#      永不返回 False（结构/语义明确矛盾才是 terminal rejected，policy 职责）。
# --------------------------------------------------------------------------- #

# 多选答案 token 之间允许的分隔符：空白 / 顿号 / 逗号（半、全角）。
_MC_SEPARATORS = " \t　、,，"
# 可选前缀：答案标记 `【答案】` / 分值前缀 `（3分）`（括号必须配对）。
# 真实语料实测的合法形态，2026-09-13 用户裁决扩展；两者均直陈答案，
# 与 `【分析】`/`【解答】` 等解析标记有原则区别——后者之后是解释正文，必须拒。
_OPTIONAL_ANSWER_PREFIX = (
    r"(?:【答案】\s*|（\s*\d+\s*分\s*）\s*|\(\s*\d+\s*分\s*\)\s*)?"
)

# 单选允许形态（**全串锚定**，带任何尾巴都拒）：
#   裸字母        A / A、
#   括号字母      （A） / (A)     —— 开闭括号必须配对（全角配全角 / 半角配半角）
#   答案标记      【答案】A
#   分值前缀      （3分）A / (3分)A —— 同样要求括号配对
#   分值后缀      D（2分） / D (2分) —— G3 parser compatibility（真实卷语文 Q6）
#   字母 + 句号    A。 / A. / A．
_SC_FORMS_RE = re.compile(
    r"""^(?:
        (?P<bare>[A-Za-z])(?:、)?                      # A / A、
      | （(?P<paren_fw>[A-Za-z]）)                     # （A） 全角配对
      | \((?P<paren_hw>[A-Za-z])\)                    # (A) 半角配对
      | (?P<marker>【答案】\s*[A-Za-z])                # 【答案】A
      | (?P<score_fw>（\s*\d+\s*分\s*）\s*[A-Za-z])    # （3分）A 全角配对
      | (?P<score_hw>\(\s*\d+\s*分\s*\)\s*[A-Za-z])    # (3分)A 半角配对
      | (?P<sfx_score_fw>[A-Za-z])\s*（\s*\d+\s*分\s*）  # D（2分） 全角后缀
      | (?P<sfx_score_hw>[A-Za-z])\s*\(\s*\d+\s*分\s*\)  # D(2分) 半角后缀
      | (?P<period>[A-Za-z])[。．.]                    # A。 / A. / A．
    )$""",
    re.VERBOSE,
)
# 多选形态：可选前缀 + ≥1 个 ASCII 字母，仅由允许的分隔符隔开，无任何其他字符
_MC_TOKEN_RE = re.compile(
    rf"^{_OPTIONAL_ANSWER_PREFIX}[A-Za-z](?:[{_MC_SEPARATORS}]*[A-Za-z])*$"
)


def _clean_answer(answer_text: str) -> str:
    """剥离题号前缀 + 头尾空白（仅作格式识别，不做 identity normalization）。"""
    if not answer_text:
        return ""
    return _LEAD_QN_RE.sub("", answer_text).strip()


# 确定性答案边界（会考/高考卷解析块尾部）：故选：X / 故选X / 答案：X
# 仅当全文**恰好一个**标记且为单字母时抽取；多标记/缺失/冲突 → 不抽取。
_GU_XUAN_RE = re.compile(r"故选\s*[：:]?\s*([A-Da-d])")
_DA_AN_RE = re.compile(r"答案\s*[：:]\s*([A-Da-d])")


def _extract_unique_choice_marker(cleaned: str) -> str | None:
    """从解析型 answer 文本中抽唯一明确答案字母；否则 None。"""
    if not cleaned:
        return None
    hits = [m.group(1).upper() for m in _GU_XUAN_RE.finditer(cleaned)]
    hits += [m.group(1).upper() for m in _DA_AN_RE.finditer(cleaned)]
    if len(set(hits)) == 1 and len(hits) >= 1:
        return hits[0]
    return None


def _answer_form_single_choice(cleaned: str) -> str | None:
    """AnswerTokenContract（单选）：返回选项字母；不符合白名单 → None。"""
    m = _SC_FORMS_RE.match(cleaned)
    if not m:
        return None
    for grp in (
        "bare", "paren_fw", "paren_hw", "marker",
        "score_fw", "score_hw", "sfx_score_fw", "sfx_score_hw", "period",
    ):
        val = m.group(grp)
        if val:
            # marker/score 组含前缀或后缀，取其中的 ASCII 字母
            letters = [ch for ch in val if ch.isascii() and ch.isalpha()]
            return letters[-1].upper() if letters else None
    return None


def _answer_form_multiple_choice(cleaned: str) -> tuple[str, ...] | None:
    """AnswerTokenContract（多选）：返回选项字母序列；不符合白名单 → None。"""
    if not cleaned or not _MC_TOKEN_RE.match(cleaned):
        return None
    return tuple(ch.upper() for ch in cleaned if ch.isascii() and ch.isalpha())


def _verify_true_false(token: str) -> bool | None:
    """DISPLAY_CONTRACT §0.2：对/错/是/否/√/× → T/F ∈ {T,F}；A/B/其他 → None。

    本身即白名单 token 判定，天然拒绝 `【解答】对` 等带说明前缀的正文
    （BUG-V3-044 实测确认不受影响）。
    """
    t = _TRAIL_NOISE_RE.sub("", token).strip()
    if t in _TRUE_TOKENS or t in _FALSE_TOKENS:
        return True
    return None


# T19 确定性 fill_in 形态（赋值 / LaTeX / 区间 / 多值 / 整数 / 简分数）。超出 fail-closed。
_FILL_IN_INT_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
_FILL_IN_FRAC_RE = re.compile(r"^[+-]?\d+/\d+$")
_FILL_IN_ASSIGN_RE = re.compile(r"^[A-Za-zα-ω\\][A-Za-z0-9_α-ω\\{}^]*\s*=\s*\S+$")
_FILL_IN_LATEX_RE = re.compile(r"^\$.+\$$", re.S)
_FILL_IN_MULTIVAL_RE = re.compile(r"^\S+\s*或\s*\S+$")
_FILL_IN_INTERVAL_RE = re.compile(r"^\$\s*[\(\[].+[\)\]]\s*\$$", re.S)


def _verify_fill_in_form(answer_text: str) -> bool:
    """受限填空形态检查（表示合法；来源/归属/完整性由 Gate 另验）。"""
    t = (answer_text or "").strip()
    if not t or len(t) > 80:
        return False
    if _FILL_IN_INT_RE.match(t) or _FILL_IN_FRAC_RE.match(t):
        return True
    if _FILL_IN_LATEX_RE.match(t) or _FILL_IN_INTERVAL_RE.match(t):
        return True
    if _FILL_IN_MULTIVAL_RE.match(t):
        return True
    if _FILL_IN_ASSIGN_RE.match(t):
        return True
    return False


def verify(
    canonical_type: str,
    answer_text: str,
    resolved_option_labels: object = (),
) -> bool | None:
    """Allowed-Answer Grammar 单 leaf 判定（表示形式，非学科正确性）。

    **输入来源契约（Gate D §6.2 冻结不变量）**：`answer_text` 必须是某个
    `ResolvedRun` 中 `role=answer` 的 `ResolvedSpan` 文本切片。题号前缀由
    `_clean_answer()` 剥除。

    **题型不是准入门槛（Owner R1/R2）**：不因 type 不在白名单返回 None。
    各型只验「答案能否以该型表示形式确定性表达」：

    - single_choice / multiple_choice / true_false → AnswerTokenContract。
    - fill_in → 五形态（整数/赋值/LaTeX/区间/多值）。
    - 其它 canonical 文本型（short_answer/essay/…）→ 非空源切片即可表达
      （学科正确性、来源可信、归属、完整性由 Gate 其它条件判定）。

    本函数只验**表示形式合法性**，不判语义对错，也不重新求解。
    """
    cleaned = _clean_answer(answer_text)
    if not cleaned:
        return None

    if canonical_type == "true_false":
        return _verify_true_false(cleaned)

    labels = {str(lb).strip().upper() for lb in resolved_option_labels if lb}

    if canonical_type == "single_choice":
        letter = _answer_form_single_choice(cleaned)
        if letter is None:
            # P0-answer: do NOT rescue explanation/stem text via marker heuristics.
            return None
        return True if letter in labels else None

    if canonical_type == "multiple_choice":
        letters = _answer_form_multiple_choice(cleaned)
        if not letters:
            return None
        return True if set(letters) <= labels else None

    if canonical_type == "fill_in":
        return True if _verify_fill_in_form(cleaned) else None

    # Free-text canonical types: short_answer / essay / cloze / reading / …
    # 非空即可表示；更深的来源/归属/完整性检查在 policy 层，且与题型无关。
    if canonical_type in (
        "short_answer",
        "essay",
        "cloze",
        "reading",
        "grammar_fill",
        "vocabulary_fill",
        "seven_to_five",
        "reading_expression",
    ):
        return True

    # 未知 type（不在 CANONICAL_TYPES）→ 无法确定性表达。
    return None
