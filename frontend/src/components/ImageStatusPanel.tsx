/** ImageStatusPanel（VIS-INSPECT-V1）：图片引用与真实加载状态。
 *  对每条 <img> 引用做可见探针加载；失败直接标红显示 URL，不静默隐藏。 */

import { useState } from "react";
import type { ImageRef } from "../lib/questionGroups";

type ProbeStatus = "loading" | "ok" | "fail";

export function ImageStatusPanel({ refs }: { refs: ImageRef[] }) {
  const [status, setStatus] = useState<Record<string, ProbeStatus>>({});

  if (refs.length === 0) {
    return (
      <div className="rounded-lg border border-hairline bg-white p-3 text-[12px] text-ink-muted">
        图片引用：本题文本中未检出 &lt;img&gt; 引用。
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-hairline bg-white p-3">
      <div className="mb-2 text-[13px] font-semibold text-ink-muted">
        图片引用（{refs.length}）与加载状态
      </div>
      <ul className="space-y-2">
        {refs.map((r, i) => {
          const key = `${r.role}-${r.label ?? ""}-${i}`;
          const st = status[key] ?? "loading";
          return (
            <li key={key} className="flex items-center gap-3 text-[12px]">
              <span className="w-28 shrink-0 text-ink-muted">
                [{r.role}]{r.label ? ` ${r.label}` : ""}
              </span>
              {r.url ? (
                <img
                  src={r.url}
                  alt={r.src}
                  className="max-h-16 rounded border border-hairline"
                  onLoad={() => setStatus((s) => ({ ...s, [key]: "ok" }))}
                  onError={() => setStatus((s) => ({ ...s, [key]: "fail" }))}
                />
              ) : (
                <span className="rounded bg-red-50 px-1 text-red-700">
                  无法安全映射
                </span>
              )}
              <span
                className={
                  st === "fail"
                    ? "rounded bg-red-50 px-1 font-medium text-red-700"
                    : st === "ok"
                      ? "rounded bg-emerald-50 px-1 text-emerald-700"
                      : "rounded bg-canvas-parchment px-1 text-ink-muted"
                }
              >
                {st === "fail" ? "加载失败" : st === "ok" ? "加载成功" : "加载中…"}
              </span>
              <span
                className="min-w-0 flex-1 truncate font-mono text-[11px] text-ink-muted"
                title={r.url ?? r.src}
              >
                {r.url ?? r.src}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
