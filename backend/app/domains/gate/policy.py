"""GatePolicy — 四层 Gate 判定（段 G，20 §8.1 / 20 §8.2，纯函数）。

一次 evaluate 判定 **一个 candidate = 一个 top-level unit**（10 §5.2 单数 + 20 §8.5
composite 原子性；plan D6）。consumed 输入为 E 的 ResolvedRun（持有 resolution_status，
D1——F 的 CompiledSnapshot 不含它）+ F 的 IR 与 CompiledSnapshot。Gate 只产 pass/fail +
reasons（gate_decision dict），**不写 decision_status、不修改 payload、不物化**（P0-G-001
enforcement 语义，application-level）。

decision 值域（20 §8.2 + P0-G-002）：
- rejected    = terminal，结构/语义明确矛盾或证据不成立 → approve() 必拒。
- pending_review = 非矛盾但未达 auto（grammar None / contextual / 非开放题型等）→ 人工。
- auto_approve = 前三层过 + 全部 answer 达 strict-auto grammar → 可自动 approve。
incomplete 输入在 Gate 前已截断（service 职责，不产 candidate），本模块防御性仍判 fail。
"""

from __future__ import annotations

import hashlib

from app.domains.compile import CANONICAL_TYPES
from app.domains.compile.ir import IR, IRNode
from app.domains.compile.snapshot import CompiledLeaf, CompiledMaterial, CompiledSnapshot
from app.domains.gate import GATE_POLICY_VERSION, STRICT_AUTO_TYPES
from app.domains.gate.grammar import verify
from app.domains.resolver.span import ResolvedRun, ResolvedSpan

# D1：自动 approve 的 span resolution 白名单（20 §8.2「所有 content role 的 span
# resolution ∈ {exact, normalized}」）。
_AUTO_RESOLUTIONS = frozenset({"exact", "normalized"})


def leaf_unit_ids(root: IRNode) -> frozenset[str]:
    """candidate 树内应产 CompiledLeaf 的 unit_id 集合（20 §6.1 leaf；composite 递归）。

    standalone root → 自身；composite root → 全部非 composite 子孙（嵌套递归）。
    """
    ids: set[str] = set()

    def walk(n: IRNode) -> None:
        if n.unit_type == "composite_unit":
            for s in n.sub_questions:
                walk(s)
        else:
            ids.add(n.unit_id)

    walk(root)
    return frozenset(ids)


def partition_candidate(
    root: IRNode, compiled: CompiledSnapshot
) -> tuple[tuple[CompiledLeaf, ...], tuple[CompiledMaterial, ...]]:
    """从整份 CompiledSnapshot 过滤出该 candidate（root）相关的 leaves/materials。

    - standalone → 自身 unit_id 的 leaf；materials 空。
    - composite  → 子题 leaves + root 名下 materials（shared component，只输出一次，
      不复制进子题，20 #4）。
    """
    want = leaf_unit_ids(root)
    leaves = tuple(l for l in compiled.leaves if l.unit_id in want)
    if root.unit_type == "composite_unit":
        materials = tuple(m for m in compiled.materials if m.unit_id == root.unit_id)
    else:
        materials = ()
    return leaves, materials


def _role_spans(leaf: CompiledLeaf) -> list[tuple[str, str]]:
    """leaf 消费的全部 content role span：(role, span_id)。answer 独立于 roles。"""
    out: list[tuple[str, str]] = []
    if leaf.stem is not None:
        out.append(("stem", leaf.stem.span_id))
    for o in leaf.options:
        out.append(("option", o.span_id))
    if leaf.explanation is not None:
        out.append(("explanation", leaf.explanation.span_id))
    return out


def _raw_sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _layer(status: str, reasons: list[str]) -> dict:
    return {"status": status, "reasons": reasons}


