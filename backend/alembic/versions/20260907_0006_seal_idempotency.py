"""H-1（BUG-V3-029/007）：documents + document_source_versions 幂等 UNIQUE 兜底。

BUG-V3-007 终裁（2026-09-07）：
  - documents.UNIQUE(original_sha256) = Source/Document Identity（一个原始文件一个主档）。
  - document_source_versions.UNIQUE(logical_execution_stage, logical_execution_hash) = Seal
    Version canonical uniqueness（同 Seal LE 至多一个 version；跨 role/provider 多 version 合法）。
  - 禁 document_source_versions.UNIQUE(original_sha256)（Seal 层全局唯一）。

双路径时序（BUG-V3-028）：0001/0003 全量 Base.metadata bootstrap 导入活 ORM（含 __table_args__）
→ from-empty 与 fresh-incremental 两路径下两约束已由 0001 建出 → 0006 为 no-op。仅对「0006
写就前已 upgrade 0005」的存量库真正 ADD CONSTRAINT。用 DO 块 IF NOT EXISTS 保证双路径安全
（PostgreSQL ADD CONSTRAINT 无 IF NOT EXISTS 语法）；ORM __table_args__ 与 migration 约束名一致。
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_documents_original_sha256'
            ) THEN
                ALTER TABLE documents
                    ADD CONSTRAINT uq_documents_original_sha256 UNIQUE (original_sha256);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_source_versions_le'
            ) THEN
                ALTER TABLE document_source_versions
                    ADD CONSTRAINT uq_source_versions_le
                    UNIQUE (logical_execution_stage, logical_execution_hash);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE document_source_versions DROP CONSTRAINT IF EXISTS uq_source_versions_le"
    )
    op.execute(
        "ALTER TABLE documents DROP CONSTRAINT IF EXISTS uq_documents_original_sha256"
    )
