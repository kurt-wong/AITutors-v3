"""Gate C2 — llm_call_audit append-only 不可变 + idempotency_key（30 §10）+ finalize_audit exactly-once。"""

import asyncio
import uuid

import pytest
from sqlalchemy import text

from app.ai.audit import build_idempotency_key
from app.db.session import async_session_maker
from app.repositories.base import AppendOnlyViolation
from app.repositories.runtime_repository import (
    AUDIT_TERMINAL_STATUSES,
    AuditNotFoundError,
    LlmCallAuditRepository,
)

_HASH = "b" * 64


async def _mk_audit(repo) -> uuid.UUID:
    row = await repo.create_audit(
        idempotency_key="k", logical_execution_stage="ann", logical_execution_hash=_HASH,
        stage="ann", provider="deepseek", model="deepseek-chat",
    )
    await repo._session.flush()
    return row.request_id


async def _audit_state(session, request_id) -> dict:
    row = (await session.execute(
        text(
            "SELECT status, \"end\", input_tokens, output_tokens, total_tokens, "
            "estimated_cost, error_type FROM llm_call_audit WHERE request_id=:id"
        ),
        {"id": request_id},
    )).mappings().one()
    return dict(row)


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


# ---- finalize_audit：STARTED → terminal exactly-once（30 §10，Phase 3 / F-1 语义） ----


async def test_finalize_started_to_terminal(session) -> None:
    """started → completed/failed/unknown 各可终态化（恰一迁移，end 落 now()）。"""
    assert AUDIT_TERMINAL_STATUSES == {"completed", "failed", "unknown"}
    for target in ("completed", "failed", "unknown"):
        async with async_session_maker() as s:
            repo = LlmCallAuditRepository(s)
            rid = await _mk_audit(repo)
            if target == "completed":
                got = await repo.finalize_audit(
                    rid, status="completed", input_tokens=10, output_tokens=5,
                    total_tokens=15, estimated_cost=1,
                )
            elif target == "failed":
                got = await repo.finalize_audit(rid, status="failed", error_type="timeout")
            else:
                got = await repo.finalize_audit(rid, status="unknown")
            await s.commit()
            assert got == target
            st = await _audit_state(s, rid)
            assert st["status"] == target
            assert st["end"] is not None
            if target == "completed":
                assert st["input_tokens"] == 10 and st["output_tokens"] == 5
                assert st["total_tokens"] == 15 and st["estimated_cost"] == 1
            if target == "failed":
                assert st["error_type"] == "timeout"


async def test_finalize_already_terminal_is_noop(session) -> None:
    """已终态再 finalize（含不同 status）→ no-op：不改写 status/end/usage。"""
    async with async_session_maker() as s:
        repo = LlmCallAuditRepository(s)
        rid = await _mk_audit(repo)
        first = await repo.finalize_audit(rid, status="completed", input_tokens=7)
        await s.commit()
        before = await _audit_state(s, rid)
        assert first == "completed"
        second = await repo.finalize_audit(rid, status="failed", error_type="timeout")
        await s.commit()
        after = await _audit_state(s, rid)
        assert second == "completed"  # no-op 返回既有终态，不采纳第二次请求的 failed
        assert after["status"] == "completed"
        assert after["end"] == before["end"]
        assert after["input_tokens"] == 7
        assert after["error_type"] is None


async def test_finalize_missing_request_raises(session) -> None:
    """不存在 request_id → raise（缺行 ≠ 已终态 no-op，F-1 不吞噬错误）。"""
    repo = LlmCallAuditRepository(session)
    with pytest.raises(AuditNotFoundError):
        await repo.finalize_audit(uuid.uuid4(), status="completed")


async def test_finalize_invalid_status_raises(session) -> None:
    """非终态 status（如 started/乱值）→ ValueError（值域合法门）。"""
    repo = LlmCallAuditRepository(session)
    rid = await _mk_audit(repo)
    for bad in ("started", "running", ""):
        with pytest.raises(ValueError):
            await repo.finalize_audit(rid, status=bad)


async def test_finalize_concurrent_exactly_one_transition() -> None:
    """并发两 finalize（不同终态）→ 恰一迁移；终态 = 胜者请求态；无二次迁移。"""
    async with async_session_maker() as s:
        repo = LlmCallAuditRepository(s)
        rid = await _mk_audit(repo)
        await s.commit()

    results = []

    async def worker(status: str) -> None:
        async with async_session_maker() as sess:
            repo = LlmCallAuditRepository(sess)
            returned = await repo.finalize_audit(rid, status=status)
            await sess.commit()
            results.append((status, returned))

    await asyncio.gather(worker("completed"), worker("failed"))

    wins = [(req, ret) for req, ret in results if req == ret]
    loses = [(req, ret) for req, ret in results if req != ret]
    assert len(wins) == 1 and len(loses) == 1
    async with async_session_maker() as s:
        st = (await s.execute(
            text("SELECT status FROM llm_call_audit WHERE request_id=:id"), {"id": rid}
        )).scalar_one()
    assert st == wins[0][0]  # DB 终态 = 迁移胜者的请求态
