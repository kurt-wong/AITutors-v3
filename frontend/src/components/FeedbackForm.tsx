/** Feedback form for a real Question (M3b). Observational only — never mutates question. */

import { useState } from "react";
import { createFeedback } from "../api/client";
import type { FeedbackOut } from "../api/types";

export const FEEDBACK_CATEGORIES: { value: string; label: string }[] = [
  { value: "stem_missing_or_incomplete", label: "题干缺失或不完整" },
  { value: "option_missing_or_incomplete", label: "选项缺失或不完整" },
  { value: "answer_missing_or_wrong", label: "答案缺失或错误" },
  { value: "explanation_missing_or_wrong", label: "解析缺失或错误" },
  { value: "material_missing_or_bad_ref", label: "材料缺失或引用错误" },
  { value: "latex_render_error", label: "LaTeX/公式渲染异常" },
  { value: "identity_or_number_mismatch", label: "题目身份或题号绑定错误" },
  { value: "subject_grade_wrong_or_unset", label: "学科/年级不正确或未设置" },
  { value: "other", label: "其他问题" },
];

export function FeedbackForm({
  questionId,
  instanceId,
  questionLabel,
  onCreated,
}: {
  questionId: string;
  instanceId?: string;
  questionLabel: string;
  onCreated?: (f: FeedbackOut) => void;
}) {
  const [category, setCategory] = useState("latex_render_error");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<FeedbackOut | null>(null);

  const submit = async () => {
    if (!description.trim()) {
      setError("请填写问题说明");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const f = await createFeedback({
        question_id: questionId,
        instance_id: instanceId,
        category,
        description: description.trim(),
        created_by: "console-user",
      });
      setSaved(f);
      setDescription("");
      onCreated?.(f);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-lg border border-hairline bg-white p-4">
      <h3 className="mb-2 text-[13px] font-semibold text-ink-muted">
        提交反馈（不会自动修改题目）
      </h3>
      <p className="mb-2 text-[12px] text-ink-muted">
        将关联：{questionLabel}
        {instanceId ? ` · instance ${instanceId.slice(0, 8)}…` : ""}
      </p>
      <div className="space-y-2">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full rounded border border-hairline px-2 py-1.5 text-[13px]"
        >
          {FEEDBACK_CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="请描述问题与可核对的证据（如选项公式未渲染）…"
          rows={3}
          className="w-full rounded border border-hairline px-2 py-1.5 text-[13px]"
        />
        {error && <div className="text-[12px] text-red-600">{error}</div>}
        {saved && (
          <div className="rounded bg-green-50 px-2 py-1.5 text-[12px] text-green-800">
            已保存反馈 <span className="font-mono">{saved.id.slice(0, 8)}…</span>
            （status={saved.status}，category={saved.category}）— 不修改题目数据
          </div>
        )}
        <button
          type="button"
          disabled={busy}
          onClick={submit}
          className="rounded bg-primary px-3 py-1.5 text-[13px] text-white disabled:opacity-50"
        >
          {busy ? "提交中…" : "提交反馈"}
        </button>
      </div>
    </div>
  );
}
