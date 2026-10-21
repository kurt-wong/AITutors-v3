/**
 * AnswerSection — answer display with trust signaling.
 *
 * P0-R4: when answers are not verified_correct, the UI MUST NOT present them
 * as the standard answer. Rendered output is covered by
 * `AnswerSection.test.tsx` via react-dom/server (no jsdom required).
 */
import { MathText } from "./MathText";

export type AnswerLike = {
  id?: string;
  label?: string | null;
  text: string | null | undefined;
  answer_status?: { verified_correct?: boolean | null } | null;
};

export function computeIsPendingReview(answers: AnswerLike[]): boolean {
  if (answers.length === 0) return false;
  // P0-R4: if ANY answer is not verified, the block must show the untrusted
  // label — a single verified row must not launder an unverified sibling.
  return answers.some(
    (a) =>
      (a.answer_status as { verified_correct?: boolean } | null)
        ?.verified_correct !== true,
  );
}

export function AnswerSection({
  answers,
  showRaw = false,
}: {
  answers: AnswerLike[];
  showRaw?: boolean;
}) {
  if (answers.length === 0) return null;
  const isPendingReview = computeIsPendingReview(answers);
  return (
    <div className="mb-2">
      <div className="mb-1 text-[13px] font-semibold text-ink-muted">
        {isPendingReview ? "待核实答案（非标准答案）" : "答案"}
      </div>
      {isPendingReview && (
        <p className="mb-2 text-[12px] text-amber-700">
          以下答案尚未通过来源核验，可能不正确，请勿作为标准答案使用。
        </p>
      )}
      {answers.map((a, i) => (
        <div key={a.id ?? i} className="flex gap-2 text-[15px]">
          {a.label &&
            !String(a.text ?? "").trimStart().startsWith(a.label) && (
              <span className="font-medium">{a.label}.</span>
            )}
          <MathText text={String(a.text ?? "")} />
          {showRaw && (
            <pre className="mt-1 whitespace-pre-wrap rounded bg-canvas-parchment p-2 text-[12px] text-ink-muted">
              {a.text}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}
