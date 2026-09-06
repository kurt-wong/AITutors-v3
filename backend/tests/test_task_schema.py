"""段 H Phase 1 schema guard：tasks/task_claims 结构契约（30 §17 + §5 lease）。

F-2 强化：除列名 exact 外，锁定 DB 侧 SQL 类型 / nullable / PK / FK（information_schema +
inspector），并锁定 ORM 模型侧 nullable / 类型（Base.metadata）与 spec 一致；ORM↔DB 双向
同锁防漂移（如 task_params 被改 dict|None，迁移前即被 ORM contract 拦下）。

双保险（Note-4 / BUG-V3-028）：机制 = 0004 migration 用 create_all(tables=[Task, TaskClaim])；
从空库 replay 时 0001/0003 全量 bootstrap 可能已建两表 → 0004 no-op，创建者语义按 from-empty /
incremental 双路径由 test_migration_replay 断言（本文件只锁 HEAD shape，空库与增量库一致）。
"""

from sqlalchemy import inspect, text

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine

RUNTIME_TABLES = {"llm_call_audit", "budget", "tasks", "task_claims"}

# 列 → (information_schema data_type, is_nullable 'YES'/'NO')。来源 = 30 §17 + §5 lease。
TASKS_SPEC = {
    "id": ("uuid", "NO"),
    "task_type": ("character varying", "NO"),
    "status": ("character varying", "NO"),
    "task_params": ("jsonb", "NO"),
    "claim_round": ("integer", "NO"),
    "current_stage": ("character varying", "YES"),
    "created_by": ("character varying", "YES"),
    "created_at": ("timestamp with time zone", "NO"),
    "decided_at": ("timestamp with time zone", "YES"),
    "worker_id": ("character varying", "YES"),
    "lease_token": ("character varying", "YES"),
    "started_at": ("timestamp with time zone", "YES"),
    "heartbeat_at": ("timestamp with time zone", "YES"),
    "lease_expires_at": ("timestamp with time zone", "YES"),
}

TASK_CLAIMS_SPEC = {
    "id": ("uuid", "NO"),
    "task_id": ("uuid", "NO"),
    "claim_round": ("integer", "NO"),
    "start": ("timestamp with time zone", "YES"),
    "end": ("timestamp with time zone", "YES"),
    "outcome": ("character varying", "YES"),
    "error_type": ("character varying", "YES"),
    "lease_snapshot": ("jsonb", "YES"),
}


def _snapshot(conn):
    insp = inspect(conn)
    tables = set(insp.get_table_names())
    pks = {
        t: set(insp.get_pk_constraint(t).get("constrained_columns") or [])
        for t in ("tasks", "task_claims")
    }
    fk = insp.get_foreign_keys("task_claims")
    return tables, pks, fk


async def _snap():
    async with engine.connect() as conn:
        return await conn.run_sync(_snapshot)


async def _db_struct(table: str) -> dict[str, tuple[str, str]]:
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:t "
                "ORDER BY ordinal_position"
            ),
            {"t": table},
        )
        return {r.column_name: (r.data_type, r.is_nullable) for r in rows}


def _orm_nullable(table: str) -> dict[str, bool]:
    return {c.name: c.nullable for c in Base.metadata.tables[table].columns}


# ---- HEAD shape（增量库 & 空库一致）----


async def test_runtime_domain_tables_exact() -> None:
    """运行域表 exact 集 = 段 C 两表 + 段 H 两表；无越权多表。"""
    tables, _, _ = await _snap()
    content_meta = set(Base.metadata.tables) - RUNTIME_TABLES
    assert tables - {"alembic_version"} == content_meta | RUNTIME_TABLES


# ---- DB 结构契约（SQL type / nullable）----


async def test_db_tasks_sql_type_and_nullable() -> None:
    db = await _db_struct("tasks")
    assert db == TASKS_SPEC


async def test_db_task_claims_sql_type_and_nullable() -> None:
    db = await _db_struct("task_claims")
    assert db == TASK_CLAIMS_SPEC


# ---- ORM 模型契约（nullable / 类型；迁移前即拦模型 drift）----


async def test_orm_tasks_nullable_contract() -> None:
    exp = {c: n == "YES" for c, (_, n) in TASKS_SPEC.items()}
    assert _orm_nullable("tasks") == exp


async def test_orm_task_claims_nullable_contract() -> None:
    exp = {c: n == "YES" for c, (_, n) in TASK_CLAIMS_SPEC.items()}
    assert _orm_nullable("task_claims") == exp


async def test_orm_jsonb_and_timezone_types() -> None:
    t = Base.metadata.tables["tasks"]
    assert t.c.task_params.type.__class__.__name__ == "JSONB"
    assert t.c.created_at.type.__class__.__name__ == "DateTime"
    assert t.c.created_at.type.timezone is True
    tc = Base.metadata.tables["task_claims"]
    assert tc.c.lease_snapshot.type.__class__.__name__ == "JSONB"
    assert tc.c.task_id.type.__class__.__name__ == "Uuid"


# ---- PK / FK / Lock-1 ----


async def test_pk_is_id_only() -> None:
    _, pks, _ = await _snap()
    assert pks["tasks"] == {"id"}
    assert pks["task_claims"] == {"id"}


async def test_task_claims_fk_to_tasks() -> None:
    _, _, fk = await _snap()
    assert any(
        f["constrained_columns"] == ["task_id"]
        and f["referred_table"] == "tasks"
        and f["referred_columns"] == ["id"]
        for f in fk
    ), "task_claims.task_id 必须 FK → tasks.id"


async def test_task_claims_lock1_no_top_level_worker_lease() -> None:
    """Lock-1：worker_id/lease_token 不进 task_claims 顶层列，只经 lease_snapshot 存证据。"""
    db = await _db_struct("task_claims")
    assert set(db) == set(TASK_CLAIMS_SPEC)
    assert "lease_snapshot" in db
    assert {"worker_id", "lease_token"} & set(db) == set()
