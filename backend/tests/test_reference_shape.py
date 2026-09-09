"""Gate E1 — BUG-V3-013：blank/image content JSON shape 冻结 + malformed fail-fast。"""

import pytest

from app.domains.resolver.reference import extract_targets


def _payload(content_extra):
    return {"semantic_units": [{
        "unit_id": "Q1", "original_question_type": "single_choice",
        "content": {
            "stem": {"question_label": "1"},
            "options": [{"label": "A"}, {"label": "B"}],
            "answer": {"answer_zone": "answer_table", "question_label": "1"},
            **content_extra,
        },
    }]}


def test_blank_malformed_non_dict_fails_fast():
    with pytest.raises(ValueError):
        extract_targets(_payload({"blank": "not-a-dict"}))


def test_blank_missing_blank_label_fails_fast():
    with pytest.raises(ValueError):
        extract_targets(_payload({"blank": [{"question_label": "1"}]}))


def test_image_malformed_non_dict_fails_fast():
    with pytest.raises(ValueError):
        extract_targets(_payload({"image": ["nope"]}))


def test_image_malformed_image_ref_fails_fast():
    with pytest.raises(ValueError):
        extract_targets(_payload({"image": {"image_ref": "not-dict"}}))


def test_blank_valid_shape_extracted():
    targets = extract_targets(
        _payload({"blank": [{"blank_label": "1", "question_label": "1"}]})
    )
    blanks = [t for t in targets if t.kind == "blank_label"]
    assert len(blanks) == 1
    assert blanks[0].label == "1"
    assert blanks[0].question_number == "1"


def test_image_valid_shape_extracted():
    targets = extract_targets(
        _payload({"image": {"image_ref": {"figure_id": "fig-001"}}})
    )
    images = [t for t in targets if t.kind == "image"]
    assert len(images) == 1
    assert images[0].image_ref == {"figure_id": "fig-001"}
