"""Resolver 输入视图与输出 dataclass（段 E，20 §5.5）。

输入视图为轻量 frozen 类型，避免 Domain 依赖 ORM（00 §3）。lines/figures 由上游
Application 从 Repository 读出后转成这些视图传给纯函数 resolve()。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceLineView:
    """sealed source 一行的轻量视图（line_ref 已冻结 P{page}L{line:03d}）。"""

    line_ref: str
    text: str
    seq: int
    page_no: int = 0
    line_no_in_page: int = 0


@dataclass(frozen=True)
class SourceFigureView:
    """source_figures 一行的轻量视图。IS-7 要求 page/bbox/placement/source 齐全。"""

    figure_id: str
    page_no: int
    bbox: dict
    placement: str
    source: str
    object_key: str
    figure_hash: str


@dataclass(frozen=True)
class ResolvedSpan:
    """20 §5.5 Resolved Span。只有 status ∈ RESOLVED_STATUSES 才实例化。"""

    span_id: str
    source_version_id: uuid.UUID
    role: str
    start_line_ref: str
    end_line_ref: str
    line_refs: tuple[str, ...]
    granularity: str
    start_offset: int | None
    end_offset: int | None
    text_hash: str
    resolution_status: str
    evidence: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class UnresolvedReference:
    """未能产生 ResolvedSpan 的 reference（fuzzy/ambiguous/missing/incomplete）。

    保留状态与证据，供 F/G 区分 pending_review（fuzzy/ambiguous/missing）与
    annotation_retry（incomplete，20 §5.2/§4.7）。
    """

    reference_id: str
    role: str
    resolution_status: str
    evidence: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ResolvedRelation:
    """20 §5.5 Resolved Relation：dependency target → 已解析 material span。"""

    relation_id: str
    source_span_id: str
    target_unit_ref: str
    relation_type: str
    resolved_target_span_id: str | None
    status: str  # resolved / unresolved


@dataclass(frozen=True)
class ResolvedRun:
    """Resolver 一次执行的 transient 输出（四象限分离，保留 unresolved 证据）。

    20 §5.5 未冻结 ResolvedRun 结构 → 本结构为段 E 实现选择（不扩大公开契约，
    内部四象限信息供 F IR 组装与 G 决策）。
    """

    source_version_id: uuid.UUID
    resolved_spans: tuple[ResolvedSpan, ...] = field(default_factory=tuple)
    unresolved_references: tuple[UnresolvedReference, ...] = field(default_factory=tuple)
    resolved_relations: tuple[ResolvedRelation, ...] = field(default_factory=tuple)
    unresolved_relations: tuple[ResolvedRelation, ...] = field(default_factory=tuple)
