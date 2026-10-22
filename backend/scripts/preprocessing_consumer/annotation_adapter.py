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
        base = dict(shared.get("material") or {})
        base.update(markers)
        base.setdefault("role", "material")
        shared["material"] = base
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
    # R3: consume declared source-location windows.
    # questions_lines is the preferred stem search window (composite units).
    # stem_lines is the fallback (standalone units — same declared evidence,
    # different Producer field name). Both map to question_search_lines.
    ql = unit.questions_lines or unit.stem_lines
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
    # P0-2: pass through Producer answer_evidence (value / type / shared lines).
    # These are already determined upstream — V3 must consume, not re-guess.
    if unit.answer_evidence_value is not None:
        answer["answer_evidence_value"] = unit.answer_evidence_value
        answer["answer_value"] = unit.answer_evidence_value
    if unit.answer_evidence_type:
        answer["answer_evidence_type"] = unit.answer_evidence_type
    ael = unit.answer_evidence_lines
    if ael and len(ael) == 2 and int(ael[0]) >= 1 and int(ael[1]) >= int(ael[0]):
        answer["answer_evidence_lines"] = [int(ael[0]), int(ael[1])]
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
    # R3: also consume options_lines as options_range (declared option-search
    # window). The resolver tightens option search with this range.
    if unit.options:
        content["options"] = [
            {"role": "option", "label": opt.label}
            for opt in unit.options
        ]
    ol = unit.options_lines
    if ol and len(ol) == 2 and int(ol[0]) >= 1 and int(ol[1]) >= int(ol[0]):
        content["options_range"] = [int(ol[0]), int(ol[1])]
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


def _recover_composite_ranges(
    line_texts: list[str],
    unit: ManifestUnit,
    qns: list[int],
    q_range,
    a_range,
):
    """Validate / lightly recover declared ranges. Never rewrite a valid range.

    - questions: keep declared window when it covers all printed question
      starts; otherwise widen only to locate missing printed entries.
    - answers: KEEP the declared answer table range when it is in-bounds.
      Match answer_evidence.value with whitespace normalization against that
      window. Only if the declared window is out of range or the value cannot
      correspond at all, search for the value — and never relocate answers
      into the question area as a substitute for the answer table.
    """
    import re as _re

    def _norm(s: str) -> str:
        return _re.sub(r"\s+", "", s or "")

    n = len(line_texts)
    qs = tuple(q_range) if q_range and len(q_range) == 2 else None
    as_ = tuple(a_range) if a_range and len(a_range) == 2 else None

    def _has_all_printed(lo, hi) -> bool:
        window = "\n".join(line_texts[lo - 1:hi])
        return all(
            _re.search(
                rf"(?:^|\n)\s*{q}\s*[.．、]\s*(?![A-Ga-g](?:\s|$|[.．、,，]))",
                window,
            )
            for q in qns
        )

    if not (qs and 1 <= qs[0] <= qs[1] <= n and _has_all_printed(qs[0], qs[1])):
        lo = min([x for x in [qs[0] if qs else None,
                              unit.material_lines[0] if unit.material_lines else None,
                              unit.stem_lines[0] if unit.stem_lines else None]
                  if x] or [1])
        hi = max([x for x in [qs[1] if qs else None,
                              unit.material_lines[1] if unit.material_lines else None,
                              unit.stem_lines[1] if unit.stem_lines else None]
                  if x] or [n])
        lo = max(1, lo - 15)
        hi = min(n, hi + 8)
        if _has_all_printed(lo, hi):
            qs = (lo, hi)

    # Answer table: declared range is authoritative when in-bounds.
    ae_val = (unit.answer_evidence_value or "").strip()
    if as_ and 1 <= as_[0] <= as_[1] <= n:
        window = "\n".join(line_texts[as_[0] - 1:as_[1]])
        if not ae_val or _norm(ae_val) in _norm(window) or _norm(window) in _norm(ae_val):
            return qs, as_  # keep declared answer table line(s)
        # Value tokens (e.g. 1.C / 1. C) appear in the window after
        # whitespace normalization → still the answer table.
        toks = _re.findall(r"(\d+)\s*[.．]?\s*([A-Za-z][A-Za-z0-9]*)", ae_val)
        if toks and all(
            _norm(f"{a}.{b}") in _norm(window) or _norm(f"{a}{b}") in _norm(window)
            for a, b in toks
        ):
            return qs, as_
        # Declared window is in-bounds but value does not correspond.
        # Do NOT relocate into the question area; keep the declared table
        # and let expand / incomplete reporting handle mismatch.
        return qs, as_

    # Declared answer range missing/out-of-bounds: search for value text.
    if ae_val:
        target = _norm(ae_val)
        for i, line in enumerate(line_texts, 1):
            if target and target in _norm(line):
                return qs, (i, i)
        toks = _re.findall(r"(\d+)\s*[.．]?\s*([A-Za-z][A-Za-z0-9]*)", ae_val)
        if toks:
            for i, line in enumerate(line_texts, 1):
                nl = _norm(line)
                if all(_norm(f"{a}.{b}") in nl or _norm(f"{a}{b}") in nl for a, b in toks):
                    return qs, (i, i)
    return qs, as_

