"""Source Resolver 核心（段 E，E3-E5，20 §5）。

resolve() 为纯函数：把 annotation payload 里显式声明的 reference 解析为 ResolvedSpan /
ResolvedRelation。七种 role 各用独立 policy（失败语义不同，不做万能 matcher）。

安全边界（代码级不变量）：
    resolved ⇔ status ∈ {exact, normalized, contextual}
    fuzzy / ambiguous / missing / incomplete ⇒ 只产 UnresolvedReference（无 ResolvedSpan）

「E 可以失败，但不能猜」。定位只依据显式 marker / 标签 / 题号 token / 显式边界，
不做文本相似度 / nearest / first-match 自动接受。
"""

from __future__ import annotations

import hashlib
import re
import uuid

from app.domains.resolver.match_normalization import (
    is_answer_header,
    is_explanation_header,
    is_question_start,
    normalize_text,
    option_tokens,
)
from app.domains.resolver.reference import (
    extract_relations,
    extract_targets,
)
from app.domains.resolver.span import (
    ResolvedRelation,
    ResolvedRun,
    ResolvedSpan,
    SourceFigureView,
    SourceLineView,
    SourceRegion,
    UnresolvedReference,
)


def _raw_sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# 行内条目形态：题号 token + 分隔符（bounded，防 qn=1 误配 "10."）。offset 基于 raw text。
_ENTRY_RE = re.compile(r"(?<![\d])(\d{1,3})\s*[.．、:]")


def _entry_offsets(text: str, qn: str) -> list[int]:
    """raw 行内 qn 条目起点列表（行内多条目如同行多题答案时 >1）。"""
    return [m.start() for m in _ENTRY_RE.finditer(text) if m.group(1) == qn]


# 行内选项标签（bounded，防 "对A项" 误配随机大写；需标签+分隔符）。
_LABEL_RE = re.compile(r"(?<![\w])([A-Ha-h])\s*[.．、:)）]")


def _label_offsets(text: str, label: str) -> list[int]:
    return [
        m.start() for m in _LABEL_RE.finditer(text)
        if m.group(1).upper() == label.upper()
    ]


# E owns source-span overlap（material span 不得与子题/其他 material 重叠）。
_MATERIAL_ROLES = frozenset(
    {"material", "word_bank", "shared_option_pool", "task_instruction"}
)


class _LineIndex:
    """有序行视图（seq 单调）。纯内存，无 ORM。"""

    def __init__(self, lines: tuple[SourceLineView, ...]):
        self.lines = tuple(sorted(lines, key=lambda l: l.seq))
        self._by_ref = {l.line_ref: l for l in self.lines}
        self._norm = [normalize_text(l.text) for l in self.lines]

    def get(self, ref: str) -> SourceLineView:
        return self._by_ref[ref]

    def seq_of(self, ref: str) -> int:
        return self._by_ref[ref].seq

    def between(self, lo: int, hi: int) -> list[SourceLineView]:
        return [l for l in self.lines if lo <= l.seq < hi]

    def between_incl(self, lo: int, hi: int) -> list[SourceLineView]:
        return [l for l in self.lines if lo <= l.seq <= hi]

    def after(self, ref: str) -> list[SourceLineView]:
        return [l for l in self.lines if l.seq > self.seq_of(ref)]

    def raw_hits(self, query: str) -> list[str]:
        return [l.line_ref for l in self.lines if query in l.text]

    def norm_hits(self, norm_query: str) -> list[str]:
        return [l.line_ref for l, n in zip(self.lines, self._norm) if norm_query in n]

    def fuzzy_hits(self, norm_query: str) -> list[str]:
        flat = norm_query.replace(" ", "")
        return [
            l.line_ref for l, n in zip(self.lines, self._norm)
            if n != flat and n.replace(" ", "") == flat
        ]


