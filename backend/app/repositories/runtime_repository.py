"""运行域 Repository：audit append-only + budget 条件 UPDATE（30 §10/§11，段 C）。

llm_call_audit 唯一受控写 = finalize_audit 的 STARTED→terminal 迁移（30 §10；
update_audit 仍拒改）；budget reserve/settle 条件 UPDATE 并发安全。

段 H（Step 2）：tasks/task_claims 状态机写路径——claim 原子（UPDATE tasks + INSERT
task_claims 证据同事务）、heartbeat/complete/fail 四元组 token 条件写（zombie 保护）、
recover/retry。
"""

import json
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.runtime import Budget, LlmCallAudit, Task, TaskClaim
from app.repositories.base import AppendOnlyViolation, BaseRepository, RepositoryError


class TaskStateError(RepositoryError):
    """tasks 状态迁移被拒（claim 非 queued / retry 非 failed·interrupted）。"""


class LeaseConflict(RepositoryError):
    """heartbeat/complete/fail 四元组不匹配（zombie 保护）或 lease 状态不符。"""


class AuditNotFoundError(RepositoryError):
    """finalize_audit 指向不存在的 request_id（缺行 ≠ 已终态 no-op，F-1）。"""


# 30 §10 终态值域（无 DB CHECK；finalize 唯一合法 terminal 出口）
AUDIT_TERMINAL_STATUSES = frozenset({"completed", "failed", "unknown"})


class LlmCallAuditRepository(BaseRepository):
    async def create_audit(
        self,
        *,
        idempotency_key: str,
        logical_execution_stage: str,
        logical_execution_hash: str,
        stage: str,
        provider: str,
        model: str,
        attempt_id: uuid.UUID | None = None,
        task_id: uuid.UUID | None = None,
        document_id: uuid.UUID | None = None,
        request_id: uuid.UUID | None = None,
        status: str = "started",
        prompt_chars: int | None = None,
    ) -> LlmCallAudit:
        """create STARTED（30 §10 append-only）。request_id 缺省 ORM 生成；显式提供时用于把
        request 预算账户 scope 与 audit 行身份绑定（executor Phase 4 同 request_id）。"""
        row = LlmCallAudit(
            **({"request_id": request_id} if request_id is not None else {}),
            idempotency_key=idempotency_key,
            logical_execution_stage=logical_execution_stage,
            logical_execution_hash=logical_execution_hash,
            attempt_id=attempt_id,
            task_id=task_id,
            document_id=document_id,
            stage=stage,
            provider=provider,
            model=model,
            status=status,
            prompt_chars=prompt_chars,
        )
        await self.add(row)
        return row

    async def update_audit(self, *_args: object, **_kwargs: object) -> None:
        """llm_call_audit append-only 不可变：任意 UPDATE → 抛错（Gate C2）。

        唯一例外是 finalize_audit 的受控 STARTED→terminal 迁移；update_audit 保持拒改，
        防绕过该受控路径的随意改写。
        """
        raise AppendOnlyViolation("llm_call_audit is append-only immutable")

    async def finalize_audit(
        self,
        request_id: uuid.UUID,
        *,
        status: str,
        end: datetime | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        reasoning_tokens: int | None = None,
        total_tokens: int | None = None,
        estimated_cost: Decimal | None = None,
        error_type: str | None = None,
        oversized_output: bool | None = None,
    ) -> str:
        """STARTED → terminal（completed/failed/unknown）exactly-once（30 §10，F-1 语义）。

        三态严格区分，绝不把「缺行」伪装成「已终态 no-op」：
          request_id 不存在            → raise AuditNotFoundError（编程错误）
          存在且 status='started'      → 条件 UPDATE 迁移，返回新终态（恰一迁移）
          存在且已是 terminal           → no-op（幂等），返回既有终态（不改写）
          并发两 finalize 争同一行      → 条件 UPDATE 保证恰一成功；败者 0 行后 reread
                                        确认 terminal，返回该终态（不抛、不二次迁移）
        只做状态迁移 primitive：不判 orphan / 不看 task lease / 不碰 budget——「何时应置
        UNKNOWN」的判定属 Phase 4（F-2 分层）。DB now() 单一来源：end 缺省取 now()。
        """
        if status not in AUDIT_TERMINAL_STATUSES:
            raise ValueError(
                f"finalize status must be one of {sorted(AUDIT_TERMINAL_STATUSES)}, got {status!r}"
            )
        existing = await self._session.execute(
            select(LlmCallAudit.status).where(LlmCallAudit.request_id == request_id)
        )
        cur = existing.scalar_one_or_none()
        if cur is None:
            raise AuditNotFoundError(f"llm_call_audit not found: {request_id}")
        if cur != "started":
            return cur  # 已终态 → no-op（幂等），不改写行
        res = await self._session.execute(
            text(
                "UPDATE llm_call_audit SET status=:s, \"end\"=COALESCE(:e, now()), "
                "input_tokens=:it, output_tokens=:ot, reasoning_tokens=:rt, "
                "total_tokens=:tt, estimated_cost=:ec, error_type=:et, oversized_output=:os "
                "WHERE request_id=:id AND status='started' RETURNING status"
            ),
            {
                "s": status, "e": end, "id": request_id,
                "it": input_tokens, "ot": output_tokens, "rt": reasoning_tokens,
                "tt": total_tokens, "ec": estimated_cost, "et": error_type, "os": oversized_output,
            },
        )
        row = res.mappings().first()
        if row is not None:
            return row["status"]  # 恰一迁移
        # 并发败者：读到 started 但 UPDATE 0 行 → 另一事务已终态化 → reread 确认终态
        after = await self._session.execute(
            select(LlmCallAudit.status).where(LlmCallAudit.request_id == request_id)
        )
        return after.scalar_one()


