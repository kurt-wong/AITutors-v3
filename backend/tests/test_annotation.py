"""Gate D1 — Forbidden-Field Validator Correctness + D4 Golden Fixture。

D1：validate_annotation_payload 正确性（深嵌套路径 + 违规路径完整）。
D4：正/反例 fixture golden（回归种子）。
"""

from app.domains.annotation import (
    FORBIDDEN_FIELDS,
    ANNO_SCHEMA_VERSION,
    ANN_PROMPT_VERSION,
    validate_annotation_payload,
)


def _valid_payload():
    return {
        "annotation_schema": ANNO_SCHEMA_VERSION,
        "document_metadata_claims": {"subject": None},
        "sections": [],
        "semantic_units": [
            {
                "type": "standalone_question",
                "question_label": "1",
                "stem_ref": {
                    "role": "question_label",
                    "label": "1",
                    "start_marker": {"kind": "question_label", "text": "1"},
                    "end_marker": None,
                },
            }
        ],
        "annotation_meta": {
            "model": "mock",
            "prompt_version": ANN_PROMPT_VERSION,
            "status": "complete",
            "warnings": [],
        },
    }


def _invalid_payload():
    p = _valid_payload()
    p["stem_text"] = "问题内容"  # 20 §4.3 forbidden
    return p


async def test_d1_valid_payload_passes():
    ok, violations = validate_annotation_payload(_valid_payload())
    assert ok is True
    assert violations == []


async def test_d1_shallow_forbidden_field_detected():
    p = {"line_refs": ["P1L001"]}
    ok, violations = validate_annotation_payload(p)
    assert ok is False
    assert "line_refs" in violations


async def test_d1_nested_forbidden_field_detected_with_full_path():
    p = _valid_payload()
    p["sections"] = [{"semantic_units": [{"stem_text": "嵌套禁字段"}]}]
    ok, violations = validate_annotation_payload(p)
    assert ok is False
    assert any("stem_text" in v for v in violations)
    # 完整路径可定位
    assert any(v.startswith("sections[") for v in violations)


async def test_d1_list_index_path_correct():
    p = {"items": [{"answer_text": "答案"}]}
    ok, violations = validate_annotation_payload(p)
    assert ok is False
    assert "items[0].answer_text" in violations


async def test_d1_multiple_violations_all_reported():
    p = {"stem_text": "x", "answer_text": "y", "options_text": "z"}
    ok, violations = validate_annotation_payload(p)
    assert ok is False
    assert len(violations) == 3
    assert set(violations) == {"stem_text", "answer_text", "options_text"}


async def test_d1_valid_payload_contains_no_forbidden_keys():
    p = _valid_payload()
    all_keys = set()
    _collect_keys(p, all_keys)
    assert all_keys.isdisjoint(FORBIDDEN_FIELDS)


async def test_d4_golden_fixtures():
    """D4：正/反例 fixture golden（固定回归种子，连续运行一致）。"""
    vp = _valid_payload()
    ip = _invalid_payload()
    ok_v, v_v = validate_annotation_payload(vp)
    ok_i, v_i = validate_annotation_payload(ip)
    assert ok_v is True and v_v == []
    assert ok_i is False and len(v_i) >= 1 and "stem_text" in v_i


def _collect_keys(obj, keys: set):
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            _collect_keys(v, keys)
    elif isinstance(obj, list):
        for v in obj:
            _collect_keys(v, keys)
