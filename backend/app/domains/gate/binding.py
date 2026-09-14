"""Annotation–SourceVersion binding validation（BUG-V3-045 / F-3，75 §六.4 no_cross_version）。

annotation.status == valid 只证明 annotation 自身有效，不证明它对当前 source 有效。
Source Version 是 V3 最核心不变量之一——不能跨版本解释。本模块集中验证
annotation ↔ source_version 的绑定关系，供 GateService.run() 及未来 admission 入口复用。
"""

from __future__ import annotations

import uuid

from app.models.snapshot import SemanticAnnotation
from app.models.source import DocumentSourceVersion
from app.repositories.base import RepositoryError
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.source_repository import SourceRepository


async def validate_annotation_binding(
    *,
    source_version_id: uuid.UUID,
    annotation_id: uuid.UUID,
    source_repo: SourceRepository,
    snap_repo: SnapshotRepository,
) -> tuple[DocumentSourceVersion, SemanticAnnotation]:
    """验证 annotation 与 source_version 的绑定关系。

    检查序列（任一失败 → RepositoryError）：
    1. source_version 存在
    2. annotation 存在
    3. annotation.status == "valid"
    4. annotation.source_version_id == source_version_id（F-3 核心，75 §六.4）
    5. source_version.status == "sealed"

    document identity 由 check 4 隐含保证：annotation → source_version → document，
    同一 source_version 必然同一 document。

    返回 (version, annotation)。
    """
    version = await source_repo.get_version(source_version_id)
    if version is None:
        raise RepositoryError(f"source_version {source_version_id} not found")

    ann = await snap_repo.find_annotation_by_id(annotation_id)
    if ann is None:
        raise RepositoryError(f"annotation {annotation_id} not found")

    if ann.status != "valid":
        raise RepositoryError(
            f"annotation {annotation_id} status={ann.status} (not valid)"
        )

    if ann.source_version_id != source_version_id:
        raise RepositoryError(
            f"annotation {annotation_id} is bound to source_version "
            f"{ann.source_version_id}, but source_version {source_version_id} "
            f"was requested — cross-version annotation is forbidden "
            f"(75 §六.4 no_cross_version)"
        )

    if version.status != "sealed":
        raise RepositoryError(
            f"source_version {source_version_id} status={version.status} "
            f"(not sealed) — annotation on non-sealed source is forbidden"
        )

    return version, ann
