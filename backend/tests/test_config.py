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


def test_minimal_required_ok(monkeypatch) -> None:
    """最小必需配置可初始化；_env_file=None + delenv 双层隔离（.env 文件 + OS 环境变量）。"""
    monkeypatch.delenv("LLM_GATEWAY_MODE", raising=False)
    monkeypatch.delenv("MIMO_API_KEY", raising=False)
    s = Settings(
        database_url="postgresql+asyncpg://u:p@h/d",
        app_env="development",
        _env_file=None,
    )
    assert s.database_url == "postgresql+asyncpg://u:p@h/d"
    assert s.app_env == "development"
    assert s.llm_gateway_mode == "disabled"
    assert s.mimo_api_key is None


def test_future_surface_defaults_and_not_required(monkeypatch) -> None:
    """段 A 无 admin endpoint → ADMIN_API_KEY 非 required；LLM_GATEWAY_MODE 默认 disabled。"""
    monkeypatch.delenv("LLM_GATEWAY_MODE", raising=False)
    monkeypatch.delenv("MIMO_API_KEY", raising=False)
    s = Settings(
        database_url="postgresql+asyncpg://u:p@h/d",
        app_env="development",
        _env_file=None,
    )
    assert s.llm_gateway_mode == "disabled"
    assert s.paddleocr_vl_token is None
    assert s.admin_api_key is None
    assert s.embedding_model == "qwen3-embedding:4b"


# ---- BUG-V3-036（C-1）：负 retry 配置必须在 Settings 层 fail-fast ----


def test_negative_llm_request_retry_count_rejects(monkeypatch) -> None:
    """llm_request_retry_count=-1 → ValidationError（ge=0 约束，env/Settings 路径 fail-fast）。"""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+asyncpg://u:p@h/d",
            app_env="development",
            llm_request_retry_count=-1,
            _env_file=None,
        )


def test_negative_http_retry_count_rejects(monkeypatch) -> None:
    """http_retry_count=-1 → ValidationError（ge=0 约束，env/Settings 路径 fail-fast）。"""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+asyncpg://u:p@h/d",
            app_env="development",
            http_retry_count=-1,
            _env_file=None,
        )
