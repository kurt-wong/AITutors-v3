"""TaskService（30 §5/§17，Step 2）：tasks/task_claims 状态机唯一入口。

边界：只拥 Runtime Authority——claim/heartbeat/complete/fail/retry/recover，不判 Question
Identity / Dedup / Gate / Admission / decision_status（用户修正 7）。**不 commit**：
本服务方法在同一 session 事务内执行，由调用方（TaskExecutor / Worker / 测试）决定
commit 边界，保证 claim 的 tasks 状态更新与 task_claims 证据原子同事务。

状态迁移的合法性由 Repository 条件 UPDATE 在 SQL 层强制（claim 仅 queued→running；
heartbeat/terminal 四元组 running 条件写；retry 仅 failed/interrupted），DB 无 CHECK（30 §17）。
heartbeat 滑动续租（liveness renewal），lease 已过期则拒（由 recover 接管），非 reclaim。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.models.runtime import Task
from app.repositories.runtime_repository import (
    TaskClaimRepository,
    TaskRepository,
    TaskStateError,
)

# 30 §17 状态值域（无 DB CHECK；供测试/文档引用）
TASK_STATUSES = frozenset(
    {"created", "queued", "running", "succeeded", "failed", "interrupted"}
)


class TaskService:
    def __init__(
        self, session, *, lease_seconds: int | None = None
    ) -> None:
        self._session = session
        self._lease_seconds = (
            settings.task_claim_lease_seconds if lease_seconds is None else lease_seconds
        )
        self._tasks = TaskRepository(session)
        self._claims = TaskClaimRepository(session)

    async def enqueue(
        self, *, task_type: str, task_params: dict, created_by: str | None = None
    ) -> Task:
        return await self._tasks.create(
            task_type=task_type, task_params=task_params,
            status="queued", created_by=created_by,
        )

    async def claim(self, task_id: uuid.UUID, *, worker_id: str, lease_token: str) -> dict:
        """原子 claim + task_claims 证据同事务（单 session；不 commit）。

        Lock-1：worker_id/lease_token 只进 lease_snapshot JSONB，不进 task_claims 顶层列。
        """
        claimed = await self._tasks.claim(
            task_id=task_id, worker_id=worker_id,
            lease_token=lease_token, lease_seconds=self._lease_seconds,
        )
        snapshot = {
            "worker_id": worker_id,
            "lease_token": lease_token,
            "lease_expires_at": claimed["lease_expires_at"].isoformat(),
        }
        await self._claims.create(
            task_id=task_id,
            claim_round=claimed["claim_round"],
            start=claimed["started_at"],
            lease_snapshot=snapshot,
        )
        return claimed

    async def heartbeat(
        self, task_id: uuid.UUID, *, worker_id: str, lease_token: str
    ) -> None:
        """心跳即续租：把 lease_expires_at 滑到 now()+lease_seconds（DB now() 单源）。

        非 reclaim/recovery：lease 已过期则拒（LeaseConflict），交由 recover 接管，
        绝不靠 heartbeat 抢救失效 claim。zombie 四元组校验在 Repository SQL 层强制。
        """
        await self._tasks.heartbeat(
            task_id=task_id, worker_id=worker_id, lease_token=lease_token,
            lease_seconds=self._lease_seconds,
        )

    async def claim_next(self, *, worker_id: str, lease_token: str) -> dict | None:
        """claim 下一个 queued task（Worker 循环）：取最早 queued → 原子 claim。

        claim 的 WHERE status='queued' 保证原子性；若候选已被并发 claim 抢占（M1
        worker_concurrency=1 下极少），claim 抛 TaskStateError → 返回 None 由调用方重试。
        """
        task_id = await self._tasks.next_queued_id()
        if task_id is None:
            return None
        try:
            return await self.claim(task_id, worker_id=worker_id, lease_token=lease_token)
        except TaskStateError:
            return None

    async def complete(self, task_id: uuid.UUID, *, worker_id: str, lease_token: str) -> dict:
        result = await self._tasks.complete(
            task_id=task_id, worker_id=worker_id, lease_token=lease_token
        )
        await self._claims.finalize_claim(
            task_id=task_id, claim_round=result["claim_round"], outcome="succeeded"
        )
        return result

    async def fail(
        self,
        task_id: uuid.UUID,
        *,
        worker_id: str,
        lease_token: str,
        error_type: str | None = None,
        error_detail: str | None = None,
    ) -> dict:
        """running → failed 终态 + task_claims 失败证据（H8-1 下游失败详情持久化）。

        error_type 为失败分类（provider_error/network_error/validation_error/…）；
        error_detail 为具体 message（并入 claim 的 lease_snapshot，不丢诊断信息）。
        """
        result = await self._tasks.fail(
            task_id=task_id, worker_id=worker_id, lease_token=lease_token
        )
        await self._claims.finalize_claim(
            task_id=task_id, claim_round=result["claim_round"],
            outcome="failed", error_type=error_type, error_detail=error_detail,
        )
        return result

    async def retry(self, task_id: uuid.UUID) -> None:
        """人工显式 retry（failed/interrupted → queued，开新 claim_round 于下次 claim）。"""
        await self._tasks.retry(task_id)

    async def recover(
        self, *, cutoff: datetime | None = None, dry_run: bool = False
    ) -> list[uuid.UUID]:
        """失效租约（running 且 lease_expires_at < cutoff）→ interrupted（不等价重跑）。

        dry_run=True 只列出不迁移（Worker recover --dry-run 用）。
        """
        now = cutoff if cutoff is not None else datetime.now(timezone.utc)
        if dry_run:
            return await self._tasks.list_expired(now)
        return await self._tasks.recover_expired(now)

    async def find(self, task_id: uuid.UUID) -> Task | None:
        return await self._tasks.find(task_id)
