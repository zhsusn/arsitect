"""Application configuration via Pydantic-Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///data/sdlc-visualizer.db",
        alias="database_url",
    )
    DATABASE_ECHO: bool = Field(default=False, alias="database_echo")

    # Application
    APP_NAME: str = Field(default="SDLC Visualizer API", alias="app_name")
    APP_VERSION: str = Field(default="0.1.0", alias="app_version")
    DEBUG: bool = Field(default=False, alias="debug")

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:5173"],
        alias="cors_origins",
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", alias="log_level")
    LOG_FORMAT: str = Field(default="json", alias="log_format")

    # File upload
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, alias="max_upload_size_mb")
    UPLOAD_DIR: str = Field(default="uploads", alias="upload_dir")

    # Health check
    HEALTH_CHECK_INTERVAL_SECONDS: float = Field(
        default=30.0, alias="health_check_interval_seconds"
    )
    OPENUI_HEALTH_CHECK_ENABLED: bool = Field(default=False, alias="openui_health_check_enabled")
    OPENUI_URL: str | None = Field(default=None, alias="openui_url")

    # Governance auto-fix LLM
    GOVERNANCE_LLM_PROVIDER: str = Field(default="kimi", alias="governance_llm_provider")
    KIMI_CLI_PATH: str = Field(default="kimi", alias="kimi_cli_path")
    OPENAI_API_BASE: str | None = Field(default=None, alias="openai_api_base")
    OPENAI_API_KEY: str | None = Field(default=None, alias="openai_api_key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", alias="openai_model")

    @property
    def upload_path(self) -> Path:
        """Return the upload directory as a Path."""
        return Path(self.UPLOAD_DIR)

    @property
    def project_root(self) -> Path:
        """Return the project root directory (parent of backend/)."""
        return Path(__file__).resolve().parents[3]


settings = Settings()
