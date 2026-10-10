"""pytest conftest: env injection (before app import), session isolation, rollback.

DB isolation (B1-R2-BOUNDARY-AND-DB-ISOLATION-03): tests MUST run against
aitutors_test, never the shared business DB `aitutors`.
"""

import os

# FORCE isolated test DB BEFORE any app import. Env vars beat .env in Settings.
_TEST_DB_URL = "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors_test"

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["APP_SECRET"] = "test-app-secret-32-bytes-minimum!!"


def _assert_not_shared_db() -> None:
    """Fail fast if the session factory points at the shared business DB."""
    from app.core.config import settings

    url = settings.database_url
    if url.rstrip("/").endswith("/aitutors") or url.rstrip("/").endswith("/aitutors?"):
        raise RuntimeError(
            f"TEST ISOLATION VIOLATION: DATABASE_URL points at shared DB: {url!r}. "
            "Tests must run against aitutors_test."
        )
    if "aitutors_test" not in url:
        raise RuntimeError(
            f"TEST ISOLATION VIOLATION: expected aitutors_test in DATABASE_URL, got {url!r}"
        )


import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config

from app.db.session import async_session_maker

_assert_not_shared_db()


@pytest.fixture(scope="session", autouse=True)
def migrated_db() -> None:
    """Ensure Phase A baseline schema is applied on the isolated test DB."""
    _assert_not_shared_db()
    command.upgrade(Config("alembic.ini"), "head")


@pytest_asyncio.fixture
async def session():
    _assert_not_shared_db()
    async with async_session_maker() as s:
        yield s
        await s.rollback()


@pytest.fixture
def pdf_bytes() -> bytes:
    """PyMuPDF-generated two-page text-only PDF (local deterministic, not external)."""
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
    """PyMuPDF one-page PDF with a real image placement (get_image_info + xref)."""
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Alpha 1 first line")
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 20, 20), True)
    page.insert_image(fitz.Rect(72, 200, 172, 300), pixmap=pix)
    data = doc.tobytes()
    doc.close()
    return data
