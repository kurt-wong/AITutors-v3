"""段 A baseline：空库一次性建 A/B/C 三域 19 张表（10 §3-6）。

DDL 源 = Base.metadata（models 是 10 冻结正文的 executable schema）。
V3 全新库，不迁移 V2 任何列/镜像（10 §11 / 00 §1）。
"""

import app.models  # noqa: F401  # 注册全部模型
from alembic import op
from app.db.base import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
