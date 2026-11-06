"""API 依赖注入：数据库 session。

QUESTION-VISUAL-INSPECTION-V1 DSH-F1 加固：活动库从进程级单例改为
每请求显式上下文。请求可带 X-Inspect-Db 头（或 ?db= 查询参数）指定隔离
卷库，白名单校验后按请求建会话；未携带时回落到 activate 的活动库。
消除「并行任务/脚本切换活动库导致读到另一卷数据」的共享状态竞态。
"""

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_active_db_name, get_session_maker, inspect_db_allowed


def effective_db_name(request: Request) -> str:
    """解析请求的生效库：显式头/参数（白名单内）优先，否则活动库。"""
    raw = request.headers.get("X-Inspect-Db") or request.query_params.get("db") or ""
    name = raw.strip()
    if name and inspect_db_allowed(name):
        return name
    return get_active_db_name()


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with get_session_maker(effective_db_name(request))() as session:
        yield session