class BudgetRepository(BaseRepository):
    async def ensure_account(
        self, *, account_dim: str, scope_id: str, limit: Decimal, stage: str | None = None
    ) -> Budget:
        """幂等建账户行（唯一约束 on_conflict 不重复），limit 由调用方提供（单位语义未冻结，BUG 记录）。"""
        stmt = (
            pg_insert(Budget)
            .values(
                account_dim=account_dim,
                scope_id=scope_id,
                stage=stage,
                limit=limit,
                used=Decimal("0"),
                reserved=Decimal("0"),
            )
            .on_conflict_do_nothing(constraint="uq_budget_account_scope")
        )
        await self._session.execute(stmt)
        res = await self._session.execute(
            text(
                "SELECT * FROM budget WHERE account_dim=:ad AND scope_id=:sc "
                "AND stage IS NOT DISTINCT FROM :st"
            ),
            {"ad": account_dim, "sc": scope_id, "st": stage},
        )
        row = res.mappings().one()
        return Budget(**{k: row[k] for k in Budget.__table__.columns.keys()})

    async def remaining(
        self, *, account_dim: str, scope_id: str, stage: str | None = None
    ) -> Decimal | None:
        """Remaining headroom (limit - used - reserved). None if account missing.
        Used by BudgetService.check() — fail-closed availability probe (Issue-03).
        """
        res = await self._session.execute(
            text(
                'SELECT ("limit" - used - reserved) AS remaining FROM budget '
                "WHERE account_dim=:ad AND scope_id=:sc AND stage IS NOT DISTINCT FROM :st"
            ),
            {"ad": account_dim, "sc": scope_id, "st": stage},
        )
        row = res.mappings().first()
        if row is None:
            return None
        return row["remaining"]

    async def reserve(self, *, account_dim: str, scope_id: str, amount: Decimal, stage: str | None = None) -> None:
        """条件 UPDATE：used+reserved+amount<=limit 原子；0 行 = 超限。"""
        res = await self._session.execute(
            text(
                "UPDATE budget SET reserved=reserved+:x, reserved_at=now(), updated_at=now() "
                "WHERE account_dim=:ad AND scope_id=:sc AND stage IS NOT DISTINCT FROM :st "
                'AND used+reserved+:x <= "limit" RETURNING id'
            ),
            {"x": amount, "ad": account_dim, "sc": scope_id, "st": stage},
        )
        if not res.first():
            raise LookupError(f"budget exceeded: {account_dim}/{scope_id}/{stage}")

    async def settle(self, *, account_dim: str, scope_id: str, reserved: Decimal, actual: Decimal, stage: str | None = None) -> None:
        res = await self._session.execute(
            text(
                "UPDATE budget SET reserved=reserved-:r, used=used+:a, updated_at=now() "
                "WHERE account_dim=:ad AND scope_id=:sc AND stage IS NOT DISTINCT FROM :st "
                "AND reserved>=:r RETURNING id"
            ),
            {"r": reserved, "a": actual, "ad": account_dim, "sc": scope_id, "st": stage},
        )
        if not res.first():
            raise LookupError(f"settle mismatch: {account_dim}/{scope_id}/{stage}")

    async def reclaim_expired(self, *, older_than_seconds: int) -> int:
        """reserve 超时确定性回收（30 §11；不调 LLM；不扩展 reservation 系统）。"""
        res = await self._session.execute(
            text(
                "UPDATE budget SET reserved=0 "
                "WHERE reserved_at < now() - make_interval(secs => :s) RETURNING id"
            ),
            {"s": older_than_seconds},
        )
        return len(res.all())


