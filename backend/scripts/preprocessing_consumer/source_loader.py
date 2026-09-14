"""Source .md loader — 把 preprocessing 源文件转成 V3 DocumentSourceLine 行列表。

V3 的 line_ref 格式是 P{page}L{line:03d}。Markdown 无分页信息，
统一视为 page 1，line_no = 1-based 行号。
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceLine:
    """V3 DocumentSourceLine 的纯数据对应物（不依赖 ORM）。"""
    line_ref: str           # P1L007
    seq: int                # 0-based global ordering
    page_no: int            # always 1 for markdown
    line_no_in_page: int    # 1-based
    text: str
    block_type: str         # "text" (simplified)
    line_hash: str          # sha256 hex of text


def load_source_lines(source_path: Path) -> list[SourceLine]:
    """读源 .md，逐行构造 SourceLine。"""
    text = source_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines):
        line_no = i + 1
        result.append(SourceLine(
            line_ref=f"P1L{line_no:03d}",
            seq=i,
            page_no=1,
            line_no_in_page=line_no,
            text=line,
            block_type="text",
            line_hash=hashlib.sha256(line.encode("utf-8")).hexdigest(),
        ))
    return result


def compute_body_hash(lines: list[SourceLine]) -> str:
    """body_hash = sha256 of joined text with \\n。"""
    joined = "\n".join(l.text for l in lines)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def line_ref_for(line_no: int) -> str:
    """preprocessing 1-based 行号 → V3 line_ref。"""
    return f"P1L{line_no:03d}"
