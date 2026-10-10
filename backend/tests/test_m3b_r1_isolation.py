"""M3b-R1 isolation: automated tests must not touch shared or acceptance DBs."""

from __future__ import annotations

import os
from urllib.parse import urlparse

import pytest

from tests.conftest import _assert_testsuite_db, _db_name_from_url


def test_conftest_points_at_testsuite_only(testsuite_url: str):
    name = _db_name_from_url(testsuite_url)
    assert name == "aitutors_testsuite"
    assert name not in {"aitutors", "aitutors_test"}


def test_settings_database_url_is_testsuite():
    from app.core.config import settings

    name = _db_name_from_url(settings.database_url)
    assert name == "aitutors_testsuite"


def test_assert_testsuite_db_rejects_shared_and_acceptance():
    from app.core.config import settings

    original = settings.database_url
    try:
        settings.database_url = (
            "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors"
        )
        with pytest.raises(RuntimeError, match="ISOLATION VIOLATION"):
            _assert_testsuite_db()

        settings.database_url = (
            "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors_test"
        )
        with pytest.raises(RuntimeError, match="ISOLATION VIOLATION"):
            _assert_testsuite_db()

        settings.database_url = (
            "postgresql+asyncpg://aitutors:change-me@localhost:5432/aitutors_testsuite"
        )
        _assert_testsuite_db()  # must not raise
    finally:
        settings.database_url = original


def test_env_database_url_forced_to_testsuite():
    # conftest sets this before app import; keep the invariant visible
    name = _db_name_from_url(os.environ["DATABASE_URL"])
    assert name == "aitutors_testsuite"


def test_no_hardcoded_production_password_in_tests():
    """Tests may use the local-dev DSN placeholder; must not embed other secrets."""
    from pathlib import Path

    root = Path(__file__).resolve().parent
    offenders = []
    for p in root.rglob("*.py"):
        text = p.read_text(encoding="utf-8", errors="replace")
        if "postgres://" in text or "postgresql://" in text:
            for line in text.splitlines():
                if "aitutors_testsuite" in line or "DATABASE_URL" in line:
                    continue
                if "change-me" in line and "aitutors" in line:
                    # local-dev placeholder is acceptable if targeting testsuite
                    if "aitutors_testsuite" not in line and "/aitutors'" in line:
                        offenders.append(f"{p.name}: {line.strip()[:120]}")
    assert offenders == [], offenders
