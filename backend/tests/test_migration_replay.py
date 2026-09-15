"""段 H Step 1 — 两层 migration regression（F-3 / 用户裁决 B 语义）。

F-1（BUG-V3-028）教训：增量库全绿 ≠ 空库 replay 正确。因此按用户裁决补双路径：

1. test_from_empty_replay_reaches_head —— 一次性 scratch 空库完整 `upgrade head`，
   断言终态表集 == ORM metadata + alembic_version（HEAD shape，层 1）。
   不要求「tasks 由 0004 首次创建」——空库上 0001/0003 全量 bootstrap 已建（B 语义）。
2. test_incremental_0003_to_0004_delta —— 在 A–G 时代增量主库上
   `downgrade 0003 → upgrade head`，断言 delta == {tasks, task_claims}（层 2，
   保留 plan「0004 在增量库建这两表」的真意）。

不引入 checksum / ownership registry（用户 §12 排除）。
"""

import asyncio
import os
import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors",
)

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from test_task_schema import TASK_CLAIMS_SPEC, TASKS_SPEC

_MAIN_SQLA = os.environ["DATABASE_URL"]


def _plain(dsn: str) -> str:
    u = make_url(dsn)
    return f"postgresql://{u.username}:{u.password}@{u.host}:{u.port}/{u.database}"


def _main_no_db() -> str:
    u = make_url(_MAIN_SQLA)
    return f"postgresql://{u.username}:{u.password}@{u.host}:{u.port}/postgres"


async def _list_tables(dsn: str) -> set[str]:
    import asyncpg

    conn = await asyncpg.connect(_plain(dsn))
    try:
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        )
        return {r["tablename"] for r in rows}
    finally:
        await conn.close()


async def _list_constraints(dsn: str, table: str) -> set[str]:
    import asyncpg

    conn = await asyncpg.connect(_plain(dsn))
    try:
        rows = await conn.fetch(
            "SELECT conname FROM pg_constraint "
            "WHERE conrelid = $1::regclass AND contype = 'u'",
            table,
        )
        return {r["conname"] for r in rows}
    finally:
        await conn.close()


async def _db_struct(dsn: str, table: str) -> dict[str, tuple[str, str]]:
    import asyncpg

    conn = await asyncpg.connect(_plain(dsn))
    try:
        rows = await conn.fetch(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=$1 "
            "ORDER BY ordinal_position",
            table,
        )
        return {r["column_name"]: (r["data_type"], r["is_nullable"]) for r in rows}
    finally:
        await conn.close()


async def _drop_scratch(name: str) -> None:
    import asyncpg

    conn = await asyncpg.connect(_plain(_main_no_db()))
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{name}"')
    finally:
        await conn.close()


async def _column_default(dsn: str, table: str, column: str) -> str | None:
    import asyncpg

    conn = await asyncpg.connect(_plain(dsn))
    try:
        return await conn.fetchval(
            "SELECT column_default FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=$1 AND column_name=$2",
            table,
            column,
        )
    finally:
        await conn.close()


def test_from_empty_replay_reaches_head() -> None:
    """层 1：空库完整 replay → HEAD 表集 == ORM metadata + alembic_version。"""
    import asyncpg

    scratch = f"aitutors_replay_{uuid.uuid4().hex[:8]}"
    # 注意：str(make_url(...)) 会把密码掩码为 *** —— 必须在 DSN 文本上换库名保留明文密码
    scratch_sqla = _MAIN_SQLA.rsplit("/", 1)[0] + "/" + scratch
    scratch_plain = _plain(scratch_sqla)

    async def _create() -> None:
        conn = await asyncpg.connect(_plain(_main_no_db()))
        try:
            await conn.execute(f'CREATE DATABASE "{scratch}"')
        finally:
            await conn.close()

    original = settings.database_url
    asyncio.run(_create())
    settings.database_url = str(scratch_sqla)
    try:
        command.upgrade(Config("alembic.ini"), "head")
        tables = asyncio.run(_list_tables(scratch_plain))
        expected = set(Base.metadata.tables) | {"alembic_version"}
        assert tables == expected, (
            f"空库 HEAD 表集不匹配: {sorted(tables - expected)} 多余, "
            f"{sorted(expected - tables)} 缺失"
        )
        # 空库上 tasks/task_claims 结构仍须与 HEAD 契约一致（与增量库同 shape）
        assert asyncio.run(_db_struct(scratch_plain, "tasks")) == TASKS_SPEC
        assert asyncio.run(_db_struct(scratch_plain, "task_claims")) == TASK_CLAIMS_SPEC
        # C-1：from-empty 路径（create_all 带 server_default）llm_invocations column_default 亦为
        # '0'，与增量 0005 ADD COLUMN DEFAULT 0 双路径一致（增量侧由 test_task_schema 锁）。
        assert asyncio.run(_column_default(scratch_plain, "tasks", "llm_invocations")) == "0"
        # BUG-011-E：from-empty（0001 create_all 读活 ORM __table_args__）建出 figure UNIQUE
        assert "uq_source_figures_figure_id" in asyncio.run(
            _list_constraints(scratch_plain, "source_figures")
        )
    finally:
        settings.database_url = original
        asyncio.run(_drop_scratch(scratch))


def test_incremental_0003_to_0004_delta() -> None:
    """层 2：A–G 时代增量库上 pre-0004 → head 恰新增 tasks/task_claims + document_source_spans。"""
    cfg = Config("alembic.ini")
    command.downgrade(cfg, "0003")
    try:
        before = asyncio.run(_list_tables(_MAIN_SQLA))
        command.upgrade(cfg, "head")
        after = asyncio.run(_list_tables(_MAIN_SQLA))
    finally:
        command.upgrade(cfg, "head")  # 无条件恢复到 head，防失败态污染后续测试
    delta = after - before
    expected_delta = {"tasks", "task_claims", "document_source_spans", "validation_events"}
    assert delta == expected_delta, f"增量 delta 期望 {sorted(expected_delta)}，实得 {sorted(delta)}"


def test_incremental_0008_to_0009_adds_figure_unique() -> None:
    """层 2：增量库 pre-0009 → 0009 恰新增 uq_source_figures_figure_id（DB 级 figure identity）。"""
    cfg = Config("alembic.ini")
    command.downgrade(cfg, "0008")
    try:
        before = asyncio.run(_list_constraints(_MAIN_SQLA, "source_figures"))
        command.upgrade(cfg, "head")  # = 0009
        after = asyncio.run(_list_constraints(_MAIN_SQLA, "source_figures"))
    finally:
        command.upgrade(cfg, "head")  # 无条件恢复到 head，防失败态污染后续测试
    assert "uq_source_figures_figure_id" in after - before, (
        f"0009 增量应新增 figure UNIQUE，实得 {sorted(after - before)}"
    )
