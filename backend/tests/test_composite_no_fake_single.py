# -*- coding: utf-8 -*-
"""Regression: multi-question composite must NOT become a fake single Question."""
from app.domains.compile.ir import IRBuilder, validate_ir
from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)


def _geo_multi_q_manifest():
    lines = [f"L{i}" for i in range(1, 21)]
    man = {
        "units": [
            {
                "unit_id": "U1-2",
                "unit_type": "composite_question",
                "question_numbers": [1, 2],
                "original_question_type": "single_choice",
                "questions_lines": [2, 8],
                "material_lines": [2, 2],
                "answer_lines": [10, 10],
            }
        ]
    }
    return man, lines


def test_multi_q_composite_no_fake_single_sub():
    """question_number_range=1-2 不得生成一个 standalone 子题冒充单题。"""
    man, lines = _geo_multi_q_manifest()
    bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
    payload = build_annotation_payload_from_bound(
        bound, source_content_sha256="a" * 64, manifest_identity_version=2
    )
    u = payload["semantic_units"][0]
    assert u["unit_type"] == "composite_unit"
    assert u["question_number_range"] == "1-2"
    assert u.get("sub_questions") == [], "must not invent a single sub-question"
    assert u.get("shared_components", {}).get("material"), "keep material evidence"
    ev = u.get("group_evidence") or {}
    assert ev.get("question_numbers") == [1, 2]
    assert ev.get("structure") == "undetermined_sub_questions"
    assert ev.get("questions_lines") == [2, 8]


def test_multi_q_composite_not_ready_in_ir():
    """无子题的 composite 必须 IR incomplete，不能变成可入库 leaf。"""
    man, lines = _geo_multi_q_manifest()
    bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
    payload = build_annotation_payload_from_bound(
        bound, source_content_sha256="a" * 64, manifest_identity_version=2
    )
    # empty resolved run → all spans missing anyway; still assert node status
    from app.domains.resolver.span import ResolvedRun

    ir = IRBuilder.build(
        ResolvedRun(source_version_id="0df40d7b-0000-0000-0000-000000000000"),
        payload,
        "0df40d7b-0000-0000-0000-000000000000",
        "c38ee1ab-0000-0000-0000-000000000000",
    )
    assert ir.units[0].semantic_status != "ready"
    assert ir.units[0].sub_questions == ()


def test_single_q_composite_still_gets_one_sub():
    """单题 composite 仍 1:1 译为一个子题（允许）。"""
    lines = [f"L{i}" for i in range(1, 21)]
    man = {
        "units": [
            {
                "unit_id": "U-P2-1",
                "unit_type": "composite_question",
                "question_numbers": [51],
                "original_question_type": "short_answer",
                "questions_lines": [2, 6],
                "material_lines": [2, 2],
                "answer_lines": [10, 11],
            }
        ]
    }
    bound = bind_units_from_manifest(man, lines, source_content_sha256="b" * 64)
    payload = build_annotation_payload_from_bound(
        bound, source_content_sha256="b" * 64, manifest_identity_version=2
    )
    u = payload["semantic_units"][0]
    assert u["unit_type"] == "composite_unit"
    assert len(u["sub_questions"]) == 1
    assert u["sub_questions"][0]["unit_type"] == "standalone_unit"
