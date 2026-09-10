/** Candidate Review (/admin/candidates/:id)：题目终审 + Approve/Reject。 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveCandidate,
  getCandidate,
  rejectCandidate,
} from "../api/client";
import type { CandidateDetail } from "../api/types";
import { ResultToolbar } from "../components/ResultToolbar";

export function CandidateReview() {
  const { id } = useParams<{ id: string }>();
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [mode, setMode] = useState<"display" | "review">("display");
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  useEffect(() => {
    if (!id) return;
    getCandidate(id)
      .then(setCandidate)
      .catch((e) => setError(String(e)));
  }, [id]);

  if (error) return <div className="p-4 text-sm text-red-600">{error}</div>;
  if (!candidate) return <p className="text-sm text-ink-muted">Loading…</p>;

  const payload = candidate.payload as Record<string, unknown>;
  const irSnapshot = payload.ir_snapshot as
    | { units?: Record<string, unknown>[] }
    | undefined;
  const compiledRoles = (payload.compiled_roles ?? []) as Record<
    string,
    unknown
  >[];
  const answers = (payload.answer ?? []) as Record<string, unknown>[];
  const resolvedSpans = (payload.resolved_spans ?? []) as Record<
    string,
    unknown
  >[];

  const stem = compiledRoles.find((r) => r.role === "stem");
  const options = compiledRoles.filter((r) => r.role === "option");

  const handleApprove = async () => {
    if (!id) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await approveCandidate(id, {
        reviewer_id: "admin",
        confirmed_fields: ["stem", "answer"],
      });
      setCandidate(updated);
    } catch (e) {
      setActionError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleReject = async () => {
    if (!id || !rejectReason.trim()) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await rejectCandidate(id, {
        reviewer_id: "admin",
        reasons: [rejectReason.trim()],
      });
      setCandidate(updated);
    } catch (e) {
      setActionError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const canAct = candidate.decision_status === "pending_review";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link to="/admin/documents" className="text-sm text-primary hover:underline">
          ← Back
        </Link>
        <h1 className="font-display text-xl font-semibold tracking-tight">
          Candidate Review
        </h1>
        <span className="rounded-pill bg-canvas-parchment px-2 py-0.5 text-[12px] font-medium text-ink-muted">
          {candidate.decision_status.replace(/_/g, " ")}
        </span>
      </div>

      <ResultToolbar mode={mode} onModeChange={setMode} />

      {actionError && (
        <div className="rounded-lg border border-hairline bg-red-50 p-3 text-sm text-red-600">
          {actionError}
        </div>
      )}

      {/* 题目卡片：白色 18px radius 24px padding */}
      <div className="rounded-lg border border-hairline bg-white p-6">
        {stem && (
          <div className="mb-4">
            <div className="mb-1 text-[13px] font-semibold text-ink-muted">
              Question
            </div>
            <div className="text-[17px] leading-relaxed">
              {String(stem.text ?? "")}
            </div>
          </div>
        )}

        {options.length > 0 && (
          <div className="mb-4">
            <div className="mb-1 text-[13px] font-semibold text-ink-muted">
              Options
            </div>
            <div className="space-y-1">
              {options.map((o, i) => (
                <div key={i} className="flex gap-2 text-[15px]">
                  <span className="font-medium">{String(o.label ?? "")}.</span>
                  <span>{String(o.text ?? "")}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {answers.length > 0 && (
          <div className="mb-4">
            <div className="mb-1 text-[13px] font-semibold text-ink-muted">
              Answer
            </div>
            {answers.map((a, i) => (
              <div key={i} className="text-[15px]">
                {String(a.text ?? "")}
                {mode === "review" && (
                  <span className="ml-2 text-[12px] text-ink-muted">
                    (located: {String(a.source_located ?? "?")}, complete:{" "}
                    {String(a.complete ?? "?")})
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {mode === "review" && (
          <div className="space-y-3 border-t border-hairline pt-4 text-[12px] text-ink-muted">
            <div>
              <span className="font-semibold">identity_hash:</span>{" "}
              {candidate.logical_execution_hash}
            </div>
            <div>
              <span className="font-semibold">stage:</span>{" "}
              {candidate.logical_execution_stage}
            </div>
            <div>
              <span className="font-semibold">unit_type:</span>{" "}
              {candidate.unit_type}
            </div>
            {irSnapshot?.units?.[0] && (
              <div>
                <span className="font-semibold">question_type:</span>{" "}
                {String(
                  (irSnapshot.units[0] as Record<string, unknown>)
                    .original_question_type ?? "—",
                )}
              </div>
            )}
            {resolvedSpans.length > 0 && (
              <div>
                <span className="font-semibold">resolved_spans:</span>{" "}
                {resolvedSpans.length} spans
              </div>
            )}
            {candidate.gate_decision && (
              <div>
                <span className="font-semibold">gate:</span>{" "}
                {JSON.stringify(candidate.gate_decision)}
              </div>
            )}
            {stem && (
              <div>
                <span className="font-semibold">text_hash:</span>{" "}
                {String(stem.text_hash ?? "—")}
              </div>
            )}
          </div>
        )}
      </div>

      {canAct && (
        <div className="flex items-center gap-3">
          <button
            onClick={handleApprove}
            disabled={busy}
            className="rounded-pill bg-primary px-6 py-2 text-sm font-semibold text-white transition-transform active:scale-95 disabled:opacity-50"
          >
            Approve
          </button>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Reject reason…"
              className="rounded-sm border border-hairline px-3 py-2 text-sm focus:border-primary focus:outline-none"
            />
            <button
              onClick={handleReject}
              disabled={busy || !rejectReason.trim()}
              className="rounded-pill border border-red-300 px-4 py-2 text-sm font-semibold text-red-600 transition-transform active:scale-95 disabled:opacity-50"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {candidate.review_trail && candidate.review_trail.length > 0 && (
        <div>
          <h3 className="mb-2 text-[13px] font-semibold text-ink-muted">
            Review Trail
          </h3>
          <div className="space-y-1">
            {candidate.review_trail.map((entry, i) => (
              <div
                key={i}
                className="rounded-sm border border-hairline px-3 py-1.5 text-[13px]"
              >
                <span className="font-medium">
                  {String(entry.decision ?? "?")}
                </span>
                <span className="ml-2 text-ink-muted">
                  by {String(entry.reviewer_id ?? entry.verified_by ?? "?")}
                </span>
                {entry.time != null && (
                  <span className="ml-2 text-ink-muted">
                    {String(entry.time)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
