"""Semantic Reference 提取（段 E，E1，20 §4.4/§4.5）。

只提取 annotation payload 里**显式声明**的 reference 字段（question_label /
option_label / answer_zone / explanation_zone / instruction_marker /
blank_label / image）。**不消费正文、不从 content 文本自行推导 reference**
（防 V2 Text-First 猜测器回潮）。annotation 含正文已被段 D 禁字段拦截（20 §4.3）。

产出 ResolveTarget 列表 + RelationDeclaration 列表，供 resolver.py 分派到各 policy。
"""

from __future__ import annotations

from dataclasses import dataclass, field

_MATERIAL_ROLES = ("material", "word_bank", "shared_option_pool", "task_instruction")


@dataclass(frozen=True)
class ResolveTarget:
    """一个待解析的 content role 引用（引用声明，非坐标/正文）。"""

    target_id: str
    unit_id: str
    role: str
    kind: str  # question_label / option_label / answer_zone / explanation_zone / instruction_marker / blank_label / image
    question_number: str | None = None
    label: str | None = None
    start_marker: dict | None = None
    end_marker: dict | None = None
    zone: str | None = None
    image_ref: dict | None = None


@dataclass(frozen=True)
class RelationDeclaration:
    """一个待解析的语义依赖声明（20 §4.6：material_dependency 等）。"""

    source_unit_id: str
    target_unit_id: str
    relation_type: str


def extract_targets(payload: dict) -> tuple[ResolveTarget, ...]:
    """遍历 semantic_units[]，为每个 content role 产出 ResolveTarget。

    standalone / composite.sub_questions 的 content 简写字段 → target；
    composite.shared_components 的 instruction_marker → material target。
    凡声明 shared_components/sub_questions（或 unit_type=composite_unit）即按 composite。
    """
    targets: list[ResolveTarget] = []
    for unit in payload.get("semantic_units", []):
        u_id = unit.get("unit_id") or unit.get("question_label") or "?"
        sc = unit.get("shared_components") or {}
        subs = unit.get("sub_questions") or []
        if unit.get("unit_type") == "composite_unit" or sc or subs:
            for sc_key, sc_val in _iter_shared_components(unit):
                targets.append(_material_target(u_id, sc_key, sc_val))
            for sub in _iter_sub_questions(unit):
                sub_id = _sub_id(unit, sub)
                _extract_content_targets(targets, sub_id, sub.get("content") or {})
        else:
            _extract_content_targets(targets, u_id, unit.get("content") or {})
    return tuple(targets)


def _sub_id(unit: dict, sub: dict) -> str:
    """子题自身 identity（sub 自带 unit_id/question_label 优先，否则父限定）。"""
    return (
        sub.get("unit_id")
        or str(sub.get("question_label"))
        or f"{unit.get('unit_id') or '?'}.sub"
    )


def _iter_shared_components(unit: dict):
    sc = unit.get("shared_components") or {}
    for key in _MATERIAL_ROLES:
        val = sc.get(key)
        if isinstance(val, dict):
            yield key, val


def _iter_sub_questions(unit: dict):
    for sub in unit.get("sub_questions") or []:
        yield sub


def _material_target(unit_id: str, role: str, val: dict) -> ResolveTarget:
    """shared_components 项 → material target（20 §4.4 完整 reference 形态）。"""
    return ResolveTarget(
        target_id=f"{unit_id}.{role}",
        unit_id=unit_id,
        role=role,
        kind="instruction_marker",
        start_marker=val.get("start_marker"),
        end_marker=val.get("end_marker"),
    )


def _extract_content_targets(
    targets: list[ResolveTarget], unit_id: str, content: dict
) -> None:
    """unit/sub_question 的 content roles → targets（20 §4.5 简写引用形态）。"""
    _stem_target(targets, unit_id, content.get("stem"))
    for opt in content.get("options") or []:
        _option_target(targets, unit_id, opt)
    _answer_target(targets, unit_id, content.get("answer"))
    _explanation_target(targets, unit_id, content.get("explanation"))
    # blank/image：20 §4.5 列 blank/option/answer/image 为 content role；完整 JSON 形态未
    # 冻结（BUG-V3-013），这里按 minimal shape 提取，policy 仍按 §5.3 规则工作。
    _blank_target(targets, unit_id, content.get("blank"))
    _image_target(targets, unit_id, content.get("image"))


