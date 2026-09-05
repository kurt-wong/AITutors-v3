"""V3 段 A 配置与密钥校验（00 硬门槛 11：缺失拒绝启动）。

段 A 必填仅 DATABASE_URL + APP_ENV。future configuration surface（LLM_GATEWAY_MODE /
cloud OCR / ollama / embedding / minio / admin_api_key）在段 C/B 接线后才 required；
段 A 提供默认值但**不校验**，保证启动零 LLM、零外部副作用（Gate A1）。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """段 A 配置。缺失必填字段 → pydantic ValidationError，拒绝启动。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- 段 A 必填（缺失 → 启动抛错，00 硬门槛 11）----
    database_url: str
    app_env: str

    # ---- future configuration surface（段 C/B 接线后才 required；段 A 不校验）----
    llm_gateway_mode: str = "disabled"
    paddleocr_vl_token: str | None = None
    paddleocr_api_base_url: str = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
    ollama_base_url: str = ""
    ollama_model: str = ""
    embedding_provider: str = "ollama"
    embedding_model: str = "qwen3-embedding:4b"
    embedding_dimension: int = 2560
    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = ""
    minio_secure: bool = False
    admin_api_key: str | None = None

    # ---- live provider 凭证（30 §6：仅 live 态校验当前 provider；disabled/mock 不要求）----
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = ""
    deepseek_vl_model: str = ""
    mimo_api_key: str | None = None
    mimo_base_url: str = ""
    mimo_model: str = ""
    mimo_vl_model: str = ""
    llm_request_timeout_seconds: float = 30.0


settings = Settings()
