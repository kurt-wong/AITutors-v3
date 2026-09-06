"""Semantic Question IR（段 F，F1-F2，20 §6）。transient；span 只存 id，不复制正文。

IRBuilder 把 E ResolvedRun + annotation 装配成 IR；validate_ir 校验 20 §6.2 不变量 1-8，
产出每 unit 的 semantic_status（{ready, incomplete}，BUG-V3-018 最小值域）。

F 只装配不补语义：content 只含 annotation 已声明的 role；role 无对应 resolved span
（span_id 缺失）→ 该 unit 非 ready（incomplete），F 不从正文补猜。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domains.compile import map_canonical_type, content_roles_for
from app.domains.resolver.span import ResolvedRun

# span_id 命名与段 E reference.py target_id 保持一致（防跨段漂移）。
_ROLE_KIND = {
    "stem": "question_label",
    "answer": "answer_zone",
    "explanation": "explanation_zone",
}


@dataclass(frozen=True)
class IRContent:
    """一个 content role 的 IR 表示：只引用 E 产出的 span（不携带正文）。

    unsupported=True：annotation 声明但 F 尚无合法编译表示（image/blank，figure_refs
    延后 BUG-V3-020）→ validator 判 incomplete（fail-loud，绝不静默丢弃）。
    """

    role: str
    span_id: str | None  # None = annotation 声明但 E 未 resolved / unsupported
    label: str | None = None  # option/blank 标签
    unsupported: bool = False


@dataclass(frozen=True)
class IRNode:
    """standalone 或 composite（sub_questions 递归）。semantic_status 由 validate_ir 给出。"""

    unit_id: str
    unit_type: str
    question_number: str | None
    question_number_range: str | None
    original_question_type: str | None
    content: tuple[IRContent, ...] = field(default_factory=tuple)
    shared_components: tuple[IRContent, ...] = field(default_factory=tuple)
    sub_questions: tuple["IRNode", ...] = field(default_factory=tuple)
    relations: tuple[str, ...] = field(default_factory=tuple)  # material_dependency targets
    semantic_status: str = "incomplete"


@dataclass(frozen=True)
class IR:
    ir_schema: str
    source_version_id: uuid.UUID
    annotation_id: uuid.UUID
    units: tuple[IRNode, ...] = field(default_factory=tuple)


def _content_span_id(unit_id: str, role: str, label: str | None = None) -> str:
    """与段 E resolver span_id 命名一致（E = f"sp-{target_id}"）。"""
    if role == "option":
        return f"sp-{unit_id}.option.{label}"
    if role == "stem":
        return f"sp-{unit_id}.stem"
    if role == "answer":
        return f"sp-{unit_id}.answer"
    if role == "explanation":
        return f"sp-{unit_id}.explanation"
    if role in ("material", "word_bank", "shared_option_pool", "task_instruction"):
        return f"sp-{unit_id}.{role}"
    return f"sp-{unit_id}.{role}"


def _has_span(resolved: dict[str, object], span_id: str) -> bool:
    return span_id in resolved


class IRBuilder:
    """ResolvedRun + annotation → IR（纯函数；只装配声明，不补语义）。"""

    @staticmethod
    def build(
        resolved_run: ResolvedRun,
        annotation_payload: dict,
        source_version_id: uuid.UUID,
        annotation_id: uuid.UUID,
    ) -> IR:
        resolved = {s.span_id: s for s in resolved_run.resolved_spans}
        units = tuple(
            IRBuilder._node(unit, resolved) for unit in annotation_payload.get("semantic_units", [])
        )
        ir = IR(
            ir_schema="semantic-question-ir/v0.3",
            source_version_id=source_version_id,
            annotation_id=annotation_id,
            units=units,
        )
        return validate_ir(ir)

    @staticmethod
    def _node(unit: dict, resolved: dict, inherited_type: str | None = None) -> IRNode:
        uid = unit.get("unit_id") or str(unit.get("question_label")) or "?"
        u_type = unit.get("unit_type", "standalone_question")
        sub_units = unit.get("sub_questions") or []
        shared = unit.get("shared_components") or {}
        content = unit.get("content") or {}
        original_type = unit.get("original_question_type") or inherited_type
        if u_type == "composite_unit" or shared or sub_units:
            shared_items = []
            for role, val in shared.items():
                sid = _content_span_id(uid, role)
                shared_items.append(
                    IRContent(role=role, span_id=sid if _has_span(resolved, sid) else None)
                )
            # 子题继承 composite 的题型（sub 通常不重复声明 original_question_type）。
            subs = tuple(IRBuilder._node(s, resolved, original_type) for s in sub_units)
            return IRNode(
                unit_id=uid, unit_type="composite_unit",
                question_number=None,
                question_number_range=unit.get("question_number_range"),
                original_question_type=original_type,
                content=_content_items(uid, content, resolved),
                shared_components=tuple(shared_items),
                sub_questions=subs,
                relations=_declared_relations(uid, unit),
            )
        return IRNode(
            unit_id=uid, unit_type="standalone_question",
            question_number=str(unit.get("question_number") or unit.get("question_label") or ""),
            question_number_range=None,
            original_question_type=original_type,
            content=_content_items(uid, content, resolved),
        )


def _content_items(unit_id: str, content: dict, resolved: dict) -> tuple[IRContent, ...]:
    """只含 annotation 已声明的 role（不补）；span_id 缺失（E 未 resolved）→ None。

    image/blank 等 F 尚无合法编译表示的 role → unsupported=True（validator 判
    incomplete，fail-loud；figure_refs 延后 BUG-V3-020）。
    """
    items: list[IRContent] = []
    for role in ("stem", "answer", "explanation"):
        if isinstance(content.get(role), dict):
            sid = _content_span_id(unit_id, role)
            items.append(IRContent(role=role, span_id=sid if _has_span(resolved, sid) else None))
    opts = content.get("options") or []
    for o in opts:
        if isinstance(o, dict) and o.get("label"):
            sid = _content_span_id(unit_id, "option", o["label"])
            items.append(IRContent(
                role="option", span_id=sid if _has_span(resolved, sid) else None,
                label=str(o["label"]),
            ))
    for unsupported_role in ("image", "blank"):
        if content.get(unsupported_role) not in (None, [], {}):
            items.append(IRContent(role=unsupported_role, span_id=None, unsupported=True))
    return tuple(items)


def _declared_relations(unit_id: str, unit: dict) -> tuple[str, ...]:
    rels: list[str] = []
    for sub in unit.get("sub_questions") or []:
        for dep in sub.get("depends_on") or []:
            if dep.get("type") == "material_dependency" and dep.get("target"):
                rels.append(str(dep["target"]))
    return tuple(rels)


# ------------------------------------------------------------------ 不变量 1-8
def validate_ir(ir: IR) -> IR:
    """逐 unit 校验 20 §6.2 不变量，返回带 semantic_status 的 IR。

    任一违规 → 该 unit semantic_status=incomplete。invariant 8：非 ready 不产 leaves
    （Compiler 侧据此只编译 ready）。
    """
    seen_units: set[str] = set()
    units = tuple(_validate_node(n, seen_units) for n in ir.units)
    return IR(ir.ir_schema, ir.source_version_id, ir.annotation_id, units)


def _validate_node(node: IRNode, seen: set[str]) -> IRNode:
    problems: list[str] = []
    if node.unit_id in seen:
        problems.append("duplicate unit_id")  # invariant 5
    seen.add(node.unit_id)

    canonical = None
    if node.original_question_type is not None:
        canonical = map_canonical_type(node.original_question_type)
        if canonical is None:
            problems.append(f"unknown canonical type {node.original_question_type!r}")
    content_by_role: dict[str, IRContent] = {c.role: c for c in node.content}

    # invariant 1：required role 全满足才可能 ready（对 leaf；composite 由子题递归校验）。
    if node.unit_type != "composite_unit":
        required_roles = content_roles_for(canonical)
        if required_roles.get("stem") == "required":
            c = content_by_role.get("stem")
            if c is None:
                problems.append("stem not declared")
            elif c.span_id is None:
                problems.append("stem unresolved")
        if required_roles.get("answer") == "required":
            c = content_by_role.get("answer")
            if c is None:
                problems.append("answer not declared")
            elif c.span_id is None:
                problems.append("answer unresolved")
        if required_roles.get("options") == "required_for_choice":
            has_opts = any(c.role == "option" for c in node.content)
            if not has_opts:
                problems.append("options missing for choice type")
        for c in node.content:
            if c.unsupported:
                problems.append(f"unsupported content role {c.role} "
                                "(figure_refs/blank deferred, BUG-V3-020)")
            elif c.span_id is None:
                problems.append(f"role {c.role} unresolved")

    # invariant 2/3/4/6/7：composite shared + relations（target 存在且 resolved）+ 子题全 ready。
    validated_subs = tuple(_validate_node(s, seen) for s in node.sub_questions)
    if node.unit_type == "composite_unit":
        if not node.shared_components:
            problems.append("composite has no shared component material")
        for sc in node.shared_components:
            if sc.span_id is None:
                problems.append(f"shared component {sc.role} unresolved")
        shared_by_role = {c.role: c for c in node.shared_components}
        for r in node.relations:  # material_dependency targets（子题声明）
            sc = shared_by_role.get(r)
            if sc is None:
                problems.append(f"material_dependency target {r!r} not in shared_components")
            elif sc.span_id is None:
                problems.append(f"material_dependency target {r!r} span unresolved")
        if any(s.semantic_status != "ready" for s in validated_subs):
            problems.append("composite sub_question not ready")  # invariant 7

    status = "incomplete" if problems else "ready"
    return IRNode(
        node.unit_id, node.unit_type, node.question_number, node.question_number_range,
        node.original_question_type, node.content, node.shared_components,
        validated_subs, node.relations, status,
    )
