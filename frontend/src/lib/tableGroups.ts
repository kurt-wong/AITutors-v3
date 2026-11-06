/**
 * tableGroups（R2X 重复渲染检测）：同一题干内内容重复的表格分组。
 *
 * 背景：数据层 stem.extra_lines 把解析区重复表渲染行混入题干（如
 * math_2021_sh_chun Q10：完整 3x5 表 + 无空格拆行 2x5/1x5），物化文本里
 * 同一表格出现多份。展示层按「归一化行集包含关系」识别重复族，供
 * 管理端标注 / 学生端折叠——只控可见性，不改任何文本内容。
 */

/** 归一化单元格：去全部空白（重复渲染差异正是空格）。 */
export function normCell(s: string): string {
  return (s || "").replace(/\s+/g, "");
}

/** 表格网格：行 = 单元格字符串数组。 */
export type TableGrid = string[][];

export interface TableGroup {
  /** 组内最全表格（行数优先、单元格总数次之、原序最后）的下标 */
  primary: number;
  /** 组内其余表格下标（重复渲染片段） */
  duplicates: number[];
}

function rowKey(row: string[]): string {
  return row.map(normCell).join("|");
}

function rowsCovered(outer: TableGrid, inner: TableGrid): boolean {
  const bag = new Map<string, number>();
  for (const r of outer) {
    const k = rowKey(r);
    bag.set(k, (bag.get(k) ?? 0) + 1);
  }
  for (const r of inner) {
    const k = rowKey(r);
    const n = bag.get(k) ?? 0;
    if (n <= 0) return false;
    bag.set(k, n - 1);
  }
  return true;
}

function cellCount(g: TableGrid): number {
  return g.reduce((acc, r) => acc + r.length, 0);
}

/**
 * 重复族分组：两表存在行集包含关系（任一方覆盖另一方）即同族。
 * 组内 primary = 信息最全者；其余为重复渲染片段。
 * 无包含关系的不同表格不分组（同一题干多张真表格互不影响）。
 */
export function groupDuplicateTables(tables: TableGrid[]): TableGroup[] {
  const n = tables.length;
  const parent = Array.from({ length: n }, (_, i) => i);
  const find = (i: number): number => {
    while (parent[i] !== i) {
      parent[i] = parent[parent[i]];
      i = parent[i];
    }
    return i;
  };
  const union = (a: number, b: number) => {
    const ra = find(a);
    const rb = find(b);
    if (ra !== rb) parent[rb] = ra;
  };
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (
        rowsCovered(tables[i], tables[j]) ||
        rowsCovered(tables[j], tables[i])
      ) {
        union(i, j);
      }
    }
  }
  const byRoot = new Map<number, number[]>();
  for (let i = 0; i < n; i++) {
    const r = find(i);
    const list = byRoot.get(r) ?? [];
    list.push(i);
    byRoot.set(r, list);
  }
  const out: TableGroup[] = [];
  for (const members of byRoot.values()) {
    const ranked = [...members].sort((a, b) => {
      const ra = tables[a].length - tables[b].length;
      if (ra !== 0) return -ra;
      const ca = cellCount(tables[a]) - cellCount(tables[b]);
      if (ca !== 0) return -ca;
      return a - b;
    });
    out.push({ primary: ranked[0], duplicates: ranked.slice(1) });
  }
  out.sort((a, b) => a.primary - b.primary);
  return out;
}
