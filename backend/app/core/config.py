from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = "Talent Acquisition API"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/talent_acquisition"
    cors_origins: str = "http://localhost:4200"
    jwt_secret_key: str = "change-me-in-production-please-use-a-long-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    remember_me_expire_days: int = 7
    integration_encryption_key: str | None = None
    zoho_accounts_base_url: str = "https://accounts.zoho.com"
    zoho_recruit_base_url: str = "https://recruit.zoho.com/recruit/v2"
    zoho_client_id: str | None = None
    zoho_client_secret: str | None = None
    zoho_connection_timeout_seconds: float = 30.0
    zoho_sync_max_records: int = 200
    zoho_resume_storage_path: str = "uploads/resumes"
    ollama_base_url: str | None = None
    ollama_host: str | None = None
    ollama_model: str = "llama3.1"
    ai_provider_priority: str = "ollama"
    openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_ad_token: str | None = None
    azure_openai_api_version: str = "2024-10-21"
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

