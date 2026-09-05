"""Telegram channel news provider architecture (Phase 15 stub)."""

from app.core.news_constants import NewsSourceType
from app.models.news import NewsSource
from app.providers.news.base import NewsProvider
from app.schemas.news import RawNewsArticle


class TelegramNewsProvider(NewsProvider):
    """Placeholder for Telegram channel ingestion (Phase 15)."""

    source_name = "telegram"

    async def fetch_latest(self, source: NewsSource, *, limit: int = 50) -> list[RawNewsArticle]:
        raise NotImplementedError(
            f"telegram provider not implemented until Phase 15 ({NewsSourceType.TELEGRAM.value})"
        )
