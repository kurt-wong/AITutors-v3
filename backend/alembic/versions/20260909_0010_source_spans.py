"""Phase I-3：document_source_spans 表（Source layout evidence）。

span_hash = SHA256(text + font + size + flags + bbox + origin)，
描述 source evidence instance（layout evidence identity），不表示 semantic equality。

双路径时序（BUG-V3-028）：0001 全量 Base.metadata bootstrap 导入活 ORM →
from-empty 路径下 0010 为 no-op。仅对增量库真正 CREATE TABLE。
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 双路径安全（BUG-V3-028）：0001 create_all 已建表 → IF NOT EXISTS no-op
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS document_source_spans (
            id UUID NOT NULL,
            source_version_id UUID NOT NULL,
            line_ref VARCHAR NOT NULL,
            seq INTEGER NOT NULL,
            text TEXT NOT NULL,
            font VARCHAR,
            size FLOAT,
            flags INTEGER,
            bbox JSONB,
            origin JSONB,
            span_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            UNIQUE (source_version_id, line_ref, seq),
            FOREIGN KEY(source_version_id) REFERENCES document_source_versions (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_source_spans_version_line "
        "ON document_source_spans (source_version_id, line_ref, seq)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_source_spans_hash "
        "ON document_source_spans (span_hash)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_source_spans_hash")
    op.execute("DROP INDEX IF EXISTS idx_source_spans_version_line")
    op.execute("DROP TABLE IF EXISTS document_source_spans")