class TaskRepository(BaseRepository):
    """tasks：任务状态行。所有状态写走条件 UPDATE（30 §5 claim/heartbeat/zombie）。"""

    async def create(
        self, *, task_type: str, task_params: dict, status: str = "queued",
        created_by: str | None = None,
    ) -> Task:
        row = Task(task_type=task_type, task_params=task_params,
                   status=status, created_by=created_by)
        self._session.add(row)
        await self._session.flush()
        return row

    async def find(self, task_id: uuid.UUID) -> Task | None:
        res = await self._session.execute(select(Task).where(Task.id == task_id))
        return res.scalar_one_or_none()

    async def next_queued_id(self) -> uuid.UUID | None:
        """取最早入队的 queued task（Worker claim 前导查询；claim 原子性由 claim 的
        WHERE status='queued' 保证，此处仅取候选 id）。"""
        res = await self._session.execute(
            select(Task.id)
            .where(Task.status == "queued")
            .order_by(Task.created_at)
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def consume_llm_invocation(
        self, *, task_id: uuid.UUID, max_invocations: int
    ) -> bool:
        """真实 Provider Invocation 原子计数（Lock-4/Clarification-2）。

        条件 UPDATE：count < max → count+1 并返回 True（放行）；count >= max → 0 行
        返回 False（越界，provider 不发出）。任务生命周期累计，attempt/retry/recover 不重置。
        提交/回滚由调用方（ProviderInvocationCounter）负责——计数须在 provider 调用前持久。
        """
        res = await self._session.execute(
            text(
                "UPDATE tasks SET llm_invocations = llm_invocations + 1 "
                "WHERE id = :id AND llm_invocations < :max RETURNING id"
            ),
            {"id": task_id, "max": max_invocations},
        )
        return res.first() is not None


    async def claim(
        self, *, task_id: uuid.UUID, worker_id: str, lease_token: str, lease_seconds: int
    ) -> dict:
        """原子 claim：单 UPDATE 从 queued → running + claim_round+1（禁 SELECT→判断→UPDATE）。

        返回 claim_round + started_at + lease_expires_at（DB now() 单一来源），供同事务写
        task_claims 证据。无返回 = 已非 queued → TaskStateError。
        """
        res = await self._session.execute(
            text(
                "UPDATE tasks SET status='running', worker_id=:w, lease_token=:t, "
                "claim_round = claim_round + 1, started_at = now(), "
                "heartbeat_at = now(), "
                "lease_expires_at = now() + make_interval(secs => :lease) "
                "WHERE id = :id AND status = 'queued' "
                "RETURNING id, claim_round, started_at, lease_expires_at"
            ),
            {"id": task_id, "w": worker_id, "t": lease_token, "lease": lease_seconds},
        )
        row = res.mappings().first()
        if row is None:
            raise TaskStateError(f"task not claimable (not queued): {task_id}")
        return {
            "id": row["id"],
            "claim_round": row["claim_round"],
            "started_at": row["started_at"],
            "lease_expires_at": row["lease_expires_at"],
        }

    async def heartbeat(
        self, *, task_id: uuid.UUID, worker_id: str, lease_token: str, lease_seconds: int
    ) -> None:
        """四元组条件续租（30 §5）：有效 running claim 把 lease 滑到 now()+lease。

        heartbeat = liveness renewal，不是 reclaim/recovery——仅当 lease 未过期
        （lease_expires_at > now()）才续租；已失效 claim 的 heartbeat 与错
        token/worker 同被拒（LeaseConflict），交由 recover 接管。DB now() 单一来源，
        不在应用层回写旧 lease。
        """
        res = await self._session.execute(
            text(
                "UPDATE tasks SET heartbeat_at = now(), "
                "lease_expires_at = now() + make_interval(secs => :lease) "
                "WHERE id = :id AND worker_id = :w AND lease_token = :t "
                "AND status = 'running' AND lease_expires_at > now() "
                "RETURNING id"
            ),
            {"id": task_id, "w": worker_id, "t": lease_token, "lease": lease_seconds},
        )
        if res.first() is None:
            raise LeaseConflict(f"heartbeat rejected (zombie/lease expired): {task_id}")

    async def complete(self, *, task_id: uuid.UUID, worker_id: str, lease_token: str) -> dict:
        """running → succeeded 终态；条件四元组写（zombie 拒）。释放运行中 lease 字段。"""
        return await self._terminal(task_id, worker_id, lease_token, status="succeeded")

    async def fail(self, *, task_id: uuid.UUID, worker_id: str, lease_token: str) -> dict:
        return await self._terminal(task_id, worker_id, lease_token, status="failed")

    async def _terminal(self, task_id, worker_id, lease_token, *, status: str) -> dict:
        res = await self._session.execute(
            text(
                "UPDATE tasks SET status=:st, decided_at = now(), heartbeat_at = now(), "
                "worker_id = NULL, lease_token = NULL, lease_expires_at = NULL, "
                "started_at = NULL "
                "WHERE id = :id AND worker_id = :w AND lease_token = :t "
                "AND status = 'running' AND lease_expires_at > now() "
                "RETURNING id, claim_round"
            ),
            {"st": status, "id": task_id, "w": worker_id, "t": lease_token},
        )
        row = res.mappings().first()
        if row is None:
            raise LeaseConflict(f"{status} rejected (zombie/lease mismatch): {task_id}")
        return {"id": row["id"], "claim_round": row["claim_round"]}

    async def retry(self, task_id: uuid.UUID) -> None:
        """人工显式 retry：failed/interrupted → queued（开新 claim_round 于下次 claim）。"""
        res = await self._session.execute(
            text(
                "UPDATE tasks SET status='queued', decided_at = NULL, worker_id = NULL, "
                "lease_token = NULL, started_at = NULL, heartbeat_at = NULL, "
                "lease_expires_at = NULL "
                "WHERE id = :id AND status IN ('failed', 'interrupted') RETURNING id"
            ),
            {"id": task_id},
        )
        if res.first() is None:
            raise TaskStateError(f"task not retryable (must be failed/interrupted): {task_id}")

    async def list_expired(self, cutoff: datetime) -> list[uuid.UUID]:
        """失效租约查询（recover dry-run；lease 过期但仍 running）。"""
        res = await self._session.execute(
            select(Task.id).where(Task.status == "running", Task.lease_expires_at < cutoff)
        )
        return list(res.scalars().all())

    async def recover_expired(self, cutoff: datetime) -> list[uuid.UUID]:
        """失效租约 running → interrupted（不等价重跑；下次经 retry 人工放行）。"""
        res = await self._session.execute(
            text(
                "UPDATE tasks SET status='interrupted', heartbeat_at = now() "
                "WHERE status = 'running' AND lease_expires_at < :c RETURNING id"
            ),
            {"c": cutoff},
        )
        return [r["id"] for r in res.mappings().all()]


class TaskClaimRepository(BaseRepository):
    """task_claims（30 §17，append-only）：task 级租约证据，非 LE attempt（Lock-1）。"""

    async def create(
        self, *, task_id: uuid.UUID, claim_round: int, start: datetime | None = None,
        lease_snapshot: dict | None = None,
    ) -> TaskClaim:
        row = TaskClaim(task_id=task_id, claim_round=claim_round,
                        start=start, lease_snapshot=lease_snapshot)
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_claim(self, *_args: object, **_kwargs: object) -> None:
        """task_claims append-only：任意 UPDATE → 抛错（30 §17）。"""
        raise AppendOnlyViolation("task_claims is append-only immutable")

    async def finalize_claim(
        self,
        *,
        task_id: uuid.UUID,
        claim_round: int,
        outcome: str,
        error_type: str | None = None,
        error_detail: str | None = None,
        end: datetime | None = None,
    ) -> None:
        """受控 claim 终态迁移（H Phase 8）：定位 (task_id, claim_round) 且 outcome IS NULL
        的记录，写 outcome/error_type/end，并把 error_detail 并入 lease_snapshot（H8-1
        下游失败详情持久化）。append-only 的受控终态（类比 audit finalize_audit）；已终态 /
        缺行 → no-op 幂等（_terminal 的 running→terminal 条件写已保证唯一迁移，此处仅补
        claim 证据，不重复迁移）。DB now() 单一来源（end 缺省取 now()）。
        """
        detail_json = (
            json.dumps({"error_detail": error_detail}) if error_detail else "{}"
        )
        await self._session.execute(
            text(
                "UPDATE task_claims SET outcome=:o, error_type=:e, "
                "\"end\"=COALESCE(:en, now()), "
                "lease_snapshot = COALESCE(lease_snapshot, '{}'::jsonb) "
                "|| CAST(:d AS jsonb) "
                "WHERE task_id=:id AND claim_round=:cr AND outcome IS NULL"
            ),
            {
                "o": outcome, "e": error_type, "en": end, "d": detail_json,
                "id": task_id, "cr": claim_round,
            },
        )
