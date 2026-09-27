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
from app.core.identity_gate import GATE_BLOCK, evaluate_identity_gate
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
from .boundary import (
    CODE_BROKEN_LINE_REFERENCE,
    CODE_BROKEN_MATERIAL_REFERENCE,
    enforce_interface_scope,
    normalize_unit_type,
)
from .manifest_reader import Manifest, ManifestUnit, find_manifests, load_manifest
from .source_loader import SourceLine, compute_body_hash, load_source_lines


def _declared_identity_version(manifest_path: Path) -> object:
    """窄读 Producer manifest 声明的 `identity_version`（verbatim，不解释、不默认）。

    M1 `read_manifest_identity` 按其**冻结设计**只暴露 `source_content_sha256`，
    不读取 Interface Scope 版本字段；此处只取该声明字段本身。**判定权 100% 在
    `boundary.enforce_interface_scope`**——本函数不判定、不归一化、不给默认值，
    因此不构成第二套 identity validation 系统（X2.6 task §4 / F-INT-01）。

    字段缺失 / JSON null → `None`（= 未声明），交由边界判定为
    `MISSING_IDENTITY_VERSION` 拒绝，**绝不默认为 2**。

    前置条件：M1 已成功解析该 JSON（`ManifestReadError` 已在此前短路），
    故本函数不会因 JSON 不可解析而上抛。
    """
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None
    return raw.get("identity_version")


