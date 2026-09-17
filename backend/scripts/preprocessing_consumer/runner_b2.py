"""Phase 0.2: Track B → IRBuilder → Compiler → Gate → Admission 完整链验证。

与 Phase 0 的 Track B 不同：不只验证 span 构造，而是走完 V3 的完整准入链。
跳过 SourceResolver（preprocessing 已提供精确行号），直接从 ResolvedRun 进入 IR。

用法：
    cd backend
    python -m scripts.preprocessing_consumer.runner_b2 \
        --corpus "D:/Project/Papers/Ocr-markdown/reslice-p2-b1" \
        --output scripts/preprocessing_consumer/consumer-report-b2.json
"""

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import os
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors",
)

from app.core.hashing import sha256_hex
from app.core.identity_gate import evaluate_identity_gate
from app.core.identity_verifier import verify_identity
from app.core.ir_identity import IRReadError, read_ir_identity
from app.core.manifest_identity import ManifestReadError, read_manifest_identity
from app.core.raw_bytes_identity import load_raw_bytes_identity
from app.db.session import async_session_maker
from app.domains.compile.compiler import Compiler
from app.domains.compile.ir import IRBuilder
from app.domains.gate.payload import build as build_payload
from app.domains.gate.policy import evaluate
from app.domains.resolver.span import ResolvedRun, ResolvedSpan
from app.models.snapshot import AdmissionCandidate, SemanticAnnotation
from app.models.source import DocumentSourceLine
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository

from .annotation_adapter import manifest_to_annotation_payload
from .manifest_reader import Manifest, ManifestUnit, find_manifests, load_manifest
from .source_loader import SourceLine, compute_body_hash, load_source_lines


def _verify_identity_boundary(
    manifest_path: Path,
    source_path: Path,
    resolver_ir_path: Path | None = None,
) -> dict:
    """Consumer Identity Verification — M1→M2→M3→M4→M5 完整边界验证。

    在任何 semantic consumption（IR/Compiler/Gate/Admission）之前执行。
    M5 BLOCK → 下游完全不执行。

    Returns:
        dict with keys: gate, identity_state, semantic_state, reason, mismatches
    """
    try:
        # M1: Manifest identity
        manifest_id = read_manifest_identity(manifest_path)
        manifest_sha = manifest_id.source_content_sha256
    except ManifestReadError as e:
        return {
            "gate": "BLOCK", "identity_state": "FAILED",
            "semantic_state": None, "reason": f"manifest_read_error: {e}",
            "mismatches": ("manifest_read_error",),
        }

    try:
        # M2: Raw bytes identity
        raw_id = load_raw_bytes_identity(source_path)
        computed_sha = raw_id.sha256
    except (FileNotFoundError, OSError) as e:
        return {
            "gate": "BLOCK", "identity_state": "FAILED",
            "semantic_state": None, "reason": f"source_bytes_error: {e}",
            "mismatches": ("source_bytes_error",),
        }

    # M3: IR identity（IR 可缺失 — Semantic Pending 正常态）
    # IR 读取失败不影响 Identity 判定（正交性原则），仅记录错误。
    # Phase 2.5: 传递 computed_sha 用于 batch IR 的确定性内容关联定位。
    ir_sha = None
    ir_error: str | None = None
    if resolver_ir_path is not None:
        try:
            ir_id = read_ir_identity(
                resolver_ir_path,
                source_file=str(source_path),
                source_sha=computed_sha,
            )
            ir_sha = ir_id.source_content_sha256
        except IRReadError as e:
            ir_error = str(e)

    # M4: Identity verification — 始终执行，IR 错误不绕过
    verification = verify_identity(
        computed_sha=computed_sha, manifest_sha=manifest_sha, ir_sha=ir_sha
    )

    # M5: Identity Gate
    decision = evaluate_identity_gate(verification)

    result = {
        "gate": decision.gate,
        "identity_state": decision.identity_state,
        "semantic_state": decision.semantic_state,
        "reason": decision.reason,
        "mismatches": list(decision.mismatches),
    }
    if ir_error is not None:
        result["ir_error"] = ir_error
    return result


