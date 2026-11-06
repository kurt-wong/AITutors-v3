"""Async engine / session factory（PostgreSQL，asyncpg）。创建不产生 I/O，启动零副作用。"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import pool
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
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


# ---------------------------------------------------------------------------
# QUESTION-VISUAL-INSPECTION-V1：隔离卷库只读浏览。
#
# 默认库（settings.database_url）业务写入路径不变；inspect 激活仅切换读出用
# session factory。白名单只放行默认库与 `ml_*` 隔离卷库（R1/R2/R2X 批次产物），
# 拒绝其它 aitutors_* 受保护/测试库。
# ---------------------------------------------------------------------------
DEFAULT_DB_NAME: str = make_url(settings.database_url).database or ""

_active_db_name: str = DEFAULT_DB_NAME
_engines: dict[str, AsyncEngine] = {DEFAULT_DB_NAME: engine}
_session_makers: dict[str, async_sessionmaker[AsyncSession]] = {
    DEFAULT_DB_NAME: async_session_maker
}


def get_active_db_name() -> str:
    return _active_db_name


def is_default_db(db_name: str | None = None) -> bool:
    return (db_name or _active_db_name) == DEFAULT_DB_NAME


def inspect_db_allowed(db_name: str) -> bool:
    """验收库白名单：仅默认库（aitutors_test）。历史 ml_* 卷库不再暴露。"""
    return bool(db_name) and db_name == DEFAULT_DB_NAME


def _make_url_for(db_name: str):
    # 注意：str(URL) 会掩码密码（渲染为 ***），必须把 URL 对象交给 engine
    return make_url(settings.database_url).set(database=db_name)


def _ensure_maker(db_name: str) -> async_sessionmaker[AsyncSession]:
    """确保指定库的 session factory 已缓存（不切换活动库）。"""
    maker = _session_makers.get(db_name)
    if maker is None:
        _engines[db_name] = create_async_engine(
            _make_url_for(db_name), poolclass=pool.NullPool
        )
        maker = async_sessionmaker(
            _engines[db_name], class_=AsyncSession, expire_on_commit=False
        )
        _session_makers[db_name] = maker
    return maker


def activate_db(db_name: str) -> None:
    """切换活动库（inspect 用）。调用方须先做白名单/存在性校验。"""
    global _active_db_name
    _ensure_maker(db_name)
    _active_db_name = db_name


def get_session_maker(db_name: str | None = None) -> async_sessionmaker[AsyncSession]:
    """返回指定库（缺省=活动库）的 session factory。不影响活动库指向。"""
    return _ensure_maker(db_name or _active_db_name)
