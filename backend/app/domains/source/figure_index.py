"""确定性 figure index 与 seal figure hashing（段 B）。纯函数：同输入必同输出。

钉定（BUG-011 Scope Freeze / 10 §4.4 v1.2.2）：
- figure_id = f"FIG-{page_no}-{ordinal:02d}"（version 内定位，10 §4.4 例 FIG-1-01）；
  ordinal = page 内 canonical visual order（1-based），排序键 =
  (page_no, bbox.y0, bbox.x0, bbox.y1, bbox.x1, figure_hash, extraction_ordinal)。
- figure_hash = SHA256(raw content)（raw 内容 hash，非 canonical sha256_hex，与 body_hash 同层）。
- object_key = f"figure:{figure_hash}"（M1 logical deterministic key，不实现 blob storage）。
- placement = "standalone"（source-level placement 未定，恒 M1 默认；≠ figure_refs.role）。

确定性 scope（BUG-011 Plan Review amendment ①）：
- extraction_ordinal = provider 在同一 source bytes 上的稳定 extraction order，仅作 canonical
  sort key 完全相同时的最后 tie-breaker，非 figure identity 的独立语义组成。
- invariant =「同一 sealed source version + 同一 provider extraction → deterministic figure_id」；
  不要求跨 provider 相同（figure_id 是 version-scoped）。

IS-7 写入门（10 §4.4 / amendment ③）：
- 无 figure = 合法空集（返回 ()）。
- 任一 figure 缺 page_no/bbox/source/content，或 bbox 缺 x0/y0/x1/y1 或值非合法有限数值
  → 不写入 + fail-loud（ValueError 上抛，seal 整体失败，无部分写）。
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from app.ai.ocr.result import OCRFigure

PLACEMENT_STANDALONE = "standalone"

_BBOX_KEYS = ("x0", "y0", "x1", "y1")


@dataclass(frozen=True)
class SealFigure:
    """落库前的一张图：figure_id/figure_hash/object_key/placement 已确定（10 §4.4）。"""

    figure_id: str
    figure_hash: str
    object_key: str
    placement: str
    page_no: int
    bbox: dict
    source: str
    content: bytes


@dataclass(frozen=True)
class _FigureEntry:
    """IS-7 校验通过 + 派生出 figure_hash 后的中间态（canonical sort 输入）。"""

    page_no: int
    top: float
    left: float
    bottom: float
    right: float
    figure_hash: str
    extraction_ordinal: int
    bbox: dict
    source: str
    content: bytes


def compute_figure_hash(content: bytes) -> str:
    """raw 内容 hash：SHA256(raw bytes)，非 canonical（与 compute_body_hash 同层）。"""
    return hashlib.sha256(content).hexdigest()


def _validate_bbox(bbox: dict, hint: str) -> None:
    """IS-7 bbox 校验：x0/y0/x1/y1 四键齐且为合法有限数值（amendment ③）。"""
    if not isinstance(bbox, dict):
        raise ValueError(f"figure {hint}: bbox 非 dict {bbox!r}")
    for key in _BBOX_KEYS:
        value = bbox.get(key)
        if value is None:
            raise ValueError(f"figure {hint}: bbox 缺键 {key}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"figure {hint}: bbox.{key} 非数值 {value!r}")
        if not math.isfinite(float(value)):
            raise ValueError(f"figure {hint}: bbox.{key} 非有限数值 {value!r}")


def _validate_figure(fig: OCRFigure, extraction_ordinal: int) -> None:
    hint = f"#{extraction_ordinal}"
    if not isinstance(fig.page_no, int) or fig.page_no < 1:
        raise ValueError(f"figure {hint}: page_no 非法 {fig.page_no!r}")
    if not fig.source:
        raise ValueError(f"figure {hint}: source 为空")
    if not fig.content:
        raise ValueError(f"figure {hint}: content 为空（无法派生 figure_hash）")
    _validate_bbox(fig.bbox, hint)


def build_figure_index(ocr_figures: tuple[OCRFigure, ...]) -> tuple[SealFigure, ...]:
    """OCR 图 → SealFigure 序列：IS-7 校验 → 派生 hash → canonical 序 → page 内 ordinal → id。"""
    entries: list[_FigureEntry] = []
    for extraction_ordinal, fig in enumerate(ocr_figures):
        _validate_figure(fig, extraction_ordinal)
        entries.append(
            _FigureEntry(
                page_no=fig.page_no,
                top=fig.bbox["y0"],
                left=fig.bbox["x0"],
                bottom=fig.bbox["y1"],
                right=fig.bbox["x1"],
                figure_hash=compute_figure_hash(fig.content),
                extraction_ordinal=extraction_ordinal,
                bbox=fig.bbox,
                source=fig.source,
                content=fig.content,
            )
        )

    entries.sort(
        key=lambda e: (
            e.page_no,
            e.top,
            e.left,
            e.bottom,
            e.right,
            e.figure_hash,
            e.extraction_ordinal,
        )
    )

    built: list[SealFigure] = []
    page_ordinals: dict[int, int] = {}
    for e in entries:
        ordinal = page_ordinals.get(e.page_no, 0) + 1
        page_ordinals[e.page_no] = ordinal
        built.append(
            SealFigure(
                figure_id=f"FIG-{e.page_no}-{ordinal:02d}",
                figure_hash=e.figure_hash,
                object_key=f"figure:{e.figure_hash}",
                placement=PLACEMENT_STANDALONE,
                page_no=e.page_no,
                bbox=e.bbox,
                source=e.source,
                content=e.content,
            )
        )
    return tuple(built)
