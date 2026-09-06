"""Candidate payload 组装（段 G，10 §5.3 + plan D6，纯函数）。

一个 candidate = 一个 top-level unit；payload 是**不可变可重放编译快照**，能在不重跑
E/F/G 的情况下重建 Question/Instance/Material（10 §5.3「不重跑 LLM」/ 20 §9 #7）。
本模块只做确定性序列化（CompiledSnapshot/IR/ResolvedRun → dict），不触 DB、不判 gate；
gate_decision 的 pass/fail+reasons **不进 payload**（P0-1：payload.evidence[] 只含
Resolver/Compiler 证据）。

顶层结构 = 10 §5.3 八个字段：ir_snapshot / resolved_spans[] / compiled_roles[] /
answer[] / figure_refs[]（M1 恒空，BUG-V3-020）/ knowledge_links[]（M1 恒空）/
evidence[] / display_hint。

物化侧重建 leaf 所需的 dedup_key/occurrence_key 不在 payload 落死——物化以 identity
纯函数 + resolved_spans/compiled_roles 确定性重算（不重跑 E/F/G，P0-3 冻结 payload）。
"""

from __future__ import annotations

import uuid

from app.domains.compile.ir import IR, IRNode
from app.domains.compile.snapshot import (
    CompiledLeaf,
    CompiledMaterial,
    CompiledRole,
    CompiledSnapshot,
)
from app.domains.gate.policy import partition_candidate
from app.domains.resolver.span import ResolvedRun, ResolvedSpan

# 序列化 identity 使用的确定性元字段清单（确保与物化/审计读一致）。
RESOLVED_SPAN_FIELDS = (
    "span_id", "role", "granularity", "line_refs", "start_offset", "end_offset",
    "text_hash", "resolution_status",
)
COMPILED_ROLE_FIELDS = ("role", "span_id", "line_refs", "text", "text_hash", "label")
ANSWER_FIELDS = (
    "span_id", "line_refs", "text", "text_hash",
    "source_located", "complete", "verified_correct",
)


def _uuid(sid: uuid.UUID) -> str:
    return str(sid)


def build(
    *,
    root: IRNode,
    ir: IR,
    compiled: CompiledSnapshot,
    resolved_run: ResolvedRun,
) -> dict:
    """组装 candidate payload dict（10 §5.3）。root 须是该 candidate 的 top-level unit。"""
    resolved: dict[str, ResolvedSpan] = {s.span_id: s for s in resolved_run.resolved_spans}
    leaves, materials = partition_candidate(root, compiled)

    return {
        "ir_snapshot": _ir_snapshot(root, ir),
        "resolved_spans": _resolved_spans(leaves, materials, resolved),
        "compiled_roles": _compiled_roles(leaves, materials),
        "answer": _answers(leaves),
        "figure_refs": [],
        "knowledge_links": [],
        "evidence": _evidence(resolved_run, leaves, materials, resolved),
        "display_hint": _display_hint(root, leaves),
    }


def _ir_snapshot(root: IRNode, ir: IR) -> dict:
    """ir_snapshot：root 子树（units 复数 = composite 子题）+ 版本/身份锚点。"""
    return {
        "ir_schema": ir.ir_schema,
        "source_version_id": _uuid(ir.source_version_id),
        "annotation_id": _uuid(ir.annotation_id),
        "units": [_node_dict(n) for n in (root,) + root.sub_questions],
    }


def _node_dict(n: IRNode) -> dict:
    d: dict = {
        "unit_id": n.unit_id,
        "unit_type": n.unit_type,
        "question_number": n.question_number,
        "question_number_range": n.question_number_range,
        "original_question_type": n.original_question_type,
        "content": [
            {"role": c.role, "span_id": c.span_id, "label": c.label, "unsupported": c.unsupported}
            for c in n.content
        ],
        "shared_components": [
            {"role": c.role, "span_id": c.span_id, "label": c.label, "unsupported": c.unsupported}
            for c in n.shared_components
        ],
        "relations": list(n.relations),
        "semantic_status": n.semantic_status,
    }
    if n.sub_questions:
        d["sub_questions"] = [_node_dict(s) for s in n.sub_questions]
    return d


def _collect_spans(leaves, materials) -> list[str]:
    """candidate 消费的全部 span_id（去重保序）。"""
    seen: dict[str, None] = {}
    for leaf in leaves:
        if leaf.stem is not None:
            seen.setdefault(leaf.stem.span_id)
        for o in leaf.options:
            seen.setdefault(o.span_id)
        if leaf.explanation is not None:
            seen.setdefault(leaf.explanation.span_id)
        if leaf.answer is not None:
            seen.setdefault(leaf.answer.span_id)
    for m in materials:
        seen.setdefault(m.span_id)
    return list(seen)


def _resolved_spans(leaves, materials, resolved: dict) -> list[dict]:
    """resolved_spans[]：每个 content role 的 Resolved Source Span（line_ref/offset/
    text_hash/resolution_status）。正文不进本段（B 域 line 由 line_ref 引用）。"""
    out: list[dict] = []
    for sid in _collect_spans(leaves, materials):
        span = resolved.get(sid)
        if span is None:
            # partition 后 material/leaf span 应全部可溯源（policy structural 层同检）。
            # 防御性仍输出占位，让 payload 自证不完整（IS-8）。
            out.append({"span_id": sid, "resolution_status": "missing"})
            continue
        d = {f: getattr(span, f) for f in RESOLVED_SPAN_FIELDS}
        d["line_refs"] = list(span.line_refs)
        d["start_offset"] = span.start_offset
        d["end_offset"] = span.end_offset
        out.append(d)
    return out


