/** StudentView (/admin/questions/:id/student)：学生实际视图。
 *
 * 内容只来自 GET /api/student/questions/{id}（学生 API），不读 admin 诊断接口。
 * 发布门控由服务端执行：非 official 答案/解析文本在此接口即为空——页面如实
 * 呈现「未发布」，不本地拼接答案、不绕过 withheld 状态。
 *
 * 展示规则（Owner 迭代）：
 *   1) 题干展示剥前导题号（页面题号栏已有，不重复）；
 *   2) 题干+选项一个显示框，答案+解析另一个显示框；
 *   3) 答案/解析默认折叠，点「生成答案与解析」再显示（给学生独立思考时间）。
 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getStudentQuestion } from "../api/client";
import type { StudentQuestionDetail, StudentRoleContentInfo } from "../api/types";
import { AnswerRevealBox } from "../components/AnswerRevealBox";
import { MathText } from "../components/MathText";
import { PublishBadge } from "../components/PublishBadge";
import { QuestionFetchError } from "../components/QuestionFetchError";
import { groupQuestionContents, stripStemNumber } from "../lib/questionGroups";

export function StudentViewPage() {
  const { id } = useParams<{ id: string }>();
  const [q, setQ] = useState<StudentQuestionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getStudentQuestion(id)
      .then(setQ)
      .catch((e) => setError(String(e)));
  }, [id]);

  if (error) return <QuestionFetchError error={error} />;
  if (!q) return <p className="text-sm text-ink-muted">Loading…</p>;

  const contents: StudentRoleContentInfo[] = q.instances.flatMap((i) => i.contents);
  const groups = groupQuestionContents(contents);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Link
          to={`/admin/questions/${q.id}`}
          className="text-sm text-primary hover:underline"
        >
          ← 管理端详情
        </Link>
        <h1 className="font-display text-xl font-semibold tracking-tight">
          学生实际视图 · Q{q.question_number}
        </h1>
        <PublishBadge publish={q.answer_publish} />
      </div>

      <div className="rounded-lg border border-hairline bg-sky-50 p-3 text-[12px] text-sky-900">
        本页内容全部来自学生 API <span className="font-mono">GET /api/student/questions/{q.id.slice(0, 8)}…</span>
        ；发布门控在服务端执行。内部诊断字段（candidate_text / BindingFact / publish
        seal / source_span / text_hash）不在此接口出参中。
      </div>

      {!q.student_answer_visible && (
        <div className="rounded-lg border-2 border-amber-300 bg-amber-50 p-3 text-[13px] text-amber-900">
          本题答案与解析<b>未发布</b>（真实状态：{q.answer_publish}）。
          按当前业务规则学生看不到答案文本；本页不以任何形式补全或拼接答案。
        </div>
      )}

      {/* 显示框 1：题干与选项（默认展示） */}
      <div className="rounded-lg border border-hairline bg-white p-6">
        <div className="mb-3 flex flex-wrap gap-3 text-[12px] text-ink-muted">
          <span>学科：{q.subject ?? "未设置"}</span>
          <span>年级：{q.grade ?? "未设置"}</span>
          <span>类型：{q.canonical_question_type}</span>
          <span>题号：{q.question_number_range || q.question_number}</span>
        </div>
        <div className="mb-1 text-[13px] font-semibold text-ink-muted">题干与选项</div>

        {groups.materials.length > 0 && (
          <div className="mb-4">
            <div className="mb-1 text-[12px] font-semibold text-ink-muted">材料</div>
            <div className="space-y-2 rounded border border-dashed border-hairline p-3 text-[15px] leading-relaxed">
              {groups.materials.map((m, i) => (
                <div key={m.id ?? i}>
                  <MathText duplicateTables="collapse" text={String(m.text ?? "")} />
                </div>
              ))}
            </div>
          </div>
        )}

        {groups.displayNotes.length > 0 && (
          <div className="mb-4">
            <div className="mb-1 text-[12px] font-semibold text-ink-muted">说明</div>
            <div className="space-y-1 rounded border border-dashed border-hairline p-2 text-[12px] italic leading-relaxed text-ink-muted">
              {groups.displayNotes.map((n, i) => (
                <div key={n.id ?? `dn-${i}`}>
                  <MathText duplicateTables="collapse" text={String(n.text ?? "")} />
                </div>
              ))}
            </div>
          </div>
        )}

        {groups.sharedOptions.length > 0 && (
          <div className="mb-4 space-y-1">
            {groups.sharedOptions.map((o, i) => (
              <div key={o.id ?? `shopt-${i}`} className="flex gap-2 text-[15px]">
                <span className="font-medium">{o.label}.</span>
                <MathText duplicateTables="collapse" text={String(o.text ?? "")} />
              </div>
            ))}
          </div>
        )}

        {groups.subs.map((sub) => (
          <div key={sub.key || "main"} className="mb-4">
            {groups.subs.length > 1 && (
              <div className="mb-1 text-[12px] font-semibold text-ink-muted">
                {sub.title}
              </div>
            )}
            {sub.stems.map((s, si) => (
              <div
                key={s.id ?? `stem-${si}`}
                className={
                  sub.key === "main" || groups.subs.length === 1
                    ? "mb-2 text-[17px] leading-relaxed"
                    : "mb-2 text-[16px] leading-relaxed"
                }
              >
                <MathText duplicateTables="collapse" text={stripStemNumber(String(s.text ?? ""))} />
              </div>
            ))}
            {sub.options.length > 0 && (
              <div className="space-y-1">
                {sub.options.map((o, i) => (
                  <div key={o.id ?? `opt-${sub.key}-${i}`} className="flex gap-2 text-[15px]">
                    <span className="font-medium">{o.label}.</span>
                    <MathText duplicateTables="collapse" text={String(o.text ?? "")} />
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {contents.length === 0 && <p className="text-sm text-ink-muted">无题目内容。</p>}
      </div>

      {/* 显示框 2：答案与解析（默认折叠，点按钮生成） */}
      <AnswerRevealBox
        emptyHint={
          q.student_answer_visible
            ? "先独立思考，准备好了点击右上「生成答案与解析」查看。"
            : "本题答案未发布，点击查看真实状态。"
        }
      >
        {!q.student_answer_visible ? (
          <div className="rounded bg-amber-50 px-3 py-2 text-[13px] text-amber-900">
            答案与解析未发布（{q.answer_publish}），学生不可见。页面不展示任何答案文本。
          </div>
        ) : (
          <div className="space-y-4">
            {groups.subs.map((sub) =>
              sub.answers.length > 0 ? (
                <div key={`ans-${sub.key || "main"}`}>
                  {groups.subs.length > 1 && (
                    <div className="mb-1 text-[12px] font-semibold text-ink-muted">
                      {sub.title}
                    </div>
                  )}
                  {sub.answers.map((a, i) => (
                    <div key={a.id ?? i} className="flex gap-2 text-[15px]">
                      {a.label &&
                        !String(a.text ?? "").trimStart().startsWith(a.label) && (
                          <span className="font-medium">{a.label}.</span>
                        )}
                      <MathText duplicateTables="collapse" text={String(a.text ?? "")} />
                    </div>
                  ))}
                </div>
              ) : null,
            )}
            {groups.explanations.length > 0 && (
              <div>
                <div className="mb-1 text-[12px] font-semibold text-ink-muted">解析</div>
                <div className="space-y-2 text-[15px] leading-relaxed">
                  {groups.explanations.map((e, i) => (
                    <div key={e.id ?? i}>
                      <MathText duplicateTables="collapse" text={String(e.text ?? "")} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </AnswerRevealBox>
    </div>
  );
}
