"""Manifest-driven Annotation input (M2-R2): Producer units are authoritative.

Formal-path module. Unit boundaries and unit_id come from the accepted
preprocessing manifest — LLM must not re-split the document or renumber units.

Identity:
  - unit_id is a display alias (Producer's), not a cross-system identity key
  - provenance binds: source_version_id + manifest source_content_sha256 +
    Producer unit_id + declared line ranges + bound text hash
  - occurrence_key stays on existing contracts (no new identity rules)

Fail-closed: out-of-range / inverted / missing line bounds reject the unit
(or the whole payload) with an explicit reason. Never silent repair.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Reuse sole authority for unit-type normalization (production module).
from app.domains.source.identity_scope import BoundaryViolation  # noqa: F401


class ManifestBindingError(Exception):
    """Manifest unit binding failed (range/identity). Explicit fail-closed."""

    def __init__(self, reason: str, *, unit_id: str | None = None) -> None:
        super().__init__(reason if unit_id is None else f"[{unit_id}] {reason}")
        self.reason = reason
        self.unit_id = unit_id


@dataclass(frozen=True)
class LineRange:
    start: int
    end: int

    def validate(self, line_count: int, *, label: str, unit_id: str) -> None:
        if self.start < 1 or self.end < self.start:
            raise ManifestBindingError(
                f"{label} range inverted/out-of-bounds: [{self.start},{self.end}]",
                unit_id=unit_id,
            )
        if self.end > line_count:
            raise ManifestBindingError(
                f"{label} range [{self.start},{self.end}] exceeds line_count={line_count}",
                unit_id=unit_id,
            )


@dataclass
class BoundUnit:
    unit_id: str
    unit_type: str  # producer vocabulary (normalized later)
    question_numbers: list[int]
    original_question_type: str
    ranges: dict[str, LineRange | None]
    bound_text: str
    bound_text_hash: str
    section: str | None = None
    printed_number: str | None = None
    # GEO-SUBQ: deterministic per-question expansion (payload-ready sub entries).
    # Empty when not expandable — never a fake single-question over a multi-q range.
    sub_questions: list[dict] = field(default_factory=list)
    subq_skipped: dict[int, str] = field(default_factory=dict)
    subq_unit_reason: str | None = None
    # material marker dict for shared_components (resolver needs marker text).
    material_shared: dict = field(default_factory=dict)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _as_range(raw: Any, *, label: str, unit_id: str) -> LineRange | None:
    if raw is None:
        return None
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        raise ManifestBindingError(
            f"{label} must be [start,end] pair, got {raw!r}", unit_id=unit_id
        )
    try:
        start, end = int(raw[0]), int(raw[1])
    except (TypeError, ValueError) as exc:
        raise ManifestBindingError(
            f"{label} non-integer bounds: {raw!r}", unit_id=unit_id
        ) from exc
    return LineRange(start=start, end=end)


def bind_units_from_manifest(
    manifest: dict,
    source_lines: list[str],
    *,
    source_content_sha256: str,
) -> list[BoundUnit]:
    """Bind every manifest unit to source lines. Fail-closed on any bad range."""
    units_raw = manifest.get("units")
    if not isinstance(units_raw, list) or not units_raw:
        raise ManifestBindingError("manifest has no units[]")

    line_count = len(source_lines)
    bound: list[BoundUnit] = []
    seen_ids: set[str] = set()

    for raw in units_raw:
        if not isinstance(raw, dict):
            raise ManifestBindingError("unit entry must be object")
        unit_id = str(raw.get("unit_id") or "").strip()
        if not unit_id:
            raise ManifestBindingError("unit_id missing")
        if unit_id in seen_ids:
            raise ManifestBindingError("duplicate unit_id", unit_id=unit_id)
        seen_ids.add(unit_id)

        ranges = {
            # stem：无 stem_lines 时用 questions_lines（composite 题干窗，Producer 已声明）
            "stem": _as_range(
                raw.get("stem_lines") or raw.get("questions_lines"),
                label="stem_lines",
                unit_id=unit_id,
            ),
            "options": _as_range(
                raw.get("options_lines"), label="options_lines", unit_id=unit_id
            ),
            "answer": _as_range(
                raw.get("answer_lines"), label="answer_lines", unit_id=unit_id
            ),
            "explanation": _as_range(
                raw.get("explanation_lines"), label="explanation_lines", unit_id=unit_id
            ),
            "material": _as_range(
                raw.get("material_lines"), label="material_lines", unit_id=unit_id
            ),
        }
        for label, rng in ranges.items():
            if rng is not None:
                rng.validate(line_count, label=label, unit_id=unit_id)

        # Bound text = union of declared ranges (inclusive), in document order.
        covered: set[int] = set()
        for rng in ranges.values():
            if rng is None:
                continue
            for n in range(rng.start, rng.end + 1):
                covered.add(n)
        if not covered:
            raise ManifestBindingError("no declared line range to bind", unit_id=unit_id)

        lines_slice = [source_lines[n - 1] for n in sorted(covered)]
        bound_text = "\n".join(lines_slice)
        qn_raw = raw.get("question_numbers") or []
        qns = [int(x) for x in qn_raw] if isinstance(qn_raw, (list, tuple)) else []
        printed = raw.get("printed_number")
        printed_label = None
        if isinstance(printed, (list, tuple)) and printed:
            printed_label = str(printed[0])
        elif printed is not None:
            printed_label = str(printed)

        bound.append(
            BoundUnit(
                unit_id=unit_id,
                unit_type=str(raw.get("unit_type") or ""),
                question_numbers=qns,
                original_question_type=str(raw.get("original_question_type") or ""),
                ranges=ranges,
                bound_text=bound_text,
                bound_text_hash=_sha256_text(bound_text),
                section=raw.get("section"),
                printed_number=printed_label,
            )
        )
        # GEO-SUBQ: deterministic sub-question expansion (fail-closed per sub).
        _expand_subs(bound[-1], source_lines)
        _bind_material_marker(bound[-1], source_lines)

    return bound


def _bind_material_marker(bu: "BoundUnit", source_lines: list[str]) -> None:
    """Declare resolver-locatable marker text for shared material.

    Resolver's _material_span resolves a marker text to a line span. For
    multi-line material, multi_line_pair takes the EXCLUSIVE interior (markers
    themselves are excluded) — wrong for inclusive manifest ranges. Use the
    first non-empty material line as a single-line marker instead: the shared
    component then resolves deterministically without inventing boundaries.
    """
    rng = bu.ranges.get("material")
    if rng is None:
        return
    n = len(source_lines)
    for i in range(rng.start, rng.end + 1):
        if 1 <= i <= n:
            text = source_lines[i - 1].strip()
            if text:
                bu.material_shared = {
                    "role": "material",
                    "start_marker": {"text": text, "granularity": "line"},
                }
                return


def _expand_subs(bu: "BoundUnit", source_lines: list[str]) -> None:
    """Attach deterministic sub_questions to a multi-q composite BoundUnit.

    Only proven structure (题号→题干→A-D→答案表) is emitted; anything ambiguous
    is skipped per question. short_answer / non-choice stays unexpanded.
    """
    from app.domains.source.subq_expand import (
        expand_composite_sub_questions,
        specs_to_payload_subs,
    )

    q_range = None
    if bu.ranges.get("stem") is not None:
        q_range = (bu.ranges["stem"].start, bu.ranges["stem"].end)
    a_range = None
    if bu.ranges.get("answer") is not None:
        a_range = (bu.ranges["answer"].start, bu.ranges["answer"].end)

    result = expand_composite_sub_questions(
        source_lines,
        question_numbers=bu.question_numbers,
        questions_range=q_range,
        answer_range=a_range,
        original_question_type=bu.original_question_type,
    )
    bu.subq_unit_reason = result.unit_reason
    bu.subq_skipped = dict(result.skipped)
    if result.sub_questions:
        bu.sub_questions = specs_to_payload_subs(
            bu.unit_id,
            result.sub_questions,
            original_question_type=bu.original_question_type,
        )


def build_annotation_payload_from_bound(
    bound_units: list[BoundUnit],
    *,
    source_content_sha256: str,
    manifest_identity_version: Any,
    subject: str | None = None,
    grade: str | None = None,
    grade_source: str | None = None,
) -> dict:
    """Produce SemanticAnnotation.payload shape from bound units.

    unit_id stays Producer's. Content roles declare structure + line evidence
    (same contract as annotation_adapter / Spec 10 §4).
    """
    from scripts.preprocessing_consumer.boundary import normalize_unit_type

    semantic_units: list[dict] = []
    normalizations: list[dict] = []
    bindings: list[dict] = []

    for bu in bound_units:
        try:
            norm = normalize_unit_type(bu.unit_type)
        except BoundaryViolation as exc:
            raise ManifestBindingError(
                f"unit_type normalize failed: {exc}", unit_id=bu.unit_id
            ) from exc

        normalizations.append(
            {
                "unit_id": bu.unit_id,
                "producer_unit_type": norm.producer_unit_type,
                "canonical_unit_type": norm.canonical_unit_type,
                "normalization_event_id": norm.normalization_event_id,
            }
        )
        bindings.append(
            {
                "unit_id": bu.unit_id,
                "question_numbers": bu.question_numbers,
                "printed_number": bu.printed_number,
                "bound_text_hash": bu.bound_text_hash,
                "ranges": {
                    k: ([v.start, v.end] if v is not None else None)
                    for k, v in bu.ranges.items()
                },
            }
        )

        content: dict[str, Any] = {}
        qn = str(bu.question_numbers[0]) if bu.question_numbers else ""
        stem: dict[str, Any] = {
            "role": "stem",
            "question_label": qn,
        }
        # P1: propagate printed_number → question_label_printed for basis=shift
        # units. Resolver uses this to match source stems with local numbering
        # (e.g. printed=1 while global=26). No inference — pass through verbatim.
        if bu.printed_number is not None:
            stem["question_label_printed"] = bu.printed_number
        if bu.ranges["stem"] is not None:
            # Resolver consumes question_search_lines (1-based inclusive).
            stem["question_search_lines"] = [
                bu.ranges["stem"].start,
                bu.ranges["stem"].end,
            ]
            stem["stem_lines"] = [bu.ranges["stem"].start, bu.ranges["stem"].end]
        content["stem"] = stem

        if bu.original_question_type in ("single_choice", "multiple_choice", "true_false"):
            content["options"] = [
                {
                    "role": "option",
                    "label": chr(ord("A") + i),
                    "question_label": qn,
                }
                for i in range(4)
            ]
            if bu.ranges["options"] is not None:
                content["options_range"] = [
                    bu.ranges["options"].start,
                    bu.ranges["options"].end,
                ]
        content["answer"] = {
            "role": "answer",
            "question_label": qn,
            "answer_zone": "answer_table",
        }
        if bu.ranges["answer"] is not None:
            content["answer"]["answer_lines"] = [
                bu.ranges["answer"].start,
                bu.ranges["answer"].end,
            ]

        # composite_question → composite_unit
        # - 单题（len(question_numbers)==1）：questions 区间 1:1 译为一个子题。
        # - 多题：优先用 GEO-SUBQ 确定性展开结果（sub_questions 已逐题带证据）；
        #   未展开则 sub_questions 留空 → IR 判 incomplete，安全拒绝，不入库。
        #   禁止合成假单题（stem 覆盖材料+多题是错误断言）。
        if norm.canonical_unit_type == "composite_unit":
            shared: dict[str, Any] = {}
            if bu.ranges["material"] is not None:
                # GEO-SUBQ: use marker-carrying material so the resolver can
                # actually bind the shared component (was bare {"role": ...}).
                shared["material"] = bu.material_shared or {"role": "material"}
            n_q = len(bu.question_numbers)
            subs: list[dict[str, Any]] = []
            if bu.sub_questions:
                # Deterministic expansion already payload-shaped (stem/options/answer).
                subs = list(bu.sub_questions)
            elif n_q == 1:
                subs = [
                    {
                        "unit_id": f"{bu.unit_id}.sub",
                        "unit_type": "standalone_unit",
                        "question_number": qn,
                        "original_question_type": bu.original_question_type,
                        "content": content,
                    }
                ]
            unit_out: dict[str, Any] = {
                "unit_id": bu.unit_id,
                "unit_type": norm.canonical_unit_type,
                "question_number": qn if n_q == 1 else None,
                "question_number_range": (
                    f"{bu.question_numbers[0]}-{bu.question_numbers[-1]}"
                    if n_q > 1
                    else (qn or None)
                ),
                "original_question_type": bu.original_question_type,
                "shared_components": shared,
                "sub_questions": subs,
            }
            if n_q > 1 and not subs:
                # 题组证据（不冒充单题）：行区间 + 题号列表
                unit_out["group_evidence"] = {
                    "question_numbers": list(bu.question_numbers),
                    "questions_lines": (
                        [bu.ranges["stem"].start, bu.ranges["stem"].end]
                        if bu.ranges["stem"] is not None
                        else None
                    ),
                    "material_lines": (
                        [bu.ranges["material"].start, bu.ranges["material"].end]
                        if bu.ranges["material"] is not None
                        else None
                    ),
                    "answer_lines": (
                        [bu.ranges["answer"].start, bu.ranges["answer"].end]
                        if bu.ranges["answer"] is not None
                        else None
                    ),
                    "structure": "undetermined_sub_questions",
                    "subq_unit_reason": bu.subq_unit_reason,
                    "subq_skipped": {str(k): v for k, v in bu.subq_skipped.items()},
                }
            semantic_units.append(unit_out)
        else:
            semantic_units.append(
                {
                    "unit_id": bu.unit_id,  # Producer identity alias — NOT renumbered
                    "unit_type": norm.canonical_unit_type,
                    "question_number": qn,
                    "original_question_type": bu.original_question_type,
                    "content": content,
                }
            )

    return {
        "document_metadata_claims": {
            # Producer manifest 权威映射（Owner 定稿）；缺失 → None（unknown）
            "subject": subject,
            "grade": grade,
            "year": None,
            "school": None,
            "grade_source": grade_source,
        },
        "sections": [],
        "semantic_units": semantic_units,
        "producer_boundary": {
            "source_content_sha256": source_content_sha256,
            "identity_version": manifest_identity_version,
            "unit_normalizations": normalizations,
            "unit_bindings": bindings,
            "input_mode": "manifest_units",
        },
    }