def _compiled_roles(leaves, materials) -> list[dict]:
    """compiled_roles[]：role → compiled text + text_hash（含 shared material，kind 区分）。

    每项带 unit_id 归属（composite 多子题不混）与 span_id/line_refs/label。物化侧据
    kind=material 重建 materials 表，其余重建 role_contents。
    """
    out: list[dict] = []
    for leaf in leaves:
        for cr in _leaf_roles(leaf):
            d = {f: getattr(cr, f) for f in COMPILED_ROLE_FIELDS}
            d["line_refs"] = list(cr.line_refs)
            d["unit_id"] = leaf.unit_id
            d["kind"] = "content"
            out.append(d)
    for m in materials:
        d = {
            "role": m.role,
            "span_id": m.span_id,
            "line_refs": [],
            "text": m.text,
            "text_hash": m.text_hash,
            "label": None,
            "unit_id": m.unit_id,
            "kind": "material",
        }
        out.append(d)
    return out


def _leaf_roles(leaf: CompiledLeaf) -> list[CompiledRole]:
    roles: list[CompiledRole] = []
    if leaf.stem is not None:
        roles.append(leaf.stem)
    roles.extend(leaf.options)
    if leaf.explanation is not None:
        roles.append(leaf.explanation)
    return roles


def _answers(leaves) -> list[dict]:
    """answer[]：编译后答案 + answer_status 三字段（D8：composite parent 无独立 answer，
    故仅每 leaf 若有 answer 才出一项）。"""
    out: list[dict] = []
    for leaf in leaves:
        a = leaf.answer
        if a is None:
            continue
        d = {f: getattr(a, f) for f in ANSWER_FIELDS}
        d["line_refs"] = list(a.line_refs)
        d["unit_id"] = leaf.unit_id
        d["question_number"] = leaf.question_number
        out.append(d)
    return out


def _evidence(
    resolved_run: ResolvedRun,
    leaves,
    materials,
    resolved: dict,
) -> list[dict]:
    """evidence[]：只含 Resolver/Compiler 证据（P0-1 归属；gate reasons 不进 payload）。

    每条 = {kind: resolver|compiler, role, span_id, evidence[]}。resolver 证据取
    ResolvedSpan.evidence；compiler 证据 = leaf 编译（text_hash）记录。
    """
    out: list[dict] = []
    for sid in _collect_spans(leaves, materials):
        span = resolved.get(sid)
        if span is not None and span.evidence:
            out.append({
                "kind": "resolver",
                "role": span.role,
                "span_id": sid,
                "evidence": list(span.evidence),
            })
    for leaf in leaves:
        for role, sid, _text_hash, _text in _compiled_proofs(leaf):
            out.append({
                "kind": "compiler",
                "role": role,
                "span_id": sid,
                "evidence": ["compiled role text", "text_hash over compiled text"],
            })
    for m in materials:
        out.append({
            "kind": "compiler",
            "role": "material",
            "span_id": m.span_id,
            "evidence": ["compiled shared material", "text_hash over compiled text"],
        })
    if resolved_run.unresolved_references:
        for u in resolved_run.unresolved_references:
            out.append({
                "kind": "resolver",
                "role": u.role,
                "span_id": None,
                "evidence": [f"unresolved {u.resolution_status}"] + list(u.evidence),
            })
    return out


def _compiled_proofs(leaf: CompiledLeaf) -> list[tuple[str, str, str, str]]:
    checks: list[tuple[str, str, str, str]] = []
    if leaf.stem is not None:
        checks.append(("stem", leaf.stem.span_id, leaf.stem.text_hash, leaf.stem.text))
    for o in leaf.options:
        checks.append(("option", o.span_id, o.text_hash, o.text))
    if leaf.explanation is not None:
        checks.append(
            ("explanation", leaf.explanation.span_id, leaf.explanation.text_hash, leaf.explanation.text)
        )
    if leaf.answer is not None:
        checks.append(("answer", leaf.answer.span_id, leaf.answer.text_hash, leaf.answer.text))
    return checks


def _display_hint(root: IRNode, leaves) -> dict:
    """display_hint：canonical_question_type + content_roles（DISPLAY_CONTRACT 兼容）。

    standalone → leaf canonical；composite → 子题 canonical 去重集合 + 无父 answer role。
    content_roles 只列 candidate 实际编译产出的 content role（供 DISPLAY 布局）。
    """
    if root.unit_type == "composite_unit":
        canonicals: list[str] = []
        for l in leaves:
            if l.canonical_question_type not in canonicals:
                canonicals.append(l.canonical_question_type)
        return {
            "unit_type": "composite_unit",
            "canonical_question_type": canonicals,
            "content_roles": _distinct_content_roles(leaves),
        }
    leaf = leaves[0] if leaves else None
    return {
        "unit_type": "standalone_unit",
        "canonical_question_type": leaf.canonical_question_type if leaf else None,
        "content_roles": _distinct_content_roles(leaves),
    }


def _distinct_content_roles(leaves) -> list[str]:
    roles: list[str] = []
    for leaf in leaves:
        for r in _leaf_roles(leaf):
            if r.role not in roles:
                roles.append(r.role)
        if leaf.answer is not None and "answer" not in roles:
            roles.append("answer")
    return roles
