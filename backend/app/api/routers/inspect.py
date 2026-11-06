"""QUESTION-VISUAL-INSPECTION-V1：隔离卷库只读浏览 API。

列出/激活 `ml_*` 批次隔离卷库，供前端真实题库可视化切换数据源。
只读定位：本路由不写任何业务表；激活仅切换读出 session factory。
白名单之外的库（aitutors_* 受保护/测试库）永不列出、永不激活。
"""

from __future__ import annotations

import asyncio
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.db.session import (
    DEFAULT_DB_NAME,
    activate_db,
    get_active_db_name,
    inspect_db_allowed,
    is_default_db,
    get_session_maker,
)

router = APIRouter(prefix="/inspect", tags=["inspect"])

_SUBJECT_MAP = {
    "math": "数学",
    "chn": "语文",
    "cn": "语文",
    "eng": "英语",
    "en": "英语",
    "phy": "物理",
    "chem": "化学",
    "bio": "生物",
}


class DatabaseInfo(BaseModel):
    db_name: str
    is_default: bool
    is_active: bool
    series: str | None = None
    subject: str | None = None
    subject_hint: str | None = None
    year: str | None = None
    region: str | None = None
    question_count: int | None = None


class DatabaseListResponse(BaseModel):
    databases: list[DatabaseInfo]
    active_db_name: str
    default_db_name: str


class ActivateRequest(BaseModel):
    db_name: str


def _parse_volume_meta(db_name: str) -> dict:
    """从卷库命名解析批次/学科/年份/地区（best-effort，失败给 None）。"""
    if not db_name.startswith("ml_"):
        return {}
    slug = db_name[3:]
    series = None
    m = re.match(r"^(r\d+(?:fix|close|x)?)_", slug)
    if m:
        series = m.group(1)
        slug = slug[m.end() :]
    subject = None
    year = None
    region = None
    # 形态1: math_2023_jia_wen / chn_2020_tj
    m2 = re.match(r"^([a-z]+)_(\d{4})_(.+)$", slug)
    if m2:
        subject, year, region = m2.group(1), m2.group(2), m2.group(3)
    else:
        # 形态2: chn2020tj / math2023jiawen
        m3 = re.match(r"^([a-z]+?)(\d{4})(.*)$", slug)
        if m3:
            subject = m3.group(1)
            year = m3.group(2)
            region = (m3.group(3) or "").strip("_") or None
        else:
            # 形态3: math_e2e / en_e2e 等
            parts = slug.split("_", 1)
            subject = parts[0] or None
            region = parts[1] if len(parts) > 1 else None
    return {
        "series": series,
        "subject": subject,
        "subject_hint": _SUBJECT_MAP.get(subject or ""),
        "year": year,
        "region": region,
    }


async def _list_ml_databases() -> list[str]:
    async with get_session_maker(DEFAULT_DB_NAME)() as s:
        rows = await s.execute(
            text(
                "SELECT datname FROM pg_database "
                "WHERE datname LIKE 'ml\\_%' ORDER BY datname"
            )
        )
        return [r[0] for r in rows.all()]


async def _count_questions(db_name: str) -> int | None:
    try:
        async with get_session_maker(db_name)() as s:
            return int((await s.execute(text("SELECT count(*) FROM questions"))).scalar_one())
    except Exception:
        return None


@router.get("/databases", response_model=DatabaseListResponse)
async def list_databases() -> DatabaseListResponse:
    """列出可浏览的隔离卷库（白名单 ml_* + 默认库），含题目数。"""
    active = get_active_db_name()
    names = [DEFAULT_DB_NAME] + [
        n for n in await _list_ml_databases() if inspect_db_allowed(n)
    ]
    # Limit concurrent DB connections to avoid exhausting max_connections.
    _sem = asyncio.Semaphore(8)
    async def _count_limited(n: str):
        async with _sem:
            return await _count_questions(n)
    counts = await asyncio.gather(*[_count_limited(n) for n in names])
    out: list[DatabaseInfo] = []
    for name, cnt in zip(names, counts):
        meta = _parse_volume_meta(name)
        out.append(
            DatabaseInfo(
                db_name=name,
                is_default=is_default_db(name),
                is_active=name == active,
                question_count=cnt,
                **meta,
            )
        )
    return DatabaseListResponse(
        databases=out, active_db_name=active, default_db_name=DEFAULT_DB_NAME
    )


@router.get("/active", response_model=DatabaseInfo)
async def get_active() -> DatabaseInfo:
    name = get_active_db_name()
    meta = _parse_volume_meta(name)
    return DatabaseInfo(
        db_name=name,
        is_default=is_default_db(name),
        is_active=True,
        question_count=await _count_questions(name),
        **meta,
    )


@router.post("/activate", response_model=DatabaseInfo)
async def post_activate(body: ActivateRequest) -> DatabaseInfo:
    """切换活动卷库。白名单外/不存在 → 400，不切换。"""
    name = body.db_name.strip()
    if not inspect_db_allowed(name):
        raise HTTPException(status_code=400, detail=f"db not allowed: {name!r}")
    existing = await _list_ml_databases()
    if name != DEFAULT_DB_NAME and name not in existing:
        raise HTTPException(status_code=400, detail=f"db not found: {name!r}")
    activate_db(name)
    meta = _parse_volume_meta(name)
    return DatabaseInfo(
        db_name=name,
        is_default=is_default_db(name),
        is_active=True,
        question_count=await _count_questions(name),
        **meta,
    )
