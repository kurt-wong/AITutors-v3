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
import re
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
    # Producer-declared option labels (e.g. A–C for 3-option listening items).
    # Empty → caller may fall back to legacy A–D.
    option_labels: list[str] = field(default_factory=list)
    # E2E-013 data-safety: manifest declares answer_evidence.type=absent AND
    # a validation issue exists → block answer-zone fallback binding.
    answer_fallback_blocked: bool = False
    # R3-D: option labels detected in extra_lines → {label: line_number}
    extra_opt_lines: dict[str, int] = field(default_factory=dict)
    # P0-answer: manifest answer_evidence.value (declared answer when
    # answer_lines is None). Used directly — never inferred from explanation.
    answer_evidence_value: str | None = None


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

        # Owner 2026-10: 英语听力题无配套音频，一律不入库。
        section = str(raw.get("section") or "")
        if "听力" in section:
            continue

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
            # P2-fix-2: layout-drifted images/tables/continuation
            "extra": _as_range(
                raw.get("extra_lines"), label="extra_lines", unit_id=unit_id
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

        option_labels: list[str] = []
        raw_opts = raw.get("options")
        if isinstance(raw_opts, (list, tuple)):
            for o in raw_opts:
                if isinstance(o, dict):
                    lab = o.get("label")
                    if lab is not None and str(lab).strip():
                        option_labels.append(str(lab).strip())
        # Fix D: scan extra_lines for option-pattern content with MISSING labels
        # (e.g. BIO Q8 "D. $O_2$" drifted into extra_lines).  Only add sequential
        # labels (next letter after current max), never arbitrary letters.
        _extra_rng = ranges.get("extra")
        _extra_opt_line: dict[str, int] = {}  # label → line number in extras
        if _extra_rng is not None and option_labels:
            max_lab = max(option_labels, key=lambda x: x.upper() if len(x) == 1 else "")
            if len(max_lab) == 1 and max_lab.isalpha():
                next_lab = chr(ord(max_lab.upper()) + 1)
                _opt_pat = re.compile(
                    rf"(?:^|>)\s*{re.escape(next_lab)}\s*[.．。:：、]")
                for ln in range(_extra_rng.start, _extra_rng.end + 1):
                    if 1 <= ln <= len(source_lines):
                        if _opt_pat.search(source_lines[ln - 1]):
                            option_labels.append(next_lab)
                            _extra_opt_line[next_lab] = ln
                            break

        # E2E-013 data-safety: when manifest declares answer_evidence.type=absent
        # AND a validation issue references this unit, block the answer-zone
        # fallback scan from force-binding unrelated answer-section text.
        # Match unit_id as complete identifier (Q1 must not match Q10).
        ae = raw.get("answer_evidence") if isinstance(raw.get("answer_evidence"), dict) else {}
        ae_absent = ae.get("type") == "absent"
        # P0-answer: capture declared answer value (e.g. "B", "1/6").
        # Used when answer_lines is None — never inferred from explanation.
        ae_value = ae.get("value")
        ae_value_str = str(ae_value).strip() if ae_value is not None and str(ae_value).strip() else None
        v_issues = (manifest.get("annotation_meta") or {}).get("validation_issues") or []
        _uid_re = re.compile(rf"^{re.escape(unit_id)}(?:[:：\s]|$)")
        has_v_issue = any(_uid_re.match(str(issue).lstrip("! ")) for issue in v_issues)
        answer_fallback_blocked = ae_absent and has_v_issue

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
                option_labels=option_labels,
                answer_fallback_blocked=answer_fallback_blocked,
                extra_opt_lines=_extra_opt_line,
                answer_evidence_value=ae_value_str,
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
    themselves are excluded) — wrong for inclusive manifest ranges. Use a
    non-empty material line as a single-line marker instead: the shared
    component then resolves deterministically without inventing boundaries.

    E2E-009R2 U45-48: the first material line may be a short heading like
    `## B` that substring-matches several later headings (`## Beauty…`,
    `## Blocks…`) — resolver then returns ambiguous and the whole composite
    is IR-incomplete (silent drop). Prefer the first material line whose text
    is a unique source hit; fall back to the first non-empty line.
    """
    rng = bu.ranges.get("material")
    if rng is None:
        return
    n = len(source_lines)
    candidates: list[str] = []
    for i in range(rng.start, rng.end + 1):
        if 1 <= i <= n:
            text = source_lines[i - 1].strip()
            if text:
                candidates.append(text)
    if not candidates:
        return

    def _hit_count(needle: str) -> int:
        return sum(1 for line in source_lines if needle in line)

    for text in candidates:
        if _hit_count(text) == 1:
            bu.material_shared = {
                "role": "material",
                "start_marker": {"text": text, "granularity": "line"},
                # E2E-009R5: full declared passage, not just the marker line.
                "evidence_lines": [rng.start, rng.end],
            }
            return
    bu.material_shared = {
        "role": "material",
        "start_marker": {"text": candidates[0], "granularity": "line"},
        "evidence_lines": [rng.start, rng.end],
    }


def _expand_subs(bu: "BoundUnit", source_lines: list[str]) -> None:
    """Attach deterministic sub_questions to a multi-q composite BoundUnit.

    Only proven structure (题号→题干→A-D→答案表) is emitted; anything ambiguous
    is skipped per question. short_answer / non-choice stays unexpanded.
    """
    from app.domains.source.subq_expand import (
        answer_evidence_mismatches,
        expand_composite_sub_questions,
        specs_to_payload_subs,
    )

    # Shared P0 gate: wrong answer_evidence.value must not expand / auto-approve.
    mismatch = answer_evidence_mismatches(
        bu.answer_evidence_value,
        list(bu.question_numbers or []),
        source_lines,
        (bu.ranges["answer"].start, bu.ranges["answer"].end)
        if bu.ranges.get("answer") is not None
        else None,
    )
    if mismatch:
        bu.subq_unit_reason = mismatch
        bu.sub_questions = []
        return

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
        has_declared_options=bool(bu.option_labels),
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
        # P2-fix-2: map extra_lines into stem content so resolver can bind
        # layout-drifted images/tables/continuation (was silently dropped).
        if bu.ranges.get("extra") is not None:
            stem["extra_lines"] = [bu.ranges["extra"].start, bu.ranges["extra"].end]
        content["stem"] = stem

        if bu.original_question_type in (
            "single_choice", "multiple_choice", "true_false", "seven_to_five",
        ):
            # Producer-declared labels win (EN listening is A–C; 七选五 is A–G).
            # Fall back to legacy A–D only when the manifest declared none.
            labels = bu.option_labels or [chr(ord("A") + i) for i in range(4)]
            content["options"] = []
            for lab in labels:
                opt_dict = {
                    "role": "option",
                    "label": lab,
                    "question_label": qn,
                }
                # R3-D: option found in extra_lines gets direct evidence_lines
                # so resolver can bind it without expanding options_range.
                if lab in (bu.extra_opt_lines or {}):
                    opt_dict["evidence_lines"] = [
                        bu.extra_opt_lines[lab], bu.extra_opt_lines[lab],
                    ]
                content["options"].append(opt_dict)
            if bu.ranges["options"] is not None:
                # R3-D: do NOT unconditionally expand options_range into extras
                # (respects next-unit boundary; avoids Q9 options bleeding into Q8).
                content["options_range"] = [
                    bu.ranges["options"].start,
                    bu.ranges["options"].end,
                ]
        content["answer"] = {
            "role": "answer",
            "question_label": qn,
            "answer_zone": "answer_table",
            "fallback_blocked": bu.answer_fallback_blocked,
        }
        if bu.ranges["answer"] is not None:
            content["answer"]["answer_lines"] = [
                bu.ranges["answer"].start,
                bu.ranges["answer"].end,
            ]
        elif bu.answer_evidence_value is not None:
            # P0-answer: answer_lines=None but manifest declared the answer
            # in answer_evidence.value. Pass it directly — resolver must NOT
            # scan explanation text to find the answer.
            content["answer"]["answer_value"] = bu.answer_evidence_value
        # P2-fix-1: map explanation_lines into content (was computed in ranges
        # but never assigned — explanations were lost for all subjects).
        if bu.ranges["explanation"] is not None:
            content["explanation"] = {
                "role": "explanation",
                "question_label": qn,
                "explanation_zone": "inline_explanation",
                "explanation_lines": [
                    bu.ranges["explanation"].start,
                    bu.ranges["explanation"].end,
                ],
            }

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
            # E2E-010: 七选五共享 A–G 选项挂在父 content，便于聚合/展示
            if content.get("options"):
                unit_out["content"] = {"options": content["options"]}
                if content.get("options_range"):
                    unit_out["content"]["options_range"] = content["options_range"]
            # Fix C: composite explanation must enter unit_out (was only in local
            # content dict, never written for composite branch).
            if content.get("explanation"):
                unit_out.setdefault("content", {})
                unit_out["content"]["explanation"] = content["explanation"]
            if n_q > 1:
                # WP7-B: always persist expansion evidence for multi-q composites.
                # Previously only written when NOT subs — partial expansion lost
                # skipped-question records (CHN-001 Q5/Q12/Q13/Q16).
                expanded_nums = sorted(
                    int(s["question_number"])
                    for s in subs
                    if s.get("question_number") is not None
                )
                skipped_map = {str(k): v for k, v in bu.subq_skipped.items()}
                if not subs:
                    structure = "undetermined_sub_questions"
                elif skipped_map or len(expanded_nums) < n_q:
                    structure = "partial_sub_questions"
                else:
                    structure = "expanded_sub_questions"
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
                    "structure": structure,
                    "subq_unit_reason": bu.subq_unit_reason,
                    "subq_skipped": skipped_map,
                    # WP7-B: actual expanded coverage — do not confuse with
                    # question_number_range (which is the full printed range).
                    "expanded_question_numbers": expanded_nums,
                    "declared_question_count": n_q,
                    "expanded_question_count": len(expanded_nums),
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
