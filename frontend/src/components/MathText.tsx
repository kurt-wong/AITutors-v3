/** MathText：`$...$` 行内公式渲染（KaTeX）。失败降级为原始文本，不整页崩溃。
 *  V3-IMG-OPTION-003：text 段中的 HTML 容器标签（`<div>`/`</div>`/`<p>`/`<br>`…）
 *  不作为字面文本显示；`<img>` 渲染为真实图片，src 经路径映射与安全校验。
 *  不使用 dangerouslySetInnerHTML 注入未净化 HTML。
 */

import katex from "katex";
import "katex/dist/katex.min.css";
import type { CSSProperties } from "react";
import { useMemo } from "react";

export type Piece =
  | { kind: "text"; value: string }
  | { kind: "math"; value: string; html: string | null }
  | { kind: "img"; src: string; alt: string; width: string | null }
  | { kind: "br" };

/** 匹配 `$...$`（允许两侧空格）；不支持 `$$...$$` 块级（本库数据未出现）。 */
const MATH_RE = /\$\s*([^$]+?)\s*\$/g;

/** 任意 HTML 标签：开标签、闭标签、自闭合。用于切分文本段。 */
const TAG_RE = /<\/?([a-zA-Z][a-zA-Z0-9]*)((?:[^>"']|"[^"]*"|'[^']*')*?)(\/?)>/g;

const IMG_SRC_RE = /\bsrc\s*=\s*["']([^"']+)["']/i;
const IMG_ALT_RE = /\balt\s*=\s*["']([^"']*)["']/i;
const IMG_WIDTH_RE = /\bwidth\s*=\s*["']([^"']+)["']/i;

/** 语义化换行标签。 */
const BR_TAGS = new Set(["br", "hr"]);

/**
 * 图片渲染尺寸策略（V3-IMG-OPTION-004）。
 *
 * 源文 `width="N%"` 是纸面版式百分比，放进 shrink-to-fit 容器会塌缩成十几像素。
 * 统一改为自然尺寸 + 容器宽度上限 + 原始宽高比，窄视口下自适应。
 */
export function imageRenderStyle(): CSSProperties {
  return { width: "auto", height: "auto", maxWidth: "100%" };
}

// ---------------------------------------------------------------- image src
/**
 * 将源文相对图片引用映射为前端可访问 URL，并做安全校验。
 *
 * 输入示例：`../../_imgs/<paper>/img_xxx.jpg` → `/api/images/<paper>/img_xxx.jpg`
 * 安全策略：
 *   - 拒绝协议相对 URL（`//host/path`）
 *   - 拒绝 `javascript:` / `data:` / `vbscript:`
 *   - 拒绝路径穿越（`..` 段在规范化后不得逃出 images 根）
 *   - 仅放行已知图片扩展名
 *   - 已是 `/api/images/...` 的 URL 直接放行（同源相对路径）
 */
const IMG_EXT_RE = /\.(jpe?g|png|gif|webp|svg|bmp|avif)$/i;

export function resolveImageSrc(raw: string): string | null {
  const s = raw.trim();
  if (!s) return null;
  // protocol-relative (`//evil.com/x`) — must not be treated as a plain path
  if (s.startsWith("//")) return null;
  if (/^(javascript|data|vbscript|file|about):/i.test(s)) return null;

  // already-mapped API URL
  if (s.startsWith("/api/images/")) {
    return safeImagesPath(s.slice("/api/images/".length)) ? s : null;
  }

  // absolute http(s): only same-origin and already on /api/images/
  if (/^https?:\/\//i.test(s)) {
    try {
      const u = new URL(s);
      if (u.origin !== window.location.origin) return null;
      if (!u.pathname.startsWith("/api/images/")) return null;
      return safeImagesPath(u.pathname.slice("/api/images/".length)) ? s : null;
    } catch {
      return null;
    }
  }

  // source-relative refs like `../../_imgs/<paper>/img_xxx.jpg`
  // extract the segment after `_imgs/` — that is the resource key under the
  // images root. No raw `..` is ever forwarded to the server.
  const idx = s.replace(/\\/g, "/").indexOf("_imgs/");
  if (idx < 0) return null;
  const key = s.replace(/\\/g, "/").slice(idx + "_imgs/".length);
  return safeImagesPath(key) ? `/api/images/${key}` : null;
}

/** 校验资源 key：无穿越、无绝对盘符、限图片扩展名。 */
function safeImagesPath(key: string): boolean {
  const k = key.replace(/\\/g, "/").replace(/^\/+/, "");
  if (!k) return false;
  if (k.includes("\0")) return false;
  // reject any `..` segment (path traversal)
  const segs = k.split("/");
  if (segs.some((seg) => seg === ".." || seg === ".")) return false;
  // reject Windows drive or UNC
  if (/^[a-zA-Z]:/.test(k) || k.startsWith("//")) return false;
  return IMG_EXT_RE.test(k);
}

// ---------------------------------------------------------------- segmentation

function pushTextPieces(out: Piece[], value: string) {
  if (value) out.push({ kind: "text", value });
}

/**
 * 将一段纯文本按 HTML 标签切分。
 * 容器标签（div/p/span/…）被消耗不显示；`<img>` 变为图片；`<br>` 变为换行；
 * 其余未知标签同样被消耗（只丢标记、保留文字），不注入 HTML。
 */
export function splitHtmlSegments(value: string): Piece[] {
  const out: Piece[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  const re = new RegExp(TAG_RE.source, "g");
  while ((m = re.exec(value)) !== null) {
    if (m.index > last) {
      pushTextPieces(out, value.slice(last, m.index));
    }
    const tag = (m[1] || "").toLowerCase();
    const attrs = m[2] || "";
    if (tag === "img") {
      const srcM = IMG_SRC_RE.exec(attrs);
      const src = srcM ? resolveImageSrc(srcM[1]) : null;
      if (src) {
        const altM = IMG_ALT_RE.exec(attrs);
        const widthM = IMG_WIDTH_RE.exec(attrs);
        out.push({
          kind: "img",
          src,
          alt: altM ? altM[1] : "",
          width: widthM ? widthM[1] : null,
        });
      } else {
        // unsafe / unmappable src — show raw tag as text (fail-closed, no drop)
        pushTextPieces(out, m[0]);
      }
    } else if (BR_TAGS.has(tag)) {
      out.push({ kind: "br" });
    }
    // other tags (div/p/span/… and unknown): consume the tag itself only
    last = m.index + m[0].length;
  }
  if (last < value.length) {
    pushTextPieces(out, value.slice(last));
  }
  return out;
}

export function splitPieces(src: string): Piece[] {
  const out: Piece[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  const re = new RegExp(MATH_RE.source, "g");
  while ((m = re.exec(src)) !== null) {
    if (m.index > last) {
      out.push(...splitHtmlSegments(src.slice(last, m.index)));
    }
    const raw = m[1];
    let html: string | null = null;
    try {
      html = katex.renderToString(raw, {
        throwOnError: true,
        displayMode: false,
        output: "html",
      });
    } catch {
      html = null;
    }
    out.push({ kind: "math", value: m[0], html });
    last = m.index + m[0].length;
  }
  if (last < src.length) {
    out.push(...splitHtmlSegments(src.slice(last)));
  }
  return out;
}

// ---------------------------------------------------------------- component

export function MathText({
  text,
  className,
}: {
  text: string;
  className?: string;
}) {
  const pieces = useMemo(() => splitPieces(text ?? ""), [text]);
  return (
    <span className={className}>
      {pieces.map((p, i) => {
        if (p.kind === "img") {
          // V3-IMG-OPTION-004: source width="N%" (paper-layout percentages)
          // collapses inside shrink-to-fit containers (15-18px). Render at
          // natural size, capped by container width; keep aspect ratio.
          return (
            <img
              key={i}
              src={p.src}
              alt={p.alt}
              style={imageRenderStyle()}
              className="inline-block align-middle my-1"
              onError={(e) => {
                // visible broken-image state, never silent swap
                const el = e.currentTarget;
                el.style.outline = "1px dashed #d97706";
                el.title = `图片加载失败: ${p.src}`;
                el.alt = `图片加载失败: ${p.alt || p.src}`;
              }}
            />
          );
        }
        if (p.kind === "br") return <br key={i} />;
        if (p.kind === "text") return <span key={i}>{p.value}</span>;
        if (p.html == null) {
          // 渲染失败降级：原始片段 + 可理解提示，不影响整页
          return (
            <span
              key={i}
              title="公式渲染失败，已显示原始内容"
              className="rounded bg-amber-50 px-1 font-mono text-[0.95em] text-amber-800"
            >
              {p.value}
            </span>
          );
        }
        return (
          <span
            key={i}
            className="katex-inline"
            dangerouslySetInnerHTML={{ __html: p.html }}
          />
        );
      })}
    </span>
  );
}
