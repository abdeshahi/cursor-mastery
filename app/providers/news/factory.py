"""Build news providers from configured sources."""

import json

from app.core.news_constants import NewsSourceType
from app.models.news import NewsSource
from app.providers.market.http_client import ResilientHttpClient, build_http_client
from app.providers.news.base import NewsProvider
from app.providers.news.financial import FinancialNewsProvider
from app.providers.news.official import OfficialNewsProvider
from app.providers.news.rest import RESTNewsProvider
from app.providers.news.rss import RSSNewsProvider
from app.providers.news.telegram import TelegramNewsProvider


def build_news_provider(source: NewsSource, http_client: ResilientHttpClient | None = None) -> NewsProvider:
    """Return the appropriate provider implementation for a DB source."""
    client = http_client or build_http_client()

    if source.source_type == NewsSourceType.TELEGRAM.value:
        return TelegramNewsProvider()

    config: dict = {}
    if source.base_url and source.base_url.startswith("{"):
        try:
            parsed = json.loads(source.base_url)
            config = parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            config = {}

    if source.feed_url:
        return RSSNewsProvider(http_client=client)

    if config.get("provider") == "rest" or (source.base_url and not source.base_url.startswith("{")):
        return RESTNewsProvider(http_client=client)

    if source.source_type == NewsSourceType.OFFICIAL.value:
        return OfficialNewsProvider()

    if source.source_type in {
        NewsSourceType.IRAN_FINANCIAL_MEDIA.value,
        NewsSourceType.WIRE.value,
        NewsSourceType.MAJOR_MEDIA.value,
    }:
        return FinancialNewsProvider()

    return RSSNewsProvider(http_client=client)
