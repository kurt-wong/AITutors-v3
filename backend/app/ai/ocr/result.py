"""OCR 输出结构（段 B）：provider 无关的解析结果，供 seal line_index 消费。

10 §4 语义边界：OCR 层只产「版面行 + 可选图定位」，不产题号/正文/语义 claim
（那属 annotation/resolver）。OCRResult 到 source version 的落库由 seal 层完成。

Phase I-3：新增 SourceSpan（layout evidence），OCRLine 增加 spans 字段。
SourceSpan 描述 source evidence instance，不表示 semantic equality。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceSpan:
    """一行内一个 span 的 layout evidence（Phase I-3）。

    span_hash = SHA256(text + font + size + flags + bbox + origin)，
    描述 source evidence instance（layout evidence identity），
    **不表示 semantic equality**——相同文本不同位置 → 不同 hash（正确行为）。
    """

    seq: int
    text: str
    font: str | None = None
    size: float | None = None
    flags: int | None = None
    bbox: dict | None = None  # {x0,y0,x1,y1}
    origin: tuple[float, float] | None = None  # (x, y) baseline
    span_hash: str = ""

    @property
    def is_superscript(self) -> bool:
        return bool(self.flags and self.flags & 1)

    @property
    def is_subscript(self) -> bool:
        return bool(self.flags and self.flags & 2)

    @property
    def is_bold(self) -> bool:
        return bool(self.flags and self.flags & 32)

    @property
    def is_italic(self) -> bool:
        return bool(self.flags and self.flags & 4)

    @staticmethod
    def compute_hash(
        text: str,
        font: str | None,
        size: float | None,
        flags: int | None,
        bbox: dict | None,
        origin: tuple[float, float] | None,
    ) -> str:
        """确定性 hash：text + font + size + flags + bbox + origin。"""
        payload = {
            "text": text,
            "font": font,
            "size": size,
            "flags": flags,
            "bbox": bbox,
            "origin": list(origin) if origin else None,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _make_span(
    seq: int,
    text: str,
    font: str | None,
    size: float | None,
    flags: int | None,
    bbox: dict | None,
    origin: tuple[float, float] | None,
) -> SourceSpan:
    """构造 SourceSpan 并计算 span_hash。"""
    h = SourceSpan.compute_hash(text, font, size, flags, bbox, origin)
    return SourceSpan(
        seq=seq, text=text, font=font, size=size, flags=flags,
        bbox=bbox, origin=origin, span_hash=h,
    )


@dataclass(frozen=True)
class OCRLine:
    """版面一行文本。bbox 为 page 坐标 {x0,y0,x1,y1}，缺省 None（不强造）。

    Phase I-3：增加 spans 字段（layout evidence）。向后兼容：默认空 tuple。
    """

    text: str
    page_no: int
    bbox: dict | None = None
    spans: tuple[SourceSpan, ...] = field(default_factory=tuple)


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
