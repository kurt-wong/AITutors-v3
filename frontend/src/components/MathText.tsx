/** MathText：`$...$` 行内公式渲染（KaTeX）。失败降级为原始文本，不整页崩溃。 */

import katex from "katex";
import "katex/dist/katex.min.css";
import { useMemo } from "react";

type Piece = { kind: "text"; value: string } | { kind: "math"; value: string; html: string | null };

/** 匹配 `$...$`（允许两侧空格）；不支持 `$$...$$` 块级（本库数据未出现）。 */
const MATH_RE = /\$\s*([^$]+?)\s*\$/g;

function splitPieces(src: string): Piece[] {
  const out: Piece[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  const re = new RegExp(MATH_RE.source, "g");
  while ((m = re.exec(src)) !== null) {
    if (m.index > last) {
      out.push({ kind: "text", value: src.slice(last, m.index) });
    }
    const raw = m[1];
    let html: string | null = null;
    try {
      html = katex.renderToString(raw, {
        throwOnError: true,
        displayMode: false,
        output: "html",
      });
    } catch {
      html = null;
    }
    out.push({ kind: "math", value: m[0], html });
    last = m.index + m[0].length;
  }
  if (last < src.length) {
    out.push({ kind: "text", value: src.slice(last) });
  }
  return out;
}

export function MathText({
  text,
  className,
}: {
  text: string;
  className?: string;
}) {
  const pieces = useMemo(() => splitPieces(text ?? ""), [text]);
  return (
    <span className={className}>
      {pieces.map((p, i) => {
        if (p.kind === "text") return <span key={i}>{p.value}</span>;
        if (p.html == null) {
          // 渲染失败降级：原始片段 + 可理解提示，不影响整页
          return (
            <span
              key={i}
              title="公式渲染失败，已显示原始内容"
              className="rounded bg-amber-50 px-1 font-mono text-[0.95em] text-amber-800"
            >
              {p.value}
            </span>
          );
        }
        return (
          <span
            key={i}
            className="katex-inline"
            dangerouslySetInnerHTML={{ __html: p.html }}
          />
        );
      })}
    </span>
  );
}
