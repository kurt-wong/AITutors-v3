"""Phase I-4: Evidence-aware replay 脚本。

用真实数学 PDF 的 spans 数据运行 evidence-aware diagnostic，比较 Before/After。

用法：
    cd backend
    python -m scripts.evidence_replay --source-version-id <uuid>

不进 pytest（与 live_smoke_ollama.py 模式一致）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid as uuid_mod

from sqlalchemy import select

from app.db.session import async_session_maker
from app.domains.resolver.diagnostic import diagnose_unresolved, format_diagnostic_report
from app.domains.resolver.evidence import (
    SpanEvidence,
    analyze_evidence,
    format_evidence_report,
)
from app.domains.resolver.resolver import SourceResolver
from app.domains.resolver.span import SourceFigureView, SourceLineView
from app.models.source import (
    DocumentSourceLine,
    DocumentSourceSpan,
    DocumentSourceVersion,
    SourceFigure,
)
from app.models.annotation import SemanticAnnotation


async def load_data(source_version_id: uuid_mod.UUID):
    """从 DB 读取 lines、spans、figures、annotation。"""
    async with async_session_maker() as session:
        # 读 lines
        res = await session.execute(
            select(DocumentSourceLine)
            .where(DocumentSourceLine.source_version_id == source_version_id)
            .order_by(DocumentSourceLine.seq)
        )
        db_lines = list(res.scalars().all())

        # 读 spans
        res = await session.execute(
            select(DocumentSourceSpan)
            .where(DocumentSourceSpan.source_version_id == source_version_id)
            .order_by(DocumentSourceSpan.line_ref, DocumentSourceSpan.seq)
        )
        db_spans = list(res.scalars().all())

        # 读 figures
        res = await session.execute(
            select(SourceFigure)
            .where(SourceFigure.source_version_id == source_version_id)
            .order_by(SourceFigure.figure_id)
        )
        db_figures = list(res.scalars().all())

        # 读 annotation（找到该 source version 关联的最新 valid annotation）
        res = await session.execute(
            select(SemanticAnnotation)
            .where(SemanticAnnotation.source_version_id == source_version_id)
            .order_by(SemanticAnnotation.created_at.desc())
        )
        annotation = res.scalars().first()

    return db_lines, db_spans, db_figures, annotation


def build_views(db_lines, db_spans, db_figures):
    """ORM → View 转换。"""
    lines = tuple(
        SourceLineView(
            line_ref=l.line_ref,
            text=l.text,
            seq=l.seq,
            page_no=l.page_no,
            line_no_in_page=l.line_no_in_page,
        )
        for l in db_lines
    )

    # spans_by_line: dict[line_ref, tuple[SpanEvidence, ...]]
    spans_by_line: dict[str, list[SpanEvidence]] = {}
    for s in db_spans:
        if s.line_ref not in spans_by_line:
            spans_by_line[s.line_ref] = []
        spans_by_line[s.line_ref].append(
            SpanEvidence(
                line_ref=s.line_ref,
                seq=s.seq,
                text=s.text,
                font=s.font,
                size=s.size,
                flags=s.flags,
                bbox=s.bbox,
                origin=s.origin,
            )
        )
    spans_by_line_t = {k: tuple(v) for k, v in spans_by_line.items()}

    figures = tuple(
        SourceFigureView(
            figure_id=f.figure_id,
            page_no=f.page_no,
            bbox=f.bbox,
            placement=f.placement,
            source=f.source,
            object_key=f.object_key,
            figure_hash=f.figure_hash,
        )
        for f in db_figures
    )

    return lines, spans_by_line_t, figures


def extract_marker_from_payload(reference_id: str, payload: dict) -> str | None:
    """从 annotation payload 提取 marker 文本（与 diagnostic.py 逻辑一致）。"""
    parts = reference_id.split(".")
    if len(parts) < 2:
        return None
    unit_id = parts[0]
    role = parts[1] if len(parts) > 1 else None

    for unit in payload.get("semantic_units", []):
        if unit.get("unit_id") != unit_id:
            continue
        if role == "stem":
            return str(unit.get("question_label", ""))
        elif role == "option" and len(parts) > 2:
            option_label = parts[2]
            for opt in unit.get("options", []):
                if opt.get("label") == option_label:
                    return str(option_label)
        elif role == "answer":
            return str(unit.get("question_label", ""))
        elif role == "explanation":
            return str(unit.get("question_label", ""))
    return None


async def main():
    parser = argparse.ArgumentParser(description="Phase I-4 evidence replay")
    parser.add_argument(
        "--source-version-id",
        type=str,
        required=True,
        help="Source version UUID to replay",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path (default: stdout)",
    )
    args = parser.parse_args()

    source_version_id = uuid_mod.UUID(args.source_version_id)
    print(f"Loading data for source_version_id={source_version_id}...")

    db_lines, db_spans, db_figures, annotation = await load_data(source_version_id)

    if annotation is None:
        print("ERROR: No annotation found for this source version")
        sys.exit(1)

    print(f"  Lines: {len(db_lines)}")
    print(f"  Spans: {len(db_spans)}")
    print(f"  Figures: {len(db_figures)}")
    print(f"  Annotation: {annotation.id} (status={annotation.semantic_status})")

    lines, spans_by_line, figures = build_views(db_lines, db_spans, db_figures)

    # === Before: SourceResolver ===
    print("\n=== Before: SourceResolver ===")
    resolved_run = SourceResolver(
        source_version_id=source_version_id, lines=lines, figures=figures
    ).resolve(annotation.payload)

    total_refs = len(resolved_run.resolved_spans) + len(resolved_run.unresolved_references)
    print(f"  Resolved: {len(resolved_run.resolved_spans)}")
    print(f"  Unresolved: {len(resolved_run.unresolved_references)}")
    print(f"  Resolution rate: {len(resolved_run.resolved_spans)}/{total_refs}")

    # === Baseline diagnostic ===
    print("\n=== Baseline Diagnostic ===")
    diag_report = diagnose_unresolved(resolved_run, lines, annotation.payload)
    print(f"  Classification: {dict(diag_report.by_classification)}")
    print(f"  By role: {dict(diag_report.by_role)}")

    # === After: Evidence-aware analysis ===
    print("\n=== After: Evidence-Aware Analysis ===")
    evidence_reports = []
    unique_count = 0
    ambiguous_count = 0

    for ref in resolved_run.unresolved_references:
        marker = extract_marker_from_payload(ref.reference_id, annotation.payload)
        if not marker:
            continue

        report = analyze_evidence(
            reference_id=ref.reference_id,
            marker=marker,
            lines=lines,
            spans_by_line=spans_by_line,
        )
        evidence_reports.append(report)

        if report.unique_with_evidence:
            unique_count += 1
        else:
            ambiguous_count += 1

    print(f"  Total analyzed: {len(evidence_reports)}")
    print(f"  Unique with evidence: {unique_count}")
    print(f"  Still ambiguous: {ambiguous_count}")
    if evidence_reports:
        print(f"  Unique rate: {unique_count}/{len(evidence_reports)} = {unique_count/len(evidence_reports)*100:.1f}%")

    # === Summary ===
    print("\n=== Before/After Comparison ===")
    print(f"  Before (Resolver): {len(resolved_run.resolved_spans)} resolved / {len(resolved_run.unresolved_references)} unresolved")
    print(f"  After (Evidence):  {unique_count} unique / {ambiguous_count} ambiguous")
    print(f"  Evidence improvement: {unique_count} refs can be uniquely identified with SourceSpan evidence")

    # === Output ===
    output = {
        "source_version_id": str(source_version_id),
        "annotation_id": str(annotation.id),
        "before": {
            "resolved": len(resolved_run.resolved_spans),
            "unresolved": len(resolved_run.unresolved_references),
            "classification": dict(diag_report.by_classification),
            "by_role": dict(diag_report.by_role),
        },
        "after": {
            "total_analyzed": len(evidence_reports),
            "unique_with_evidence": unique_count,
            "still_ambiguous": ambiguous_count,
        },
        "evidence_reports": [format_evidence_report(r) for r in evidence_reports],
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\nOutput written to {args.output}")
    else:
        print("\n=== Full Report ===")
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
