"""FORMAL-E2E-ENABLEMENT-02 Issue-03: budget check fail-closed (no fail-open)."""

from __future__ import annotations

import pytest

from app.ai.budget import AccountRef, BudgetService
from app.ai.gateway import LLMGateway
from app.core.errors import GatewayDeniedError


async def test_budget_check_missing_account_unavailable(session):
    svc = BudgetService(session)
    ok = await svc.check([AccountRef("task", "no-such-task")])
    assert ok is False


async def test_budget_check_after_ensure_available(session):
    svc = BudgetService(session)
    ref = AccountRef("task", "task-check-1")
    await svc.ensure(ref)
    await session.commit()
    ok = await svc.check([ref])
    assert ok is True


async def test_authorize_default_budget_not_ok():
    gw = LLMGateway("live", allow_live=True, live_provider=object())
    gw.authorize(task_context={"task_id": "t1"})  # budget_ok defaults False
    assert gw._budget_ok is False


async def test_authorize_rejects_none_context():
    gw = LLMGateway("live", allow_live=True, live_provider=object())
    with pytest.raises(GatewayDeniedError):
        gw.authorize(task_context=None, budget_ok=True)
