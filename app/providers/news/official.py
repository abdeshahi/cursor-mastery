"""Official source news provider architecture (Phase 4 stub)."""

from app.core.news_constants import NewsSourceType
from app.models.news import NewsSource
from app.providers.news.base import NewsProvider
from app.schemas.news import RawNewsArticle


class OfficialNewsProvider(NewsProvider):
    """Placeholder for official institutional feeds without RSS endpoints."""

    source_name = "official"

    async def fetch_latest(self, source: NewsSource, *, limit: int = 50) -> list[RawNewsArticle]:
        raise NotImplementedError(
            f"official provider adapter not implemented for {NewsSourceType.OFFICIAL.value} source {source.slug}"
        )
