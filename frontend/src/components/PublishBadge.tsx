/** PublishBadge（VIS-INSPECT-V1）：答案发布状态真实标注。
 *  official=绿 / withheld_review=红 / mixed=黄 / none=灰。不做美化掩饰。 */

const STYLES: Record<string, { cls: string; label: string }> = {
  official: { cls: "bg-emerald-100 text-emerald-800", label: "official 已发布" },
  withheld_review: {
    cls: "bg-red-100 text-red-800",
    label: "withheld_review 未发布",
  },
  mixed: { cls: "bg-amber-100 text-amber-800", label: "mixed 部分发布" },
  none: { cls: "bg-gray-100 text-gray-600", label: "none 无答案行" },
};

export function PublishBadge({ publish }: { publish: string }) {
  const s = STYLES[publish] ?? {
    cls: "bg-gray-100 text-gray-600",
    label: publish || "unknown",
  };
  return (
    <span
      className={`inline-block rounded-pill px-2 py-0.5 text-[11px] font-medium whitespace-nowrap ${s.cls}`}
    >
      {s.label}
    </span>
  );
}
