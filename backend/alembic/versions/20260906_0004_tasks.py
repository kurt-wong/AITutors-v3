"""段 H Phase 1：tasks/task_claims 专责 migration（30 §17 + §5 lease）。

upgrade() 用 create_all(tables=[Task, TaskClaim])，限定 tables、不依赖完整 Base.metadata：
0004 是这两张表的**专责 migration**，在当前已存在的 A–G 增量数据库上承担其首次创建。
但因 0001/0003 使用全量 Base.metadata bootstrap（BUG-V3-028），从空库 replay 时两表可能
已被早期 revision 建出 → 0004 在此场景为 no-op。创建者语义由 test_migration_replay 按
from-empty / incremental 双路径断言。
"""

import app.models  # noqa: F401  # 注册全部模型到 Base.metadata
from alembic import op
from app.db.base import Base
from app.models.runtime import Task, TaskClaim

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

_RUN_TABLES = ("task_claims", "tasks")


def upgrade() -> None:
    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=[Task.__table__, TaskClaim.__table__],
    )


def downgrade() -> None:
    # 子先父后：task_claims 持 FK → tasks，先 drop 子表
    for t in _RUN_TABLES:
        op.drop_table(t)
