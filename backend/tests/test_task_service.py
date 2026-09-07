"""段 H Step 2 — TaskService 状态机（真实 DB）。

覆盖（plan Phase 2 验证项）：
- enqueue → queued；claim 原子（非 queued 拒 + 不产生证据行）；task_claims 证据同事务
- heartbeat/complete/fail 四元组条件写（错误 token/worker → LeaseConflict，zombie 保护）
- heartbeat 滑动续租：有效 claim 续租（lease 严格后移）；持续 heartbeat 不被 recover；
  停止 heartbeat 超过 lease 后可被 recover（heartbeat 非 reclaim，过期拒）
- 真并发 claim：两 session 同时争同一 queued task → 恰一 winner + 单证据行
- 禁迁移：succeeded/failed/interrupted 后 terminal 写拒；queued 上二次 claim 拒；
  retry 仅 failed/interrupted；failed/interrupted 无自动出口
- recover 只置 interrupted 不等价重跑（dry-run 列表 + 实际迁移）
- TaskService 不自动 commit（未提交不可见于另一 session）；commit 后原子可见
"""

import asyncio
import uuid

import pytest
from sqlalchemy import text

from app.db.session import async_session_maker
from app.domains.task.service import TASK_STATUSES, TaskService
from app.models.runtime import Task
from app.repositories.base import AppendOnlyViolation
from app.repositories.runtime_repository import (
    LeaseConflict,
    TaskClaimRepository,
    TaskStateError,
)

W1 = "worker-a"
W2 = "worker-b"
TOK1 = "tok-1"
TOK2 = "tok-2"


async def _enqueue(session, *, task_type="document_ingest", **params):
    return await TaskService(session).enqueue(
        task_type=task_type, task_params=params or {"document_id": str(uuid.uuid4())}
    )


async def _status(session, task_id) -> str:
    res = await session.execute(text("SELECT status FROM tasks WHERE id=:id"), {"id": task_id})
    return res.scalar_one()


async def _claims_count(session, task_id) -> int:
    res = await session.execute(
        text("SELECT count(*) FROM task_claims WHERE task_id=:id"), {"id": task_id}
    )
    return res.scalar_one()


async def _reload_task(task_id) -> Task | None:
    async with async_session_maker() as s:
        return await s.get(Task, task_id)


async def _lease_state(session, task_id) -> dict:
    row = (await session.execute(
        text("SELECT lease_expires_at, heartbeat_at FROM tasks WHERE id=:id"),
        {"id": task_id},
    )).mappings().one()
    return dict(row)


# ---- enqueue / 初始态 ----


async def test_enqueue_creates_queued_task() -> None:
    async with async_session_maker() as session:
        t = await _enqueue(session)
        await session.commit()
        assert t.status == "queued"
        assert t.claim_round == 0
        reloaded = await _reload_task(t.id)
        assert reloaded is not None and reloaded.status == "queued"
        assert reloaded.task_type == "document_ingest"


# ---- 全迁移 + 禁迁移 ----


async def test_full_lifecycle_queued_to_succeeded() -> None:
    async with async_session_maker() as session:
        svc = TaskService(session)
        t = await _enqueue(session)
        await session.commit()
        claimed = await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        assert claimed["claim_round"] == 1
        await svc.heartbeat(t.id, worker_id=W1, lease_token=TOK1)
        out = await svc.complete(t.id, worker_id=W1, lease_token=TOK1)
        assert out["claim_round"] == 1
        await session.commit()
        assert await _status(session, t.id) == "succeeded"
        row = (await session.execute(
            text("SELECT worker_id, lease_token FROM tasks WHERE id=:id"), {"id": t.id}
        )).mappings().one()
        assert row["worker_id"] is None and row["lease_token"] is None


