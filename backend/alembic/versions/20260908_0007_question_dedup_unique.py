"""BUG-V3-027：questions.dedup_key 全局 UNIQUE 兜底。

dedup_key = Question canonical identity（跨文档），全局唯一；并发 approve 同 dedup_key →
恰 1 Question。前置查重：存量重复 → fail-loud（不静默 merge/删行）。

双路径时序（BUG-V3-028）：0001 全量 Base.metadata bootstrap 导入活 ORM（含 __table_args__）
→ from-empty 与 fresh-incremental 两路径下约束已由 0001 建出 → 0007 为 no-op。仅对「0007
写就前已 upgrade 0006」的存量库真正 ADD CONSTRAINT。DO 块 IF NOT EXISTS 双路径安全。
"""

from alembic import op
from sqlalchemy import text

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 前置查重：存量重复 dedup_key → fail-loud（重复 = 已发生的 canonical identity 违例，
    # 不静默 merge/删行，由 owner 手工裁决去重）。
    dupes = op.get_bind().execute(
        text(
            "SELECT dedup_key, count(*) AS n FROM questions "
            "GROUP BY dedup_key HAVING count(*) > 1"
        )
    ).fetchall()
    if dupes:
        preview = "; ".join(f"{d[0][:16]}...:{d[1]}" for d in dupes[:5])
        raise RuntimeError(
            f"questions.dedup_key duplicates detected ({len(dupes)} groups); "
            f"manual dedup required before 0007. first: {preview}"
        )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_questions_dedup_key'
            ) THEN
                ALTER TABLE questions
                    ADD CONSTRAINT uq_questions_dedup_key UNIQUE (dedup_key);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE questions DROP CONSTRAINT IF EXISTS uq_questions_dedup_key"
    )
