/** Question Detail (/admin/questions/:id)：真实入库题目正文/选项/答案 + LaTeX。 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getQuestion } from "../api/client";
import type { QuestionDetail as QDetail } from "../api/types";
import { FeedbackForm } from "../components/FeedbackForm";
import { MathText } from "../components/MathText";

const ROLE_ORDER: Record<string, number> = {
  stem: 0,
  option: 1,
  answer: 2,
  explanation: 3,
};

export function QuestionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [q, setQ] = useState<QDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  useEffect(() => {
    if (!id) return;
    getQuestion(id)
      .then(setQ)
      .catch((e) => setError(String(e)));
  }, [id]);

  if (error) return <div className="p-4 text-sm text-red-600">{error}</div>;
  if (!q) return <p className="text-sm text-ink-muted">Loading…</p>;

  const inst = q.instances[0];
  const contents = inst
    ? [...inst.contents].sort(
        (a, b) =>
          (ROLE_ORDER[a.role] ?? 9) - (ROLE_ORDER[b.role] ?? 9) ||
          a.role_index - b.role_index ||
          (a.label ?? "").localeCompare(b.label ?? ""),
      )
    : [];
  const stem = contents.find((c) => c.role === "stem");
  const options = contents.filter((c) => c.role === "option");
  const answers = contents.filter((c) => c.role === "answer");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link to="/admin/questions" className="text-sm text-primary hover:underline">
          ← Questions
        </Link>
        <h1 className="font-display text-xl font-semibold tracking-tight">
          Question {inst?.question_number ?? q.id.slice(0, 8)}
        </h1>
        <span className="rounded-pill bg-canvas-parchment px-2 py-0.5 text-[12px] font-medium text-ink-muted">
          {q.canonical_question_type}
        </span>
      </div>

      {/* identity + metadata */}
      <div className="flex flex-wrap gap-3 text-[12px] text-ink-muted">
        <span>
          学科：
          {q.subject ?? (
            <span className="rounded bg-amber-50 px-1 text-amber-800">未设置</span>
          )}
        </span>
        <span>
          年级：
          {q.grade ?? (
            <span className="rounded bg-amber-50 px-1 text-amber-800">未设置</span>
          )}
        </span>
        {inst && (
          <>
            <span>来源文档：{inst.document_file_name ?? inst.document_id.slice(0, 8)}</span>
            <span>
              Source：{inst.source_role}/{inst.source_artifact_kind}
            </span>
            <span>p{inst.page_no}</span>
            <span>
              identity：<span className="font-mono">{q.id.slice(0, 8)}…</span>
            </span>
            <span>
              dedup：<span className="font-mono">{q.dedup_key.slice(0, 12)}…</span>
            </span>
          </>
        )}
        <button
          type="button"
          onClick={() => setShowRaw((v) => !v)}
          className="rounded border border-hairline px-2 py-0.5 text-primary hover:bg-canvas-parchment"
        >
          {showRaw ? "隐藏原始文本" : "显示原始文本"}
        </button>
      </div>

      <div className="rounded-lg border border-hairline bg-white p-6">
        {stem && (
          <div className="mb-4">
            <div className="mb-1 text-[13px] font-semibold text-ink-muted">题干</div>
            <div className="text-[17px] leading-relaxed">
              <MathText text={stem.text} />
            </div>
            {showRaw && (
              <pre className="mt-2 whitespace-pre-wrap rounded bg-canvas-parchment p-2 text-[12px] text-ink-muted">
                {stem.text}
              </pre>
            )}
          </div>
        )}

        {options.length > 0 && (
          <div className="mb-4">
            <div className="mb-1 text-[13px] font-semibold text-ink-muted">选项</div>
            <div className="space-y-1">
              {options.map((o) => (
                <div key={o.id} className="flex gap-2 text-[15px]">
                  <span className="font-medium">{o.label}.</span>
                  <MathText text={o.text} />
                  {showRaw && (
                    <span className="ml-2 font-mono text-[11px] text-ink-muted">
                      {o.text}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {answers.length > 0 && (
          <div className="mb-2">
            <div className="mb-1 text-[13px] font-semibold text-ink-muted">答案</div>
            {answers.map((a) => (
              <div key={a.id} className="text-[15px]">
                <MathText text={a.text} />
                {showRaw && (
                  <pre className="mt-1 whitespace-pre-wrap rounded bg-canvas-parchment p-2 text-[12px] text-ink-muted">
                    {a.text}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}

        {!stem && !options.length && !answers.length && (
          <p className="text-sm text-ink-muted">无 role contents。</p>
        )}
      </div>

      {inst && (
        <div className="text-[12px] text-ink-muted">
          instance_order={inst.instance_order} · occurrence_key=
          <span className="font-mono">{inst.occurrence_key.slice(0, 32)}…</span>
        </div>
      )}

      <FeedbackForm
        questionId={q.id}
        instanceId={inst?.id}
        questionLabel={`Question ${inst?.question_number ?? q.id.slice(0, 8)}（${q.id.slice(0, 8)}…）`}
      />
    </div>
  );
}