def _blank_target(targets: list, unit_id: str, blank) -> None:
    """20 §4.5 / BUG-V3-013 终裁：blank 形态 = [{blank_label(必填), question_label(可选)}]。

    malformed（非 dict/list、缺必填 blank_label）→ fail-fast（ValueError），非静默跳过。
    """
    if blank is None:
        return
    if isinstance(blank, dict):
        blank = [blank]
    if not isinstance(blank, list):
        raise ValueError(
            f"unit {unit_id!r} content.blank must be dict or list, got {type(blank).__name__}"
        )
    for b in blank:
        if not isinstance(b, dict):
            raise ValueError(
                f"unit {unit_id!r} content.blank[] must be dict, got {type(b).__name__}"
            )
        label = b.get("blank_label")
        if label is None:
            raise ValueError(
                f"unit {unit_id!r} content.blank[] missing required blank_label"
            )
        qn = b.get("question_label")
        targets.append(
            ResolveTarget(
                target_id=f"{unit_id}.blank.{label}", unit_id=unit_id,
                role="blank", kind="blank_label", label=str(label),
                question_number=str(qn) if qn is not None else None,
            )
        )


def _image_target(targets: list, unit_id: str, image) -> None:
    """20 §4.5 / BUG-V3-013 终裁：image 形态 = {image_ref: {figure_id(可选)}}。

    figure_id 是 M1 唯一图像引用 identity；malformed → fail-fast（ValueError）。
    """
    if image is None:
        return
    if not isinstance(image, dict):
        raise ValueError(
            f"unit {unit_id!r} content.image must be dict, got {type(image).__name__}"
        )
    img_ref = image.get("image_ref")
    if not isinstance(img_ref, dict):
        raise ValueError(
            f"unit {unit_id!r} content.image.image_ref must be dict, got {type(img_ref).__name__}"
        )
    targets.append(
        ResolveTarget(
            target_id=f"{unit_id}.image", unit_id=unit_id, role="image",
            kind="image", image_ref=img_ref,
        )
    )


def _stem_target(targets: list, unit_id: str, stem) -> None:
    if not isinstance(stem, dict):
        return
    qnum = stem.get("question_label")
    if qnum is None:
        return
    targets.append(
        ResolveTarget(
            target_id=f"{unit_id}.stem", unit_id=unit_id, role="stem",
            kind="question_label", question_number=str(qnum),
        )
    )


def _option_target(targets: list, unit_id: str, opt) -> None:
    if not isinstance(opt, dict):
        return
    label = opt.get("label")
    qnum = opt.get("question_label")
    if label is None:
        return
    targets.append(
        ResolveTarget(
            target_id=f"{unit_id}.option.{label}", unit_id=unit_id,
            role="option", kind="option_label", label=str(label),
            question_number=str(qnum) if qnum is not None else None,
        )
    )


def _answer_target(targets: list, unit_id: str, answer) -> None:
    if not isinstance(answer, dict):
        return
    zone = answer.get("answer_zone") or answer.get("zone")
    if zone is None:
        return
    targets.append(
        ResolveTarget(
            target_id=f"{unit_id}.answer", unit_id=unit_id, role="answer",
            kind="answer_zone", zone=str(zone),
            question_number=(
                str(answer["question_number"]) if answer.get("question_number") else None
            ),
        )
    )


def _explanation_target(targets: list, unit_id: str, expl) -> None:
    if not isinstance(expl, dict):
        return
    zone = expl.get("explanation_zone") or expl.get("zone")
    if zone is None:
        return
    targets.append(
        ResolveTarget(
            target_id=f"{unit_id}.explanation", unit_id=unit_id,
            role="explanation", kind="explanation_zone", zone=str(zone),
            question_number=(
                str(expl["question_number"]) if expl.get("question_number") else None
            ),
        )
    )


def extract_relations(payload: dict) -> tuple[RelationDeclaration, ...]:
    """遍历 unit 声明（composite shared_components + sub_questions depends_on）。"""
    rels: list[RelationDeclaration] = []
    for unit in payload.get("semantic_units", []):
        u_id = unit.get("unit_id") or unit.get("question_label") or "?"
        sc = unit.get("shared_components") or {}
        for key in _MATERIAL_ROLES:
            if isinstance(sc.get(key), dict):
                rels.append(
                    RelationDeclaration(u_id, f"{u_id}.{key}", "material_dependency")
                )
        for sub in _iter_sub_questions(unit):
            s_id = _sub_id(unit, sub)
            for dep in sub.get("depends_on") or []:
                if dep.get("type") == "material_dependency":
                    tgt = dep.get("target")
                    if tgt:
                        rels.append(
                            RelationDeclaration(s_id, f"{u_id}.{tgt}", "material_dependency")
                        )
    return tuple(rels)
