# -*- coding: utf-8 -*-
"""CORE-DELIVERY-04-A：short_answer 复合题确定性导入适配（最小实现）。

职责（Owner 04-A 任务书）：已审核 Preprocessing 产物 → 确定性结构转换 →
现有 Question/Instance/BindingFact/Admission 可消费的冻结 candidate payload。

原则：
- 只做确定性消费、映射、校验和必要的结构转换；
- 不重新 OCR、不重新猜题、不重新猜答案归属；任一结构计数不齐 → fail-loud；
- 不拆分复合题为多个 Question（一个 unit = 一个父 Question，子问为内部有序行）；
- 答案归属走 derive_binding_fact（唯一生产者），发布门槛走 _publish_decision。

确定性子问分解规则（零猜测）：
  S1 子问题干  = questions_lines 内以（N）/(N) 入口开头的行（剔除 material_lines 行）
  S2 空位      = 子问题干内 ``_{2,}`` 计数（空位序 = 全文档顺序）
  S3 答案段    = answer_evidence.value 按（N）入口切段（与 seg_cmp 同口径）
  S4 空位序映射 = 全文第 k 个空位 ↔ 第 k 个答案段（R1C-R2 已复核规则）；
                子问答案 = 其空位对应各段按序合并
  S5 解析段    = explanation_lines 内（N）入口段落 → 同号子问；
                【分析】/【点睛】 = 组级（父级共享）
  S6 任一计数不齐（子问数/空位数/答案段数/解析段数）→ 展开失败并给出原因，
                绝不猜测补齐
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

# ── 入口 token（（N）/ (N)，可带 . 、 ：）────────────────────────────
_ENTRY_RE = re.compile(r"[(（]\s*(\d{1,3})\s*[)）]\s*[\.、．：:]?")
# 行首子问入口：`（1）…` / `(1)…`
_LINE_SUB_RE = re.compile(r"^\s*[(（]\s*(\d{1,3})\s*[)）]")
# 空位：连续下划线（Q8/Q9 样本为 `___`；不认 $\\underline$ 形态——样本不涉及）
_BLANK_RE = re.compile(r"_{2,}")
# 解析区组级标记
_GROUP_MARKERS = ("【分析】", "【点睛】", "【解析】", "【详解】")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_entry_segments(text: str) -> dict[int, str]:
    """（N）入口切段 → {N: 段原文}。与 r1c_r31b_seg_cmp 同口径（入口含可选点号）。"""
    if not text:
        return {}
    ms = list(_ENTRY_RE.finditer(text))
    out: dict[int, str] = {}
    for i, m in enumerate(ms):
        n = int(m.group(1))
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        seg = text[m.end():end].strip()
        if n in out:
            raise ValueError(f"duplicate entry token ({n}) in text")
        out[n] = seg
    return out


def count_blanks(text: str) -> int:
    return len(_BLANK_RE.findall(text))


@dataclass
class SubQuestionRow:
    """一个子问的确定性映射结果（payload-ready）。"""
    sub_number: int
    stem_start: int
    stem_end: int
    stem_text: str
    blank_count: int
    answer_segment_numbers: list[int]
    answer_text: str
    answer_entry_lines: list[int]
    explanation_start: int | None
    explanation_end: int | None
    explanation_text: str


@dataclass
class CompositeExpandResult:
    unit_id: str
    subs: list[SubQuestionRow] = field(default_factory=list)
    group_explanation: str = ""
    group_explanation_lines: list[int] = field(default_factory=list)
    # B1：父级共享上下文（题头+指导语）= questions 行区剔除 material 行与
    # 子问区间后的确定性切片（原样保留行内容，不做识别/改写）。
    parent_context_lines: list[int] = field(default_factory=list)
    parent_stem_text: str = ""
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues and bool(self.subs)


def _slice(src: list[str], lo: int, hi: int) -> str:
    return "\n".join(src[lo - 1:hi])


def expand_short_answer_composite(
    source_lines: list[str],
    *,
    unit_id: str,
    questions_range: tuple[int, int],
    material_range: tuple[int, int] | None,
    answer_value: str,
    answer_range: tuple[int, int],
    explanation_range: tuple[int, int] | None,
) -> CompositeExpandResult:
    """S1–S6 确定性展开。任何不齐 → issues 非空且 subs 为空（fail-loud）。"""
    res = CompositeExpandResult(unit_id=unit_id)
    q_lo, q_hi = questions_range
    mat_excl: set[int] = set()
    if material_range:
        mat_excl = set(range(material_range[0], material_range[1] + 1))

    # S1 子问题干行
    sub_lines: list[tuple[int, int]] = []  # (sub_number, line_no)
    for ln in range(q_lo, q_hi + 1):
        if ln in mat_excl:
            continue
        m = _LINE_SUB_RE.match(source_lines[ln - 1])
        if m:
            n = int(m.group(1))
            if sub_lines and n != sub_lines[-1][0] + 1:
                res.issues.append(
                    f"sub entry numbering not sequential at line {ln}: "
                    f"got {n} after {sub_lines[-1][0]}"
                )
            sub_lines.append((n, ln))
    if not sub_lines:
        res.issues.append("no (N) sub-question entries in questions region")
        return res

    # 子问行区间：从入口行到下一入口行前（跳过空行后的行）
    bounds: list[tuple[int, int, int]] = []  # (n, start, end)
    for i, (n, ln) in enumerate(sub_lines):
        end = (sub_lines[i + 1][1] - 1) if i + 1 < len(sub_lines) else q_hi
        # 收紧尾部空行
        while end > ln and not source_lines[end - 1].strip():
            end -= 1
        bounds.append((n, ln, end))

    # B1 父级共享上下文：questions 行区 − material 行 − 子问区间（确定性切片）
    sub_excl: set[int] = set()
    for _n, lo, hi in bounds:
        sub_excl.update(range(lo, hi + 1))
    keep = [ln for ln in range(q_lo, q_hi + 1)
            if ln not in mat_excl and ln not in sub_excl]
    while keep and not source_lines[keep[0] - 1].strip():
        keep.pop(0)
    while keep and not source_lines[keep[-1] - 1].strip():
        keep.pop()
    res.parent_context_lines = keep
    res.parent_stem_text = "\n".join(source_lines[ln - 1] for ln in keep).strip()

    # S3 答案段
    try:
        segs = split_entry_segments(answer_value)
    except ValueError as exc:
        res.issues.append(f"answer segment split failed: {exc}")
        return res
    if not segs:
        res.issues.append("answer_evidence.value has no (N) segments")
        return res

    # S2 空位 + S4 空位序映射
    total_blanks = 0
    per_sub_blanks: list[int] = []
    for n, lo, hi in bounds:
        b = count_blanks(_slice(source_lines, lo, hi))
        per_sub_blanks.append(b)
        total_blanks += b
    if total_blanks != len(segs):
        res.issues.append(
            f"blank/segment count mismatch: blanks={total_blanks} "
            f"segments={len(segs)} (expected equal under S4)"
        )
        return res

    # 答案段落行（用于 fact 溯源）：段 N 的入口所在行 ∈ answer_range
    seg_entry_line: dict[int, int] = {}
    for ln in range(answer_range[0], answer_range[1] + 1):
        for m in _ENTRY_RE.finditer(source_lines[ln - 1]):
            n = int(m.group(1))
            if n not in seg_entry_line:
                seg_entry_line[n] = ln
    missing = [n for n in segs if n not in seg_entry_line]
    if missing:
        res.issues.append(
            f"answer segments {missing} not located within answer_range {answer_range}"
        )
        return res

    # S5 解析段
    expl_segs: dict[int, str] = {}
    expl_seg_range: dict[int, tuple[int, int]] = {}
    group_lines: list[int] = []
    group_parts: list[str] = []
    if explanation_range:
        e_lo, e_hi = explanation_range
        cur_n: int | None = None
        cur_start = 0
        cur_buf: list[str] = []
        # 04-C-R3（04-A/04-B 修订单）：【分析】/【点睛】是**组级节**——节内
        # 全部内容归父级公共，即使行文呈 (N) 形式（Q9【分析】正文三条曾被
        # 当作子问段入口后遭【详解】同号段覆盖丢失；含「第(2)题」的【点睛】
        # 行曾被并入子问段）。【详解】标志退出组级节，(N) 入口恢复子问语义。
        in_group_section = False
        for ln in range(e_lo, e_hi + 1):
            raw = source_lines[ln - 1]
            hits = list(_ENTRY_RE.finditer(raw))
            has_group_marker = ("【分析】" in raw) or ("【点睛】" in raw)
            has_detail_marker = "【详解】" in raw
            if has_group_marker and not has_detail_marker:
                if cur_n is not None:
                    expl_segs[cur_n] = "\n".join(cur_buf).strip()
                    expl_seg_range[cur_n] = (cur_start, ln - 1)
                    cur_n, cur_buf = None, []
                in_group_section = True
                group_lines.append(ln)
                group_parts.append(raw)
                continue
            if has_detail_marker:
                in_group_section = False
            if in_group_section:
                if cur_n is not None:
                    expl_segs[cur_n] = "\n".join(cur_buf).strip()
                    expl_seg_range[cur_n] = (cur_start, ln - 1)
                    cur_n, cur_buf = None, []
                group_lines.append(ln)
                group_parts.append(raw)
                continue
            if hits and not has_group_marker:
                n = int(hits[0].group(1))
                if cur_n is not None:
                    expl_segs[cur_n] = "\n".join(cur_buf).strip()
                    expl_seg_range[cur_n] = (cur_start, ln - 1)
                cur_n = n
                cur_start = ln
                # 行内入口后的内容归入本段；行首【详解】等标记保留在文本
                cur_buf = [raw]
                continue
            if cur_n is not None:
                cur_buf.append(raw)
            else:
                group_lines.append(ln)
                group_parts.append(raw)
        if cur_n is not None:
            expl_segs[cur_n] = "\n".join(cur_buf).strip()
            expl_seg_range[cur_n] = (cur_start, e_hi)
    res.group_explanation = "\n".join(group_parts).strip()
    res.group_explanation_lines = group_lines

    expected_subs = [n for n, _ in sub_lines]
    if sorted(expl_segs) != expected_subs:
        res.issues.append(
            f"explanation segments {sorted(expl_segs)} != sub numbers {expected_subs}"
        )
        return res

    # 组装子问行（S4：全局空位序）
    k = 0
    for i, (n, lo, hi) in enumerate(bounds):
        seg_nos = list(range(k + 1, k + per_sub_blanks[i] + 1))
        k += per_sub_blanks[i]
        ans_text = " ".join(segs[s] for s in seg_nos)
        e_lo, e_hi = expl_seg_range[n]
        res.subs.append(SubQuestionRow(
            sub_number=n,
            stem_start=lo,
            stem_end=hi,
            stem_text=_slice(source_lines, lo, hi),
            blank_count=per_sub_blanks[i],
            answer_segment_numbers=seg_nos,
            answer_text=ans_text,
            answer_entry_lines=sorted({seg_entry_line[s] for s in seg_nos}),
            explanation_start=e_lo,
            explanation_end=e_hi,
            explanation_text=expl_segs[n],
        ))
    return res


# ══════════════════════════════════════════════════════════════════
# 适配输出：冻结 candidate.payload 形状（_materialize 可消费）
# ══════════════════════════════════════════════════════════════════


def _refs(lo: int, hi: int) -> list[str]:
    return [f"P1L{n:03d}" for n in range(lo, hi + 1)]


def build_adapter_unit_payload(
    unit: dict,
    source_lines: list[str],
    *,
    display_annotations: list[dict] | None = None,
    image_assets: list[dict] | None = None,
) -> dict:
    """单 unit（复合 short_answer）→ 适配输出条目（确定性）。

    返回 {
      "unit_id", "ok", "issues",
      "ir_unit": {…unit_type=composite_unit, sub_questions[]},
      "compiled_roles": [...], "answer": [...], "resolved_spans": [...],
      "figure_links": [...],
    }
    子问 roles 命名：stem/answer/explanation 行 label=str(子问号)，
    与 _aggregate_composite_roles「每子题答案独立 role 行 label=题号」一致。
    """
    uid = str(unit.get("unit_id"))
    issues: list[str] = []

    def span(span_id: str, lo: int, hi: int, text: str) -> dict:
        return {
            "span_id": span_id,
            "line_refs": _refs(lo, hi),
            "text_hash": _sha256_text(text),
            "unit_id": uid,
        }

    q_rng = unit.get("questions_lines")
    a_rng = unit.get("answer_lines")
    e_rng = unit.get("explanation_lines")
    m_rng = unit.get("material_lines")
    ae = unit.get("answer_evidence") or {}
    val = ae.get("value")
    if not q_rng or not a_rng or val is None:
        return {"unit_id": uid, "ok": False,
                "issues": ["missing questions/answer range or answer_evidence.value"]}

    exp = expand_short_answer_composite(
        source_lines,
        unit_id=uid,
        questions_range=(int(q_rng[0]), int(q_rng[1])),
        material_range=(int(m_rng[0]), int(m_rng[1])) if m_rng else None,
        answer_value=str(val),
        answer_range=(int(a_rng[0]), int(a_rng[1])),
        explanation_range=(int(e_rng[0]), int(e_rng[1])) if e_rng else None,
    )
    issues.extend(exp.issues)
    if not exp.ok:
        return {"unit_id": uid, "ok": False, "issues": issues}

    compiled: list[dict] = []
    answers: list[dict] = []
    spans: dict[str, dict] = {}
    sub_payloads: list[dict] = []

    def add_role(role: str, label: str | None, text: str, lo: int, hi: int,
                 unit_id: str, span_id: str,
                 line_refs: list[str] | None = None) -> None:
        # 生产契约（admission.py:1079-1081）：compiled role 行自身携带
        # line_refs，_materialize 直接用该行构建 source_span（非 answer 行
        # 不回查 resolved_spans）——缺失即持久化丢行号。
        refs = line_refs if line_refs is not None else _refs(lo, hi)
        compiled.append({
            "kind": "content", "role": role, "unit_id": unit_id,
            "label": label, "text": text, "text_hash": _sha256_text(text),
            "span_id": span_id, "line_refs": refs,
        })
        spans[span_id] = {
            "span_id": span_id, "line_refs": refs,
            "text_hash": _sha256_text(text), "unit_id": uid,
        }

    # 公共材料（一次）
    if m_rng:
        lo, hi = int(m_rng[0]), int(m_rng[1])
        mat_text = _slice(source_lines, lo, hi)
        sid = f"imp:{uid}:material"
        compiled.append({
            "kind": "material", "role": "material", "unit_id": uid,
            "label": None, "text": mat_text, "text_hash": _sha256_text(mat_text),
            "span_id": sid, "line_refs": _refs(lo, hi),
        })
        spans[sid] = span(sid, lo, hi, mat_text)

    # B1 父级共享 stem（题头+指导语）：恰一条，unit 归属父级；子问 stem 不充当父级
    if exp.parent_context_lines:
        p_refs = [f"P1L{n:03d}" for n in exp.parent_context_lines]
        sid = f"imp:{uid}:stem.parent"
        compiled.append({
            "kind": "content", "role": "stem", "unit_id": uid,
            "label": None, "text": exp.parent_stem_text,
            "text_hash": _sha256_text(exp.parent_stem_text),
            "span_id": sid,
            # 非连续区间如实逐行记录（dry-run noncontiguous_region 同口径）
            "line_refs": p_refs,
        })
        spans[sid] = {
            "span_id": sid, "line_refs": p_refs,
            "text_hash": _sha256_text(exp.parent_stem_text),
            "unit_id": uid,
        }

    # 组级解析（【分析】/【点睛】）
    if exp.group_explanation:
        lo = min(exp.group_explanation_lines)
        hi = max(exp.group_explanation_lines)
        sid = f"imp:{uid}:explanation.group"
        add_role("explanation", None, exp.group_explanation, lo, hi, uid, sid)

    # 子问（compiled_roles 归属子 unit，_aggregate_composite_roles 按 cid 取）
    for row in exp.subs:
        n = str(row.sub_number)
        cid = f"{uid}.sub{n}"
        sid_stem = f"imp:{uid}:sub{n}:stem"
        add_role("stem", n, row.stem_text, row.stem_start, row.stem_end, cid, sid_stem)
        sid_ans = f"imp:{uid}:sub{n}:answer"
        a_lo = min(row.answer_entry_lines)
        a_hi = max(row.answer_entry_lines)
        add_role("answer", n, row.answer_text, a_lo, a_hi, cid, sid_ans)
        sid_expl = f"imp:{uid}:sub{n}:explanation"
        add_role("explanation", n, row.explanation_text,
                 int(row.explanation_start), int(row.explanation_end), cid, sid_expl)
        answers.append({
            "role": "answer", "unit_id": cid,
            "label": n, "question_number": n,
            "text": row.answer_text,
            "text_hash": _sha256_text(row.answer_text),
            "span_id": sid_ans,
            "line_refs": _refs(a_lo, a_hi),
            "source_located": True,
            "complete": unit.get("answer_completeness") == "full",
            "verified_correct": None,
        })
        sub_payloads.append({
            "unit_id": cid,
            "unit_type": "standalone_unit",
            "question_number": n,
            "original_question_type": unit.get("original_question_type"),
            "content": {
                "stem": {
                    "role": "stem", "question_label": n,
                    "question_search_lines": [row.stem_start, row.stem_end],
                    "stem_lines": [row.stem_start, row.stem_end],
                },
                "options": [],
                "answer": {
                    "role": "answer", "question_label": n,
                    "answer_zone": "answer_block",
                    "answer_lines": [a_lo, a_hi],
                    "expected_value": row.answer_text,
                },
                # 契约：子问解析同时存在于 compiled_roles（role=explanation,
                # label=子问号）与 sub content（此处）——冻结 payload 自包含，
                # 消费方两者皆可取，禁止只读父级解析。
                "explanation": {
                    "role": "explanation", "question_label": n,
                    "explanation_lines": [int(row.explanation_start),
                                          int(row.explanation_end)],
                },
            },
            "depends_on": [{"type": "material_dependency", "target": "material"}],
        })

    # display_annotations → display_note role 行（B2：展示层数据，独立于解析
    # 证据链——display_only 标记、无 span_id、无 line_refs、不入
    # resolved_spans/BindingFact；持久化 source_span 亦为 display_only 形态）。
    for da in display_annotations or []:
        note_text = str(da.get("text") or "")
        if not note_text:
            continue
        lab = str(da.get("key") or f"note{len(compiled)}")
        compiled.append({
            "kind": "content", "role": "display_note", "unit_id": uid,
            "label": lab, "text": note_text,
            "text_hash": _sha256_text(note_text),
            "display_only": True,
        })

    # 图片关联（InstanceFigureLink 形状；DB 写入属 04-B）。
    # 只收 line_no 落在本 unit 声明区间内的资产（含 extra_lines），防串题。
    unit_ranges: list[tuple[int, int]] = []
    extra_rng: tuple[int, int] | None = None
    for key in ("material_lines", "questions_lines", "answer_lines",
                "explanation_lines", "extra_lines"):
        rng = unit.get(key)
        if isinstance(rng, (list, tuple)) and len(rng) == 2:
            unit_ranges.append((int(rng[0]), int(rng[1])))
            if key == "extra_lines":
                extra_rng = (int(rng[0]), int(rng[1]))
    figure_links: list[dict] = []
    for ai, a in enumerate(image_assets or []):
        ln = a.get("line_no")
        if not isinstance(ln, int):
            continue
        if not any(lo <= ln <= hi for lo, hi in unit_ranges):
            continue
        # zone：extra 区图=重复材料副本图（非本题正文图），如实区分
        zone = "extra_duplicate" if (extra_rng and extra_rng[0] <= ln <= extra_rng[1]) else "main"
        hit_role = None
        hit_unit = uid
        for sp in spans.values():
            refs = [int(r[3:]) for r in sp.get("line_refs", [])
                    if isinstance(r, str) and r.startswith("P1L")]
            if ln in refs:
                sid_parts = sp["span_id"].split(":")
                tail = sid_parts[-1]
                hit_role = "explanation" if tail == "group" else tail
                if ":sub" in sp["span_id"]:
                    hit_unit = f"{uid}.sub{sp['span_id'].split(':sub')[1].split(':')[0]}"
                break
        figure_links.append({
            "instance_unit": hit_unit,
            "figure_src": a.get("src"),
            "figure_hash": a.get("sha256") or _sha256_text(str(a.get("src"))),
            "role": hit_role or "unassigned",
            "zone": zone,
            "order": ai,
            "line_no": ln,
            "resolved_from": a.get("resolved_from"),
        })

    return {
        "unit_id": uid,
        "ok": not issues,
        "issues": issues,
        "ir_unit": {
            "unit_id": uid,
            "unit_type": "composite_unit",
            "original_question_type": unit.get("original_question_type"),
            "question_number": str(unit.get("printed_number") or ""),
            "question_number_range": str(unit.get("printed_number") or ""),
            "sub_questions": sub_payloads,
            "content": [],
        },
        "compiled_roles": compiled,
        "answer": answers,
        "resolved_spans": list(spans.values()),
        "figure_links": figure_links,
        "group_explanation": exp.group_explanation,
    }


# ══════════════════════════════════════════════════════════════════
# 组包规范（basename）：clean package dir，杜绝 03_FIXED 同名视图误用
# ══════════════════════════════════════════════════════════════════


def build_clean_package_dir(
    out_dir,
    *,
    manifest_path,
    source_md_path,
    original_path,
):
    """组包规范（04-A）：只放必要件进 clean 目录，basename 槽 = 权威源文内容。

    - manifest 原字节（*.manifest.json）
    - 权威源文（Ocr-markdown）→ 放到 manifest.source_file 的 basename 下
    - 原始 PDF/DOCX
    产出后必须用 load_package_from_dir + _verify_package_identity 复核。
    绝不把 03_FIXED 目录直接当 package_dir（同 basename 展示视图会顶位）。
    """
    import json
    import shutil
    from pathlib import Path

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    base = Path(str(manifest["source_file"]).replace("\\", "/")).name
    shutil.copy2(manifest_path, out / Path(manifest_path).name)
    shutil.copy2(source_md_path, out / base)
    shutil.copy2(original_path, out / Path(original_path).name)
    return {"package_dir": str(out), "source_basename": base,
            "manifest_name": Path(manifest_path).name,
            "original_name": Path(original_path).name}
