/** questionGroups（VIS-INSPECT-V1）：复合题真实层级分组 + 残片/图片检出。
 *
 * label 形态（来自 admission.py 聚合，已对真实库核验）：
 *   - 子题 stem：label=null，文本以「21. 」开头
 *   - 子题选项：label="21A"…"21D"；共享选项 label="PA"…（父级共享）
 *   - 子题答案：label="21"；单题答案 label=null/字母
 *   - material / explanation：label=null，组级共享
 */

export interface RoleContentLike {
  id?: string;
  role: string;
  label?: string | null;
  role_index: number;
  text: string | null | undefined;
  answer_status?: Record<string, unknown> | null;
}

export interface SubQuestionGroup {
  key: string; // "21" | ""（单题）
  title: string;
  /** 组内全部题干（单题多 stem / 未归组残留不丢弃） */
  stems: RoleContentLike[];
  options: RoleContentLike[];
  answers: RoleContentLike[];
}

export interface QuestionGroups {
  materials: RoleContentLike[];
  explanations: RoleContentLike[];
  sharedOptions: RoleContentLike[];
  displayNotes: RoleContentLike[];
  subs: SubQuestionGroup[];
}

const SUB_KEY_RE = /^(\d+)$/;
const OPTION_SUB_RE = /^(\d+)([A-Za-z])$/;
const OPTION_SHARED_RE = /^P([A-Za-z])$/i;
/** 文本启发式：N. / N． / N、 / （N） / (N) / （N）． 等形态。 */
const STEM_LEAD_RE = /^(?:（(\d+)）[.．、]?|\((\d+)\)[.．、]?|(\d+)\s*\\?\s*[.．、])/;

function stemSubKey(s: RoleContentLike): string | null {
  // 优先用行自己的数字 label（子问 label='1'..'6' 直接作 sub key）
  const labelM = SUB_KEY_RE.exec(String(s.label ?? "").trim());
  if (labelM) return labelM[1];
  // 退回文本启发式
  const m = STEM_LEAD_RE.exec(String(s.text ?? "").trim());
  return m ? (m[1] ?? m[2] ?? m[3]) : null;
}

export function groupQuestionContents(contents: RoleContentLike[]): QuestionGroups {
  const materials = contents.filter((c) => c.role === "material");
  const explanations = contents.filter((c) => c.role === "explanation");
  const displayNotes = contents.filter((c) => c.role === "display_note");
  const stems = contents.filter((c) => c.role === "stem");
  const options = contents.filter((c) => c.role === "option");
  const answers = contents.filter((c) => c.role === "answer");

  const sharedOptions = options.filter((o) => OPTION_SHARED_RE.test(String(o.label ?? "")));

  // 子题键：选项 label 前缀（21A→21）∪ 数字 answer label（21）。
  // stem 文本开头的数字只用于「归组」，不创建键——数学单题题干也以「1. 」开头。
  const keys = new Set<string>();
  for (const a of answers) {
    const k = String(a.label ?? "").trim();
    if (SUB_KEY_RE.test(k)) keys.add(k);
  }
  for (const o of options) {
    const m = OPTION_SUB_RE.exec(String(o.label ?? "").trim());
    if (m) keys.add(m[1]);
  }

  const subs: SubQuestionGroup[] = [];
  if (keys.size === 0) {
    // 单题：全部平铺进一个组
    subs.push({
      key: "",
      title: "题目",
      stems,
      options: options.filter((o) => !OPTION_SHARED_RE.test(String(o.label ?? ""))),
      answers,
    });
  } else {
    const ordered = [...keys].sort((a, b) => Number(a) - Number(b));
    // 先分配子问组，收集被认领的行
    const claimedStems = new Set<RoleContentLike>();
    const subGroups: SubQuestionGroup[] = [];
    for (const k of ordered) {
      const myStems = stems.filter((s) => stemSubKey(s) === k);
      myStems.forEach((s) => claimedStems.add(s));
      subGroups.push({
        key: k,
        title: `子问题 ${k}`,
        stems: myStems,
        options: options.filter((o) => {
          const m = OPTION_SUB_RE.exec(String(o.label ?? "").trim());
          return m && m[1] === k;
        }),
        answers: answers.filter((a) => String(a.label ?? "").trim() === k),
      });
    }

    // 父级 stem（label=null 且不被子问认领）→ 「题目」主组，渲染在子问组之上
    const parentStems = stems.filter((s) => !claimedStems.has(s) && s.label == null);
    if (parentStems.length > 0) {
      subs.push({
        key: "",
        title: "题目",
        stems: parentStems,
        options: [],
        answers: [],
      });
    }
    subs.push(...subGroups);

    // 仍无主的选项/答案及非 null-label 残留 stem（异常）：不静默丢弃，挂到「其他内容」
    const usedOpts = new Set(subGroups.flatMap((s) => s.options));
    const usedAns = new Set(subGroups.flatMap((s) => s.answers));
    const orphanStems = stems.filter((s) => !claimedStems.has(s) && s.label != null);
    const orphan = {
      stems: orphanStems,
      options: options.filter(
        (o) =>
          !usedOpts.has(o) && !OPTION_SHARED_RE.test(String(o.label ?? "")),
      ),
      answers: answers.filter((a) => !usedAns.has(a)),
    };
    if (orphan.stems.length || orphan.options.length || orphan.answers.length) {
      subs.push({
        key: "_orphan",
        title: "其他内容",
        stems: orphan.stems,
        options: orphan.options,
        answers: orphan.answers,
      });
    }
  }

  return { materials, explanations, sharedOptions, displayNotes, subs };
}

