"""Gate C2 — llm_call_audit append-only 不可变 + idempotency_key（30 §10）。"""

import pytest

from app.ai.audit import build_idempotency_key
from app.repositories.base import AppendOnlyViolation
from app.repositories.runtime_repository import LlmCallAuditRepository

_HASH = "b" * 64


async def test_audit_row_created(session) -> None:
    repo = LlmCallAuditRepository(session)
    row = await repo.create_audit(
        idempotency_key="k", logical_execution_stage="ann", logical_execution_hash=_HASH,
        stage="ann", provider="deepseek", model="deepseek-chat",
    )
    await session.flush()
    assert row.request_id is not None
    assert row.status == "started"


async def test_audit_update_raises(session) -> None:
    repo = LlmCallAuditRepository(session)
    with pytest.raises(AppendOnlyViolation):
        await repo.update_audit()


async def test_idempotency_key_deterministic() -> None:
    args = dict(
        logical_execution_stage="ann", logical_execution_hash=_HASH,
        attempt_id=None, provider="deepseek", model="deepseek-chat", stage="ann",
    )
    assert build_idempotency_key(**args) == build_idempotency_key(**args)
    assert len(build_idempotency_key(**args)) == 64
    # provider/model 参与身份：换 provider 键不同
    other = dict(args, provider="mimo")
    assert build_idempotency_key(**other) != build_idempotency_key(**args)
