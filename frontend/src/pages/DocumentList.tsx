/** Document List (/admin/documents)：hairline 表格 + 状态筛选。 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listDocuments } from "../api/client";
import type { DocumentSummary } from "../api/types";

const FILTERS = [
  "all",
  "imported",
  "sealed",
  "annotating",
  "resolved",
  "compiled",
  "pending_review",
  "failed",
] as const;

export function DocumentList() {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    listDocuments({ status: filter === "all" ? undefined : filter, limit: 50 })
      .then((r) => {
        setDocs(r.documents);
        setTotal(r.total);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold tracking-tight">
          Documents
        </h1>
        <div className="flex items-center gap-3">
          <Link
            to="/admin/documents/upload"
            className="rounded-pill bg-primary px-4 py-1.5 text-[13px] font-medium text-white hover:bg-blue-700"
          >
            + Import
          </Link>
          <span className="text-sm text-ink-muted">{total} total</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-pill px-3 py-1 text-[13px] transition-colors ${
              filter === f
                ? "bg-primary text-white"
                : "border border-hairline bg-white text-ink hover:bg-canvas-parchment"
            }`}
          >
            {f.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-lg border border-hairline bg-canvas-parchment p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-ink-muted">Loading…</p>
      ) : docs.length === 0 ? (
        <p className="text-sm text-ink-muted">No documents found.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left text-[13px] font-semibold text-ink-muted">
              <th className="pb-2 pr-4">Filename</th>
              <th className="pb-2 pr-4">Type</th>
              <th className="pb-2 pr-4">Status</th>
              <th className="pb-2 pr-4">Candidates</th>
              <th className="pb-2 pr-4">Pending</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id} className="border-b border-hairline">
                <td className="py-2 pr-4">
                  <Link
                    to={`/admin/documents/${d.id}`}
                    className="text-primary hover:underline"
                  >
                    {d.file_name}
                  </Link>
                </td>
                <td className="py-2 pr-4">{d.file_type}</td>
                <td className="py-2 pr-4">
                  <StatusCell status={d.processing_status} />
                </td>
                <td className="py-2 pr-4">{d.candidate_count}</td>
                <td className="py-2">
                  {d.pending_count > 0 ? (
                    <span className="font-medium text-amber-600">
                      {d.pending_count}
                    </span>
                  ) : (
                    <span className="text-ink-muted">0</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function StatusCell({ status }: { status: string }) {
  const colors: Record<string, string> = {
    imported: "text-gray-500",
    sealed: "text-green-600",
    annotating: "text-blue-600",
    resolved: "text-blue-600",
    compiled: "text-blue-600",
    pending_review: "text-amber-600",
    failed: "text-red-600",
  };
  return (
    <span className={`font-medium ${colors[status] ?? "text-ink"}`}>
      {status}
    </span>
  );
}
