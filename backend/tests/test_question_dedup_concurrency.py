"""BUG-V3-027：Question.dedup_key 全局 UNIQUE + 并发幂等（真实 PostgreSQL 真并发）。

dedup_key = Question canonical identity（跨文档），全局唯一；并发 approve 同 dedup_key →
恰 1 Question（修复前真 DB 探针 FAIL：2 Question 重复行）。
"""

import asyncio

import pytest
from sqlalchemy import text

from app.db.session import async_session_maker
from app.repositories.content_repository import ContentRepository

_DEDUP = "d" * 64
_CLEANUP = ("question_instances", "questions")


@pytest.fixture(autouse=True)
async def _cleanup():
    yield
    async with async_session_maker() as s:
        for t in _CLEANUP:
            await s.execute(text(f"DELETE FROM {t}"))
        await s.commit()


async def _create():
    async with async_session_maker() as s:
        q = await ContentRepository(s).create_question(
            subject="数学", grade="7",
            canonical_question_type="single_choice", dedup_key=_DEDUP,
        )
        await s.commit()
        return q.id


async def test_concurrent_create_question_single_row():
    """并发 create_question 同 dedup_key → 恰 1 Question，两调用同一 identity。"""
    ids = await asyncio.gather(_create(), _create())
    assert len(set(ids)) == 1, f"并发 create_question 应收敛到同一 Question，实为 {ids}"
    async with async_session_maker() as s:
        n = (await s.execute(text("SELECT count(*) FROM questions"))).scalar()
    assert n == 1, f"并发应恰 1 Question，实为 {n}"


async def test_serial_recreate_returns_existing_question():
    """串行二次 create 同 dedup_key → 返回既有 Question（不新增）。"""
    q1 = await _create()
    q2 = await _create()
    assert q1 == q2
    async with async_session_maker() as s:
        n = (await s.execute(text("SELECT count(*) FROM questions"))).scalar()
    assert n == 1