def _verify_identity_boundary(
    manifest_path: Path,
    source_path: Path,
    resolver_ir_path: Path | None = None,
) -> dict:
    """Consumer Identity Verification — Interface Scope + M1→M2→M3→M4→M5 完整边界验证。

    在任何 semantic consumption（annotation payload / ResolvedRun / IR / Compiler /
    Gate / Admission）之前执行。任一轴拒绝 → 下游完全不执行。

    两轴**正交**，必须同时通过（AND 语义）：

    1. **Interface Scope**（F-INT-08）：输入属 Frozen Contract v0.2 Interface Scope，
       即 `identity_version == 2`。由唯一权威接入点
       `boundary.enforce_interface_scope` → `normalize_interface_identity` 判定。
    2. **Identity authenticity**（M1–M5，冻结设计，未改动）：manifest 声明 SHA
       与 raw bytes 实算 SHA 一致。

    判定顺序与 runtime invariant 一致：先证明 identity 有效，再确认 Interface Scope
    成员资格。M5 已拒绝时保留 M1–M5 的原始 reason code（既有行为与断言不变）；
    仅当 M5 放行而 Interface Scope 拒绝时，以边界错误码阻断。

    Returns:
        dict with keys: gate, identity_state, semantic_state, reason, mismatches,
        interface_scope。其中 `interface_scope` 在 M1 成功读取 manifest 后恒存在；
        M1/M2 早期返回（manifest_read_error / source_bytes_error）仅含前五键，
        且已 `gate=BLOCK`——失败同样发生在边界，下游不执行。
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

    # ── Interface Scope gate（F-INT-08 / F-INT-01）─────────────────────────
    # Frozen Contract v0.2 Interface Scope 字段口径：identity_version == 2。
    # 判定由唯一权威接入点 enforce_interface_scope 承担（→ normalize_interface_identity），
    # 此处不复制规则、不建第二套校验体系。执行位置在集成边界，先于一切
    # semantic consumption，故 `identity_version != 2` 在进入 IRBuilder / Compiler /
    # Gate 之前即被拒绝——这是 Interface Boundary Enforcement，不是 V3 内部补救。
    declared_identity_version = _declared_identity_version(manifest_path)
    scope = enforce_interface_scope(manifest_sha, declared_identity_version)

    result = {
        "gate": decision.gate,
        "identity_state": decision.identity_state,
        "semantic_state": decision.semantic_state,
        "reason": decision.reason,
        "mismatches": list(decision.mismatches),
        # Producer 声明值 verbatim 保留（provenance：原始 identity 是什么），
        # 不解释、不改写、不作为放行依据。
        "interface_scope": {
            "accepted": scope.accepted,
            "code": scope.code,
            "declared_identity_version": declared_identity_version,
            "reason": scope.reason,
        },
    }
    if ir_error is not None:
        result["ir_error"] = ir_error

    # AND 语义：两轴任一拒绝即阻断。M5 已拒绝 → 原样返回（既有 reason code 不变）。
    if decision.gate == GATE_BLOCK:
        return result

    # M5 放行但不属于 Interface Scope → 以稳定边界错误码显式阻断。
    # 不存在 `version != 2 → 当成 v2`，也不存在 `version != 2 → fallback → 继续运行`。
    if not scope.accepted:
        result["gate"] = GATE_BLOCK
        result["reason"] = scope.reason
        result["mismatches"] = list(decision.mismatches) + [scope.code]
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
        else:
            # broken reference（行号越界 / 反转区间）：显式留痕，绝不静默丢弃。
            # Frozen Contract §4.2-5「任何处置不得静默丢弃」；X2.6 task §13 No Silent Repair。
            # 错误码按 role 区分：material 断链与一般行区间断链是不同事实。
            unresolved.append({
                "reference_id": f"ref-{unit_id}.{role}" + (f".{label}" if label else ""),
                "role": role,
                "resolution_status": "missing",
                "evidence": (f"lines {span} out of range 1..{len(lines)}",),
                "code": (
                    CODE_BROKEN_MATERIAL_REFERENCE
                    if role == "material"
                    else CODE_BROKEN_LINE_REFERENCE
                ),
            })

    def _try_options_region(unit: ManifestUnit):
        """options: per-label spans when available; fallback to single region."""
        if unit.options:
            for opt in unit.options:
                s = _make_resolved_span(unit.unit_id, "option", lines,
                                        opt.start_line, opt.end_line,
                                        sv_id, label=opt.label)
                if s is not None:
                    spans.append(s)
                else:
                    unresolved.append({
                        "reference_id": f"ref-{unit.unit_id}.option.{opt.label}",
                        "role": "option",
                        "resolution_status": "missing",
                        "evidence": (f"option {opt.label} lines {opt.start_line}-{opt.end_line} out of range",),
                        "code": CODE_BROKEN_LINE_REFERENCE,
                    })
        elif unit.options_lines:
            start, end = unit.options_lines
            _try(unit.unit_id, "options", (start, end), sv_id)

    def _answer_span(unit: ManifestUnit) -> tuple[int, int] | None:
        """answer_lines 优先；fallback 到 answer_evidence_lines（v2.4+）。"""
        return unit.answer_lines or unit.answer_evidence_lines

    for unit in manifest.units:
        # 边界归一化（Class A，OD-2 授权映射）：Producer legacy → canonical。
        # 失败即显式上抛；不再 `else → composite` 静默 fallback（X2.6 task §13）。
        norm = normalize_unit_type(unit.unit_type)
        if norm.canonical_unit_type == "standalone_unit":
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
                    # 显式携带真实语义态，避免 incomplete/unknown 被「not_ready」
                    # 一词掩盖真实原因（Frozen Contract §4.2-1；X2.6 task §13）。
                    # 处置路由**不变**（unknown → pending_review 机制属 OQ-16′/OQ-19
                    # 未裁项，须 Owner 单独授权，本层不实施）。
                    "semantic_status": root.semantic_status,
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

            # Candidate unit_type = canonical IR value 直通。
            # 原二元三目（判 legacy standalone 字面量则取 standalone_unit，否则取
            # composite_unit）是 silent fallback（X2.5.2 Class D）：F-M3-04 之后 IR
            # 输出域已是 {standalone_unit, composite_unit}，该三目会把**每个**
            # standalone_unit 误判为 composite_unit。词表归一化已在集成边界完成（OD-2），
            # 此处只需直通；Gate 侧 `_candidate_unit_type` 仍做 fail-closed 防御（M.3）。
            unit_type = root.unit_type
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
