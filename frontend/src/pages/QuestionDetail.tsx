/** Question Detail (/admin/questions/:id)：真实入库题目正文/选项/答案 + LaTeX。
 *  VIS-INSPECT-V1：真实发布状态标注、复合题真实层级、HTML 残片与图片状态直查、
 *  学生实际视图入口。不美化、不掩盖既有缺陷（R2X-04 类选项残片必须可见）。
 *
 *  展示规则（Owner 迭代，与学生视图一致）：题干剥前导题号；题干+选项与
 *  答案+解析分框；答案/解析默认折叠、点「生成答案与解析」再显示。
 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getQuestion } from "../api/client";
import type {
  InstanceRoleContentInfo,
  QuestionDetail as QDetail,
} from "../api/types";
import { AnswerRevealBox } from "../components/AnswerRevealBox";
import { FeedbackForm } from "../components/FeedbackForm";
import { ImageStatusPanel } from "../components/ImageStatusPanel";
import { MathText, resolveImageSrc } from "../components/MathText";
import { PublishBadge } from "../components/PublishBadge";
import { QuestionFetchError } from "../components/QuestionFetchError";
import {
  AnswerSection,
  computeIsPendingReview,
} from "../components/AnswerSection";
import {
  extractImageRefs,
  findHtmlResidue,
  findHtmlStructures,
  groupQuestionContents,
  stripStemNumber,
} from "../lib/questionGroups";

function aggregatePublish(answers: InstanceRoleContentInfo[]): string {
  const pubs = new Set(
    answers.map(
      (a) => (a.answer_status as { publish?: string } | null)?.publish ?? "withheld_review",
    ),
  );
  if (pubs.size === 0) return "none";
  if (pubs.has("official") && pubs.size === 1) return "official";
  if (pubs.has("withheld_review") && pubs.size === 1) return "withheld_review";
  return "mixed";
}

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

  if (error) return <QuestionFetchError error={error} />;
  if (!q) return <p className="text-sm text-ink-muted">Loading…</p>;

  // 取第一个 occurrence 的 role contents（与原实现一致）
  const inst = q.instances[0];
  const contents: InstanceRoleContentInfo[] = inst ? inst.contents : [];
  const groups = groupQuestionContents(contents);
  const answers = contents.filter((c) => c.role === "answer");
  const isPendingReview = computeIsPendingReview(answers);
  const publish = aggregatePublish(answers);
  const residues = findHtmlResidue(contents);
  const structures = findHtmlStructures(contents);
  const imageRefs = extractImageRefs(contents, resolveImageSrc);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/admin/questions" className="text-sm text-primary hover:underline">
          ← Questions
        </Link>
        <h1 className="font-display text-xl font-semibold tracking-tight">
          Question {inst?.question_number || ""}
        </h1>
        <span className="rounded-pill bg-canvas-parchment px-2 py-0.5 text-[12px] font-medium text-ink-muted">
          {q.canonical_question_type}
        </span>
        <PublishBadge publish={publish} />
        {isPendingReview && (
          <span className="rounded-pill bg-amber-100 px-2 py-0.5 text-[12px] font-medium text-amber-800">
            待审核（答案未经来源核验）
          </span>
        )}
        <Link
          to={`/admin/questions/${q.id}/student`}
          className="ml-auto rounded border border-hairline bg-white px-3 py-1 text-[12px] font-medium text-primary hover:bg-canvas-parchment"
        >
          学生实际视图 →
        </Link>
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

      {/* 异常直查：HTML 残片（渲染层消隐，此处显式列出） */}
      {(residues.length > 0 || structures.length > 0) && (
        <div
          className={`rounded-lg border-2 p-3 ${
            residues.length > 0 ? "border-red-300 bg-red-50" : "border-hairline bg-canvas-parchment"
          }`}
        >
          {residues.length > 0 && (
          <>
          <div className="mb-1 text-[13px] font-semibold text-red-800">
            检出 HTML 残片（{residues.length} 处）— 默认渲染会消隐这些标签，此处显式暴露
          </div>
          <ul className="space-y-1 text-[12px] text-red-900">
            {residues.map((r, i) => (
              <li key={i} className="font-mono">
                [{r.role}]{r.label ? ` ${r.label}` : ""}:{" "}
                <span className="rounded bg-red-100 px-1">{r.raw}</span>{" "}
                <span className="text-red-700">…{r.text_excerpt}…
                </span>
              </li>
            ))}
          </ul>
          </>
          )}
          {structures.length > 0 && (
            <div className="mt-2 rounded border border-hairline bg-white/60 p-2 text-[12px] text-ink-muted">
              表格结构标签（{structures.length} 处）— 已按表格结构化渲染，不计残片
              <span className="ml-2 font-mono">
                {Object.entries(
                  structures.reduce<Record<string, number>>((acc, s) => {
                    acc[s.tag] = (acc[s.tag] ?? 0) + 1;
                    return acc;
                  }, {}),
                )
                  .map(([tag, n]) => `${tag}×${n}`)
                  .join(" · ")}
              </span>
            </div>
          )}
        </div>
      )}

      {/* 显示框 1：题干与选项（默认展示；复合题保留真实层级） */}
      <div className="rounded-lg border border-hairline bg-white p-6">
        <div className="mb-1 text-[13px] font-semibold text-ink-muted">题干与选项</div>

        {groups.materials.length > 0 && (
          <div className="mb-4">
            <div className="mb-1 text-[12px] font-semibold text-ink-muted">共享材料</div>
            <div className="space-y-2 rounded border border-dashed border-hairline p-3 text-[15px] leading-relaxed">
              {groups.materials.map((m, i) => (
                <div key={m.id ?? i}>
                  <MathText duplicateTables="annotate" text={String(m.text ?? "")} />
                  {showRaw && (
                    <pre className="mt-2 whitespace-pre-wrap rounded bg-canvas-parchment p-2 text-[12px] text-ink-muted">
                      {m.text}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {groups.sharedOptions.length > 0 && (
          <div className="mb-4">
            <div className="mb-1 text-[12px] font-semibold text-ink-muted">共享选项</div>
            <div className="space-y-1">
              {groups.sharedOptions.map((o) => (
                <div key={o.id} className="flex gap-2 text-[15px]">
                  <span className="font-medium">{o.label}.</span>
                  <MathText duplicateTables="annotate" text={String(o.text ?? "")} />
                </div>
              ))}
            </div>
          </div>
        )}

        {groups.subs.map((sub) => (
          <div
            key={sub.key || "main"}
            className={`mb-4 ${sub.key === "_orphan" ? "rounded border-2 border-amber-300 p-3" : ""}`}
          >
            {groups.subs.length > 1 && (
              <div className="mb-1 text-[12px] font-semibold text-ink-muted">
                {sub.title}
              </div>
            )}
            {sub.stems.map((s, si) => (
              <div key={s.id ?? `stem-${si}`} className="mb-2 text-[17px] leading-relaxed">
                <MathText duplicateTables="annotate" text={stripStemNumber(String(s.text ?? ""))} />
                {showRaw && (
                  <pre className="mt-2 whitespace-pre-wrap rounded bg-canvas-parchment p-2 text-[12px] text-ink-muted">
                    {s.text}
                  </pre>
                )}
              </div>
            ))}
            {sub.options.length > 0 && (
              <div className="space-y-1">
                {sub.options.map((o) => (
                  <div key={o.id} className="flex gap-2 text-[15px]">
                    <span className="font-medium">{o.label}.</span>
                    <MathText duplicateTables="annotate" text={String(o.text ?? "")} />
                    {showRaw && (
                      <span className="ml-2 font-mono text-[11px] text-ink-muted">
                        {o.text}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {contents.length === 0 && <p className="text-sm text-ink-muted">无 role contents。</p>}
      </div>

      {/* 显示框 2：答案与解析（默认折叠，点按钮生成） */}
      <AnswerRevealBox>
        <div className="space-y-4">
          {groups.subs.map((sub) =>
            sub.answers.length > 0 ? (
              <div key={`ans-${sub.key || "main"}`}>
                {groups.subs.length > 1 && (
                  <div className="mb-1 text-[12px] font-semibold text-ink-muted">
                    {sub.title}
                  </div>
                )}
                <AnswerSection answers={sub.answers} showRaw={showRaw} />
              </div>
            ) : null,
          )}
          {groups.explanations.length > 0 && (
            <div>
              <div className="mb-1 text-[12px] font-semibold text-ink-muted">解析</div>
              <div className="space-y-2 text-[15px] leading-relaxed">
                {groups.explanations.map((e, i) => (
                  <div key={e.id ?? i}>
                    <MathText duplicateTables="annotate" text={String(e.text ?? "")} />
                    {showRaw && (
                      <pre className="mt-2 whitespace-pre-wrap rounded bg-canvas-parchment p-2 text-[12px] text-ink-muted">
                        {e.text}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </AnswerRevealBox>

      <ImageStatusPanel refs={imageRefs} />

      {inst && (
        <div className="text-[12px] text-ink-muted">
          instance_order={inst.instance_order} · occurrence_key=
          <span className="font-mono">{inst.occurrence_key.slice(0, 32)}…</span>
        </div>
      )}

      <FeedbackForm
        questionId={q.id}
        instanceId={inst?.id}
        questionLabel={`Question ${inst?.question_number || q.id.slice(0, 8)}`}
      />
    </div>
  );
}
