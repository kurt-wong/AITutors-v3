"""Annotation adapter: manifest → V3 SemanticAnnotation payload。

把 preprocessing manifest 的 units 转成 V3 annotation 的 semantic_units 格式。

【集成边界归一化 · X2.6】Producer legacy vocabulary 在本层被**确定性**归一化为
canonical V3/X Unit Type（仅 OD-2 授权的两条映射）。canonical runtime 结构
（`semantic_units`）**只允许**出现 canonical Unit Type；Producer 原值以 legacy
evidence 形式保存在 payload 顶层 `producer_boundary`，供血缘追溯
（UQ-01 Decision 7：Preserve legacy value / Introduce canonical value——
不做破坏性全局替换，不改写 corpus 或 manifest）。

**这是 boundary normalization rule，不是 Question-Type→Unit-Type mapping。**
Question Type 与 Unit Type 正交；本模块**从不**由 `original_question_type`
推导 `unit_type`（Owner D1 / 10 §5.2）。

禁止（X2.6 task §13 No Silent Repair）——已消除的历史 wash 路径：

- ~~unknown unit_type → else 分支静默 wash 为 standalone~~（原 P1，已消除）
- ~~输出词表硬编码 `"standalone_question"`~~（原 P2，已消除）

现在：任何无法归一化的 Producer 值 → `BoundaryViolation` 显式失败，不默认、
不 fallback、不静默 skip、不猜。

结构派发依据 = **声明并归一化后的 unit type**，不是结构形态推断
（X2.5.2 行为分类法：本层为 Class A explicit mapping，非 Class C）。

关键格式要求（V3 IRBuilder）：
- standalone: content.{stem,answer,explanation} 为 dict；content.options 为 [{label,...}]
- composite: shared_components.{material} + sub_questions[]（每个子题独立 unit）
"""

from .boundary import BoundaryViolation, NormalizedUnitType, normalize_unit_type
from .manifest_reader import Manifest, ManifestUnit

_CHOICE_TYPES = {"single_choice", "multiple_choice", "true_false"}

# 已知 gap 码（显式登记，不静默吞掉；对应 Frozen Contract / UQ-06 的开放项）。
GAP_SUB_QUESTION_DECOMPOSITION = "SUB_QUESTION_DECOMPOSITION_UNAVAILABLE"
GAP_STANDALONE_MATERIAL_NOT_CONSUMED = "STANDALONE_MATERIAL_NOT_CONSUMED"
GAP_OPTION_LABEL_SPAN_UNAVAILABLE = "OPTION_LABEL_SPAN_UNAVAILABLE"

# Producer 不拆子题（material + questions + answer 是原子块）。V3 composite_unit
# 要求 sub_questions 结构，故 questions 区间做 1:1 结构翻译为单个子题。
# 这是确定性结构翻译，**不是**语义拆分猜测——显式登记于 known_gaps。
_SUB_DECOMPOSITION = "producer_region_as_single_sub"


def _qn(unit: ManifestUnit) -> str:
    return str(unit.question_numbers[0]) if unit.question_numbers else ""


def _leaf_content(unit: ManifestUnit) -> dict:
    """leaf 级 content role 声明（只声明 role，不携带正文；不补、不猜）。"""
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
    # options: per-label declaration when producer provides per-option spans.
    # Fall back to gap registration when only options_lines range is available.
    if unit.options:
        content["options"] = [
            {"role": "option", "label": opt.label}
            for opt in unit.options
        ]
    return content


def _unit_gaps(unit: ManifestUnit, canonical_unit_type: str) -> list[dict]:
    """收集该单元的已知证据粒度/消费策略 gap（显式登记，非静默丢弃）。"""
    gaps: list[dict] = []
    if canonical_unit_type == "standalone_unit" and unit.material_lines:
        # 领域事实：standalone **可以**有 material（UQ-06 §1.4）。
        # 消费策略：当前 Gate 对 standalone 产 materials=()（CL-22 OPEN，
        # OD-BLOCK-02 未裁，implementation authorized = NONE）。
        # 因此显式登记「未消费」，**不得**记为「standalone 无 material」。
        gaps.append({
            "code": GAP_STANDALONE_MATERIAL_NOT_CONSUMED,
            "unit_id": unit.unit_id,
            "detail": (
                "standalone_unit declares material_lines, but V3 compiler/gate does not "
                "consume standalone materials (CL-22 OPEN / OD-BLOCK-02). "
                "Declared material is preserved as a fact and explicitly reported here; "
                "it is NOT evidence that standalone units have no material."
            ),
        })
    if unit.original_question_type in _CHOICE_TYPES and unit.options_lines and not unit.options:
        gaps.append({
            "code": GAP_OPTION_LABEL_SPAN_UNAVAILABLE,
            "unit_id": unit.unit_id,
            "detail": (
                "preprocessing exposes options_lines as a single line range, not per-label "
                "spans (sp-<unit>.option.<label>). V3 IRBuilder requires per-label spans, "
                "so options cannot be declared without fabricating evidence."
            ),
        })
    return gaps


