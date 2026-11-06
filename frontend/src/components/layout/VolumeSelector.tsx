/** VolumeSelector（VIS-INSPECT-V1 + DSH-F1/F2 加固）：隔离卷库切换。
 *
 * 数据来自真实 /api/inspect/databases（白名单 ml_* 卷库 + 默认库）。
 * DSH-F1：选中即写入请求上下文（X-Inspect-Db），读接口不依赖进程级活动库，
 * 消除并行脚本切换活动库的竞态；activate 仍执行（兼容无头调用方与写保护）。
 * DSH-F2：下拉按批次分组，R2X 验收批次置顶，避免遗留 e2e 库被误认。
 */

import { useEffect, useState } from "react";
import { activateDatabase, listDatabases, setInspectDb } from "../../api/client";
import type { DatabaseInfo } from "../../api/types";

function groupOf(d: DatabaseInfo): string {
  if (d.is_default) return "默认库";
  if (d.series === "r2x") return "R2X 批次（48 卷验收）";
  if (d.series && d.series.startsWith("r2")) return "R2 修复/验证库";
  if (d.series === "r1") return "R1 批次";
  return "其它（e2e/遗留，非验收数据）";
}

const GROUP_ORDER = [
  "R2X 批次（48 卷验收）",
  "R2 修复/验证库",
  "R1 批次",
  "其它（e2e/遗留，非验收数据）",
  "默认库",
];

export function VolumeSelector({ onChanged }: { onChanged?: () => void }) {
  const [dbs, setDbs] = useState<DatabaseInfo[]>([]);
  const [active, setActive] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDatabases()
      .then((r) => {
        setDbs(r.databases);
        setActive(r.active_db_name);
        setInspectDb(r.active_db_name);
      })
      .catch((e) => setError(String(e)));
  }, []);

  async function switchTo(name: string) {
    if (!name || name === active || busy) return;
    setBusy(true);
    setError(null);
    // F1：先写请求上下文再切活动库——即使 activate 慢/失败，读请求也已指向新库
    setInspectDb(name);
    setActive(name);
    try {
      const info = await activateDatabase(name);
      setActive(info.db_name);
      setDbs((prev) =>
        prev.map((d) => ({ ...d, is_active: d.db_name === info.db_name })),
      );
      onChanged?.();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  const label = (d: DatabaseInfo) => {
    const parts = [d.db_name];
    if (d.subject_hint || d.year) {
      parts.push(
        `（${d.subject_hint ?? d.subject ?? "?"}${d.year ? " " + d.year : ""}${d.region ? " " + d.region : ""}）`,
      );
    }
    if (d.question_count != null) parts.push(`· ${d.question_count} 题`);
    return parts.join(" ");
  };

  const grouped = GROUP_ORDER.map((g) => ({
    name: g,
    items: dbs.filter((d) => groupOf(d) === g),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="flex items-center gap-2">
      <label className="text-[11px] text-body-muted" htmlFor="volume-select">
        卷库
      </label>
      <select
        id="volume-select"
        className="h-7 max-w-[320px] rounded border border-white/20 bg-surface-tile px-2 text-[12px] text-white"
        value={active}
        disabled={busy || dbs.length === 0}
        onChange={(e) => switchTo(e.target.value)}
      >
        {grouped.map((g) => (
          <optgroup key={g.name} label={g.name}>
            {g.items.map((d) => (
              <option key={d.db_name} value={d.db_name}>
                {label(d)}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      {busy && <span className="text-[11px] text-body-muted">切换中…</span>}
      {error && (
        <span
          className="max-w-[220px] truncate text-[11px] text-amber-300"
          title={error}
        >
          {error}
        </span>
      )}
    </div>
  );
}
