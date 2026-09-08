"""BUG-V3-011-E：source_figures UNIQUE(source_version_id, figure_id) 兜底。

figure_id = Figure identity（version-scoped，10 §4.4）；同 version 重复 figure_id → 恰 1 图。
前置查重：存量重复 → fail-loud（不静默 merge/删行）。

双路径时序（BUG-V3-028）：0001 全量 Base.metadata bootstrap 导入活 ORM（含 __table_args__）
→ from-empty 与 fresh-incremental 两路径下约束已由 0001 建出 → 0009 为 no-op。仅对「0009
写就前已 upgrade 0008」的存量库真正 ADD CONSTRAINT。DO 块 IF NOT EXISTS 双路径安全。
"""

from alembic import op
from sqlalchemy import text

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 前置查重：存量重复 (source_version_id, figure_id) → fail-loud（重复 = 已发生的
    # figure identity 违例，不静默 merge/删行，由 owner 手工裁决去重）。
    dupes = op.get_bind().execute(
        text(
            "SELECT source_version_id, figure_id, count(*) AS n FROM source_figures "
            "GROUP BY source_version_id, figure_id HAVING count(*) > 1"
        )
    ).fetchall()
    if dupes:
        preview = "; ".join(f"{d[0]}/{d[1][:16]}...:{d[2]}" for d in dupes[:5])
        raise RuntimeError(
            f"source_figures (source_version_id, figure_id) duplicates detected "
            f"({len(dupes)} groups); manual dedup required before 0009. first: {preview}"
        )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_source_figures_figure_id'
            ) THEN
                ALTER TABLE source_figures
                    ADD CONSTRAINT uq_source_figures_figure_id
                    UNIQUE (source_version_id, figure_id);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE source_figures DROP CONSTRAINT IF EXISTS uq_source_figures_figure_id"
    )
