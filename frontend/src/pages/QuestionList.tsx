/** Question List (/admin/questions)：已物化真实 Question 列表（M3a + VIS-INSPECT-V1）。
 *  真实数据来自 /api/questions；筛选（学科/发布状态/试卷）走真实 API 参数。
 *  withheld / pending_review 等非学生可见状态按真实 answer_status.publish 明确标注。 */

import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listQuestions } from "../api/client";
import type { QuestionListResponse } from "../api/types";
import { PublishBadge } from "../components/PublishBadge";
import { stripStemNumber } from "../lib/questionGroups";

const SUBJECT_OPTIONS = ["数学", "语文", "英语", "物理", "化学", "生物"];
const PUBLISH_OPTIONS = [
  { value: "", label: "全部发布状态" },
  { value: "official", label: "official 已发布" },
  { value: "withheld_review", label: "withheld_review 未发布" },
  { value: "mixed", label: "mixed 部分发布" },
  { value: "none", label: "none 无答案行" },
];

export function QuestionList() {
  const [params, setParams] = useSearchParams();
  const documentId = params.get("document_id") ?? undefined;
  const subject = params.get("subject") ?? "";
  const publish = params.get("publish") ?? "";
  const [data, setData] = useState<QuestionListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    listQuestions({
      document_id: documentId,
      subject: subject || undefined,
      publish: publish || undefined,
      limit: 200,
    })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, [documentId, subject, publish]);

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next);
  }

  if (error) return <div className="p-4 text-sm text-red-600">{error}</div>;
  if (!data) return <p className="text-sm text-ink-muted">Loading…</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
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

      {/* 真实筛选：学科 / 发布状态（API 参数，非前端假过滤） */}
      <div className="flex flex-wrap items-center gap-3 text-[12px]">
        <label className="flex items-center gap-1 text-ink-muted">
          学科
          <select
            className="h-7 rounded border border-hairline bg-white px-2 text-[12px]"
            value={subject}
            onChange={(e) => updateParam("subject", e.target.value)}
          >
            <option value="">全部学科</option>
            {SUBJECT_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1 text-ink-muted">
          发布状态
          <select
            className="h-7 rounded border border-hairline bg-white px-2 text-[12px]"
            value={publish}
            onChange={(e) => updateParam("publish", e.target.value)}
          >
            {PUBLISH_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {data.total === 0 ? (
        <p className="text-sm text-ink-muted">
          当前筛选条件下暂无已 Admission 物化的 Question。
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-hairline bg-white">
          <table className="w-full text-[13px]">
            <thead className="bg-canvas-parchment text-left text-ink-muted">
              <tr>
                <th className="px-3 py-2 font-medium">题号</th>
                <th className="px-3 py-2 font-medium">类型</th>
                <th className="px-3 py-2 font-medium">学科</th>
                <th className="px-3 py-2 font-medium">发布状态</th>
                <th className="px-3 py-2 font-medium">题干摘要</th>
                <th className="px-3 py-2 font-medium">选项/答案</th>
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
                      className="font-mono text-[12px] text-primary hover:underline"
                      title={q.id}
                    >
                      {q.question_number || q.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td className="px-3 py-2">{q.canonical_question_type}</td>
                  <td className="px-3 py-2">
                    {q.subject ?? (
                      <span className="text-ink-muted">未设置</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <PublishBadge publish={q.answer_publish} />
                  </td>
                  <td className="max-w-[320px] truncate px-3 py-2" title={stripStemNumber(q.stem_excerpt)}>
                    {stripStemNumber(q.stem_excerpt) || <span className="text-ink-muted">—</span>}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-ink-muted">
                    {q.option_count} 选项 / {q.answer_count} 答案
                  </td>
                  <td className="px-3 py-2 text-ink-muted">
                    {q.document_file_name ?? "—"} · p{q.page_no}
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
