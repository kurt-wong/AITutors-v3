"""Phase 0 双轨执行器：preprocessing manifest → V3 Gate/Admission 消费验证。

用法：
    cd backend
    python -m scripts.preprocessing_consumer.runner \
        --corpus "D:/Project/Papers/Ocr-markdown/reslice-p2-b1" \
        --output scripts/preprocessing_consumer/consumer-report.json

边界（85 号 §5）：
- 不改 backend/app/ 生产代码
- 不建正式 API
- 只读 preprocessing 产出
- 输出是报告，不是入库结果
"""

import argparse
import asyncio
import json
import sys
import traceback
import uuid
from pathlib import Path

# 确保 backend 根在 sys.path
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import os
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors",
)

from sqlalchemy import delete

from app.core.hashing import sha256_hex
from app.db.session import async_session_maker
from app.domains.gate.service import GateService
from app.repositories.source_repository import SourceRepository
from app.models.snapshot import AdmissionCandidate, SemanticAnnotation
from app.models.source import Document, DocumentSourceLine, DocumentSourceVersion, SourceFigure

from .annotation_adapter import manifest_to_annotation_payload
from .boundary import enforce_interface_scope
from .manifest_reader import Manifest, find_manifests, load_manifest
from .resolved_span_adapter import manifest_to_resolved_spans
from .source_loader import SourceLine, compute_body_hash, load_source_lines


def _classify_error(exc: Exception) -> str:
    """把异常分类为 Gap 类型。"""
    msg = str(exc).lower()
    if "forbidden" in msg or "validation" in msg or "invalid" in msg:
        return "schema_gap"
    if "resolver" in msg or "unresolved" in msg:
        return "philosophy_gap"
    if "not found" in msg:
        return "schema_gap"
    return "implementation_bug"


async def _create_source_records(
    session,
    source_lines: list[SourceLine],
    source_path: Path,
) -> tuple[uuid.UUID, uuid.UUID]:
    """创建 Document + DocumentSourceVersion(sealed) + DocumentSourceLine[]。"""
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


async def _track_a(
    session,
    manifest: Manifest,
    source_lines: list[SourceLine],
    source_path: Path,
) -> dict:
    """Track A: manifest → V3 annotation payload → GateService。"""
    result: dict = {"track": "A", "status": "unknown"}

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
            logical_execution_hash=sha256_hex(f"track-a:{sv_id}:{json.dumps(payload, sort_keys=True)}"),
        )
        session.add(ann)
        await session.flush()

        gate = GateService(session)
        candidates, skipped = await gate.run(
            source_version_id=sv_id,
            annotation_id=ann.id,
            task_type="preprocessing_consumer_phase0",
        )

        result["candidates_created"] = len(candidates)
        result["skipped"] = list(skipped)
        result["gate_pass"] = len([
            c for c in candidates
            if c.gate_decision and c.gate_decision.get("decision") == "auto_approve"
        ])
        result["gate_rejected"] = len([
            c for c in candidates
            if c.gate_decision and c.gate_decision.get("decision") == "rejected"
        ])
        result["pending_review"] = len([
            c for c in candidates if c.decision_status == "pending_review"
        ])
        result["status"] = "completed"

    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)[:500]
        result["error_type"] = _classify_error(exc)

    return result


async def _track_b(
    session,
    manifest: Manifest,
    source_lines: list[SourceLine],
    source_path: Path,
) -> dict:
    """Track B: manifest → ResolvedSpan 直通（只验证构造，不跑 Gate）。"""
    result: dict = {"track": "B", "status": "unknown"}

    try:
        doc_id, sv_id = await _create_source_records(session, source_lines, source_path)

        resolved, unresolved = manifest_to_resolved_spans(manifest, source_lines, sv_id)

        result["spans_constructed"] = len(resolved)
        result["spans_failed"] = len(unresolved)
        result["unresolved_detail"] = [
            {"ref": u["reference_id"], "status": u["resolution_status"]}
            for u in unresolved[:10]
        ]

        # 验证 line_refs 在 source lines 中存在
        valid_refs = {sl.line_ref for sl in source_lines}
        bad_spans = sum(
            1 for s in resolved
            if any(r not in valid_refs for r in s["line_refs"])
        )
        result["spans_with_bad_refs"] = bad_spans

        result["status"] = "completed"

    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)[:500]

    return result


