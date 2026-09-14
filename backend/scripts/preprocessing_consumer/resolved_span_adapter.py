"""Track B: manifest → ResolvedSpan 直通适配器。

把 preprocessing manifest 的行号区间直接转成 V3 ResolvedSpan，
跳过 Resolver 的搜索阶段。这是未来正式集成的方向。
"""

import hashlib
import uuid

from .manifest_reader import Manifest, ManifestUnit
from .source_loader import SourceLine, line_ref_for


def _span_text_hash(lines: list[SourceLine], start: int, end: int) -> str:
    """计算 span 内文本的 sha256（1-based 闭区间）。"""
    texts = [lines[i - 1].text for i in range(start, end + 1) if 1 <= i <= len(lines)]
    joined = "\n".join(texts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _make_span(
    unit_id: str,
    role: str,
    lines: list[SourceLine],
    start: int,
    end: int,
    source_version_id: uuid.UUID,
) -> dict | None:
    """构造一个 ResolvedSpan dict。行号越界返回 None。"""
    n = len(lines)
    if start < 1 or end > n or start > end:
        return None
    line_refs = tuple(line_ref_for(i) for i in range(start, end + 1))
    return {
        "span_id": f"sp-{unit_id}.{role}",
        "source_version_id": source_version_id,
        "role": role,
        "start_line_ref": line_ref_for(start),
        "end_line_ref": line_ref_for(end),
        "line_refs": line_refs,
        "granularity": "line",
        "start_offset": None,
        "end_offset": None,
        "text_hash": _span_text_hash(lines, start, end),
        "resolution_status": "exact",
        "evidence": (),
    }


def manifest_to_resolved_spans(
    manifest: Manifest,
    lines: list[SourceLine],
    source_version_id: uuid.UUID,
) -> tuple[list[dict], list[dict]]:
    """把 manifest units 转成 (resolved_spans, unresolved) 列表。

    每个 unit 的每个 role（stem/options/answer/explanation/material/questions）
    各产生一个 ResolvedSpan。行号越界或缺失 → unresolved。
    """
    resolved: list[dict] = []
    unresolved: list[dict] = []

    def _try(unit: ManifestUnit, role: str, span: tuple[int, int] | None):
        if span is None:
            return
        s = _make_span(unit.unit_id, role, lines, span[0], span[1], source_version_id)
        if s is not None:
            resolved.append(s)
        else:
            unresolved.append({
                "reference_id": f"ref-{unit.unit_id}.{role}",
                "role": role,
                "resolution_status": "missing",
                "evidence": (f"lines {span} out of range 1..{len(lines)}",),
            })

    for unit in manifest.units:
        if unit.unit_type == "standalone_question":
            _try(unit, "stem", unit.stem_lines)
            _try(unit, "answer", unit.answer_lines)
            _try(unit, "explanation", unit.explanation_lines)
            _try(unit, "extra", unit.extra_lines)
            # options: preprocessing 只给区间，V3 option 是逐选项。
            # Track B 先把整个 options 区间作为一个 span。
            _try(unit, "option", unit.options_lines)
        else:
            _try(unit, "material", unit.material_lines)
            _try(unit, "questions", unit.questions_lines)
            _try(unit, "answer", unit.answer_lines)
            _try(unit, "explanation", unit.explanation_lines)

    return resolved, unresolved
