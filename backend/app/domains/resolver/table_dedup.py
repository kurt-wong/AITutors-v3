# -*- coding: utf-8 -*-
"""R2X-10 P-2：extra→stem 表块去重判据（口径已与 DSH 对齐）。

判据（数据实证：整串包含 3/7、行元组 4/7、单元格多重集覆盖 7/7）：
  - 答案区表是重排重打副本而非字节副本，故用**单元格多重集覆盖率 ≥ 0.75** 判重复；
  - **块粒度全有全无**：按行去重会造出 2 行残表，比三表更难修；
  - **含 <img> 的块一律不参与去重**：图行 strip 标签后是空 <div>，文本级去重会把
    不同漂移图误判 DUP（实测 3 条）；
  - 被删块的**未覆盖单元格进审计字段**，不得静默丢（bio_2022_yi Q11 的 2.30 赖此保留）。

仅作用于 extra 表块；非表内容（文本/图片行）不走本判据，沿用既有归集行为。
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

TABLE_OPEN_RE = re.compile(r"<table\b", re.I)
TABLE_BLOCK_RE = re.compile(r"<table\b[\s\S]*?</table>", re.I)
ROW_RE = re.compile(r"<tr\b[^>]*>([\s\S]*?)</tr>", re.I)
CELL_RE = re.compile(r"<(?:td|th)\b[^>]*>([\s\S]*?)</(?:td|th)>", re.I)
TAG_RE = re.compile(r"<[^>]+>")

COVERAGE_THRESHOLD = 0.75


def norm_cell(s: str) -> str:
    """归一化单元格：去全部空白（重复渲染差异正是空格/重打）。"""
    return re.sub(r"\s+", "", s or "")


def extract_cells(html: str) -> list[str]:
    """表格 HTML → 扁平单元格列表（按行序，norm_cell 归一）。"""
    cells: list[str] = []
    for rm in ROW_RE.finditer(html):
        for cm in CELL_RE.finditer(rm.group(1)):
            cells.append(norm_cell(TAG_RE.sub("", cm.group(1)).replace("&nbsp;", " ")))
    return cells


@dataclass(frozen=True)
class TableBlock:
    """extra/stem 区间内的一个完整 <table> 块。"""

    start_seq: int  # 含
    end_seq: int  # 含
    cells: tuple[str, ...]
    has_img: bool
    has_text: bool


@dataclass(frozen=True)
class DedupDecision:
    """单个 extra 表块的去留判定（块粒度全有全无）。"""

    block: TableBlock
    action: str  # "keep" | "drop"
    reason: str  # img_block / no_text_cells / no_stem_table / coverage_below_threshold / duplicate_of_stem
    coverage: float
    uncovered_cells: tuple[str, ...] = field(default_factory=tuple)  # 仅 drop：审计字段


def _make_block(start_seq: int, end_seq: int, html: str) -> TableBlock:
    cells = tuple(extract_cells(html))
    return TableBlock(
        start_seq=start_seq,
        end_seq=end_seq,
        cells=cells,
        has_img="<img" in html.lower(),
        has_text=any(cells),
    )


def iter_table_blocks(
    lines, lo: int, hi: int
) -> list[TableBlock]:
    """扫描 seq∈[lo,hi] 的行（iterable of (seq, text)），返回完整 <table> 块。

    块可跨行（缓冲至 </table>）；同含多块的行逐块取。未闭合块不产出
    （fail-closed：残缺表不参与去重判定，保留原样并入）。
    """
    blocks: list[TableBlock] = []
    open_seq: int | None = None
    buf: list[str] = []
    for seq, text in sorted(lines, key=lambda x: x[0]):
        if seq < lo or seq > hi:
            continue
        lower = text.lower()
        pos = 0
        while pos <= len(text):
            if open_seq is None:
                i = lower.find("<table", pos)
                if i < 0:
                    break
                j = lower.find("</table>", i)
                if j >= 0:
                    end = j + len("</table>")
                    blocks.append(_make_block(seq, seq, text[i:end]))
                    pos = end
                else:
                    open_seq = seq
                    buf = [text[i:]]
                    break
            else:
                j = lower.find("</table>", pos)
                if j >= 0:
                    end = j + len("</table>")
                    buf.append(text[pos:end])
                    blocks.append(_make_block(open_seq, seq, "".join(buf)))
                    open_seq, buf = None, []
                    pos = end
                else:
                    buf.append(text[pos:])
                    break
    return blocks


def cell_multiset_coverage(extra_cells, stem_cells) -> float:
    """extra 单元格多重集被 stem 单元格多重集覆盖的比例（0~1）。"""
    if not extra_cells:
        return 0.0
    ec, sc = Counter(extra_cells), Counter(stem_cells)
    covered = sum(min(n, sc[k]) for k, n in ec.items())
    return covered / sum(ec.values())


def uncovered_cells(extra_cells, stem_cells) -> tuple[str, ...]:
    """多重集差：extra 中未被 stem 覆盖的单元格（保序、保重数）。"""
    sc = Counter(stem_cells)
    out: list[str] = []
    for c in extra_cells:
        if sc[c] > 0:
            sc[c] -= 1
        else:
            out.append(c)
    return tuple(out)


def classify_extra_table_block(
    block: TableBlock,
    stem_cells,
    threshold: float = COVERAGE_THRESHOLD,
) -> DedupDecision:
    """块粒度判定：重复则整块去（audit 带未覆盖单元格），否则整块留。"""
    if block.has_img:
        return DedupDecision(block, "keep", "img_block", 0.0)
    if not block.has_text:
        return DedupDecision(block, "keep", "no_text_cells", 0.0)
    cov = cell_multiset_coverage(block.cells, stem_cells)
    if not stem_cells:
        return DedupDecision(block, "keep", "no_stem_table", 0.0)
    if cov >= threshold:
        return DedupDecision(
            block, "drop", "duplicate_of_stem", cov, uncovered_cells(block.cells, stem_cells)
        )
    return DedupDecision(block, "keep", "coverage_below_threshold", cov)


def audit_tag(unit_id: str, d: DedupDecision) -> str:
    """审计 evidence 串（挂 stem span evidence，不静默丢）。"""
    b = d.block
    unc = ",".join(d.uncovered_cells) if d.uncovered_cells else ""
    return (
        f"table_dedup={unit_id}:L{b.start_seq}-{b.end_seq}"
        f":{d.action}:{d.reason}:cov={d.coverage:.2f}"
        + (f":uncovered={unc}" if unc else "")
    )