async def run_corpus(corpus_root: Path, output_path: Path):
    manifests = find_manifests(corpus_root)
    print(f"Found {len(manifests)} manifests in {corpus_root}")

    report: dict = {
        "dataset": str(corpus_root),
        "version": "phase0-v0.1",
        "total_manifests": len(manifests),
        "total_units": 0,
        "interface_scope_blocked": 0,
        "track_a": {"completed": 0, "error": 0, "gate_pass_total": 0, "candidates_total": 0},
        "track_b": {"completed": 0, "error": 0, "spans_total": 0, "unresolved_total": 0},
        "papers": [],
        "contract_gaps": [],
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
            report["papers"].append({"paper": paper_id, "error": f"source not found: {source_path}"})
            continue

        try:
            source_lines = load_source_lines(source_path)
        except Exception as exc:
            report["papers"].append({"paper": paper_id, "error": f"source load: {exc}"})
            continue

        report["total_units"] += len(manifest.units)

        # ── Interface Scope gate（F-INT-08 / F-INT-01）────────────────────        # Track A 直接进入 V3 生产 GateService（`gate.service.GateService.run`），
        # Track B 产出 V3 ResolvedSpan；两者都是 preprocessing → V3 的实际消费入口。
        # 此前本 runner **无任何** interface identity 检查，构成
        # `identity_version == 2` 的 bypass。现与 runner_b2 共用同一权威接入点
        # `boundary.enforce_interface_scope`（不复制规则、不建第二套校验体系）。
        # 拒绝 → 显式失败并跳过 Track A/B，任何 V3 semantic consumption 不执行。
        scope = enforce_interface_scope(
            manifest.source_content_sha256, manifest.identity_version
        )
        if not scope.accepted:
            report["interface_scope_blocked"] += 1
            report["papers"].append({
                "paper": paper_id,
                "units": len(manifest.units),
                "prompt_version": manifest.prompt_version,
                "interface_scope_rejected": {
                    "accepted": False,
                    "code": scope.code,
                    # Producer 声明值 verbatim 保留（provenance），不解释、不改写。
                    "declared_identity_version": manifest.identity_version,
                    "reason": scope.reason,
                    "downstream_executed": False,
                },
            })
            continue

        paper_result: dict = {
            "paper": paper_id,
            "source": str(source_path),
            "units": len(manifest.units),
            "prompt_version": manifest.prompt_version,
        }

        # Track A
        async with async_session_maker() as session:
            try:
                ta = await _track_a(session, manifest, source_lines, source_path)
            except Exception as exc:
                ta = {"track": "A", "status": "session_error", "error": str(exc)[:500]}
            finally:
                await session.rollback()
        paper_result["track_a"] = ta
        if ta.get("status") == "completed":
            report["track_a"]["completed"] += 1
            report["track_a"]["gate_pass_total"] += ta.get("gate_pass", 0)
            report["track_a"]["candidates_total"] += ta.get("candidates_created", 0)
        else:
            report["track_a"]["error"] += 1
            report["contract_gaps"].append({
                "paper": paper_id, "track": "A",
                "type": ta.get("error_type", "unknown"),
                "error": ta.get("error", "")[:200],
            })

        # Track B
        async with async_session_maker() as session:
            try:
                tb = await _track_b(session, manifest, source_lines, source_path)
            except Exception as exc:
                tb = {"track": "B", "status": "session_error", "error": str(exc)[:500]}
            finally:
                await session.rollback()
        paper_result["track_b"] = tb
        if tb.get("status") == "completed":
            report["track_b"]["completed"] += 1
            report["track_b"]["spans_total"] += tb.get("spans_constructed", 0)
            report["track_b"]["unresolved_total"] += tb.get("spans_failed", 0)
        else:
            report["track_b"]["error"] += 1

        report["papers"].append(paper_result)

    report["summary"] = {
        "track_a_completion_rate": report["track_a"]["completed"] / max(len(manifests), 1),
        "track_b_completion_rate": report["track_b"]["completed"] / max(len(manifests), 1),
        "total_contract_gaps": len(report["contract_gaps"]),
    }

    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport: {output_path}")
    print(f"Interface Scope blocked: {report['interface_scope_blocked']}")
    print(f"Track A: {report['track_a']['completed']}/{len(manifests)} ok, {report['track_a']['error']} errors")
    print(f"Track B: {report['track_b']['completed']}/{len(manifests)} ok, {report['track_b']['error']} errors")
    print(f"Contract gaps: {len(report['contract_gaps'])}")


def main():
    parser = argparse.ArgumentParser(description="Phase 0 preprocessing consumer")
    parser.add_argument("--corpus", type=Path,
                        default=Path(r"D:\Project\Papers\Ocr-markdown\reslice-p2-b1"))
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent / "consumer-report.json")
    args = parser.parse_args()
    asyncio.run(run_corpus(args.corpus, args.output))


if __name__ == "__main__":
    main()
