/**
 * V3-IMG-OPTION-003 — MathText HTML container tags + image URL mapping + security.
 */
import { describe, expect, it } from "vitest";
import {
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
    const pieces = splitHtmlSegments("<table><tr><td>foo</td></tr></table>");
    const text = pieces.map((p) => (p.kind === "text" ? p.value : "")).join("");
    expect(text).toContain("foo");
    expect(text).not.toMatch(/<\/?(table|tr|td)/i);
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
