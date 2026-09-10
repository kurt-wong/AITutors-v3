/** Document Review (/admin/documents/:id)：Review Console — Quality + Source Lines + Pipeline. */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getDocument, getSourceLines, getSourceQuality } from "../api/client";
import type {
  CandidateSummary,
  DocumentDetail,
  SourceLineInfo,
  SourceLinesResponse,
  SourceQualityReport,
} from "../api/types";
import { ResultToolbar } from "../components/ResultToolbar";

export function DocumentReview() {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [quality, setQuality] = useState<SourceQualityReport | null>(null);
  const [sourceLines, setSourceLines] = useState<SourceLinesResponse | null>(null);
  const [pageFilter, setPageFilter] = useState<number | undefined>(undefined);
  const [mode, setMode] = useState<"display" | "review">("display");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getDocument(id)
      .then(setDetail)
      .catch((e) => setError(String(e)));
    getSourceQuality(id)
      .then(setQuality)
      .catch(() => setQuality(null)); // quality 可能不存在
  }, [id]);

  useEffect(() => {
    if (!id) return;
    getSourceLines(id, { page_no: pageFilter })
      .then(setSourceLines)
      .catch(() => setSourceLines(null));
  }, [id, pageFilter]);

  if (error) return <div className="p-4 text-sm text-red-600">{error}</div>;
  if (!detail) return <p className="text-sm text-ink-muted">Loading…</p>;

  const { document: doc, source_versions, figures, candidates } = detail;
  const activeSource =
    source_versions.find((sv) => sv.status === "sealed") ?? source_versions[0];

  // 从 source lines 提取可用页码
  const availablePages = sourceLines
    ? [...new Set(sourceLines.lines.map((l) => l.page_no))].sort((a, b) => a - b)
    : [];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link
          to="/admin/documents"
          className="text-sm text-primary hover:underline"
        >
          ← Documents
        </Link>
        <h1 className="font-display text-xl font-semibold tracking-tight">
          {doc.file_name}
        </h1>
        <span className="rounded-pill bg-canvas-parchment px-2 py-0.5 text-[12px] font-medium text-ink-muted">
          {doc.processing_status}
        </span>
      </div>

      <ResultToolbar mode={mode} onModeChange={setMode} />

      {/* Source Quality Banner */}
      {quality && <QualityBanner quality={quality} />}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: Source Viewer */}
        <section className="space-y-4">
          <h2 className="font-display text-base font-semibold tracking-tight">
            Source
          </h2>
          {activeSource ? (
            <div className="rounded-lg border border-hairline bg-white p-4">
              <div className="mb-2 flex gap-4 text-[13px] text-ink-muted">
                <span>Role: {activeSource.role}</span>
                <span>Provider: {activeSource.provider}</span>
                <span>
                  {activeSource.page_count} pages / {activeSource.line_count}{" "}
                  lines
                </span>
              </div>
              {activeSource.body_text && (
                <pre className="max-h-[300px] overflow-auto rounded-sm bg-canvas-parchment p-3 text-[13px] leading-relaxed whitespace-pre-wrap">
                  {activeSource.body_text}
                </pre>
              )}
              {mode === "review" && (
                <div className="mt-2 space-y-1 text-[12px] text-ink-muted">
                  <div>body_hash: {activeSource.body_hash}</div>
                  <div>integrity_hash: {activeSource.integrity_hash}</div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-ink-muted">No source version.</p>
          )}

          {/* Page Source Viewer */}
          {sourceLines && sourceLines.lines.length > 0 && (
            <div className="rounded-lg border border-hairline bg-white p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-[13px] font-semibold text-ink-muted">
                  Source Lines ({sourceLines.total_lines})
                </h3>
                <div className="flex gap-1">
                  <button
                    onClick={() => setPageFilter(undefined)}
                    className={`rounded px-2 py-0.5 text-[12px] ${
                      pageFilter === undefined
                        ? "bg-primary text-white"
                        : "bg-canvas-parchment text-ink-muted hover:bg-hairline"
                    }`}
                  >
                    All
                  </button>
                  {availablePages.map((p) => (
                    <button
                      key={p}
                      onClick={() => setPageFilter(p)}
                      className={`rounded px-2 py-0.5 text-[12px] ${
                        pageFilter === p
                          ? "bg-primary text-white"
                          : "bg-canvas-parchment text-ink-muted hover:bg-hairline"
                      }`}
                    >
                      p{p}
                    </button>
                  ))}
                </div>
              </div>
              <div className="max-h-[400px] space-y-1 overflow-auto">
                {sourceLines.lines.map((line) => (
                  <SourceLineRow key={line.line_ref} line={line} mode={mode} />
                ))}
              </div>
            </div>
          )}

          {figures.length > 0 && (
            <div>
              <h3 className="mb-2 text-[13px] font-semibold text-ink-muted">
                Figures ({figures.length})
              </h3>
              <div className="space-y-1">
                {figures.map((f) => (
                  <div
                    key={f.id}
                    className="rounded-sm border border-hairline px-3 py-1.5 text-[13px]"
                  >
                    <span className="font-medium">{f.figure_id}</span>
                    <span className="ml-2 text-ink-muted">p.{f.page_no}</span>
                    {mode === "review" && (
                      <span className="ml-2 text-[12px] text-ink-muted">
                        {f.figure_hash.slice(0, 12)}…
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Right: Pipeline Result */}
        <section className="space-y-4">
          <h2 className="font-display text-base font-semibold tracking-tight">
            Pipeline Candidates ({candidates.length})
          </h2>
          {candidates.length === 0 ? (
            <p className="text-sm text-ink-muted">No candidates yet.</p>
          ) : (
            <div className="space-y-3">
              {candidates.map((c) => (
                <CandidateCard key={c.id} candidate={c} mode={mode} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function QualityBanner({ quality }: { quality: SourceQualityReport }) {
  const colors: Record<string, string> = {
    valid: "bg-green-50 text-green-700 border-green-200",
    degraded: "bg-amber-50 text-amber-700 border-amber-200",
    invalid: "bg-red-50 text-red-700 border-red-200",
    ocr_required: "bg-purple-50 text-purple-700 border-purple-200",
  };
  const labels: Record<string, string> = {
    valid: "✓ Source Quality: Valid",
    degraded: "⚠ Source Quality: Degraded",
    invalid: "✗ Source Quality: Invalid",
    ocr_required: "📷 OCR Required",
  };

  return (
    <div className={`rounded-lg border p-3 ${colors[quality.status] ?? "bg-canvas-parchment"}`}>
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-semibold">
          {labels[quality.status] ?? quality.status}
        </span>
        <div className="flex gap-3 text-[12px]">
          <span>chars: {quality.total_chars}</span>
          <span>CJK: {(quality.cjk_ratio * 100).toFixed(1)}%</span>
          <span>replacement: {(quality.replacement_char_ratio * 100).toFixed(1)}%</span>
        </div>
      </div>
      {quality.issues.length > 0 && (
        <ul className="mt-1 space-y-0.5 text-[12px]">
          {quality.issues.map((issue, i) => (
            <li key={i}>• {issue}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SourceLineRow({
  line,
  mode,
}: {
  line: SourceLineInfo;
  mode: "display" | "review";
}) {
  return (
    <div className="flex items-start gap-2 rounded-sm px-2 py-1 text-[13px] hover:bg-canvas-parchment">
      <span className="w-16 shrink-0 text-[11px] text-ink-muted">
        {line.line_ref}
      </span>
      <span className="flex-1 whitespace-pre-wrap">{line.text}</span>
      {mode === "review" && (
        <span className="shrink-0 text-[11px] text-ink-muted">
          {line.line_hash.slice(0, 8)}…
        </span>
      )}
    </div>
  );
}

function CandidateCard({
  candidate,
  mode,
}: {
  candidate: CandidateSummary;
  mode: "display" | "review";
}) {
  const gd = candidate.gate_decision as Record<string, unknown> | null;
  return (
    <div className="rounded-lg border border-hairline bg-white p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[13px] font-semibold">
            {candidate.unit_type}
          </span>
          <DecisionBadge status={candidate.decision_status} />
        </div>
        <Link
          to={`/admin/candidates/${candidate.id}`}
          className="text-[13px] text-primary hover:underline"
        >
          Review →
        </Link>
      </div>
      {gd && (
        <div className="mt-2 text-[13px] text-ink-muted">
          Gate:{" "}
          <span className="font-medium text-ink">
            {String(gd.decision ?? "—")}
          </span>
          {gd.reason != null && <span className="ml-2">{String(gd.reason)}</span>}
        </div>
      )}
      {mode === "review" && (
        <div className="mt-2 text-[12px] text-ink-muted">
          <div>ID: {candidate.id}</div>
          <div>Created: {candidate.created_at ?? "—"}</div>
        </div>
      )}
    </div>
  );
}

function DecisionBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending_review: "bg-amber-50 text-amber-700",
    approved: "bg-green-50 text-green-700",
    rejected: "bg-red-50 text-red-700",
  };
  return (
    <span
      className={`rounded-pill px-2 py-0.5 text-[12px] font-medium ${
        colors[status] ?? "bg-canvas-parchment text-ink"
      }`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
