"""BUG-V3-021：questions/materials subject·grade 可空 + 历史空串→NULL。

A' 终裁：unknown 用 NULL 表示（不用空串 "" 伪值）。metadata 与 identity（dedup_key）分层；
claim 缺失 → NULL。历史空串占位 → NULL 迁移。
"""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

_TABLES = ("questions", "materials")
_COLS = ("subject", "grade")


def upgrade() -> None:
    for table in _TABLES:
        for col in _COLS:
            op.execute(f"UPDATE {table} SET {col} = NULL WHERE {col} = ''")
            op.alter_column(table, col, existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    for table in _TABLES:
        for col in _COLS:
            op.execute(f"UPDATE {table} SET {col} = '' WHERE {col} IS NULL")
            op.alter_column(table, col, existing_type=sa.String(), nullable=False)
