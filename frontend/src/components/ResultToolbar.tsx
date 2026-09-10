/** Result Toolbar：毛玻璃浮层工具条（UI.md §3.7）。 */

interface ResultToolbarProps {
  mode: "display" | "review";
  onModeChange: (mode: "display" | "review") => void;
}

export function ResultToolbar({ mode, onModeChange }: ResultToolbarProps) {
  return (
    <div className="sticky top-0 z-10 flex items-center gap-3 rounded-lg border border-hairline bg-white/80 px-4 py-2 backdrop-blur-md">
      <span className="text-[13px] font-semibold text-ink-muted">View</span>
      <div className="flex overflow-hidden rounded-sm border border-hairline">
        <button
          onClick={() => onModeChange("display")}
          className={`px-3 py-1 text-[13px] transition-colors ${
            mode === "display"
              ? "bg-primary text-white"
              : "bg-white text-ink hover:bg-canvas-parchment"
          }`}
        >
          Display
        </button>
        <button
          onClick={() => onModeChange("review")}
          className={`px-3 py-1 text-[13px] transition-colors ${
            mode === "review"
              ? "bg-primary text-white"
              : "bg-white text-ink hover:bg-canvas-parchment"
          }`}
        >
          Review
        </button>
      </div>
    </div>
  );
}
