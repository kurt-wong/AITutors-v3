"""Source Resolver 核心（段 E，E3-E5，20 §5）。

resolve() 为纯函数：把 annotation payload 里显式声明的 reference 解析为 ResolvedSpan /
ResolvedRelation。七种 role 各用独立 policy（失败语义不同，不做万能 matcher）。

安全边界（代码级不变量）：
    resolved ⇔ status ∈ {exact, normalized, contextual}
    fuzzy / ambiguous / missing / incomplete ⇒ 只产 UnresolvedReference（无 ResolvedSpan）

「E 可以失败，但不能猜」。定位只依据显式 marker / 标签 / 题号 token / 显式边界，
不做文本相似度 / nearest / first-match 自动接受。
"""

from __future__ import annotations

import hashlib
import re
import uuid

from app.domains.resolver.match_normalization import (
    is_answer_header,
    is_explanation_header,
    is_question_start,
    normalize_text,
    option_tokens,
)
from app.domains.resolver.reference import (
    extract_relations,
    extract_targets,
)
from app.domains.resolver.span import (
    ResolvedRelation,
    ResolvedRun,
    ResolvedSpan,
    SourceFigureView,
    SourceLineView,
    SourceRegion,
    UnresolvedReference,
)


def _raw_sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# 行内条目形态：题号 token + 分隔符（bounded，防 qn=1 误配 "10."）。offset 基于 raw text。
# 兼容 Markdown escaped-dot（`27\\. A` ≡ `27. A`），与 is_question_start v1.2 同界。
# GEO-SUBQ：OCR 分隔符变体 `·`/`，`（实测 `15·`/`20，`）同等对待。
_ENTRY_RE = re.compile(r"(?<![\d@-])(\d{1,3})\s*(?:\\[.．、:·，)）]|[.．、:·，)）])")

# 行中题号入口（真实卷拼接形态）：
#   …完成 16~17 题。16. 北京…     —— 句号后紧接题号
#   …完成26－2926.优化…           —— 区间尾数字后紧接题号（OCR 无分隔拼接）
# 仅在查找「已声明的特定题号」时使用，不开放任意行中数字为题号。
_MID_SENTENCE_QN_RE_T = r"。{qn}\s*(?:\\[.．、:·，]|[.．、:·，])"
_MID_RANGE_QN_RE_T = (
    r"(?<![\d]){qn}\s*[－~—–-]\s*\d{{1,3}}\s*{qn}\s*(?:\\[.．、:·，]|[.．、:·，])"
)


def _extract_printed_numeric_prefix(printed: str) -> str | None:
    """Extract leading numeric prefix from a printed_number label.

    "14①" -> "14", "7①" -> "7", "15" -> "15", "1-10" -> None,
    "②" -> None, "abc" -> None.

    Marker-only labels (no digits) must NOT yield a search key.
    """
    m = re.match(r"^(\d+)", printed)
    return m.group(1) if m else None


# Scored answer pattern: "17. (BC) 3分; (B) 2分; (C) 2分"
# Extracts the primary answer bracket only (question number + bracket + letters).
# Scoring breakdowns like "(A)2分；(C)2分" do NOT match (no question number prefix).
_SCORED_ANSWER_RE = re.compile(
    r"^\s*(\d{1,3})\s*[.．、]\s*[\(（]([A-Da-d]+)[\)）]"
)


def _decode_scored_answer(raw: str, qn: str) -> tuple[int, int, str] | None:
    """Extract canonical answer from scored answer text.

    Input:  "17. (BC) 3分; (B) 2分; (C) 2分"
    Output: (start, end, "BC")

    P0-R4: the matched question number MUST equal the target qn.
    Previously the regex ignored qn, so `12. (A)` was extracted as Q1's
    answer (DSH bypass). Conservative: requires question number + bracket +
    continuous letters, and the number must be the target question.
    """
    m = _SCORED_ANSWER_RE.match(raw)
    if not m:
        return None
    if m.group(1) != qn:
        return None
    letters = m.group(2).upper()
    return (m.start(2), m.end(2), letters)


# Circled-number markers used in composite sub-question labels.
_MARKER_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨]")


def _has_marker(printed: str) -> bool:
    """True if printed_number label contains a circled-number marker."""
    return bool(_MARKER_RE.search(printed))


def _find_sibling_marker_seq(idx, start_seq: int, upper: int | None,
                             exclude_marker: str) -> int | None:
    """Find the seq of the first sibling marker line after start_seq.

    Sibling marker = a line whose text contains a circled-number marker
    (①②③...) that is different from exclude_marker. Returns the seq of
    that line, or None if no sibling found within upper bound.
    """
    for l in idx.lines:
        if l.seq <= start_seq:
            continue
        if upper is not None and l.seq >= upper:
            break
        m = _MARKER_RE.search(l.text)
        if m and m.group() != exclude_marker:
            return l.seq
    return None


def _line_has_question_entry(text: str, qn: str) -> bool:
    """该行是否存在题号 qn 的合法入口（行首 / 句末拼接 / 区间拼接）。

    确定性：只认已声明的 qn，不猜「最近题号」。行首仍走 is_question_start
    （含 escaped-dot v1.2）；行中仅接受上述两种真实卷拼接形态。
    """
    if is_question_start(normalize_text(text)) == qn:
        return True
    qn_esc = re.escape(qn)
    if re.search(_MID_SENTENCE_QN_RE_T.format(qn=qn_esc), text):
        return True
    if re.search(_MID_RANGE_QN_RE_T.format(qn=qn_esc), text):
        return True
    return False


# Fix A (E2E-007B)：括号式顶层题号仅用于「入口定位」。
# 不得进入 is_question_start / _region_end —— PHY/CHEM 小问标记 `（1）`
# 会把题干提前截断（DSH_QUESTION_NUMBER_MECHANISM_AUDIT）。
# 调用方必须已经限定：具体 qn + 声明窗口 question_search_lines。
_PAREN_QN_LINE_RE = re.compile(r"^\((\d{1,3})\)(?!\d)")


def _line_has_paren_question_entry(text: str, qn: str) -> bool:
    """括号式入口 `(qn)` / `（qn）`（normalize 已将全角折为半角）。

    仅匹配与声明 qn 完全一致的行首括号题号；`(1, -1)` / `(1.` 不匹配。
    """
    m = _PAREN_QN_LINE_RE.match(normalize_text(text))
    return bool(m) and m.group(1) == qn


def _find_paren_question_entry_col(text: str, qn: str) -> int | None:
    """括号式入口的字符列位。行首入口返回 0（与数字形态 col 语义一致）。"""
    if _line_has_paren_question_entry(text, qn):
        return 0
    return None


def _find_question_entry_col(text: str, qn: str) -> int | None:
    """Find column position of question entry for qn in text. None if not found.

    P3-TD: return the offset of the actual question number, not the regex
    match start (which includes leading anchor/range prefix like 。 or 26－29).
    """
    if is_question_start(normalize_text(text)) == qn:
        return 0
    qn_esc = re.escape(qn)
    m = re.search(_MID_SENTENCE_QN_RE_T.format(qn=qn_esc), text)
    if m:
        return m.start() + m.group(0).rfind(qn)
    m = re.search(_MID_RANGE_QN_RE_T.format(qn=qn_esc), text)
    if m:
        return m.start() + m.group(0).rfind(qn)
    # Fix A: paren entry column for lines already chosen as the unit entry.
    return _find_paren_question_entry_col(text, qn)


def _entry_offsets(text: str, qn: str) -> list[int]:
    """raw 行内 qn 条目起点列表（行内多条目如同行多题答案时 >1）。"""
    return [m.start() for m in _ENTRY_RE.finditer(text) if m.group(1) == qn]


# ---------------------------------------------------------------------------
# P0 unified ownership (CONTRACT-FINAL v2): only match / foreign / unknown.
# local_proven is an EMPTY set — no L1/L2/L3, no text-shape heuristics.
# ---------------------------------------------------------------------------

OWNERSHIP_MATCH = "match"
OWNERSHIP_FOREIGN = "foreign"
OWNERSHIP_UNKNOWN = "unknown"
# legacy aliases used by older call sites / tests
LEGACY_BARE = "bare"
LEGACY_FOREIGN = "foreign_question"
LEGACY_LOCAL = "local_index"


def _entry_nums_of(texts: list[str]) -> set[int]:
    nums: set[int] = set()
    for raw in texts:
        for m in _ENTRY_RE.finditer(raw):
            try:
                n = int(m.group(1))
            except ValueError:
                continue
            if n < 1:
                continue
            nums.add(n)
    return nums


def classify_answer_ownership(texts: list[str], qn: str) -> str:
    """Return OWNERSHIP_MATCH | OWNERSHIP_FOREIGN | OWNERSHIP_UNKNOWN.

    - match: some entry token equals the target question number.
    - foreign: entry tokens name other global question numbers
      (not the ambiguous local-label band).
    - unknown: bare (no entry), or ambiguous small-entry vs high-target
      (cannot prove local, cannot prove foreign). local_proven is empty.

    NEVER infers ownership from answer-token shape or text morphology.
    """
    entry_nums = _entry_nums_of(texts)
    try:
        target = int(qn)
    except (TypeError, ValueError):
        for raw in texts:
            for m in _ENTRY_RE.finditer(raw):
                if m.group(1) == str(qn):
                    return OWNERSHIP_MATCH
        return OWNERSHIP_UNKNOWN if not entry_nums else OWNERSHIP_FOREIGN

    if not entry_nums:
        return OWNERSHIP_UNKNOWN
    if target in entry_nums:
        return OWNERSHIP_MATCH
    # Ambiguous local-label band: small entries vs high target.
    # Not local_proven (no structure evidence) — unknown, never auto-publish.
    if all(e <= 10 for e in entry_nums) and target > 10:
        return OWNERSHIP_UNKNOWN
    return OWNERSHIP_FOREIGN


def bind_answer_text(texts: list[str], qn: str) -> tuple[str, str]:
    """Sole ownership decision used by every answer emit path.

    Returns (ownership, binding_evidence).
    """
    own = classify_answer_ownership(texts, qn)
    nums = sorted(_entry_nums_of(texts))
    ev = f"entries={nums};qn={qn};rule=p0-unified"
    return own, ev


def _entry_ownership(
    texts: list[str],
    qn: str,
    *,
    allow_local_index: bool = False,
) -> str:
    """Legacy-compatible wrapper over classify_answer_ownership.

    Returns historical tokens (match / bare / foreign_question / local_index)
    so older unit tests keep working; `local_index` is returned only for the
    ambiguous band and does NOT mean proven local ownership. Production bind
    paths must use bind_answer_text() / classify_answer_ownership().
    """
    own = classify_answer_ownership(texts, qn)
    if own == OWNERSHIP_MATCH:
        return "match"
    if own == OWNERSHIP_UNKNOWN:
        if not _entry_nums_of(texts):
            return "bare"
        return "local_index" if allow_local_index else "foreign_question"
    return "foreign_question"

def _is_local_body_content(content: str) -> bool:
    """True when content is a multi-part local answer body (not a simple cell).

    Evidence for local_index: `（3分）Mg | TiCl4 | 1` style — score + parts,
    pipe separators, or multiple （n） sub-sections. A bare letter / TF token /
    short fill-in (`A`, `正确`, `砖红色沉淀`) is NOT local-body evidence.
    """
    if not content or not content.strip():
        return False
    t = content.strip()
    if "|" in t or "｜" in t:
        return True
    if re.match(r"^[（(]\s*\d+\s*分\s*[)）]", t) and len(t) > 12:
        return True
    if len(re.findall(r"[（(]\s*\d+\s*[)）]", t)) >= 2:
        return True
    # substantial multi-clause body
    if len(t) >= 24 and ("；" in t or "。" in t or ";" in t):
        return True
    return False


def _is_local_prose_body(content: str) -> bool:
    """True for a prose/worded local body, never for a short simple cell.

    A batch of simple cells (`1. A`, `2. B`) must not become a local 1..k
    sequence; a per-unit local block with worded bodies (`1. answer-one`) is
    still evidence.
    """
    t = content.strip()
    if not t:
        return False
    if _is_local_body_content(t):
        return True
    if len(t) < 8:
        return False
    return len(re.findall(r"[A-Za-z\u4e00-\u9fff]", t)) >= 4


_ANSWER_INDICATOR_RE = re.compile(
    r"^\s*(?:故选|答案|故答案为|故答案是|应选|选|正确答案(?:为|是)?)\s*[：:，,]?\s*"
)


def _extract_qn_answer_from_value(value: str, qn: str) -> str | None:
    """Extract the per-question answer substring from a multi-q answer block.

    Manifest answer_evidence.value for composites is the FULL answer block
    (e.g. "（1）A （2）B （3）C …"), not the single answer for one question.
    Conflict comparison must use the current unit's answer substring, never
    the whole block. Handles （N）X / (N)X / N. X / N、X forms.
    """
    if not value or not qn:
        return None
    qn_s = str(qn).strip()
    qn_esc = re.escape(qn_s)
    # （N）X / (N)X / [N]X
    m = re.search(
        rf"[（(\[]\s*{qn_esc}\s*[）)\]]\s*([A-Za-z0-9][A-Za-z0-9/]*)",
        value,
    )
    if m:
        return m.group(1).strip()
    # N. X / N、X / N．X / N: X
    m = re.search(
        rf"(?<!\d){qn_esc}\s*[.．、:：]\s*([A-Za-z0-9][A-Za-z0-9/]*)",
        value,
    )
    if m:
        return m.group(1).strip()
    return None


def _clean_answer_for_conflict(text: str) -> str:
    """Normalize answer-ish text for conflict comparison (strip qn prefix + noise)."""
    if not text:
        return ""
    t = text.strip()
    t = _ANSWER_INDICATOR_RE.sub("", t)
    t = re.sub(r"^\s*[0-9]{1,3}\s*(?:\\[.．、:]|[.．、:)])*\s*", "", t)
    t = t.strip().strip("（）()【】[]").strip()
    t = t.strip().rstrip(".．。：:，,、 \t")
    return t.upper() if len(t) <= 4 else t


def _normalize_answer_block(text: str) -> str:
    """Normalize a full answer block for conflict comparison.

    Strips answer labels (答案:/故选：/etc.), all whitespace, and trailing
    punctuation — but PRESERVES all content and order. Used for comparing
    a multi-part answer block (e.g. Chinese composite Q1's 7-item block)
    against the declared answer_value at the same semantic scope.
    Never truncates to per-q. A genuine content mismatch (different answers)
    remains a conflict after normalization.
    """
    if not text:
        return ""
    t = text.strip()
    t = _ANSWER_INDICATOR_RE.sub("", t)
    # Strip a leading "答案:" / "参考答案:" label.
    t = re.sub(r"^\s*(?:参考?答案|解[答折])\s*[：:]\s*", "", t)
    # Normalize full-width → half-width punctuation for consistent comparison.
    t = t.replace("（", "(").replace("）", ")")
    t = t.replace("　", " ")  # full-width space
    # Strip common annotations like (重点字：X) / (注：X).
    t = re.sub(r"\(\s*(?:重点字|注|说明|重点)\s*[：:][^)]*\)", "", t)
    # Remove ALL whitespace (newlines, spaces) to unify formatting.
    t = re.sub(r"\s+", "", t)
    return t


def _answer_content_overlap(av_norm: str, blk_norm: str) -> bool:
    """Check if answer_value content is substantially present in block.

    Handles paraphrase: Manifest answer_evidence.value may reword the source
    block (e.g. 要 vs 需要). Uses sliding-window token presence: if >70% of
    the value's 8-char windows appear in the block, consider content present.
    """
    if not av_norm or not blk_norm:
        return False
    if len(av_norm) < 4:
        return av_norm in blk_norm
    window = 8
    hits = 0
    total = 0
    for i in range(0, len(av_norm) - window + 1):
        total += 1
        if av_norm[i : i + window] in blk_norm:
            hits += 1
    return total > 0 and hits / total >= 0.7


def _entry_content_bounds(raw: str, entry_start: int, entry_end: int) -> tuple[int, int]:
    """Entry content bounds after stripping the `N.` / `N\\.` question-number prefix.

    Given the full entry slice [entry_start, entry_end), locate the `_ENTRY_RE`
    match at entry_start and return (content_start, content_end) covering only
    the answer content. Returns a zero-width span when content is empty (bare
    `N.` with no value).
    """
    m = next((m for m in _ENTRY_RE.finditer(raw) if m.start() == entry_start), None)
    if m is None:
        return entry_start, entry_end
    cs = m.end()
    while cs < entry_end and raw[cs].isspace():
        cs += 1
    ce = entry_end
    while ce > cs and raw[ce - 1].isspace():
        ce -= 1
    return cs, ce


