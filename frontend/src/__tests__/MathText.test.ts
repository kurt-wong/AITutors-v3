/**
 * V3-IMG-OPTION-003 — MathText HTML container tags + image URL mapping + security.
 */
import { describe, expect, it } from "vitest";
import {
  imageRenderStyle,
  resolveImageSrc,
  splitHtmlSegments,
  splitPieces,
} from "../components/MathText";

const GEO_IMG =
  '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考地理（教师版）(1)/img_in_image_box_114_100_392_229.jpg" alt="Image" width="23%" /></div>';

const PHY_IMG_A =
  '<div style="text-align: center;"><img src="../../_imgs/2018北京夏季高中会考物理（教师版）(1)/img_in_image_box_72_1439_218_1534.jpg" alt="Image" width="12%" /></div>';

describe("resolveImageSrc — URL mapping", () => {
  it("maps ../../_imgs/<paper>/img.jpg to /api/images/<paper>/img.jpg", () => {
    const out = resolveImageSrc(
      "../../_imgs/2018北京夏季高中会考地理（教师版）(1)/img_in_image_box_114_100_392_229.jpg",
    );
    expect(out).toBe(
      "/api/images/2018北京夏季高中会考地理（教师版）(1)/img_in_image_box_114_100_392_229.jpg",
    );
  });

  it("maps imgs/<file>.jpg (新管线同目录引用, key 保留 imgs/ 段) to /api/images/imgs/<file>.jpg", () => {
    expect(resolveImageSrc("imgs/img_in_image_box_157_151_247_252.jpg")).toBe(
      "/api/images/imgs/img_in_image_box_157_151_247_252.jpg",
    );
  });

  it("keeps already-mapped /api/images/ URLs", () => {
    expect(resolveImageSrc("/api/images/paper/img.jpg")).toBe(
      "/api/images/paper/img.jpg",
    );
  });

  it("maps Windows-style backslash refs", () => {
    const out = resolveImageSrc("..\\_imgs\\paper\\img.png");
    expect(out).toBe("/api/images/paper/img.png");
  });
});

describe("resolveImageSrc — security", () => {
  it("rejects protocol-relative URLs", () => {
    expect(resolveImageSrc("//evil.com/x.jpg")).toBeNull();
  });

  it("rejects javascript/data/vbscript schemes", () => {
    expect(resolveImageSrc("javascript:alert(1)")).toBeNull();
    expect(resolveImageSrc("data:image/png;base64,xx")).toBeNull();
    expect(resolveImageSrc("vbscript:msgbox")).toBeNull();
  });

  it("rejects path traversal segments", () => {
    expect(resolveImageSrc("../../_imgs/../etc/passwd.jpg")).toBeNull();
    expect(resolveImageSrc("../../_imgs/a/../../b.jpg")).toBeNull();
    expect(resolveImageSrc("/api/images/../secret.jpg")).toBeNull();
    expect(resolveImageSrc("/api/images/./x.jpg")).toBeNull();
  });

  it("rejects non-image extensions", () => {
    expect(resolveImageSrc("../../_imgs/paper/evil.html")).toBeNull();
    expect(resolveImageSrc("../../_imgs/paper/evil.php")).toBeNull();
    expect(resolveImageSrc("/api/images/paper/x.txt")).toBeNull();
  });

  it("rejects cross-origin absolute URLs", () => {
    expect(resolveImageSrc("https://evil.com/x.jpg")).toBeNull();
    expect(resolveImageSrc("http://evil.com/api/images/x.jpg")).toBeNull();
  });

  it("rejects absolute Windows paths and empty", () => {
    expect(resolveImageSrc("C:/Windows/x.jpg")).toBeNull();
    expect(resolveImageSrc("")).toBeNull();
    expect(resolveImageSrc("   ")).toBeNull();
  });
});

