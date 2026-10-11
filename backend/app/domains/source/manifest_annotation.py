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
    printed_number: int | None = None


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
        printed_i = None
        if isinstance(printed, (list, tuple)) and printed:
            printed_i = int(printed[0])
        elif isinstance(printed, int):
            printed_i = printed

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
                printed_number=printed_i,
            )
        )

    return bound


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

        # composite_question → composite_unit：material→shared，questions 区间 1:1
        # 译为单个子题（确定性结构翻译；不猜子题拆分，同 annotation_adapter._build_composite）
        if norm.canonical_unit_type == "composite_unit":
            shared: dict[str, Any] = {}
            if bu.ranges["material"] is not None:
                shared["material"] = {"role": "material"}
            semantic_units.append(
                {
                    "unit_id": bu.unit_id,
                    "unit_type": norm.canonical_unit_type,
                    "question_number": qn,
                    "question_number_range": (
                        f"{bu.question_numbers[0]}-{bu.question_numbers[-1]}"
                        if len(bu.question_numbers) > 1
                        else None
                    ),
                    "original_question_type": bu.original_question_type,
                    "shared_components": shared,
                    "sub_questions": [
                        {
                            "unit_id": f"{bu.unit_id}.sub",
                            "unit_type": "standalone_unit",
                            "question_number": qn,
                            "original_question_type": bu.original_question_type,
                            "content": content,
                        }
                    ],
                }
            )
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