def _build_standalone(
    unit: ManifestUnit, norm: NormalizedUnitType
) -> tuple[dict, list[dict]]:
    """standalone 形态的 semantic_unit dict（unit_type = canonical）。"""
    return {
        "unit_id": unit.unit_id,
        "unit_type": norm.canonical_unit_type,
        "question_number": _qn(unit),
        "original_question_type": unit.original_question_type,
        "content": _leaf_content(unit),
    }, _unit_gaps(unit, norm.canonical_unit_type)


def _build_composite(
    unit: ManifestUnit, norm: NormalizedUnitType
) -> tuple[dict, list[dict]]:
    """composite 形态 → V3 composite_unit（shared_components + sub_questions）。

    preprocessing 的 composite 是一个原子单元（material + questions + answer）。
    V3 的 composite_unit 需要 shared_components + sub_questions。
    这里把 material 放 shared_components，把整块 questions 区间 1:1 译为单个子题
    （确定性结构翻译；Producer 无子题拆分证据，不猜拆分）。
    """
    shared: dict = {}
    if unit.material_lines:
        shared["material"] = {"role": "material"}

    sub = {
        "unit_id": f"{unit.unit_id}.sub",
        "unit_type": "standalone_unit",
        "question_number": _qn(unit),
        "original_question_type": unit.original_question_type,
        "content": _leaf_content(unit),
    }

    gaps = _unit_gaps(unit, norm.canonical_unit_type)
    gaps.append({
        "code": GAP_SUB_QUESTION_DECOMPOSITION,
        "unit_id": unit.unit_id,
        "detail": (
            f"preprocessing does not decompose sub-questions; the single questions "
            f"region is translated 1:1 into one sub-question ({_SUB_DECOMPOSITION}). "
            f"No sub-question boundaries are invented."
        ),
    })

    return {
        "unit_id": unit.unit_id,
        "unit_type": norm.canonical_unit_type,
        "question_number_range": (
            f"{unit.question_numbers[0]}-{unit.question_numbers[-1]}"
            if len(unit.question_numbers) > 1
            else None
        ),
        "original_question_type": unit.original_question_type,
        "shared_components": shared,
        "sub_questions": [sub],
    }, gaps


def manifest_to_annotation_payload(manifest: Manifest) -> dict:
    """把 preprocessing manifest 转成 V3 annotation payload。

    归一化失败（含 legacy 噪声如 `andalone_question`）→ `BoundaryViolation`
    上抛；**不**产出部分 payload。
    """
    semantic_units = []
    normalizations: list[dict] = []
    known_gaps: list[dict] = []

    for unit in manifest.units:
        # 显式归一化（Class A）。失败即整份 manifest 边界违规，不做 per-unit 洗白。
        norm = normalize_unit_type(unit.unit_type)
        normalizations.append({
            "unit_id": unit.unit_id,
            "producer_unit_type": norm.producer_unit_type,
            "canonical_unit_type": norm.canonical_unit_type,
            "normalization_event_id": norm.normalization_event_id,
            "already_canonical": norm.already_canonical,
        })

        if norm.canonical_unit_type == "composite_unit":
            payload_unit, gaps = _build_composite(unit, norm)
        else:
            payload_unit, gaps = _build_standalone(unit, norm)

        semantic_units.append(payload_unit)
        known_gaps.extend(gaps)

    return {
        "document_metadata_claims": {
            "subject": None,
            "grade": None,
            "year": None,
            "school": None,
        },
        "sections": [],
        "semantic_units": semantic_units,
        # legacy evidence only — 不进入 canonical runtime 结构（IRBuilder 只读
        # semantic_units）。UQ-01 Decision 7: Preserve legacy value.
        "producer_boundary": {
            "normalization_rule": (
                "legacy Producer vocabulary -> canonical V3/X Unit Type "
                "(boundary normalization; NOT a Question-Type->Unit-Type mapping)"
            ),
            "authority": (
                "Owner OD-2: X2.6-OD-2-MAP-STANDALONE-01 / "
                "X2.6-OD-2-MAP-COMPOSITE-01"
            ),
            "unit_normalizations": normalizations,
            "known_gaps": known_gaps,
        },
    }


__all__ = [
    "BoundaryViolation",
    "GAP_OPTION_LABEL_SPAN_UNAVAILABLE",
    "GAP_STANDALONE_MATERIAL_NOT_CONSUMED",
    "GAP_SUB_QUESTION_DECOMPOSITION",
    "manifest_to_annotation_payload",
]
