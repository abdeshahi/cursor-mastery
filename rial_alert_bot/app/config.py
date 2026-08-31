from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_RSS_URLS: list[str] = [
    'https://www.bbc.com/persian/business/index.xml',
    'https://www.tejaratnews.com/feed/',
    'https://www.donya-e-eqtesad.com/fa/feeds/?output=xml',
    'https://www.eghtesadonline.com/fa/feeds/?output=xml',
    'https://www.isna.ir/rss/tp/economy',
]

DEFAULT_KEYWORDS: list[str] = [
    'دلار',
    'ارز',
    'ریال',
    'تحریم',
    'نفت',
    'هرمز',
    'بانک مرکزی',
    'نیما',
    'مرکز مبادله',
    'تورم',
    'مذاکره',
    'تفاهم',
    'صادرات',
    'درهم',
    'تتر',
    'امارات',
    'خزانه‌داری',
]

SOURCE_WEIGHTS: dict[str, float] = {
    'bbc_persian': 1.0,
    'tejaratnews': 0.9,
    'donya_e_eqtesad': 0.9,
    'eghtesadonline': 0.85,
    'isna_economy': 0.85,
    'html_fallback': 0.75,
    'telegram_public': 0.6,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    bot_token: str = Field(alias='BOT_TOKEN')
    telegram_admin_ids: str = Field(default='', alias='TELEGRAM_ADMIN_IDS')

    llm_base_url: str = Field(default='https://api.openai.com/v1', alias='LLM_BASE_URL')
    llm_api_key: str = Field(default='', alias='LLM_API_KEY')
    llm_model: str = Field(default='gpt-4o-mini', alias='LLM_MODEL')
    llm_timeout_seconds: float = Field(default=45.0, alias='LLM_TIMEOUT_SECONDS')

    poll_seconds: int = Field(default=180, alias='POLL_SECONDS')
    alert_intensity_min: int = Field(default=7, alias='ALERT_INTENSITY_MIN')
    cluster_window_min: int = Field(default=120, alias='CLUSTER_WINDOW_MIN')
    cluster_score_min: float = Field(default=16.0, alias='CLUSTER_SCORE_MIN')
    timezone: str = Field(default='Asia/Tehran', alias='TIMEZONE')

    database_path: str = Field(default='./data/rial_alert.db', alias='DATABASE_PATH')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')

    news_rss_urls: list[str] = Field(default_factory=lambda: list(DEFAULT_RSS_URLS), alias='NEWS_RSS_URLS')
    news_keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_KEYWORDS), alias='NEWS_KEYWORDS')

    jobs_paused: bool = Field(default=False, alias='JOBS_PAUSED')

    @field_validator('news_rss_urls', mode='before')
    @classmethod
    def parse_rss_urls(cls, value: Any) -> list[str]:
        if value is None or value == '':
            return list(DEFAULT_RSS_URLS)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith('['):
                parsed = json.loads(raw)
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [part.strip() for part in raw.split(',') if part.strip()]
        raise TypeError('NEWS_RSS_URLS must be JSON list or comma-separated string')

    @field_validator('news_keywords', mode='before')
    @classmethod
    def parse_keywords(cls, value: Any) -> list[str]:
        if value is None or value == '':
            return list(DEFAULT_KEYWORDS)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith('['):
                parsed = json.loads(raw)
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [part.strip() for part in raw.split(',') if part.strip()]
        raise TypeError('NEWS_KEYWORDS must be JSON list or comma-separated string')

    @property
    def admin_ids(self) -> set[int]:
        if not self.telegram_admin_ids.strip():
            return set()
        return {int(part.strip()) for part in self.telegram_admin_ids.split(',') if part.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
