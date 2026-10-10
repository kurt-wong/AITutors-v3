"""pytest conftest: dedicated testsuite DB, fail-closed isolation, session rollback.

DB isolation (M3b-R1): automated tests MUST use `aitutors_testsuite` only.
- NEVER `aitutors` (shared business DB)
- NEVER `aitutors_test` (human acceptance DB — real exam data lives there)
"""

import os
from urllib.parse import urlparse

# FORCE dedicated testsuite DB BEFORE any app import. Env vars beat .env in Settings.
# Password is local-dev placeholder shared by all three DBs; not a production secret.
_TEST_DB_URL = "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors_testsuite"

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["APP_SECRET"] = "test-app-secret-32-bytes-minimum!!"

_FORBIDDEN_DB_NAMES = frozenset({"aitutors", "aitutors_test"})


def _db_name_from_url(url: str) -> str:
    path = urlparse(url).path or ""
    return path.lstrip("/").split("?")[0]


def _assert_testsuite_db() -> None:
    """Fail closed if the engine would touch shared or acceptance DBs."""
    from app.core.config import settings

    url = settings.database_url
    name = _db_name_from_url(url)
    if name in _FORBIDDEN_DB_NAMES:
        raise RuntimeError(
            f"TEST ISOLATION VIOLATION: DATABASE_URL targets {name!r} "
            f"({url!r}). Automated tests must use aitutors_testsuite only. "
            "Shared DB = aitutors; human acceptance DB = aitutors_test."
        )
    if name != "aitutors_testsuite":
        raise RuntimeError(
            f"TEST ISOLATION VIOLATION: expected database aitutors_testsuite, "
            f"got {name!r} from {url!r}"
        )


import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config

from app.db.session import async_session_maker

_assert_testsuite_db()


@pytest.fixture(scope="session", autouse=True)
def migrated_db() -> None:
    """Apply schema only on the dedicated testsuite DB."""
    _assert_testsuite_db()
    command.upgrade(Config("alembic.ini"), "head")


@pytest_asyncio.fixture
async def session():
    _assert_testsuite_db()
    async with async_session_maker() as s:
        yield s
        await s.rollback()


@pytest.fixture
def testsuite_url() -> str:
    """Exposed for isolation assertions in tests."""
    _assert_testsuite_db()
    return _TEST_DB_URL


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
    # 8x8 RGB PNG embedded as image
    import struct
    import zlib

    def _png() -> bytes:
        def chunk(tag: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + tag
                + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        ihdr = struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0)
        raw = b"".join(b"\x00" + bytes([255, 0, 0] * 8) for _ in range(8))
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b"")
        )

    page.insert_image(fitz.Rect(100, 100, 200, 200), stream=_png())
    page.insert_text((72, 80), "Caption line")
    data = doc.tobytes()
    doc.close()
    return data