def _make_resolved_span(
    unit_id: str,
    role: str,
    lines: list[SourceLine],
    start: int,
    end: int,
    source_version_id: uuid.UUID,
    label: str | None = None,
) -> ResolvedSpan | None:
    """构造 V3 ResolvedSpan dataclass。行号越界返回 None。"""
    n = len(lines)
    if start < 1 or end > n or start > end:
        return None
    line_refs = tuple(f"P1L{i:03d}" for i in range(start, end + 1))
    texts = [lines[i - 1].text for i in range(start, end + 1)]
    text_hash = sha256_hex("\n".join(texts))
    span_id = f"sp-{unit_id}.{role}" + (f".{label}" if label else "")
    return ResolvedSpan(
        span_id=span_id,
        source_version_id=source_version_id,
        role=role,
        start_line_ref=line_refs[0],
        end_line_ref=line_refs[-1],
        line_refs=line_refs,
        granularity="line",
        start_offset=None,
        end_offset=None,
        text_hash=text_hash,
        resolution_status="exact",
        evidence=(),
    )


def _build_resolved_run(
    manifest: Manifest,
    lines: list[SourceLine],
    sv_id: uuid.UUID,
) -> ResolvedRun:
    """从 manifest 构造完整 ResolvedRun。

    span_id 约定（与 IRBuilder 对齐）：
    - standalone stem/answer/explanation: sp-{unit_id}.{role}
    - standalone options: sp-{unit_id}.option.{label}（per-label）
    - composite material: sp-{unit_id}.material
    - composite sub stem/answer/explanation: sp-{unit_id}.sub.{role}
    """
    spans: list[ResolvedSpan] = []
    unresolved = []

    def _try(unit_id: str, role: str, span: tuple[int, int] | None,
             sv_id: uuid.UUID, label: str | None = None):
        if span is None:
            return
        s = _make_resolved_span(unit_id, role, lines, span[0], span[1], sv_id, label)
        if s is not None:
            spans.append(s)

    def _try_options_region(unit: ManifestUnit):
        """options_lines → 单个 options_region span（不制造 per-label A/B/C/D）。"""
        if not unit.options_lines:
            return
        start, end = unit.options_lines
        _try(unit.unit_id, "options", (start, end), sv_id)

    def _answer_span(unit: ManifestUnit) -> tuple[int, int] | None:
        """answer_lines 优先；fallback 到 answer_evidence_lines（v2.4+）。"""
        return unit.answer_lines or unit.answer_evidence_lines

    for unit in manifest.units:
        if unit.unit_type == "standalone_question":
            _try(unit.unit_id, "stem", unit.stem_lines, sv_id)
            _try(unit.unit_id, "answer", _answer_span(unit), sv_id)
            _try(unit.unit_id, "explanation", unit.explanation_lines, sv_id)
            _try_options_region(unit)
        else:
            _try(unit.unit_id, "material", unit.material_lines, sv_id)
            sub_id = f"{unit.unit_id}.sub"
            _try(sub_id, "stem", unit.questions_lines, sv_id)
            _try(sub_id, "answer", _answer_span(unit), sv_id)
            _try(sub_id, "explanation", unit.explanation_lines, sv_id)

    return ResolvedRun(
        source_version_id=sv_id,
        resolved_spans=tuple(spans),
        unresolved_references=tuple(unresolved),
    )


async def _create_source_records(
    session,
    source_lines: list[SourceLine],
    source_path: Path,
) -> tuple[uuid.UUID, uuid.UUID]:
    """创建 Document + sealed SourceVersion + SourceLines。"""
    src_repo = SourceRepository(session)
    body_text = "\n".join(l.text for l in source_lines)
    body_hash = compute_body_hash(source_lines)
    file_sha = sha256_hex(body_text)

    doc = await src_repo.create_document(
        original_object_key=f"preprocessing/{source_path.name}",
        original_sha256=file_sha,
        file_name=source_path.name,
        file_type="text/markdown",
        upload_meta={"source": "preprocessing_phase0"},
        processing_status="pending",
    )
    await session.flush()

    le_hash = sha256_hex(f"seal:preprocessing:{file_sha}")
    version = await src_repo.create_source_version(
        document_id=doc.id,
        artifact_kind="markdown",
        role="native",
        provider="native",
        body_text=body_text,
        body_hash=body_hash,
        integrity_hash=body_hash,
        page_count=1,
        line_count=len(source_lines),
        status="draft",
        logical_execution_stage="seal",
        logical_execution_hash=le_hash,
    )
    await session.flush()

    for sl in source_lines:
        await src_repo.append_line(DocumentSourceLine(
            source_version_id=version.id,
            line_ref=sl.line_ref,
            seq=sl.seq,
            page_no=sl.page_no,
            line_no_in_page=sl.line_no_in_page,
            text=sl.text,
            block_type=sl.block_type,
            line_hash=sl.line_hash,
        ))
    await session.flush()
    await src_repo.seal_version(version.id)
    await session.flush()
    return doc.id, version.id


