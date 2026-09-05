"""段 C：运行域 2 表 llm_call_audit + budget（30 §10/§11/§17）。create_all 增量（19 表已存在 no-op）。"""

import app.models  # noqa: F401
from alembic import op
from app.db.base import Base

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_RUNTIME_TABLES = ("llm_call_audit", "budget")


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    for t in _RUNTIME_TABLES:
        op.drop_table(t)
