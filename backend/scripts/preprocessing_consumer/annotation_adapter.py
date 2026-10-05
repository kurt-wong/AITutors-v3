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


def _text_occurrence_count(line_texts: list[str], text: str) -> int:
    return sum(1 for t in line_texts if t == text)


def _nearest_unique_nonempty(
    line_texts: list[str],
    start_no: int,
    *,
    forward: bool,
    limit: int = 12,
    min_no: int | None = None,
    max_no: int | None = None,
) -> tuple[int, str] | None:
    """Walk outward for a non-empty line whose text is UNIQUE in the document.

    Duplicate marker text lets SourceResolver land on the wrong occurrence
    (span explosion). If a line's text occurs more than once we skip it;
    if no unique delimiter is found we return None (leave unresolved)
    rather than emit an ambiguous marker.

    min_no / max_no: hard scope bounds (1-based inclusive). The walk never
    leaves this window — neighbours' declared material ranges must not be
    entered (English listening blocks sit adjacent and their duplicated
    section headers force the unbounded walk into the neighbour).
    """
    n = len(line_texts)
    step = 1 if forward else -1
    lo = min_no if min_no is not None else 1
    hi = max_no if max_no is not None else n
    no = start_no
    # Clamp the walk origin into the legal window before stepping.
    if no > hi:
        no = hi
    if no < lo:
        no = lo
    for _ in range(limit):
        if no < lo or no > hi or no < 1 or no > n:
            return None
        text = line_texts[no - 1]
        if text and text.strip() and _text_occurrence_count(line_texts, text) == 1:
            return no, text
        no += step
    return None


def _unique_in_range(
    line_texts: list[str],
    lo: int,
    hi: int,
    *,
    from_end: bool = False,
) -> tuple[int, str] | None:
    """First/last unique non-empty line inside [lo, hi] (1-based inclusive)."""
    if lo > hi:
        return None
    span = range(hi, lo - 1, -1) if from_end else range(lo, hi + 1)
    for no in span:
        text = line_texts[no - 1]
        if text and text.strip() and _text_occurrence_count(line_texts, text) == 1:
            return no, text
    return None