async def test_terminal_is_terminal_no_auto_exit() -> None:
    """succeeded 后：complete/heartbeat/claim 全部拒；无自动 stale→queued 出口。"""
    async with async_session_maker() as session:
        svc = TaskService(session)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await svc.complete(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        assert await _status(session, t.id) == "succeeded"
        with pytest.raises(LeaseConflict):
            await svc.complete(t.id, worker_id=W1, lease_token=TOK1)
        with pytest.raises(LeaseConflict):
            await svc.heartbeat(t.id, worker_id=W1, lease_token=TOK1)
        with pytest.raises(TaskStateError):
            await svc.claim(t.id, worker_id=W2, lease_token=TOK2)


async def test_fail_reachable_and_then_retry() -> None:
    async with async_session_maker() as session:
        svc = TaskService(session)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await svc.fail(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        assert await _status(session, t.id) == "failed"
        await svc.retry(t.id)
        await session.commit()
        assert await _status(session, t.id) == "queued"
        claimed = await svc.claim(t.id, worker_id=W2, lease_token=TOK2)
        assert claimed["claim_round"] == 2
        await session.commit()


async def test_retry_refused_when_not_terminal() -> None:
    """retry 仅 failed/interrupted；queued/running/succeeded 上拒。"""
    async with async_session_maker() as session:
        svc = TaskService(session)
        t = await _enqueue(session)
        await session.commit()
        with pytest.raises(TaskStateError):
            await svc.retry(t.id)
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        with pytest.raises(TaskStateError):
            await svc.retry(t.id)
        await svc.complete(t.id, worker_id=W1, lease_token=TOK1)
        with pytest.raises(TaskStateError):
            await svc.retry(t.id)


# ---- claim 原子 + zombie ----


async def test_claim_refused_when_not_queued_no_evidence() -> None:
    async with async_session_maker() as session:
        svc = TaskService(session)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        with pytest.raises(TaskStateError):
            await svc.claim(t.id, worker_id=W2, lease_token=TOK2)
        await session.commit()
        assert await _claims_count(session, t.id) == 1


async def test_zombie_token_mismatch_rejected() -> None:
    """错误 token/worker 的 heartbeat/complete/fail 全拒（任务仍属原 worker）。"""
    async with async_session_maker() as session:
        svc = TaskService(session)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        with pytest.raises(LeaseConflict):
            await svc.heartbeat(t.id, worker_id=W1, lease_token=TOK2)
        with pytest.raises(LeaseConflict):
            await svc.heartbeat(t.id, worker_id=W2, lease_token=TOK1)
        with pytest.raises(LeaseConflict):
            await svc.complete(t.id, worker_id=W2, lease_token=TOK1)
        with pytest.raises(LeaseConflict):
            await svc.fail(t.id, worker_id=W1, lease_token="forged")
        await session.commit()
        assert await _status(session, t.id) == "running"
        row = (await session.execute(
            text("SELECT worker_id FROM tasks WHERE id=:id"), {"id": t.id}
        )).mappings().one()
        assert row["worker_id"] == W1


# ---- heartbeat 滑动续租（F-2：liveness renewal，非 reclaim） ----


async def test_heartbeat_slides_lease_expiry() -> None:
    """heartbeat 把 lease_expires_at 滑到 (DB now)+lease：跨事务严格后移（F2-1）。

    必须跨 commit 断言：PostgreSQL now() = 事务开始时刻，claim 与 heartbeat 在同一
    事务内会取同一 now()。真实 worker 是独立调用/事务，故这里 claim 先 commit。
    """
    async with async_session_maker() as session:
        svc = TaskService(session, lease_seconds=3600)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        lease0 = await _lease_state(session, t.id)
        await svc.heartbeat(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        lease1 = await _lease_state(session, t.id)
        assert lease1["lease_expires_at"] > lease0["lease_expires_at"]
        assert lease1["heartbeat_at"] > lease0["heartbeat_at"]
        assert await _status(session, t.id) == "running"


async def test_continuous_heartbeat_survives_initial_lease() -> None:
    """持续 heartbeat（间隔 < lease）穿过原 lease 边界 → recover 不中断（F2-2）。

    反证修复：lease=2s，claim 后每 ~0.8s 心跳，最后一次心跳落在原 lease 过期点之后
    ——若无滑动续租，此刻已过期会被 recover 置 interrupted；有续租则仍 running。
    """
    async with async_session_maker() as session:
        svc = TaskService(session, lease_seconds=2)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        for _ in range(3):
            await asyncio.sleep(0.8)
            await svc.heartbeat(t.id, worker_id=W1, lease_token=TOK1)
            await session.commit()
        recovered = await svc.recover()
        await session.commit()
        assert t.id not in recovered
        assert await _status(session, t.id) == "running"
        await svc.complete(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        assert await _status(session, t.id) == "succeeded"


async def test_claim_evidence_same_transaction() -> None:
    """claim 后：tasks running + claim_round=1 且 task_claims 恰一行证据（start+snapshot）。"""
    async with async_session_maker() as session:
        svc = TaskService(session)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        row = (await session.execute(
            text(
                "SELECT claim_round, start, outcome, lease_snapshot "
                "FROM task_claims WHERE task_id=:id"
            ),
            {"id": t.id},
        )).mappings().one()
        assert row["claim_round"] == 1
        assert row["start"] is not None
        assert row["outcome"] is None
        snap = row["lease_snapshot"]
        assert snap["worker_id"] == W1
        assert snap["lease_token"] == TOK1
        assert "lease_expires_at" in snap
        cols = (await session.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='task_claims' "
                "AND column_name IN ('worker_id','lease_token')"
            )
        )).scalars().all()
        assert cols == []


async def test_concurrent_claim_exactly_one_winner() -> None:
    """真并发 claim（F-1）：两独立 session 同时争同一 queued task → 恰一 winner。

    锁定原子 claim 核心性质（防顺序测试掩盖回归）：
    winner=exactly 1（claim_round=1）+ loser=exactly 1 + 单证据行 + status=running。
    同时断证据行数==1，杜绝 "winner=1 但证据=2" 的状态机污染。
    """
    async with async_session_maker() as session:
        t = await _enqueue(session)
        await session.commit()
        tid = t.id

    results = []

    async def worker(worker_id: str, token: str) -> None:
        async with async_session_maker() as sess:
            svc = TaskService(sess)
            try:
                claimed = await svc.claim(tid, worker_id=worker_id, lease_token=token)
                await sess.commit()
                results.append(("win", worker_id, claimed["claim_round"]))
            except TaskStateError:
                await sess.rollback()
                results.append(("lose", worker_id, None))

    await asyncio.gather(worker(W1, TOK1), worker(W2, TOK2))

    wins = [r for r in results if r[0] == "win"]
    loses = [r for r in results if r[0] == "lose"]
    assert len(wins) == 1 and len(loses) == 1
    assert wins[0][2] == 1  # claim_round = 1（首轮）
    assert wins[0][1] in (W1, W2)
    async with async_session_maker() as session:
        assert await _status(session, tid) == "running"
        assert await _claims_count(session, tid) == 1


async def test_service_does_not_autocommit() -> None:
    """TaskService 不 commit：未提交的 enqueue/claim 在另一 session 不可见。"""
    async with async_session_maker() as session:
        svc = TaskService(session)
        t = await _enqueue(session)
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        async with async_session_maker() as other:
            assert await other.get(Task, t.id) is None
        await session.rollback()


# ---- recover ----


async def test_recover_interrupted_no_rerun() -> None:
    async with async_session_maker() as session:
        svc = TaskService(session, lease_seconds=-3600)  # 租约立即过期
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        expired = await svc.recover(dry_run=True)
        assert t.id in expired
        assert await _status(session, t.id) == "running"
        recovered = await svc.recover()
        assert t.id in recovered
        await session.commit()
        assert await _status(session, t.id) == "interrupted"
        assert await _claims_count(session, t.id) == 1
        with pytest.raises(LeaseConflict):
            await svc.complete(t.id, worker_id=W1, lease_token=TOK1)
        await svc.retry(t.id)
        claimed = await svc.claim(t.id, worker_id=W1, lease_token=TOK2)
        assert claimed["claim_round"] == 2
        await session.commit()
        assert await _claims_count(session, t.id) == 2


async def test_recover_ignores_active_lease() -> None:
    """未过期（running + lease 未失效）的**本任务**不被迁移。

    recover 是 tasks 全表扫描，共享测试库可能残留其他 running 任务，故只断本任务 id
    不在 recovered 集（不主张全局空），避免跨测试耦合。
    """
    async with async_session_maker() as session:
        svc = TaskService(session, lease_seconds=3600)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        recovered = await svc.recover()
        await session.commit()
        assert t.id not in recovered
        assert await _status(session, t.id) == "running"


async def test_expired_claim_heartbeat_refused_then_recovered() -> None:
    """停止 heartbeat 超过 lease → heartbeat 拒（非 reclaim）且 recover 可接管（F2-3）。

    heartbeat 不是 reclaim：lease 已过期的 claim 不能靠心跳抢救（LeaseConflict），
    之后 recover 置 interrupted。反向锁死：持续心跳不被 recover（F2-2）≠ recover 失效。
    """
    async with async_session_maker() as session:
        svc = TaskService(session, lease_seconds=1)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await svc.heartbeat(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        await asyncio.sleep(1.5)  # 停止心跳，超过 1s lease
        with pytest.raises(LeaseConflict):
            await svc.heartbeat(t.id, worker_id=W1, lease_token=TOK1)
        recovered = await svc.recover()
        await session.commit()
        assert t.id in recovered
        assert await _status(session, t.id) == "interrupted"


# ---- repository append-only + 值域 ----


async def test_task_claims_update_raises_append_only() -> None:
    async with async_session_maker() as session:
        t = await _enqueue(session)
        await session.commit()
        with pytest.raises(AppendOnlyViolation):
            await TaskClaimRepository(session).update_claim()


async def test_statuses_vocabulary() -> None:
    assert TASK_STATUSES == {
        "created", "queued", "running", "succeeded", "failed", "interrupted"
    }


async def test_expired_lease_complete_fail_rejected() -> None:
    """Batch 3-2：lease 过期后 complete/fail 被拒（与 heartbeat 一致）——旧 worker 不得改终态。

    _terminal 补 lease_expires_at > now() 条件，防「recover 未跑但 lease 已过期」窗口内
    过期 worker 把自己的 task 误标 failed（应保持 running 交 recover 置 interrupted）。
    """
    async with async_session_maker() as session:
        svc = TaskService(session, lease_seconds=1)
        t = await _enqueue(session)
        await session.commit()
        await svc.claim(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        await asyncio.sleep(1.5)  # 停止心跳，超过 1s lease
        with pytest.raises(LeaseConflict):
            await svc.complete(t.id, worker_id=W1, lease_token=TOK1)
        with pytest.raises(LeaseConflict):
            await svc.fail(t.id, worker_id=W1, lease_token=TOK1)
        await session.commit()
        # 旧 worker 的 complete/fail 被拒 → task 仍 running（交 recover 置 interrupted）
        assert await _status(session, t.id) == "running"
        recovered = await svc.recover()
        await session.commit()
        assert t.id in recovered
        assert await _status(session, t.id) == "interrupted"
