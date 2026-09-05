"""段 A 配置/密钥校验测试（00 硬门槛 11：缺失拒绝启动）。"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_missing_database_url_rejects_startup(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(ValidationError):
        Settings(app_env="development", _env_file=None)


def test_missing_app_env_rejects_startup(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql+asyncpg://u:p@h/d", _env_file=None)


def test_minimal_required_ok() -> None:
    s = Settings(database_url="postgresql+asyncpg://u:p@h/d", app_env="development")
    assert s.database_url == "postgresql+asyncpg://u:p@h/d"
    assert s.app_env == "development"


def test_future_surface_defaults_and_not_required() -> None:
    """段 A 无 admin endpoint → ADMIN_API_KEY 非 required；LLM_GATEWAY_MODE 默认 disabled。"""
    s = Settings(database_url="postgresql+asyncpg://u:p@h/d", app_env="development")
    assert s.llm_gateway_mode == "disabled"
    assert s.paddleocr_vl_token is None
    assert s.admin_api_key is None
    assert s.embedding_model == "qwen3-embedding:4b"
