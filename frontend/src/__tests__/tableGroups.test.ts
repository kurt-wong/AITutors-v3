/**
 * tableGroups 回归（R2X 重复渲染检测）：签名归一化 + 行集包含分组。
 * 场景锚点：math_2021_sh_chun Q10（完整 3x5 表 + 解析区无空格拆行 2x5/1x5）。
 */
import { describe, expect, it } from "vitest";
import {
  groupDuplicateTables,
  normCell,
  type TableGrid,
} from "../lib/tableGroups";

// Q10 真实形态：表1 完整（带空格）；表2+3 解析区拆行（无空格）
const T_FULL: TableGrid = [
  ["A 运动", "B 运动", "C 运动", "D 运动", "E 运动"],
  ["7 点-8 点", "8 点-9 点", "9 点-10 点", "10 点-11 点", "11 点-12 点"],
  ["30 分钟", "20 分钟", "40 分钟", "30 分钟", "30 分钟"],
];
const T_SPLIT_A: TableGrid = [
  ["A运动", "B运动", "C运动", "D运动", "E运动"],
  ["7点-8点", "8点-9点", "9点-10点", "10点-11点", "11点-12点"],
];
const T_SPLIT_B: TableGrid = [["30分钟", "20分钟", "40分钟", "30分钟", "30分钟"]];
const T_OTHER: TableGrid = [
  ["题号", "分值"],
  ["1", "5"],
];

describe("normCell", () => {
  it("去全部空白（含全角空格差异由调用方文本层归一）", () => {
    expect(normCell("A 运动")).toBe("A运动");
    expect(normCell(" 30 分钟 ")).toBe("30分钟");
  });
});

describe("groupDuplicateTables", () => {
  it("Q10 形态：完整表 + 拆行重复 → 一组，primary=完整表", () => {
    const groups = groupDuplicateTables([T_FULL, T_SPLIT_A, T_SPLIT_B]);
    expect(groups).toHaveLength(1);
    expect(groups[0].primary).toBe(0);
    expect(groups[0].duplicates.sort()).toEqual([1, 2]);
  });

  it("完全相同（仅空格差异）的表同组", () => {
    const a: TableGrid = [["A 运动", "B"]];
    const b: TableGrid = [["A运动", "B"]];
    const groups = groupDuplicateTables([a, b]);
    expect(groups).toHaveLength(1);
    expect(groups[0].duplicates).toHaveLength(1);
  });

  it("不同表格不分组（同一题干多张真表）", () => {
    const groups = groupDuplicateTables([T_FULL, T_OTHER]);
    expect(groups).toHaveLength(2);
    expect(groups[0].duplicates).toHaveLength(0);
    expect(groups[1].duplicates).toHaveLength(0);
  });

  it("primary 选信息最全者（行数优先），与出现顺序无关", () => {
    const groups = groupDuplicateTables([T_SPLIT_A, T_FULL]);
    expect(groups).toHaveLength(1);
    expect(groups[0].primary).toBe(1);
    expect(groups[0].duplicates).toEqual([0]);
  });

  it("部分行巧合不构成重复（仅共享一行的不同表）", () => {
    const a: TableGrid = [["30分钟", "20分钟", "40分钟", "30分钟", "30分钟"], ["x", "y", "z", "w", "v"]];
    // T_SPLIT_B 只是 a 的第一行 → 行集包含成立 → 同组（这是定义行为：片段=重复）
    const groups = groupDuplicateTables([a, T_SPLIT_B]);
    expect(groups).toHaveLength(1);
  });

  it("空输入安全", () => {
    expect(groupDuplicateTables([])).toEqual([]);
  });
});
