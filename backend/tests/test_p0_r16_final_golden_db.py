"""R16-FINAL-R1: golden grant and ownership persistence orthogonality.

Proves through REAL AdmissionService.approve → _materialize → DB that:
  - golden grant allows publish for unknown ownership
  - persisted ownership stays "unknown" (not rewritten to "match")
  - missing evidence → no publish

NOTE: production create_role_content REQUIRES a verified binding fact for
non-empty text. So the test registers a fact with ownership=unknown
(e.g., from source lines that don't prove match) — not NO fact.
"""
from __future__ import annotations

import uuid

import pytest

from app.domains.gate.admission import AdmissionService
from app.domains.gate.binding_fact import (
    derive_binding_fact,
    get_registry,
    register_trusted_binding_fact,
)

SVID = uuid.UUID("00000000-0000-0000-0000-00000000f001")
ANN_ID = uuid.UUID("00000000-0000-0000-0000-00000000a001")


def _mk(*texts):
    from app.domains.resolver.span import SourceLineView
    return tuple(
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    )


@pytest.fixture(autouse=True)
def _clean_registry():
    get_registry().clear()
    yield
    get_registry().clear()


async def _seed_candidate_with_unknown_fact(session):
    """Create Candidate + register a BindingFact with ownership=unknown.

    Uses source lines that don't prove match (e.g., '12. A' bound to Q1)
    so the fact's ownership is unknown/foreign.
    """
    from app.core.hashing import sha256_hex
    from app.domains.compile.compiler import Compiler
    from app.domains.compile.ir import IRBuilder
    from app.domains.gate.payload import build as build_payload
    from app.domains.resolver.resolver import SourceResolver
    from app.models.source import DocumentSourceLine
    from app.repositories.snapshot_repository import SnapshotRepository
    from app.repositories.source_repository import SourceRepository

    lines = _mk(
        "1. Q?", "A. a", "B. b", "C. c", "D. d",
        "答案", "1. B",
    )
    payload_meta = {
        "semantic_units": [{
            "unit_id": "Q1",
            "unit_type": "standalone_unit",
            "question_label": "1",
            "original_question_type": "single_choice",
            "content": {
                "stem": {"question_label": "1"},
                "options": [{"label": l} for l in "ABCD"],
                "answer": {"answer_zone": "answer_table", "question_label": "1", "answer_lines": [7, 7]},
            },
        }]
    }
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload_meta)
    ir = IRBuilder.build(run, payload_meta, SVID, ANN_ID)
    spans = {s.span_id: s for s in run.resolved_spans}
    compiled = Compiler(spans, {l.line_ref: l for l in lines}).compile(ir)

    # Register an UNKNOWN-ownership fact (source lines don't prove match)
    # Bare text without entry token → classify_answer_ownership returns unknown
    unknown_fact = derive_binding_fact(
        span_id="sp-Q1.answer",
        source_version_id=str(SVID),
        unit_id="Q1",
        question_number="1",
        source_lines=["just some bare text without any entry token"],
        answer_text="B",
    )
    assert unknown_fact.ownership == "unknown", (
        f"fact must be unknown for this test, got {unknown_fact.ownership}"
    )
    register_trusted_binding_fact(unknown_fact)

    # Seed source
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.md",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="t.md", file_type="md", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        id=SVID, document_id=doc.id, artifact_kind="raw_l1", role="native",
        provider="native", body_text="\n".join(l.text for l in lines),
        body_hash=sha256_hex(list(l.text for l in lines)),
        integrity_hash=sha256_hex(list(l.text for l in lines)),
        page_count=1, line_count=len(lines), status="draft",
    )
    await session.flush()
    for i, t in enumerate(lines):
        await src.append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref=f"P1L{i+1:03d}", seq=i + 1,
            page_no=1, line_no_in_page=i + 1, text=t.text,
            block_type="text", line_hash=sha256_hex(t.text),
        ))
    await session.flush()
    await src.seal_version(sv.id)
    await session.flush()

    root = ir.units[0]
    payload = build_payload(root=root, ir=ir, compiled=compiled, resolved_run=run)

    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id,
        annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="semantic-annotation/v1",
        model_config_hash=sha256_hex("m"),
        payload={"semantic_units": [], "document_metadata_claims": {}},
        status="valid", logical_execution_stage="ann",
        logical_execution_hash=sha256_hex("ann"),
    )
    await session.flush()
    cand = await SnapshotRepository(session).create_admission_candidate(
        unit_type="standalone_unit", source_version_id=sv.id,
        annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=payload,
        gate_decision={"decision": "pending_review"},
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex("compile"),
    )
    await session.flush()
    return cand, sv