def material_boundary_markers(
    material_lines: tuple[int, int] | list[int],
    line_texts: list[str],
    *,
    neighbour_bounds: tuple[int, int] | None = None,
) -> dict | None:
    """Producer inclusive material_lines → resolver multi_line_pair boundary markers.

    Producer `material_lines=[s,e]` is INCLUSIVE content. Resolver multi_line_pair
    interior is EXCLUSIVE of marker lines.

    Rules (duplicate-marker / span-explosion guard):
    - N=1: single-marker on the content line itself when its text is UNIQUE
      (resolver default path yields exactly that one line).
    - N>=2: unique-text delimiters strictly outside [s,e]; reject if padding
      would exceed one line per side (prevents inflation drift).
    - Never emit ambiguous (non-unique) marker text — leave unresolved instead.
    - neighbour_bounds=(prev_end, next_start): anchor search must not enter
      another unit's declared material range. prev_end = end line of the
      nearest previous material (0 if none); next_start = start line of the
      nearest next material (len+1 if none). Start anchor ≥ prev_end,
      end anchor ≤ next_start (shared boundary lines allowed).
    - Fallback when a side has no unique line in scope: tighten BOTH anchors
      to the first/last unique lines inside [s,e]. Keeps the span
      non-overlapping and free of neighbour/section pollution; loses at most
      the non-unique edge lines of the block.
    """
    if not material_lines or len(material_lines) != 2:
        return None
    s, e = int(material_lines[0]), int(material_lines[1])
    if s < 1 or e > len(line_texts) or s > e:
        return None

    if s == e:
        text = line_texts[s - 1]
        if not text or not text.strip():
            return None
        if _text_occurrence_count(line_texts, text) != 1:
            return None
        return {"role": "material", "start_marker": {"text": text}}

    # Scope: never enter a neighbour's declared material range.
    prev_end = 0
    next_start = len(line_texts) + 1
    if neighbour_bounds is not None:
        prev_end = int(neighbour_bounds[0]) if neighbour_bounds[0] is not None else 0
        next_start = (
            int(neighbour_bounds[1]) if neighbour_bounds[1] is not None
            else len(line_texts) + 1
        )
    # Anchor windows (shared boundary lines are legal):
    #   start ∈ [prev_end, s-1]   end ∈ [e+1, next_start]
    start_lo = max(prev_end, 1)
    start_hi = s - 1
    end_lo = e + 1
    end_hi = min(next_start, len(line_texts))

    start = (
        _nearest_unique_nonempty(
            line_texts, s - 1, forward=False, limit=8,
            min_no=start_lo, max_no=start_hi,
        )
        if start_hi >= start_lo else None
    )
    end = (
        _nearest_unique_nonempty(
            line_texts, e + 1, forward=True, limit=8,
            min_no=end_lo, max_no=end_hi,
        )
        if end_hi >= end_lo else None
    )

    if not start or not end:
        # Deterministic fallback: replace only the missing side(s) with the
        # first/last unique line inside [s,e]. Keeps the pair non-overlapping
        # with neighbours; loses at most the non-unique edge lines of the block.
        if not start:
            start = _unique_in_range(line_texts, s, e, from_end=False)
        if not end:
            end = _unique_in_range(line_texts, s, e, from_end=True)
        if not start or not end or start[0] >= end[0]:
            return None
        # Fallback pair: interior must be non-empty. Adjacent unique edges of a
        # 2-line block leave no interior — reject rather than emit a broken pair.
        if start[0] >= e and end[0] <= s:
            return None
        interior_n = (end[0] - 1) - (start[0] + 1) + 1
        if interior_n < 1:
            # last resort: single-marker on a unique in-block line (N=1 form)
            solo = _unique_in_range(line_texts, s, e, from_end=False)
            if solo:
                return {"role": "material", "start_marker": {"text": solo[1]}}
            return None
        return {
            "role": "material",
            "start_marker": {"granularity": "multi_line_pair", "text": start[1]},
            "end_marker": {"text": end[1]},
        }

    if end[0] <= start[0] + 1:
        return None
    # interior must cover [s,e]; extra edge lines are blank/separator padding
    # that Fourth-cut A trims after resolver forms the raw interior.
    interior_n = (end[0] - 1) - (start[0] + 1) + 1
    if interior_n < (e - s + 1) or interior_n > (e - s + 1) + 12:
        return None
    return {
        "role": "material",
        "start_marker": {"granularity": "multi_line_pair", "text": start[1]},
        "end_marker": {"text": end[1]},
    }


def attach_material_boundary_markers(
    payload: dict,
    material_lines_by_unit: dict,
    line_texts: list[str],
) -> dict:
    """Attach boundary markers onto composite shared_components.material.

    `material_lines_by_unit`: unit_id → (start, end) inclusive Producer range.
    Only fills material declarations that lack start_marker (idempotent).
    Records explicit gaps when a boundary marker cannot be formed.

    Neighbour scope: for each unit, start/end anchors must not enter another
    unit's declared material range (see material_boundary_markers).
    """
    gaps = payload.setdefault("producer_boundary", {})
    known = gaps.setdefault("known_gaps", []) if isinstance(gaps, dict) else []

    # All declared material ranges for neighbour-scope computation.
    ranges: list[tuple[int, int, str]] = []
    for uid, ml in (material_lines_by_unit or {}).items():
        if not ml or len(ml) != 2:
            continue
        try:
            s, e = int(ml[0]), int(ml[1])
        except (TypeError, ValueError):
            continue
        if s >= 1 and e >= s:
            ranges.append((s, e, uid))
    ranges.sort(key=lambda t: t[0])

    def _neighbour_bounds(uid: str, s: int, e: int) -> tuple[int, int]:
        prev_end = 0
        next_start = len(line_texts) + 1
        for rs, re, rid in ranges:
            if rid == uid:
                continue
            # nearest previous material that ends at/before this start
            if re < s and re > prev_end:
                prev_end = re
            # nearest next material that starts at/after this end
            if rs > e and rs < next_start:
                next_start = rs
        return prev_end, next_start

    for unit in payload.get("semantic_units") or []:
        if unit.get("unit_type") != "composite_unit":
            continue
        uid = unit.get("unit_id")
        shared = unit.setdefault("shared_components", {})
        mat = shared.get("material")
        if not isinstance(mat, dict):
            continue
        if mat.get("start_marker") and mat.get("end_marker"):
            continue
        ml = material_lines_by_unit.get(uid)
        if not ml:
            continue
        s, e = int(ml[0]), int(ml[1])
        markers = material_boundary_markers(
            ml, line_texts,
            neighbour_bounds=_neighbour_bounds(uid, s, e),
        )
        if markers is None:
            known.append({
                "code": "MATERIAL_BOUNDARY_MARKER_UNAVAILABLE",
                "unit_id": uid,
                "detail": (
                    f"material_lines={list(ml)} cannot be mapped to multi_line_pair "
                    f"boundary markers (missing/empty delimiter line outside inclusive range)"
                ),
            })
            continue
        shared["material"] = markers
    return payload


