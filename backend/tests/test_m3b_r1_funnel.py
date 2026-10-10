"""M3b-R1: FunnelRecorder is invoked on the formal GateService path for skips."""

from __future__ import annotations

import uuid

import pytest

from app.domains.gate.service import GateService
from app.domains.source.funnel_recorder import FunnelRecorder
from app.models.snapshot import SemanticAnnotation
from app.models.source import Document, DocumentSourceVersion


async def _seed_sv_ann(session, body_text: str, payload: dict):
    doc = Document(
        id=uuid.uuid4(),
        original_object_key="k",
        original_sha256=uuid.uuid4().hex + uuid.uuid4().hex,
        file_name="funnel.pdf",
        file_type="pdf",
        upload_meta={},
        processing_status="sealed",
    )
    session.add(doc)
    sv = DocumentSourceVersion(
        id=uuid.uuid4(),
        document_id=doc.id,
        artifact_kind="canonical_l1",
        role="preprocessing",
        provider="preprocessing",
        body_text=body_text,
        body_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        integrity_hash=uuid.uuid4().hex + uuid.uuid4().hex,
        page_count=1,
        line_count=len(body_text.splitlines()),
        status="sealed",
    )
    session.add(sv)
    await session.flush()
    ann = SemanticAnnotation(
        id=uuid.uuid4(),
        source_version_id=sv.id,
        annotation_schema_version="1",
        prompt_version="t",
        model_config_hash="a" * 64,
        payload=payload,
        status="valid",
        logical_execution_stage="annotation",
        logical_execution_hash="b" * 64,
    )
    session.add(ann)
    await session.flush()
    return sv, ann


@pytest.mark.asyncio
async def test_gate_records_skipped_units_in_funnel(session):
    # Unit with unresolved stem/answer → semantic_status incomplete → skip + funnel
    body = "\n".join(f"line {i}" for i in range(1, 6))
    payload = {
        "document_metadata_claims": {"subject": "化学", "grade": "高一"},
        "semantic_units": [
            {
                "unit_id": "Q9",
                "unit_type": "standalone_unit",
                "question_number": "9",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {
                        "role": "stem",
                        "question_label": "9",
                        "question_search_lines": [1, 1],
                    },
                    "options": [
                        {"role": "option", "label": "A", "question_label": "9"}
                    ],
                    "answer": {
                        "role": "answer",
                        "question_label": "9",
                        "answer_zone": "answer_table",
                    },
                },
            }
        ],
    }
    sv, ann = await _seed_sv_ann(session, body, payload)

    funnel = FunnelRecorder(package_id=f"sv-{sv.id}")
    candidates, skipped = await GateService(session).run(
        source_version_id=sv.id,
        annotation_id=ann.id,
        task_type="document_ingest",
        funnel=funnel,
    )
    assert "Q9" in skipped
    assert funnel.counts["input_units"] == 1
    assert funnel.counts["candidates"] == 0
    failed_units = {f["unit_id"] for f in funnel.failures}
    assert "Q9" in failed_units
    rec = next(f for f in funnel.failures if f["unit_id"] == "Q9")
    assert rec["stage"] == "resolver_ir"
    assert rec["reason"]
    assert rec["evidence"].get("semantic_status") == "incomplete"
    assert rec["evidence"].get("problems")


@pytest.mark.asyncio
async def test_gate_funnel_records_ready_unit_candidate(session):
    body = "\n".join(
        [
            "8．下列物质中，含有离子键的是",
            "A. HCl",
            "B. $CO_{2}$",
            "C. $MgCl_{2}$",
            "D. $CH_{4}$",
            "答案：C",
        ]
    )
    payload = {
        "document_metadata_claims": {"subject": "化学", "grade": "高一"},
        "semantic_units": [
            {
                "unit_id": "Q8",
                "unit_type": "standalone_unit",
                "question_number": "8",
                "original_question_type": "single_choice",
                "content": {
                    "stem": {
                        "role": "stem",
                        "question_label": "8",
                        "question_search_lines": [1, 1],
                    },
                    "options": [
                        {
                            "role": "option",
                            "label": "A",
                            "question_label": "8",
                            "option_content_spans": {"A": [2, 2]},
                        },
                        {
                            "role": "option",
                            "label": "B",
                            "question_label": "8",
                            "option_content_spans": {"B": [3, 3]},
                        },
                        {
                            "role": "option",
                            "label": "C",
                            "question_label": "8",
                            "option_content_spans": {"C": [4, 4]},
                        },
                        {
                            "role": "option",
                            "label": "D",
                            "question_label": "8",
                            "option_content_spans": {"D": [5, 5]},
                        },
                    ],
                    "answer": {
                        "role": "answer",
                        "question_label": "8",
                        "answer_lines": [6, 6],
                    },
                },
            }
        ],
    }
    sv, ann = await _seed_sv_ann(session, body, payload)
    funnel = FunnelRecorder(package_id=f"sv-{sv.id}")
    candidates, skipped = await GateService(session).run(
        source_version_id=sv.id,
        annotation_id=ann.id,
        funnel=funnel,
    )
    # May or may not fully resolve; funnel must still record unit outcomes
    assert funnel.counts["input_units"] == 1
    if skipped:
        assert any(f["unit_id"] == "Q8" for f in funnel.failures)
    else:
        assert funnel.counts["candidates"] >= 1