async def _get_answer_status(session, sv_id):
    from sqlalchemy import select
    from app.models.content import InstanceRoleContent, QuestionInstance
    insts = (await session.execute(
        select(QuestionInstance).where(QuestionInstance.source_version_id == sv_id)
    )).scalars().all()
    rows = []
    for inst in insts:
        for r in (await session.execute(
            select(InstanceRoleContent).where(
                InstanceRoleContent.instance_id == inst.id,
                InstanceRoleContent.role == "answer",
            )
        )).scalars().all():
            rows.append({
                "text": r.text,
                "ownership": (r.answer_status or {}).get("ownership"),
                "publish": (r.answer_status or {}).get("publish"),
                "publish_grant": (r.answer_status or {}).get("publish_grant"),
            })
    return rows


class TestGoldenOwnershipOrthogonality:
    """R16-FINAL-R1: golden grant changes publish permission, NOT ownership."""

    @pytest.mark.asyncio
    async def test_golden_unknown_persists_ownership_unknown(self, session):
        """unknown fact + golden → publish official, ownership stays unknown in DB."""
        cand, sv = await _seed_candidate_with_unknown_fact(session)

        # Append golden review_trail (required for _has_human_approve)
        from app.repositories.snapshot_repository import SnapshotRepository
        snap = SnapshotRepository(session)
        await snap.append_review_trail(cand.id, {
            "decision": "approve",
            "verified_by": "golden",
            "reviewer_id": "golden-reviewer-1",
            "confirmed_fields": ["content", "belongs_to"],
        })
        await session.flush()

        # REAL approve with golden provenance
        result = await AdmissionService(session).approve(
            candidate_id=cand.id,
            provenance={
                "source": "golden",
                "reviewer_id": "golden-reviewer-1",
                "confirmed_fields": ["content", "belongs_to"],
            },
        )
        assert result.decision_status == "approved"

        # R16-FINAL-R1: query DB and verify ownership is NOT rewritten
        rows = await _get_answer_status(session, sv.id)
        assert rows, "must have answer rows in DB"
        for r in rows:
            assert r["ownership"] == "unknown", (
                f"ownership must stay 'unknown' after golden publish, "
                f"got {r['ownership']!r}"
            )
            assert r["text"] != "", (
                f"golden + valid evidence must produce non-empty text, got {r!r}"
            )
            assert r["publish"] == "official", (
                f"golden + valid evidence must publish official, got {r['publish']!r}"
            )
            assert r["publish_grant"] == "golden", (
                f"publish_grant must be 'golden', got {r['publish_grant']!r}"
            )

    @pytest.mark.asyncio
    async def test_golden_missing_evidence_no_publish(self, session):
        """golden but missing belongs_to → no publish, empty text."""
        cand, sv = await _seed_candidate_with_unknown_fact(session)

        from app.repositories.snapshot_repository import SnapshotRepository
        snap = SnapshotRepository(session)
        await snap.append_review_trail(cand.id, {
            "decision": "approve",
            "verified_by": "golden",
            "reviewer_id": "golden-reviewer-2",
            "confirmed_fields": ["content"],  # missing belongs_to
        })
        await session.flush()

        result = await AdmissionService(session).approve(
            candidate_id=cand.id,
            provenance={
                "source": "golden",
                "reviewer_id": "golden-reviewer-2",
                "confirmed_fields": ["content"],  # missing belongs_to
            },
        )

        rows = await _get_answer_status(session, sv.id)
        assert rows, "must have answer rows in DB"
        for r in rows:
            assert r["text"] == "", (
                f"missing belongs_to must withhold, got text={r['text']!r}"
            )
            assert r["publish"] != "official", (
                f"missing belongs_to must not publish official, got {r['publish']!r}"
            )
            assert r["ownership"] == "unknown", (
                f"ownership must stay unknown, got {r['ownership']!r}"
            )
