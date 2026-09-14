"""Annotation adapter: manifest → V3 SemanticAnnotation payload。

把 preprocessing manifest 的 units 转成 V3 annotation 的 semantic_units 格式。
V3 禁止 payload 含 line_refs，所以只转角色声明，不含行号。

关键格式要求（V3 IRBuilder）：
- standalone: content.{stem,answer,explanation} 为 dict；content.options 为 [{label,...}]
- composite: shared_components.{material} + sub_questions[]（每个子题独立 unit）
"""

from .manifest_reader import Manifest, ManifestUnit


_OPTION_LABELS = ["A", "B", "C", "D", "E", "F"]
_CHOICE_TYPES = {"single_choice", "multiple_choice", "true_false"}


def _qn(unit: ManifestUnit) -> str:
    return str(unit.question_numbers[0]) if unit.question_numbers else ""


def _build_standalone(unit: ManifestUnit) -> dict:
    """standalone_question 的 semantic_unit dict。"""
    content: dict = {}
    content["stem"] = {"role": "stem", "question_label": _qn(unit)}
    content["answer"] = {
        "role": "answer",
        "question_label": _qn(unit),
        "answer_zone": "answer_table",
    }
    if unit.explanation_lines:
        content["explanation"] = {
            "role": "explanation",
            "explanation_zone": "inline_explanation",
        }
    # options: 选择题需要 per-label 声明（IRBuilder 按 label 查 span）
    if unit.options_lines and unit.original_question_type in _CHOICE_TYPES:
        content["options"] = [
            {"label": lbl, "role": "option", "question_label": _qn(unit)}
            for lbl in _OPTION_LABELS[:4]
        ]
    return {
        "unit_id": unit.unit_id,
        "unit_type": "standalone_question",
        "question_number": _qn(unit),
        "original_question_type": unit.original_question_type,
        "content": content,
    }


def _build_composite(unit: ManifestUnit) -> dict:
    """composite_question → V3 composite_unit 格式。

    preprocessing 的 composite 是一个原子单元（material + questions + answer）。
    V3 的 composite_unit 需要 shared_components + sub_questions。
    这里把 material 放 shared_components，把整块 questions 作为单个子题。
    """
    shared: dict = {}
    if unit.material_lines:
        shared["material"] = {"role": "material"}

    # 子题：preprocessing 不拆子题，把整个 questions 区域作为一个子题
    sub_content: dict = {
        "stem": {"role": "stem", "question_label": _qn(unit)},
        "answer": {
            "role": "answer",
            "question_label": _qn(unit),
            "answer_zone": "answer_table",
        },
    }
    if unit.explanation_lines:
        sub_content["explanation"] = {
            "role": "explanation",
            "explanation_zone": "inline_explanation",
        }

    sub = {
        "unit_id": f"{unit.unit_id}.sub",
        "unit_type": "standalone_question",
        "question_number": _qn(unit),
        "original_question_type": unit.original_question_type,
        "content": sub_content,
    }

    return {
        "unit_id": unit.unit_id,
        "unit_type": "composite_unit",
        "question_number_range": (
            f"{unit.question_numbers[0]}-{unit.question_numbers[-1]}"
            if len(unit.question_numbers) > 1
            else None
        ),
        "original_question_type": unit.original_question_type,
        "shared_components": shared,
        "sub_questions": [sub],
    }


def manifest_to_annotation_payload(manifest: Manifest) -> dict:
    """把 preprocessing manifest 转成 V3 annotation payload。"""
    semantic_units = []
    for unit in manifest.units:
        if unit.unit_type == "composite_question":
            semantic_units.append(_build_composite(unit))
        else:
            semantic_units.append(_build_standalone(unit))

    return {
        "document_metadata_claims": {
            "subject": None,
            "grade": None,
            "year": None,
            "school": None,
        },
        "sections": [],
        "semantic_units": semantic_units,
    }
