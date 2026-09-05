"""确定性行索引与 seal hashing（段 B）。纯函数：同输入必同输出。

钉定（计划 §决策 5/6）：
- line_ref = f"P{page_no}L{line_no_in_page:03d}"（10 §4.3 例 P1L001）；seq 跨页全局 1-based。
- body_hash 是对「由 line index 按 seq 以 \\n join 重建的 body_text」的 raw UTF-8 SHA256
  （IS-4 确定性重建，事实层非规范化层）；不把 sha256_hex 误用于 raw 内容 hash。
- line_hash/integrity_hash 用 canonical sha256_hex（复合语义）。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.ai.ocr.result import OCRLine
from app.core.hashing import sha256_hex


@dataclass(frozen=True)
class SealLine:
    """落库前的一行：带 line_ref/seq（version 内定位，10 §4.3）。"""

    line_ref: str
    seq: int
    page_no: int
    line_no_in_page: int
    text: str
    block_type: str = "text"
    bbox: dict | None = None


def build_line_index(ocr_lines: tuple[OCRLine, ...]) -> tuple[SealLine, ...]:
    """OCR 行 → SealLine 序列：按页序给全局 seq；页内 line_no 自增；line_ref 确定性。"""
    built: list[SealLine] = []
    seq = 0
    page_lines: dict[int, int] = {}
    for ol in ocr_lines:
        seq += 1
        line_no = page_lines.get(ol.page_no, 0) + 1
        page_lines[ol.page_no] = line_no
        built.append(
            SealLine(
                line_ref=f"P{ol.page_no}L{line_no:03d}",
                seq=seq,
                page_no=ol.page_no,
                line_no_in_page=line_no,
                text=ol.text,
                bbox=ol.bbox,
            )
        )
    return tuple(built)


def rebuild_body_text(lines: tuple[SealLine, ...]) -> str:
    """IS-4：按 seq 排序以 \\n join（事实层重建，不含规范化）。"""
    ordered = sorted(lines, key=lambda l: l.seq)
    return "\n".join(l.text for l in ordered)


def verify_body_rebuild(body_text: str, lines: tuple[SealLine, ...]) -> bool:
    """body_text 必须能由 line index 按 seq 以 \\n 重建（10 §4.2 约束）。"""
    return rebuild_body_text(lines) == body_text


def compute_body_hash(body_text: str) -> str:
    """raw 内容 hash：SHA256(body_text UTF-8)，非 canonical（防 JSON 引号语义漂移）。"""
    return hashlib.sha256(body_text.encode("utf-8")).hexdigest()


def compute_line_hash(
    *,
    text: str,
    raw_sources: dict | None,
    selected_source: str | None,
    evidence: str | None,
) -> str:
    """行 hash：canonical 复合（10 §4.3 line_hash 语义）。"""
    return sha256_hex(
        {
            "text": text,
            "raw_sources": raw_sources,
            "selected_source": selected_source,
            "evidence": evidence,
        }
    )


def compute_integrity_hash(
    *,
    body_hash: str,
    line_hashes: list[str],
    figure_hashes: list[str],
    provenance: dict,
) -> str:
    """version integrity_hash：正文+行+图+provenance 任一变化 → hash 变（10 §4.2）。"""
    return sha256_hex(
        {
            "body_hash": body_hash,
            "line_hashes": line_hashes,
            "figure_hashes": figure_hashes,
            "provenance": provenance,
        }
    )
