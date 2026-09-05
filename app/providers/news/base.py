"""News provider abstraction."""

from abc import ABC, abstractmethod

from app.models.news import NewsSource
from app.schemas.news import RawNewsArticle


class NewsProvider(ABC):
    """Fetch and normalize news articles from an external source."""

    @abstractmethod
    async def fetch_latest(self, source: NewsSource, *, limit: int = 50) -> list[RawNewsArticle]:
        """Fetch latest articles for a configured source."""