def _block_entry_nums(text: str) -> set[str]:
    """Distinct question-number tokens in an answer-block text (guard-level).

    Filters decimal/quantity/version false positives: if every _ENTRY_RE match
    is immediately followed by a digit (e.g. ``3.0m/s``, ``2.0s``, ``v1.2``),
    the text has no real entry labels — return empty. If at least one match is
    entry-like (followed by non-digit), include all ≥1 numbers that form a
    sequence (≥2 with a consecutive pair). This keeps ``22.808-7754`` in a
    sequence like ``21.Gladys 22.808-7754 23.Lake`` while rejecting isolated
    or paired decimals.
    """
    entry_like: set[int] = set()
    all_nums: set[int] = set()
    for m in _ENTRY_RE.finditer(text):
        num = int(m.group(1))
        if num < 1:
            continue
        after = text[m.end():m.end() + 1] if m.end() < len(text) else ""
        all_nums.add(num)
        if not after.isdigit():
            entry_like.add(num)
    if not entry_like:
        return set()
    nums = all_nums
    if len(nums) < 2:
        return set()
    if not any((n + 1) in nums for n in nums):
        return set()
    return {str(n) for n in nums}


def _block_entry_range(text: str) -> tuple[int, int] | None:
    """(min, max) of plausible entry numbers, or None if no numbering sequence."""
    nums = _block_entry_nums(text)
    if not nums:
        return None
    ints = sorted(int(n) for n in nums)
    return (ints[0], ints[-1])


# ------------------------------------------------------------------ B3c-B
# Structured Answer Table Evidence Consumption (Owner ruling 2026-09).
# When answer_lines points at an HTML/table line that self-describes
# 「题号」row + 「答案」row, the target question number's same-column cell
# is deterministic structured evidence — NOT semantic inference.
# Any step fails → None (unresolved). No position/fallback guessing.

_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)


def _table_cells_with_offsets(raw: str) -> list[tuple[int, int, str]]:
    """Parse <td>…</td> cells as (start, end, inner_text) over the raw line."""
    out = []
    for m in _TD_RE.finditer(raw):
        inner = m.group(1)
        # strip nested tags inside the cell (e.g. <br>) — keep visible text
        visible = re.sub(r"<[^>]+>", "", inner)
        # offsets of the visible text within raw: find first occurrence of visible in inner span
        if visible == inner:
            # account for whitespace-only differences by locating in the match
            rel = inner.find(visible) if visible else 0
            start = m.start(1) + (rel if rel >= 0 else 0)
        else:
            # find visible inside the original inner region
            rel = inner.find(visible) if visible else -1
            start = m.start(1) + (rel if rel >= 0 else 0)
        if not visible:
            # empty cell: keep span at inner start (zero-length not useful)
            out.append((m.start(1), m.start(1), ""))
            continue
        out.append((start, start + len(visible), visible.strip()))
    return out


def decode_answer_table_cell(raw: str, qn: str) -> tuple[int, int, str] | None:
    """Deterministic 题号-row + 答案-row same-column lookup (B3c-B).

    Returns (start, end, cell_value) of the answer cell for `qn`, or None.
    Strict conditions (Owner C-2) — all must hold:
      1. a cell equal to '题号' exists;
      2. a cell equal to '答案' exists;
      3. `qn` appears in a 题号 sequence;
      4. that qn maps to a unique column;
      5. the paired 答案 sequence has a cell in the same column;
      6. cell value is non-empty.
    No last-row / nearest-token / order guessing.
    """
    if not raw or "<td" not in raw.lower():
        return None
    cells = _table_cells_with_offsets(raw)
    if len(cells) < 4:
        return None

    # Collect row sequences: each '题号' or '选项' starts a number row; each '答案' starts a value row.
    # Tables may repeat the pair for horizontal paging (1-10, 11-20, ...).
    # '选项' is used in some exam formats as the question-number row header
    # alongside '答案' (e.g. GEN-CHEM-002 shared answer table).
    _QN_ROW_HEADERS = frozenset({"题号", "选项"})
    qn_rows: list[list[tuple[int, int, str]]] = []
    ans_rows: list[list[tuple[int, int, str]]] = []
    mode = None
    cur: list[tuple[int, int, str]] = []
    for cell in cells:
        txt = cell[2]
        if txt in _QN_ROW_HEADERS:
            if mode == "a" and cur:
                ans_rows.append(cur)
            elif mode == "n" and cur:
                qn_rows.append(cur)
            mode, cur = "n", []
            continue
        if txt == "答案":
            if mode == "n" and cur:
                qn_rows.append(cur)
            elif mode == "a" and cur:
                ans_rows.append(cur)
            mode, cur = "a", []
            continue
        if mode is not None:
            cur.append(cell)
    if mode == "n" and cur:
        qn_rows.append(cur)
    if mode == "a" and cur:
        ans_rows.append(cur)

    if not qn_rows or not ans_rows:
        return None

    # Pair each 题号 row with the next 答案 row (declaration order).
    hits: list[tuple[int, int, str]] = []
    ai = 0
    for qrow in qn_rows:
        if ai >= len(ans_rows):
            break
        arow = ans_rows[ai]
        ai += 1
        for col, qcell in enumerate(qrow):
            if qcell[2] != qn:
                continue
            if col >= len(arow):
                continue
            acell = arow[col]
            if not acell[2]:
                continue
            hits.append((acell[0], acell[1], acell[2]))

    # Unique column required (Owner C-2 #5).
    if len(hits) != 1:
        return None
    return hits[0]


def decode_answer_table_headerless_horizontal(raw: str, qn: str) -> tuple[int, int, str] | None:
    """Header-less horizontal answer table (EN 2018 Shape B).

    Layout (no 题号/答案 label cells):
        <tr><td>1</td><td>2</td>...<td>10</td></tr>
        <tr><td>A</td><td>C</td>...<td>C</td></tr>
        <tr><td>11</td>...  (paged block repeats)

    Strict conditions — all must hold or return None:
      1. cells split into number-rows / answer-rows of equal length pairs;
      2. number-row cells are 1–3 digit integers only;
      3. answer-row cells are non-empty;
      4. `qn` hits exactly one column in a number-row;
      5. the paired answer-row has a non-empty cell in that column.
    No header inference, no nearest-token guessing.
    """
    if not raw or "<td" not in raw.lower():
        return None
    cells = _table_cells_with_offsets(raw)
    if len(cells) < 4 or len(cells) % 2 != 0:
        return None

    # Group into rows using <tr> boundaries when present; else split cells in
    # half only when the first half is all integers (strict page block).
    tr_parts = _TR_RE.split(raw)
    rows: list[list[tuple[int, int, str]]] = []
    if len(tr_parts) > 2:
        # re-parse per <tr> segment
        pos = 0
        ordered = []
        for seg in re.split(r"(<tr[^>]*>)", raw, flags=re.I):
            seg_cells = _table_cells_with_offsets(seg)
            if seg_cells:
                ordered.append(seg_cells)
        rows = ordered
    else:
        half = len(cells) // 2
        rows = [cells[:half], cells[half:]]

    # Pair number-row with following answer-row (equal length required).
    hits: list[tuple[int, int, str]] = []
    i = 0
    while i + 1 < len(rows):
        nrow, arow = rows[i], rows[i + 1]
        i += 2
        if len(nrow) != len(arow) or not nrow:
            return None
        for col, ncell in enumerate(nrow):
            if not re.fullmatch(r"\d{1,3}", ncell[2].strip()):
                return None  # not a number-row — fail closed
        for col, ncell in enumerate(nrow):
            if ncell[2].strip() != qn:
                continue
            acell = arow[col]
            if not acell[2].strip():
                continue
            hits.append((acell[0], acell[1], acell[2]))
    if len(hits) != 1:
        return None
    return hits[0]


_TR_RE = re.compile(r"<tr[^>]*>", re.I)
_TD_ATTR_RE = re.compile(r"<td([^>]*)>", re.I)


# \s* not \s+: real corpus has glued form `21-23DBC` / `36-40ADCGF`
# (no space between range end and letters) — E2E-011 昌平临川.
# \s*[:：]?\s*: real corpus has colon separator `56—59:CBBA` / `36—40：ABCBA`
# (fullwidth or halfwidth colon between range and letters) — E2E-012 一七一中.
_RANGE_KEY_RE = re.compile(
    r"(?<![\d])(\d{1,3})\s*[－~—–-]\s*(\d{1,3})\s*[:：]?\s*([A-Za-z]{2,20})"
)


def decode_range_answer_key(raw: str, qn: str) -> tuple[int, int, str] | None:
    """区间式答案键（E2E-010R1）：`19-23 DABCA` / `39-41 ADC 42-45 ADBB`。

    返回该 qn 对应字母在 raw 中的 (start, end, letter)。
    fail-closed：区间长度 != 字母串长度 -> None；qn 不在任何区间 -> None。
    """
    if not raw:
        return None
    try:
        n = int(qn)
    except (TypeError, ValueError):
        return None
    for m in _RANGE_KEY_RE.finditer(raw):
        lo, hi = int(m.group(1)), int(m.group(2))
        letters = m.group(3)
        if hi < lo:
            continue
        span_len = hi - lo + 1
        if len(letters) != span_len:
            continue  # fail-closed
        if lo <= n <= hi:
            idx = n - lo
            letter_start = m.start(3) + idx
            return (letter_start, letter_start + 1, letters[idx])
    return None


def decode_compact_answer_key(
    raw: str, qn: str, qn_list: list | None
) -> tuple[int, int, str] | None:
    """紧凑字母键 `FGDAE`：按声明题号顺序拆分（E2E-010 七选五）。"""
    if not raw or not qn_list:
        return None
    s = re.sub(r"\s+", "", raw)
    if not re.fullmatch(r"[A-Za-z]+", s):
        return None
    if len(s) != len(qn_list):
        return None
    try:
        n = int(qn)
    except (TypeError, ValueError):
        return None
    if n not in qn_list:
        return None
    idx = list(qn_list).index(n)
    start = raw.find(s[0]) if s else 0
    # map compact index to raw offset (skip whitespace in raw)
    pos = 0
    seen = 0
    for i, ch in enumerate(raw):
        if ch.isspace():
            continue
        if seen == idx:
            pos = i
            break
        seen += 1
    else:
        pos = 0
    return (pos, pos + 1, s[idx])


def _table_rows_with_cells(raw: str) -> list[list[tuple[int, int, str]]]:
    """Parse <tr> rows, each as a list of (start, end, inner_text) cells.

    Handles rowspan: when a <td rowspan=N> is seen, the next N-1 rows get
    an empty placeholder cell at that column position (maintaining alignment).
    """
    rows: list[list[tuple[int, int, str]]] = []
    tr_matches = list(_TR_RE.finditer(raw))
    # rowspan_remaining[col] = rows still to skip for that column
    rowspan_remaining: dict[int, int] = {}

    for i, trm in enumerate(tr_matches):
        row_start = trm.end()
        row_end = tr_matches[i + 1].start() if i + 1 < len(tr_matches) else len(raw)
        row_text = raw[row_start:row_end]

        cells: list[tuple[int, int, str]] = []
        col = 0
        for td_m in _TD_RE.finditer(row_text):
            inner = td_m.group(1)
            tag_start = row_text.rfind("<td", 0, td_m.start(1))
            attrs = row_text[tag_start:td_m.start(1)] if tag_start >= 0 else ""
            rs_m = re.search(r'rowspan\s*=\s*["\']?(\d+)', attrs, re.I)
            rowspan = int(rs_m.group(1)) if rs_m else 1

            visible = re.sub(r"<[^>]+>", "", inner).strip()
            rel = inner.find(visible) if visible else 0
            start = row_start + td_m.start(1) + (rel if rel >= 0 else 0)

            # insert placeholders for columns consumed by prior rowspan
            while col in rowspan_remaining and rowspan_remaining[col] > 0:
                rowspan_remaining[col] -= 1
                if rowspan_remaining[col] == 0:
                    del rowspan_remaining[col]
                cells.append((row_start, row_start, ""))  # placeholder
                col += 1

            cells.append((start, start + len(visible), visible))
            if rowspan > 1:
                rowspan_remaining[col] = rowspan - 1
            col += 1

        # trailing placeholders
        while col in rowspan_remaining and rowspan_remaining[col] > 0:
            rowspan_remaining[col] -= 1
            if rowspan_remaining[col] == 0:
                del rowspan_remaining[col]
            cells.append((row_start, row_start, ""))
            col += 1

        rows.append(cells)
    return rows


def _decode_answer_table_continuation(raw: str) -> str | None:
    """Detect answer table continuation rows (empty first cell = rowspan overflow).

    For cross-line evidence where a question's answer continues on the next
    line's table (e.g. Physics Q26 spans lines 368 and 373). Returns the
    answer cell text from continuation rows, or None if no continuation found.
    """
    rows = _table_rows_with_cells(raw)
    if not rows:
        return None
    parts = []
    for cells in rows:
        if len(cells) < 2:
            continue
        first_text = cells[0][2].strip()
        # Continuation: empty first cell (rowspan overflow)
        if first_text:
            break  # non-empty first cell = new question or header
        ans_text = cells[1][2].strip()
        if ans_text:
            parts.append(ans_text)
    return "\n".join(parts) if parts else None


def decode_answer_table_vertical(raw: str, qn: str) -> tuple[int, int, str] | None:
    """Vertical-format answer table lookup (题号|答案 as column headers).

    Format:
        <tr><td>题号</td><td>答案</td><td>分数</td></tr>
        <tr><td>21</td><td>正</td><td>2分</td></tr>
        <tr><td></td><td>变小</td><td>2分</td></tr>   ← rowspan continuation

    Also handles header-less continuation tables (second page of answers):
        <tr><td></td><td>续接内容</td><td>4分</td></tr>
        <tr><td>27（6分）</td><td>解：...</td><td></td></tr>

    Returns (start, end, answer_text) or None.
    Deterministic: only matches question-number cell patterns,
    no last-row / nearest-token guessing.
    """
    rows = _table_rows_with_cells(raw)
    if not rows:
        return None

    # Find header row and column layout.
    # Standard 3-col:   题号 | 答案 | 分数
    # Dual-block 6-col: 题号 | 答案 | 分数 | 题号 | 答案 | 分数
    header_idx = -1
    qn_col, ans_col = 0, 1  # left block columns
    for i, cells in enumerate(rows):
        if len(cells) >= 2 and cells[0][2] == "题号" and cells[1][2] == "答案":
            header_idx = i
            if len(cells) >= 5 and cells[3][2] == "题号" and cells[4][2] == "答案":
                # six-column dual-block: try left first, then right
                pass  # will handle both blocks below
            break

    data_start = header_idx + 1 if header_idx >= 0 else 0

    qn_pat = re.compile(rf"^{re.escape(qn)}(?:\s*[（(].*[)）])?\s*$")
    any_qn_pat = re.compile(r"^\d{1,3}(?:\s*[（(].*[)）])?\s*$")

    # Scan one block (qn_col → ans_col); return (start, end, text) or None.
    def _scan_block(qc: int, ac: int):
        for i in range(data_start, len(rows)):
            cells = rows[i]
            if len(cells) <= max(qc, ac):
                continue
            first_text = cells[qc][2].strip()
            if not qn_pat.match(first_text):
                continue
            ans_start = cells[ac][0]
            ans_end = cells[ac][1]
            parts = [cells[ac][2]]
            for j in range(i + 1, len(rows)):
                cont = rows[j]
                if len(cont) <= max(qc, ac):
                    break
                cont_first = cont[qc][2].strip()
                if any_qn_pat.match(cont_first):
                    break
                parts.append(cont[ac][2])
                ans_end = cont[ac][1]
            return (ans_start, ans_end, "\n".join(parts))
        return None

    # Left block (standard 3-col layout).
    result = _scan_block(0, 1)
    if result is not None:
        return result
    # Right block (six-column dual-block layout).
    result = _scan_block(3, 4)
    return result


# 行内选项标签（bounded，防 "对A项" 误配随机大写；需标签+分隔符）。
# 全角逗号 `，`：真实卷 `C. 水土流失 D，物种减少`（U44-46）。格式兼容，非 heuristic。
# GEO-SUBQ：紧凑组合选项 `A.①②B.①④` 的圈号紧贴下一标签；`②` 属 \\w 会挡住
# `(?<![\w])`，改为仅排除 ASCII 词符 + CJK 汉字（防 `对A`/`则A`），圈号不再误挡。
_LABEL_RE = re.compile(r"(?<![A-Za-z0-9_一-鿿])[（(]?([A-Ha-h])\s*[.．、:，,)）]")
# P1.4-B Rule B：digit-glued `2D.`（数学 Q4）。clean lookbehind `(?<![\w])` 会因
# 前置 `2` 而漏检，故单独识别。NOT `2\cos…`（字母后无分隔符）。
_LABEL_DIGIT_GLUE_RE = re.compile(r"(?<![A-Za-z0-9_])(\d)([A-H])\s*[.．、]")
# P1.4-B Rule C：line-start `D 麦哲伦`（历史 Q29），缺分隔符。
_LABEL_SPACE_SEP_RE = re.compile(r"^(?:[ \u00a0]*)([A-Ha-h])[ \u00a0]{1,3}(?=[\u4e00-\u9fff])")
_LABEL_SPACE_SEP_PROSE = re.compile(
    r"^[ \u00a0]*[A-Ha-h][ \u00a0]+(?:是|有|在|了|和|与|或|被|把|对|从|到|为|要|会|能|可|这|那|其|年|月|日)"
)


