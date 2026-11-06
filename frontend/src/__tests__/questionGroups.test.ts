/** questionGroups 回归：复合题真实层级分组 + HTML 残片检出 + 图片引用检出。 */

import { describe, expect, it } from "vitest";
import {
  extractImageRefs,
  findHtmlResidue,
  findHtmlStructures,
  groupQuestionContents,
  stripStemNumber,
  type RoleContentLike,
} from "../lib/questionGroups";

function c(
  role: string,
  text: string,
  opts: Partial<RoleContentLike> = {},
): RoleContentLike {
  return { role, text, role_index: 0, ...opts };
}

describe("groupQuestionContents（复合题层级）", () => {
  it("英语阅读复合题：material 共享 + 子问题按题号归组", () => {
    const contents: RoleContentLike[] = [
      c("material", "## A\n Where to Eat", { role_index: 0 }),
      c("stem", "21. What do Nahm and Issaya have in common?", { role_index: 0 }),
      c("stem", "22. Which restaurant offers a show?", { role_index: 1 }),
      c("option", "They adopt modern cooking.", { label: "21A", role_index: 0 }),
      c("option", "They have branches.", { label: "21B", role_index: 1 }),
      c("option", "Gaggan.", { label: "22A", role_index: 2 }),
      c("option", "Nahm.", { label: "22B", role_index: 3 }),
      c("answer", "A", { label: "21", role_index: 0 }),
      c("answer", "D", { label: "22", role_index: 1 }),
      c("explanation", "【导语】本文是应用文。", { role_index: 0 }),
    ];
    const g = groupQuestionContents(contents);
    expect(g.materials).toHaveLength(1);
    expect(g.explanations).toHaveLength(1);
    expect(g.subs).toHaveLength(2);
    expect(g.subs[0].key).toBe("21");
    expect(g.subs[0].title).toBe("子问题 21");
    expect(g.subs[0].options.map((o) => o.label)).toEqual(["21A", "21B"]);
    expect(g.subs[0].answers.map((a) => a.label)).toEqual(["21"]);
    expect(g.subs[1].key).toBe("22");
    expect(g.subs[1].options.map((o) => o.label)).toEqual(["22A", "22B"]);
  });

  it("单题：无数字键 → 单组平铺", () => {
    const contents: RoleContentLike[] = [
      c("stem", "1. 设全集 U = {1,2,3}", { role_index: 0 }),
      c("option", "{2,3}", { label: "A", role_index: 0 }),
      c("option", "{1,3}", { label: "B", role_index: 1 }),
      c("answer", "A", { role_index: 0 }),
    ];
    const g = groupQuestionContents(contents);
    expect(g.subs).toHaveLength(1);
    expect(g.subs[0].key).toBe("");
    expect(g.subs[0].options).toHaveLength(2);
    expect(g.subs[0].answers).toHaveLength(1);
    expect(g.subs[0].stems).toHaveLength(1);
  });

  it("单题多 stem：全部保留（鲁棒性，不丢第二根题干）", () => {
    const contents: RoleContentLike[] = [
      c("stem", "1. 第一问", { role_index: 0 }),
      c("stem", "补充说明段", { role_index: 1 }),
      c("answer", "A", { role_index: 0 }),
    ];
    const g = groupQuestionContents(contents);
    expect(g.subs).toHaveLength(1);
    expect(g.subs[0].stems.map((s) => s.text)).toEqual(["1. 第一问", "补充说明段"]);
  });

  it("未归组内容不静默丢弃，进『其他内容』块", () => {
    const contents: RoleContentLike[] = [
      c("stem", "21. 正常题干", { role_index: 0 }),
      c("option", "A项", { label: "21A", role_index: 0 }),
      c("answer", "A", { label: "21", role_index: 0 }),
      c("answer", "孤儿答案", { label: "错位", role_index: 1 }),
    ];
    const g = groupQuestionContents(contents);
    const orphan = g.subs.find((s) => s.key === "_orphan");
    expect(orphan).toBeTruthy();
    expect(orphan!.title).toBe("其他内容");
    expect(orphan!.answers.map((a) => a.label)).toEqual(["错位"]);
  });

  it("Q8/Q9 化学复合题：label=null 父 stem + label=1..6 子 stem + 数字 label answers", () => {
    // 模拟化学复合题：父级题头（label=null）+ 6 个子问（label='1'..'6'）
    const contents: RoleContentLike[] = [
      c("material", "实验材料说明……", { role_index: 0 }),
      c("stem", "8\\. (14分)\n\n\n回答下列问题：", { label: null, role_index: 0 }),
      c("stem", "（1）写出 Fe^{3+} 的检验方法", { label: "1", role_index: 1 }),
      c("stem", "（2）计算 pH 值", { label: "2", role_index: 2 }),
      c("stem", "（3）判断盐桥方向", { label: "3", role_index: 3 }),
      c("stem", "（4）写出电极反应", { label: "4", role_index: 4 }),
      c("stem", "（5）解释现象", { label: "5", role_index: 5 }),
      c("stem", "（6）总结结论", { label: "6", role_index: 6 }),
      c("answer", "取少量试液…", { label: "1", role_index: 0 }),
      c("answer", "pH=2", { label: "2", role_index: 1 }),
      c("answer", "左正右负", { label: "3", role_index: 2 }),
      c("answer", "Fe-3e⁻=Fe³⁺", { label: "4", role_index: 3 }),
      c("answer", "生成沉淀", { label: "5", role_index: 4 }),
      c("answer", "结论……", { label: "6", role_index: 5 }),
      c("explanation", "组解析", { label: null, role_index: 0 }),
      c("display_note", "本题分值 14 分", { label: "q9_concentration_original", role_index: 0 }),
    ];
    const g = groupQuestionContents(contents);
    // 父 stem 在主组 key=''（title='题目'），在子问组之前
    const mainGroup = g.subs.find((s) => s.key === "");
    expect(mainGroup).toBeTruthy();
    expect(mainGroup!.title).toBe("题目");
    expect(mainGroup!.stems).toHaveLength(1);
    expect(mainGroup!.stems[0].text).toContain("回答下列问题");
    // 主组在 6 个子问组之上（数组序在前）
    expect(g.subs[0].key).toBe("");
    // 6 个子问各挂到 '子问题 N'
    const subKeys = g.subs.filter((s) => s.key !== "" && s.key !== "_orphan").map((s) => s.key);
    expect(subKeys).toEqual(["1", "2", "3", "4", "5", "6"]);
    for (let i = 1; i <= 6; i++) {
      const sub = g.subs.find((s) => s.key === String(i));
      expect(sub).toBeTruthy();
      expect(sub!.title).toBe(`子问题 ${i}`);
      expect(sub!.stems).toHaveLength(1);
      expect(sub!.stems[0].label).toBe(String(i));
      expect(sub!.answers).toHaveLength(1);
      expect(sub!.answers[0].label).toBe(String(i));
    }
    // 无 orphan
    expect(g.subs.find((s) => s.key === "_orphan")).toBeFalsy();
    // displayNotes 通道
    expect(g.displayNotes).toHaveLength(1);
    expect(g.displayNotes[0].label).toBe("q9_concentration_original");
  });

  it("（N）文本启发式兜底（无 label 时）", () => {
    // 子问 stem 无 label，靠文本开头 （N）/ (N) / （N）． 归组
    const contents: RoleContentLike[] = [
      c("stem", "（1）求 sin A：", { role_index: 0 }),
      c("stem", "(2) 计算面积", { role_index: 1 }),
      c("stem", "（3）．证明结论", { role_index: 2 }),
      c("answer", "A=30°", { label: "1", role_index: 0 }),
      c("answer", "S=42", { label: "2", role_index: 1 }),
      c("answer", "证明略", { label: "3", role_index: 2 }),
    ];
    const g = groupQuestionContents(contents);
    const sub1 = g.subs.find((s) => s.key === "1");
    const sub2 = g.subs.find((s) => s.key === "2");
    const sub3 = g.subs.find((s) => s.key === "3");
    expect(sub1!.stems.map((s) => s.text)).toEqual(["（1）求 sin A："]);
    expect(sub2!.stems.map((s) => s.text)).toEqual(["(2) 计算面积"]);
    expect(sub3!.stems.map((s) => s.text)).toEqual(["（3）．证明结论"]);
    // 不应有 orphan 或 parent 组
    expect(g.subs.find((s) => s.key === "_orphan")).toBeFalsy();
  });

  it("displayNotes 通道：role='display_note' 独立出", () => {
    const contents: RoleContentLike[] = [
      c("stem", "1. 题干", { role_index: 0 }),
      c("answer", "A", { role_index: 0 }),
      c("display_note", "浓度参考原始值", { label: "q9_concentration_original", role_index: 0 }),
      c("display_note", "实验温度 25°C", { label: null, role_index: 1 }),
    ];
    const g = groupQuestionContents(contents);
    expect(g.displayNotes).toHaveLength(2);
    expect(g.displayNotes[0].text).toBe("浓度参考原始值");
    expect(g.displayNotes[1].text).toBe("实验温度 25°C");
    // display_note 不混入 stems / explanations
    expect(g.subs[0].stems).toHaveLength(1);
    expect(g.explanations).toHaveLength(0);
  });
});

