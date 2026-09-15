"""EB-008：validation_events 表（Evidence Authority 持久化 ledger，92号 §5.1/§6）。

append-only：应用层 Repository 唯一写入口（无 update/delete）；DB 触发器为后续加固项
（92号 §5.5，trade-off 已记录 §7 风险 2）。

双路径时序（BUG-V3-028）：0001 全量 Base.metadata bootstrap 导入活 ORM →
from-empty 路径下 0011 为 no-op。仅对增量库真正 CREATE TABLE。
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 双路径安全（BUG-V3-028）：0001 create_all 已建表 → IF NOT EXISTS no-op
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS validation_events (
            id UUID NOT NULL,
            claim_id VARCHAR NOT NULL,
            candidate_id UUID NOT NULL,
            source_version_id UUID NOT NULL,
            validation_result VARCHAR NOT NULL,
            checks JSONB NOT NULL,
            validation_method VARCHAR NOT NULL,
            validator VARCHAR NOT NULL,
            reference_ids JSONB,
            review_proof VARCHAR,
            validated_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY(candidate_id) REFERENCES admission_candidates (id),
            FOREIGN KEY(source_version_id) REFERENCES document_source_versions (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ve_claim_candidate "
        "ON validation_events (claim_id, candidate_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_ve_candidate "
        "ON validation_events (candidate_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ve_candidate")
    op.execute("DROP INDEX IF EXISTS idx_ve_claim_candidate")
    op.execute("DROP TABLE IF EXISTS validation_events")
