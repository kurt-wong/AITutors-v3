/** AnswerRevealBox（VIS-INSPECT-V1 迭代）：答案与解析默认折叠。
 *
 * 题干/选项默认展示；答案/解析需点击「生成答案与解析」再显示——
 * 给学生保留独立思考时间。收起后可再次展开。
 */

import { useState, type ReactNode } from "react";

export function AnswerRevealBox({
  children,
  emptyHint,
}: {
  children: ReactNode;
  emptyHint?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-hairline bg-white p-6">
      <div className="flex items-center justify-between gap-3">
        <div className="text-[13px] font-semibold text-ink-muted">答案与解析</div>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className={`rounded px-4 py-1.5 text-[13px] font-medium transition-colors ${
            open
              ? "border border-hairline bg-canvas-parchment text-ink-muted hover:bg-white"
              : "bg-primary text-white hover:opacity-90"
          }`}
        >
          {open ? "收起答案与解析" : "生成答案与解析"}
        </button>
      </div>
      {open ? (
        <div className="mt-4">{children}</div>
      ) : (
        <p className="mt-2 text-[12px] text-ink-muted">
          {emptyHint ?? "先独立思考，准备好了点击右上「生成答案与解析」查看。"}
        </p>
      )}
    </div>
  );
}
