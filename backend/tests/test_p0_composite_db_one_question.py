"""P0-1 proof: real composite (no fake sub) reaches DB as ONE Question.

Uses real BIO-style fill-in composite through AdmissionService._materialize
and asserts:
- one Question identity
- parent content (stem + answer) present
- no fabricated U*.sub unit
- answer row exists
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.admission import AdmissionService
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from scripts.preprocessing_consumer.annotation_adapter import (
    manifest_to_annotation_payload,
)
from scripts.preprocessing_consumer.manifest_reader import load_manifest
from scripts.preprocessing_consumer.source_loader import load_source_lines
from tests.test_p0_r16c_bio001 import ANN_ID, BIO_MANIFEST, BIO_SOURCE, SVID


async def test_bio_u41_composite_one_question_no_fake_sub(session):
    """U41 fill-in composite → one Question, parent-as-body, no .sub."""
    manifest = load_manifest(BIO_MANIFEST)
    lines = load_source_lines(BIO_SOURCE)
    payload = manifest_to_annotation_payload(manifest)
    run = SourceResolver(source_version_id=SVID, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, SVID, ANN_ID)
    comp = Compiler({s.span_id: s for s in run.resolved_spans},
                    {l.line_ref: l for l in lines}).compile(ir)

    u41 = next(n for n in ir.units if n.unit_id == "U41")
    assert u41.semantic_status == "ready", (
        f"U41 must be ready parent-as-body, got {u41.semantic_status}"
    )
    assert u41.sub_questions == (), "must not fabricate sub_questions"
    assert u41.unit_type == "composite_unit"
    # parent leaf compiled
    leaf_ids = {l.unit_id for l in comp.leaves}
    assert "U41" in leaf_ids, f"U41 parent must be a compiled leaf, got {leaf_ids}"
    assert not any(i.endswith(".sub") for i in leaf_ids), "no fake .sub leaf"

    # Material must be compiled for composite
    assert any(m.unit_id == "U41" for m in comp.materials), (
        "U41 shared material must compile"
    )

    # Gate must not reject for missing fake sub
    decision = evaluate(root=u41, ir=ir, compiled=comp, resolved_run=run)
    assert decision.get("decision") in ("pending_review", "auto_approve"), decision
    reasons = str(decision.get("reasons") or [])
    assert "has no compiled sub-question leaf" not in reasons
    assert "has no leaf unit" not in reasons

    # --- DB materialize via real AdmissionService ---
    # Seed a minimal candidate payload from build_payload
    from app.domains.gate.payload import build as build_payload
    from app.domains.evidence.models import CheckResult, ValidationEvent
    from app.domains.gate.admission import AdmissionService
    from app.repositories.evidence_repository import EvidenceRepository
    from app.repositories.snapshot_repository import SnapshotRepository
    from app.repositories.source_repository import SourceRepository
    from app.core.hashing import sha256_hex

    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="b.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        id=SVID, document_id=doc.id, artifact_kind="raw_l1", role="native",
        provider="native",
        body_text="\n".join(l.text for l in lines),
        body_hash=sha256_hex([l.text for l in lines]),
        integrity_hash=sha256_hex([l.text for l in lines]),
        page_count=1, line_count=len(lines), status="draft",
    )
    await session.flush()
    for i, l in enumerate(lines):
        from app.models.source import DocumentSourceLine
        await src.append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref=l.line_ref, seq=l.seq,
            page_no=l.page_no, line_no_in_page=l.line_no_in_page,
            text=l.text, block_type="text", line_hash=l.line_hash,
        ))
    await session.flush()
    await src.seal_version(sv.id)
    await session.flush()

    # Build a U41-only payload for a focused materialize
    # Re-use full run but Gate/Admission on U41 root
    payload_one = build_payload(
        root=u41, ir=ir, compiled=comp, resolved_run=run,
    )
    ann = await SnapshotRepository(session).create_semantic_annotation(
        source_version_id=sv.id,
        annotation_schema_version="semantic-metadata-annotation/v0.3",
        prompt_version="t", model_config_hash=sha256_hex("m"),
        payload={"semantic_units": [], "document_metadata_claims": {}},
        status="valid",
        logical_execution_stage="ann",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    # Force pending_review materialize (fill_in not strict-auto)
    gate = dict(decision)
    gate["decision"] = "pending_review"
    cand = await SnapshotRepository(session).create_admission_candidate(
        unit_type="composite_unit", source_version_id=sv.id,
        annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=payload_one,
        gate_decision=gate,
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    from datetime import datetime, timezone

    ev = ValidationEvent(
        event_id=f"ve-{uuid.uuid4().hex[:8]}",
        claim_id=u41.unit_id,
        validation_result="validated",
        checks=(CheckResult(check_id="X", result="pass"),),
        validation_method="frozen_header_rule",
        validator="gate/v1",
        validated_at=datetime.now(timezone.utc),
    )
    await EvidenceRepository(session).append_event(ev, candidate_id=cand.id, source_version_id=sv.id)
    await session.flush()

    snap = SnapshotRepository(session)
    await snap.append_review_trail(cand.id, {
        "decision": "approve",
        "verified_by": "human",
        "reviewer_id": "e2e-reviewer",
        "confirmed_fields": ["content", "belongs_to"],
    })
    await session.flush()

    result = await AdmissionService(session).approve(
        candidate_id=cand.id,
        provenance={
            "source": "human",
            "reviewer_id": "e2e-reviewer",
            "confirmed_fields": ["content", "belongs_to"],
        },
    )
    assert result.decision_status == "approved", result
    # ONE Question for the composite
    # Scope to THIS test's source_version — never count the whole DB.
    insts = (await session.execute(
        select(QuestionInstance).where(QuestionInstance.source_version_id == sv.id)
    )).scalars().all()
    qs = (await session.execute(
        select(Question).join(QuestionInstance)
        .where(QuestionInstance.source_version_id == sv.id)
    )).scalars().all()
    inst_id = insts[0].id if insts else None
    answers = (
        await session.execute(
            select(InstanceRoleContent).where(
                InstanceRoleContent.instance_id == inst_id,
                InstanceRoleContent.role == "answer",
            )
        )
    ).scalars().all()
    stems = (
        await session.execute(
            select(InstanceRoleContent).where(
                InstanceRoleContent.instance_id == inst_id,
                InstanceRoleContent.role == "stem",
            )
        )
    ).scalars().all()

    assert len(qs) == 1, f"composite must create 1 Question, got {len(qs)}"
    assert len(insts) == 1, f"composite must create 1 Instance, got {len(insts)}"
    assert stems, "stem content must be persisted"
    assert answers, "answer content must be persisted"
    # No fake sub unit in persisted identity
    for a in answers:
        st = a.answer_status or {}
        assert ".sub" not in str(st.get("binding_unit_id") or ""), (
            f"fake sub leaked into DB: {st}"
        )
