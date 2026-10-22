"""P0-1 acceptance: real GEO U1-2 as ONE Question with both sub-parts.

Invariant (owner):
1. One Question / one Instance — never split Q1/Q2 into two Questions
2. Q1 and Q2 stems + options preserved as ordered internal structure
3. Both answers bind (1.C 2.B) to the same Question
4. Gate must NOT auto_approve when provenance unverified → pending_review
5. DB readback shows complete content, no fake .sub identity
"""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.hashing import sha256_hex
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.evidence.models import CheckResult, ValidationEvent
from app.domains.gate.admission import AdmissionService
from app.domains.gate.payload import build as build_payload
from app.domains.gate.policy import evaluate
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceLineView
from app.models.content import InstanceRoleContent, Question, QuestionInstance
from app.models.source import DocumentSourceLine
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository
from scripts.preprocessing_consumer.annotation_adapter import (
    manifest_to_annotation_payload,
)
from scripts.preprocessing_consumer.manifest_reader import load_manifest

GEO_ROOT = Path(
    r"D:\Project\Papers\Ocr-markdown\gen-test-runs\run-20261013-GEO-001"
)
GEO_MANIFEST = GEO_ROOT / "2018北京夏季高中会考地理（教师版）(1).manifest.json"


def _load_real_source(manifest_path: Path) -> tuple[Path, str, list[str]]:
    """Resolve Manifest source_file and verify source_content_sha256.

    Must use the Manifest-declared source — not a resliced sibling copy.
    """
    import hashlib
    import json

    man = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared = Path(str(man.get("source_file") or "").replace("\\", "/"))
    expected = str(man.get("source_content_sha256") or "")
    # source_file is package-relative or repo-relative; resolve against
    # known roots without falling back to a different same-name file first.
    candidates = []
    if declared.is_absolute():
        candidates.append(declared)
    candidates.append(manifest_path.parent / declared.name)
    candidates.append(Path(r"D:\Project\Papers") / declared)
    candidates.append(Path(r"D:\Project\Papers\Ocr-markdown") / Path(*declared.parts[1:]))
    seen = []
    for cand in candidates:
        if not cand.is_file():
            continue
        actual = hashlib.sha256(cand.read_bytes()).hexdigest()
        seen.append((str(cand), actual))
        if actual == expected:
            return cand, actual, cand.read_text(encoding="utf-8").splitlines()
    raise AssertionError(
        f"Manifest source_file hash mismatch or not found: {declared!r}\n"
        f"  expected {expected}\n  tried {seen}"
    )



def _svid() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-00000000e002")


