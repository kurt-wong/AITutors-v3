/** StudentQuestionList (/admin/questions-student)：学生视角题单（真实学生 API）。
 *  数据来自 GET /api/student/questions；按真实发布状态标注学生可见性。 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listStudentQuestions } from "../api/client";
import type { StudentQuestionListResponse } from "../api/types";
import { PublishBadge } from "../components/PublishBadge";
import { stripStemNumber } from "../lib/questionGroups";

export function StudentQuestionList() {
  const [data, setData] = useState<StudentQuestionListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listStudentQuestions({ limit: 200 })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="p-4 text-sm text-red-600">{error}</div>;
  if (!data) return <p className="text-sm text-ink-muted">Loading…</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="font-display text-xl font-semibold tracking-tight">
          Student View 题单
        </h1>
        <span className="rounded-pill bg-canvas-parchment px-2 py-0.5 text-[12px] font-medium text-ink-muted">
          {data.total} 题（真实 /api/student/questions）
        </span>
      </div>

      <div className="overflow-hidden rounded-lg border border-hairline bg-white">
        <table className="w-full text-[13px]">
          <thead className="bg-canvas-parchment text-left text-ink-muted">
            <tr>
              <th className="px-3 py-2 font-medium">题号</th>
              <th className="px-3 py-2 font-medium">学科</th>
              <th className="px-3 py-2 font-medium">发布状态</th>
              <th className="px-3 py-2 font-medium">学生答案可见</th>
              <th className="px-3 py-2 font-medium">题干摘要</th>
            </tr>
          </thead>
          <tbody>
            {data.questions.map((q) => (
              <tr
                key={q.id}
                className="border-t border-hairline hover:bg-canvas-parchment/50"
              >
                <td className="px-3 py-2">
                  <Link
                    to={`/admin/questions/${q.id}/student`}
                    className="font-mono text-[12px] text-primary hover:underline"
                    title={q.id}
                  >
                    {q.question_number || q.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-3 py-2">{q.subject ?? "未设置"}</td>
                <td className="px-3 py-2">
                  <PublishBadge publish={q.answer_publish} />
                </td>
                <td className="px-3 py-2">
                  {q.student_answer_visible ? (
                    <span className="text-emerald-700">是</span>
                  ) : (
                    <span className="text-red-700">否</span>
                  )}
                </td>
                <td className="max-w-[360px] truncate px-3 py-2" title={stripStemNumber(q.stem_excerpt)}>
                  {stripStemNumber(q.stem_excerpt) || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
