"""Async engine / session factory（PostgreSQL，asyncpg）。创建不产生 I/O，启动零副作用。"""

from collections.abc import AsyncGenerator

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    poolclass=pool.NullPool,  # 每连接按当前事件循环现建，防 asyncpg 跨事件循环复用（pytest 每测试新 loop）
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