def _printed_qn(unit: ManifestUnit) -> str | None:
    """Producer printed_number → source-entry form (str). list/int/str 皆可。

    printed_number 是源文印刷题号（identity evidence，printed_provenance 标明
    来源）；question_numbers 是入库全局身份。二者不同时，Resolver 查源必须用
    printed form，IR 仍保留 question_numbers。不猜、不按顺序映射。
    """
    pn = unit.printed_number
    if pn is None:
        return None
    if isinstance(pn, (list, tuple)):
        if not pn:
            return None
        pn = pn[0]
    s = str(pn).strip()
    return s or None


def _leaf_content(unit: ManifestUnit) -> dict:
    """leaf 级 content role 声明（只声明 role，不携带正文；不补、不猜）。"""
    content: dict = {}
    stem = {"role": "stem", "question_label": _qn(unit)}
    # Question-identity evidence transport（B3c-A 同模式）：
    # printed_number = 源文入口题号；questions_lines = 查源窗口。
    # 二者均为 Producer 已声明事实，本层原样保留，不推导映射。
    printed = _printed_qn(unit)
    if printed is not None:
        stem["question_label_printed"] = printed
    ql = unit.questions_lines
    if ql and len(ql) == 2 and int(ql[0]) >= 1 and int(ql[1]) >= int(ql[0]):
        stem["question_search_lines"] = [int(ql[0]), int(ql[1])]
    content["stem"] = stem
    answer = {
        "role": "answer",
        "question_label": _qn(unit),
        "answer_zone": "answer_table",
    }
    # B3c-A evidence transport: Producer inclusive answer_lines is the
    # authoritative answer-evidence range. Previously dropped here, forcing
    # Resolver to re-scan the whole answer_zone (defects A/C). Preserve it
    # verbatim as a [start, end] pair (answer_evidence_lines = v2.4+ fallback,
    # same precedence as Track B runner_b2._answer_span).
    al = unit.answer_lines or unit.answer_evidence_lines
    if al and len(al) == 2 and int(al[0]) >= 1 and int(al[1]) >= int(al[0]):
        answer["answer_lines"] = [int(al[0]), int(al[1])]
    content["answer"] = answer
    if unit.explanation_lines:
        expl = {
            "role": "explanation",
            "explanation_zone": "inline_explanation",
        }
        # Existing Producer mechanism (same evidence-transport as answer_lines):
        # ManifestUnit.explanation_lines is the declared explanation-evidence
        # range. Track B already consumes it (resolved_span_adapter). Dropping
        # it forced _explanation_span to re-scan from the first 【解析】 to EOF.
        xl = unit.explanation_lines
        if len(xl) == 2 and int(xl[0]) >= 1 and int(xl[1]) >= int(xl[0]):
            expl["explanation_lines"] = [int(xl[0]), int(xl[1])]
        content["explanation"] = expl
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
