"""Task API endpoints：任务列表（工作台用）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.schemas import TaskListResponse, TaskSummary
from app.models.runtime import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """列出任务，可按 status 筛选。"""
    stmt = select(Task)
    count_stmt = select(func.count()).select_from(Task)
    if status:
        stmt = stmt.where(Task.status == status)
        count_stmt = count_stmt.where(Task.status == status)

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(Task.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    tasks = [
        TaskSummary(
            id=t.id,
            task_type=t.task_type,
            status=t.status,
            current_stage=t.current_stage,
            created_at=t.created_at,
            decided_at=t.decided_at,
            llm_invocations=t.llm_invocations,
        )
        for t in rows
    ]
    return TaskListResponse(tasks=tasks, total=total)
