# -*- coding: utf-8 -*-
"""E2E-009R6: composite children with identical option labels must not collide."""
from __future__ import annotations

from app.domains.gate.admission import _aggregate_composite_roles


def _roles(unit_id: str, qn: str):
    return [
        {"kind": "content", "role": "stem", "unit_id": unit_id, "text": f"{qn}. stem",
         "text_hash": f"h{qn}", "span_id": f"sp-{unit_id}.stem",
         "question_number": qn},
        *[
            {
                "kind": "content", "role": "option", "unit_id": unit_id,
                "label": lab, "text": f"{lab}. opt-{lab}", "text_hash": f"h{qn}{lab}",
                "span_id": f"sp-{unit_id}.option.{lab}", "question_number": qn,
            }
            for lab in "ABC"
        ],
    ]


def test_two_subs_same_abc_labels_unique():
    root = {
        "unit_id": "U1",
        "unit_type": "composite_unit",
        "original_question_type": "single_choice",
        "question_number_range": "1-2",
        "sub_questions": [
            {"unit_id": "Q1", "unit_type": "standalone_unit", "question_number": "1"},
            {"unit_id": "Q2", "unit_type": "standalone_unit", "question_number": "2"},
        ],
    }
    roles_by_unit = {
        "Q1": _roles("Q1", "1"),
        "Q2": _roles("Q2", "2"),
    }
    answers_by_unit = {
        "Q1": {"unit_id": "Q1", "text": "A", "text_hash": "ha", "span_id": "sp-q1a",
               "question_number": "1", "source_located": True, "complete": True},
        "Q2": {"unit_id": "Q2", "text": "B", "text_hash": "hb", "span_id": "sp-q2a",
               "question_number": "2", "source_located": True, "complete": True},
    }
    roles, stem, answers = _aggregate_composite_roles(
        root, [root], roles_by_unit, answers_by_unit, {}
    )
    opt_labels = [r["label"] for r in roles if r.get("role") == "option"]
    assert len(opt_labels) == 6
    assert len(opt_labels) == len(set(opt_labels)), opt_labels
    # both children keep A/B/C identity inside the unique label
    assert any(x.endswith("A") for x in opt_labels)
    assert any(x.startswith("1") for x in opt_labels)
    assert any(x.startswith("2") for x in opt_labels)
    # answers stay per-child
    assert [a["label"] for a in answers] == ["1", "2"]
    assert [a["text"] for a in answers] == ["A", "B"]
    # E2E-009R7: option text must NOT repeat the letter label (UI shows label once)
    for r in roles:
        if r.get("role") == "option":
            lab = str(r.get("label") or "")
            letter = lab[-1] if lab else ""
            text = r.get("text") or ""
            assert not text.startswith(f"{letter}."), (lab, text)
            assert text.startswith("opt-"), text