def _locate(query: str, idx: _LineIndex) -> tuple[str, list[str]]:
    """exact > normalized > fuzzy/missing/ambiguous（不做自动接受）。"""
    raw = idx.raw_hits(query)
    if len(raw) == 1:
        return "exact", raw
    if len(raw) > 1:
        return "ambiguous", raw
    nq = normalize_text(query)
    norm = idx.norm_hits(nq)
    if len(norm) == 1:
        return "normalized", norm
    if len(norm) > 1:
        return "ambiguous", norm
    fuzzy = idx.fuzzy_hits(nq)
    if fuzzy:
        return "fuzzy", fuzzy
    return "missing", []


def _is_resolved(status: str) -> bool:
    return status in ("exact", "normalized", "contextual")


class _Out:
    """一次 resolve 的收集容器。持 idx 以便从 line_ref 切片 span 文本（BUG-V3-012）。"""

    def __init__(self, svid: uuid.UUID, idx: "_LineIndex"):
        self.svid = svid
        self._idx = idx
        self.resolved: list[ResolvedSpan] = []
        self.unresolved: list[UnresolvedReference] = []

    def add_span(self, unit_id: str, t, refs, status, evidence, role_hint=None):
        text = self._slice(refs)
        self.resolved.append(
            ResolvedSpan(
                span_id=f"sp-{t.target_id}",
                source_version_id=self.svid,
                role=role_hint or t.role,
                start_line_ref=refs[0],
                end_line_ref=refs[-1],
                line_refs=tuple(refs),
                granularity="line",
                start_offset=None,
                end_offset=None,
                text_hash=_raw_sha256(text),
                resolution_status=status,
                evidence=tuple(evidence),
            )
        )

    def add_char_span(self, unit_id, t, line_ref, start, end, status, evidence):
        """line_character span：按已知 [start,end) raw offsets 切片（不重查，调用方保证有界唯一）。"""
        raw = self._idx.get(line_ref).text
        end = min(end, len(raw))
        if start < 0 or start >= end:
            self.unresolved.append(
                UnresolvedReference(
                    reference_id=t.target_id, role=t.role,
                    resolution_status="incomplete",
                    evidence=("invalid inline offsets", str(start), str(end)),
                )
            )
            return
        self.resolved.append(
            ResolvedSpan(
                span_id=f"sp-{t.target_id}", source_version_id=self.svid,
                role=t.role, start_line_ref=line_ref, end_line_ref=line_ref,
                line_refs=(line_ref,), granularity="line_character",
                start_offset=start, end_offset=end,
                text_hash=_raw_sha256(raw[start:end]),
                resolution_status=status, evidence=tuple(evidence),
            )
        )

    def add_unresolved(self, t, status, evidence):
        self.unresolved.append(
            UnresolvedReference(
                reference_id=t.target_id, role=t.role,
                resolution_status=status, evidence=tuple(evidence),
            )
        )

    def add_fragment_span(self, unit_id, t, line_ref, q, status, evidence):
        """line_character span：在 raw 行文本内精确子串查找 offset（code-point 索引）。

        行内多命中 → 调用方须先判 ambiguous（不在此 first-match）。找不到唯一 raw 子串
        （仅 normalized 命中）→ 退化整行 granularity=line。
        """
        raw = self._idx.get(line_ref).text
        pos = raw.find(q)
        if pos == -1:
            # normalized 命中但 raw 无该串 → 无法给可靠 offset，退化为整行 line span。
            self.resolved.append(
                ResolvedSpan(
                    span_id=f"sp-{t.target_id}", source_version_id=self.svid,
                    role=t.role, start_line_ref=line_ref, end_line_ref=line_ref,
                    line_refs=(line_ref,), granularity="line",
                    start_offset=None, end_offset=None,
                    text_hash=_raw_sha256(raw), resolution_status=status,
                    evidence=tuple(evidence) + ("degrade-to-line(no-raw-slice)",),
                )
            )
            return
        if raw.find(q, pos + len(q)) != -1:
            self.unresolved.append(
                UnresolvedReference(
                    reference_id=t.target_id, role=t.role,
                    resolution_status="ambiguous",
                    evidence=("line-fragment matches more than once on raw line",),
                )
            )
            return
        self.resolved.append(
            ResolvedSpan(
                span_id=f"sp-{t.target_id}", source_version_id=self.svid,
                role=t.role, start_line_ref=line_ref, end_line_ref=line_ref,
                line_refs=(line_ref,), granularity="line_character",
                start_offset=pos, end_offset=pos + len(q),
                text_hash=_raw_sha256(raw[pos : pos + len(q)]),
                resolution_status=status, evidence=tuple(evidence),
            )
        )

    def _slice(self, refs: list[str]) -> str:
        """span 覆盖行文本：多行以 "\\n" join（BUG-V3-012 implementation choice，
        与段 B IS-4 重建规则一致；20 §5.5 未冻结跨行拼接）。"""
        return "\n".join(self._idx.get(r).text for r in refs)


