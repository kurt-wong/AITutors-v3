"""Deterministic Compiler（段 F，F5-F6，20 §7）。IR(ready) → CompiledSnapshot（transient）。

Compiler 只消费通过不变量校验（semantic_status=ready）的 IR；只从
ResolvedSpan.line_refs → SourceLineView.text slice 取正文（不补推、不猜、不归一化展示）。

红线：identity_normalization 只用于三 key，不用于 compiled text；text_hash raw（2c/2d）
绝不经 canonical JSON（BUG-V3-017）；未知 canonical type 不 guess（BUG-V3-014）。
"""

from __future__ import annotations

import hashlib
import uuid

from app.domains.compile import map_canonical_type
from app.domains.compile.identity_normalization import (
    canonical_options_input,
    identity_hash,
    normalize_identity,
    strip_option_label,
)
from app.domains.compile.ir import IR, IRNode
from app.domains.compile.snapshot import (
    CompiledAnswer,
    CompiledLeaf,
    CompiledMaterial,
    CompiledRole,
    CompiledSnapshot,
)
from app.domains.resolver.span import ResolvedSpan


def _raw_sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _slice_span(span: ResolvedSpan, line_by_ref: dict) -> str:
    """从权威正文 slice（BUG-V3-012 跨行拼接规则与段 E 一致）。"""
    if (
        span.granularity == "line_character"
        and span.start_offset is not None
        and span.end_offset is not None
        and len(span.line_refs) == 1
    ):
        return line_by_ref[span.line_refs[0]].text[span.start_offset : span.end_offset]
    return "\n".join(line_by_ref[r].text for r in span.line_refs)


class Compiler:
    def __init__(
        self,
        span_by_id: dict[str, ResolvedSpan],
        line_by_ref: dict,
    ):
        self._span_by_id = span_by_id
        self._line_by_ref = line_by_ref

    def compile(self, ir: IR) -> CompiledSnapshot:
        """只编译 ready node；incomplete/composite-not-ready 一律不产 leaves。"""
        leaves: list[CompiledLeaf] = []
        materials: list[CompiledMaterial] = []
        for node in ir.units:
            self._compile_node(node, leaves, materials)
        return CompiledSnapshot(
            source_version_id=ir.source_version_id,
            annotation_id=ir.annotation_id,
            leaves=tuple(leaves),
            materials=tuple(materials),
        )

    def _compile_node(self, node: IRNode, leaves, materials) -> None:
        if node.semantic_status != "ready":
            return  # invariant 8：非 ready 不编译
        if node.unit_type == "composite_unit":
            for sc in node.shared_components:
                if sc.span_id:
                    mat = self._compile_material(node, sc)
                    if mat:
                        materials.append(mat)
            for sub in node.sub_questions:
                if sub.semantic_status == "ready":
                    leaf = self._compile_leaf(sub)
                    if leaf:
                        leaves.append(leaf)
            return
        leaf = self._compile_leaf(node)
        if leaf:
            leaves.append(leaf)

    def _role_by(self, node: IRNode, role: str):
        return next((c for c in node.content if c.role == role), None)

    def _compile_role(self, role: str, label: str | None, span_id: str) -> CompiledRole:
        span = self._span_by_id.get(span_id)
        if span is None:
            # 确定性拒绝：IR 引用的 span 不在 ResolvedRun 中（装配错误 / 悬空 span_id）
            raise ValueError(
                f"compiled role {role!r} references unknown span_id {span_id!r} "
                f"(not in ResolvedRun); refuse to materialize"
            )
        text = _slice_span(span, self._line_by_ref)
        return CompiledRole(
            role=role, span_id=span_id, line_refs=tuple(span.line_refs),
            text=text, text_hash=_raw_sha256(text), label=label,
        )

    def _compile_material(self, node: IRNode, sc):
        span = self._span_by_id.get(sc.span_id)
        if span is None:
            raise ValueError(
                f"material {sc.role!r} references unknown span_id {sc.span_id!r} "
                f"(not in ResolvedRun); refuse to materialize"
            )
        text = _slice_span(span, self._line_by_ref)
        dedup = identity_hash({"material_type": sc.role, "text": normalize_identity(text)})
        return CompiledMaterial(
            unit_id=node.unit_id, role=sc.role, span_id=sc.span_id,
            text=text, text_hash=_raw_sha256(text), dedup_key=dedup,
        )

    def _compile_leaf(self, node: IRNode) -> CompiledLeaf | None:
        canonical = map_canonical_type(node.original_question_type) if node.original_question_type else None
        if canonical is None:
            return None  # ready 不该发生；防御
        stem_item = self._role_by(node, "stem")
        if stem_item is None or stem_item.span_id is None:
            return None
        stem = self._compile_role("stem", None, stem_item.span_id)
        opt_items = [c for c in node.content if c.role == "option"]
        opts = tuple(
            self._compile_role("option", c.label, c.span_id)
            for c in opt_items if c.span_id
        )
        ans_item = self._role_by(node, "answer")
        answer = None
        if ans_item is not None and ans_item.span_id:
            cr = self._compile_role("answer", None, ans_item.span_id)
            answer = CompiledAnswer(
                span_id=cr.span_id, line_refs=cr.line_refs, text=cr.text,
                text_hash=cr.text_hash, source_located=True,
                complete=bool(cr.text.strip()), verified_correct=None,
            )
        expl_item = self._role_by(node, "explanation")
        explanation = None
        if expl_item is not None and expl_item.span_id:
            explanation = self._compile_role("explanation", None, expl_item.span_id)
        qn = node.question_number or ""
        dedup = self._question_dedup_key(canonical, stem, opts)
        occ = self._occurrence_key(node.unit_id, qn, stem_item.span_id)
        return CompiledLeaf(
            unit_id=node.unit_id, question_number=qn,
            canonical_question_type=canonical, stem=stem, options=opts,
            answer=answer, explanation=explanation,
            dedup_key=dedup, occurrence_key=occ,
        )

    def _question_dedup_key(self, canonical: str, stem: CompiledRole, opts: tuple) -> str:
        """Question dedup_key（20 §7.3）：canonical type + own stem + own options
        （options 按 canonical label order 排序，声明序无关，BUG-V3-019）。

        不含 shared material / answer / explanation / question no. / source_version / unit_id。
        """
        labeled = [
            (o.label, normalize_identity(strip_option_label(o.text)))
            for o in opts if o.label
        ]
        options_input = canonical_options_input(labeled)
        return identity_hash(
            {
                "canonical_question_type": canonical,
                "stem": normalize_identity(stem.text),
                "options": options_input,
            }
        )

    def _occurrence_key(self, unit_id: str, qn: str, stem_span_id: str) -> str:
        """occurrence_key（20 §7.3）：unit_id + question_number + resolved stem span。

        document-local；不含 question_id；unit_id 须来自 annotation（不得 UUID/random 生成）。
        """
        span = self._span_by_id[stem_span_id]
        stem_refs = list(span.line_refs)
        offsets = (
            [span.start_offset, span.end_offset]
            if span.granularity == "line_character" else None
        )
        return identity_hash(
            {
                "unit_id": unit_id,
                "question_number": qn,
                "stem_refs": stem_refs,
                "stem_offsets": offsets,
            }
        )