def evaluate(
    *,
    root: IRNode,
    ir: IR,
    compiled: CompiledSnapshot,
    resolved_run: ResolvedRun,
) -> dict:
    """四层 Gate 判定（20 §8.1），返回 gate_decision dict。纯函数；不触 DB。"""
    resolved: dict[str, ResolvedSpan] = {s.span_id: s for s in resolved_run.resolved_spans}

    structural_reasons: list[str] = []
    provenance_reasons: list[str] = []
    semantic_reasons: list[str] = []
    admission_reasons: list[str] = []

    leaves, materials = partition_candidate(root, compiled)

    # ---------------------------------------------------------------- structural
    if root.semantic_status != "ready":
        structural_reasons.append(
            f"unit {root.unit_id!r} semantic_status={root.semantic_status} (not ready)"
        )
    expected = leaf_unit_ids(root)
    if not expected:
        structural_reasons.append(f"unit {root.unit_id!r} has no leaf unit in its tree")
    leaf_by_id = {l.unit_id: l for l in leaves}
    for uid in sorted(expected):
        leaf = leaf_by_id.get(uid)
        if leaf is None:
            structural_reasons.append(f"missing compiled leaf for unit {uid!r}")
            continue
        if leaf.canonical_question_type not in CANONICAL_TYPES:
            structural_reasons.append(
                f"leaf {uid!r} canonical {leaf.canonical_question_type!r} not in CANONICAL_TYPES"
            )
        if leaf.stem is None or not leaf.stem.text.strip():
            structural_reasons.append(f"leaf {uid!r} has no non-empty stem text")
        for role, sid in _role_spans(leaf):
            if sid not in resolved:
                structural_reasons.append(
                    f"leaf {uid!r} role {role!r} span {sid!r} not traceable in ResolvedRun"
                )
        if leaf.answer is not None and leaf.answer.span_id not in resolved:
            structural_reasons.append(
                f"leaf {uid!r} answer span {leaf.answer.span_id!r} not traceable in ResolvedRun"
            )
    structural = _layer("pass" if not structural_reasons else "fail", structural_reasons)

    # ---------------------------------------------------------------- provenance
    # byte-proven：content span 全部 exact/normalized 才可自动（D1 / 20 §8.2）。
    auto_allowed = True
    byte_proven_spans: list[str] = []
    unproven_spans: list[tuple[str, str, str]] = []  # (role, span_id, resolution)
    for leaf in leaves:
        for role, sid in _role_spans(leaf):
            span = resolved.get(sid)
            res = span.resolution_status if span else "missing"
            if res in _AUTO_RESOLUTIONS:
                byte_proven_spans.append(sid)
            else:
                auto_allowed = False
                unproven_spans.append((role, sid, res))
        if leaf.answer is not None:
            sid = leaf.answer.span_id
            span = resolved.get(sid)
            res = span.resolution_status if span else "missing"
            if res in _AUTO_RESOLUTIONS:
                byte_proven_spans.append(sid)
            else:
                auto_allowed = False
                unproven_spans.append(("answer", sid, res))
        # 证据不成立：compiled text_hash 与正文不一致 → 矛盾（rejected）。
        for role, sid, text_hash, text in _compiled_hash_checks(leaf):
            if text_hash != _raw_sha256(text):
                provenance_reasons.append(
                    f"leaf {leaf.unit_id!r} {role} text_hash mismatch (evidence broken)"
                )
    # H-4（BUG-V3-032）：composite shared material 也纳入 provenance 白名单——任一 material
    # resolution ∉ {exact,normalized} → auto_allowed=False（contextual 材料不得自动准入，
    # 20 §8.2「所有 content role 的 span resolution ∈ {exact,normalized}」含 material）。
    for m in materials:
        span = resolved.get(m.span_id)
        res = span.resolution_status if span else "missing"
        if res in _AUTO_RESOLUTIONS:
            byte_proven_spans.append(m.span_id)
        else:
            auto_allowed = False
            unproven_spans.append(("material", m.span_id, res))
    if unproven_spans:
        for role, sid, res in unproven_spans:
            provenance_reasons.append(
                f"span {sid!r} ({role}) resolution={res} not byte-proven; requires manual review"
            )
    # 重复 span 检查：覆盖所有被消费的 content span（含 contextual/fuzzy），
    # 不仅 byte_proven_spans——任一 resolution 的 span 不得被多个 leaf 重复消费。
    all_consumed = byte_proven_spans + [sid for _, sid, _ in unproven_spans]
    if len(set(all_consumed)) != len(all_consumed):
        provenance_reasons.append("duplicate content span consumed across candidate leaves")

    # Source Evidence structural consistency check:
    # answer span must not fall into explanation/question structural regions.
    # Resolver produces structural region map via deterministic header grammar;
    # Gate performs span set intersection (contract self-consistency, NOT NLP).
    # Overlap -> downgrade auto (pending_review), not terminal rejected.
    role_provenance_violations: list[str] = []
    if resolved_run.structural_regions:
        region_by_role: dict[str, set[str]] = {}
        for reg in resolved_run.structural_regions:
            region_by_role.setdefault(reg.role, set()).update(reg.line_refs)
        for leaf in leaves:
            if leaf.answer is None:
                continue
            ans_span = resolved.get(leaf.answer.span_id)
            if ans_span is None:
                continue
            ans_lines = set(ans_span.line_refs)
            for bad_role in ("explanation", "question"):
                bad_lines = region_by_role.get(bad_role, set())
                overlap = ans_lines & bad_lines
                if overlap:
                    auto_allowed = False
                    violation = (
                        f"leaf {leaf.unit_id!r} answer span {leaf.answer.span_id!r} "
                        f"overlaps {bad_role} region at lines {sorted(overlap)[:5]} "
                        f"(role provenance violation)"
                    )
                    provenance_reasons.append(violation)
                    role_provenance_violations.append(violation)

    # provenance 层 fail 仅当证据矛盾（text_hash mismatch）；resolution 非 exact/normalized
    # 只降级 auto（pending），不构成 terminal 矛盾（20 §8.2 contextual 可人工）。
    # role provenance violation 同样只降级 auto（pending_review）。
    hash_broken = any("text_hash mismatch" in r for r in provenance_reasons)
    provenance = _layer(
        "pass" if not hash_broken else "fail",
        provenance_reasons,
    )
    provenance["auto_allowed"] = bool(auto_allowed)

    # ---------------------------------------------------------------- semantic
    # F 已校验不变量 1-8（ready），G 只复核不重判（plan 组件2 / 20 §8.1「语义状态与 IR 一致」）。
    if root.unit_type == "composite_unit":
        if not materials:
            semantic_reasons.append(f"composite {root.unit_id!r} compiled no shared material")
        seen_material_keys: set[str] = set()
        for m in materials:
            if m.dedup_key in seen_material_keys:
                semantic_reasons.append(
                    f"composite material dedup_key {m.dedup_key!r} duplicated (material not unique)"
                )
            seen_material_keys.add(m.dedup_key)
            if m.span_id not in resolved:
                semantic_reasons.append(f"material span {m.span_id!r} not traceable in ResolvedRun")
        if not leaves:
            semantic_reasons.append(f"composite {root.unit_id!r} has no compiled sub-question leaf")
    semantic = _layer("pass" if not semantic_reasons else "fail", semantic_reasons)

    # ---------------------------------------------------------------- admission
    structural_pass = structural["status"] == "pass"
    provenance_pass = provenance["status"] == "pass"
    semantic_pass = semantic["status"] == "pass"
    if not (structural_pass and provenance_pass and semantic_pass):
        # 结构/语义矛盾或证据不成立 → terminal rejected（P0-G-002：approve() 必拒）。
        for r in structural_reasons + semantic_reasons + provenance_reasons:
            admission_reasons.append(r)
        decision = "rejected"
    else:
        # 非矛盾路径：逐 leaf 跑 strict-auto grammar（D2：子题递归，composite 全子题过才过）。
        auto_blockers: list[str] = []
        if not auto_allowed:
            auto_blockers.append("not byte-proven (resolution not in {exact, normalized})")
        # Role-provenance violations surface as explicit auto_blockers.
        for v in role_provenance_violations:
            auto_blockers.append(v)
        for leaf in leaves:
            g = _leaf_grammar(leaf)
            if g is not None:
                ok, why = g
                if not ok:
                    auto_blockers.append(f"leaf {leaf.unit_id!r} answer grammar: {why}")
            else:
                auto_blockers.append(
                    f"leaf {leaf.unit_id!r} type {leaf.canonical_question_type!r} "
                    "not strict-auto (grammar None)"
                )
            if leaf.answer is None or not leaf.answer.source_located or not leaf.answer.complete:
                auto_blockers.append(
                    f"leaf {leaf.unit_id!r} answer not source_located+complete"
                )
        if auto_blockers:
            for b in auto_blockers:
                admission_reasons.append(b)
            decision = "pending_review"
        else:
            admission_reasons.append("strict-auto: all answers verified_correct=true")
            decision = "auto_approve"
    admission = _layer("pass" if decision == "auto_approve" else "fail", admission_reasons)
    admission["decision"] = decision

    return {
        "gate_policy_version": GATE_POLICY_VERSION,
        "decision": decision,
        "layers": {
            "structural": structural,
            "provenance": provenance,
            "semantic": semantic,
            "admission": admission,
        },
        "reasons": admission_reasons,
    }


