"""News provider package."""

from app.providers.news.base import NewsProvider
from app.providers.news.factory import build_news_provider
from app.providers.news.financial import FinancialNewsProvider
from app.providers.news.official import OfficialNewsProvider
from app.providers.news.rest import RESTNewsProvider
from app.providers.news.rss import RSSNewsProvider
from app.providers.news.telegram import TelegramNewsProvider

__all__ = [
    "NewsProvider",
    "RSSNewsProvider",
    "RESTNewsProvider",
    "OfficialNewsProvider",
    "FinancialNewsProvider",
    "TelegramNewsProvider",
    "build_news_provider",
]
