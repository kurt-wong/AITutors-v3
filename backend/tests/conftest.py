"""pytest conftest：env 注入（app import 前）、session 迁移、async session 回滚隔离。"""

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors",
)

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config

from app.db.session import async_session_maker


@pytest.fixture(scope="session", autouse=True)
def migrated_db() -> None:
    """确保段 A baseline（19 表）已应用（幂等）。"""
    command.upgrade(Config("alembic.ini"), "head")


@pytest_asyncio.fixture
async def session():
    async with async_session_maker() as s:
        yield s
        await s.rollback()


@pytest.fixture
def pdf_bytes() -> bytes:
    """PyMuPDF 生成的两页文本层 PDF（本地确定性，非外部资产）。"""
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Alpha 1 first line")
    page.insert_text((72, 96), "Beta 2 second line")
    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((72, 72), "Gamma 3 third line")
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def pdf_bytes_with_figure() -> bytes:
    """PyMuPDF 生成的一页文本 + 一张已放置图片 PDF（本地确定性，非外部资产）。

    BUG-011-B：native 图提取需真实 image placement（get_image_info 可定位 + xref 可
    extract_image），区别于纯文本 pdf_bytes（figures=()）。
    """
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Alpha 1 first line")
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 20, 20), True)
    page.insert_image(fitz.Rect(72, 200, 172, 300), pixmap=pix)
    data = doc.tobytes()
    doc.close()
    return data

