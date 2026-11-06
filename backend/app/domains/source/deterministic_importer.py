# -*- coding: utf-8 -*-
"""CORE-DELIVERY-05-B：Deterministic Question Importer（04-A 消费模型全形态扩展）。

职责（Owner 05-B 终裁）：已审核 Preprocessing manifest unit → 确定性结构转换 →
现有 Question/Instance/BindingFact/Admission 可消费的冻结 candidate payload。
只做确定性消费、映射、校验和必要的结构转换；不重新 OCR、不重新猜题、
不重新猜答案归属；不调用旧 Resolver/IR/Gate 语义重建链。

形态覆盖（05-B 阶段一契约）：
  1. standalone（Q1-8/Q11-15）：stem/options/answer/explanation 按 manifest
     区间直映射；options 数组缺标签时从 options_lines 区确定性解析
     （行入口 A./表格单元），解析不出 → hold。
  2. multi-q composite（U9-10 形态）：共享材料 + 逐题干/选项（源行入口按
     printed question_numbers 定位）+ 答案值「9.A 10.C」token 映射。
  3. single-q multi-part composite（Q16-22）：S1-S6 扩展版
     - S1 子问 = questions 区行首 (N) 入口（04-A 不变）
     - S2'' 答案条目 = `_{2,}` 空位 + 独立 ①②③ 条目 + 无下划线「（填X）」子句
     - S3'' 答案段 = answer_evidence.value 按「；」切段（Producer 规范化边界）
     - S4'' 全局 slot 序↔段序；子问答案 = slots 对应段按序合并
     - S5 解析：【分析】/【点睛】组级节归父级（04-C R3 语义），【详解】(N) 归子问
     - S6'' 计数/归属不齐 → fail-loud hold，绝不猜测补齐

消费契约（importer 最小完整性门，hold=不交付+精确原因）：
  H1 choice options 非自 A 起连续；H2 answer_completeness=partial；
  H3 S6'' 不齐；H4 跨 unit 声明行重叠；H5 answer_evidence.value/区间缺失。
输出形状与 04-A build_adapter_unit_payload 一致（_materialize 可直接消费）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.domains.source.short_answer_composite import (
    _BLANK_RE,
    _ENTRY_RE,
    _GROUP_MARKERS,
    _LINE_SUB_RE,
    _sha256_text,
)

FILL_RE = re.compile(r"[（(]填[^）)]*[）)]")
CIRCLED_RE = re.compile(r"[①②③④⑤⑥⑦⑧⑨]")
OPT_LINE_RE = re.compile(r"^\s*([A-H])[.．、]\s*(.*)$")
QNUM_LINE_RE = re.compile(r"^\s*(\d{1,3})[.．、]\s*")
TABLE_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
TABLE_CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def _refs(lo: int, hi: int) -> list[str]:
    return [f"P1L{n:03d}" for n in range(lo, hi + 1)]


def _slice(src: list[str], lo: int, hi: int) -> str:
    return "\n".join(src[lo - 1:hi]).strip()


# ══════════════════════════════════════════════════════════════════
# 切分/映射规则
# ══════════════════════════════════════════════════════════════════


def split_value_segments(value: str) -> list[str]:
    """S3''：answer_evidence.value 按「；」切段（「（或…）」括注保留在段内）。"""
    return [s.strip() for s in str(value).split("；") if s.strip()]


def count_slots(source_lines: list[str], lo: int, hi: int,
                mat_excl: set[int]) -> list[tuple[str, int]]:
    """S2''：答案条目（slot）。空白位 + 独立 ①② 条目 + 无下划线（填X）子句。"""
    slots: list[tuple[str, int]] = []
    for ln in range(lo, hi + 1):
        if ln in mat_excl:
            continue
        raw = source_lines[ln - 1]
        if not raw.strip():
            continue
        for cl in re.split(r"[；;。]", raw):
            if not cl.strip():
                continue
            n = len(_BLANK_RE.findall(cl))
            if n:
                slots.extend([("blank", ln)] * n)
                continue
            if FILL_RE.search(cl):
                slots.append(("fill", ln))
                continue
            if CIRCLED_RE.match(cl):
                slots.append(("item", ln))
    return slots


@dataclass
class ExplSplit:
    group_text: str = ""
    group_lines: list[int] = field(default_factory=list)
    group_parts: list[str] = field(default_factory=list)
    sub_segs: dict[int, str] = field(default_factory=dict)
    sub_ranges: dict[int, tuple[int, int]] = field(default_factory=dict)


def segment_explanation(source_lines: list[str], e_lo: int, e_hi: int,
                        expected_subs: list[int]) -> tuple[ExplSplit, list[str]]:
    """S5（04-C R3 语义）：【分析】/【点睛】组级节归父；【详解】(N) 归子问。"""
    out = ExplSplit()
    issues: list[str] = []
    cur_n: int | None = None
    cur_start = 0
    cur_buf: list[str] = []
    in_group = False

    def _close_sub(end_ln: int) -> None:
        nonlocal cur_n, cur_buf
        if cur_n is not None:
            out.sub_segs[cur_n] = "\n".join(cur_buf).strip()
            out.sub_ranges[cur_n] = (cur_start, end_ln)
            cur_n, cur_buf = None, []

    for ln in range(e_lo, e_hi + 1):
        raw = source_lines[ln - 1]
        hits = list(_ENTRY_RE.finditer(raw))
        has_group = any(mk in raw for mk in ("【分析】", "【点睛】"))
        has_detail = "【详解】" in raw
        if has_group and not has_detail:
            _close_sub(ln - 1)
            in_group = True
            out.group_lines.append(ln)
            out.group_parts.append(raw)
            continue
        if has_detail:
            in_group = False
        if in_group:
            _close_sub(ln - 1)
            out.group_lines.append(ln)
            out.group_parts.append(raw)
            continue
        if hits and not has_group:
            n = int(hits[0].group(1))
            _close_sub(ln - 1)
            cur_n = n
            cur_start = ln
            cur_buf = [raw]
            continue
        if cur_n is not None:
            cur_buf.append(raw)
        else:
            out.group_lines.append(ln)
            out.group_parts.append(raw)
    _close_sub(e_hi)
    out.group_text = "\n".join(out.group_parts).strip()
    if expected_subs and sorted(out.sub_segs) != sorted(expected_subs):
        issues.append(
            f"explanation segments {sorted(out.sub_segs)} != sub numbers "
            f"{sorted(expected_subs)}"
        )
    return out, issues


def parse_region_options(source_lines: list[str], lo: int, hi: int):
    """从 options_lines 区按行入口 A./B./… 确定性解析选项。"""
    opts = []
    cur = None
    for ln in range(lo, hi + 1):
        raw = source_lines[ln - 1]
        m = OPT_LINE_RE.match(raw)
        if m:
            if cur:
                opts.append(cur)
            cur = {"label": m.group(1), "start_line": ln, "end_line": ln,
                   "text": m.group(2).strip()}
        elif cur is not None and raw.strip():
            cur["end_line"] = ln
            cur["text"] += "\n" + raw.strip()
    if cur:
        opts.append(cur)
    return opts


def parse_table_options(source_lines: list[str], lo: int, hi: int):
    """HTML 表格选项（Q13 形态）：<tr> 首格为 A-H 标签的行 → 选项。"""
    blob = "\n".join(source_lines[lo - 1:hi])
    opts = []
    for row in TABLE_ROW_RE.findall(blob):
        cells = [TAG_RE.sub("", c).strip() for c in TABLE_CELL_RE.findall(row)]
        if not cells:
            continue
        lab = cells[0]
        if len(lab) == 1 and lab.isalpha() and lab.isupper():
            opts.append({"label": lab, "start_line": lo, "end_line": hi,
                         "text": " | ".join(c for c in cells[1:] if c)})
    return opts


def check_options_contract(labels: list[str]) -> list[str]:
    """H1：choice 选项标签须自 A 起连续。"""
    if not labels:
        return ["options missing (no labels parsed)"]
    if labels[0] != "A":
        return [f"options labels not starting at A: {labels}"]
    expect = [chr(ord("A") + i) for i in range(len(labels))]
    if labels != expect:
        return [f"options labels not contiguous from A: {labels}"]
    return []


def _is_choice(qtype: str | None) -> bool:
    return str(qtype or "") in ("single_choice", "multiple_choice", "true_false")


def check_review_ready(facts: list) -> list[str]:
    """05-B.1 安全闸：任一答案 BindingFact ownership != match → 阻断 review-ready。

    发现绑定不可信 → 阻止交付（fail-closed）；importer 不修答案。
    facts: derive_binding_fact 产物（含 .ownership/.span_id）。
    返回阻断原因列表（空=可进入 review-ready）。
    """
    reasons = []
    for f in facts:
        own = getattr(f, "ownership", None)
        if own != "match":
            reasons.append(
                f"BLOCK: answer fact ownership={own!r} (span={getattr(f, 'span_id', '?')})"
                " — binding untrusted; unit must not enter review-ready"
            )
    return reasons


# ══════════════════════════════════════════════════════════════════
# payload 组装工具（输出形状与 04-A build_adapter_unit_payload 一致）
# ══════════════════════════════════════════════════════════════════


class _Asm:
    """compiled_roles / answer / resolved_spans 组装器。"""

    def __init__(self, uid: str):
        self.uid = uid
        self.compiled: list[dict] = []
        self.answers: list[dict] = []
        self.spans: dict[str, dict] = {}

    def role(self, role: str, label: str | None, text: str, lo: int, hi: int,
             unit_id: str, span_id: str, kind: str = "content",
             line_refs: list[str] | None = None, **extra) -> dict:
        refs = line_refs if line_refs is not None else _refs(lo, hi)
        row = {
            "kind": kind, "role": role, "unit_id": unit_id,
            "label": label, "text": text, "text_hash": _sha256_text(text),
            "span_id": span_id, "line_refs": refs,
        }
        row.update(extra)
        self.compiled.append(row)
        self.spans[span_id] = {
            "span_id": span_id, "line_refs": refs,
            "text_hash": _sha256_text(text), "unit_id": unit_id,
        }
        return row

    def answer(self, label: str | None, text: str, lo: int, hi: int,
               unit_id: str, span_id: str, question_number: str | None = None,
               complete: bool = False, declared_value: str | None = None,
               decode_loc: str = "") -> None:
        # 契约（admission._materialize）：答案文本只经 answer[] 通道按
        # _publish_decision 写入（pending 时空文本+withheld）；compiled_roles
        # 不放 answer 行——standalone 路径会把 role 行原样落库触发
        # 「non-official answer text must be empty」闸。
        # declared_value/decode_loc：逐子问 fact 生成输入（05-B.1）。
        refs = _refs(lo, hi)
        self.spans[span_id] = {
            "span_id": span_id, "line_refs": refs,
            "text_hash": _sha256_text(text), "unit_id": unit_id,
        }
        entry = {
            "role": "answer", "unit_id": unit_id,
            "label": label, "question_number": question_number or label,
            "text": text, "text_hash": _sha256_text(text),
            "span_id": span_id, "line_refs": refs,
            "source_located": True, "complete": complete,
            "verified_correct": None,
        }
        if declared_value is not None:
            entry["declared_value"] = declared_value
        if decode_loc:
            entry["decode_loc"] = decode_loc
        self.answers.append(entry)


def _sub_content(n: str, stem_rng, ans_rng, expl_rng, opt_count: int = 0):
    return {
        "stem": {"role": "stem", "question_label": n,
                 "question_search_lines": list(stem_rng),
                 "stem_lines": list(stem_rng)},
        "options": [] if not opt_count else [{"label": chr(65 + i)} for i in range(opt_count)],
        "answer": {"role": "answer", "question_label": n,
                   "answer_zone": "answer_block", "answer_lines": list(ans_rng),
                   "expected_value": None},
        "explanation": {"role": "explanation", "question_label": n,
                        "explanation_lines": list(expl_rng) if expl_rng else None},
    }


def _sub_payload(cid: str, n: str, qtype: str | None, content: dict):
    return {
        "unit_id": cid, "unit_type": "standalone_unit",
        "question_number": n, "original_question_type": qtype,
        "content": content,
        "depends_on": [{"type": "material_dependency", "target": "material"}],
    }


# ══════════════════════════════════════════════════════════════════
# 1) standalone builder
# ══════════════════════════════════════════════════════════════════


def build_standalone_payload(unit: dict, source_lines: list[str]):
    uid = str(unit.get("unit_id"))
    qtype = unit.get("original_question_type")
    holds: list[str] = []
    asm = _Asm(uid)

    s_rng = unit.get("stem_lines")
    a_rng = unit.get("answer_lines")
    e_rng = unit.get("explanation_lines")
    m_rng = unit.get("material_lines")
    ae = unit.get("answer_evidence") or {}
    val = ae.get("value")
    if val is None:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": ["H5: answer_evidence.value missing"]}

    # stem
    if s_rng:
        lo, hi = int(s_rng[0]), int(s_rng[1])
        stem_text = _slice(source_lines, lo, hi)
    else:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": ["H5: stem_lines missing"]}
    asm.role("stem", None, stem_text, lo, hi, uid, f"imp:{uid}:stem")

    # material
    if m_rng:
        mlo, mhi = int(m_rng[0]), int(m_rng[1])
        asm.role("material", None, _slice(source_lines, mlo, mhi), mlo, mhi,
                 uid, f"imp:{uid}:material", kind="material")

    # options：manifest 数组优先；缺则从 options_lines 区解析
    opt_entries = unit.get("options") or []
    parsed = []
    if opt_entries:
        for o in opt_entries:
            olo, ohi = int(o["start_line"]), int(o["end_line"])
            parsed.append({"label": str(o["label"]),
                           "text": _slice(source_lines, olo, ohi),
                           "lo": olo, "hi": ohi})
    else:
        o_rng = unit.get("options_lines")
        if o_rng:
            olo, ohi = int(o_rng[0]), int(o_rng[1])
            blob = "\n".join(source_lines[olo - 1:ohi])
            if "<table" in blob.lower():
                raw_opts = parse_table_options(source_lines, olo, ohi)
            else:
                raw_opts = parse_region_options(source_lines, olo, ohi)
            for o in raw_opts:
                parsed.append({"label": o["label"], "text": o["text"],
                               "lo": o["start_line"], "hi": o["end_line"]})
    labels = [p["label"] for p in parsed]
    if _is_choice(qtype):
        holds.extend(f"H1: {m}" for m in check_options_contract(labels))
    for p in parsed:
        asm.role("option", p["label"], p["text"], p["lo"], p["hi"], uid,
                 f"imp:{uid}:option.{p['label']}")

    # answer：value 直用（审计值）；证据区间=answer_lines 或 explanation 区
    if a_rng:
        alo, ahi = int(a_rng[0]), int(a_rng[1])
    elif e_rng:
        alo, ahi = int(e_rng[0]), int(e_rng[1])
    else:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": ["H5: answer evidence region missing"]}
    ans_text = str(val)
    asm.answer(None, ans_text, alo, ahi, uid, f"imp:{uid}:answer",
               question_number=str(unit.get("printed_number") or ""),
               complete=unit.get("answer_completeness") == "full")

    # explanation 整段
    if e_rng:
        elo, ehi = int(e_rng[0]), int(e_rng[1])
        asm.role("explanation", None, _slice(source_lines, elo, ehi), elo, ehi,
                 uid, f"imp:{uid}:explanation")

    hold = bool(holds)
    return {
        "unit_id": uid, "ok": not hold, "hold": hold, "hold_reasons": holds,
        "issues": [],
        "ir_unit": {
            "unit_id": uid, "unit_type": "standalone_unit",
            "original_question_type": qtype,
            "question_number": str(unit.get("printed_number") or ""),
            "question_number_range": str(unit.get("printed_number") or ""),
            "sub_questions": [], "content": [],
        },
        "compiled_roles": asm.compiled,
        "answer": asm.answers,
        "resolved_spans": list(asm.spans.values()),
        "figure_links": [],
        "group_explanation": "",
    }


# ══════════════════════════════════════════════════════════════════
# 2) multi-q choice composite builder（U9-10 形态）
# ══════════════════════════════════════════════════════════════════


def build_multi_q_payload(unit: dict, source_lines: list[str]):
    uid = str(unit.get("unit_id"))
    qtype = unit.get("original_question_type")
    holds: list[str] = []
    asm = _Asm(uid)
    qns = [int(x) for x in (unit.get("question_numbers") or [])]
    q_rng = unit.get("questions_lines")
    m_rng = unit.get("material_lines")
    ae = unit.get("answer_evidence") or {}
    val = ae.get("value")
    if not q_rng or val is None:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": ["H5: questions_lines/value missing"]}

    q_lo, q_hi = int(q_rng[0]), int(q_rng[1])
    mat_excl: set[int] = set()
    if m_rng:
        mat_excl = set(range(int(m_rng[0]), int(m_rng[1]) + 1))
        mlo, mhi = int(m_rng[0]), int(m_rng[1])
        asm.role("material", None, _slice(source_lines, mlo, mhi), mlo, mhi,
                 uid, f"imp:{uid}:material", kind="material")

    # 子题干定位：printed question_number 行入口
    entries: list[tuple[int, int]] = []  # (qn, line)
    for ln in range(q_lo, q_hi + 1):
        if ln in mat_excl:
            continue
        m = QNUM_LINE_RE.match(source_lines[ln - 1])
        if m and int(m.group(1)) in qns:
            entries.append((int(m.group(1)), ln))
    if [e[0] for e in entries] != qns:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": [
                    f"H3: sub question entries {[e[0] for e in entries]} != "
                    f"question_numbers {qns}"]}

    # 父级 stem：B1 上下文；空则材料首行（如实映射，不合成）
    sub_excl: set[int] = set()
    bounds = []
    for i, (qn, ln) in enumerate(entries):
        end = entries[i + 1][1] - 1 if i + 1 < len(entries) else q_hi
        while end > ln and not source_lines[end - 1].strip():
            end -= 1
        bounds.append((qn, ln, end))
        sub_excl.update(range(ln, end + 1))
    keep = [ln for ln in range(q_lo, q_hi + 1)
            if ln not in mat_excl and ln not in sub_excl]
    while keep and not source_lines[keep[0] - 1].strip():
        keep.pop(0)
    while keep and not source_lines[keep[-1] - 1].strip():
        keep.pop()
    if keep:
        p_text = "\n".join(source_lines[ln - 1] for ln in keep).strip()
        asm.role("stem", None, p_text, min(keep), max(keep), uid,
                 f"imp:{uid}:stem.parent", line_refs=[f"P1L{n:03d}" for n in keep])
    else:
        lead = next((ln for ln in sorted(mat_excl) if source_lines[ln - 1].strip()), None)
        if lead is None:
            return {"unit_id": uid, "ok": False, "hold": True,
                    "hold_reasons": ["H5: no parent stem/material content"]}
        asm.role("stem", None, source_lines[lead - 1].strip(), lead, lead, uid,
                 f"imp:{uid}:stem.parent")

    # 答案 token：「9.A 10.C」
    ans_map: dict[int, str] = {}
    for m in re.finditer(r"(\d{1,3})\s*[.．、:：]\s*([A-Za-z]+)", str(val)):
        ans_map[int(m.group(1))] = m.group(2)
    if sorted(ans_map) != sorted(qns):
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": [
                    f"H3: answer tokens {sorted(ans_map)} != question_numbers {qns}"]}

    # 逐子问答案行定位（05-B.1）：答案区内「【答案】」入口行按序映射到子问，
    # 字母须与 token 一致；span=入口行至下一空行（多行答案含续行）。
    # 不得把整个 answer_lines 区间作为每个子问的 answer evidence（整窗含
    # 选项标签 A-D 会污染单字母归属 → foreign）。
    a_lo, a_hi = int(unit["answer_lines"][0]), int(unit["answer_lines"][1])
    entry_lines: list[tuple[int, str]] = []
    for ln in range(a_lo, a_hi + 1):
        raw = source_lines[ln - 1]
        m = re.match(r"\s*【?\s*答案\s*】?\s*[：:]?\s*([A-Za-z0-9]+)", raw)
        if m:
            entry_lines.append((ln, m.group(1)))
    if len(entry_lines) != len(qns):
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": [
                    f"H3: answer entry lines {entry_lines} count != question_numbers {qns}"]}
    ans_line_map: dict[int, tuple[int, int]] = {}
    for i, qn in enumerate(qns):
        ln, letter = entry_lines[i]
        if letter.upper() != ans_map[qn].upper():
            return {"unit_id": uid, "ok": False, "hold": True,
                    "hold_reasons": [
                        f"H3: answer entry letter {letter!r} != token "
                        f"{ans_map[qn]!r} for qn {qn} at L{ln}"]}
        end = ln
        while end < a_hi and source_lines[end].strip():
            end += 1
        ans_line_map[qn] = (ln, end)

    sub_payloads = []
    for qn, lo, hi in bounds:
        cid = f"{uid}.sub{qn}"
        n = str(qn)
        # 子问干=入口行至本区间内第一个选项行前；选项=A. 行入口
        opt_entries = []
        stem_end = hi
        for ln in range(lo, hi + 1):
            m = OPT_LINE_RE.match(source_lines[ln - 1])
            if m:
                opt_entries.append((m.group(1), ln))
                if stem_end == hi and ln > lo:
                    stem_end = ln - 1
        while stem_end > lo and not source_lines[stem_end - 1].strip():
            stem_end -= 1
        stem_text = _slice(source_lines, lo, stem_end)
        asm.role("stem", n, stem_text, lo, stem_end, cid, f"imp:{uid}:sub{qn}:stem")
        # 选项区间：各自标签行至下个标签行/区间尾
        for i, (lab, ln) in enumerate(opt_entries):
            end = opt_entries[i + 1][1] - 1 if i + 1 < len(opt_entries) else hi
            while end > ln and not source_lines[end - 1].strip():
                end -= 1
            asm.role("option", lab, _slice(source_lines, ln, end), ln, end, cid,
                     f"imp:{uid}:sub{qn}:option.{lab}")
        labels = [e[0] for e in opt_entries]
        if _is_choice(qtype):
            holds.extend(f"H1(sub {n}): {m}" for m in check_options_contract(labels))
        # 答案（token 映射；05-B.1：逐子问 span + token 级 declared_value）
        atext = ans_map[qn]
        alo, ahi2 = ans_line_map[qn]
        asm.answer(n, atext, alo, ahi2, cid, f"imp:{uid}:sub{qn}:answer",
                   question_number=n,
                   complete=unit.get("answer_completeness") == "full",
                   declared_value=atext,
                   decode_loc=f"qn:{qn}|cell:{atext}")
        sub_payloads.append(_sub_payload(
            cid, n, qtype,
            _sub_content(n, (lo, stem_end), (alo, ahi2), None,
                         opt_count=len(labels))))

    # 组级解析（multi-q 共享解析块）
    e_rng = unit.get("explanation_lines")
    group_text = ""
    if e_rng:
        elo, ehi = int(e_rng[0]), int(e_rng[1])
        group_text = _slice(source_lines, elo, ehi)
        asm.role("explanation", None, group_text, elo, ehi, uid,
                 f"imp:{uid}:explanation.group")

    hold = bool(holds)
    return {
        "unit_id": uid, "ok": not hold, "hold": hold, "hold_reasons": holds,
        "issues": [],
        "ir_unit": {
            "unit_id": uid, "unit_type": "composite_unit",
            "original_question_type": qtype,
            "question_number": None,
            "question_number_range": f"{qns[0]}-{qns[-1]}",
            "sub_questions": sub_payloads, "content": [],
        },
        "compiled_roles": asm.compiled,
        "answer": asm.answers,
        "resolved_spans": list(asm.spans.values()),
        "figure_links": [],
        "group_explanation": group_text,
    }


# ══════════════════════════════════════════════════════════════════
# 3) single-q multi-part composite builder（Q16-22 形态，S1-S6''）
# ══════════════════════════════════════════════════════════════════


def build_multi_part_payload(unit: dict, source_lines: list[str]):
    uid = str(unit.get("unit_id"))
    qtype = unit.get("original_question_type")
    holds: list[str] = []
    asm = _Asm(uid)

    q_rng = unit.get("questions_lines")
    a_rng = unit.get("answer_lines")
    e_rng = unit.get("explanation_lines")
    m_rng = unit.get("material_lines")
    ae = unit.get("answer_evidence") or {}
    val = ae.get("value")
    if not q_rng or not a_rng or val is None:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": ["H5: questions/answer range or value missing"]}
    if unit.get("answer_completeness") == "partial":
        holds.append("H2: answer_completeness=partial (declared incomplete evidence)")

    q_lo, q_hi = int(q_rng[0]), int(q_rng[1])
    a_lo, a_hi = int(a_rng[0]), int(a_rng[1])
    mat_excl: set[int] = set()
    if m_rng:
        mat_excl = set(range(int(m_rng[0]), int(m_rng[1]) + 1))
        mlo, mhi = int(m_rng[0]), int(m_rng[1])
        asm.role("material", None, _slice(source_lines, mlo, mhi), mlo, mhi,
                 uid, f"imp:{uid}:material", kind="material")

    # S1 子问 = 行首 (N) 入口
    sub_lines: list[tuple[int, int]] = []
    for ln in range(q_lo, q_hi + 1):
        if ln in mat_excl:
            continue
        m = _LINE_SUB_RE.match(source_lines[ln - 1])
        if m:
            n = int(m.group(1))
            if sub_lines and n != sub_lines[-1][0] + 1:
                holds.append(f"H3: sub entry numbering not sequential at L{ln}")
            sub_lines.append((n, ln))
    if not sub_lines:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": ["H3: no (N) sub-question entries"]}
    bounds = []
    for i, (n, ln) in enumerate(sub_lines):
        end = sub_lines[i + 1][1] - 1 if i + 1 < len(sub_lines) else q_hi
        while end > ln and not source_lines[end - 1].strip():
            end -= 1
        bounds.append((n, ln, end))
    expected_subs = [n for n, _ in sub_lines]

    # B1 父级 stem
    sub_excl: set[int] = set()
    for _n, lo, hi in bounds:
        sub_excl.update(range(lo, hi + 1))
    keep = [ln for ln in range(q_lo, q_hi + 1)
            if ln not in mat_excl and ln not in sub_excl]
    while keep and not source_lines[keep[0] - 1].strip():
        keep.pop(0)
    while keep and not source_lines[keep[-1] - 1].strip():
        keep.pop()
    if keep:
        p_text = "\n".join(source_lines[ln - 1] for ln in keep).strip()
        asm.role("stem", None, p_text, min(keep), max(keep), uid,
                 f"imp:{uid}:stem.parent", line_refs=[f"P1L{n:03d}" for n in keep])
    else:
        lead = next((ln for ln in sorted(mat_excl) if source_lines[ln - 1].strip()), None)
        if lead is None:
            return {"unit_id": uid, "ok": False, "hold": True,
                    "hold_reasons": ["H5: no parent stem/material content"]}
        asm.role("stem", None, source_lines[lead - 1].strip(), lead, lead, uid,
                 f"imp:{uid}:stem.parent")

    # S2''/S3''/S4''
    segs = split_value_segments(val)
    slots: list[tuple[str, int]] = []
    per_sub_slots: list[int] = []
    for n, lo, hi in bounds:
        s = count_slots(source_lines, lo, hi, mat_excl)
        per_sub_slots.append(len(s))
        slots.extend(s)
    if len(slots) != len(segs):
        holds.append(
            f"H3: slots/segments mismatch: slots={len(slots)} "
            f"({per_sub_slots}) vs segs={len(segs)}")
    # 段入口行定位（溯源）
    seg_entry_line: dict[int, int] = {}
    for ln in range(a_lo, a_hi + 1):
        for m in _ENTRY_RE.finditer(source_lines[ln - 1]):
            n = int(m.group(1))
            if n not in seg_entry_line:
                seg_entry_line[n] = ln
    # S5 解析切分
    expl, expl_issues = (ExplSplit(), [])
    if e_rng:
        expl, expl_issues = segment_explanation(
            source_lines, int(e_rng[0]), int(e_rng[1]), expected_subs)
        holds.extend(f"H3: {i}" for i in expl_issues)

    if holds:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": holds, "issues": holds}

    # 组装子问
    sub_payloads = []
    k = 0
    for i, (n, lo, hi) in enumerate(bounds):
        cid = f"{uid}.sub{n}"
        ns = str(n)
        seg_nos = list(range(k, k + per_sub_slots[i]))
        k += per_sub_slots[i]
        ans_text = " ".join(segs[j] for j in seg_nos)
        a_lines = sorted({seg_entry_line.get(j + 1, a_lo) for j in seg_nos}) or [a_lo]
        alo2, ahi2 = min(a_lines), max(a_lines)
        asm.role("stem", ns, _slice(source_lines, lo, hi), lo, hi, cid,
                 f"imp:{uid}:sub{n}:stem")
        asm.answer(ns, ans_text, alo2, ahi2, cid, f"imp:{uid}:sub{n}:answer",
                   question_number=ns,
                   complete=unit.get("answer_completeness") == "full")
        expl_rng = None
        if n in expl.sub_ranges:
            elo, ehi = expl.sub_ranges[n]
            expl_rng = (elo, ehi)
            asm.role("explanation", ns, expl.sub_segs[n], elo, ehi, cid,
                     f"imp:{uid}:sub{n}:explanation")
        sub_payloads.append(_sub_payload(
            cid, ns, qtype,
            _sub_content(ns, (lo, hi), (alo2, ahi2), expl_rng)))

    # 组级解析
    group_text = ""
    if expl.group_text:
        glo = min(expl.group_lines)
        ghi = max(expl.group_lines)
        group_text = expl.group_text
        asm.role("explanation", None, group_text, glo, ghi, uid,
                 f"imp:{uid}:explanation.group")

    return {
        "unit_id": uid, "ok": True, "hold": False, "hold_reasons": [],
        "issues": [],
        "ir_unit": {
            "unit_id": uid, "unit_type": "composite_unit",
            "original_question_type": qtype,
            "question_number": str(unit.get("printed_number") or ""),
            "question_number_range": str(unit.get("printed_number") or ""),
            "sub_questions": sub_payloads, "content": [],
        },
        "compiled_roles": asm.compiled,
        "answer": asm.answers,
        "resolved_spans": list(asm.spans.values()),
        "figure_links": [],
        "group_explanation": group_text,
    }


# ══════════════════════════════════════════════════════════════════
# 调度器：形态分发 + 跨 unit 边界冲突（H4）
# ══════════════════════════════════════════════════════════════════


def build_unit_payload(unit: dict, source_lines: list[str],
                       *, overlap_units: set[str] | None = None):
    """manifest unit → 冻结 payload（确定性）。overlap_units=跨 unit 声明行
    重叠涉事 unit 集（H4：hold，不修不猜）。"""
    uid = str(unit.get("unit_id"))
    if overlap_units and uid in overlap_units:
        return {"unit_id": uid, "ok": False, "hold": True,
                "hold_reasons": ["H4: cross-unit declared line overlap "
                                 "(input contract conflict; consume-not-repair)"]}
    ut = unit.get("unit_type")
    n_qns = len(unit.get("question_numbers") or [])
    if ut == "standalone_question":
        return build_standalone_payload(unit, source_lines)
    if ut == "composite_question" and n_qns > 1:
        return build_multi_q_payload(unit, source_lines)
    if ut == "composite_question":
        return build_multi_part_payload(unit, source_lines)
    return {"unit_id": uid, "ok": False, "hold": True,
            "hold_reasons": [f"H3: unknown unit_type {ut!r}"]}