def _build_composite(
    unit: ManifestUnit, norm: NormalizedUnitType,
    line_texts: list[str] | None = None,
) -> tuple[dict, list[dict]]:
    """composite 形态 → V3 composite_unit。

    产品定义：综合题整体 = 一道 Question；子题是**内部有序结构**，不是独立
    Question。多题号 composite 用生产端 expand_composite_sub_questions 展开
    真实子题（各自题干/选项/答案），父节点仍是唯一 Question 身份。
    展开失败/单题号 → 父节点 content 为本体，不制造伪子题。
    """
    shared: dict = {}
    if unit.material_lines:
        shared["material"] = {
            "role": "material",
            "evidence_lines": [int(unit.material_lines[0]), int(unit.material_lines[1])],
        }

    gaps = _unit_gaps(unit, norm.canonical_unit_type)
    qns = list(unit.question_numbers or [])
    parent = {
        "unit_id": unit.unit_id,
        "unit_type": norm.canonical_unit_type,
        "question_number": _qn(unit),
        "question_number_range": (
            f"{qns[0]}-{qns[-1]}" if len(qns) > 1 else None
        ),
        "original_question_type": unit.original_question_type,
        "content": {},
        "shared_components": shared,
        "sub_questions": [],
    }

    # Multi-q composite: real ordered internal sub_questions (GEO U1-2 etc.)
    # P0: answer_evidence.value must cover declared question_numbers AND
    # correspond to the answer window. Mismatch → no expand, incomplete.
    a_range = unit.answer_lines or unit.answer_evidence_lines
    q_range = unit.questions_lines or unit.stem_lines
    # Shared P0 gate (same rule as Formal Binder).
    if line_texts and len(qns) > 1:
        from app.domains.source.subq_expand import answer_evidence_mismatches
        mismatch = answer_evidence_mismatches(
            unit.answer_evidence_value, qns, list(line_texts),
            tuple(a_range) if a_range and len(a_range) == 2 else None,
        )
        if mismatch:
            gaps.append({
                "code": "COMPOSITE_ANSWER_EVIDENCE_MISMATCH",
                "unit_id": unit.unit_id,
                "detail": mismatch,
            })
            return parent, gaps
    if line_texts and len(qns) > 1:
        try:
            from app.domains.source.subq_expand import (
                expand_composite_sub_questions,
                specs_to_payload_subs,
            )
            q_range = unit.questions_lines or unit.stem_lines
            a_range = unit.answer_lines or unit.answer_evidence_lines
            # Recover evidence windows when declared ranges miss declared
            # question_numbers / answer value (Producer range drift). Not a
            # silent clamp: we re-locate by printed entry / value text.
            q_range, a_range = _recover_composite_ranges(
                line_texts, unit, qns, q_range, a_range
            )
            result = expand_composite_sub_questions(
                list(line_texts),
                question_numbers=qns,
                questions_range=tuple(q_range) if q_range else None,
                answer_range=tuple(a_range) if a_range else None,
                original_question_type=unit.original_question_type,
                has_declared_options=bool(unit.options),
            )
            if result.sub_questions:
                parent["sub_questions"] = specs_to_payload_subs(
                    unit.unit_id,
                    result.sub_questions,
                    original_question_type=unit.original_question_type,
                )
                if result.skipped:
                    gaps.append({
                        "code": "COMPOSITE_SUB_EXPAND_PARTIAL",
                        "unit_id": unit.unit_id,
                        "detail": f"skipped question_numbers: {result.skipped}",
                    })
                return parent, gaps
        except Exception as exc:  # noqa: BLE001
            gaps.append({
                "code": "COMPOSITE_SUB_EXPAND_FAILED",
                "unit_id": unit.unit_id,
                "detail": f"{type(exc).__name__}: {exc}",
            })

    # Single-q or expand unavailable: parent content is the Question body.
    parent["content"] = _leaf_content(unit)
    return parent, gaps

def manifest_to_annotation_payload(manifest: Manifest, line_texts: list[str] | None = None) -> dict:
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
            payload_unit, gaps = _build_composite(unit, norm, line_texts=line_texts)
        else:
            payload_unit, gaps = _build_standalone(unit, norm)

        semantic_units.append(payload_unit)
        known_gaps.extend(gaps)

    return {
        "document_metadata_claims": {
            # Producer manifest 权威映射；缺失 → None（unknown）。
            # 此前硬编码 None 会静默清空 manifest 已有值（触碰底线 2）。
            "subject": manifest.subject,
            "grade": manifest.grade,
            "year": None,
            "school": None,
            "grade_source": manifest.grade_source,
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