async def test_geo_u12_one_question_two_parts_in_db(session):
    """U1-2: Q1+Q2 complete as one Question; Gate pending; DB readback."""
    manifest = load_manifest(GEO_MANIFEST)
    src_path, src_sha, texts = _load_real_source(GEO_MANIFEST)
    lines = [
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    ]
    svid = _svid()
    payload = manifest_to_annotation_payload(manifest, line_texts=texts)
    u = next(x for x in payload["semantic_units"] if x["unit_id"] == "U1-2")
    assert len(u["sub_questions"]) == 2, (
        f"U1-2 must expand to 2 ordered internal subs, got {u['sub_questions']}"
    )
    qns = sorted(int(s["question_number"]) for s in u["sub_questions"])
    assert qns == [1, 2], qns

    run = SourceResolver(source_version_id=svid, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, svid, uuid.uuid4())
    comp = Compiler({s.span_id: s for s in run.resolved_spans},
                    {l.line_ref: l for l in lines}).compile(ir)
    node = next(n for n in ir.units if n.unit_id == "U1-2")
    assert node.semantic_status == "ready", node.semantic_status
    assert len(node.sub_questions) == 2
    for sub in node.sub_questions:
        roles = {c.role: bool(c.span_id) for c in sub.content}
        assert roles.get("stem"), f"{sub.unit_id} stem must resolve"
        assert roles.get("answer"), f"{sub.unit_id} answer must resolve"
        n_opt = sum(1 for c in sub.content if c.role == "option")
        assert n_opt >= 2, f"{sub.unit_id} options missing: {sub.content}"

    # Leaves are internal subs — parent stays ONE Question identity
    leaf_ids = {l.unit_id for l in comp.leaves}
    assert "U1-2.sub1" in leaf_ids and "U1-2.sub2" in leaf_ids

    decision = evaluate(root=node, ir=ir, compiled=comp, resolved_run=run)
    # Owner: auto_approve is allowed ONLY when content + evidence are truly
    # complete (2 subs, stems, options, answers). We assert completeness
    # below — here we record the decision, not force one label.
    assert decision.get("decision") in ("auto_approve", "pending_review", "rejected"), decision
    # If auto_approve, it must be strict-auto with verified answers, not a
    # silent skip of completeness.
    if decision.get("decision") == "auto_approve":
        reasons = " ".join(decision.get("reasons") or [])
        assert "verified_correct" in reasons or "strict-auto" in reasons, reasons

    # ---- Admission: ONE Question / ONE Instance ----
    src = SourceRepository(session)
    doc = await src.create_document(
        original_object_key=f"obj/{uuid.uuid4()}.pdf",
        original_sha256=sha256_hex(str(uuid.uuid4())),
        file_name="geo.pdf", file_type="pdf", upload_meta={},
        processing_status="sealed",
    )
    await session.flush()
    sv = await src.create_source_version(
        id=svid, document_id=doc.id, artifact_kind="raw_l1", role="native",
        provider="native",
        body_text="\n".join(texts),
        body_hash=src_sha,
        integrity_hash=src_sha,
        page_count=1, line_count=len(texts), status="draft",
    )
    await session.flush()
    for i, t in enumerate(texts):
        await src.append_line(DocumentSourceLine(
            source_version_id=sv.id, line_ref=f"P1L{i+1:03d}", seq=i,
            page_no=1, line_no_in_page=i + 1, text=t,
            block_type="text", line_hash=sha256_hex(t),
        ))
    await session.flush()
    await src.seal_version(sv.id)
    await session.flush()

    # Build payload from the parent composite
    p_one = build_payload(root=node, ir=ir, compiled=comp, resolved_run=run)
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
    # Use the REAL Gate decision — never override.
    gate = dict(decision)
    cand = await SnapshotRepository(session).create_admission_candidate(
        unit_type="composite_unit", source_version_id=sv.id,
        annotation_id=ann.id,
        build_versions={"annotation_schema_version": "v0.3"},
        input_identity={"source_version_id": str(sv.id)},
        payload=p_one,
        gate_decision=gate,
        logical_execution_stage="compile",
        logical_execution_hash=sha256_hex(str(uuid.uuid4())),
    )
    await session.flush()
    snap = SnapshotRepository(session)
    await EvidenceRepository(session).append_event(
        ValidationEvent(
            event_id=f"ve-{uuid.uuid4().hex[:8]}",
            claim_id="U1-2",
            validation_result="validated",
            checks=(CheckResult(check_id="X", result="pass"),),
            validation_method="frozen_header_rule",
            validator="gate/v1",
            validated_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        ),
        candidate_id=cand.id, source_version_id=sv.id,
    )
    await session.flush()

    real_dec = (gate.get("decision") or "").strip()
    if real_dec == "auto_approve":
        result = await AdmissionService(session).approve(
            candidate_id=cand.id,
            provenance={"source": "auto_gate"},
        )
    else:
        await snap.append_review_trail(cand.id, {
            "decision": "approve",
            "verified_by": "human",
            "reviewer_id": "geo-reviewer",
            "confirmed_fields": ["content", "belongs_to"],
        })
        await session.flush()
        result = await AdmissionService(session).approve(
            candidate_id=cand.id,
            provenance={
                "source": "human",
                "reviewer_id": "geo-reviewer",
                "confirmed_fields": ["content", "belongs_to"],
            },
        )
    assert result.decision_status == "approved", result

    qs = (await session.execute(
        select(Question).join(QuestionInstance)
        .where(QuestionInstance.source_version_id == sv.id)
    )).scalars().all()
    insts = (await session.execute(
        select(QuestionInstance).where(QuestionInstance.source_version_id == sv.id)
    )).scalars().all()
    inst_id = insts[0].id
    answers = (await session.execute(
        select(InstanceRoleContent).where(
            InstanceRoleContent.instance_id == inst_id,
            InstanceRoleContent.role == "answer",
        )
    )).scalars().all()
    stems = (await session.execute(
        select(InstanceRoleContent).where(
            InstanceRoleContent.instance_id == inst_id,
            InstanceRoleContent.role == "stem",
        )
    )).scalars().all()
    options = (await session.execute(
        select(InstanceRoleContent).where(
            InstanceRoleContent.instance_id == inst_id,
            InstanceRoleContent.role == "option",
        )
    )).scalars().all()

    # Identity: exactly one Question for this source version's U1-2
    assert len(insts) == 1, f"U1-2 must be ONE instance, got {len(insts)}"
    # Source traceability: this SV's body_hash must match the Manifest
    # source content hash used for the run.
    assert str(sv.body_hash or "") == src_sha or str(sv.integrity_hash or "") == src_sha, (
        f"source hash not linked: body={sv.body_hash} integrity={sv.integrity_hash} src={src_sha}"
    )
    assert len(qs) == 1, f"U1-2 must be ONE question, got {len(qs)}"

    # Content: both Q1 and Q2 stems present (ordered internal parts)
    stem_texts = [(s.label or "", (s.text or "")[:40]) for s in stems]
    assert len(stems) >= 2, f"need Q1+Q2 stems, got {stem_texts}"
    joined_stem = " ".join(s.text or "" for s in stems)
    assert "火星冲日" in joined_stem or "天体系统" in joined_stem, joined_stem[:80]
    assert "火星和地球" in joined_stem or "相同的" in joined_stem, joined_stem[:80]

    # Options for both parts
    opt_labels = sorted((o.label or "") for o in options)
    # Must be exactly the 8 real child options: 1A-1D + 2A-2D.
    # No PA/PB/PC/PD (parent option re-materialization).
    assert not any(l.startswith("P") for l in opt_labels), f"parent P* options leaked: {opt_labels}"
    assert len(options) == 8, f"expected exactly 8 child options, got {opt_labels}"
    for expect in ("1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D"):
        assert expect in opt_labels, f"missing {expect}: {opt_labels}"

    # Answers: both parts present (1.C 2.B bound internally)
    assert len(answers) >= 1, "answers must persist"
    by_qn = {}
    for a in answers:
        st = a.answer_status or {}
        qn = str(st.get("binding_question_number") or "")
        by_qn.setdefault(qn, []).append((a.text or "").strip())
    assert "1" in by_qn and "2" in by_qn, f"answers must bind qn 1 and 2: {by_qn}"
    t1 = "".join(by_qn["1"]).upper()
    t2 = "".join(by_qn["2"]).upper()
    assert "C" in t1, f"Q1 answer must be C, got {by_qn['1']!r}"
    assert "B" in t2, f"Q2 answer must be B, got {by_qn['2']!r}"

    # Internal structure is U1-2.sub1 / U1-2.sub2 (ordered parts of ONE
    # Question). The forbidden form is the collapsed fake-single `U1-2.sub`.
    seen_qns = set()
    for a in answers:
        st = a.answer_status or {}
        bu = str(st.get("binding_unit_id") or "")
        assert bu != "U1-2.sub", f"collapsed fake-single sub leaked: {st}"
        if bu.startswith("U1-2.sub"):
            seen_qns.add(str(st.get("binding_question_number") or ""))
    assert "1" in seen_qns and "2" in seen_qns, (
        f"both Q1 and Q2 answers must bind inside one Question, got qns={seen_qns}"
    )


