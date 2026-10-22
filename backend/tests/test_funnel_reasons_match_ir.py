# -*- coding: utf-8 -*-
"""Funnel skip reasons must match real IR validator (no drift)."""
from app.domains.compile.ir import IRContent, IRNode, collect_validation_problems
from app.domains.source.funnel_recorder import ir_skip_reasons


def _leaf(**kw):
    defaults = dict(
        unit_id="Q1",
        unit_type="standalone_unit",
        question_number="1",
        question_number_range=None,
        original_question_type="single_choice",
        content=(),
        shared_components=(),
        sub_questions=(),
        relations=(),
        semantic_status="incomplete",
    )
    defaults.update(kw)
    return IRNode(**defaults)


def test_multi_q_composite_reason_is_real_validator_reason():
    """sub_questions=[] → 'composite has no sub_questions'，不得报 leaf 缺失。"""
    node = _leaf(
        unit_id="U1-2",
        unit_type="composite_unit",
        question_number=None,
        question_number_range="1-2",
        original_question_type="single_choice",
        shared_components=(IRContent(role="material", span_id=None),),
        sub_questions=(),
        semantic_status="incomplete",
    )
    summary, problems = ir_skip_reasons(node)
    real = collect_validation_problems(node, set())
    # Core constraint: funnel reasons must match the IR validator (no drift).
    assert problems == real, (problems, real)
    # New composite semantics: empty sub_questions + empty parent content
    # reports the real missing roles (not a fabricated "no sub_questions").
    assert "stem not declared" in problems
    assert "answer not declared" in problems
    assert "composite has no sub_questions" not in problems


def test_standalone_reasons_unchanged():
    node = _leaf(
        content=(
            IRContent(role="stem", span_id=None),
            IRContent(role="answer", span_id=None),
        ),
    )
    summary, problems = ir_skip_reasons(node)
    real = collect_validation_problems(node, set())
    assert problems == real
    assert "stem unresolved" in problems
    assert "answer unresolved" in problems
    assert "options missing for choice type" in problems


def test_single_q_composite_with_unready_sub():
    sub = _leaf(unit_id="U1.sub", unit_type="standalone_unit", semantic_status="incomplete")
    node = _leaf(
        unit_id="U-P2-1",
        unit_type="composite_unit",
        question_number_range="51",
        original_question_type="short_answer",
        shared_components=(IRContent(role="material", span_id="sp-U-P2-1.material"),),
        sub_questions=(sub,),
        semantic_status="incomplete",
    )
    summary, problems = ir_skip_reasons(node)
    assert problems == collect_validation_problems(node, set())
    assert "composite sub_question not ready" in problems
    assert "composite has no sub_questions" not in problems