class SourceResolver:
    """Semantic Reference → ResolvedRun（纯函数入口）。"""

    def __init__(
        self,
        *,
        source_version_id: uuid.UUID,
        lines: tuple[SourceLineView, ...],
        figures: tuple[SourceFigureView, ...] = (),
    ):
        self._svid = source_version_id
        self._idx = _LineIndex(lines)
        self._figures = figures
        # 题目区终点 = 首个 答案/详解/解析 表头 seq（其后为答案/详解区，不得当题号行）。
        self._qzone_end = next(
            (l.seq for l in self._idx.lines
             if is_answer_header(normalize_text(l.text))
             or is_explanation_header(normalize_text(l.text))),
            10**9,
        )

    def _question_zone(self):
        """仅题目区（答案/详解表头之前）的行。"""
        return [l for l in self._idx.lines if l.seq < self._qzone_end]

    def resolve(self, annotation_payload: dict) -> ResolvedRun:
        out = _Out(self._svid, self._idx)
        by_unit: dict[str, list] = {}
        for t in extract_targets(annotation_payload):
            by_unit.setdefault(t.unit_id, []).append(t)
        for unit_id, targets in by_unit.items():
            self._resolve_unit(out, unit_id, targets)
        self._enforce_material_overlap(out)
        rels = self._resolve_relations(
            out, extract_relations(annotation_payload)
        )
        return ResolvedRun(
            source_version_id=self._svid,
            resolved_spans=tuple(out.resolved),
            unresolved_references=tuple(out.unresolved),
            resolved_relations=tuple(r for r in rels if r.status == "resolved"),
            unresolved_relations=tuple(r for r in rels if r.status != "resolved"),
            semantic_regions=self._compute_regions(),
        )

    def _compute_regions(self) -> tuple[SourceRegion, ...]:
        """Structural region map from deterministic header grammar (H-3).

        Produces question/answer/explanation structural regions. This is
        **consistency evidence** for the Source Evidence Binding Contract,
        NOT semantic truth. Gate uses it for span-overlap consistency checks.

        No answer header -> only question region (entire source is question zone).
        """
        lines = self._idx.lines
        answer_hdr_seq: int | None = None
        explanation_hdr_seq: int | None = None
        for l in lines:
            norm = normalize_text(l.text)
            if answer_hdr_seq is None and is_answer_header(norm):
                answer_hdr_seq = l.seq
            if explanation_hdr_seq is None and is_explanation_header(norm):
                explanation_hdr_seq = l.seq
            if answer_hdr_seq is not None and explanation_hdr_seq is not None:
                break

        regions: list[SourceRegion] = []

        def _refs_between(lo: int, hi: int) -> tuple[str, ...]:
            return tuple(l.line_ref for l in lines if lo <= l.seq < hi)

        # question region: [first_seq, answer_hdr or explanation_hdr or +inf)
        q_end = answer_hdr_seq or explanation_hdr_seq or (lines[-1].seq + 1 if lines else 0)
        q_refs = _refs_between(lines[0].seq if lines else 0, q_end)
        if q_refs:
            regions.append(SourceRegion("question", lines[0].seq if lines else 0, q_end, q_refs))

        # answer region: (answer_hdr, explanation_hdr or +inf)
        if answer_hdr_seq is not None:
            a_end = explanation_hdr_seq or (lines[-1].seq + 1)
            a_refs = _refs_between(answer_hdr_seq + 1, a_end)
            if a_refs:
                regions.append(SourceRegion("answer", answer_hdr_seq + 1, a_end, a_refs))

        # explanation region: (explanation_hdr, +inf)
        if explanation_hdr_seq is not None:
            e_end = lines[-1].seq + 1
            e_refs = _refs_between(explanation_hdr_seq + 1, e_end)
            if e_refs:
                regions.append(SourceRegion("explanation", explanation_hdr_seq + 1, e_end, e_refs))

        return tuple(regions)

    # ------------------------------------------------------------------ 调度
    def _resolve_unit(self, out: _Out, unit_id: str, targets) -> None:
        stem_t = next((t for t in targets if t.kind == "question_label"), None)
        qn = stem_t.question_number if stem_t else None
        start_ref: str | None = None
        region_upper: int | None = None
        if qn:
            start_ref = self._locate_question_start(out, unit_id, stem_t, qn)
        if start_ref:
            # 本 unit 内容区 = 题号行之后、下一题/答案/详解表头之前（显式边界）。
            region_upper = self._region_end(start_ref)
        option_hits = {}
        if start_ref:
            labels = tuple(t.label for t in targets if t.kind == "option_label" and t.label)
            option_hits = self._locate_options(out, unit_id, labels, start_ref, region_upper)
        for t in targets:
            if t.kind == "question_label":
                self._stem_span(out, unit_id, t, qn, start_ref, option_hits, region_upper)
            elif t.kind == "option_label":
                self._option_span(out, unit_id, t, option_hits)
            else:
                self._span_other(out, unit_id, t)

    def _locate_question_start(self, out, unit_id, t, qn):
        hits = [
            l.line_ref for l in self._question_zone()
            if is_question_start(normalize_text(l.text)) == qn
        ]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            out.add_unresolved(t, "ambiguous", (f"question {qn} start not unique",))
            return None
        out.add_unresolved(t, "missing", (f"question number {qn!r} not found",))
        return None

    def _region_end(self, start_ref: str) -> int | None:
        """题号行后第一个显式区界：下一题号行 或 答案/详解/解析 表头。无 → None。"""
        start_seq = self._idx.seq_of(start_ref)
        for l in self._idx.lines:
            if l.seq <= start_seq:
                continue
            norm = normalize_text(l.text)
            if is_question_start(norm) is not None:
                return l.seq
            if is_answer_header(norm) or is_explanation_header(norm):
                return l.seq
        return None

    def _locate_options(self, out, unit_id, labels, start_ref, region_upper):
        """逐 label 定位：优先行首选项；否则前一个选项行上的 bounded inline（单行多选项）。

        返回 {label: ("ok", ref) | ("inline", ref, start, end) | ("ambiguous",) | ("incomplete",)}。
        重复→ambiguous；完全缺失→incomplete。
        """
        found: dict[str, tuple] = {}
        cursor_seq = self._idx.seq_of(start_ref)
        cursor_ref: str | None = None
        cursor_end = 0
        for lab in labels:
            starts = [
                l for l in self._idx.lines
                if l.seq > cursor_seq
                and (region_upper is None or l.seq < region_upper)
                and lab in option_tokens(normalize_text(l.text), (lab,))
            ]
            if len(starts) == 1:
                found[lab] = ("ok", starts[0].line_ref)
                cursor_seq = starts[0].seq
                cursor_ref = starts[0].line_ref
                cursor_end = 0  # 同行后续标签从行首后任意 offset 找（单行多选项）
                continue
            if len(starts) > 1:
                found[lab] = ("ambiguous",)
                continue
            # 无行首选项：尝试在前一个选项行（同物理行多选项）bounded inline。
            if cursor_ref is not None:
                line = self._idx.get(cursor_ref)
                offs = [o for o in _label_offsets(line.text, lab) if o >= cursor_end]
                if len(offs) == 1:
                    found[lab] = ("inline", cursor_ref, offs[0], offs[0] + len(lab))
                    cursor_end = offs[0] + len(lab)
                    continue
            found[lab] = ("incomplete",)
        return found

    def _stem_span(self, out, unit_id, t, qn, start_ref, option_hits, region_upper):
        if start_ref is None:
            return  # 已由 _locate_question_start 记录 unresolved
        first_option_seq = None
        for lab, entry in option_hits.items():
            if entry[0] == "ok" and entry[1]:
                seq = self._idx.seq_of(entry[1])
                first_option_seq = seq if first_option_seq is None else min(first_option_seq, seq)
        # 显式边界：本 unit 首选项行；否则区界（下一题/表头）。
        boundary_seq = first_option_seq if first_option_seq is not None else region_upper
        if boundary_seq is None:
            out.add_unresolved(
                t, "incomplete",
                ("no explicit end boundary (option/next-question) for stem",),
            )
            return
        start_seq = self._idx.seq_of(start_ref)
        refs = [l.line_ref for l in self._idx.between(start_seq, boundary_seq)]
        if not refs:
            out.add_unresolved(t, "incomplete", ("stem span empty",))
            return
        out.add_span(unit_id, t, refs, "exact",
                     ("stem start", start_ref, "boundary", "option-or-region-end"))

    def _option_span(self, out, unit_id, t, option_hits):
        entry = option_hits.get(t.label or "", ("incomplete",))
        kind = entry[0]
        if kind == "ok":
            out.add_span(unit_id, t, [entry[1]], "exact", (f"option label={t.label}",))
            return
        if kind == "inline":
            out.add_char_span(unit_id, t, entry[1], entry[2], entry[3], "exact",
                              (f"option label={t.label} (inline, line_character)",))
            return
        out.add_unresolved(t, kind if kind in ("ambiguous", "incomplete") else "incomplete",
                           (f"option {t.label}",))

    def _span_other(self, out, unit_id, t):
        if t.kind == "instruction_marker":
            self._material_span(out, unit_id, t)
        elif t.kind == "answer_zone":
            self._answer_span(out, unit_id, t)
        elif t.kind == "explanation_zone":
            self._explanation_span(out, unit_id, t)
        elif t.kind == "image":
            self._image_span(out, unit_id, t)
        elif t.kind == "blank_label":
            self._blank_span(out, unit_id, t)

    def _material_span(self, out, unit_id, t):
        sm = t.start_marker or {}
        em = t.end_marker or {}
        granularity = sm.get("granularity")
        if granularity == "multi_line_pair":
            sq, eq = sm.get("text"), em.get("text")
            if not sq or not eq:
                out.add_unresolved(t, "incomplete",
                                   ("material pair requires start+end marker text",))
                return
            st, s_refs, s_extra = self._resolve_marker_cascade(sq)
            et, e_refs, e_extra = self._resolve_marker_cascade(eq)
            if not _is_resolved(st):
                self._unresolved_marker(out, t, st, "start", sq)
                return
            if not _is_resolved(et):
                self._unresolved_marker(out, t, et, "end", eq)
                return
            s_seq = self._idx.seq_of(s_refs[0])
            e_seq = self._idx.seq_of(e_refs[0])
            if e_seq <= s_seq + 1:
                out.add_unresolved(t, "incomplete",
                                   ("material interior empty (markers adjacent)",))
                return
            # material 正文 = start/end marker **之间**（排他，instruction 行不进材料）。
            refs = [l.line_ref for l in self._idx.between(s_seq + 1, e_seq)]
            status = "exact" if st == "exact" and et == "exact" else \
                ("contextual" if "contextual" in (st, et) else "normalized")
            out.add_span(unit_id, t, refs, status,
                         ("material between markers", sq, "…", eq, *s_extra, *e_extra))
            return
        q = sm.get("text")
        if not q:
            out.add_unresolved(t, "incomplete", ("material marker text missing",))
            return
        status, hits, extra = self._resolve_marker_cascade(q)
        if not _is_resolved(status):
            self._unresolved_marker(out, t, status, "marker", q)
            return
        if granularity == "line_fragment":
            out.add_fragment_span(unit_id, t, hits[0], q, status,
                                  ("material fragment", q, *extra))
            return
        out.add_span(unit_id, t, [hits[0]], status, ("material marker", q, *extra))

    def _unresolved_marker(self, out, t, status, label, query):
        out.add_unresolved(t, status, (f"{label} {query!r} not uniquely located",))

    def _resolve_marker_cascade(self, query: str):
        """marker 文本定位 + contextual 收窄（20 §5.4）。

        contextual 仅允许用确定性 source 边界排除候选（此处=题目区/答案详解区显式表头
        边界），**不得**用文本相似度 / nearest / first-match。机器不变量：
        contextual ⇒ initial>1 ⇒ final==1。
        返回 (status, refs, extra_evidence)。
        """
        status, refs = _locate(query, self._idx)
        if status == "ambiguous":
            in_zone = [r for r in refs if self._idx.seq_of(r) < self._qzone_end]
            if len(in_zone) == 1 and len(refs) > 1:
                extra = tuple(
                    f"excluded {r} (outside question zone)" for r in refs if r not in in_zone
                )
                return "contextual", in_zone, extra
        return status, refs, ()

    def _answer_span(self, out, unit_id, t):
        qn = t.question_number
        if not qn:
            out.add_unresolved(t, "incomplete", ("answer needs question_label",))
            return
        # 答案区：答案表头后、详解/解析表头前的行。qnbounded entry（题号 token+分隔）。
        entries: list[tuple[str, int, int]] = []
        in_zone = False
        for l in self._idx.lines:
            norm = normalize_text(l.text)
            if not in_zone:
                if is_answer_header(norm):
                    in_zone = True
                continue
            if is_explanation_header(norm):
                break
            offs = _entry_offsets(l.text, qn)
            if offs:
                # 同行多题答案：本 qn 切片止于本行下一个任意 qn 条目（或无则行尾）。
                all_off = [m.start() for m in _ENTRY_RE.finditer(l.text)]
                nxt = next((o for o in all_off if o > offs[0]), len(l.text))
                entries.append((l.line_ref, offs[0], nxt))
        if not entries:
            out.add_unresolved(t, "missing", (f"answer row qn={qn} not found",))
            return
        distinct_lines = {e[0] for e in entries}
        if len(distinct_lines) > 1:
            out.add_unresolved(t, "ambiguous",
                               (f"answer row qn={qn} spans multiple lines",))
            return
        line_ref, start, end = entries[0]
        out.add_char_span(unit_id, t, line_ref, start, end, "exact",
                          ("answer zone", t.zone or "", f"qn={qn}"))

    def _explanation_span(self, out, unit_id, t):
        qn = t.question_number
        header_seen = False
        region: list[str] = []
        for l in self._idx.lines:
            norm = normalize_text(l.text)
            if is_explanation_header(norm):
                header_seen = True
                continue
            if not header_seen:
                continue
            if is_explanation_header(norm) or is_answer_header(norm):
                break
            region.append(l.line_ref)
        if not header_seen:
            out.add_unresolved(t, "missing", ("no 详解/解析 header",))
            return
        if not region:
            out.add_unresolved(t, "missing", ("explanation region empty",))
            return
        owned = [
            r for r in region
            if qn is None or is_question_start(normalize_text(self._idx.get(r).text)) == qn
        ]
        if not owned:
            out.add_unresolved(t, "missing", (f"no explanation row for qn={qn}",))
            return
        out.add_span(unit_id, t, owned, "exact", ("explanation", f"qn={qn}"))

    def _image_span(self, out, unit_id, t):
        ok = [
            f for f in self._figures
            if f.page_no is not None and f.bbox and f.placement and f.source
        ]
        if not ok:
            out.add_unresolved(t, "ambiguous", ("no IS-7-complete figure",))
            return
        fid = (t.image_ref or {}).get("figure_id")
        cands = [f for f in ok if fid is None or f.figure_id == fid]
        if not cands:
            out.add_unresolved(t, "missing", (f"figure {fid} not found",))
        elif len(cands) > 1:
            out.add_unresolved(t, "ambiguous", ("multiple figures",))
        else:
            f = cands[0]
            page_lines = [l.line_ref for l in self._idx.lines if l.page_no == f.page_no]
            if not page_lines:
                out.add_unresolved(t, "ambiguous", ("figure page has no lines",))
                return
            out.add_span(unit_id, t, page_lines, "exact",
                         ("image figure", f.figure_id, f"page={f.page_no}"), role_hint="image")

    def _blank_span(self, out, unit_id, t):
        # blank 须闭合到 sub_question/answer（§5.3）；M1 annotation 无闭合声明 →
        # incomplete（回 Annotation，段 F 不凭空造闭合）。
        out.add_unresolved(
            t, "incomplete",
            ("blank requires sub_question/answer closure (deferred to 段 F)",),
        )

    # ------------------------------------------------------------------ relations
    def _enforce_material_overlap(self, out: _Out) -> None:
        """E owns source-span overlap validation（20 §5.3 material + §5.5）。

        material span 与任何非 material resolved span、或其他 material span 共享行
        → material 不得 resolved（demote 为 incomplete unresolved，避免污染 F 输入）。
        """
        mats = [s for s in out.resolved if s.role in _MATERIAL_ROLES]
        if not mats:
            return
        non_mats = [s for s in out.resolved if s.role not in _MATERIAL_ROLES]
        for m in list(mats):
            mrefs = frozenset(m.line_refs)
            conflicts = []
            for o in non_mats:
                if frozenset(o.line_refs) & mrefs:
                    conflicts.append(
                        f"overlaps {o.role} span {o.span_id} ({o.line_refs[0]}..{o.line_refs[-1]})"
                    )
            for m2 in mats:
                if m2.span_id != m.span_id and frozenset(m2.line_refs) & mrefs:
                    conflicts.append(f"overlaps material {m2.span_id}")
            if not conflicts:
                continue
            out.resolved.remove(m)
            out.unresolved.append(
                UnresolvedReference(
                    reference_id=m.span_id[3:] if m.span_id.startswith("sp-") else m.span_id,
                    role=m.role, resolution_status="incomplete",
                    evidence=tuple(conflicts) + ("material overlap → unresolved",),
                )
            )

    def _resolve_relations(self, out: _Out, rel_decls):
        span_id_to_span = {s.span_id: s for s in out.resolved}
        result: list[ResolvedRelation] = []
        for rel in rel_decls:
            target_span = span_id_to_span.get(f"sp-{rel.target_unit_id}")
            result.append(
                ResolvedRelation(
                    relation_id=f"{rel.source_unit_id}->{rel.target_unit_id}",
                    source_span_id=f"sp-{rel.source_unit_id}",
                    target_unit_ref=rel.target_unit_id,
                    relation_type=rel.relation_type,
                    resolved_target_span_id=target_span.span_id if target_span else None,
                    status="resolved" if target_span else "unresolved",
                )
            )
        return result
