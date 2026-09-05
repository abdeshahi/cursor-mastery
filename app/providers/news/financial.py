"""Financial source news provider architecture (Phase 4 stub)."""

from app.core.news_constants import NewsSourceType
from app.models.news import NewsSource
from app.providers.news.base import NewsProvider
from app.schemas.news import RawNewsArticle


class FinancialNewsProvider(NewsProvider):
    """Placeholder for proprietary financial news APIs."""

    source_name = "financial"

    async def fetch_latest(self, source: NewsSource, *, limit: int = 50) -> list[RawNewsArticle]:
        raise NotImplementedError(
            f"financial provider adapter not implemented for {NewsSourceType.IRAN_FINANCIAL_MEDIA.value} source {source.slug}"
        )
