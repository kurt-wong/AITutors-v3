"""Resolver Diagnostic Layer（Phase I-2C-2）：结构化诊断 unresolved references。

职责：对 ResolvedRun 中的 unresolved 做结构化分析，回答"为什么失败"。
不改变 resolution 算法，只提供可观测性。

诊断维度：
- attempts: 每个匹配方法（exact/normalized/fuzzy）的尝试结果
- candidate_lines: 与 marker 部分匹配的候选行
- classification: unresolved 原因分类

纯函数，无 IO，确定性。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domains.resolver.match_normalization import normalize_text
from app.domains.resolver.span import (
    ResolvedRun,
    SourceLineView,
    UnresolvedReference,
)


@dataclass(frozen=True)
class MatchAttempt:
    """一次匹配尝试的结果。"""

    method: str  # exact / normalized / fuzzy
    result: str  # found / not_found / multiple_matches
    hit_count: int
    hits: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CandidateLine:
    """与 marker 部分匹配的候选行。"""

    line_ref: str
    text: str
    match_type: str  # partial / token / fuzzy
    matched_chars: int


@dataclass(frozen=True)
class UnresolvedDiagnostic:
    """单个 unresolved reference 的结构化诊断。"""

    reference_id: str
    role: str
    status: str
    evidence: tuple[str, ...]
    attempts: tuple[MatchAttempt, ...]
    candidate_lines: tuple[CandidateLine, ...]
    classification: str


@dataclass(frozen=True)
class DiagnosticReport:
    """一次诊断的完整报告。"""

    source_version_id: uuid.UUID
    total_unresolved: int
    by_classification: dict[str, int]
    by_role: dict[str, int]
    diagnostics: tuple[UnresolvedDiagnostic, ...]


def classify_unresolved(
    ref: UnresolvedReference,
    attempts: tuple[MatchAttempt, ...],
    candidates: tuple[CandidateLine, ...],
) -> str:
    """分类 unresolved 原因。

    分类规则（基于 attempts 和 candidates 的确定性推断）：
    - marker_not_found: 所有方法都 not_found，无候选行
    - marker_fragmented: 所有方法 not_found，但有 partial 候选行（数学公式拆行）
    - marker_ambiguous: exact/normalized 返回 multiple_matches
    - marker_fuzzy_only: 只有 fuzzy 找到（低置信度）
    - grammar_mismatch: evidence 含 grammar 相关关键词
    - unknown: 无法分类
    """
    # 检查 evidence 中的 grammar 关键词
    evidence_text = " ".join(ref.evidence).lower()
    if "header" in evidence_text or "grammar" in evidence_text:
        return "grammar_mismatch"

    # 检查 attempts 结果
    exact_result = next((a for a in attempts if a.method == "exact"), None)
    norm_result = next((a for a in attempts if a.method == "normalized"), None)
    fuzzy_result = next((a for a in attempts if a.method == "fuzzy"), None)

    # exact 或 normalized 返回 multiple → ambiguous
    if (exact_result and exact_result.result == "multiple_matches") or \
       (norm_result and norm_result.result == "multiple_matches"):
        return "marker_ambiguous"

    # 所有方法 not_found
    all_not_found = all(a.result == "not_found" for a in attempts)
    if all_not_found:
        if candidates:
            return "marker_fragmented"  # 有部分匹配候选 → 可能是拆行
        return "marker_not_found"

    # 只有 fuzzy 找到
    if fuzzy_result and fuzzy_result.result == "found":
        if (exact_result and exact_result.result == "not_found") and \
           (norm_result and norm_result.result == "not_found"):
            return "marker_fuzzy_only"

    return "unknown"


def _find_candidate_lines(
    marker: str,
    lines: tuple[SourceLineView, ...],
    max_candidates: int = 10,
) -> tuple[CandidateLine, ...]:
    """查找与 marker 部分匹配的候选行。

    策略：
    1. 按字符重叠率排序
    2. 只返回重叠率 > 30% 的行
    3. 限制数量
    """
    if not marker:
        return ()

    norm_marker = normalize_text(marker)
    marker_chars = set(norm_marker.replace(" ", ""))
    if not marker_chars:
        return ()

    candidates: list[CandidateLine] = []
    for line in lines:
        norm_line = normalize_text(line.text)
        line_chars = set(norm_line.replace(" ", ""))

        # 计算字符重叠率
        overlap = marker_chars & line_chars
        if not overlap:
            continue

        overlap_ratio = len(overlap) / len(marker_chars)
        if overlap_ratio < 0.3:
            continue

        # 判断匹配类型
        if norm_marker in norm_line:
            match_type = "partial"
        elif any(token in norm_line for token in norm_marker.split()):
            match_type = "token"
        else:
            match_type = "fuzzy"

        candidates.append(CandidateLine(
            line_ref=line.line_ref,
            text=line.text[:100],  # 截断避免过长
            match_type=match_type,
            matched_chars=len(overlap),
        ))

    # 按重叠字符数降序排序
    candidates.sort(key=lambda c: c.matched_chars, reverse=True)
    return tuple(candidates[:max_candidates])


def _attempt_match(
    marker: str,
    lines: tuple[SourceLineView, ...],
) -> tuple[MatchAttempt, ...]:
    """尝试三种匹配方法，记录结果。"""
    attempts: list[MatchAttempt] = []

    # exact
    exact_hits = tuple(l.line_ref for l in lines if marker in l.text)
    if len(exact_hits) == 1:
        attempts.append(MatchAttempt("exact", "found", 1, exact_hits))
    elif len(exact_hits) > 1:
        attempts.append(MatchAttempt("exact", "multiple_matches", len(exact_hits), exact_hits))
    else:
        attempts.append(MatchAttempt("exact", "not_found", 0))

    # normalized
    norm_marker = normalize_text(marker)
    norm_hits = tuple(
        l.line_ref for l in lines if norm_marker in normalize_text(l.text)
    )
    if len(norm_hits) == 1:
        attempts.append(MatchAttempt("normalized", "found", 1, norm_hits))
    elif len(norm_hits) > 1:
        attempts.append(MatchAttempt("normalized", "multiple_matches", len(norm_hits), norm_hits))
    else:
        attempts.append(MatchAttempt("normalized", "not_found", 0))

    # fuzzy (flatten whitespace)
    flat_marker = norm_marker.replace(" ", "")
    fuzzy_hits = tuple(
        l.line_ref for l in lines
        if normalize_text(l.text).replace(" ", "") == flat_marker
    )
    if len(fuzzy_hits) == 1:
        attempts.append(MatchAttempt("fuzzy", "found", 1, fuzzy_hits))
    elif len(fuzzy_hits) > 1:
        attempts.append(MatchAttempt("fuzzy", "multiple_matches", len(fuzzy_hits), fuzzy_hits))
    else:
        attempts.append(MatchAttempt("fuzzy", "not_found", 0))

    return tuple(attempts)


def diagnose_unresolved(
    resolved_run: ResolvedRun,
    lines: tuple[SourceLineView, ...],
    annotation_payload: dict | None = None,
) -> DiagnosticReport:
    """对 ResolvedRun 中的 unresolved 做结构化诊断。

    Args:
        resolved_run: Resolver 的输出
        lines: 源行视图
        annotation_payload: 可选，用于提取 marker 信息

    Returns:
        DiagnosticReport: 结构化诊断报告
    """
    diagnostics: list[UnresolvedDiagnostic] = []

    for ref in resolved_run.unresolved_references:
        # 从 annotation_payload 提取 marker（如果可用）
        marker = _extract_marker_for_reference(ref, annotation_payload)

        # 尝试匹配
        attempts = _attempt_match(marker, lines) if marker else ()

        # 查找候选行
        candidates = _find_candidate_lines(marker, lines) if marker else ()

        # 分类
        classification = classify_unresolved(ref, attempts, candidates)

        diagnostics.append(UnresolvedDiagnostic(
            reference_id=ref.reference_id,
            role=ref.role,
            status=ref.resolution_status,
            evidence=ref.evidence,
            attempts=attempts,
            candidate_lines=candidates,
            classification=classification,
        ))

    # 统计
    by_classification: dict[str, int] = {}
    by_role: dict[str, int] = {}
    for d in diagnostics:
        by_classification[d.classification] = by_classification.get(d.classification, 0) + 1
        by_role[d.role] = by_role.get(d.role, 0) + 1

    return DiagnosticReport(
        source_version_id=resolved_run.source_version_id,
        total_unresolved=len(diagnostics),
        by_classification=by_classification,
        by_role=by_role,
        diagnostics=tuple(diagnostics),
    )


def _extract_marker_for_reference(
    ref: UnresolvedReference,
    annotation_payload: dict | None,
) -> str:
    """从 annotation_payload 中提取对应的 marker 文本。

    如果找不到，返回空字符串。
    """
    if not annotation_payload:
        return ""

    # 遍历 semantic_units 查找匹配的 reference
    for unit in annotation_payload.get("semantic_units", []):
        content = unit.get("content", {})
        for role_key, role_data in content.items():
            if isinstance(role_data, dict):
                # stem/option 等
                if role_data.get("question_label") == ref.reference_id:
                    return role_data.get("text", "")
            elif isinstance(role_data, list):
                # options/answers 等
                for item in role_data:
                    if isinstance(item, dict) and item.get("question_label") == ref.reference_id:
                        return item.get("text", "")

    return ""


def format_diagnostic_report(report: DiagnosticReport) -> dict:
    """将 DiagnosticReport 转换为可序列化的 dict（供 API/CLI 输出）。"""
    return {
        "source_version_id": str(report.source_version_id),
        "total_unresolved": report.total_unresolved,
        "by_classification": report.by_classification,
        "by_role": report.by_role,
        "diagnostics": [
            {
                "reference_id": d.reference_id,
                "role": d.role,
                "status": d.status,
                "evidence": list(d.evidence),
                "attempts": [
                    {
                        "method": a.method,
                        "result": a.result,
                        "hit_count": a.hit_count,
                        "hits": list(a.hits),
                    }
                    for a in d.attempts
                ],
                "candidate_lines": [
                    {
                        "line_ref": c.line_ref,
                        "text": c.text,
                        "match_type": c.match_type,
                        "matched_chars": c.matched_chars,
                    }
                    for c in d.candidate_lines
                ],
                "classification": d.classification,
            }
            for d in report.diagnostics
        ],
    }
