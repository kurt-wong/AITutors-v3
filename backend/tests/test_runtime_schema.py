"""段 C schema：llm_call_audit + budget 2 表 exact（30 §10/§11/§17 + reserved 补列）。"""

from sqlalchemy import inspect

from app.db.session import engine

AUDIT_EXPECT_COLS = 24
BUDGET_EXPECT_COLS = 9


def _snapshot(conn):
    insp = inspect(conn)
    tables = set(insp.get_table_names())
    audit_cols = {c["name"] for c in insp.get_columns("llm_call_audit")}
    budget_cols = {c["name"] for c in insp.get_columns("budget")}
    budget_uniq = [
        frozenset(u["column_names"]) for u in insp.get_unique_constraints("budget")
    ]
    return tables, audit_cols, budget_cols, budget_uniq


async def _snap():
    async with engine.connect() as conn:
        return await conn.run_sync(_snapshot)


async def test_runtime_tables_exist() -> None:
    tables, *_ = await _snap()
    assert {"llm_call_audit", "budget"} <= tables


async def test_audit_24_columns() -> None:
    _, audit_cols, _, _ = await _snap()
    assert len(audit_cols) == AUDIT_EXPECT_COLS
    required = {
        "request_id", "idempotency_key", "logical_execution_stage",
        "logical_execution_hash", "attempt_id", "task_id", "document_id", "stage",
        "provider", "model", "process_id", "process_name", "hostname", "start", "end",
        "status", "prompt_chars", "input_tokens", "output_tokens", "reasoning_tokens",
        "total_tokens", "estimated_cost", "error_type", "oversized_output",
    }
    assert required <= audit_cols


async def test_budget_unique_includes_stage() -> None:
    _, _, budget_cols, budget_uniq = await _snap()
    assert len(budget_cols) == BUDGET_EXPECT_COLS
    assert {"account_dim", "scope_id", "stage", "limit", "used", "reserved", "reserved_at", "updated_at"} <= budget_cols
    assert any(c == frozenset({"account_dim", "scope_id", "stage"}) for c in budget_uniq)