def _label_offsets(text: str, label: str) -> list[int]:
    """Char offsets of option-label tokens for `label` in `text` (Rules A-C forms)."""
    offs: list[int] = []
    for m in _LABEL_RE.finditer(text):
        if m.group(1).upper() == label.upper():
            offs.append(m.start())
    for m in _LABEL_DIGIT_GLUE_RE.finditer(text):
        if m.group(2).upper() == label.upper():
            offs.append(m.start(2))
    if not _LABEL_SPACE_SEP_PROSE.search(text):
        for m in _LABEL_SPACE_SEP_RE.finditer(text):
            if m.group(1).upper() == label.upper():
                offs.append(m.start(1))
    return sorted(set(offs))


def _all_label_token_spans(text: str) -> list[tuple[int, int, str]]:
    """All option-label token spans on a line: (start, end, letter) in source order.

    end = index AFTER the separator (start of option content).
    Used to slice content = after this label → before next label (Task A).
    """
    hits: list[tuple[int, int, str]] = []
    for m in _LABEL_RE.finditer(text):
        hits.append((m.start(), m.end(), m.group(1).upper()))
    for m in _LABEL_DIGIT_GLUE_RE.finditer(text):
        # token is `2D.` — glue digit belongs to the label TOKEN (not previous content)
        # so previous option content ends before `2`, and D content starts after `D.`
        hits.append((m.start(1), m.end(), m.group(2).upper()))
    if not _LABEL_SPACE_SEP_PROSE.search(text):
        for m in _LABEL_SPACE_SEP_RE.finditer(text):
            # `D 麦哲伦` — content starts after letter + spaces
            hits.append((m.start(1), m.end(), m.group(1).upper()))
    # stable by start offset; drop exact duplicates
    hits = sorted(set(hits), key=lambda x: (x[0], x[1]))
    return hits


def _option_content_bounds(
    text: str,
    label: str,
    prefer_offset: int | None = None,
    boundary_labels: frozenset | set | None = None,
):
    """Return (content_start, content_end) for `label` on `text`, or None.

    Content = characters after this label's separator up to the next **declared**
    option-label token (or end of line). NEVER includes the label token itself.
    Task A: `A. 1 B. 2` → A content='1', B content='2'.
    `boundary_labels` limits which tokens may end content — prevents chemical
    `H:` in `B. H: O: H` from slicing B to empty when H is not a declared option.
    """
    tokens = _all_label_token_spans(text)
    if not tokens:
        return None
    lab_u = label.upper()
    idxs = [i for i, t in enumerate(tokens) if t[2] == lab_u]
    if not idxs:
        return None
    pick = idxs[0]
    if prefer_offset is not None:
        for i in idxs:
            if tokens[i][0] >= prefer_offset:
                pick = i
                break
    start = tokens[pick][1]  # after separator
    # next boundary: first later token whose letter is a declared option label
    end = len(text)
    for i in range(pick + 1, len(tokens)):
        letter = tokens[i][2]
        if boundary_labels is None or letter in boundary_labels:
            end = tokens[i][0]
            break
    while end > start and text[end - 1] in " \t\u3000":
        end -= 1
    if start > end:
        return None
    return (start, end)



# ---------------------------------------------------------------- P4
# HTML-table option cells (Chemistry Q9/Q19/Q24/Q25).
# Deterministic cell-to-label mapping. Three layouts only; anything else -> {}.
# Figures are NOT bound here (figure_refs is unsupported, BUG-V3-020).
# Q24 figure order is positional (col0->A), never sorted by F number.

_HTML_OPT_LABEL_RE = re.compile(r"^([A-Ha-h])\s*[.．、:，,)）]\s*(.+)$", re.S)
_HTML_BARE_LABEL_RE = re.compile(r"^([A-Ha-h])$")
# page footer / section header -- never option content (Rule A hard guard)
_PAGE_FOOTER_RE = re.compile(r"第\s*\d+\s*页|共\s*\d+\s*页")
_SECTION_HDR_RE = re.compile(r"^第[一二三四五六七八九十]+[部分章节]")


def _html_table_option_cells(raw: str) -> dict[str, tuple[int, int, str]]:
    """Extract A-D options from a single HTML table line.

    Returns {label: (content_start, content_end, clean_text)}.
    content_* are char offsets in `raw`. clean_text is for `cell=` evidence.

    Layouts (deterministic, fail-closed):
      1. horizontal  -- cell text is `A. content` (Q9, Q24)
      2. row-oriented -- col0 is bare `A`, content = remaining cells (Q25)
      3. column-oriented -- header row has bare `A`..`D`, content = cells below (Q19)
    """
    if "<td" not in raw.lower():
        return {}
    rows = _table_rows_with_cells(raw)
    if not rows:
        return {}

    # --- layout 1: horizontal, label+content in the same cell ---
    hits: dict[str, tuple[int, int, str]] = {}
    for row in rows:
        for (s, e, text) in row:
            m = _HTML_OPT_LABEL_RE.match(text)
            if not m:
                continue
            lab = m.group(1).upper()
            c_start = s + m.start(2)
            c_end = s + m.end(2)
            hits.setdefault(lab, (c_start, c_end, text[m.start(2):].strip()))
    if len(hits) >= 2:
        return hits

    # --- layout 2: row-oriented, bare label in col0 ---
    hits = {}
    for row in rows:
        if len(row) < 2:
            continue
        m = _HTML_BARE_LABEL_RE.match(row[0][2].strip())
        if not m:
            continue
        lab = m.group(1).upper()
        parts = [c[2] for c in row[1:] if c[2]]
        if not parts:
            continue
        c_start, c_end = row[1][0], row[-1][1]
        hits.setdefault(lab, (c_start, c_end, " ".join(parts)))
    if len(hits) >= 2:
        return hits

    # --- layout 3: column-oriented, bare labels in one header row ---
    for i, row in enumerate(rows):
        label_cols: dict[str, int] = {}
        for j, cell in enumerate(row):
            m = _HTML_BARE_LABEL_RE.match(cell[2].strip())
            if m:
                label_cols[m.group(1).upper()] = j
        if len(label_cols) < 2:
            continue
        hits = {}
        for lab, col in label_cols.items():
            vals = [
                r[col][2] for r in rows[i + 1:]
                if col < len(r) and r[col][2]
            ]
            if not vals:
                continue
            first = next(
                r[col][0] for r in rows[i + 1:]
                if col < len(r) and r[col][2]
            )
            last = next(
                r[col][1] for r in reversed(rows[i + 1:])
                if col < len(r) and r[col][2]
            )
            hits.setdefault(lab, (first, last, " ".join(vals)))
        return hits
    return {}


# E owns source-span overlap（material span 不得与子题/其他 material 重叠）。
_MATERIAL_ROLES = frozenset(
    {"material", "word_bank", "shared_option_pool", "task_instruction"}
)


class _LineIndex:
    """有序行视图（seq 单调）。纯内存，无 ORM。"""

    def __init__(self, lines: tuple[SourceLineView, ...]):
        self.lines = tuple(sorted(lines, key=lambda l: l.seq))
        self._by_ref = {l.line_ref: l for l in self.lines}
        self._norm = [normalize_text(l.text) for l in self.lines]

    def get(self, ref: str) -> SourceLineView:
        return self._by_ref[ref]

    def seq_of(self, ref: str) -> int:
        return self._by_ref[ref].seq

    def between(self, lo: int, hi: int) -> list[SourceLineView]:
        return [l for l in self.lines if lo <= l.seq < hi]

    def between_incl(self, lo: int, hi: int) -> list[SourceLineView]:
        return [l for l in self.lines if lo <= l.seq <= hi]

    def after(self, ref: str) -> list[SourceLineView]:
        return [l for l in self.lines if l.seq > self.seq_of(ref)]

    def raw_hits(self, query: str) -> list[str]:
        return [l.line_ref for l in self.lines if query in l.text]

    def norm_hits(self, norm_query: str) -> list[str]:
        return [l.line_ref for l, n in zip(self.lines, self._norm) if norm_query in n]

    def fuzzy_hits(self, norm_query: str) -> list[str]:
        flat = norm_query.replace(" ", "")
        return [
            l.line_ref for l, n in zip(self.lines, self._norm)
            if n != flat and n.replace(" ", "") == flat
        ]


def _locate(query: str, idx: _LineIndex) -> tuple[str, list[str]]:
    """exact > normalized > fuzzy/missing/ambiguous（不做自动接受）。"""
    raw = idx.raw_hits(query)
    if len(raw) == 1:
        return "exact", raw
    if len(raw) > 1:
        return "ambiguous", raw
    nq = normalize_text(query)
    norm = idx.norm_hits(nq)
    if len(norm) == 1:
        return "normalized", norm
    if len(norm) > 1:
        return "ambiguous", norm
    fuzzy = idx.fuzzy_hits(nq)
    if fuzzy:
        return "fuzzy", fuzzy
    return "missing", []


def _is_resolved(status: str) -> bool:
    return status in ("exact", "normalized", "contextual")


class _Out:
    """一次 resolve 的收集容器。持 idx 以便从 line_ref 切片 span 文本（BUG-V3-012）。"""

    def __init__(self, svid: uuid.UUID, idx: "_LineIndex"):
        self.svid = svid
        self._idx = idx
        self.resolved: list[ResolvedSpan] = []
        self.unresolved: list[UnresolvedReference] = []

    def _seal_answer_ownership(self, t, evidence, texts, role=None, answer_text=""):
        """Attach ownership= to answer evidence; force foreign to empty later.

        Every answer emit MUST pass through here so no branch can skip
        ownership classification (CONTRACT-FINAL: sole binding exit).

        P0-R16: registers BindingFact with source_version_id + decode_loc.
        """
        ev = tuple(evidence)
        role_v = role or getattr(t, "role", "")
        if role_v != "answer":
            return ev
        qn = str(getattr(t, "question_number", "") or "")
        _lines = [x for x in (texts or ()) if x is not None]
        _span_id = f"sp-{t.target_id}" if getattr(t, "target_id", "") else ""
        _unit_id = str(getattr(t, "unit_id", "") or "")
        _ans = answer_text if answer_text is not None else ""
        _svid = str(self.svid)

        # Extract existing ownership + structural evidence from evidence tags.
        _existing_own = None
        _existing_bev = ""
        _decode_parts = []
        for e in ev:
            s = str(e)
            if s.startswith("ownership="):
                _existing_own = s.split("=", 1)[1]
            elif s.startswith("binding_evidence="):
                _existing_bev = s.split("=", 1)[1]
            elif s.startswith("cell="):
                _decode_parts.append(f"cell:{s.split('=', 1)[1]}")
            elif s.startswith("qn="):
                _decode_parts.append(f"qn:{s.split('=', 1)[1].strip()}")
            elif s.startswith("qns="):
                _decode_parts.append(f"qns:{s.split('=', 1)[1].strip()}")
            elif s.startswith("range="):
                _decode_parts.append(f"range:{s.split('=', 1)[1].strip()}")
        _decode_loc = "|".join(_decode_parts)

        # R16c: BindingFact is the single ownership authority. Register it
        # from real source lines, then write fact.ownership back onto span
        # evidence so Compiler/Gate see the same conclusion (fixes
        # fact=match vs compiled=unknown divergence).
        _fact_own = None
        _fact_bev = ""
        if _span_id and _svid:
            try:
                from app.domains.gate.binding_fact import (
                    derive_binding_fact,
                    register_trusted_binding_fact,
                )
                _fact = derive_binding_fact(
                    span_id=_span_id,
                    source_version_id=_svid,
                    unit_id=_unit_id,
                    question_number=qn,
                    source_lines=_lines,
                    answer_text=str(_ans),
                    evidence_kind=_existing_bev or "",
                    decode_loc=_decode_loc,
                    declared_value=str(
                        getattr(t, "answer_value", "") or ""
                    ),
                )
                register_trusted_binding_fact(_fact)
                _fact_own = _fact.ownership or "unknown"
                _fact_bev = (
                    f"fact:{_fact.evidence_kind}"
                    if _fact.evidence_kind
                    else "fact"
                )
            except Exception:
                # Registration failure → force unknown (fail closed).
                _fact_own = "unknown"
                _fact_bev = "registration_failed"
        else:
            # No span/svid (defensive): fall back to local classify only.
            own, bev = bind_answer_text(_lines, qn)
            _fact_own = own
            _fact_bev = bev or "p0-unified"

        # Single write-back: strip any prior ownership/binding tags and
        # stamp the fact conclusion.
        cleaned = tuple(
            e
            for e in ev
            if not str(e).startswith("ownership=")
            and not str(e).startswith("binding_evidence=")
        )
        # R2-HANDOFF: persist BindingFact verification inputs in evidence so
        # a cross-process review path can reconstruct and re-verify the fact.
        # Never a trust shortcut — verify_binding_fact re-derives ownership.
        _dv = str(getattr(t, "answer_value", "") or "")
        return cleaned + (
            f"ownership={_fact_own}",
            f"binding_evidence={_fact_bev}",
            f"fact_declared_value={_dv}",
            f"fact_decode_loc={_decode_loc}",
            f"fact_source_hash={_fact.source_hash if _fact else ''}",
        )

    def add_span(self, unit_id: str, t, refs, status, evidence, role_hint=None):
        text = self._slice(refs)
        role_v = role_hint or t.role
        try:
            raw_lines = [self._idx.get(r).text for r in refs]
        except Exception:
            raw_lines = [text]
        evidence = self._seal_answer_ownership(t, evidence, raw_lines or [text], role=role_v, answer_text=text)
        # foreign / never-publish-bind: keep span empty when ownership is foreign
        own = next(
            (str(e).split("=", 1)[1] for e in evidence if str(e).startswith("ownership=")),
            None,
        )
        if role_v == "answer" and own == OWNERSHIP_FOREIGN:
            self.add_empty_answer(
                t,
                tuple(evidence) + (f"foreign_source_text={text[:80]}",),
            )
            return
        self.resolved.append(
            ResolvedSpan(
                span_id=f"sp-{t.target_id}",
                source_version_id=self.svid,
                role=role_v,
                start_line_ref=refs[0],
                end_line_ref=refs[-1],
                line_refs=tuple(refs),
                granularity="line",
                start_offset=None,
                end_offset=None,
                text_hash=_raw_sha256(text),
                resolution_status=status,
                evidence=tuple(evidence),
            )
        )

    def add_char_span(self, unit_id, t, line_ref, start, end, status, evidence):
        """line_character span：按已知 [start,end) raw offsets 切片（不重查，调用方保证有界唯一）。"""
        raw = self._idx.get(line_ref).text
        end = min(end, len(raw))
        if start < 0 or start >= end:
            self.unresolved.append(
                UnresolvedReference(
                    reference_id=t.target_id, role=t.role,
                    resolution_status="incomplete",
                    evidence=("invalid inline offsets", str(start), str(end)),
                )
            )
            return
        _slice_text = raw[start:end]
        # Classify ownership from the RAW LINE (may carry the N. entry token),
        # not from the stripped answer cell — otherwise `1. B` → text `B` is bare.
        evidence = self._seal_answer_ownership(t, evidence, [raw], answer_text=_slice_text)
        own = next(
            (str(e).split("=", 1)[1] for e in evidence if str(e).startswith("ownership=")),
            None,
        )
        if t.role == "answer" and own == OWNERSHIP_FOREIGN:
            self.add_empty_answer(
                t,
                tuple(evidence) + (f"foreign_source_text={_slice_text[:80]}",),
            )
            return
        self.resolved.append(
            ResolvedSpan(
                span_id=f"sp-{t.target_id}", source_version_id=self.svid,
                role=t.role, start_line_ref=line_ref, end_line_ref=line_ref,
                line_refs=(line_ref,), granularity="line_character",
                start_offset=start, end_offset=end,
                text_hash=_raw_sha256(_slice_text),
                resolution_status=status, evidence=tuple(evidence),
            )
        )

    def add_unresolved(self, t, status, evidence):
        self.unresolved.append(
            UnresolvedReference(
                reference_id=t.target_id, role=t.role,
                resolution_status=status, evidence=tuple(evidence),
            )
        )

    def add_value_only_answer(self, t, value, evidence):
        """Bind a declared answer_value with NO fabricated source location.

        P0-R3: when the manifest carries answer_value but no reliable
        answer_lines, the honest representation is value-only. Do NOT invent
        line_refs (e.g. P1L001) — fabricated provenance must never look
        byte-proven. resolution_status='value_only' is outside
        {exact, normalized}, so Gate auto_allowed stays False.
        """
        evidence = self._seal_answer_ownership(t, evidence, [value], answer_text=value) + (
            f"cell={value}",
            "ownership=unknown",  # value_only cannot prove line ownership
        ) if t.role == "answer" else tuple(evidence) + (f"cell={value}",)
        # ensure single ownership= tag (classifier may have added one)
        if t.role == "answer" and not any(str(e).startswith("ownership=") for e in evidence[: -2]):
            pass
        # force unknown for value_only even if classifier said otherwise
        evidence = tuple(
            e if not str(e).startswith("ownership=") else "ownership=unknown"
            for e in evidence
        ) if t.role == "answer" else evidence
        self.resolved.append(
            ResolvedSpan(
                span_id=f"sp-{t.target_id}",
                source_version_id=self.svid,
                role=t.role,
                start_line_ref="VALUE-ONLY",
                end_line_ref="VALUE-ONLY",
                line_refs=(),
                granularity="value_only",
                start_offset=None,
                end_offset=None,
                text_hash=_raw_sha256(value),
                resolution_status="value_only",
                evidence=tuple(evidence),
            )
        )

    def add_empty_answer(self, t, evidence):
        """Bind an answer span. When extraction fails but a declared
        answer_value exists, use it as the answer text (value-passing fix).
        Otherwise force text="" via cell= evidence so compilation cannot
        pick up an unrelated line.

        E2E-013 fallback-guard pattern. P0-R3: never fabricate source
        location for value-only answers.
        """
        # R2-FIX: when a declared answer_value exists, use it as the answer
        # text instead of going empty. Register BindingFact via
        # _seal_answer_ownership so downstream admission can verify.
        _av = getattr(t, "answer_value", None)
        _av_s = str(_av).strip() if _av is not None and str(_av).strip() else ""
        if _av_s:
            sealed = self._seal_answer_ownership(t, evidence, [_av_s], answer_text=_av_s)
            self.resolved.append(
                ResolvedSpan(
                    span_id=f"sp-{t.target_id}",
                    source_version_id=self.svid,
                    role=t.role,
                    start_line_ref="VALUE-ONLY",
                    end_line_ref="VALUE-ONLY",
                    line_refs=(),
                    granularity="value_only",
                    start_offset=None,
                    end_offset=None,
                    text_hash=_raw_sha256(_av_s),
                    resolution_status="value_only",
                    evidence=sealed + (f"cell={_av_s}",),
                )
            )
            return
        self.resolved.append(
            ResolvedSpan(
                span_id=f"sp-{t.target_id}",
                source_version_id=self.svid,
                role=t.role,
                start_line_ref="ABSENT",
                end_line_ref="ABSENT",
                line_refs=(),
                granularity="absent",
                start_offset=None,
                end_offset=None,
                text_hash=_raw_sha256(""),
                resolution_status="absent",
                evidence=tuple(evidence) + ("cell=",),
            )
        )

    def add_fragment_span(self, unit_id, t, line_ref, q, status, evidence):
        """line_character span：在 raw 行文本内精确子串查找 offset（code-point 索引）。

        行内多命中 → 调用方须先判 ambiguous（不在此 first-match）。找不到唯一 raw 子串
        （仅 normalized 命中）→ 退化整行 granularity=line。
        """
        raw = self._idx.get(line_ref).text
        pos = raw.find(q)
        if pos == -1:
            # normalized 命中但 raw 无该串 → 无法给可靠 offset，退化为整行 line span。
            self.resolved.append(
                ResolvedSpan(
                    span_id=f"sp-{t.target_id}", source_version_id=self.svid,
                    role=t.role, start_line_ref=line_ref, end_line_ref=line_ref,
                    line_refs=(line_ref,), granularity="line",
                    start_offset=None, end_offset=None,
                    text_hash=_raw_sha256(raw), resolution_status=status,
                    evidence=tuple(evidence) + ("degrade-to-line(no-raw-slice)",),
                )
            )
            return
        if raw.find(q, pos + len(q)) != -1:
            self.unresolved.append(
                UnresolvedReference(
                    reference_id=t.target_id, role=t.role,
                    resolution_status="ambiguous",
                    evidence=("line-fragment matches more than once on raw line",),
                )
            )
            return
        self.resolved.append(
            ResolvedSpan(
                span_id=f"sp-{t.target_id}", source_version_id=self.svid,
                role=t.role, start_line_ref=line_ref, end_line_ref=line_ref,
                line_refs=(line_ref,), granularity="line_character",
                start_offset=pos, end_offset=pos + len(q),
                text_hash=_raw_sha256(raw[pos : pos + len(q)]),
                resolution_status=status, evidence=tuple(evidence),
            )
        )

    def _slice(self, refs: list[str]) -> str:
        """span 覆盖行文本：多行以 "\\n" join（BUG-V3-012 implementation choice，
        与段 B IS-4 重建规则一致；20 §5.5 未冻结跨行拼接）。"""
        return "\n".join(self._idx.get(r).text for r in refs)