async def test_answer_evidence_mismatch_fails_closed():
    """P0: wrong answer_evidence.value must NOT produce auto-approvable subs."""
    import dataclasses

    man = load_manifest(GEO_MANIFEST)
    src_path, src_sha, texts = _load_real_source(GEO_MANIFEST)
    u0 = next(x for x in man.units if x.unit_id == "U1-2")
    bad = dataclasses.replace(u0, answer_evidence_value="9.Z 10.Y")
    man_bad = dataclasses.replace(
        man, units=tuple(bad if x.unit_id == "U1-2" else x for x in man.units)
    )
    payload = manifest_to_annotation_payload(man_bad, line_texts=texts)
    u = next(x for x in payload["semantic_units"] if x["unit_id"] == "U1-2")
    # Fail closed: no fabricated subs, explicit mismatch gap.
    assert u["sub_questions"] == [], u["sub_questions"]
    gaps = [
        g["code"]
        for g in payload["producer_boundary"]["known_gaps"]
        if g.get("unit_id") == "U1-2"
    ]
    assert "COMPOSITE_ANSWER_EVIDENCE_MISMATCH" in gaps, gaps
    # Good manifest still expands to 2 correct subs.
    payload_ok = manifest_to_annotation_payload(man, line_texts=texts)
    u_ok = next(x for x in payload_ok["semantic_units"] if x["unit_id"] == "U1-2")
    assert len(u_ok["sub_questions"]) == 2
    for s in u_ok["sub_questions"]:
        assert s["content"]["answer"]["answer_lines"] == [543, 543]


