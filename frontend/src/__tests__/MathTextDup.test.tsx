/**
 * MathText 重复渲染表格展示策略（R2X）：
 * show=如实全显；annotate=全显+标注（管理端）；collapse=折叠披露（学生端）。
 * 用 renderToStaticMarkup 对真实渲染结果断言。
 */
import { describe, expect, it } from "vitest";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MathText } from "../components/MathText";

// Q10 真实形态：完整表（带空格）+ 解析区拆行重复（无空格）
const Q10_TEXT = [
  "某人某天需要运动总时长大于等于60分钟，如表所示：",
  "<table border=1><tr><td style='text-align: center;'>A 运动</td><td style='text-align: center;'>B 运动</td></tr><tr><td style='text-align: center;'>30 分钟</td><td style='text-align: center;'>20 分钟</td></tr></table>",
  "<table border=1><tr><td style='text-align: center;'>A运动</td><td style='text-align: center;'>B运动</td></tr></table>",
  "<table border=1><tr><td style='text-align: center;'>30分钟</td><td style='text-align: center;'>20分钟</td></tr></table>",
].join("\n");

function render(mode?: "show" | "annotate" | "collapse"): string {
  return renderToStaticMarkup(
    createElement(MathText, {
      text: Q10_TEXT,
      ...(mode ? { duplicateTables: mode } : {}),
    }),
  );
}

describe("MathText duplicateTables 策略", () => {
  it("默认 show：三表全显，无标注无折叠", () => {
    const html = render();
    expect(html.match(/<table/g)).toHaveLength(3);
    expect(html).not.toContain("重复渲染表格");
    expect(html).not.toContain("<details");
  });

  it("annotate（管理端）：三表全显 + 2 处重复标注", () => {
    const html = render("annotate");
    expect(html.match(/<table/g)).toHaveLength(3);
    expect(html.match(/重复渲染表格/g)).toHaveLength(2);
    expect(html).toContain("如实显示");
    expect(html).not.toContain("<details");
  });

  it("collapse（学生端）：主表直显，重复进可展开披露", () => {
    const html = render("collapse");
    // 主表 + 折叠内 2 表仍存在（可展开，不吞内容）
    expect(html.match(/<table/g)).toHaveLength(3);
    expect(html.match(/<details/g)).toHaveLength(2);
    expect(html).toContain("展开查看");
    // 主表（带空格内容）在披露外直接可见
    expect(html.indexOf("A 运动")).toBeLessThan(html.indexOf("<details"));
  });

  it("不同表格共存时不折叠（非重复不动）", () => {
    const text =
      "<table><tr><td>x1</td></tr></table><table><tr><td>y1</td></tr></table>";
    const html = renderToStaticMarkup(
      createElement(MathText, { text, duplicateTables: "collapse" }),
    );
    expect(html.match(/<table/g)).toHaveLength(2);
    expect(html).not.toContain("<details");
    expect(html).not.toContain("重复渲染表格");
  });
});
