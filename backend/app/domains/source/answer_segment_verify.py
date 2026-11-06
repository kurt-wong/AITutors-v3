# -*- coding: utf-8 -*-
"""分段答案证据核验（TASK-QCC-ANSWER-EVIDENCE-1 证据契约实现）。

契约（AE1_EVIDENCE_AND_CONTRACT.md §二）：
- ``answer_evidence.value`` 是**语义答案声明**（可读纯文本/打包形态），不是源文字节；
- 源文字节 = ``answer_lines`` 范围的源行切片；
- 对应关系 = 分段 + 确定性表示折叠（有限规则表，规则 ID 可回放）+ 逐段源内恢复；
- 每段留痕：原始声明段 / 原始源切片 / 命中规则 / 校验结论。

安全边界：
- 折叠只折"同一答案的不同表示"（LaTeX/Unicode 上下标/全半角/空白/条件注记位置），
  不折内容差异；改变答案含义的差异（数字、字母、词干）不会折叠消失。
- 语义相似度（70% 字窗等）**不是**证据；本模块只做折叠后全等/内容串包含。
- 图片段与语义压缩段如实判 unverifiable，不伪装文本字节匹配。
- 判定分层（每对 声明段 ↔ 源条目）：
    verified        折叠后全等（主干相等 + 声明注记/备选 ⊆ 源）
    consistent      声明主干每个内容串都在源条目中出现（压缩/子集声明，仍不可证实）
    contradiction   声明段在对齐条目不可恢复、却在**其他**条目全等恢复（串段），
                    或连内容串都不在对齐条目（声明与源矛盾）
    uncovered       源条目无声明段覆盖（含图片条目——文本值通道无法承载）
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# 表示折叠（有限显式规则表；每条规则有 ID，进证据可回放）
# ---------------------------------------------------------------------------

# R9：Unicode 上下标/电荷 → ASCII（有限映射）。
_R9_SCRIPTS = str.maketrans({
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "⁺": "+", "⁻": "-", "₊": "+", "₋": "-",
    "ⁿ": "n",
    # NFKC 把 ⁻ 折成 U+2212 MINUS SIGN；减号变体统一（normalize_decl_surface 同则）
    "−": "-", "–": "-", "—": "-", "―": "-",
})

# R2：全角 → 半角标点（只折标点面，不折内容）。
_R2_WIDTH = str.maketrans({
    "（": "(", "）": ")", "［": "[", "］": "]", "【": "[", "】": "]",
    "，": ",", "、": ",", "；": ";", "：": ":", "。": ".", "．": ".",
    "？": "?", "！": "!", "　": " ", "％": "%", "＝": "=", "＋": "+",
    "－": "-", "／": "/", "＜": "<", "＞": ">", "～": "~",
})

# R6：LaTeX 符号命令 → Unicode/ASCII（有限表；未收录命令**不**盲删，
# 保留原样使内容差异仍可检出）。
_R6_SYMBOLS = {
    r"\cdot": "·", r"\times": "×", r"\div": "÷",
    r"\rightarrow": "→", r"\to": "→", r"\leftarrow": "←",
    r"\downarrow": "↓", r"\uparrow": "↑",
    r"\leq": "≤", r"\le": "≤", r"\geq": "≥", r"\ge": "≥",
    r"\approx": "≈", r"\equiv": "≡", r"\neq": "≠",
    r"\circ": "°", r"\degree": "°", r"\prime": "'",
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\Delta": "Δ", r"\mu": "μ", r"\pi": "π", r"\sigma": "σ",
    r"\omega": "ω", r"\Omega": "Ω", r"\lambda": "λ",
    r"\pm": "±", r"\mp": "∓", r"\infty": "∞",
    r"\%": "%", r"\{": "{", r"\}": "}", r"\_": "_",
    r"\,": "", r"\;": "", r"\:": "", r"\!": "", r"\quad": "",
    r"\qquad": "", r"\displaystyle": "", r"\left": "", r"\right": "",
    r"\limits": "", r"\nolimits": "",
}

_R4_WRAP_RE = re.compile(
    r"\\(?:mathrm|text|ce|mathbf|mathcal|mathit|mathsf|textrm|textbf|"
    r"textit|texttt|operatorname|rm|bf|it)\{([^{}]*)\}"
)
_R7_FRAC_RE = re.compile(
    r"\\(?:dfrac|tfrac|frac)\{([^{}]*)\}\{([^{}]*)\}"
)
_R5_SCRIPT_RE = re.compile(r"[\^_]\{([^{}]*)\}|[\^_]([A-Za-z0-9+\-=])")
# R8：条件注记（\xlongequal{X} / \stackrel{X}{=} 等）→ 主干符号 + 注记 X。
_R8_COND_RE = re.compile(
    r"\\(?:xlongequal|xrightarrow|xleftarrow|overset|underset|stackrel)"
    r"\{([^{}]*)\}\{([^{}]*)\}"
)
_R8_COND_SINGLE_RE = re.compile(
    r"\\(?:xlongequal|xrightarrow|xleftarrow)\{([^{}]*)\}"
)
_R8_SYMBOL_MAP = {
    r"\xlongequal": "=", r"\xrightarrow": "→", r"\xleftarrow": "←",
}

# R10：编辑注记（重点字：X 等）直接剥离（编辑性旁注，非答案内容）。
_R10_ANN_STRIP_RE = re.compile(
    r"\(\s*(?:重点字|注|说明|重点|注释)\s*[：:][^()]*\)"
)

# R14：列表序号守卫（TASK-QCC-ANSWER-EVIDENCE-2 / DSH D2）。
# NFKC 把圈号 ① 折成数字 1，会让列表序号伪装成答案值证据（单 token
# 独立恢复命中 `1`）。两侧同映射到 NFKC 稳定的占位符：同形圈号仍可全等
# 恢复；圈号永不再充当数字证据。只覆盖圈号/括号编号族，不动上下标
# （R9 化学计量需要）。
_R14_LISTNUM = str.maketrans({
    **{chr(0x2460 + i): chr(0xE5E1 + i) for i in range(20)},   # ①-⑳
    **{chr(0x2474 + i): chr(0xE5C1 + i) for i in range(20)},   # ⑴-⒇
    **{chr(0x2776 + i): chr(0xE5B1 + i) for i in range(10)},   # ❶-❿
    **{chr(0x278A + i): chr(0xE5A1 + i) for i in range(10)},   # ➊-➓
    **{chr(0x24F5 + i): chr(0xE5F5 + i) for i in range(9)},    # ⓵-⓽
    "\u24EA": "\uE5E0",  # ⓪
})
_R14_LISTNUM_RE = re.compile(
    "["
    "\u2460-\u2473\u2474-\u2487\u2776-\u277F\u278A-\u2793\u24EA\u24F5-\u24FD"
    "]"
)

# R11：备选（或）形态。
_R11_PAREN_OR_RE = re.compile(r"[(（]\s*或\s*([^()（）]*)\s*[)）]")
_R11_BARE_OR = "或"

# R12：答案标签剥离（【答案】/答案：/故选：等）。
_R12_LABEL_RE = re.compile(
    r"^\s*【?\s*(?:参考)?(?:答案|解[答折])\s*】?\s*[：:]?\s*"
    r"|^\s*(?:故选|故答案为|故答案是|应选|正确答案(?:为|是)?)\s*[：:，,]?\s*"
)

# 分段分隔：全角/半角分号（括号深度 0 处才切）。
_SEG_SEP_RE = re.compile(r"[；;]")
# entry token（decimal-safe）：`12.` / `12、` / `12：` 后不跟数字。
_ENTRY_TOK_RE = re.compile(r"(\d{1,3})\s*[\.、．：:]\s*(?!\d)")
# 括号 entry：（1） / (1) 后可跟 . 、
_ENTRY_PAREN_RE = re.compile(r"[(（]\s*(\d{1,3})\s*[)）]\s*[\.、．：:]?")

_IMG_RE = re.compile(r"<img\b|<div[^>]*>\s*<img", re.I)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# R15（TASK-QCC-ANSWER-EVIDENCE-3）：图片节点原子识别——条目拆分前先切出
# 图片节点（div 包裹 img / 裸 img / 裸图片路径），URL 目录、文件名中的数字
# （`（教师版）(1)`、`_451_1126_630_1208.jpg`）不再触发答案条目号。
_IMG_ATOM_RE = re.compile(
    r"<div\b[^>]*>\s*<img\b[\s\S]*?</div>"
    r"|<img\b[^>]*>"
    r"|(?<![\w.])(?:[A-Za-z0-9_.\-]*[/\\])*[A-Za-z0-9_.\-]+"
    r"\.(?:jpe?g|png|gif|webp|bmp|svg)(?![\w.])",
    re.I,
)
# 单 token 值（选项字母/短 cell）：token 恢复判定用。
_CELL_TOKEN_RE = re.compile(r"^[A-Za-z0-9]{1,8}$")

# 【答案】标记（源块内答案内容区的权威起点）。
_ANSWER_MARKER_RE = re.compile(r"【\s*答案\s*】|^\s*答案\s*[：:]", re.M)
# 解析/详解边界：标记内容区止于此（与 resolver._EXPL_BODY_PREFIXES 同族）。
_EXPL_BOUNDARY_RE = re.compile(
    r"【\s*(?:解析|详解|分析|解答|点评|考点|知识点|答案)\s*】"
)
# 排版残渣行（分页线/页码）——不进条目内容。
_PAGE_NOISE_RE = re.compile(r"^\s*(?:-{3,}|\d+\s*/\s*\d+)\s*$")


@dataclass(frozen=True)
class Folded:
    """折叠结果：主干 + 注记集 + 备选集 + 命中规则 ID。"""
    main: str
    anns: frozenset
    alts: frozenset
    rules: tuple


@dataclass(frozen=True)
class SourceEntry:
    """源块条目：条目号（可空）/ 原始切片 / 形态（text|image）。"""
    label: str
    raw: str
    kind: str


@dataclass(frozen=True)
class SegmentCheck:
    index: int
    declared_raw: str
    source_raw: str
    source_kind: str
    status: str          # verified | consistent | contradiction | uncovered
    rule_ids: tuple
    detail: str
    # TASK-QCC-ANSWER-EVIDENCE-3：对应声明段序号（合并段=范围；未覆盖=[]）。
    # 声明段↔源条目非总一一对应——多段合并→单条目时本字段为连续范围。
    declared_idx: tuple = ()


@dataclass(frozen=True)
class SegmentReport:
    checks: tuple
    n_declared: int
    n_source: int
    n_verified: int
    contra: bool
    coverage_full: bool
    summary: str
    mode: str            # whole | per_q | none


def fold_surface(text: str) -> Folded:
    """确定性表示折叠。只折表示面，不折内容差异。

    返回 (主干, 注记集, 备选集, 规则 ID 列表)。注记=条件注记+括号旁注；
    备选=`或` 形式。比较语义：主干全等 + 声明 注记/备选 ⊆ 源。
    """
    rules: list[str] = []
    t = (text or "")
    if not t:
        return Folded("", frozenset(), frozenset(), ())

    # R14：列表序号守卫（必须先于 NFKC——① 否则被折成数字 1）。
    t2 = t.translate(_R14_LISTNUM)
    if t2 != t:
        rules.append("R14_listnum_guard")
    t = t2

    # R0：NFKC 表示等价折叠（全角拉丁/数字/兼容符号——与
    # answer_evidence_mapping._repr_norm 同层的"表示等价"口径）。
    t2 = unicodedata.normalize("NFKC", t)
    if t2 != t:
        rules.append("R0_nfkc")
    t = t2

    # R12：答案标签
    t2 = _R12_LABEL_RE.sub("", t)
    if t2 != t:
        rules.append("R12_label_strip")
    t = t2

    # R10：编辑注记剥离
    t2 = _R10_ANN_STRIP_RE.sub("", t)
    if t2 != t:
        rules.append("R10_ann_strip")
    t = t2

    # R11：备选拆分（先括号（或X），再裸 或 对称二分）。
    alts: set[str] = set()

    def _take_alt(m: re.Match) -> str:
        alts.add(m.group(1).strip())
        rules.append("R11_or_paren")
        return ""

    t2 = _R11_PAREN_OR_RE.sub(_take_alt, t)
    t = t2
    if _R11_BARE_OR in t:
        parts = [p for p in t.split(_R11_BARE_OR) if p.strip()]
        if len(parts) >= 2:
            t = parts[0]
            alts.update(p.strip() for p in parts[1:])
            rules.append("R11_or_bare")

    anns: set[str] = set()

    # R7：分数（先于包裹展开，防止 \frac 内部被拆）
    t2 = _R7_FRAC_RE.sub(lambda m: f"{m.group(1)}/{m.group(2)}", t)
    if t2 != t:
        rules.append("R7_frac")
    t = t2

    # R4：包裹命令递归展开（\text{X} 等 → X）
    prev = None
    while prev != t:
        prev = t
        t2 = _R4_WRAP_RE.sub(lambda m: m.group(1), t)
        if t2 != t:
            rules.append("R4_latex_wrap")
        t = t2

    # R5：上下标 → 内容
    t2 = _R5_SCRIPT_RE.sub(lambda m: m.group(1) or m.group(2), t)
    if t2 != t:
        rules.append("R5_script")
    t = t2

    # R8：条件注记 → 主干符号 + 注记（须在 R4 展开后，\xlongequal{X} 才是平面形态）
    def _cond(m: re.Match) -> str:
        anns.add(m.group(1).strip())
        rules.append("R8_cond_note")
        return m.group(2)

    t = _R8_COND_RE.sub(_cond, t)

    def _cond_single(m: re.Match) -> str:
        anns.add(m.group(1).strip())
        rules.append("R8_cond_note")
        return _R8_SYMBOL_MAP.get(m.group(0)[: m.group(0).index("{")], "=")

    t = _R8_COND_SINGLE_RE.sub(_cond_single, t)

    # R6：符号命令（长命令优先，避免 \le 吃掉 \left 等——按 key 长度倒序）
    for cmd in sorted(_R6_SYMBOLS, key=len, reverse=True):
        if cmd in t:
            t = t.replace(cmd, _R6_SYMBOLS[cmd])
            rules.append("R6_latex_symbol")

    # R3：残余定界符（$、转义空格、反斜杠+标点）
    t2 = t.replace("$", "")
    t2 = re.sub(r"\\[\s]", "", t2)
    t2 = re.sub(r"\\([.,;:!%])", r"\1", t2)
    if t2 != t:
        rules.append("R3_latex_delim")
    t = t2

    # R9：Unicode 上下标
    t2 = t.translate(_R9_SCRIPTS)
    if t2 != t:
        rules.append("R9_unicode_script")
    t = t2

    # R2：全角 → 半角
    t2 = t.translate(_R2_WIDTH)
    if t2 != t:
        rules.append("R2_width")
    t = t2

    # 括号旁注 → anns（内层先提；内容进注记集，主干去括号）。
    for _ in range(4):
        m = re.search(r"[(]([^()]*)[)]", t)
        if not m:
            break
        inner = m.group(1).strip()
        if inner:
            anns.add(inner)
        rules.append("R13_paren_ann")
        t = t[: m.start()] + t[m.end():]

    # R1：去空白 + 残余花括号（LaTeX 结构符，内容已展开）
    t2 = re.sub(r"\s+", "", t)
    t2 = t2.replace("{", "").replace("}", "")
    if t2 != t:
        rules.append("R1_whitespace")
    t = t2

    # 折叠备选/注记自身（同规则）
    def _fold_inner(s: str) -> str:
        f = fold_surface(s)
        return f.main

    alt_mains = frozenset(_fold_inner(a) for a in alts if a)
    ann_folded = frozenset(_fold_inner(a) for a in anns if a)
    return Folded(t, ann_folded, alt_mains, tuple(dict.fromkeys(rules)))


def split_declared_segments(value: str) -> list:
    """声明值 → 段列表。

    优先 `；`/`;` 打包（括号深度 0 处切）；无分号时按 entry token
    （`9.A 10.C` / `（1）A（2）B`）拆；否则单段。
    """
    v = (value or "").strip()
    if not v:
        return []
    # 括号深度感知的分号切分
    segs: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in v:
        if ch in "（(":
            depth += 1
        elif ch in "）)":
            depth = max(0, depth - 1)
        if ch in "；;" and depth == 0:
            seg = "".join(cur).strip()
            if seg:
                segs.append(seg)
            cur = []
            continue
        cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        segs.append(tail)
    if len(segs) >= 2:
        return segs
    # entry token 形态（≥2 个 token 才视为打包）
    toks = []
    for m in _ENTRY_PAREN_RE.finditer(v):
        toks.append((m.start(), m.end()))
    for m in _ENTRY_TOK_RE.finditer(v):
        toks.append((m.start(), m.end()))
    toks.sort()
    # 去重叠（括号 token 优先，剔除被覆盖的数字 token）
    picked: list[tuple[int, int]] = []
    for s, e in toks:
        if picked and s < picked[-1][1]:
            continue
        picked.append((s, e))
    if len(picked) >= 2:
        out: list[str] = []
        for i, (s, e) in enumerate(picked):
            end = picked[i + 1][0] if i + 1 < len(picked) else len(v)
            seg = v[e:end].strip()
            if seg:
                out.append(seg)
        if len(out) >= 2:
            return out
    return [v]


def split_source_entries(block: str) -> list:
    """源块 → 条目列表（label/raw/kind）。

    权威边界：以【答案】标记区为答案内容区（标记处起，止于解析边界/下一标记/末尾）。
    - 标记区无 entry token → 整个标记内容区为一条目（U9-10 `【答案】A` 形态）；
    - `(N).` / `（N）` / `N.` entry token 切条目（decimal-safe）；
    - 条目内容仅图片/HTML → kind=image；空 → kind=empty；其余 kind=text。
    """
    text = block or ""
    if not text.strip():
        return []

    # 标记区切分（每个【答案】标记到下一标记/末尾）
    positions = [m.start() for m in _ANSWER_MARKER_RE.finditer(text)]
    if positions:
        regions = []
        for i, p in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            regions.append(text[p:end])
    else:
        regions = [text]

    def _kind(seg: str) -> str:
        body = _HTML_TAG_RE.sub(" ", seg)
        body = re.sub(r"\s+", "", body)
        return "image" if (_IMG_RE.search(seg) and not body) else "text"

    def _clean_region(region: str) -> str:
        # 去答案标签；止于解析边界（FIX-2b 同规则：不吞解析/详解正文）
        body = _R12_LABEL_RE.sub("", region, count=1)
        m = _EXPL_BOUNDARY_RE.search(body)
        if m:
            body = body[: m.start()]
        lines = [ln for ln in body.splitlines() if not _PAGE_NOISE_RE.match(ln)]
        return "\n".join(lines).strip()

    entries: list[SourceEntry] = []
    for region in regions:
        body = _clean_region(region)
        if not body:
            continue
        # R15：图片节点先识别——条目标记只在文本片段内查找，URL/文件名数字
        # 不作答案条目号（Q17 `（教师版）(1)`/`_1208.jpg` 伪条目）。
        hits: list[tuple[int, int, str]] = []
        pos = 0
        for am in _IMG_ATOM_RE.finditer(body):
            t_seg, t_off = body[pos:am.start()], pos
            for m in _ENTRY_PAREN_RE.finditer(t_seg):
                # R15：路径目录片段 `(1)/` 不作答案条目号。
                if t_seg[m.end():m.end() + 1] in ("/", "\\"):
                    continue
                hits.append((t_off + m.start(), t_off + m.end(), str(int(m.group(1)))))
            for m in _ENTRY_TOK_RE.finditer(t_seg):
                hits.append((t_off + m.start(), t_off + m.end(), str(int(m.group(1)))))
            pos = am.end()
        t_seg, t_off = body[pos:], pos
        for m in _ENTRY_PAREN_RE.finditer(t_seg):
            if t_seg[m.end():m.end() + 1] in ("/", "\\"):
                continue
            hits.append((t_off + m.start(), t_off + m.end(), str(int(m.group(1)))))
        for m in _ENTRY_TOK_RE.finditer(t_seg):
            hits.append((t_off + m.start(), t_off + m.end(), str(int(m.group(1)))))
        hits.sort()
        picked: list[tuple[int, int, str]] = []
        for s, e, lab in hits:
            if picked and s < picked[-1][1]:
                continue
            picked.append((s, e, lab))

        def _emit(lab: str, seg: str) -> list:
            """条目产出：内容含图片节点时按 文本|图片|文本 边界切开——图片节点
            = 完整 kind=image 段（首个分段带条目号）；纯文本单条目，混合文本不
            虚假标 image。"""
            if not _IMG_ATOM_RE.search(seg):
                return [SourceEntry(lab, seg, _kind(seg))]
            out: list[SourceEntry] = []
            pos2 = 0
            first = True
            for m in _IMG_ATOM_RE.finditer(seg):
                t = seg[pos2:m.start()].strip()
                if t:
                    out.append(SourceEntry(lab if first else "", t, _kind(t)))
                    first = False
                out.append(SourceEntry(lab if first else "", m.group(0), "image"))
                first = False
                pos2 = m.end()
            t = seg[pos2:].strip()
            if t:
                out.append(SourceEntry(lab if first else "", t, _kind(t)))
            return out or [SourceEntry(lab, seg, _kind(seg))]

        if not picked:
            entries.extend(_emit("", body))
            continue
        pre = body[: picked[0][0]].strip()
        if pre:
            entries.extend(_emit("", pre))
        for i, (s, e, lab) in enumerate(picked):
            end = picked[i + 1][0] if i + 1 < len(picked) else len(body)
            seg = body[e:end].strip()
            if not seg:
                entries.append(SourceEntry(lab, "", "empty"))
                continue
            entries.extend(_emit(lab, seg))
    return entries


def _content_runs(folded_main: str) -> list:
    """主干内容串：CJK 连段 + 字母数字段（含电荷/小数/百分号），按序返回。"""
    return [
        m.group(0)
        for m in re.finditer(r"[A-Za-z0-9][A-Za-z0-9.+\-%]*|[一-鿿]+", folded_main)
        if m.group(0)
    ]


def _entry_scope(entries: list, qn: str) -> set:
    """必需条目范围（TASK-QCC-ANSWER-EVIDENCE-2 D1 口径）。

    完整性 = 声明覆盖**该题**要求的全部答案条目。区分两种同形块：
    - 共享答案行（`11.C 12.B`）：条目号=全局题号，本题只要求 qn 条目
      （一个声明段=一条完整答案条目）；
    - 一题多空（`(1). 减小 (2). 防止暴沸`）：条目号=本题局部小问，全部必需。
    与 binding_fact._classify 同口径（连续 1..N=局部小问；小条目号带
    ≤10 对高目标题号=局部；其余异号=他题条目）。无法判定 → 全部必需
    （fail-closed：宁可判不完整）。
    """
    idx_all = set(range(len(entries)))
    labels = [str(e.label or "") for e in entries]
    if not qn or not any(labels):
        return idx_all
    nums = [int(l) for l in labels if l.isdigit()]
    # 局部小问：条目号连续 1..N（Q17/Q4 形态，括号形或裸号形）→ 全部条目
    # 属本题。含 qn∈1..N 的歧义形态（`1.X 2.Y 3.Z` 究竟是 1 题 3 空还是
    # 1-3 题共享行）——安全优先：按本题多空处理（判不完整=扣留），不得按
    # 共享行放行完整（D1 同类过度授予）。
    if (
        len(nums) == len(labels)
        and nums
        and sorted(nums) == list(range(1, len(nums) + 1))
    ):
        return idx_all
    match = [i for i, l in enumerate(labels) if l == str(qn)]
    if len(match) != 1:
        return idx_all
    # 小条目号带（≤10）对高目标题号（>10）= 局部小问（Q17 形态）→ 全部必需。
    others = [n for n in nums if str(n) != str(qn)]
    if str(qn).isdigit() and others and all(
        o <= 10 and int(qn) > 10 for o in others
    ):
        return idx_all
    # 其他编号条目命名他题 → 共享答案行：本题只需 qn 条目（+ 无号条目保守计入）。
    return set(match) | {i for i, l in enumerate(labels) if not l}


def _pair_status(d_fold: Folded, e_fold: Folded, e_raw: str) -> tuple:
    """单对判定：(status, detail)。verified ⊃ consistent ⊃ contradiction。"""
    # 备选/注记：声明 ⊆ 源
    if not d_fold.alts <= e_fold.alts:
        return "contradiction", "declared alternative not in source"
    if not d_fold.anns <= e_fold.anns:
        return "contradiction", "declared annotation not in source"
    if d_fold.main == e_fold.main:
        return "verified", "folded-equal"
    # 单 token 值（选项字母/短填空 cell）：独立 token 唯一恢复 = 字节证据
    # （与 binding_fact._value_supported_by_lines 单字母规则同口径；
    # inline_in_explanation 形态：声明值内嵌于解析行结论句）。
    if _CELL_TOKEN_RE.match(d_fold.main):
        pat = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(d_fold.main)}(?![A-Za-z0-9])"
        )
        hay = e_fold.main + "|" + "|".join(sorted(e_fold.alts))
        if pat.search(hay):
            return "verified", "standalone token recovery"
    # 压缩/子集一致：声明主干内容串全部出现在源条目折叠文本中
    hay = e_fold.main + "|" + "|".join(sorted(e_fold.anns)) + "|" + "|".join(sorted(e_fold.alts))
    runs = _content_runs(d_fold.main)
    if runs and all(r in hay for r in runs):
        return "consistent", "declared runs present (compressed/subset form)"
    return "contradiction", "declared content not recoverable in aligned entry"


def verify_declared_vs_source(value: str, block: str, qn: str = "") -> SegmentReport:
    """分段核验：声明值 vs 源块。详见模块文档。

    qn（可选）：本题题号——界定“必需条目范围”（共享答案行 vs 一题多空，
    见 _entry_scope）。缺省=块内全部条目必需（fail-closed）。
    """
    dsegs = split_declared_segments(value)
    entries = split_source_entries(block)
    if not dsegs:
        return SegmentReport((), 0, len(entries), 0, False, False, "none", "none")

    scope = _entry_scope(entries, qn)
    mode = "whole" if len(dsegs) > 1 else "per_q"
    checks: list[SegmentCheck] = []
    n_verified = 0
    contra = False
    entry_folds = [fold_surface(e.raw) for e in entries]

    if mode == "whole":
        # 顺序对齐 + 多声明段合并对应单条目（`；` 既作打包分隔也作条目内内容
        # 分隔，如 Q19(6) 三步操作；合并后逐条目全等恢复才认）。
        MAX_MERGE = 4
        i = 0  # 声明段游标
        for j, e in enumerate(entries):
            if e.kind == "image":
                checks.append(SegmentCheck(
                    j, "", e.raw, "image", "uncovered", (),
                    "image answer not expressible in text channel",
                ))
                continue
            if e.kind == "empty" or not e.raw.strip():
                checks.append(SegmentCheck(
                    j, "", e.raw, "empty", "uncovered", (),
                    "empty source entry",
                ))
                continue
            if i >= len(dsegs):
                checks.append(SegmentCheck(
                    j, "", e.raw, e.kind, "uncovered", (),
                    "source entry without declared segment",
                ))
                continue
            best_k = 0
            best_status = ""
            best_detail = ""
            best_rules: tuple = ()
            consistent_k = 0
            consistent_detail = ""
            consistent_rules: tuple = ()
            for k in range(1, min(MAX_MERGE, len(dsegs) - i) + 1):
                merged = "；".join(dsegs[i:i + k])
                d_fold = fold_surface(merged)
                status, detail = _pair_status(d_fold, entry_folds[j], e.raw)
                if status == "verified":
                    best_k, best_status = k, status
                    best_detail = detail if k == 1 else f"merged {k} declared segments"
                    best_rules = d_fold.rules
                    break
                if status == "consistent" and consistent_k == 0:
                    consistent_k = k
                    consistent_detail = detail
                    consistent_rules = d_fold.rules
            if best_k == 0 and consistent_k:
                best_k = consistent_k
                best_status = "consistent"
                best_detail = consistent_detail
                best_rules = consistent_rules
            if best_k == 0:
                merged = dsegs[i]
                d_fold = fold_surface(merged)
                best_k, best_status = 1, "contradiction"
                best_detail = "declared content not recoverable in aligned entry"
                best_rules = d_fold.rules
                # 串段检测：合并段在他条目全等恢复 → cross-binding
                for jj, ef in enumerate(entry_folds):
                    if jj != j and entries[jj].kind == "text":
                        st2, _ = _pair_status(d_fold, ef, entries[jj].raw)
                        if st2 == "verified":
                            best_detail = (
                                f"declared segment verified at entry #{jj} (cross-binding)"
                            )
                            break
                contra = True
            if best_status == "verified":
                n_verified += 1
            merged_raw = "；".join(dsegs[i:i + best_k])
            checks.append(SegmentCheck(
                j, merged_raw, e.raw, e.kind, best_status, best_rules, best_detail,
                # AE3：合并段对应声明序号范围（N 段→1 条目）。
                tuple(range(i, i + best_k)),
            ))
            i += best_k
        # 声明段溢出（源条目已耗尽仍有声明段）→ 矛盾（entry=-1：无对应源条目）
        while i < len(dsegs):
            checks.append(SegmentCheck(
                -1, dsegs[i], "", "", "contradiction", (),
                "declared segment beyond source entries",
                (i,),
            ))
            contra = True
            i += 1
    else:
        # per_q：单段声明在源块中唯一恢复（只在必需条目范围内判定归属）
        d_raw = dsegs[0]
        d_fold = fold_surface(d_raw)
        hit = -1
        for j in sorted(scope):
            ef = entry_folds[j]
            if entries[j].kind != "text":
                continue
            st, _ = _pair_status(d_fold, ef, entries[j].raw)
            if st == "verified":
                if hit >= 0:
                    hit = -2  # 范围内多命中 → ambiguous
                    break
                hit = j
        if hit >= 0:
            n_verified = 1
            checks.append(SegmentCheck(
                hit, d_raw, entries[hit].raw, entries[hit].kind,
                "verified", d_fold.rules,
                f"unique recovery at entry #{hit}",
                (0,),
            ))
            # TASK-QCC-ANSWER-EVIDENCE-2 D1：范围内其余必需条目如实记
            # uncovered（缺证≠矛盾，不设 contra；覆盖不全 → 不得 full）。
            for j in sorted(scope):
                if j != hit:
                    e = entries[j]
                    checks.append(SegmentCheck(
                        j, "", e.raw, e.kind, "uncovered", (),
                        "source entry without declared segment",
                    ))
        elif hit == -2:
            checks.append(SegmentCheck(
                -1, d_raw, "", "", "contradiction", d_fold.rules,
                "declared segment matches more than one source entry",
                (0,),
            ))
            contra = True
        else:
            # 无全等恢复：consistent 或 contradiction
            best = ("contradiction", "not recoverable in any entry")
            best_j = -1
            for j in sorted(scope):
                ef = entry_folds[j]
                if entries[j].kind != "text":
                    continue
                st, detail = _pair_status(d_fold, ef, entries[j].raw)
                if st == "consistent":
                    best = ("consistent", f"compressed/subset at entry #{j}")
                    best_j = j
                    break
            if best[0] == "contradiction":
                # 串段留痕：声明段在他条目（范围外）全等恢复
                for jj, ef in enumerate(entry_folds):
                    if jj not in scope and entries[jj].kind == "text":
                        st2, _ = _pair_status(d_fold, ef, entries[jj].raw)
                        if st2 == "verified":
                            best = (
                                "contradiction",
                                f"declared segment verified at entry #{jj}"
                                " (outside required scope / cross-binding)",
                            )
                            break
            status, detail = best
            if status == "contradiction":
                contra = True
            checks.append(SegmentCheck(
                best_j, d_raw, entries[0].raw if entries else "",
                entries[0].kind if entries else "", status, d_fold.rules, detail,
                (0,),
            ))

    n_declared = len(dsegs)
    n_source = len(entries)
    if mode == "whole":
        # full：每个源条目都被 verified 覆盖（无 uncovered/consistent/矛盾、无声明溢出）
        coverage_full = (
            bool(checks)
            and all(c.status == "verified" for c in checks)
        )
    else:
        # TASK-QCC-ANSWER-EVIDENCE-2 D1：per_q 单声明段至多覆盖一个条目。
        # full 仅当必需条目范围内全部条目被证（唯一条目=共享答案行本题条目，
        # 或整块即一条答案）；范围内还有其他必需条目（多空形态）→ 覆盖不全，
        # 不得 full。缺证是 partial/unknown，不判 contradiction（要求4）。
        coverage_full = n_verified == 1 and scope == {hit}
    if coverage_full:
        summary = f"ok {n_verified}/{n_source}"
    elif contra:
        summary = "contra"
    elif n_verified:
        summary = f"partial {n_verified}/{n_source}"
    else:
        summary = f"none 0/{n_source}"
    return SegmentReport(
        tuple(checks), n_declared, n_source, n_verified,
        contra, coverage_full, summary, mode,
    )


def segments_contradict(value: str, block: str, qn: str = "") -> bool:
    """True = 声明与源块存在真实矛盾（串段/内容不可恢复且非压缩一致）。

    供 compiler 完整性守卫使用：仅真实矛盾撤销 full，表示差异/压缩一致不撤销。
    """
    rep = verify_declared_vs_source(value, block, qn=qn)
    if rep.mode == "none":
        return False
    return rep.contra or (
        rep.n_verified == 0
        and any(c.status == "contradiction" for c in rep.checks)
    )


def derive_answer_completeness(report: SegmentReport) -> str:
    """同一证据轴派生完整性（v3_derived）：full | partial | unknown。"""
    if report.mode == "none":
        return ""
    if report.contra:
        return "unknown"
    if report.coverage_full:
        return "full"
    if report.n_verified > 0 or any(c.status == "consistent" for c in report.checks):
        return "partial"
    return "unknown"


# 折叠/分段规则版本（TASK-QCC-ANSWER-EVIDENCE-2/3：验证证据持久化须可回放）。
# R0-R13 = AE1 冻结规则面；R14 = AE2 列表序号守卫；R15 = AE3 图片节点原子化
# （split 阶段：图片节点先识别，URL/文件名数字不作答案条目号）。
# 规则增删须递增本串。
RULES_VERSION = "seg-verify-r0-r15"


def report_to_dict(report: SegmentReport, line_refs=None) -> dict:
    """SegmentReport → 紧凑结构化证据（供 Question 级持久化）。

    区分四态（verdict）：verified_full 已验证 / partial 部分验证 /
    unverified 不可验证 / contradiction 真实矛盾。逐段保留声明段（declared +
    declared_idx 映射）与源条目（source_head，来自权威源文切片）与未验证原因
    （detail），使 withheld 答案在最终 Question 数据中可独立复核。
    不含调试流水（有界：declared≤200 / source_head≤120 字符）。
    """
    if report.mode == "none":
        return {
            "rules_version": RULES_VERSION,
            "mode": "none",
            "verdict": "unverified",
            "completeness": "",
        }
    if report.contra:
        verdict = "contradiction"
    elif report.coverage_full:
        verdict = "verified_full"
    elif report.n_verified > 0 or any(
        c.status == "consistent" for c in report.checks
    ):
        verdict = "partial"
    else:
        verdict = "unverified"
    d = {
        "rules_version": RULES_VERSION,
        "mode": report.mode,
        "verdict": verdict,
        "completeness": derive_answer_completeness(report),
        "completeness_source": "v3_derived",
        "n_declared": report.n_declared,
        "n_source": report.n_source,
        "n_verified": report.n_verified,
        "contra": report.contra,
        "summary": report.summary,
        "segments": [
            {
                "i": i,
                "entry": c.index,
                "declared_idx": list(c.declared_idx),
                "declared": (c.declared_raw or "")[:200],
                "source_head": (c.source_raw or "")[:120],
                "status": c.status,
                "kind": c.source_kind,
                "rules": list(c.rule_ids),
                "detail": c.detail,
            }
            for i, c in enumerate(report.checks)
        ],
    }
    if line_refs:
        d["line_refs"] = list(line_refs)
    return d


# ---------------------------------------------------------------------------
# 04-C BP-A：多段合并答案的恢复性核验（分段全证的连续条目合并形态）
# ---------------------------------------------------------------------------

def value_recoverable_in_block(
    value: str,
    block: str,
    allowed_labels: set | None = None,
) -> bool:
    """答案/声明值 vs 源块**连续条目合并**的折叠全等恢复。

    背景（04-C BP-A）：复合题子问答案为多段合并（空格打包，如 Q8 子问 2 =
    段(2)+(3)），源条目之间有 `(N)` 标记，整串连续恢复（
    ``_value_supported_by_lines``）无法命中。

    本函数要求 value 折叠后与源块中**某段连续条目合并**折叠后
    ``_pair_status == verified``（主干全等 + 注记/备选 ⊆ 源）。
    - ``consistent``（压缩/子集一致）**不算**恢复成功（不足以证归属）；
    - ``allowed_labels``（可选）：命中条目号必须全部落在该集合内
      （调用方以答案 span 自身行窗的条目号收窄，防跨子问错位）；
    - 全等恢复语义 = 整个 value 被该连续条目段完整证实（分段全证）。
    """
    if not (value or "").strip() or not (block or "").strip():
        return False
    entries = split_source_entries(block)
    if not entries:
        return False
    d_fold = fold_surface(value)
    n = len(entries)
    allowed = {str(x) for x in allowed_labels} if allowed_labels is not None else None
    for i in range(n):
        for j in range(i, n):
            run = entries[i : j + 1]
            if allowed is not None:
                labels = {str(e.label) for e in run}
                if not labels <= allowed:
                    continue
            merged = "\n".join(e.raw for e in run if e.kind != "empty")
            if not merged.strip():
                continue
            e_fold = fold_surface(merged)
            status, _ = _pair_status(d_fold, e_fold, merged)
            if status == "verified":
                return True
    return False
