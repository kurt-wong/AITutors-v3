/** MathText：`$...$` 行内公式渲染（KaTeX）。失败降级为原始文本，不整页崩溃。
 *  V3-IMG-OPTION-003：text 段中的 HTML 容器标签（`<div>`/`</div>`/`<p>`/`<br>`…）
 *  不作为字面文本显示；`<img>` 渲染为真实图片，src 经路径映射与安全校验。
 *  不使用 dangerouslySetInnerHTML 注入未净化 HTML。
 */

import katex from "katex";
import "katex/dist/katex.min.css";
import type { CSSProperties } from "react";
import { useMemo } from "react";
import {
  groupDuplicateTables,
  type TableGrid,
} from "../lib/tableGroups";

export type Piece =
  | { kind: "text"; value: string }
  | { kind: "math"; value: string; html: string | null }
  | { kind: "img"; src: string; alt: string; width: string | null }
  | { kind: "br" }
  | { kind: "table"; rows: TableCell[][]; caption: Piece[] | null };

/** 表格单元：内嵌 Piece（文本/公式/图片递归），保留对齐与合并信息。 */
export interface TableCell {
  pieces: Piece[];
  align: "left" | "center" | "right" | null;
  header: boolean;
  colspan: number;
}

/** Piece 列表 → 纯文本（重复表格签名用：文本/公式原文/图片 alt）。 */
export function piecesPlainText(pieces: Piece[]): string {
  return pieces
    .map((p) => {
      if (p.kind === "text") return p.value;
      if (p.kind === "math") return p.value;
      if (p.kind === "img") return p.alt || "";
      return "";
    })
    .join("");
}

/** 表格行 → 归一化网格（供 tableGroups 分组签名）。 */
export function tableGridOf(rows: TableCell[][]): TableGrid {
  return rows.map((row) => row.map((cell) => piecesPlainText(cell.pieces)));
}

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
  // 本轮新管线产物引用形态为 `imgs/<file>.jpg`（无 `_imgs/` 段）：
  // 同规则剥去 `imgs/`（仅路径段起点，避免误吞 `_imgs/` 内部）取 key。
  const norm = s.replace(/\\/g, "/");
  let idx = norm.indexOf("_imgs/");
  let token = "_imgs/";
  if (idx < 0) {
    const m = norm.match(/(^|\/)imgs\//);
    if (m) {
      // 新管线引用 `imgs/<file>` 本身即资源根下的 key(文件在 <root>/imgs/),
      // 不剥 `imgs/` 段,与 /api/images 的 key 语义一致。
      idx = m.index + m[1].length;
      token = "";
    }
  }
  if (idx < 0) return null;
  const key = norm.slice(idx + token.length);
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

// ---------------------------------------------------------------- table 解析
/**
 * R2X 表格渲染（白名单结构化渲染，非压平）：
 * 源文 `preprocessing/canonical_l1` 的题干表格是真 HTML 表
 * （`<table><tr><td style='text-align: center'>…`），承载矩阵关系
 * （如「运动 × 时段 × 时长」表），压平会丢列对应。按 table/tr/td(th) 白名单
 * 解析为真实表格结构；单元内容递归走 splitPieces（可含 $公式$/<img>）。
 */

/** 从 `<table` 开标签后扫描配对 `</table>`（容嵌套）。返回闭标签区间。 */
function findTableClose(
  src: string,
  from: number,
): { start: number; end: number } | null {
  const re = new RegExp(TAG_RE.source, "g");
  re.lastIndex = from;
  let depth = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(src)) !== null) {
    const name = (m[1] || "").toLowerCase();
    const closing = m[0].startsWith("</");
    const selfClose = (m[3] || "") === "/";
    if (name === "table" && !closing && !selfClose) {
      depth++;
    } else if (name === "table" && closing) {
      if (depth === 0) {
        return { start: m.index, end: m.index + m[0].length };
      }
      depth--;
    }
  }
  return null;
}

