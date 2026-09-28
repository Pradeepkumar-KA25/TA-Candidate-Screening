from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = "Talent Acquisition API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str
    frontend_cors_origin: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    remember_me_expire_days: int = 7
    integration_encryption_key: str | None = None
    initial_admin_name: str = "Admin User"
    initial_admin_email: str | None = None
    initial_admin_password: str | None = None
    zoho_accounts_base_url: str = "https://accounts.zoho.com"
    zoho_recruit_base_url: str = "https://recruit.zoho.com/recruit/v2"
    zoho_client_id: str | None = None
    zoho_client_secret: str | None = None
    zoho_connection_timeout_seconds: float = 30.0
    zoho_sync_max_records: int = 200
    storage_backend: Literal["local", "azure_blob"] = "local"
    local_storage_root: str = "uploads"
    azure_storage_account_url: str | None = None
    azure_storage_container: str = "candidate-files"
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    ollama_sector_model: str | None = None
    ollama_models: str = ""
    ai_provider_priority: str = "ollama"
    ollama_request_timeout_seconds: float = 90.0
    ollama_upload_timeout_seconds: float = 10.0
    ollama_background_chunk_timeout_seconds: float = 180.0
    ollama_num_predict: int = 2048
    ollama_staged_line_threshold: int = 50
    ollama_section_chunk_lines: int = 12
    ollama_section_overlap_lines: int = 2
    ollama_section_num_predict: int = 512
    sector_enrichment_enabled: bool = True
    sector_enrichment_on_upload: bool = False
    sector_web_context_enabled: bool = True
    sector_web_timeout_seconds: float = 10.0
    sector_minimum_confidence: float = 0.35

    # Phase 1: Resume Enrichment Configuration
    review_batch_size: int = 20  # Number of candidates per review batch
    resume_extraction_timeout_seconds: float = 120.0  # Resume extraction timeout
    resume_extraction_retry_attempts: int = 2  # Retry extraction if it fails
    zoho_write_enabled: bool = False  # SAFETY: Disable Zoho write operations during development

    @model_validator(mode="after")
    def validate_deployment_settings(self) -> "Settings":
        if self.app_env.lower() == "production":
            placeholders = ("change-me", "your-", "localhost", "127.0.0.1")
            deployment_values = {
                "DATABASE_URL": self.database_url,
                "FRONTEND_CORS_ORIGIN": self.frontend_cors_origin,
                "JWT_SECRET_KEY": self.jwt_secret_key,
                "INTEGRATION_ENCRYPTION_KEY": self.integration_encryption_key,
            }
            invalid = [
                name
                for name, value in deployment_values.items()
                if not value or any(placeholder in value.lower() for placeholder in placeholders)
            ]
            if invalid:
                raise ValueError(f"Production settings missing or unsafe: {', '.join(invalid)}")

        if self.storage_backend == "azure_blob" and not self.azure_storage_account_url:
            raise ValueError("AZURE_STORAGE_ACCOUNT_URL is required for Azure Blob storage")

        if self.ollama_base_url:
            self.ollama_base_url = self.ollama_base_url.rstrip("/")

        return self

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

