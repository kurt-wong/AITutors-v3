/** Feedback list (/admin/feedbacks)：可追溯待处理反馈列表（M3b）。 */

import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listFeedbacks } from "../api/client";
import type { FeedbackListResponse } from "../api/types";
import { FEEDBACK_CATEGORIES } from "../components/FeedbackForm";

const CAT_LABEL = Object.fromEntries(
  FEEDBACK_CATEGORIES.map((c) => [c.value, c.label]),
);

export function FeedbackList() {
  const [params] = useSearchParams();
  const questionId = params.get("question_id") ?? undefined;
  const [data, setData] = useState<FeedbackListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () =>
    listFeedbacks({ question_id: questionId, limit: 100 })
      .then(setData)
      .catch((e) => setError(String(e)));

  useEffect(() => {
    load();
  }, [questionId]);

  if (error) return <div className="p-4 text-sm text-red-600">{error}</div>;
  if (!data) return <p className="text-sm text-ink-muted">Loading…</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="font-display text-xl font-semibold tracking-tight">
          Feedbacks
        </h1>
        <span className="rounded-pill bg-canvas-parchment px-2 py-0.5 text-[12px] font-medium text-ink-muted">
          {data.total} 条
        </span>
        <button
          type="button"
          onClick={load}
          className="rounded border border-hairline px-2 py-0.5 text-[12px] text-primary hover:bg-canvas-parchment"
        >
          刷新
        </button>
      </div>

      {data.total === 0 ? (
        <p className="text-sm text-ink-muted">暂无反馈。可在题目详情页提交。</p>
      ) : (
        <div className="space-y-2">
          {data.feedbacks.map((f) => (
            <div
              key={f.id}
              className="rounded-lg border border-hairline bg-white p-4"
            >
              <div className="mb-1 flex flex-wrap items-center gap-2 text-[12px]">
                <span className="rounded bg-canvas-parchment px-2 py-0.5 font-medium">
                  {CAT_LABEL[f.category] ?? f.category}
                </span>
                <span
                  className={`rounded px-2 py-0.5 ${
                    f.status === "open"
                      ? "bg-amber-50 text-amber-800"
                      : "bg-canvas-parchment text-ink-muted"
                  }`}
                >
                  {f.status}
                </span>
                <Link
                  to={`/admin/questions/${f.question_id}`}
                  className="text-primary hover:underline"
                >
                  Question {f.question_id.slice(0, 8)}…
                </Link>
                <span className="text-ink-muted">
                  {f.created_at ?? ""} · {f.created_by}
                </span>
              </div>
              <div className="text-[13px] leading-relaxed">{f.description}</div>
              <div className="mt-2 text-[11px] text-ink-muted">
                instance=
                <span className="font-mono">
                  {f.instance_id?.slice(0, 8) ?? "—"}
                </span>
                {" · "}
                sv=
                <span className="font-mono">
                  {f.source_version_id?.slice(0, 8) ?? "—"}
                </span>
                {" · "}
                unit=
                <span className="font-mono">{f.producer_unit_id ?? "—"}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
