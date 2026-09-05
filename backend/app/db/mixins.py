"""通用 mixin：UUID v4 PK / TIMESTAMPTZ / 10 §3 标准 provenance 列。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


class ProvenanceMixin:
    """10 §3 标准 provenance 列（各表按 10 冻结正文取舍，非全部必填）。"""

    logical_execution_stage: Mapped[str | None] = mapped_column(String, nullable=True)
    logical_execution_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    input_identity: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
