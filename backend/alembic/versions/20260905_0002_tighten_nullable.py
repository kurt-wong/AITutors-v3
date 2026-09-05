"""段 A 对抗审查修正：撤越权 server_default + 收紧 NOT NULL（对照 10 冻结正文可空标记）。

R2（NOT NULL 收紧）：10 未标 NULL 即 required。
  - semantic_annotations.prompt_version / model_config_hash（注解身份）
  - admission_candidates.annotation_id
  - question_instances.question_number / question_number_range
  - instance_role_contents.source_span
  - materials.source_span
R3（撤 server_default=now() → 应用层 python default）。
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _drop_defaults() -> None:
    for table, col in [
        ("questions", "created_at"),
        ("question_instances", "created_at"),
        ("document_source_selection_events", "created_at"),
        ("admission_candidates", "created_at"),
        ("admission_events", "materialized_at"),
        ("document_active_sources", "selected_at"),
    ]:
        op.alter_column(table, col, server_default=None)


def upgrade() -> None:
    _drop_defaults()
    op.alter_column("semantic_annotations", "prompt_version", existing_type=sa.String(), nullable=False)
    op.alter_column("semantic_annotations", "model_config_hash", existing_type=sa.String(64), nullable=False)
    op.alter_column("admission_candidates", "annotation_id", existing_type=sa.Uuid(), nullable=False)
    op.alter_column("question_instances", "question_number", existing_type=sa.String(), nullable=False)
    op.alter_column("question_instances", "question_number_range", existing_type=sa.String(), nullable=False)
    op.alter_column("instance_role_contents", "source_span", existing_type=sa.dialects.postgresql.JSONB(), nullable=False)
    op.alter_column("materials", "source_span", existing_type=sa.dialects.postgresql.JSONB(), nullable=False)


def downgrade() -> None:
    op.alter_column("materials", "source_span", existing_type=sa.dialects.postgresql.JSONB(), nullable=True)
    op.alter_column("instance_role_contents", "source_span", existing_type=sa.dialects.postgresql.JSONB(), nullable=True)
    op.alter_column("question_instances", "question_number_range", existing_type=sa.String(), nullable=True)
    op.alter_column("question_instances", "question_number", existing_type=sa.String(), nullable=True)
    op.alter_column("admission_candidates", "annotation_id", existing_type=sa.Uuid(), nullable=True)
    op.alter_column("semantic_annotations", "model_config_hash", existing_type=sa.String(64), nullable=True)
    op.alter_column("semantic_annotations", "prompt_version", existing_type=sa.String(), nullable=True)
    _drop_defaults()