async def _run_full_chain(
    session,
    manifest: Manifest,
    source_lines: list[SourceLine],
    source_path: Path,
    gate_decision: dict,
) -> dict:
    """Track B2: manifest → ResolvedRun → IR → Compiler → Gate → Candidate。

    gate_decision: M5 Identity Gate 决策结果（必填）。gate="BLOCK" 时，
    所有 semantic consumption（IR/Compiler/Gate/Admission）完全不执行。
    """
    result: dict = {"track": "B2", "status": "unknown"}

    # ── M5 Identity Gate: BLOCK → 完全阻断下游 ──
    if gate_decision.get("gate") == "BLOCK":
        result["status"] = "identity_blocked"
        result["identity_gate"] = gate_decision
        result["downstream_executed"] = False
        return result

    result["identity_gate"] = gate_decision

    try:
        doc_id, sv_id = await _create_source_records(session, source_lines, source_path)

        payload = manifest_to_annotation_payload(manifest)

        ann = SemanticAnnotation(
            source_version_id=sv_id,
            annotation_schema_version="semantic-metadata-annotation/v0.3",
            prompt_version=f"preprocessing-adapter/{manifest.prompt_version}",
            model_config_hash=sha256_hex(payload),
            payload=payload,
            status="valid",
            logical_execution_stage="ann",
            logical_execution_hash=sha256_hex(f"track-b2:{sv_id}"),
        )
        session.add(ann)
        await session.flush()

        resolved_run = _build_resolved_run(manifest, source_lines, sv_id)

        ir = IRBuilder.build(resolved_run, payload, sv_id, ann.id)

        line_map = {sl.line_ref: sl for sl in source_lines}
        span_map = {s.span_id: s for s in resolved_run.resolved_spans}
        compiled = Compiler(span_map, line_map).compile(ir)

        snap_repo = SnapshotRepository(session)
        ready_count = 0
        skip_count = 0
        gate_results = []

        for root in ir.units:
            if root.semantic_status != "ready":
                skip_count += 1
                gate_results.append({
                    "unit_id": root.unit_id,
                    "status": "skipped",
                    "reason": "not_ready",
                })
                continue

            ready_count += 1
            gate = evaluate(root=root, ir=ir, compiled=compiled, resolved_run=resolved_run)
            payload_dict = build_payload(root=root, ir=ir, compiled=compiled, resolved_run=resolved_run)

            gate_results.append({
                "unit_id": root.unit_id,
                "status": "evaluated",
                "decision": gate.get("decision"),
                "reasons": gate.get("reasons", []),
            })

            unit_type = "standalone_unit" if root.unit_type == "standalone_question" else "composite_unit"
            le_hash = sha256_hex(f"compile:track-b2:{sv_id}:{ann.id}:{root.unit_id}")
            candidate = await snap_repo.create_admission_candidate(
                unit_type=unit_type,
                source_version_id=sv_id,
                annotation_id=ann.id,
                build_versions={"phase0_2_r2": "v0.2"},
                input_identity={"source": "preprocessing_manifest"},
                payload=payload_dict,
                gate_decision=gate,
                logical_execution_stage="compile",
                logical_execution_hash=le_hash,
            )
            await session.flush()

        result["status"] = "completed"
        result["total_units"] = len(ir.units)
        result["ready"] = ready_count
        result["skipped"] = skip_count
        result["spans_in_run"] = len(resolved_run.resolved_spans)
        result["unresolved_in_run"] = len(resolved_run.unresolved_references)
        result["compiled_leaves"] = len(compiled.leaves)
        result["compiled_materials"] = len(compiled.materials)
        result["gate_results"] = gate_results

        decisions = [g.get("decision") for g in gate_results if g.get("status") == "evaluated"]
        result["gate_auto_approve"] = decisions.count("auto_approve")
        result["gate_rejected"] = decisions.count("rejected")
        result["gate_pending_review"] = decisions.count("pending_review")

    except Exception as exc:
        import traceback
        result["status"] = "error"
        result["error"] = str(exc)[:500]
        result["traceback"] = traceback.format_exc()[-1500:]

    return result