/** 解析 `<table>` 内层为行/单元格。caption 保留；thead/tbody 包裹标签忽略。 */
export function parseTableHtml(inner: string): {
  rows: TableCell[][];
  caption: Piece[] | null;
} {
  let caption: Piece[] | null = null;
  const capM = /<caption\b[^>]*>([\s\S]*?)<\/caption>/i.exec(inner);
  if (capM) caption = splitPieces(capM[1]);
  const rows: TableCell[][] = [];
  const rowRe = /<tr\b[^>]*>([\s\S]*?)<\/tr>/gi;
  let rm: RegExpExecArray | null;
  while ((rm = rowRe.exec(inner)) !== null) {
    const cells: TableCell[] = [];
    const cellRe = /<(td|th)\b([^>]*?)(\/?)>([\s\S]*?)<\/\1>/gi;
    let cm: RegExpExecArray | null;
    while ((cm = cellRe.exec(rm[1])) !== null) {
      const attrs = cm[2] || "";
      const alignM = /text-align\s*:\s*(left|center|right)/i.exec(attrs);
      const colM = /colspan\s*=\s*["']?(\d+)/i.exec(attrs);
      cells.push({
        pieces: splitPieces(cm[4] || ""),
        align: alignM
          ? (alignM[1].toLowerCase() as "left" | "center" | "right")
          : null,
        header: (cm[1] || "").toLowerCase() === "th",
        colspan: colM ? parseInt(colM[1], 10) : 1,
      });
    }
    if (cells.length) rows.push(cells);
  }
  return { rows, caption };
}

/**
 * 将一段纯文本按 HTML 标签切分。
 * 容器标签（div/p/span/…）被消耗不显示；`<img>` 变为图片；`<br>` 变为换行；
 * 其余未知标签同样被消耗（只丢标记、保留文字），不注入 HTML。
 */
export function splitHtmlSegments(value: string): Piece[] {
  const out: Piece[] = [];
  // OCR 导出伪影:img 标签属性收尾出现双引号(`alt="Image"" />`),会使
  // 标签正则失配而整段降级为文本。仅在 <img> 标签内归一 `""`→`"`,不动其余内容。
  const normValue = String(value ?? "").replace(
    /<img\b[^>]*>/gi,
    (tag) => tag.replace(/""/g, '"'),
  );
  const value2 = normValue;
  let last = 0;
  let m: RegExpExecArray | null;
  const re = new RegExp(TAG_RE.source, "g");
  while ((m = re.exec(value2)) !== null) {
    if (m.index > last) {
      pushTextPieces(out, value2.slice(last, m.index));
    }
    const tag = (m[1] || "").toLowerCase();
    const attrs = m[2] || "";
    // R2X 表格：成对 <table>…</table> 整块解析为结构化表格（保矩阵）。
    if (tag === "table" && !m[0].startsWith("</") && (m[3] || "") !== "/") {
      const close = findTableClose(value2, m.index + m[0].length);
      if (close) {
        out.push({
          kind: "table",
          ...parseTableHtml(value2.slice(m.index + m[0].length, close.start)),
        });
        last = close.end;
        re.lastIndex = close.end; // 跳过已消费的整块（避免块内标签二次切分）
        continue;
      }
      // 未闭合 <table>：只消费标签本身，内文保持文本（残片分类层显式暴露）
    }
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
  if (last < value2.length) {
    pushTextPieces(out, value2.slice(last));
  }
  return out;
}

/** 文本段的 $…$ 公式切分 + HTML 标签切分（不含表格整块提取）。 */
function splitTextPieces(src: string): Piece[] {
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

/**
 * 将一段文本切分为 Piece 列表。
 * 先扫描配对 <table>…</table> 整块（复用 findTableClose / parseTableHtml），
 * 块外文本再做 $…$ 公式切分——防止表格单元格内公式把 <table> 结构切碎。
 * parseTableHtml 单元格内递归调用本函数，可含公式/嵌套表格。
 */
export function splitPieces(src: string): Piece[] {
  const out: Piece[] = [];
  let last = 0;
  const re = new RegExp(TAG_RE.source, "g");
  let m: RegExpExecArray | null;
  while ((m = re.exec(src)) !== null) {
    const tag = (m[1] || "").toLowerCase();
    const closing = m[0].startsWith("</");
    const selfClose = (m[3] || "") === "/";
    if (tag === "table" && !closing && !selfClose) {
      // 表前文本
      if (m.index > last) {
        out.push(...splitTextPieces(src.slice(last, m.index)));
      }
      const close = findTableClose(src, m.index + m[0].length);
      if (close) {
        out.push({
          kind: "table",
          ...parseTableHtml(src.slice(m.index + m[0].length, close.start)),
        });
        last = close.end;
        re.lastIndex = close.end;
      } else {
        // 未闭合 <table>：只消费标签本身，内文留给后续文本管线（fail-visible）
        last = m.index + m[0].length;
      }
    }
  }
  if (last < src.length) {
    out.push(...splitTextPieces(src.slice(last)));
  }
  return out;
}

// ---------------------------------------------------------------- component

/** 单个 Piece 渲染（表格单元/标题内递归复用）。 */
function PieceView({ p }: { p: Piece }) {
  if (p.kind === "img") {
    // V3-IMG-OPTION-004: source width="N%" (paper-layout percentages)
    // collapses inside shrink-to-fit containers (15-18px). Render at
    // natural size, capped by container width; keep aspect ratio.
    return (
      <img
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
  if (p.kind === "br") return <br />;
  if (p.kind === "text") return <span>{p.value}</span>;
  if (p.kind === "table") {
    // R2X：白名单结构化渲染——保留行列矩阵（td 对齐/合并随源声明）。
    return (
      <table className="my-2 border-collapse text-[0.95em]">
        {p.caption && (
          <caption className="px-2 py-1 text-ink-muted">
            <Pieces items={p.caption} />
          </caption>
        )}
        <tbody>
          {p.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => {
                const Tag = cell.header ? "th" : "td";
                return (
                  <Tag
                    key={ci}
                    colSpan={cell.colspan > 1 ? cell.colspan : undefined}
                    className={`border border-gray-400 px-2 py-1 ${
                      cell.header ? "bg-canvas-parchment font-semibold" : ""
                    }`}
                    style={cell.align ? { textAlign: cell.align } : undefined}
                  >
                    <Pieces items={cell.pieces} />
                  </Tag>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  if (p.html == null) {
    // 渲染失败降级：原始片段 + 可理解提示，不影响整页
    return (
      <span
        title="公式渲染失败，已显示原始内容"
        className="rounded bg-amber-50 px-1 font-mono text-[0.95em] text-amber-800"
      >
        {p.value}
      </span>
    );
  }
  return (
    <span className="katex-inline" dangerouslySetInnerHTML={{ __html: p.html }} />
  );
}

function Pieces({ items }: { items: Piece[] }) {
  return (
    <>
      {items.map((p, i) => (
        <PieceView key={i} p={p} />
      ))}
    </>
  );
}

export function MathText({
  text,
  className,
  duplicateTables = "show",
}: {
  text: string;
  className?: string;
  /**
   * R2X 重复渲染表格（数据层 stem.extra_lines 缺陷）的展示策略：
   *  - "show"：如实全显（默认，兼容旧行为）
   *  - "annotate"：全显 + 重复片段标注（管理端）
   *  - "collapse"：重复片段折叠进可展开披露（学生端，避免干扰作答）
   * 只控可见性，不修改任何文本。
   */
  duplicateTables?: "show" | "annotate" | "collapse";
}) {
  const pieces = useMemo(() => splitPieces(text ?? ""), [text]);
  const dupMeta = useMemo(() => {
    if (duplicateTables === "show") return null;
    const idxMap: number[] = [];
    const grids: TableGrid[] = [];
    pieces.forEach((p, i) => {
      if (p.kind === "table") {
        idxMap.push(i);
        grids.push(tableGridOf(p.rows));
      }
    });
    const meta = new Map<number, "primary" | "duplicate">();
    for (const g of groupDuplicateTables(grids)) {
      meta.set(idxMap[g.primary], "primary");
      for (const d of g.duplicates) meta.set(idxMap[d], "duplicate");
    }
    return meta;
  }, [pieces, duplicateTables]);
  // 根元素 div：语义化合法嵌套 <table>（span 内放 table 不合法）。
  return (
    <div className={className}>
      {pieces.map((p, i) => {
        const role = dupMeta?.get(i);
        if (p.kind === "table" && role === "duplicate") {
          if (duplicateTables === "collapse") {
            return (
              <details
                key={i}
                className="my-2 rounded border border-dashed border-amber-300 bg-amber-50/40 px-2 py-1"
              >
                <summary className="cursor-pointer text-[12px] text-amber-800">
                  重复渲染表格（内容与本题另一表格重复，源数据缺陷）— 展开查看
                </summary>
                <div className="mt-2">
                  <PieceView p={p} />
                </div>
              </details>
            );
          }
          return (
            <div key={i} className="my-2">
              <div className="mb-1 rounded bg-amber-50 px-2 py-0.5 text-[11px] text-amber-800">
                重复渲染表格（内容与本题另一表格重复，源数据缺陷）— 如实显示
              </div>
              <PieceView p={p} />
            </div>
          );
        }
        return <PieceView key={i} p={p} />;
      })}
    </div>
  );
}