describe("findHtmlResidue（R2X-04 类残片必须可见）", () => {
  it("检出 </div> 等被渲染层消隐的容器标签", () => {
    const contents: RoleContentLike[] = [
      c("option", "A. 正常</div>残片", { label: "A", role_index: 0 }),
    ];
    const r = findHtmlResidue(contents);
    expect(r).toHaveLength(1);
    expect(r[0].raw).toBe("</div>");
    expect(r[0].role).toBe("option");
    expect(r[0].label).toBe("A");
  });

  it("<img>/<br>/<hr> 是合法渲染标签，不报残片", () => {
    const contents: RoleContentLike[] = [
      c("stem", '题干 <img src="x.jpg"> 换行<br>继续', { role_index: 0 }),
    ];
    expect(findHtmlResidue(contents)).toHaveLength(0);
  });

  it("成对 <table> 的结构标签不计残片，但单独披露（不洗零）", () => {
    const contents: RoleContentLike[] = [
      c("stem", "<table><tr><td>A 运动</td><td>30 分钟</td></tr></table>", {
        role_index: 0,
      }),
    ];
    expect(findHtmlResidue(contents)).toHaveLength(0);
    const structs = findHtmlStructures(contents);
    // table/tr/td/闭合标签全部可见计数：8 处（2 单元格）
    expect(structs).toHaveLength(8);
    expect(structs.map((s) => s.tag)).toEqual(
      expect.arrayContaining(["table", "tr", "td"]),
    );
  });

  it("块外孤残表格标签（如 </td>）仍算残片", () => {
    const contents: RoleContentLike[] = [
      c("option", "A. 正常</td>残片", { label: "A", role_index: 0 }),
    ];
    const r = findHtmlResidue(contents);
    expect(r).toHaveLength(1);
    expect(r[0].raw).toBe("</td>");
    expect(findHtmlStructures(contents)).toHaveLength(0);
  });

  it("表格结构 + 真残片共存：分类分离", () => {
    const contents: RoleContentLike[] = [
      c(
        "stem",
        "<table><tr><td>x</td></tr></table></div>",
        { role_index: 0 },
      ),
    ];
    const r = findHtmlResidue(contents);
    expect(r).toHaveLength(1);
    expect(r[0].raw).toBe("</div>");
    expect(findHtmlStructures(contents)).toHaveLength(6);
  });
});

