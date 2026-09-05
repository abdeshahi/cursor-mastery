"""Application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import DEFAULT_PAPER_MODE, DEFAULT_TIMEZONE


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/cttel_dollar_bot",
        description="Async SQLAlchemy database URL",
    )

    # Application
    paper_mode: bool = Field(default=DEFAULT_PAPER_MODE)
    timezone: str = Field(default=DEFAULT_TIMEZONE)
    log_level: str = Field(default="INFO")
    app_name: str = Field(default="CTTEL Dollar Intelligence Bot")
    app_version: str = Field(default="0.1.0")

    # Telegram (Phase 15)
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_admin_chat_ids: str | None = None

    # OpenAI (Phase 5)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    llm_provider: str = "openai"
    llm_mock_model: str = "mock-model-v1"
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 3
    llm_retry_backoff_base: float = 1.0
    llm_max_articles_per_event: int = 8
    llm_max_chars_per_article: int = 1500
    llm_max_total_context_chars: int = 12000
    news_analyzer_prompt_version: str = "NEWS_ANALYZER_PROMPT_V1"

    # Scheduler intervals in seconds (Phase 14)
    analysis_interval: int = 900
    news_interval: int = 600
    market_interval: int = 300
    signal_alert_threshold: float = 0.1

    # Market data providers (Phase 3)
    alphavantage_api_key: str | None = None
    fred_api_key: str | None = None
    tgju_base_url: str = "https://api.tgju.org/v1/market/indicator/summary-table-data"
    provider_connect_timeout: float = 5.0
    provider_read_timeout: float = 15.0
    provider_max_retries: int = 3
    provider_retry_backoff_base: float = 0.5
    provider_retry_backoff_max: float = 4.0
    market_stale_after_seconds: int = 86_400

    # News collection (Phase 4)
    news_cluster_title_similarity_threshold: float = 0.85
    news_cluster_token_similarity_threshold: float = 0.45
    news_cluster_combined_threshold: float = 0.78
    news_cluster_default_window_hours: int = 48
    news_cluster_military_window_hours: int = 12
    news_cluster_sanctions_window_hours: int = 72
    news_cluster_negotiation_window_hours: int = 48
    news_cluster_economic_window_hours: int = 72

    @field_validator("paper_mode", mode="before")
    @classmethod
    def enforce_paper_mode(cls, value: object) -> bool:
        """Phase 1 requires paper mode; reject explicit disable attempts."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"false", "0", "no", "off"}:
                raise ValueError("PAPER_MODE must remain true in this version")
            return normalized in {"true", "1", "yes", "on"}
        if value is False:
            raise ValueError("PAPER_MODE must remain true in this version")
        return bool(value) if value is not None else DEFAULT_PAPER_MODE

    @field_validator("database_url")
    @classmethod
    def validate_async_database_url(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg:// driver for async support")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
