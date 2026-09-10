/** Admin Workspace (/admin)：摘要卡 + 最近任务。 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminStats, listTasks } from "../api/client";
import type { AdminStats, TaskSummary } from "../api/types";

export function AdminWorkspace() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch((e) => setError(String(e)));
    listTasks({ limit: 10 })
      .then((r) => setTasks(r.tasks))
      .catch(() => {});
  }, []);

  const cards = stats
    ? [
        { label: "Pending Review", value: stats.pending_review },
        { label: "Running Tasks", value: stats.running_tasks },
        { label: "Failed Tasks", value: stats.failed_tasks },
        { label: "Approved Today", value: stats.approved_today },
      ]
    : [];

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl font-semibold tracking-tight">
        Review Console
      </h1>

      {error && (
        <div className="rounded-lg border border-hairline bg-canvas-parchment p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {cards.map((c) => (
          <div
            key={c.label}
            className="rounded-lg border border-hairline bg-white p-5"
          >
            <div className="text-[13px] font-semibold text-ink-muted">
              {c.label}
            </div>
            <div className="mt-1 font-display text-3xl font-semibold tracking-tight">
              {c.value}
            </div>
          </div>
        ))}
      </div>

      <div>
        <h2 className="mb-3 font-display text-lg font-semibold tracking-tight">
          Recent Tasks
        </h2>
        {tasks.length === 0 ? (
          <p className="text-sm text-ink-muted">No tasks yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-hairline text-left text-[13px] font-semibold text-ink-muted">
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Stage</th>
                <th className="pb-2 pr-4">LLM Calls</th>
                <th className="pb-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id} className="border-b border-hairline">
                  <td className="py-2 pr-4">{t.task_type}</td>
                  <td className="py-2 pr-4">
                    <StatusBadge status={t.status} />
                  </td>
                  <td className="py-2 pr-4">{t.current_stage ?? "—"}</td>
                  <td className="py-2 pr-4">{t.llm_invocations}</td>
                  <td className="py-2 text-ink-muted">
                    {t.created_at
                      ? new Date(t.created_at).toLocaleString()
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="flex gap-4">
        <Link
          to="/admin/documents"
          className="rounded-pill bg-primary px-5 py-2 text-sm font-semibold text-white transition-transform active:scale-95"
        >
          Browse Documents
        </Link>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: "text-blue-600",
    succeeded: "text-green-600",
    failed: "text-red-600",
    queued: "text-ink-muted",
    created: "text-ink-muted",
    interrupted: "text-amber-600",
  };
  return (
    <span className={`font-medium ${colors[status] ?? "text-ink"}`}>
      {status}
    </span>
  );
}
