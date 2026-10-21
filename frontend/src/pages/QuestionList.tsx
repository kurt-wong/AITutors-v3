/** Question List (/admin/questions)：已物化真实 Question 列表（M3a）。 */

import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listQuestions } from "../api/client";
import type { QuestionListResponse } from "../api/types";

export function QuestionList() {
  const [params] = useSearchParams();
  const documentId = params.get("document_id") ?? undefined;
  const [data, setData] = useState<QuestionListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listQuestions({ document_id: documentId, limit: 100 })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, [documentId]);

  if (error) return <div className="p-4 text-sm text-red-600">{error}</div>;
  if (!data) return <p className="text-sm text-ink-muted">Loading…</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="font-display text-xl font-semibold tracking-tight">
          Questions
        </h1>
        <span className="rounded-pill bg-canvas-parchment px-2 py-0.5 text-[12px] font-medium text-ink-muted">
          {data.total} in DB
        </span>
        {documentId && (
          <span className="text-[12px] text-ink-muted">
            filtered by document {documentId.slice(0, 8)}…
          </span>
        )}
      </div>

      {data.total === 0 ? (
        <p className="text-sm text-ink-muted">
          暂无已 Admission 物化的 Question。
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-hairline bg-white">
          <table className="w-full text-[13px]">
            <thead className="bg-canvas-parchment text-left text-ink-muted">
              <tr>
                <th className="px-3 py-2 font-medium">ID</th>
                <th className="px-3 py-2 font-medium">类型</th>
                <th className="px-3 py-2 font-medium">学科</th>
                <th className="px-3 py-2 font-medium">年级</th>
                <th className="px-3 py-2 font-medium">来源</th>
              </tr>
            </thead>
            <tbody>
              {data.questions.map((q) => (
                <tr
                  key={q.instance_id}
                  className="border-t border-hairline hover:bg-canvas-parchment/50"
                >
                  <td className="px-3 py-2">
                    <Link
                      to={`/admin/questions/${q.id}`}
                      className="text-primary hover:underline font-mono text-[11px]"
                    >
                      {q.id.slice(0, 8)}…
                    </Link>
                  </td>
                  <td className="px-3 py-2">{q.canonical_question_type}</td>
                  <td className="px-3 py-2">
                    {q.subject ?? (
                      <span className="text-ink-muted">未设置</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {q.grade ?? <span className="text-ink-muted">未设置</span>}
                  </td>
                  <td className="px-3 py-2 text-ink-muted">
                    p{q.page_no} · {q.document_id.slice(0, 8)}…
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