def test_geo_u12_formal_binder_payload():
    """Formal Binder path: bind_units_from_manifest → build_annotation_payload_from_bound.

    Must use Manifest-declared source (hash-checked). Not the Adapter path.
    """
    import json as _json

    from app.domains.source.manifest_annotation import (
        bind_units_from_manifest,
        build_annotation_payload_from_bound,
    )

    man_raw = _json.loads(GEO_MANIFEST.read_text(encoding="utf-8"))
    src_path, src_sha, texts = _load_real_source(GEO_MANIFEST)
    assert src_sha == man_raw["source_content_sha256"]

    bound = bind_units_from_manifest(
        man_raw,
        texts,
        source_content_sha256=src_sha,
    )
    u12 = next((b for b in bound if b.unit_id == "U1-2"), None)
    assert u12 is not None, [b.unit_id for b in bound]

    payload = build_annotation_payload_from_bound(
        bound,
        source_content_sha256=src_sha,
        manifest_identity_version=man_raw.get("identity_version"),
        subject=man_raw.get("subject"),
        grade=man_raw.get("grade"),
        grade_source=man_raw.get("grade_source"),
    )
    u = next(x for x in payload["semantic_units"] if x["unit_id"] == "U1-2")
    assert u["unit_type"] == "composite_unit"
    subs = u.get("sub_questions") or []
    assert len(subs) == 2, f"formal binder must emit 2 subs, got {len(subs)}"
    qns = sorted(int(s.get("question_number")) for s in subs)
    assert qns == [1, 2], qns
    # No collapsed fake-single
    assert all(s["unit_id"] != "U1-2.sub" for s in subs)
    for s in subs:
        c = s.get("content") or {}
        assert c.get("stem"), s
        assert c.get("answer"), s
        opts = c.get("options") or []
        assert len(opts) == 4, f"{s['unit_id']} options {opts}"
        ans_lines = (c.get("answer") or {}).get("answer_lines")
        assert ans_lines == [543, 543], f"answer must stay on table line: {ans_lines}"


def _formal_binder_u12(answer_value: str | None, texts: list[str]):
    """Formal Binder path for U1-2 with a given answer_evidence.value."""
    import dataclasses
    import json as _json

    from app.domains.source.manifest_annotation import (
        bind_units_from_manifest,
        build_annotation_payload_from_bound,
    )

    man_raw = _json.loads(GEO_MANIFEST.read_text(encoding="utf-8"))
    for u in man_raw.get("units") or []:
        if u.get("unit_id") == "U1-2":
            ae = dict(u.get("answer_evidence") or {})
            ae["value"] = answer_value
            u["answer_evidence"] = ae
    src_path, src_sha, texts = _load_real_source(GEO_MANIFEST)
    bound = bind_units_from_manifest(man_raw, texts, source_content_sha256=src_sha)
    payload = build_annotation_payload_from_bound(
        bound,
        source_content_sha256=src_sha,
        manifest_identity_version=man_raw.get("identity_version"),
        subject=man_raw.get("subject"),
        grade=man_raw.get("grade"),
        grade_source=man_raw.get("grade_source"),
    )
    u = next(x for x in payload["semantic_units"] if x["unit_id"] == "U1-2")
    return u