// ---------------------------------------------------------------- 题号剥离
// 入库题干文本自带前导题号（"1. " / "21．" / "3、"），与页面题号栏重复。
// 展示层剥离前导题号（只剥一次、只剥开头）；原始文本仍存库里，原始文本开关可见。
const STEM_NUM_RE = /^\s*\d+\s*\\?\s*[.．、]\s*/;

export function stripStemNumber(text: string): string {
  return String(text ?? "").replace(STEM_NUM_RE, "");
}

// ---------------------------------------------------------------- HTML 残片检出
// MathText 渲染时会「消隐」容器类 HTML 标签（div/p/span…），`</div>` 等残片
// 在默认视图不可见。本检出把消隐标签显式列成异常，供 R2X-04 类缺陷直观察看。
// R2X 表格分类：成对 <table>…</table> 块内的 table/tr/td(th) 是**合法结构**
// （已结构化渲染），单独计数披露、不计入残片；块外的表格家族标签（孤残
// `</td>` 等）仍算残片——分类不洗零：结构标签不消失，只是不冒充缺陷。
const RENDERED_TAGS = new Set(["img", "br", "hr"]);
const TABLE_FAMILY_TAGS = new Set([
  "table",
  "thead",
  "tbody",
  "tfoot",
  "tr",
  "td",
  "th",
  "caption",
  "colgroup",
  "col",
]);
const TAG_SCAN_RE = /<\/?([a-zA-Z][a-zA-Z0-9]*)((?:[^>"']|"[^"]*"|'[^']*')*?)(\/?)>/g;

/** 成对 <table> 块区间（容嵌套）；块外表格标签视为孤残。 */
function tableBlockRanges(src: string): Array<[number, number]> {
  const ranges: Array<[number, number]> = [];
  const re = new RegExp(TAG_SCAN_RE.source, "g");
  let depth = 0;
  let start = -1;
  let m: RegExpExecArray | null;
  while ((m = re.exec(src)) !== null) {
    const name = (m[1] || "").toLowerCase();
    const closing = m[0].startsWith("</");
    const selfClose = (m[3] || "") === "/";
    if (name === "table" && !closing && !selfClose) {
      if (depth === 0) start = m.index;
      depth++;
    } else if (name === "table" && closing) {
      depth--;
      if (depth === 0 && start >= 0) {
        ranges.push([start, m.index + m[0].length]);
        start = -1;
      } else if (depth < 0) {
        depth = 0;
      }
    }
  }
  return ranges;
}

export interface HtmlResidue {
  role: string;
  label: string | null;
  tag: string;
  raw: string;
  text_excerpt: string;
}

/** 表格结构标签（成对 table 块内，已结构化渲染）。分类披露用，非缺陷。 */
export interface HtmlStructure {
  role: string;
  label: string | null;
  tag: string;
  raw: string;
}

function scanHtml(contents: RoleContentLike[]): {
  residues: HtmlResidue[];
  structures: HtmlStructure[];
} {
  const residues: HtmlResidue[] = [];
  const structures: HtmlStructure[] = [];
  for (const c of contents) {
    const src = String(c.text ?? "");
    const blocks = tableBlockRanges(src);
    const inBlock = (idx: number) => blocks.some(([a, b]) => idx >= a && idx < b);
    const re = new RegExp(TAG_SCAN_RE.source, "g");
    let m: RegExpExecArray | null;
    while ((m = re.exec(src)) !== null) {
      const tag = (m[1] || "").toLowerCase();
      if (RENDERED_TAGS.has(tag)) continue;
      if (TABLE_FAMILY_TAGS.has(tag) && inBlock(m.index)) {
        structures.push({ role: c.role, label: c.label ?? null, tag, raw: m[0] });
        continue;
      }
      residues.push({
        role: c.role,
        label: c.label ?? null,
        tag,
        raw: m[0],
        text_excerpt: src.slice(Math.max(0, m.index - 12), m.index + m[0].length + 12),
      });
    }
  }
  return { residues, structures };
}

export function findHtmlResidue(contents: RoleContentLike[]): HtmlResidue[] {
  return scanHtml(contents).residues;
}

export function findHtmlStructures(contents: RoleContentLike[]): HtmlStructure[] {
  return scanHtml(contents).structures;
}

// ---------------------------------------------------------------- 图片引用检出
export interface ImageRef {
  role: string;
  label: string | null;
  src: string;
  /** 映射后的前端 URL（/api/images/…）；无法安全映射时为 null */
  url: string | null;
}

const IMG_SCAN_RE = /<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi;

export function extractImageRefs(
  contents: RoleContentLike[],
  resolveSrc: (raw: string) => string | null,
): ImageRef[] {
  const out: ImageRef[] = [];
  for (const c of contents) {
    const src = String(c.text ?? "");
    const re = new RegExp(IMG_SCAN_RE.source, "gi");
    let m: RegExpExecArray | null;
    while ((m = re.exec(src)) !== null) {
      const raw = m[1];
      out.push({
        role: c.role,
        label: c.label ?? null,
        src: raw,
        url: resolveSrc(raw),
      });
    }
  }
  return out;
}