describe("extractImageRefs", () => {
  it("提取 img 引用并经 resolveSrc 映射", () => {
    const contents: RoleContentLike[] = [
      c("stem", '看图 <img src="../../_imgs/paper/img_1.jpg">', { role_index: 0 }),
    ];
    const refs = extractImageRefs(contents, (raw) => `/api/images/${raw.split("_imgs/")[1]}`);
    expect(refs).toHaveLength(1);
    expect(refs[0].url).toBe("/api/images/paper/img_1.jpg");
  });
});

describe("stripStemNumber（展示层剥前导题号）", () => {
  it("剥离半角/全角句点/顿号题号", () => {
    expect(stripStemNumber("1. 设全集 U = {1,2,3}")).toBe("设全集 U = {1,2,3}");
    expect(stripStemNumber("21. What do Nahm and Issaya have in common?")).toBe(
      "What do Nahm and Issaya have in common?",
    );
    expect(stripStemNumber("3、下列说法正确的是")).toBe("下列说法正确的是");
    expect(stripStemNumber("12．已知函数 f(x)")).toBe("已知函数 f(x)");
  });

  it("剥离转义点形态题号（N\\. 源文 OCR 产物）", () => {
    expect(stripStemNumber("1\\. 2017年，我国科学家")).toBe("2017年，我国科学家");
    expect(stripStemNumber("13\\. 下列营养物质中")).toBe("下列营养物质中");
  });

  it("只剥开头一处；无题号不动；数字开头但无点不剥", () => {
    expect(stripStemNumber("（1）求 sin A：")).toBe("（1）求 sin A：");
    expect(stripStemNumber("2021 年高考题")).toBe("2021 年高考题");
    expect(stripStemNumber("15. 在横线处填写 3. 文学常识")).toBe("在横线处填写 3. 文学常识");
  });
});