describe("splitHtmlSegments — HTML container tags", () => {
  it("div+img wrapper: img is a piece, no literal div text", () => {
    const pieces = splitHtmlSegments(GEO_IMG);
    expect(pieces.some((p) => p.kind === "img")).toBe(true);
    for (const p of pieces) {
      if (p.kind === "text") {
        expect(p.value).not.toMatch(/<\/?div/i);
        expect(p.value).not.toMatch(/<img/i);
      }
    }
  });

  it("div with text content keeps the text, drops the tags", () => {
    const pieces = splitHtmlSegments(
      '<div style="text-align: center;">B.</div>',
    );
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("B.");
    expect(text).not.toMatch(/<\/?div/i);
  });

  it("consecutive image options each keep their own src", () => {
    const joined = [
      GEO_IMG,
      '<div style="text-align: center;">B.</div>',
      PHY_IMG_A,
    ].join("\n");
    const pieces = splitHtmlSegments(joined);
    const imgs = pieces.filter((p) => p.kind === "img") as Array<{
      kind: string;
      src: string;
    }>;
    expect(imgs).toHaveLength(2);
    expect(imgs[0].src).toContain("114_100_392_229");
    expect(imgs[1].src).toContain("72_1439_218_1534");
  });

  it("mixed text + image: both survive, tags gone", () => {
    const src = 'A. 苹果\n<div><img src="../../_imgs/p/i.jpg" /></div>';
    const pieces = splitHtmlSegments(src);
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("A. 苹果");
    expect(pieces.some((p) => p.kind === "img")).toBe(true);
    expect(text).not.toMatch(/<\/?div/i);
  });

  it("br / hr become br pieces", () => {
    const pieces = splitHtmlSegments("a<br/>b<hr/>c");
    expect(pieces.filter((p) => p.kind === "br")).toHaveLength(2);
  });

  it("unsafe img src is kept as raw text, not dropped", () => {
    const pieces = splitHtmlSegments(
      '<img src="javascript:alert(1)" alt="x" />',
    );
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("javascript:alert(1)");
    expect(pieces.some((p) => p.kind === "img")).toBe(false);
  });

  it("unknown tags are consumed, inner text kept", () => {
    const pieces = splitHtmlSegments("<foo><bar>foo</bar></foo>");
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("foo");
    expect(text).not.toMatch(/<\/?(foo|bar)/i);
  });
});

describe("splitHtmlSegments — 表格结构化渲染（R2X，非压平）", () => {
  const TABLE =
    "<table border=1 style='margin: auto;'><tr><td style='text-align: center;'>A 运动</td><td style='text-align: center;'>B 运动</td></tr><tr><td style='text-align: center;'>30 分钟</td><td style='text-align: center;'>20 分钟</td></tr></table>";

  it("成对 <table> 解析为表格 piece，行列矩阵保留", () => {
    const pieces = splitHtmlSegments(TABLE);
    expect(pieces).toHaveLength(1);
    const t = pieces[0];
    if (t.kind !== "table") throw new Error(`expected table, got ${t.kind}`);
    expect(t.rows).toHaveLength(2);
    expect(t.rows[0]).toHaveLength(2);
    const cellText = (pieces2: typeof t) =>
      pieces2.rows.map((r) =>
        r.map((c) =>
          c.pieces.map((p) => (p.kind === "text" ? p.value : "")).join(""),
        ),
      );
    expect(cellText(t)).toEqual([
      ["A 运动", "B 运动"],
      ["30 分钟", "20 分钟"],
    ]);
  });

  it("td 对齐与 th 表头保留", () => {
    const src =
      "<table><tr><th>题号</th></tr><tr><td style='text-align: right;'>42</td></tr></table>";
    const pieces = splitHtmlSegments(src);
    const t = pieces[0];
    if (t.kind !== "table") throw new Error("expected table");
    expect(t.rows[0][0].header).toBe(true);
    expect(t.rows[1][0].header).toBe(false);
    expect(t.rows[1][0].align).toBe("right");
    expect(t.rows[1][0].colspan).toBe(1);
  });

  it("单元内递归：$公式$ 与 <img> 进单元 piece", () => {
    const src =
      "<table><tr><td>$x^2$</td><td><img src='../../_imgs/p/i.jpg'></td></tr></table>";
    const pieces = splitHtmlSegments(src);
    const t = pieces[0];
    if (t.kind !== "table") throw new Error("expected table");
    expect(t.rows[0][0].pieces.some((p) => p.kind === "math")).toBe(true);
    expect(t.rows[0][1].pieces.some((p) => p.kind === "img")).toBe(true);
  });

  it("表前后的文本与表格共存", () => {
    const src = `如表所示：${TABLE}完`;
    const pieces = splitHtmlSegments(src);
    expect(pieces.filter((p) => p.kind === "table")).toHaveLength(1);
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("如表所示：");
    expect(text).toContain("完");
  });

  it("未闭合 <table> 不产表格 piece，内文保留（fail-visible）", () => {
    const src = "<table><tr><td>foo</td>";
    const pieces = splitHtmlSegments(src);
    expect(pieces.some((p) => p.kind === "table")).toBe(false);
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("foo");
  });

  it("caption 保留为 pieces", () => {
    const src = "<table><caption>表 1</caption><tr><td>x</td></tr></table>";
    const pieces = splitHtmlSegments(src);
    const t = pieces[0];
    if (t.kind !== "table") throw new Error("expected table");
    expect(t.caption).not.toBeNull();
    const cap = (t.caption ?? [])
      .map((p) => (p.kind === "text" ? p.value : ""))
      .join("");
    expect(cap).toContain("表 1");
  });
});

