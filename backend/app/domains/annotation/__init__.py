"""Annotation Stage 域（段 D，20 §4）：forbidden-field 校验 + LE 常量。

validate_annotation_payload 只做 20 §4.3 明确冻结的递归禁字段检查
（P1-a：不加 required / enum / type coercion / unknown-field rejection / 结构约束）。
"""

FORBIDDEN_FIELDS = frozenset(
    {
        "line_refs",
        "corrected_line_ids",
        "resolved_span",
        "final_line_ids",
        "canonical_question_type",
        "answer_text",
        "stem_text",
        "material_text",
        "options_text",
        "explanation_text",
    }
)

ANNO_SCHEMA_VERSION = "semantic-metadata-annotation/v0.3"
ANN_PROMPT_VERSION = "semantic-annotation/v1"


def validate_annotation_payload(
    payload: dict,
) -> tuple[bool, list[str]]:
    """20 §4.3 递归禁字段检查：任意深度出现禁字段 → (False, violations)。

    violations 为完整路径列表（如 "sections[0].semantic_units[0].stem_text"）。
    只做 Frozen Spec 明确冻结的禁字段检查，不自行扩大。

    H-2（BUG-V3-030）：顶层必须为 JSON object/dict；非 dict（[]/null/"str"/数字）是结构违规
    （非「禁字段」），同属 validation failure → 不落 valid artifact（方案 B 失败路径）。
    """
    if not isinstance(payload, dict):
        return (False, [f"payload must be a JSON object, got {type(payload).__name__}"])
    violations: list[str] = []
    _walk(payload, "", violations)
    return (not violations, violations)


def _walk(obj: object, path: str, violations: list[str]) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            child = f"{path}.{key}" if path else key
            if key in FORBIDDEN_FIELDS:
                violations.append(child)
            _walk(val, child, violations)
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            _walk(val, f"{path}[{i}]", violations)
