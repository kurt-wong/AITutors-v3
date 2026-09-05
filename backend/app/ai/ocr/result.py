"""OCR 输出结构（段 B）：provider 无关的解析结果，供 seal line_index 消费。

10 §4 语义边界：OCR 层只产「版面行 + 可选图定位」，不产题号/正文/语义 claim
（那属 annotation/resolver）。OCRResult 到 source version 的落库由 seal 层完成。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OCRLine:
    """版面一行文本。bbox 为 page 坐标 {x0,y0,x1,y1}，缺省 None（不强造）。"""

    text: str
    page_no: int
    bbox: dict | None = None


@dataclass(frozen=True)
class OCRFigure:
    """版面一张图。缺 page/bbox 定位信息则 seal 不落库（10 §4.4 IS-7）。"""

    page_no: int
    bbox: dict
    source: str
    content: bytes = b""


@dataclass(frozen=True)
class OCRResult:
    provider: str
    model: str
    pages: int
    lines: tuple[OCRLine, ...] = field(default_factory=tuple)
    figures: tuple[OCRFigure, ...] = field(default_factory=tuple)
    source_meta: dict = field(default_factory=dict)
