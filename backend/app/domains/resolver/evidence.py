"""Phase I-4: Evidence-aware diagnostic 层。

输入 SourceLine + SourceSpan，输出 candidate evidence 排名。
**不修改 SourceResolver**——这是独立的分析层，用于评估 SourceSpan evidence
是否能降低 marker_ambiguous。

架构护栏（63_ARCHITECTURE_COMPLEXITY_GUARDRAILS.md §5-6）：
- Source Layer 只保存 evidence，不做 semantic interpretation
- Resolver 修改前必须完成 Evidence Utilization Gate（Before/After 对比）
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domains.resolver.match_normalization import normalize_text
from app.domains.resolver.span import SourceLineView

# 评分权重常量（Phase I-4）。未来调整须通过 §6 Evidence Utilization Gate（Before/After 对比）。
_WEIGHT_ISOLATED_SPAN = 0.3
_WEIGHT_FEW_SPANS = 0.1
_WEIGHT_SMALL_BBOX = 0.15
_WEIGHT_BOLD = 0.1
_WEIGHT_EXACT_TEXT_MATCH = 0.35
_WEIGHT_STARTS_WITH_MARKER = 0.15
_SMALL_BBOX_THRESHOLD = 500.0  # 经验阈值：面积 < 500 视为小 bbox
_FEW_SPANS_THRESHOLD = 2  # span 数 ≤ 2 视为少
_UNIQUE_GAP_THRESHOLD = 0.2  # top 与 second 分差 > 0.2 视为唯一


@dataclass(frozen=True)
class SpanEvidence:
    """一行内一个 span 的 evidence 视图（从 DB 读回）。"""

    line_ref: str
    seq: int  # span 在行内的顺序
    text: str
    font: str | None = None
    size: float | None = None
    flags: int | None = None
    bbox: dict | None = None
    origin: dict | None = None

    @property
    def is_bold(self) -> bool:
        return bool(self.flags and self.flags & 32)

    @property
    def is_superscript(self) -> bool:
        return bool(self.flags and self.flags & 1)

    @property
    def is_subscript(self) -> bool:
        return bool(self.flags and self.flags & 2)

    @property
    def bbox_area(self) -> float | None:
        if not self.bbox:
            return None
        x0 = self.bbox.get("x0")
        y0 = self.bbox.get("y0")
        x1 = self.bbox.get("x1")
        y1 = self.bbox.get("y1")
        if None in (x0, y0, x1, y1):
            return None
        return abs(x1 - x0) * abs(y1 - y0)


@dataclass(frozen=True)
class EvidenceCandidate:
    """一个 marker 候选位置的 evidence 评分。"""

    line_ref: str
    line_seq: int
    line_text: str
    match_method: str  # exact / normalized
    # Span-level evidence
    span_count: int
    dominant_font: str | None
    dominant_size: float | None
    is_bold: bool
    is_isolated: bool  # 该行是否只有这一个 span（题号通常是独立 span）
    bbox_area: float | None  # 面积越小越可能是孤立题号
    # Scoring
    evidence_score: float  # 0.0 - 1.0
    score_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceReport:
    """单个 unresolved reference 的 evidence 分析。"""

    reference_id: str
    marker: str
    total_candidates: int
    candidates: tuple[EvidenceCandidate, ...]  # 按 evidence_score 降序
    top_candidate: EvidenceCandidate | None
    unique_with_evidence: bool  # evidence 是否能唯一确定


def _dominant_font(spans: tuple[SpanEvidence, ...]) -> str | None:
    """返回出现次数最多的 font。"""
    if not spans:
        return None
    fonts: dict[str, int] = {}
    for s in spans:
        if s.font:
            fonts[s.font] = fonts.get(s.font, 0) + 1
    if not fonts:
        return None
    return max(fonts, key=fonts.get)  # type: ignore[arg-type]


def _dominant_size(spans: tuple[SpanEvidence, ...]) -> float | None:
    """返回出现次数最多的 size。"""
    if not spans:
        return None
    sizes: dict[float, int] = {}
    for s in spans:
        if s.size is not None:
            sizes[s.size] = sizes.get(s.size, 0) + 1
    if not sizes:
        return None
    return max(sizes, key=sizes.get)  # type: ignore[arg-type]


def score_candidate(
    line: SourceLineView,
    spans: tuple[SpanEvidence, ...],
    marker: str,
    match_method: str,
) -> EvidenceCandidate:
    """给一个 candidate line 打 evidence 分。

    评分因素（基于 layout evidence，非 semantic interpretation）：
    1. is_isolated: 行内只有 1 个 span → 孤立题号可能性高
    2. span_count: span 越少越可能是简单题号行
    3. bbox_area: 面积小 → 短文本/孤立标记
    4. is_bold: 粗体 → 题号常见样式
    5. marker 精确匹配: line text 精确等于 marker → 高分
    """
    score = 0.0
    reasons: list[str] = []

    # 因素 1: 孤立 span（行内只有 1 个 span）
    is_isolated = len(spans) == 1
    if is_isolated:
        score += _WEIGHT_ISOLATED_SPAN
        reasons.append("isolated_span")

    # 因素 2: span count 越少越好
    span_count = len(spans)
    if span_count <= _FEW_SPANS_THRESHOLD:
        score += _WEIGHT_FEW_SPANS
        reasons.append("few_spans")

    # 因素 3: bbox 面积小
    bbox_area = None
    if spans:
        areas = [s.bbox_area for s in spans if s.bbox_area is not None]
        if areas:
            bbox_area = min(areas)
            if bbox_area < _SMALL_BBOX_THRESHOLD:
                score += _WEIGHT_SMALL_BBOX
                reasons.append("small_bbox")

    # 因素 4: 粗体
    is_bold = any(s.is_bold for s in spans)
    if is_bold:
        score += _WEIGHT_BOLD
        reasons.append("bold")

    # 因素 5: line text 精确等于 marker（或 marker 加标点）
    line_text_stripped = line.text.strip()
    marker_stripped = marker.strip()
    if line_text_stripped == marker_stripped:
        score += _WEIGHT_EXACT_TEXT_MATCH
        reasons.append("exact_text_match")
    elif line_text_stripped.startswith(marker_stripped):
        score += _WEIGHT_STARTS_WITH_MARKER
        reasons.append("starts_with_marker")

    return EvidenceCandidate(
        line_ref=line.line_ref,
        line_seq=line.seq,
        line_text=line.text[:200],  # 截断
        match_method=match_method,
        span_count=span_count,
        dominant_font=_dominant_font(spans),
        dominant_size=_dominant_size(spans),
        is_bold=is_bold,
        is_isolated=is_isolated,
        bbox_area=bbox_area,
        evidence_score=min(score, 1.0),
        score_reasons=tuple(reasons),
    )


def _find_matching_lines(
    marker: str,
    lines: tuple[SourceLineView, ...],
) -> list[tuple[SourceLineView, str]]:
    """找到所有包含 marker 的行，返回 (line, match_method) 列表。"""
    results: list[tuple[SourceLineView, str]] = []
    marker_norm = normalize_text(marker)
    for line in lines:
        # exact match
        if marker in line.text:
            results.append((line, "exact"))
            continue
        # normalized match
        if marker_norm and marker_norm in normalize_text(line.text):
            results.append((line, "normalized"))
    return results


def analyze_evidence(
    reference_id: str,
    marker: str,
    lines: tuple[SourceLineView, ...],
    spans_by_line: dict[str, tuple[SpanEvidence, ...]],
) -> EvidenceReport:
    """对一个 unresolved reference 做 evidence-aware candidate 分析。

    流程：
    1. 找到所有包含 marker 的行（exact + normalized）
    2. 对每个候选行，获取其 spans
    3. 计算 evidence score
    4. 按 score 降序排列
    5. 判断 evidence 是否能唯一确定
    """
    matching = _find_matching_lines(marker, lines)

    candidates: list[EvidenceCandidate] = []
    for line, method in matching:
        spans = spans_by_line.get(line.line_ref, ())
        candidate = score_candidate(line, spans, marker, method)
        candidates.append(candidate)

    # 按 evidence_score 降序排列，同分按 line_seq 升序（稳定）
    candidates.sort(key=lambda c: (-c.evidence_score, c.line_seq))

    top = candidates[0] if candidates else None

    # 判断 evidence 是否能唯一确定：
    # top candidate 的 score 显著高于第二名（差距 > 0.2）
    unique_with_evidence = False
    if len(candidates) == 1:
        unique_with_evidence = True
    elif len(candidates) >= 2:
        gap = candidates[0].evidence_score - candidates[1].evidence_score
        unique_with_evidence = gap > _UNIQUE_GAP_THRESHOLD

    return EvidenceReport(
        reference_id=reference_id,
        marker=marker,
        total_candidates=len(candidates),
        candidates=tuple(candidates),
        top_candidate=top,
        unique_with_evidence=unique_with_evidence,
    )


def format_evidence_report(report: EvidenceReport) -> dict:
    """序列化 EvidenceReport 为 JSON-compatible dict。"""
    return {
        "reference_id": report.reference_id,
        "marker": report.marker,
        "total_candidates": report.total_candidates,
        "unique_with_evidence": report.unique_with_evidence,
        "top_candidate": (
            {
                "line_ref": report.top_candidate.line_ref,
                "line_seq": report.top_candidate.line_seq,
                "line_text": report.top_candidate.line_text[:100],
                "evidence_score": report.top_candidate.evidence_score,
                "score_reasons": list(report.top_candidate.score_reasons),
                "is_isolated": report.top_candidate.is_isolated,
                "span_count": report.top_candidate.span_count,
                "is_bold": report.top_candidate.is_bold,
            }
            if report.top_candidate
            else None
        ),
        "candidates": [
            {
                "line_ref": c.line_ref,
                "line_seq": c.line_seq,
                "line_text": c.line_text[:100],
                "match_method": c.match_method,
                "evidence_score": c.evidence_score,
                "score_reasons": list(c.score_reasons),
                "is_isolated": c.is_isolated,
                "span_count": c.span_count,
                "is_bold": c.is_bold,
                "dominant_font": c.dominant_font,
                "dominant_size": c.dominant_size,
            }
            for c in report.candidates
        ],
    }
