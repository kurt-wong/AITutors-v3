"""T2.5 P0 regression: partial composite expansion must not be ready.

Covers Spec 10 §645 (composite atomic group) + README composite rule.
All cases go through real IRBuilder.build — not helper-only assertions.
"""
from __future__ import annotations

import uuid

import pytest

from app.domains.compile.ir import IRBuilder
from app.domains.resolver.resolver import ResolvedRun
from app.domains.resolver.span import ResolvedSpan

SVID = uuid.uuid4()


def _span(span_id: str) -> ResolvedSpan:
    return ResolvedSpan(
        span_id=span_id,
        source_version_id=SVID,
        role="stem",
        start_line_ref="P1L001",
        end_line_ref="P1L001",
        line_refs=("P1L001",),
        granularity="line",
        start_offset=0,
        end_offset=1,
        text_hash="deadbeef",
        resolution_status="exact",
    )


def _run_with_spans(span_ids: list[str]) -> ResolvedRun:
    spans = tuple(_span(s) for s in span_ids)
    return ResolvedRun(
        resolved_spans=spans,
        unresolved_references=(),
        source_version_id=SVID,
    )


def _sub(
    unit_id: str,
    qn: int,
    *,
    with_stem: bool = True,
    with_answer: bool = True,
    unresolved: bool = False,
) -> dict:
    content: dict = {}
    if with_stem:
        content["stem"] = {
            "role": "stem",
            "question_label": str(qn),
            "question_search_lines": [1, 1],
        }
    if with_answer:
        content["answer"] = {
            "role": "answer",
            "question_label": str(qn),
            "answer_lines": [2, 2],
        }
    return {
        "unit_id": f"{unit_id}.sub{qn}",
        "unit_type": "standalone_unit",
        "question_number": str(qn),
        "original_question_type": "fill_in",
        "content": content,
    }


def _composite(
    unit_id: str,
    declared: list[int],
    expanded: list[int],
    subs: list[dict],
    *,
    skipped: dict | None = None,
    structure: str = "partial_sub_questions",
    with_shared: bool = True,
) -> dict:
    shared = {}
    if with_shared:
        shared["material"] = {"role": "material"}
    unit = {
        "unit_id": unit_id,
        "unit_type": "composite_unit",
        "question_number": None,
        "question_number_range": f"{declared[0]}-{declared[-1]}" if declared else None,
        "original_question_type": "fill_in",
        "shared_components": shared,
        "sub_questions": subs,
        "group_evidence": {
            "question_numbers": declared,
            "structure": structure,
            "subq_skipped": skipped or {},
            "expanded_question_numbers": expanded,
            "declared_question_count": len(declared),
            "expanded_question_count": len(expanded),
        },
    }
    return unit


def _build(payload_units: list[dict]) -> object:
    payload = {"semantic_units": payload_units}
    span_ids = ["sp-C.material"]
    for u in payload_units:
        for s in u.get("sub_questions") or []:
            sid = s.get("unit_id") or ""
            if "stem" in (s.get("content") or {}):
                span_ids.append(f"sp-{sid}.stem")
            if "answer" in (s.get("content") or {}):
                span_ids.append(f"sp-{sid}.answer")
        if u.get("shared_components"):
            span_ids.append(f"sp-{u['unit_id']}.material")
    run = _run_with_spans(span_ids)
    return IRBuilder.build(run, payload, SVID, uuid.uuid4())


def _status(ir, unit_id: str) -> tuple[str, list[str]]:
    for n in ir.units:
        if n.unit_id == unit_id:
            from app.domains.compile.ir import collect_validation_problems

            return n.semantic_status, collect_validation_problems(n, set())
    raise AssertionError(f"unit {unit_id} not in IR")


# ---------------------------------------------------------------------------
# 1) declared 5, expanded 2 → NOT ready
# ---------------------------------------------------------------------------
def test_partial_expansion_5_of_2_not_ready():
    subs = [_sub("C", 21), _sub("C", 25)]
    unit = _composite(
        "C",
        [21, 22, 23, 24, 25],
        [21, 25],
        subs,
        skipped={"22": "question start not found", "23": "x", "24": "x"},
    )
    ir = _build([unit])
    status, problems = _status(ir, "C")
    assert status == "incomplete"
    assert any("missing" in p and "22" in p for p in problems), problems


# ---------------------------------------------------------------------------
# 2) declared 15, expanded 14 → NOT ready (U26-40 case)
# ---------------------------------------------------------------------------
def test_partial_expansion_15_of_14_not_ready():
    declared = list(range(26, 41))
    expanded = [q for q in declared if q != 35]
    subs = [_sub("C", q) for q in expanded]
    unit = _composite(
        "C",
        declared,
        expanded,
        subs,
        skipped={"35": "option boundary unresolved"},
    )
    ir = _build([unit])
    status, problems = _status(ir, "C")
    assert status == "incomplete"
    assert any("35" in p for p in problems), problems