async def run_corpus(corpus_root: Path, output_path: Path,
                     resolver_ir_path: Path | None = None):
    manifests = find_manifests(corpus_root)
    print(f"Found {len(manifests)} manifests in {corpus_root}")
    if resolver_ir_path:
        print(f"Resolver IR: {resolver_ir_path}")

    report: dict = {
        "dataset": str(corpus_root),
        "version": "phase0.2-r2-evidence-faithful",
        "total_manifests": len(manifests),
        "total_units": 0,
        "summary": {
            "completed": 0, "error": 0, "identity_blocked": 0,
            "ready_total": 0, "skipped_total": 0,
            "gate_auto_approve": 0, "gate_rejected": 0, "gate_pending_review": 0,
            "compiled_leaves_total": 0,
        },
        "papers": [],
        "errors": [],
    }

    for i, mpath in enumerate(manifests):
        paper_id = mpath.stem.replace(".manifest", "")
        print(f"[{i+1}/{len(manifests)}] {paper_id}")

        try:
            manifest = load_manifest(mpath)
        except Exception as exc:
            report["papers"].append({"paper": paper_id, "error": f"manifest load: {exc}"})
            continue

        source_path = Path(manifest.source_file)
        if not source_path.exists():
            report["papers"].append({"paper": paper_id, "error": "source not found"})
            continue

        try:
            source_lines = load_source_lines(source_path)
        except Exception as exc:
            report["papers"].append({"paper": paper_id, "error": f"source load: {exc}"})
            continue

        report["total_units"] += len(manifest.units)

        # ── Consumer Identity Verification (M1→M5) ──
        gate_decision = _verify_identity_boundary(
            manifest_path=mpath,
            source_path=source_path,
            resolver_ir_path=resolver_ir_path,
        )

        if gate_decision.get("gate") == "BLOCK":
            paper_result = {
                "paper": paper_id,
                "units": len(manifest.units),
                "prompt_version": manifest.prompt_version,
                "result": {
                    "track": "B2",
                    "status": "identity_blocked",
                    "identity_gate": gate_decision,
                    "downstream_executed": False,
                },
            }
            report["papers"].append(paper_result)
            report["summary"]["identity_blocked"] = (
                report["summary"].get("identity_blocked", 0) + 1
            )
            continue

        async with async_session_maker() as session:
            try:
                r = await _run_full_chain(
                    session, manifest, source_lines, source_path,
                    gate_decision=gate_decision,
                )
            except Exception as exc:
                r = {"track": "B2", "status": "session_error", "error": str(exc)[:500]}
            finally:
                await session.rollback()

        paper_result = {
            "paper": paper_id,
            "units": len(manifest.units),
            "prompt_version": manifest.prompt_version,
            "result": r,
        }
        report["papers"].append(paper_result)

        if r.get("status") == "completed":
            report["summary"]["completed"] += 1
            report["summary"]["ready_total"] += r.get("ready", 0)
            report["summary"]["skipped_total"] += r.get("skipped", 0)
            report["summary"]["gate_auto_approve"] += r.get("gate_auto_approve", 0)
            report["summary"]["gate_rejected"] += r.get("gate_rejected", 0)
            report["summary"]["gate_pending_review"] += r.get("gate_pending_review", 0)
            report["summary"]["compiled_leaves_total"] += r.get("compiled_leaves", 0)
        else:
            report["summary"]["error"] += 1
            report["errors"].append({
                "paper": paper_id,
                "error": r.get("error", "")[:300],
            })

    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    s = report["summary"]
    print(f"\nReport: {output_path}")
    print(f"Completed: {s['completed']}/{len(manifests)}, Errors: {s['error']}, "
          f"Identity Blocked: {s.get('identity_blocked', 0)}")
    print(f"Ready units: {s['ready_total']}, Skipped: {s['skipped_total']}")
    print(f"Gate: auto_approve={s['gate_auto_approve']} rejected={s['gate_rejected']} pending_review={s['gate_pending_review']}")
    print(f"Compiled leaves: {s['compiled_leaves_total']}")


def main():
    parser = argparse.ArgumentParser(description="Phase 0.2 Track B full chain")
    parser.add_argument("--corpus", type=Path,
                        default=Path(r"D:\Project\Papers\Ocr-markdown\reslice-p2-b1"))
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "consumer-report-b2-r2.json")
    parser.add_argument("--resolver-ir", type=Path, default=None,
                        help="Path to batch resolver IR JSON (optional)")
    args = parser.parse_args()
    asyncio.run(run_corpus(args.corpus, args.output, resolver_ir_path=args.resolver_ir))


if __name__ == "__main__":
    main()