describe("splitPieces — regression", () => {
  it("plain text unchanged", () => {
    const pieces = splitPieces("A. 苹果");
    expect(pieces).toHaveLength(1);
    expect(pieces[0]).toMatchObject({ kind: "text", value: "A. 苹果" });
  });

  it("LaTeX is still detected", () => {
    const pieces = splitPieces("速度 $v=at$ 时刻");
    const kinds = pieces.map((p) => p.kind);
    expect(kinds).toContain("math");
    expect(kinds).toContain("text");
  });

  it("math + image both present", () => {
    const pieces = splitPieces(`$E=mc^2$ ${GEO_IMG}`);
    expect(pieces.some((p) => p.kind === "math")).toBe(true);
    expect(pieces.some((p) => p.kind === "img")).toBe(true);
  });
});

describe("splitPieces — 表格与公式共存（F3 表格修复）", () => {
  it("单元格含 $…$ 公式的 <table> 产生 table piece，矩阵保留", () => {
    const src =
      '<table><tr><td>$ Fe^{3+} $</td><td>$ SO_4^{2-} $</td></tr><tr><td>pH=2</td><td>$ K^+ $</td></tr></table>';
    const pieces = splitPieces(src);
    expect(pieces).toHaveLength(1);
    const t = pieces[0];
    if (t.kind !== "table") throw new Error(`expected table, got ${t.kind}`);
    expect(t.rows).toHaveLength(2);
    expect(t.rows[0]).toHaveLength(2);
    expect(t.rows[1]).toHaveLength(2);
    // 每个含 $…$ 的单元格内有 math piece
    expect(t.rows[0][0].pieces.some((p) => p.kind === "math")).toBe(true);
    expect(t.rows[0][1].pieces.some((p) => p.kind === "math")).toBe(true);
    expect(t.rows[1][1].pieces.some((p) => p.kind === "math")).toBe(true);
    // 纯文本单元格内容正确
    const cellText = (cell: typeof t.rows[0][0]) =>
      cell.pieces.map((p) => (p.kind === "text" ? p.value : p.kind === "math" ? p.value : "")).join("");
    expect(cellText(t.rows[1][0])).toBe("pH=2");
  });

  it("表前后文本共存，表格不被公式切碎", () => {
    const table =
      "<table><tr><td>$ Fe^{3+} $</td><td>文字</td></tr></table>";
    const src = `前文 $x^2$ ：${table}后文 $y$ 结束`;
    const pieces = splitPieces(src);
    const tables = pieces.filter((p) => p.kind === "table");
    expect(tables).toHaveLength(1);
    // 表前后文本与公式都保留
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("前文");
    expect(text).toContain("后文");
    expect(text).toContain("结束");
    const maths = pieces.filter((p) => p.kind === "math");
    expect(maths.length).toBeGreaterThanOrEqual(2); // x^2 和 y
  });

  it("未闭合 table 内文保留（splitPieces 路径）", () => {
    const src = "<table><tr><td>foo $x$ bar</td>";
    const pieces = splitPieces(src);
    expect(pieces.some((p) => p.kind === "table")).toBe(false);
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("foo");
    expect(text).toContain("bar");
    // 内文公式仍被识别（内文保留，不是整体丢弃）
    expect(pieces.some((p) => p.kind === "math")).toBe(true);
  });

  it("纯文本 + 公式回归不破", () => {
    const text1 = splitPieces("A. 苹果");
    expect(text1).toHaveLength(1);
    expect(text1[0]).toMatchObject({ kind: "text", value: "A. 苹果" });

    const text2 = splitPieces("速度 $v=at$ 时刻");
    const kinds2 = text2.map((p) => p.kind);
    expect(kinds2).toContain("math");
    expect(kinds2).toContain("text");

    // 多个表格共存
    const src =
      "<table><tr><td>a</td></tr></table>文本<table><tr><td>b</td></tr></table>";
    const pieces = splitPieces(src);
    expect(pieces.filter((p) => p.kind === "table")).toHaveLength(2);
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("文本");
  });

  it("Q8 pH 表 / Q9 盐桥表真实形态（含公式的表格）", () => {
    // 模拟 Q9 盐桥表：单元格含离子公式
    const src =
      '<table border="1"><tr><th>离子</th><th>浓度 / (mol·L⁻¹)</th></tr><tr><td>$ Fe^{3+} $</td><td>0.10</td></tr><tr><td>$ Fe^{2+} $</td><td>0.01</td></tr></table>';
    const pieces = splitPieces(src);
    expect(pieces).toHaveLength(1);
    const t = pieces[0];
    if (t.kind !== "table") throw new Error(`expected table, got ${t.kind}`);
    expect(t.rows).toHaveLength(3);
    // 表头
    expect(t.rows[0][0].header).toBe(true);
    // 数据行：含公式
    expect(t.rows[1][0].pieces.some((p) => p.kind === "math")).toBe(true);
    expect(t.rows[2][0].pieces.some((p) => p.kind === "math")).toBe(true);
    // 数值列纯文本
    const val = t.rows[1][1].pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(val).toBe("0.10");
  });
});