class SourceResolver:
    """Semantic Reference → ResolvedRun（纯函数入口）。"""

    def __init__(
        self,
        *,
        source_version_id: uuid.UUID,
        lines: tuple[SourceLineView, ...],
        figures: tuple[SourceFigureView, ...] = (),
    ):
        self._svid = source_version_id
        self._idx = _LineIndex(lines)
        self._figures = figures
        # Declared stem starts (from question_search_lines), set in resolve().
        # Upper-bound guard: stem must not cross the next declared question start.
        self._declared_starts: tuple[int, ...] = ()
        # Answer evidence ranges shared by ≥2 units, set in resolve().
        # Maps (start, end) → ordered qn list for compact key splitting.
        self._shared_answer_ranges: dict[tuple[int, int], list[str]] = {}
        self._local_body_units: set[str] = set()
        self._local_seq_units: set[str] = set()
        # Printed number of the current unit (set in _resolve_unit).
        self._current_printed: str | None = None
        # Whether stem location produced an unresolved (ambiguous/missing).
        self._stem_had_unresolved: bool = False
        # 题目区终点 = 首个 答案/详解/解析 表头 seq（其后为答案/详解区，不得当题号行）。
        self._qzone_end = next(
            (l.seq for l in self._idx.lines
             if is_answer_header(normalize_text(l.text))
             or is_explanation_header(normalize_text(l.text))),
            10**9,
        )

    def _question_zone(self):
        """仅题目区（答案/详解表头之前）的行。"""
        return [l for l in self._idx.lines if l.seq < self._qzone_end]

    def resolve(self, annotation_payload: dict) -> ResolvedRun:
        out = _Out(self._svid, self._idx)
        by_unit: dict[str, list] = {}
        for t in extract_targets(annotation_payload):
            by_unit.setdefault(t.unit_id, []).append(t)
        # E2E-014 answer-binding safety: pre-compute which answer evidence
        # ranges are shared by ≥2 units. Only shared ranges are eligible for
        # the "unmappable local numbering" fail-closed guard; per-unit ranges
        # are that unit's own answer and must not be cleared.
        _range_owners: dict[tuple[int, int], int] = {}
        _range_qns: dict[tuple[int, int], list[str]] = {}
        for uid, _targets in by_unit.items():
            for _t in _targets:
                if _t.kind == "answer_zone" and _t.evidence_lines is not None:
                    _r = (_t.evidence_lines[0], _t.evidence_lines[1])
                    _range_owners[_r] = _range_owners.get(_r, 0) + 1
                    _qn_str = str(_t.question_number or "")
                    if _qn_str:
                        _range_qns.setdefault(_r, []).append(_qn_str)
        self._shared_answer_ranges = {
            r: sorted(qns, key=lambda x: int(x) if x.isdigit() else 0)
            for r, qns in _range_qns.items()
            if _range_owners.get(r, 0) >= 2
        }
        # P0-R5b: units with positive local-numbering evidence. A local
        # sub-index label (`1.` for unit 26) is allowed ONLY when:
        # (a) the entry content is a multi-part local body, OR
        # (b) multiple units in this batch form a local label sequence
        #     (1., 2., 3., …) while their question numbers are all > 10.
        self._local_body_units: set[str] = set()
        self._local_seq_units: set[str] = set()
        _entry_no_by_unit: dict[str, int] = {}
        _qn_by_unit: dict[str, int] = {}
        for uid, targets in by_unit.items():
            for t in targets:
                if t.kind == "question_label" and getattr(t, "question_number", None):
                    try:
                        _qn_by_unit[uid] = int(t.question_number)
                    except (TypeError, ValueError):
                        pass
                if t.kind == "answer_zone" and t.evidence_lines is not None:
                    refs = self._evidence_line_refs(
                        t.evidence_lines[0], t.evidence_lines[1]
                    )
                    if not refs:
                        continue
                    raw = self._idx.get(refs[0]).text
                    rest = "\n".join(self._idx.get(r).text for r in refs[1:])
                    for m in _ENTRY_RE.finditer(raw):
                        try:
                            _entry_no_by_unit[uid] = int(m.group(1))
                        except ValueError:
                            pass
                        cs, ce = _entry_content_bounds(raw, m.start(), len(raw))
                        body = raw[cs:ce].strip()
                        if rest.strip():
                            body = (body + "\n" + rest).strip()
                        if _is_local_body_content(body) or _is_local_prose_body(body):
                            self._local_body_units.add(uid)
                        break
        # multi-unit local label sequence: entries 1..k, qns all > 10
        _seq_entries = {
            uid: e for uid, e in _entry_no_by_unit.items()
            if e <= 10 and _qn_by_unit.get(uid, 0) > 10
        }
        if len(_seq_entries) >= 2:
            _vals = sorted(_seq_entries.values())
            # P0-R5b: a batch sequence is local evidence only when it starts
            # at 1 and is consecutive. A pair `5.A / 6.B` is another
            # question's answers, not a local 1..k sequence.
            if _vals[0] == 1 and all(
                uid in self._local_body_units for uid in _seq_entries
            ) and _vals == list(range(_vals[0], _vals[0] + len(_vals))):
                self._local_seq_units.update(_seq_entries.keys())
        # Fix (E2E-007B KHH2 over-capture): declared stem starts in document order.
        # Used as an upper bound so a stem cannot swallow later questions'
        # declared content (option-less fill-in/short-answer especially).
        declared_starts: list[int] = []
        self._declared_stem_ranges: dict[str, tuple[int, int]] = {}
        for uid, targets in by_unit.items():
            for t in targets:
                if t.kind == "question_label" and t.question_search_lines:
                    lo, hi = t.question_search_lines
                    refs_lo = self._evidence_line_refs(lo, lo)
                    if refs_lo:
                        declared_starts.append(self._idx.seq_of(refs_lo[0]))
                    # Track full stem ranges for extra_lines ownership filtering
                    refs_hi = self._evidence_line_refs(hi, hi)
                    if refs_lo and refs_hi:
                        self._declared_stem_ranges[uid] = (
                            self._idx.seq_of(refs_lo[0]),
                            self._idx.seq_of(refs_hi[0]),
                        )
        self._declared_starts = tuple(sorted(set(declared_starts)))
        # Fourth-cut B: resolve ALL material bodies first so stem boundaries can
        # respect material regions (own-stem and neighbor-stem).
        for unit_id, targets in by_unit.items():
            for t in targets:
                if t.kind == "instruction_marker":
                    self._span_other(out, unit_id, t)
        mat_lines: set[str] = set()
        mat_starts: list[int] = []
        for s in out.resolved:
            if s.role in _MATERIAL_ROLES:
                for ref in s.line_refs:
                    mat_lines.add(ref)
                if s.line_refs:
                    mat_starts.append(self._idx.seq_of(s.line_refs[0]))
        for unit_id, targets in by_unit.items():
            self._resolve_unit(out, unit_id, targets,
                               mat_lines=mat_lines, mat_starts=mat_starts)
        self._enforce_material_overlap(out)
        rels = self._resolve_relations(
            out, extract_relations(annotation_payload)
        )
        return ResolvedRun(
            source_version_id=self._svid,
            resolved_spans=tuple(out.resolved),
            unresolved_references=tuple(out.unresolved),
            resolved_relations=tuple(r for r in rels if r.status == "resolved"),
            unresolved_relations=tuple(r for r in rels if r.status != "resolved"),
            structural_regions=self._compute_regions(),
        )

    def _compute_regions(self) -> tuple[SourceRegion, ...]:
        """Structural region map from deterministic header grammar (H-3).

        Produces question/answer/explanation structural regions. This is
        **consistency evidence** for the Source Evidence Binding Contract,
        NOT semantic truth. Gate uses it for span-overlap consistency checks.

        No answer header -> only question region (entire source is question zone).
        """
        lines = self._idx.lines
        answer_hdr_seq: int | None = None
        explanation_hdr_seq: int | None = None
        for l in lines:
            norm = normalize_text(l.text)
            if answer_hdr_seq is None and is_answer_header(norm):
                answer_hdr_seq = l.seq
            if explanation_hdr_seq is None and is_explanation_header(norm):
                explanation_hdr_seq = l.seq
            if answer_hdr_seq is not None and explanation_hdr_seq is not None:
                break

        regions: list[SourceRegion] = []

        def _refs_between(lo: int, hi: int) -> tuple[str, ...]:
            return tuple(l.line_ref for l in lines if lo <= l.seq < hi)

        # question region: [first_seq, answer_hdr or explanation_hdr or +inf)
        q_end = answer_hdr_seq or explanation_hdr_seq or (lines[-1].seq + 1 if lines else 0)
        q_refs = _refs_between(lines[0].seq if lines else 0, q_end)
        if q_refs:
            regions.append(SourceRegion("question", lines[0].seq if lines else 0, q_end, q_refs))

        # answer region: (answer_hdr, explanation_hdr or +inf)
        if answer_hdr_seq is not None:
            a_end = explanation_hdr_seq or (lines[-1].seq + 1)
            a_refs = _refs_between(answer_hdr_seq + 1, a_end)
            if a_refs:
                regions.append(SourceRegion("answer", answer_hdr_seq + 1, a_end, a_refs))

        # explanation region: (explanation_hdr, +inf)
        if explanation_hdr_seq is not None:
            e_end = lines[-1].seq + 1
            e_refs = _refs_between(explanation_hdr_seq + 1, e_end)
            if e_refs:
                regions.append(SourceRegion("explanation", explanation_hdr_seq + 1, e_end, e_refs))

        return tuple(regions)

    # ------------------------------------------------------------------ 调度
    def _resolve_unit(
        self,
        out: _Out,
        unit_id: str,
        targets,
        mat_lines: set | frozenset = frozenset(),
        mat_starts: list[int] | None = None,
    ) -> None:
        stem_t = next((t for t in targets if t.kind == "question_label"), None)
        qn = stem_t.question_number if stem_t else None
        # Printed number (source-entry form) — used by table decoders when
        # the answer table uses local numbering (e.g. printed=1, global=19).
        self._current_printed = (
            stem_t.question_label_printed if stem_t else None
        )
        start_ref: str | None = None
        region_upper: int | None = None
        if qn:
            start_ref = self._locate_question_start(out, unit_id, stem_t, qn)
        if start_ref:
            region_upper = self._region_end(start_ref)
            # Neighbor-stem: stop at any resolved material body start.
            start_seq = self._idx.seq_of(start_ref)
            for ms in mat_starts or []:
                if ms > start_seq and (region_upper is None or ms < region_upper):
                    region_upper = ms
            # Sibling marker boundary: for marker sub-questions (①②),
            # end at the next sibling marker to avoid consuming sibling content.
            if stem_t and stem_t.question_label_printed:
                printed = stem_t.question_label_printed
                if _has_marker(printed):
                    cur_marker = _MARKER_RE.search(printed)
                    cur_ch = cur_marker.group() if cur_marker else ""
                    sib_seq = _find_sibling_marker_seq(
                        self._idx, start_seq, region_upper, cur_ch
                    )
                    if sib_seq is not None:
                        region_upper = sib_seq
        option_hits = {}
        option_consumed: set[int] = set()
        # Track whether stem location already produced an unresolved
        # (ambiguous/missing) — heuristic stem fallbacks must NOT upgrade
        # it to an approvable stem.
        _stem_id = f"{unit_id}.stem"
        _stem_had_unresolved = any(
            u.reference_id == _stem_id for u in out.unresolved
        )
        self._stem_had_unresolved = _stem_had_unresolved
        if start_ref is None:
            # E2E-010 七选五：父单元无题号，但声明了 options_range（A–G 共享选项）。
            # Also used for option location when stem is unresolved — but the
            # stem itself must NOT be heuristic-upgraded (see _stem_span).
            opt_targets0 = [t for t in targets if t.kind == "option_label" and t.label]
            if opt_targets0 and opt_targets0[0].options_range:
                ostart, _oend = opt_targets0[0].options_range
                try:
                    start_ref = f"P1L{ostart:03d}"
                    self._idx.get(start_ref)
                except KeyError:
                    start_ref = None
        if start_ref:
            opt_targets = [t for t in targets if t.kind == "option_label" and t.label]
            labels = tuple(t.label for t in opt_targets)
            opts_range = opt_targets[0].options_range if opt_targets else None
            option_hits = self._locate_options(out, unit_id, labels, start_ref,
                                               region_upper, opts_range,
                                               consumed_out=option_consumed)
        for t in targets:
            if t.kind == "instruction_marker":
                continue  # already resolved in phase 1
            if t.kind == "question_label":
                self._stem_span(out, unit_id, t, qn, start_ref, option_hits, region_upper,
                                exclude_refs=mat_lines,
                                consumed_seqs=option_consumed)
            elif t.kind == "option_label":
                self._option_span(out, unit_id, t, option_hits)
            else:
                self._span_other(out, unit_id, t)

    def _locate_question_start(self, out, unit_id, t, qn):
        # Three-priority search: full printed label -> numeric prefix -> global qn.
        search_qn = t.question_label_printed or qn
        lines = self._question_zone()
        declared_window = False
        if t.question_search_lines:
            lo, hi = t.question_search_lines
            win_refs = self._evidence_line_refs(lo, hi)
            if win_refs is not None:
                win = frozenset(win_refs)
                lines = [l for l in lines if l.line_ref in win]
                declared_window = True
        # Priority 1: full printed label
        hits = [
            l.line_ref for l in lines
            if _line_has_question_entry(l.text, search_qn)
        ]
        # Priority 2: numeric prefix of printed label (e.g. "14①" -> "14")
        if not hits and t.question_label_printed:
            prefix = _extract_printed_numeric_prefix(t.question_label_printed)
            if prefix and prefix != search_qn:
                hits = [
                    l.line_ref for l in lines
                    if _line_has_question_entry(l.text, prefix)
                ]
                if hits:
                    search_qn = prefix
        # Priority 3: global question_number
        if not hits and search_qn != qn and t.question_search_lines:
            hits = [
                l.line_ref for l in lines
                if _line_has_question_entry(l.text, qn)
            ]
        # Priority 4 (Fix A, E2E-007B): parenthesized top-level entry `(n)`.
        # Bounded on purpose:
        #   - only inside the unit's declared question_search_lines window
        #   - only for the unit's own declared qn (not "any (n)")
        #   - only after digit-form priorities failed
        # Never used by _region_end — sub-question markers must not cut stems.
        if not hits and declared_window:
            for cand in {search_qn, qn}:
                if not cand:
                    continue
                hits = [
                    l.line_ref for l in lines
                    if _line_has_paren_question_entry(l.text, cand)
                ]
                if hits:
                    search_qn = cand
                    break
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            out.add_unresolved(t, "ambiguous", (f"question {qn} start not unique",))
            return None
        out.add_unresolved(t, "missing", (f"question number {qn!r} not found",))
        return None

    def _region_end(self, start_ref: str) -> int | None:
        """题号行后第一个显式区界：下一题号行 或 答案/详解/解析 表头。无 → None。"""
        start_seq = self._idx.seq_of(start_ref)
        for l in self._idx.lines:
            if l.seq <= start_seq:
                continue
            norm = normalize_text(l.text)
            if is_question_start(norm) is not None:
                return l.seq
            if is_answer_header(norm) or is_explanation_header(norm):
                return l.seq
        return None

    def _locate_options(self, out, unit_id, labels, start_ref, region_upper,
                        options_range=None, consumed_out: set | None = None):
        """逐 label 定位：优先行首选项；否则前一个选项行上的 bounded inline（单行多选项）。

        Task A: 多标签同行时返回 **内容区间**（标签后→下一标签前），不再整行吞并。
        返回 {label: ("content", ref, c_start, c_end) | ("ok", ref) |
                     ("inline", ref, start, end) | ("ambiguous",) | ("incomplete",)}。
        重复→ambiguous；完全缺失→incomplete。
        搜索范围不扩大：仍只在已命中的选项行 / cursor 行上切内容。
        """
        found: dict[str, tuple] = {}
        # U44-46: tighten option-search window with declared options_range.
        # Only tightens (min), never expands. options_range=None keeps current behavior.
        if options_range is not None:
            _, hi = options_range
            tightened = hi + 1  # options_range is 1-based inclusive; seq is exclusive upper
            if region_upper is None or tightened < region_upper:
                region_upper = tightened
        cursor_seq = self._idx.seq_of(start_ref)
        cursor_ref: str | None = None
        cursor_end = 0
        # P4: HTML table cell options (Chem Q9/Q19/Q24/Q25). Deterministic
        # cell-to-label mapping takes priority over line-start search. Any label
        # not found in the table is marked incomplete (fail-closed) -- Rule A
        # must NOT fire when a table is present (footer/section misbinding).
        html_hits = self._html_table_options(labels, start_ref, region_upper)
        if html_hits is not None:
            return html_hits
        # E2E-010: options may begin on the start/options-range line itself
        # (七选五 A–G). Include start line in the line-start search window.
        search_from = cursor_seq - 1
        for lab in labels:
            starts = [
                l for l in self._idx.lines
                if l.seq > search_from
                and (region_upper is None or l.seq < region_upper)
                and lab in option_tokens(normalize_text(l.text), (lab,))
            ]
            if len(starts) == 1:
                line = starts[0]
                bounds = _option_content_bounds(line.text, lab, prefer_offset=None, boundary_labels=set(labels))
                # Task A: empty/invalid content (e.g. false-positive declared label
                # `H` in `B. H: O: H` used as boundary) → fallback whole-line OK
                # so we do not turn previously-resolved options into incomplete.
                if bounds is not None and bounds[1] > bounds[0]:
                    found[lab] = ("content", line.line_ref, bounds[0], bounds[1])
                    cursor_seq = line.seq
                    cursor_ref = line.line_ref
                    cursor_end = bounds[1]
                else:
                    found[lab] = ("ok", line.line_ref)
                    cursor_seq = line.seq
                    cursor_ref = line.line_ref
                    cursor_end = 0
                continue
            if len(starts) > 1:
                found[lab] = ("ambiguous",)
                continue
            # 无行首选项：尝试在前一个选项行（同物理行多选项）bounded inline。
            # BIO Q35: stem_lines==options_lines — options sit on the start/stem
            # line itself. When no option line has been hit yet, treat start_ref
            # as the initial cursor line (does not widen search past the window).
            cursor_line_ref = cursor_ref if cursor_ref is not None else start_ref
            if cursor_line_ref is not None:
                line = self._idx.get(cursor_line_ref)
                bounds = _option_content_bounds(line.text, lab, prefer_offset=cursor_end, boundary_labels=set(labels))
                if bounds is not None and bounds[1] > bounds[0] and bounds[0] >= cursor_end:
                    found[lab] = ("content", cursor_line_ref, bounds[0], bounds[1])
                    cursor_end = bounds[1]
                    cursor_ref = cursor_line_ref
                    continue
                offs = [o for o in _label_offsets(line.text, lab) if o >= cursor_end]
                if len(offs) == 1:
                    # content after this label if non-empty, else label-only inline
                    cb = _option_content_bounds(line.text, lab, prefer_offset=offs[0], boundary_labels=set(labels))
                    if cb is not None and cb[1] > cb[0] and cb[0] >= cursor_end:
                        found[lab] = ("content", cursor_line_ref, cb[0], cb[1])
                        cursor_end = cb[1]
                        cursor_ref = cursor_line_ref
                        continue
                    found[lab] = ("inline", cursor_line_ref, offs[0], offs[0] + len(lab))
                    cursor_end = offs[0] + len(lab)
                    cursor_ref = cursor_line_ref
                    continue
            # P1.4-B Rule A: trailing unlabeled option content after last located
            # option (Chem Q23 `D．` dropped). Source-local only: content line
            # inside the option region, no label token, next sequential letter.
            trailing = self._trailing_unlabeled_option_line(
                labels, found, cursor_seq, region_upper
            )
            if trailing is not None:
                found[lab] = ("ok", trailing)
                cursor_seq = self._idx.seq_of(trailing)
                cursor_ref = trailing
                cursor_end = 0
                continue
            found[lab] = ("incomplete",)
        # V3-IMG-OPTION-001: label-only rows (plain `A.` / `<div>B.</div>`)
        # rebind to the following image row as the option body.
        found = self._rebind_image_option_bodies(
            found, labels, region_upper, consumed_out=consumed_out
        )
        # V3-IMG-OPTION-001: image-only option region (PHY Q12) — labels are a
        # caption row near the figures, bodies are `<img>` rows in order.
        # V3-IMG-OPTION-002 (DSH §7.1): only fall back to positional image
        # mapping when EVERY label is still unresolved. A single already-correct
        # text binding must never be wholesale-replaced by image rows.
        if labels and all(
            found.get(lab, ("incomplete",))[0] in ("incomplete", "ambiguous")
            for lab in labels
        ):
            img_hits = self._locate_image_only_options(
                labels, start_ref, region_upper, options_range
            )
            if img_hits is not None:
                return img_hits
        return found

    def _locate_image_only_options(
        self, labels, start_ref, region_upper, options_range=None
    ):
        """Positional image-option mapping (V3-IMG-OPTION-001).

        Fires only when the options region is image rows (`<img`) and a nearby
        caption row exposes the declared labels in order (e.g. `A B C 2/11 D`).
        Image order ↔ label order is source structure, not a guess. Fail-closed
        on any mismatch in counts or label sequence.
        """
        img_re = re.compile(r"<img\b", re.I)
        # a label-caption row: each declared label appears as a bare token
        cursor_seq = self._idx.seq_of(start_ref)
        upper = region_upper
        if options_range is not None:
            _, hi = options_range
            tightened = hi + 1
            if upper is None or tightened < upper:
                upper = tightened
        # collect image rows in the options window
        img_refs: list[str] = []
        window_end = upper if upper is not None else cursor_seq + 30
        for l in self._idx.lines:
            if l.seq <= cursor_seq:
                continue
            if l.seq >= window_end:
                break
            if img_re.search(l.text):
                img_refs.append(l.line_ref)
        if len(img_refs) != len(labels):
            return None
        # look for a caption row carrying ALL declared labels in sequential
        # order — search options window first, then a small trailing band
        # (figure captions sit just under the option figures).
        caption_seq = None
        trailing_end = window_end + 8
        for l in self._idx.lines:
            if l.seq <= cursor_seq:
                continue
            if l.seq >= trailing_end:
                break
            found_order: list[str] = []
            for lab in labels:
                # bare label token (letter only or letter + punctuation)
                if re.search(
                    rf"(?<![A-Za-z0-9]){re.escape(lab)}(?![A-Za-z0-9])",
                    l.text,
                ):
                    if lab not in found_order:
                        found_order.append(lab)
            if found_order == list(labels):
                caption_seq = l.seq
                break
        if caption_seq is None:
            return None
        out: dict[str, tuple] = {}
        for lab, ref in zip(labels, img_refs):
            out[lab] = ("ok", ref)
        return out

    def _rebind_image_option_bodies(self, found, labels, region_upper, consumed_out: set | None = None):
        """Rebind label-only option hits to a following `<img>` body row.

        GEO Q8 shape: `A.` / `<div>B.</div>` then `<div><img …/></div>`.
        Only fires when the label row itself carries no visible body text and
        exactly one image row follows before the next label/prose. Pad rows
        (`---`, blanks) between label and image are skipped. Never invents
        content; count mismatch keeps the original hit.

        E2E-006: consumed label rows and pad rows are recorded into
        `consumed_out` so the stem boundary stops before them — they must
        never be swallowed into the stem after a rebind.
        """
        img_re = re.compile(r"<img\b", re.I)
        tag_re = re.compile(r"<[^>]+>")
        pad_re = re.compile(r"^---\s*$")

        def _visible_body(line_text: str, lab: str) -> str:
            visible = tag_re.sub(" ", line_text).strip()
            return re.sub(
                rf"^\s*{re.escape(lab)}\s*[.．、:，,)）]\s*", "", visible
            ).strip()

        for lab in labels:
            entry = found.get(lab)
            if entry is None or entry[0] not in ("ok", "inline", "content"):
                continue
            line_ref = entry[1]
            line = self._idx.get(line_ref)
            if _visible_body(line.text, lab):
                continue  # real text body — keep as-is
            # scan forward for a single image row before the next label/prose
            img_refs: list[str] = []
            for nxt in self._idx.lines:
                if nxt.seq <= line.seq:
                    continue
                if region_upper is not None and nxt.seq >= region_upper:
                    break
                t = nxt.text.strip()
                if not t or pad_re.match(t):
                    continue  # blank / `---` pad between label and image
                if img_re.search(t):
                    img_refs.append(nxt.line_ref)
                    continue
                break  # next label row or prose stops the search
            if len(img_refs) == 1:
                if consumed_out is not None:
                    consumed_out.add(line.seq)  # original label row
                    for nxt in self._idx.lines:
                        if nxt.seq <= line.seq:
                            continue
                        if nxt.line_ref == img_refs[0]:
                            break
                        t = nxt.text.strip()
                        if not t or pad_re.match(t):
                            consumed_out.add(nxt.seq)  # blank / `---` pad
                found[lab] = ("ok", img_refs[0])
        return found

    def _html_table_options(self, labels, start_ref, region_upper):
        """P4: extract options from an HTML table line in the option region.

        Returns {label: entry} if a table with >=2 option labels is found,
        else None (caller falls through to normal logic).
        Missing labels -> ("incomplete",) so Rule A cannot misbind.
        """
        cursor_seq = self._idx.seq_of(start_ref)
        for l in self._idx.lines:
            if l.seq <= cursor_seq:
                continue
            if region_upper is not None and l.seq >= region_upper:
                break
            cells = _html_table_option_cells(l.text)
            if len(cells) < 2:
                continue
            out: dict[str, tuple] = {}
            for lab in labels:
                if lab in cells:
                    c_start, c_end, clean = cells[lab]
                    out[lab] = ("cell", l.line_ref, c_start, c_end, clean)
                else:
                    out[lab] = ("incomplete",)
            return out
        return None

    def _trailing_unlabeled_option_line(self, labels, found, cursor_seq, region_upper):
        """Rule A: first option-like content line after last located option with no label token.

        Only used for the next sequential missing letter. Never scans outside the
        option region (region_upper / cursor). Never uses answer evidence.
        """
        if not labels:
            return None
        # next expected letter among declared labels not yet found
        missing = [lab for lab in labels if lab not in found or found[lab][0] == "incomplete"]
        if not missing:
            return None
        want = missing[0]
        # sequential: want must be the next letter after the highest found label
        # Task A: "content" hits count as located options for sequential trailing
        found_ok = [lab for lab in labels if lab in found and found[lab][0] in ("ok", "inline", "content")]
        if found_ok:
            nxt = chr(ord(max(found_ok)) + 1)
            if want != nxt:
                return None
        else:
            if want != "A":
                return None
        for l in self._idx.lines:
            if l.seq <= cursor_seq:
                continue
            if region_upper is not None and l.seq >= region_upper:
                break
            text = l.text
            t = text.strip()
            if not t or len(t) < 4:
                continue
            if t.startswith("<") or t.startswith("#") or t.startswith("---"):
                continue
            # P4 hard guard: page footer / section header is never option content
            if _PAGE_FOOTER_RE.search(t) or _SECTION_HDR_RE.match(t):
                continue
            if _LABEL_RE.search(text) or _LABEL_DIGIT_GLUE_RE.search(text):
                continue
            if _LABEL_SPACE_SEP_PROSE.search(text):
                continue
            if _LABEL_SPACE_SEP_RE.search(text):
                continue
            # V3-IMG-OPTION-001: bare multi-label caption rows (`A B C 2/11 D`)
            # are figure labels, never option body content.
            if len(re.findall(r"(?<![A-Za-z0-9])[A-Ha-h](?![A-Za-z0-9])", t)) >= 2:
                continue
            if re.match(r"^\d+\s*[.．、\\]", t):
                continue
            return l.line_ref
        return None

    def _extra_owned_refs(self, t, unit_id: str,
                          exclude_refs: frozenset | set | None = None) -> list[str]:
        """Fix A: return extra_lines refs owned by THIS unit only.

        Filters out any line that falls within ANOTHER unit's declared stem range
        (prevents cross-unit pollution, e.g. PHY Q19 extras swallowing Q21/Q22 stems).
        Also excludes option-pattern lines (e.g. BIO Q8 "D. $O_2$") — those belong
        in options, not stem.
        """
        extra = getattr(t, "extra_lines", None)
        if not extra:
            return []
        exclude = exclude_refs or frozenset()
        e_lo, e_hi = extra
        # Option pattern: "X." at line start OR inside HTML (e.g. <div>D. ...</div>)
        _opt_line_re = re.compile(r"(?:^|>)\s*[A-Ha-h]\s*[.．。:：、]")
        out_refs: list[str] = []
        for l in self._idx.between_incl(e_lo, e_hi):
            seq = l.seq
            # Skip if this line is within another unit's declared stem range
            polluted = False
            for other_uid, (o_lo, o_hi) in getattr(self, "_declared_stem_ranges", {}).items():
                if other_uid == unit_id:
                    continue
                if o_lo <= seq <= o_hi:
                    polluted = True
                    break
            if polluted:
                continue
            # Fix D: option-pattern lines are options, not stem content
            if _opt_line_re.search(l.text):
                continue
            if l.line_ref not in exclude:
                out_refs.append(l.line_ref)
        out_refs.sort(key=lambda r: self._idx.seq_of(r))
        return out_refs

    def _stem_span(self, out, unit_id, t, qn, start_ref, option_hits, region_upper,
                   exclude_refs: frozenset | set | None = None,
                   consumed_seqs: set[int] | None = None):
        if start_ref is None or getattr(self, "_stem_had_unresolved", False):
            # Owner 2026-01 / Q6 safety: when stem location already produced
            # an unresolved (ambiguous/missing), do NOT use heuristic fallbacks
            # (same-line-options / first-option-offset / options_range start).
            # Producer-declared question_search_lines is authoritative.
            qs = getattr(t, "question_search_lines", None)
            if qs:
                refs = self._evidence_line_refs(qs[0], qs[1])
                if refs:
                    # Fix B: also merge owned extra_lines in the fallback path.
                    extra_refs = self._extra_owned_refs(t, unit_id, exclude_refs)
                    merged = list(refs) + [r for r in extra_refs if r not in refs]
                    merged.sort(key=lambda r: self._idx.seq_of(r))
                    out.add_span(
                        unit_id, t, merged, "exact",
                        ("stem start", "declared question_search_lines",
                         f"lines={qs[0]}-{qs[1]}", "extra_merged"),
                    )
                    return
            return  # 已由 _locate_question_start 记录 unresolved
        first_option_seq = None
        for lab, entry in option_hits.items():
            # Task A: content/inline hits also carry a line_ref (entry[1])
            if entry[0] in ("ok", "content", "inline", "cell") and entry[1]:
                seq = self._idx.seq_of(entry[1])
                first_option_seq = seq if first_option_seq is None else min(first_option_seq, seq)
        # E2E-006: option label/pad rows consumed by image-rebind must not be
        # swallowed into the stem — tighten the boundary to the earliest one.
        if consumed_seqs:
            cmin = min(consumed_seqs)
            first_option_seq = cmin if first_option_seq is None else min(first_option_seq, cmin)
        # 显式边界：本 unit 首选项行；否则区界（下一题/表头/material）。
        boundary_seq = first_option_seq if first_option_seq is not None else region_upper
        start_seq = self._idx.seq_of(start_ref)
        # Upper bound (E2E-007B KHH2 Q21-Q28): stem must not cross the next
        # question's DECLARED start (document order + Producer stem_lines).
        # Only tightens. Not "any (n)" text matching — those remain in _region_end.
        for ds in getattr(self, "_declared_starts", ()):
            if ds > start_seq and (boundary_seq is None or ds < boundary_seq):
                boundary_seq = ds
                break
        # WP7-A: tighten to Producer-declared stem end (question_search_lines /
        # stem_lines [start, end]). Only tightens — never expands past the
        # declared stem content range.  between() is exclusive of hi, so use
        # seq(end)+1 to include the declared last stem line.
        qs = getattr(t, "question_search_lines", None)
        if qs and qs[1] is not None:
            hi_refs = self._evidence_line_refs(qs[1], qs[1])
            if hi_refs:
                declared_end_seq = self._idx.seq_of(hi_refs[0]) + 1
                if boundary_seq is None or declared_end_seq < boundary_seq:
                    boundary_seq = declared_end_seq
        if boundary_seq is None:
            out.add_unresolved(
                t, "incomplete",
                ("no explicit end boundary (option/next-question) for stem",),
            )
            return
        # Fourth-cut B: stem must not consume material body lines.
        # P3: when start_ref is a material line (stem and material share a line),
        # use char-span binding from the question entry position to avoid overlap.
        exclude = exclude_refs or frozenset()
        if start_ref in exclude:
            # Find question entry column on start_ref line
            raw = self._idx.get(start_ref).text
            entry_col = _find_question_entry_col(raw, qn)
            if entry_col is not None:
                # Char-span from question entry to end of line (or next option)
                end_col = len(raw)
                out.add_char_span(unit_id, t, start_ref, entry_col, end_col, "exact",
                                  ("stem start", start_ref, "material-shared-line",
                                   f"col={entry_col}", "boundary", "option-or-region-end"))
                return
        refs = [
            l.line_ref for l in self._idx.between(start_seq, boundary_seq)
            if l.line_ref not in exclude or l.line_ref == start_ref
        ]
        # Fix A+B: include ownership-filtered extra_lines as UNION.
        extra_refs = self._extra_owned_refs(t, unit_id, exclude)
        if extra_refs:
            refs.extend(r for r in extra_refs if r not in refs)
            refs.sort(key=lambda r: self._idx.seq_of(r))
        # E2E-006: trim trailing structural pads (`---`, blanks) — never stem
        # content. Only pads are trimmed, not real text like trailing `A.`.
        pad_re = re.compile(r"^---\s*$")
        while len(refs) > 1:
            tail = self._idx.get(refs[-1]).text
            if tail.strip() and not pad_re.match(tail):
                break
            refs.pop()
        if not refs:
            # BIO Q35 (E2E-009R1): stem and A–D options share one source line.
            # between(start, first_option_seq) is empty — bind stem as a char-span
            # from the question entry up to the first option content offset.
            if start_seq == boundary_seq and boundary_seq is not None:
                first_off = None
                for lab, entry in option_hits.items():
                    if entry[0] in ("content", "inline") and len(entry) >= 3:
                        off = entry[2]
                        first_off = off if first_off is None else min(first_off, off)
                raw = self._idx.get(start_ref).text
                entry_col = _find_question_entry_col(raw, qn)
                if entry_col is None:
                    entry_col = 0
                end_col = first_off if first_off is not None else len(raw)
                if end_col > entry_col:
                    out.add_char_span(
                        unit_id, t, start_ref, entry_col, end_col, "exact",
                        ("stem start", start_ref, "same-line-options",
                         f"col={entry_col}", "boundary", "first-option-offset"),
                    )
                    return
            out.add_unresolved(t, "incomplete", ("stem span empty",))
            return
        out.add_span(unit_id, t, refs, "exact",
                     ("stem start", start_ref, "boundary", "option-or-region-end"))

    def _option_span(self, out, unit_id, t, option_hits):
        # R3-D: option with direct evidence_lines (e.g. D in extra_lines) binds
        # without searching — avoids options_range expansion / cross-unit bleed.
        ev = getattr(t, "evidence_lines", None)
        if ev:
            refs = self._evidence_line_refs(ev[0], ev[1])
            if refs:
                out.add_span(unit_id, t, refs, "exact",
                             (f"option label={t.label} (evidence_lines)",
                              f"lines={ev[0]}-{ev[1]}"))
                return
        entry = option_hits.get(t.label or "", ("incomplete",))
        kind = entry[0]
        if kind == "ok":
            out.add_span(unit_id, t, [entry[1]], "exact", (f"option label={t.label}",))
            return
        if kind == "content":
            # Task A: content span = after label → before next label (line_character)
            out.add_char_span(unit_id, t, entry[1], entry[2], entry[3], "exact",
                              (f"option label={t.label} (content span, line_character)",))
            return
        if kind == "inline":
            out.add_char_span(unit_id, t, entry[1], entry[2], entry[3], "exact",
                              (f"option label={t.label} (inline, line_character)",))
            return
        if kind == "cell":
            # P4: HTML table cell -- clean text via cell= evidence (compiler
            # _slice_span prefers cell= over raw offset slicing).
            out.add_char_span(
                unit_id, t, entry[1], entry[2], entry[3], "exact",
                (f"option label={t.label} (html_table_cell)",
                 f"cell={entry[4]}"),
            )
            return
        out.add_unresolved(t, kind if kind in ("ambiguous", "incomplete") else "incomplete",
                           (f"option {t.label}",))

    def _span_other(self, out, unit_id, t):
        if t.kind == "instruction_marker":
            self._material_span(out, unit_id, t)
        elif t.kind == "answer_zone":
            self._answer_span(out, unit_id, t)
        elif t.kind == "explanation_zone":
            self._explanation_span(out, unit_id, t)
        elif t.kind == "image":
            self._image_span(out, unit_id, t)
        elif t.kind == "blank_label":
            self._blank_span(out, unit_id, t)

    def _trim_blank_edge_refs(self, refs: list[str]) -> tuple[list[str], int, int]:
        """Drop leading/trailing pure-blank lines from a material interior.

        Fourth-cut A: marker ±1 padding can place blank lines at the interior
        edges and collide with neighboring units. Substantive content is kept;
        empty result is returned for the caller to treat as unresolved.
        """
        if not refs:
            return [], 0, 0
        lead = 0
        while lead < len(refs):
            line = self._idx.get(refs[lead])
            if line.text and line.text.strip():
                break
            lead += 1
        trail = 0
        while trail < len(refs) - lead:
            line = self._idx.get(refs[len(refs) - 1 - trail])
            if line.text and line.text.strip():
                break
            trail += 1
        end = len(refs) - trail
        if lead >= end:
            return [], lead, trail
        return refs[lead:end], lead, trail

    def _material_span(self, out, unit_id, t):
        sm = t.start_marker or {}
        em = t.end_marker or {}
        # E2E-009R5: Producer-declared material_lines is the authoritative
        # passage range. Marker line alone is a heading/first line — never a
        # substitute for the passage body.
        el = getattr(t, "evidence_lines", None)
        if el is not None:
            refs = self._evidence_line_refs(el[0], el[1])
            if refs is None:
                out.add_unresolved(
                    t, "incomplete",
                    ("material evidence range not fully bound to source lines",
                     f"declared={el[0]}-{el[1]}"),
                )
                return
            q = sm.get("text")
            st, _hits, extra = self._resolve_marker_cascade(q) if q else ("missing", [], ())
            status = st if _is_resolved(st) else "exact"
            out.add_span(
                unit_id, t, refs, status,
                ("material evidence range", f"lines={el[0]}-{el[1]}",
                 f"marker={q!r}", *extra),
            )
            return
        granularity = sm.get("granularity")
        if granularity == "multi_line_pair":
            sq, eq = sm.get("text"), em.get("text")
            if not sq or not eq:
                out.add_unresolved(t, "incomplete",
                                   ("material pair requires start+end marker text",))
                return
            st, s_refs, s_extra = self._resolve_marker_cascade(sq)
            et, e_refs, e_extra = self._resolve_marker_cascade(eq)
            if not _is_resolved(st):
                self._unresolved_marker(out, t, st, "start", sq)
                return
            if not _is_resolved(et):
                self._unresolved_marker(out, t, et, "end", eq)
                return
            s_seq = self._idx.seq_of(s_refs[0])
            e_seq = self._idx.seq_of(e_refs[0])
            if e_seq <= s_seq + 1:
                out.add_unresolved(t, "incomplete",
                                   ("material interior empty (markers adjacent)",))
                return
            # material 正文 = start/end marker **之间**（排他，instruction 行不进材料）。
            raw_refs = [l.line_ref for l in self._idx.between(s_seq + 1, e_seq)]
            # Fourth-cut A: trim leading/trailing pure-blank padding lines.
            refs, lead_n, trail_n = self._trim_blank_edge_refs(raw_refs)
            if not refs:
                out.add_unresolved(t, "incomplete",
                                   ("material interior empty after blank trim",))
                return
            status = "exact" if st == "exact" and et == "exact" else \
                ("contextual" if "contextual" in (st, et) else "normalized")
            out.add_span(unit_id, t, refs, status,
                         ("material between markers", sq, "…", eq,
                          f"trim_blanks lead={lead_n} trail={trail_n}",
                          *s_extra, *e_extra))
            return
        q = sm.get("text")
        if not q:
            out.add_unresolved(t, "incomplete", ("material marker text missing",))
            return
        status, hits, extra = self._resolve_marker_cascade(q)
        if not _is_resolved(status):
            self._unresolved_marker(out, t, status, "marker", q)
            return
        if granularity == "line_fragment":
            out.add_fragment_span(unit_id, t, hits[0], q, status,
                                  ("material fragment", q, *extra))
            return
        out.add_span(unit_id, t, [hits[0]], status, ("material marker", q, *extra))

    def _unresolved_marker(self, out, t, status, label, query):
        out.add_unresolved(t, status, (f"{label} {query!r} not uniquely located",))

    def _resolve_marker_cascade(self, query: str):
        """marker 文本定位 + contextual 收窄（20 §5.4）。

        contextual 仅允许用确定性 source 边界排除候选（此处=题目区/答案详解区显式表头
        边界），**不得**用文本相似度 / nearest / first-match。机器不变量：
        contextual ⇒ initial>1 ⇒ final==1。
        返回 (status, refs, extra_evidence)。
        """
        status, refs = _locate(query, self._idx)
        if status == "ambiguous":
            in_zone = [r for r in refs if self._idx.seq_of(r) < self._qzone_end]
            if len(in_zone) == 1 and len(refs) > 1:
                extra = tuple(
                    f"excluded {r} (outside question zone)" for r in refs if r not in in_zone
                )
                return "contextual", in_zone, extra
        return status, refs, ()

    def _evidence_line_refs(self, start_no: int, end_no: int) -> list[str] | None:
        """Producer inclusive 1-based line numbers → line_refs.

        Preprocessing convention (source_loader): single-page markdown with
        line_ref = P1L{line_no:03d}. Missing any declared line → None
        (no guessing / no partial range).
        """
        refs: list[str] = []
        for n in range(start_no, end_no + 1):
            ref = f"P1L{n:03d}"
            try:
                self._idx.get(ref)
            except KeyError:
                return None
            refs.append(ref)
        return refs

    def _answer_span(self, out, unit_id, t):
        qn = t.question_number
        if not qn:
            out.add_unresolved(t, "incomplete", ("answer needs question_label",))
            return

        # P0-answer: when answer_lines is None but manifest declared
        # answer_evidence.value, bind it as VALUE-ONLY. NEVER scan explanation
        # or answer-zone text to infer the answer. NEVER fabricate line_refs
        # (P0-R3: fake P1L001 provenance must not look byte-proven).
        el = getattr(t, "evidence_lines", None)
        av = getattr(t, "answer_value", None)
        # answer_value is ALWAYS the answer for THIS target. For a single
        # composite question (e.g. Chinese Q1 with question_numbers=[1]),
        # the value is the FULL multi-part answer block — never truncate it
        # to one sub-answer. Per-q extraction is only for multi-q composite
        # sub-question targets where the caller explicitly needs it.
        if el is None and av is not None:
            out.add_value_only_answer(
                t, av,
                ("answer_value_only", "no declared answer_lines", f"cell={av}"),
            )
            return

        # B3c-A evidence transport: declared Producer answer_lines is the
        # authoritative answer-evidence range. Do not re-scan the whole
        # answer_zone to guess which line holds the answer (defects A/C).
        if el is not None:
            def _conflict_with_declared_value(extracted: str) -> bool:
                """P0-R3: answer_value vs extractable answer_lines content must agree."""
                if av is None:
                    return False
                return _clean_answer_for_conflict(extracted) != _clean_answer_for_conflict(av)

            refs = self._evidence_line_refs(el[0], el[1])
            if refs is None:
                out.add_unresolved(
                    t, "incomplete",
                    ("answer evidence range not fully bound to source lines",
                     f"declared={el[0]}-{el[1]}"),
                )
                return

            # P0-R5d: shared ranges must NOT bypass ownership for a single
            # entry, including a multi-line shared range whose only entry is
            # `1. A` (plus blank/continuation). Multi-entry blocks/tables keep
            # their existing shared-range handling below.
            if el in self._shared_answer_ranges:
                _shared_all = "\n".join(self._idx.get(r).text for r in refs)
                _shared_entries = list(_ENTRY_RE.finditer(_shared_all))
                if (
                    len(_shared_entries) == 1
                    and _shared_entries[0].group(1) != str(qn)
                ):
                    out.add_empty_answer(t, (
                        "answer source line belongs to a different question",
                        f"qn={qn}",
                        f"evidence_lines={el[0]}-{el[1]}",
                        f"evidence_text={_shared_all.strip()[:80]}",
                        "ownership=foreign_question (shared single-entry)",
                    ))
                    return

            # P0-R5 ownership PRE-GUARD (number relationship, not token shape):
            # runs BEFORE scored/table/packed/full-line extractors. Any line
            # whose entry numbering identifies ANOTHER question must never
            # reach an extractor, and must NEVER leak the foreign full text
            # into this question's answer field.
            if el not in self._shared_answer_ranges:
                _raw_texts = [self._idx.get(r).text for r in refs]
                # P0-R5b: local_index only with positive evidence
                # (multi-part local body OR multi-unit local label sequence).
                _local_ok = False
                if unit_id in self._local_body_units or unit_id in self._local_seq_units:
                    _local_ok = True
                else:
                    # P0-R5b: a multi-line declared range is local evidence ONLY
                    # when the first entry is the local label `1.` and either
                    # (i) it is a bare `1.` + continuation body, or
                    # (ii) the combined block is a multi-part local body.
                    # A foreign `5. A` + blank line is NOT local.
                    if len(refs) > 1:
                        _first = _raw_texts[0]
                        _m0 = next(_ENTRY_RE.finditer(_first), None)
                        if _m0 is not None and _m0.group(1) == "1":
                            _block = "\n".join(_raw_texts)
                            if _is_local_body_content(_block) or _is_local_prose_body(
                                _block
                            ):
                                _local_ok = True
                    for _raw in _raw_texts:
                        for _m in _ENTRY_RE.finditer(_raw):
                            _cs, _ce = _entry_content_bounds(
                                _raw, _m.start(), len(_raw)
                            )
                            if _is_local_body_content(_raw[_cs:_ce].strip()):
                                _local_ok = True
                                break
                self._last_local_ok = _local_ok
                _own = _entry_ownership(
                    _raw_texts, qn, allow_local_index=_local_ok
                )
                if _own == "foreign_question":
                    _first = _raw_texts[0].strip()[:80] if _raw_texts else ""
                    if av is not None:
                        out.add_empty_answer(t, (
                            "answer_lines/answer_value conflict: source line "
                            "belongs to a different question",
                            f"qn={qn}",
                            f"declared_answer_value={av}",
                            f"evidence_lines={el[0]}-{el[1]}",
                            f"evidence_text={_first}",
                            "ownership=foreign_question",
                        ))
                    else:
                        out.add_empty_answer(t, (
                            "answer source line belongs to a different question",
                            f"qn={qn}",
                            f"evidence_lines={el[0]}-{el[1]}",
                            f"evidence_text={_first}",
                            "ownership=foreign_question",
                        ))
                    return
                # P0-R5 role check: explanation body is not an answer even when
                # the entry number matches. Do not materialize it as answer.
                # Only inspect the ENTRY CONTENT (after `N.`) — multi-line
                # blocks whose continuation lines are explanation sections
                # (B3c-A bare `1.` + body) must stay intact.
                _EXPL_BODY_PREFIXES = (
                    "【分析】", "【解答】", "【解析】", "【详解】", "【点评】",
                    "【考点】", "【知识点】",
                )
                for _raw in _raw_texts:
                    for _m in _ENTRY_RE.finditer(_raw):
                        _cs, _ce = _entry_content_bounds(
                            _raw, _m.start(), len(_raw)
                        )
                        _content = _raw[_cs:_ce].strip()
                        if _content and any(
                            _content.startswith(p) for p in _EXPL_BODY_PREFIXES
                        ):
                            out.add_empty_answer(t, (
                                "answer evidence is explanation body, not an answer",
                                f"qn={qn}",
                                f"evidence_lines={el[0]}-{el[1]}",
                                f"evidence_text={_raw.strip()[:60]}",
                                "role=explanation_body",
                            ))
                            return

            if len(refs) > 1:
                # Multi-line evidence block: try vertical-format table parsing
                # with cross-line continuation (P2-R). If found, bind the
                # specific answer cell range. Otherwise fall through.
                combined_parts: list[str] = []
                first_ref = None
                for _lr in refs:
                    _raw = self._idx.get(_lr).text
                    _dv = decode_answer_table_vertical(_raw, qn)
                    _dv_printed = False
                    if _dv is None and self._current_printed and self._current_printed != qn:
                        _dv = decode_answer_table_vertical(_raw, self._current_printed)
                        _dv_printed = _dv is not None
                    if _dv is not None:
                        _ds, _de, _dt = _dv
                        if first_ref is None:
                            first_ref = _lr
                        combined_parts.append(_dt)
                        # Check for continuation on subsequent lines
                        for _next_lr in refs[refs.index(_lr) + 1:]:
                            _next_raw = self._idx.get(_next_lr).text
                            _cont = _decode_answer_table_continuation(_next_raw)
                            if _cont is not None:
                                combined_parts.append(_cont)
                            # Don't break — skip non-continuation lines
                            # (empty lines, separators) and keep looking
                        break
                    # Check if this line starts with a continuation row
                    _cont = _decode_answer_table_continuation(_raw)
                    if _cont is not None and combined_parts:
                        combined_parts.append(_cont)
                if combined_parts and first_ref is not None:
                    full_text = "\n".join(combined_parts)
                    _ev = [
                        "answer evidence range",
                        f"lines={el[0]}-{el[1]}",
                        "structured_answer_table_vertical", f"qn={qn}",
                        f"cell={full_text}",
                        "ownership=match",
                        "binding_evidence=table_vertical_qn_column",
                    ]
                    if _dv_printed:
                        _ev.append(f"matched_by=printed({qn}->{self._current_printed})")
                    out.add_char_span(
                        unit_id, t, first_ref, 0, len(full_text), "exact", tuple(_ev),
                    )
                    return
                # Try horizontal table format (选项/答案 rows) for multi-line
                # evidence (e.g. answer table at L431 with continuation at L433).
                for _lr in refs:
                    _raw = self._idx.get(_lr).text
                    _dch = decode_answer_table_cell(_raw, qn)
                    _dch_printed = False
                    if _dch is None and self._current_printed and self._current_printed != qn:
                        _dch = decode_answer_table_cell(_raw, self._current_printed)
                        _dch_printed = _dch is not None
                    if _dch is not None:
                        _ds, _de, _dt = _dch
                        _ev = [
                            "answer evidence range",
                            f"lines={el[0]}-{el[1]}",
                            "structured_answer_table", f"qn={qn}",
                            f"cell={_dt}",
                            "ownership=match",
                            "binding_evidence=table_qn_answer_column",
                        ]
                        if _dch_printed:
                            _ev.append(f"matched_by=printed({qn}->{self._current_printed})")
                        out.add_char_span(
                            unit_id, t, _lr, _ds, _de, "exact", tuple(_ev),
                        )
                        return
                # E2E-009R1: header-less horizontal qn/answer rows (EN Shape B).
                for _lr in refs:
                    _raw = self._idx.get(_lr).text
                    _dhh = decode_answer_table_headerless_horizontal(_raw, qn)
                    if _dhh is not None:
                        _ds, _de, _dt = _dhh
                        out.add_char_span(
                            unit_id, t, _lr, _ds, _de, "exact",
                            ("answer evidence range",
                             f"lines={el[0]}-{el[1]}",
                             "structured_answer_table_headerless", f"qn={qn}",
                             f"cell={_dt}",
                             "ownership=match",
                             "binding_evidence=table_headerless_qn_column"),
                        )
                        return
                # No structured table match: try scored answer extraction
                # (e.g. "17. (BC) 3分; (B) 2分; (C) 2分" -> "BC").
                for _lr in refs:
                    _raw = self._idx.get(_lr).text
                    _dsa = _decode_scored_answer(_raw, qn)
                    if _dsa is not None:
                        _ds, _de, _dt = _dsa
                        out.add_char_span(
                            unit_id, t, _lr, _ds, _de, "exact",
                            ("answer evidence range",
                             f"lines={el[0]}-{el[1]}",
                             "scored_answer", f"qn={qn}",
                             f"cell={_dt}"),
                        )
                        return
                # E2E-010R1: 区间式答案键 `19-23 DABCA 24-28 BDCDA` 逐题取字母
                for _lr in refs:
                    _raw = self._idx.get(_lr).text
                    _rk = decode_range_answer_key(_raw, qn)
                    if _rk is not None:
                        _ds, _de, _dt = _rk
                        out.add_char_span(
                            unit_id, t, _lr, _ds, _de, "exact",
                            ("answer evidence range",
                             f"lines={el[0]}-{el[1]}",
                             "range_answer_key", f"qn={qn}",
                             f"cell={_dt}"),
                        )
                        return
                # E2E-009R2: packed per-qn entries on any evidence line
                # (`1.C 2.B 3.C 4.D` / `5.(1). …`). Without this, every child
                # of a Chinese composite received the identical whole-block
                # answer text + hash (U1-5).
                # R9-fix: when the evidence range spans MULTIPLE entry-bearing
                # lines (Chinese composite `（1）A / （2）B / …`), single-entry
                # lines are sub-answers — fall through to full-range block
                # binding. When only ONE line carries an entry (e.g. `【答案】`
                # + `1. A`), that line IS the answer — packed-extract the token.
                # Exception: shared multi-qn ranges (`1. A` + `2. B` for Q1/Q2)
                # always take the packed path per-q.
                _entry_line_count = sum(
                    1 for _lr_c in refs
                    if any(int(m.group(1)) >= 1 for m in _ENTRY_RE.finditer(self._idx.get(_lr_c).text))
                )
                _is_shared_multi_qn = el in self._shared_answer_ranges
                for _lr in refs:
                    _raw = self._idx.get(_lr).text
                    _offs = _entry_offsets(_raw, qn)
                    if len(_offs) == 1:
                        all_off = [
                            m.start() for m in _ENTRY_RE.finditer(_raw)
                            if int(m.group(1)) >= 1
                        ]
                        if (
                            len(all_off) <= 1
                            and _entry_line_count > 1
                            and not _is_shared_multi_qn
                        ):
                            continue
                        # R9-fix: single-entry lines with long prose bodies
                        # (`（28）简析：…`) fall through to block binding.
                        if len(all_off) <= 1 and not _is_shared_multi_qn:
                            _nxt_chk = next(
                                (o for o in all_off if o > _offs[0]), len(_raw)
                            )
                            _cs_chk, _ce_chk = _entry_content_bounds(
                                _raw, _offs[0], _nxt_chk
                            )
                            if _ce_chk - _cs_chk > 8:
                                continue
                        nxt = next((o for o in all_off if o > _offs[0]), len(_raw))
                        # Strip `N.` / `N\\.` prefix: bind only answer content.
                        _cs, _ce = _entry_content_bounds(_raw, _offs[0], nxt)
                        # Only packed entries with a real value (`1.C` / `10. A`).
                        # Bare `1.` + multi-line body stays on the block path
                        # (B3c-A full-range binding).
                        if _cs < _ce:
                            out.add_char_span(
                                unit_id, t, _lr, _cs, _ce, "exact",
                                ("answer evidence range",
                                 f"lines={el[0]}-{el[1]}",
                                 f"qn={qn}", "multi-line entry"),
                            )
                            return
                # Answer-binding safety (E2E-014, narrowed): only clear when
                # the evidence range is SHARED by ≥2 units AND carries local
                # numbering that does not include this unit's question number.
                # Per-unit ranges are that unit's own answer (possibly labeled
                # with a local number) and must NOT be cleared.
                if el in self._shared_answer_ranges:
                    _combined = "\n".join(self._idx.get(r).text for r in refs)
                    _block_nums = _block_entry_nums(_combined)
                    if _block_nums and qn not in _block_nums:
                        _er = _block_entry_range(_combined)
                        _qn_int = None
                        try:
                            _qn_int = int(qn)
                        except (TypeError, ValueError):
                            pass
                        # Only clear when qn is outside the block's numbering
                        # range (different numbering system). If qn falls
                        # within [min, max] the entry exists but may be
                        # OCR-malformed (e.g. `68 but`) — keep the block.
                        if _qn_int is not None and _er and _er[0] <= _qn_int <= _er[1]:
                            pass  # same numbering range — do not clear
                        else:
                            out.add_empty_answer(t, (
                                "answer block local numbering not mappable to this unit",
                                f"qn={qn}",
                                f"block_entries={sorted(_block_nums, key=int)}",
                                f"shared_lines={el[0]}-{el[1]}",
                            ))
                            return
                # P0-R3 ownership: a declared per-unit evidence block whose
                # entry numbering names a DIFFERENT question AND whose content
                # is a bare choice token (`12. A`) is a FOREIGN binding.
                # Do not claim it, and do not silently substitute answer_value.
                # Multi-part local-numbered bodies (`1.（3分）…`) stay allowed.
                _combined_all = "\n".join(self._idx.get(r).text for r in refs)
                _own = _entry_ownership(
                    [_combined_all], qn,
                    allow_local_index=getattr(self, "_last_local_ok", False),
                )
                if _own == "foreign_question" and el not in self._shared_answer_ranges:
                    if av is not None:
                        out.add_empty_answer(t, (
                            "answer_lines/answer_value conflict: evidence entry "
                            "numbering does not match target question",
                            f"qn={qn}",
                            f"declared_answer_value={av}",
                            f"evidence_lines={el[0]}-{el[1]}",
                            f"evidence_entries={sorted(_block_entry_nums(_combined_all), key=lambda x: int(x) if x.isdigit() else 0)}",
                        ))
                    else:
                        out.add_empty_answer(t, (
                            "answer evidence entry numbering does not match target question",
                            f"qn={qn}",
                            f"evidence_lines={el[0]}-{el[1]}",
                            f"evidence_entries={sorted(_block_entry_nums(_combined_all), key=lambda x: int(x) if x.isdigit() else 0)}",
                        ))
                    return
                # Still no match: bind as multi-line block (no local numbering,
                # or bare `qn.` multi-line body — B3c-A full-range).
                # P0-R3 conflict: declared answer_value must not be silently
                # overridden by a different block text.
                if av is not None:
                    _blk = "\n".join(self._idx.get(r).text for r in refs).strip()
                    if _blk:
                        # Compare SAME semantic scope: full block vs full block.
                        # Normalize whitespace/labels, never truncate to per-q.
                        # Chinese composite Q1: answer_value IS the full
                        # 7-item block; block text is the same content with
                        # newlines + "答案:" header. After normalization they
                        # must agree. A genuine content mismatch (e.g. block
                        # says （1）B but value says （1）A) is a real conflict.
                        _blk_norm = _normalize_answer_block(_blk)
                        _av_norm = _normalize_answer_block(av)
                        # R9-fix: block often has MORE content than value
                        # (headers, explanation, annotations). Check content
                        # presence: either direction of containment, or
                        # significant overlap (value is paraphrase of block).
                        _content_ok = (
                            _av_norm in _blk_norm
                            or _blk_norm in _av_norm
                            or _answer_content_overlap(_av_norm, _blk_norm)
                        )
                        if not _content_ok:
                            out.add_empty_answer(t, (
                                "answer_lines/answer_value conflict: block text != declared value",
                                f"qn={qn}",
                                f"declared_answer_value={av[:80]}",
                                f"block_text_len={len(_blk)}",
                            ))
                            return
                out.add_span(
                    unit_id, t, refs, "exact",
                    ("answer evidence range",
                     f"lines={el[0]}-{el[1]}",
                     "multi-line block (no token extraction)"),
                )
                return
            # Single-line evidence: try scored answer first (e.g. "17. (BC) 3分"),
            # then AnswerTokenContract char-slice path (qn-entry within the line).
            line_ref = refs[0]
            raw = self._idx.get(line_ref).text
            dsa = _decode_scored_answer(raw, qn)
            if dsa is not None:
                d_start, d_end, d_val = dsa
                if _conflict_with_declared_value(d_val):
                    out.add_empty_answer(t, (
                        "answer_lines/answer_value conflict: scored cell != declared value",
                        f"qn={qn}", f"declared_answer_value={av}", f"cell={d_val}",
                    ))
                    return
                out.add_char_span(
                    unit_id, t, line_ref, d_start, d_end, "exact",
                    ("answer evidence range", f"lines={el[0]}-{el[1]}",
                     "scored_answer", f"qn={qn}", f"cell={d_val}"),
                )
                return
            # E2E-010R1: 区间式答案键
            _rk = decode_range_answer_key(raw, qn)
            if _rk is not None:
                _ds, _de, _dt = _rk
                if _conflict_with_declared_value(_dt):
                    out.add_empty_answer(t, (
                        "answer_lines/answer_value conflict: range-key cell != declared value",
                        f"qn={qn}", f"declared_answer_value={av}", f"cell={_dt}",
                    ))
                    return
                out.add_char_span(
                    unit_id, t, line_ref, _ds, _de, "exact",
                    ("answer evidence range", f"lines={el[0]}-{el[1]}",
                     "range_answer_key", f"qn={qn}", f"cell={_dt}"),
                )
                return
            offs = _entry_offsets(raw, qn)
            if offs:
                all_off = [m.start() for m in _ENTRY_RE.finditer(raw)]
                nxt = next((o for o in all_off if o > offs[0]), len(raw))
                # Strip `N.` / `N\\.` prefix: bind only answer content.
                _cs, _ce = _entry_content_bounds(raw, offs[0], nxt)
                if _cs < _ce:
                    if _conflict_with_declared_value(raw[_cs:_ce]):
                        out.add_empty_answer(t, (
                            "answer_lines/answer_value conflict: entry content != declared value",
                            f"qn={qn}", f"declared_answer_value={av}",
                            f"entry_content={raw[_cs:_ce].strip()[:80]}",
                        ))
                        return
                    out.add_char_span(
                        unit_id, t, line_ref, _cs, _ce, "exact",
                        ("answer evidence range", f"lines={el[0]}-{el[1]}",
                         f"qn={qn}", "single-line entry"),
                    )
                    return
            # No qn token on the declared line: try B3c-B structured table
            # consumption (self-describing 题号/答案 rows). Deterministic
            # same-column lookup only — any failure falls through, no guessing.
            decoded = decode_answer_table_cell(raw, qn)
            _used_printed_cell = False
            if decoded is None and self._current_printed and self._current_printed != qn:
                decoded = decode_answer_table_cell(raw, self._current_printed)
                _used_printed_cell = decoded is not None
            if decoded is not None:
                d_start, d_end, d_val = decoded
                if _conflict_with_declared_value(d_val):
                    out.add_empty_answer(t, (
                        "answer_lines/answer_value conflict: table cell != declared value",
                        f"qn={qn}", f"declared_answer_value={av}", f"cell={d_val}",
                    ))
                    return
                _ev = [
                    "answer evidence range", f"lines={el[0]}-{el[1]}",
                    "structured_answer_table", f"qn={qn}",
                    f"cell={d_val}",
                    "ownership=match",
                    "binding_evidence=table_qn_answer_column",
                ]
                if _used_printed_cell:
                    _ev.append(f"matched_by=printed({qn}->{self._current_printed})")
                out.add_char_span(
                    unit_id, t, line_ref, d_start, d_end, "exact", tuple(_ev),
                )
                return
            # E2E-009R1: EN 2018 Shape B — header-less horizontal qn/answer rows.
            # Must run BEFORE vertical: vertical's header-less continuation path
            # mis-reads this shape (Q26 got '27\\nB' instead of 'C').
            decoded_h = decode_answer_table_headerless_horizontal(raw, qn)
            if decoded_h is not None:
                d_start, d_end, d_val = decoded_h
                out.add_char_span(
                    unit_id, t, line_ref, d_start, d_end, "exact",
                    ("answer evidence range", f"lines={el[0]}-{el[1]}",
                     "structured_answer_table_headerless", f"qn={qn}",
                     f"cell={d_val}",
                     "ownership=match",
                     "binding_evidence=table_headerless_qn_column"),
                )
                return
            # P2: vertical-format table (题号|答案 column headers, one row
            # per question). Deterministic — no guessing.
            decoded_v = decode_answer_table_vertical(raw, qn)
            _used_printed = False
            if decoded_v is None and self._current_printed and self._current_printed != qn:
                decoded_v = decode_answer_table_vertical(raw, self._current_printed)
                _used_printed = decoded_v is not None
            if decoded_v is not None:
                d_start, d_end, d_val = decoded_v
                _ev = [
                    "answer evidence range", f"lines={el[0]}-{el[1]}",
                    "structured_answer_table_vertical", f"qn={qn}",
                    f"cell={d_val}",
                    "ownership=match",
                    "binding_evidence=table_vertical_qn_column",
                ]
                if _used_printed:
                    _ev.append(f"matched_by=printed({qn}->{self._current_printed})")
                out.add_char_span(
                    unit_id, t, line_ref, d_start, d_end, "exact", tuple(_ev),
                )
                return
            # No qn token on the declared line: the declared line itself is
            # the evidence (e.g. bare answer cell). Bind the full line —
            # unless it is a SHARED range with local numbering that does not
            # map to this unit.
            if el in self._shared_answer_ranges:
                _line_nums = _block_entry_nums(raw)
                if _line_nums and qn not in _line_nums:
                    _er = _block_entry_range(raw)
                    _qn_int = None
                    try:
                        _qn_int = int(qn)
                    except (TypeError, ValueError):
                        pass
                    if _qn_int is not None and _er and _er[0] <= _qn_int <= _er[1]:
                        pass  # same numbering range — do not clear
                    else:
                        out.add_empty_answer(t, (
                            "answer line local numbering not mappable to this unit",
                            f"qn={qn}",
                            f"line_entries={sorted(_line_nums, key=int)}",
                            f"shared_lines={el[0]}-{el[1]}",
                        ))
                        return
            # P0-R3 ownership: a declared line whose entry numbering names a
            # DIFFERENT question and whose content is a bare choice token
            # (e.g. `12. A` bound to Q1) is a foreign binding.
            # Local-numbered multi-part bodies stay allowed (per-unit ranges).
            _own = _entry_ownership(
                [raw], qn,
                allow_local_index=getattr(self, "_last_local_ok", False),
            )
            if _own == "foreign_question" and el not in self._shared_answer_ranges:
                if av is not None:
                    out.add_empty_answer(t, (
                        "answer_lines/answer_value conflict: evidence entry "
                        "numbering does not match target question",
                        f"qn={qn}",
                        f"declared_answer_value={av}",
                        f"evidence_lines={el[0]}-{el[1]}",
                        f"evidence_text={raw.strip()[:80]}",
                    ))
                else:
                    out.add_empty_answer(t, (
                        "answer evidence entry numbering does not match target question",
                        f"qn={qn}",
                        f"evidence_lines={el[0]}-{el[1]}",
                        f"evidence_text={raw.strip()[:80]}",
                    ))
                return
            # P0-R3 conflict: bare cell + declared answer_value must agree.
            if _own == "bare" and av is not None:
                _cell = raw.strip()
                if _cell and _cell != av.strip():
                    # allow cell to be a labeled form of av (e.g. "（A）" vs "A")
                    _cell_clean = _clean_answer_for_conflict(_cell)
                    _av_clean = _clean_answer_for_conflict(av)
                    if _cell_clean != _av_clean:
                        out.add_empty_answer(t, (
                            "answer_lines/answer_value conflict: cell text != declared value",
                            f"qn={qn}",
                            f"declared_answer_value={av}",
                            f"evidence_text={_cell[:80]}",
                        ))
                        return
            # P0-R16 F7: try compact answer key (e.g. FGDAE) before
            # falling through to single-line full. Only for multi-qn
            # shared ranges — single-letter answers (e.g. "A") are not
            # compact keys.
            _qn_list = None
            if el and el in self._shared_answer_ranges:
                _raw_qns = self._shared_answer_ranges[el]
                _qn_list = []
                for _q in _raw_qns:
                    try:
                        _qn_list.append(int(_q))
                    except (TypeError, ValueError):
                        pass
                if not _qn_list or len(_qn_list) < 2:
                    _qn_list = None
            if _qn_list is not None:
                _ck = decode_compact_answer_key(raw, qn, _qn_list)
                if _ck is not None:
                    _ck_start, _ck_end, _ck_val = _ck
                    out.add_char_span(
                        unit_id, t, line_ref, _ck_start, _ck_end, "exact",
                        ("answer evidence range", f"lines={el[0]}-{el[1]}",
                         "compact_answer_key", f"qn={qn}",
                         f"qns={','.join(str(x) for x in _qn_list)}",
                         f"cell={_ck_val}"),
                    )
                    return
            # Extract declared answer token from the raw line when av is
            # present (e.g. `故选：A.` → cell `A`). Binds the token as a
            # char_span so the answer text is `A`, not the whole line.
            if av is not None:
                _av_s = av.strip()
                if _av_s and _av_s in raw:
                    _tok_off = raw.find(_av_s)
                    if _tok_off >= 0:
                        out.add_char_span(
                            unit_id, t, line_ref, _tok_off,
                            _tok_off + len(_av_s), "exact",
                            ("answer evidence range",
                             f"lines={el[0]}-{el[1]}",
                             "answer_token_extracted",
                             f"qn={qn}", f"cell={_av_s}"),
                        )
                        return
            out.add_span(
                unit_id, t, [line_ref], "exact",
                ("answer evidence range", f"lines={el[0]}-{el[1]}",
                 "single-line full (no qn entry)"),
            )
            return

        # E2E-013 data-safety: when manifest declared answer_evidence.type=absent
        # AND a validation issue exists, the answer-zone fallback must not
        # force-bind unrelated answer-section text. Bind an empty (absent)
        # answer span so the unit stays IR-ready without fabricating answers.
        if getattr(t, "answer_fallback_blocked", False):
            out.add_empty_answer(t, (
                "answer absent: fallback blocked (absent + validation issue)",
            ))
            return

        # P0-answer: when answer_lines is None AND answer_value is None,
        # fall back to answer-zone scan BUT reject explanation-looking text.
        # Never infer answer from 【分析】/【解答】/【解析】 content.
        if el is None:
            if getattr(t, "answer_fallback_blocked", False):
                out.add_empty_answer(t, (
                    "answer absent: fallback blocked (absent + validation issue)",
                ))
                return
            # Fallback: scan answer zone for qn-bounded entry.
            # P0-answer: reject entries that look like explanation text.
            _EXPL_PREFIXES = ("【分析】", "【解答】", "【解析】", "【详解】", "【点评】")
            entries: list[tuple[str, int, int]] = []
            in_zone = False
            for l in self._idx.lines:
                norm = normalize_text(l.text)
                if not in_zone:
                    if is_answer_header(norm):
                        in_zone = True
                    continue
                if is_explanation_header(norm):
                    break
                offs = _entry_offsets(l.text, qn)
                if offs:
                    all_off = [m.start() for m in _ENTRY_RE.finditer(l.text)]
                    nxt = next((o for o in all_off if o > offs[0]), len(l.text))
                    _cs, _ce = _entry_content_bounds(l.text, offs[0], nxt)
                    if _cs < _ce:
                        _candidate = l.text[_cs:_ce].strip()
                        # P0-answer: reject explanation-looking text
                        if any(_candidate.startswith(p) for p in _EXPL_PREFIXES):
                            continue
                        entries.append((l.line_ref, _cs, _ce))
            if not entries:
                out.add_unresolved(t, "missing", (
                    f"answer row qn={qn} not found in answer zone",
                    "or entry was explanation text (rejected)",
                ))
                return
            distinct_lines = {e[0] for e in entries}
            if len(distinct_lines) > 1:
                out.add_unresolved(t, "ambiguous",
                                   (f"answer row qn={qn} spans multiple lines",))
                return
            line_ref, start, end = entries[0]
            out.add_char_span(unit_id, t, line_ref, start, end, "exact",
                              ("answer zone fallback", t.zone or "", f"qn={qn}"))
            return

    def _explanation_span(self, out, unit_id, t):
        qn = t.question_number

        # Existing Producer mechanism (not a heuristic): ManifestUnit.explanation_lines
        # is the declared explanation-evidence range — same transport as B3c-A
        # answer_lines. Bind the full declared range; do not invent token lines.
        el = getattr(t, "evidence_lines", None)
        if el is not None:
            refs = self._evidence_line_refs(el[0], el[1])
            if refs is None:
                out.add_unresolved(
                    t, "incomplete",
                    ("explanation evidence range not fully bound to source lines",
                     f"declared={el[0]}-{el[1]}"),
                )
                return
            out.add_span(
                unit_id, t, refs, "exact",
                ("explanation evidence range", f"lines={el[0]}-{el[1]}"),
            )
            return

        # Fallback (no declared range): header scan. A second H-3 header is the
        # existing region boundary (see the break below); the first header only
        # opens the region.
        header_seen = False
        region: list[str] = []
        for l in self._idx.lines:
            norm = normalize_text(l.text)
            if not header_seen:
                if is_explanation_header(norm):
                    header_seen = True
                continue
            if is_explanation_header(norm) or is_answer_header(norm):
                break
            region.append(l.line_ref)
        if not header_seen:
            out.add_unresolved(t, "missing", ("no 详解/解析 header",))
            return
        if not region:
            out.add_unresolved(t, "missing", ("explanation region empty",))
            return
        owned = [
            r for r in region
            if qn is None or is_question_start(normalize_text(self._idx.get(r).text)) == qn
        ]
        if not owned:
            out.add_unresolved(t, "missing", (f"no explanation row for qn={qn}",))
            return
        out.add_span(unit_id, t, owned, "exact", ("explanation", f"qn={qn}"))

    def _image_span(self, out, unit_id, t):
        ok = [
            f for f in self._figures
            if f.page_no is not None and f.bbox and f.placement and f.source
        ]
        if not ok:
            out.add_unresolved(t, "ambiguous", ("no IS-7-complete figure",))
            return
        fid = (t.image_ref or {}).get("figure_id")
        cands = [f for f in ok if fid is None or f.figure_id == fid]
        if not cands:
            out.add_unresolved(t, "missing", (f"figure {fid} not found",))
        elif len(cands) > 1:
            out.add_unresolved(t, "ambiguous", ("multiple figures",))
        else:
            f = cands[0]
            page_lines = [l.line_ref for l in self._idx.lines if l.page_no == f.page_no]
            if not page_lines:
                out.add_unresolved(t, "ambiguous", ("figure page has no lines",))
                return
            out.add_span(unit_id, t, page_lines, "exact",
                         ("image figure", f.figure_id, f"page={f.page_no}"), role_hint="image")

    def _blank_span(self, out, unit_id, t):
        # blank 须闭合到 sub_question/answer（§5.3）；M1 annotation 无闭合声明 →
        # incomplete（回 Annotation，段 F 不凭空造闭合）。
        out.add_unresolved(
            t, "incomplete",
            ("blank requires sub_question/answer closure (deferred to 段 F)",),
        )

    # ------------------------------------------------------------------ relations
    def _enforce_material_overlap(self, out: _Out) -> None:
        """E owns source-span overlap validation（20 §5.3 material + §5.5）。

        material span 与任何非 material resolved span、或其他 material span 共享行
        → material 不得 resolved（demote 为 incomplete unresolved，避免污染 F 输入）。
        """
        mats = [s for s in out.resolved if s.role in _MATERIAL_ROLES]
        if not mats:
            return
        non_mats = [s for s in out.resolved if s.role not in _MATERIAL_ROLES]
        for m in list(mats):
            mrefs = frozenset(m.line_refs)
            conflicts = []
            for o in non_mats:
                # P3: skip char-spans that intentionally share a material line
                # (stem starts mid-line on material line — char-level, not line-level overlap)
                if any("material-shared-line" in ev for ev in o.evidence):
                    continue
                # E2E-009R5: composite child stems/options live inside the
                # shared passage (cloze blanks / reading stems). Not pollution.
                if ".sub" in (o.span_id or "") and o.role in ("stem", "option"):
                    continue
                if o.role in ("stem", "option") and (o.span_id or "").startswith("sp-") and (m.span_id or "").startswith("sp-"):
                    o_pre = o.span_id[3:].rsplit(".", 1)[0]
                    m_pre = m.span_id[3:].rsplit(".", 1)[0]
                    if o_pre == m_pre:
                        continue
                if frozenset(o.line_refs) & mrefs:
                    conflicts.append(
                        f"overlaps {o.role} span {o.span_id} ({o.line_refs[0]}..{o.line_refs[-1]})"
                    )
            for m2 in mats:
                if m2.span_id != m.span_id and frozenset(m2.line_refs) & mrefs:
                    conflicts.append(f"overlaps material {m2.span_id}")
            if not conflicts:
                continue
            out.resolved.remove(m)
            out.unresolved.append(
                UnresolvedReference(
                    reference_id=m.span_id[3:] if m.span_id.startswith("sp-") else m.span_id,
                    role=m.role, resolution_status="incomplete",
                    evidence=tuple(conflicts) + ("material overlap → unresolved",),
                )
            )

    def _resolve_relations(self, out: _Out, rel_decls):
        span_id_to_span = {s.span_id: s for s in out.resolved}
        result: list[ResolvedRelation] = []
        for rel in rel_decls:
            target_span = span_id_to_span.get(f"sp-{rel.target_unit_id}")
            result.append(
                ResolvedRelation(
                    relation_id=f"{rel.source_unit_id}->{rel.target_unit_id}",
                    source_span_id=f"sp-{rel.source_unit_id}",
                    target_unit_ref=rel.target_unit_id,
                    relation_type=rel.relation_type,
                    resolved_target_span_id=target_span.span_id if target_span else None,
                    status="resolved" if target_span else "unresolved",
                )
            )
        return result
