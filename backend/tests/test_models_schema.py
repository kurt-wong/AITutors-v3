"""Gate A2 — schema exact-set 契约测试：ORM metadata == Alembic baseline == 实际 PostgreSQL。"""

from sqlalchemy import inspect

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine

EXPECTED_TABLES = {
    # B 域（6）
    "documents",
    "document_source_versions",
    "document_source_lines",
    "source_figures",
    "document_active_sources",
    "document_source_selection_events",
    # C 域（3）
    "semantic_annotations",
    "admission_candidates",
    "admission_events",
    # A 域（10）
    "questions",
    "question_instances",
    "instance_role_contents",
    "materials",
    "material_links",
    "unit_groups",
    "unit_group_members",
    "instance_figure_links",
    "knowledge_nodes",
    "question_knowledge_links",
}

# 10 冻结正文显式声明的 7 组唯一性（UNIQUE 或 composite PK 实现，exact-set）
DECLARED_UNIQUES = {
    "document_source_lines": {"source_version_id", "line_ref"},
    "semantic_annotations": {"logical_execution_stage", "logical_execution_hash"},
    "admission_candidates": {"logical_execution_stage", "logical_execution_hash"},
    "admission_events": {"candidate_id"},
    "question_instances": {"question_id", "source_version_id", "occurrence_key"},
    "instance_role_contents": {"instance_id", "role", "label", "role_index"},
    "instance_figure_links": {"instance_id", "source_figure_id", "role", "order"},
}

LINK_TABLES_WITHOUT_UNIQUE = {
    "material_links",
    "unit_group_members",
    "question_knowledge_links",
}


def _schema_snapshot(conn):
    insp = inspect(conn)
    tables = set(insp.get_table_names())
    uniq = {
        t: [frozenset(u["column_names"]) for u in insp.get_unique_constraints(t)]
        for t in tables
    }
    pks = {
        t: set((insp.get_pk_constraint(t).get("constrained_columns") or []))
        for t in tables
    }
    return tables, uniq, pks


async def _snapshot():
    async with engine.connect() as conn:
        return await conn.run_sync(_schema_snapshot)


async def test_db_tables_exact_19() -> None:
    tables, _, _ = await _snapshot()
    db_tables = tables - {"alembic_version"}
    assert db_tables == EXPECTED_TABLES
    assert len(db_tables) == 19


async def test_orm_metadata_matches_db() -> None:
    tables, _, _ = await _snapshot()
    db_tables = tables - {"alembic_version"}
    assert set(Base.metadata.tables) == db_tables


async def test_declared_uniques_present() -> None:
    tables, uniq, pks = await _snapshot()
    for table, cols in DECLARED_UNIQUES.items():
        enforced = uniq[table] + ([frozenset(pks[table])] if pks[table] else [])
        assert any(c == frozenset(cols) for c in enforced), f"{table} 缺 {cols}"


async def test_link_tables_have_no_unique_constraint() -> None:
    tables, uniq, _ = await _snapshot()
    for table in LINK_TABLES_WITHOUT_UNIQUE:
        assert uniq[table] == [], f"{table} 不应出现额外 UNIQUE（10 未声明）"


async def test_no_unauthorized_unique_constraints() -> None:
    """全库非-PK UNIQUE 约束总数须恰为 6（声明表），无越权。"""
    tables, uniq, _ = await _snapshot()
    declared_flat = {frozenset(c) for c in DECLARED_UNIQUES.values()}
    seen = []
    for table in tables:
        for u in uniq[table]:
            assert u in declared_flat, f"未授权 UNIQUE {table}: {u}"
            seen.append(u)
    assert len(seen) == 6, f"期望 6 条 UNIQUE 约束，实得 {len(seen)}"
