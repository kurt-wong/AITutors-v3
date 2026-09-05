"""pytest conftest：env 注入（app import 前）、session 迁移、async session 回滚隔离。"""

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors",
)

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config

from app.db.session import async_session_maker


@pytest.fixture(scope="session", autouse=True)
def migrated_db() -> None:
    """确保段 A baseline（19 表）已应用（幂等）。"""
    command.upgrade(Config("alembic.ini"), "head")


@pytest_asyncio.fixture
async def session():
    async with async_session_maker() as s:
        yield s
        await s.rollback()
