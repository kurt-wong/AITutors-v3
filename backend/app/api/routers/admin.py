"""Admin API endpoints：工作台摘要统计。"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import AdminStats
from app.models.runtime import Task
from app.models.snapshot import AdmissionCandidate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
) -> AdminStats:
    """工作台摘要：pending_review / running_tasks / failed_tasks / approved_today。"""
    pending = (
        await db.execute(
            select(func.count())
            .select_from(AdmissionCandidate)
            .where(AdmissionCandidate.decision_status == "pending_review")
        )
    ).scalar() or 0

    running = (
        await db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.status == "running")
        )
    ).scalar() or 0

    failed = (
        await db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.status == "failed")
        )
    ).scalar() or 0

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    approved_today = (
        await db.execute(
            select(func.count())
            .select_from(AdmissionCandidate)
            .where(
                AdmissionCandidate.decision_status == "approved",
                AdmissionCandidate.decided_at >= today_start,
            )
        )
    ).scalar() or 0

    return AdminStats(
        pending_review=pending,
        running_tasks=running,
        failed_tasks=failed,
        approved_today=approved_today,
    )
