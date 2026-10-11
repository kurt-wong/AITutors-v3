# -*- coding: utf-8 -*-
"""Answer marker extraction + geo composite binding (deterministic)."""
import pytest

from app.domains.gate.grammar import _extract_unique_choice_marker, verify
from app.domains.source.manifest_annotation import (
    bind_units_from_manifest,
    build_annotation_payload_from_bound,
)


def test_extract_unique_gu_xuan():
    assert _extract_unique_choice_marker("【考点】xx\n【解答】解：……\n故选：D.") == "D"
    assert _extract_unique_choice_marker("故选C.") == "C"
    assert _extract_unique_choice_marker("答案：B") == "B"


def test_extract_rejects_ambiguous_or_missing():
    assert _extract_unique_choice_marker("【解答】没有标记") is None
    assert _extract_unique_choice_marker("故选：A 故选：B") is None
    assert _extract_unique_choice_marker("短") is None


def test_verify_single_choice_from_explanation_block():
    # 全文不匹配白名单，但含唯一故选
    text = (
        "【考点】三角函数.\n【分析】……\n【解答】解：……\n故选：D."
    )
    assert verify("single_choice", text, resolved_option_labels={"A", "B", "C", "D"}) is True
    assert verify("single_choice", text, resolved_option_labels={"A", "B", "C"}) is None


def test_geo_composite_binds_questions_lines_as_stem():
    lines = [f"L{i}" for i in range(1, 21)]
    man = {
        "units": [
            {
                "unit_id": "U1-2",
                "unit_type": "composite_question",
                "question_numbers": [1, 2],
                "original_question_type": "single_choice",
                "questions_lines": [2, 5],
                "material_lines": [2, 2],
                "answer_lines": [10, 10],
            }
        ]
    }
    bound = bind_units_from_manifest(man, lines, source_content_sha256="a" * 64)
    assert bound[0].ranges["stem"] is not None
    assert bound[0].ranges["stem"].start == 2
    payload = build_annotation_payload_from_bound(
        bound, source_content_sha256="a" * 64, manifest_identity_version=2
    )
    u = payload["semantic_units"][0]
    assert u["unit_type"] == "composite_unit"
    assert u["shared_components"].get("material")
    assert len(u["sub_questions"]) == 1
    sub = u["sub_questions"][0]
    assert sub["content"]["stem"]["question_search_lines"] == [2, 5]
