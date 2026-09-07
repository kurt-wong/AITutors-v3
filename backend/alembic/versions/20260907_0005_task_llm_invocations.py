"""段 H Phase 4：tasks.llm_invocations — 真实 Provider Invocation 熔断计数列（Lock-4）。

双路径时序：Task ORM 活模型已声明该列（server_default text("0")）；0001/0003 全量
Base.metadata bootstrap（BUG-V3-028）与 0004 create_all(tables=[Task.__table__]) 都导入活
ORM → from-empty 与「0005 写就前已 upgrade 0004」的 fresh-incremental 两路径下 tasks 已带此
列 → 0005 为 no-op。仅对「0005 版本前已 upgrade 0004」的存量库（当时 Task 模型无此列）真正
ADD COLUMN 补列。`ADD COLUMN IF NOT EXISTS` 保证双路径安全；server default 与 ORM 对齐，
column_default 两条路径一致（审查 C-1）。schema 契约（类型/nullable/default）由
test_task_schema 锁定，双路径结构由 test_migration_replay 断言。
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tasks "
        "ADD COLUMN IF NOT EXISTS llm_invocations integer NOT NULL DEFAULT 0"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS llm_invocations")