# ---------------------------------------------------------------------------
# 3) declared 4, expanded 0 → NOT ready
# ---------------------------------------------------------------------------
def test_zero_expansion_not_ready():
    unit = _composite(
        "C",
        [41, 42, 43, 44],
        [],
        [],
        skipped={},
        structure="undetermined_sub_questions",
    )
    ir = _build([unit])
    status, problems = _status(ir, "C")
    assert status == "incomplete"


# ---------------------------------------------------------------------------
# 4) fully expanded and each sub OK → ready (no false reject)
# ---------------------------------------------------------------------------
def test_full_expansion_ready():
    declared = [57, 58, 59, 60]
    subs = [_sub("C", q) for q in declared]
    unit = _composite(
        "C",
        declared,
        declared,
        subs,
        structure="expanded_sub_questions",
    )
    ir = _build([unit])
    status, problems = _status(ir, "C")
    assert status == "ready", problems


# ---------------------------------------------------------------------------
# 5) same count but wrong / shifted numbers → NOT complete
# ---------------------------------------------------------------------------
def test_same_count_wrong_numbers_not_complete():
    # declared 21-22, but subs carry 21 and 25 (same count=2, wrong set)
    subs = [_sub("C", 21), _sub("C", 25)]
    unit = _composite(
        "C",
        [21, 22],
        [21, 25],  # evidence claims 21,25 but declared is 21,22
        subs,
    )
    ir = _build([unit])
    status, problems = _status(ir, "C")
    assert status == "incomplete"
    assert any("22" in p for p in problems), problems


def test_expanded_evidence_mismatch_with_subs_not_complete():
    # evidence says all expanded, but one sub is actually missing
    declared = [1, 2, 3]
    subs = [_sub("C", 1), _sub("C", 2)]
    unit = _composite(
        "C",
        declared,
        [1, 2, 3],  # evidence lies
        subs,
    )
    ir = _build([unit])
    status, problems = _status(ir, "C")
    assert status == "incomplete"
    # either missing-sub path or evidence-mismatch path
    assert any("3" in p or "mismatch" in p for p in problems), problems


# ---------------------------------------------------------------------------
# 6) legitimate full expansion with explicit skip record empty → not misjudged
# ---------------------------------------------------------------------------
def test_legitimate_expansion_not_flagged_as_loss():
    declared = [1, 2]
    subs = [_sub("C", 1), _sub("C", 2)]
    unit = _composite(
        "C",
        declared,
        declared,
        subs,
        skipped={},
        structure="expanded_sub_questions",
    )
    ir = _build([unit])
    status, problems = _status(ir, "C")
    assert status == "ready"
    assert not any("missing" in p for p in problems)


# ---------------------------------------------------------------------------
# 7) sub with unresolved stem → whole composite not ready (atomic group)
# ---------------------------------------------------------------------------
def test_sub_problem_forces_composite_incomplete():
    declared = [1, 2]
    # sub 2 has stem declared but we won't add the span → unresolved
    subs = [
        _sub("C", 1),
        {
            "unit_id": "C.sub2",
            "unit_type": "standalone_unit",
            "question_number": "2",
            "original_question_type": "fill_in",
            "content": {
                "stem": {"role": "stem", "question_label": "2", "question_search_lines": [1, 1]},
                "answer": {"role": "answer", "question_label": "2", "answer_lines": [2, 2]},
            },
        },
    ]
    unit = _composite(
        "C",
        declared,
        declared,
        subs,
        structure="expanded_sub_questions",
    )
    # only provide spans for sub1 + material; sub2 stem/answer spans missing
    payload = {"semantic_units": [unit]}
    run = _run_with_spans(
        [
            "sp-C.material",
            "sp-C.sub1.stem",
            "sp-C.sub1.answer",
            # C.sub2.stem / .answer intentionally absent
        ]
    )
    ir = IRBuilder.build(run, payload, SVID, uuid.uuid4())
    status, problems = _status(ir, "C")
    assert status == "incomplete"


# ---------------------------------------------------------------------------
# 8) no group_evidence (n_q==1 style) → new check must not fire
# ---------------------------------------------------------------------------
def test_no_group_evidence_untouched():
    unit = {
        "unit_id": "C",
        "unit_type": "composite_unit",
        "question_number": "1",
        "question_number_range": "1",
        "original_question_type": "fill_in",
        "shared_components": {"material": {"role": "material"}},
        "sub_questions": [_sub("C", 1)],
    }
    ir = _build([unit])
    status, problems = _status(ir, "C")
    assert status == "ready", problems
    assert not any("composite incomplete" in p for p in problems), problems