describe("imageRenderStyle — V3-IMG-OPTION-004 size collapse", () => {
  it("ignores percentage widths: auto + maxWidth 100% + aspect ratio", () => {
    const s = imageRenderStyle();
    expect(s.width).toBe("auto");
    expect(s.height).toBe("auto");
    expect(s.maxWidth).toBe("100%");
  });

  it("does not apply a percentage width (shrink-to-fit safe)", () => {
    const s = imageRenderStyle();
    expect(String(s.width)).not.toMatch(/^\d+(\.\d+)?%$/);
    expect(String(s.height)).not.toMatch(/^\d+(\.\d+)?%$/);
    // maxWidth % is the responsive cap — allowed and required
    expect(s.maxWidth).toBe("100%");
  });

  it("source width attr is captured in Piece but not applied as CSS %", () => {
    const pieces = splitHtmlSegments(
      '<img src="../../_imgs/p/i.jpg" width="12%" />',
    );
    const img = pieces.find((p) => p.kind === "img") as {
      kind: string;
      width: string | null;
    } | null;
    expect(img).not.toBeNull();
    expect(img!.width).toBe("12%"); // source fact preserved
    expect(imageRenderStyle().width).toBe("auto"); // not used as CSS
  });

  it("is stable across repeated calls (pure)", () => {
    expect(imageRenderStyle()).toEqual(imageRenderStyle());
  });
});