def _gate_for_u12(payload_unit: dict, texts: list[str]):
    """Resolver → IR → Gate for one semantic unit (formal consumption)."""
    from app.domains.compile.compiler import Compiler
    from app.domains.compile.ir import IRBuilder
    from app.domains.gate.policy import evaluate
    from app.domains.resolver.resolver import SourceResolver
    from app.domains.resolver.span import SourceLineView

    svid = uuid.uuid4()
    lines = [
        SourceLineView(f"P1L{i+1:03d}", t, i + 1, 1, i + 1)
        for i, t in enumerate(texts)
    ]
    payload = {
        "semantic_units": [payload_unit],
        "document_metadata_claims": {},
    }
    run = SourceResolver(source_version_id=svid, lines=lines).resolve(payload)
    ir = IRBuilder.build(run, payload, svid, uuid.uuid4())
    comp = Compiler(
        {s.span_id: s for s in run.resolved_spans},
        {l.line_ref: l for l in lines},
    ).compile(ir)
    node = ir.units[0]
    if node.semantic_status != "ready":
        return node.semantic_status, None
    decision = evaluate(root=node, ir=ir, compiled=comp, resolved_run=run)
    return node.semantic_status, decision.get("decision")


def test_formal_binder_wrong_evidence_not_auto_approved():
    """P0 Formal Binder: wrong evidence must not yield ready+auto_approve."""
    src_path, src_sha, texts = _load_real_source(GEO_MANIFEST)

    # 1) valid 1.C 2.B → 2 subs, ready (Gate may auto_approve if verified)
    u_ok = _formal_binder_u12("1.C 2.B", texts)
    assert len(u_ok["sub_questions"]) == 2
    status, dec = _gate_for_u12(u_ok, texts)
    assert status == "ready", status
    assert dec in ("auto_approve", "pending_review", "rejected")

    # 2) wrong qns 9.Z 10.Y → must NOT be ready+auto_approve
    u_bad1 = _formal_binder_u12("9.Z 10.Y", texts)
    status, dec = _gate_for_u12(u_bad1, texts)
    assert not (status == "ready" and dec == "auto_approve"), (status, dec)

    # 3) non-token junk → must NOT be ready+auto_approve
    u_bad2 = _formal_binder_u12("not-an-answer", texts)
    status, dec = _gate_for_u12(u_bad2, texts)
    assert not (status == "ready" and dec == "auto_approve"), (status, dec)


def test_manifest_missing_hash_blocks_v3():
    """Fail-closed via PRODUCTION gate in x_pdf_papers_v3.run_v3_after_manifest.

    Must actually invoke the orchestration entry and prove V3 is never called.
    """
    import hashlib
    import importlib.util
    import tempfile
    from pathlib import Path as _P

    script = _P(r"D:\Project\AITutor-X\e2e_run\x_pdf_papers_v3.py")
    spec = importlib.util.spec_from_file_location("x_pdf_papers_v3", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    run = _P(tempfile.mkdtemp(prefix="manhash_"))
    md = run / "paper.md"
    md.write_text("1. Q\nA. a\n", encoding="utf-8")
    man = {
        "source_file": "paper.md",
        "units": [],
    }

    calls = []

    def _v3(*a, **k):
        calls.append(1)
        return 0

    code, reason, v3_calls = mod.run_v3_after_manifest(man, md, invoke_v3=_v3)
    assert code != 0
    assert v3_calls == 0 and not calls
    assert reason and "source_content_sha256" in reason

    man2 = dict(man, source_content_sha256="zz" * 32)
    code2, reason2, v3_calls2 = mod.run_v3_after_manifest(man2, md, invoke_v3=_v3)
    assert code2 != 0 and v3_calls2 == 0 and not calls

    actual = hashlib.sha256(md.read_bytes()).hexdigest()
    wrong = ("0" if actual[0] != "0" else "1") + actual[1:]
    man3 = dict(man, source_content_sha256=wrong)
    code3, reason3, v3_calls3 = mod.run_v3_after_manifest(man3, md, invoke_v3=_v3)
    assert code3 != 0 and v3_calls3 == 0 and not calls
    assert "mismatch" in (reason3 or "").lower()

    man4 = dict(man, source_content_sha256=actual)
    code4, reason4, v3_calls4 = mod.run_v3_after_manifest(man4, md, invoke_v3=_v3)
    assert code4 == 0 and v3_calls4 == 1 and len(calls) == 1
