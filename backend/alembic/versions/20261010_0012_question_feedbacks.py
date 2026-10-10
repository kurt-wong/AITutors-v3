"""M3b: question_feedbacks table (Human Verification Console).

Feedback is append/persist-only; does not alter frozen Question/Source models.
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 双路径安全（BUG-V3-028）：0001 create_all 可能已建 → IF NOT EXISTS no-op
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS question_feedbacks (
            id UUID NOT NULL,
            question_id UUID NOT NULL,
            instance_id UUID,
            source_version_id UUID,
            producer_unit_id VARCHAR,
            source_evidence JSONB NOT NULL,
            content_snapshot JSONB NOT NULL,
            category VARCHAR NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'open',
            created_by VARCHAR NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            review_note TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY(question_id) REFERENCES questions (id),
            FOREIGN KEY(instance_id) REFERENCES question_instances (id),
            FOREIGN KEY(source_version_id) REFERENCES document_source_versions (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_qf_question "
        "ON question_feedbacks (question_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_qf_status "
        "ON question_feedbacks (status, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_qf_status")
    op.execute("DROP INDEX IF EXISTS idx_qf_question")
    op.execute("DROP TABLE IF EXISTS question_feedbacks")