def _leaf_grammar(leaf: CompiledLeaf) -> tuple[bool, str] | None:
    """单 leaf strict-auto grammar 判定。canonical 不在开放集 → None（pending）。"""
    if leaf.canonical_question_type not in STRICT_AUTO_TYPES:
        return None
    if leaf.answer is None or not leaf.answer.text:
        return False, "no answer text"
    labels = tuple(str(o.label) for o in leaf.options if o.label)
    result = verify(leaf.canonical_question_type, leaf.answer.text, labels)
    if result is True:
        return True, ""
    return False, "answer not expressible as canonical value"


def _compiled_hash_checks(leaf: CompiledLeaf) -> list[tuple[str, str, str, str]]:
    """leaf 全部 compiled text 的 (role, span_id, text_hash, text) 校验元组（含 answer）。"""
    checks: list[tuple[str, str, str, str]] = []
    if leaf.stem is not None:
        checks.append(("stem", leaf.stem.span_id, leaf.stem.text_hash, leaf.stem.text))
    for o in leaf.options:
        checks.append(("option", o.span_id, o.text_hash, o.text))
    if leaf.explanation is not None:
        checks.append(
            ("explanation", leaf.explanation.span_id, leaf.explanation.text_hash, leaf.explanation.text)
        )
    if leaf.answer is not None:
        checks.append(("answer", leaf.answer.span_id, leaf.answer.text_hash, leaf.answer.text))
    return checks
