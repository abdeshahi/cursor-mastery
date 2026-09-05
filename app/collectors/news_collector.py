"""Asynchronous news collector."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import BaseCollector, CollectorRunResult
from app.core.logging import get_logger
from app.database.repositories.news_repository import NewsRepository
from app.providers.news.factory import build_news_provider

logger = get_logger(__name__)


class NewsCollector(BaseCollector):
    """Fetch news from configured sources, deduplicate, and cluster events."""

    def __init__(self, repository: NewsRepository | None = None) -> None:
        self._repository = repository or NewsRepository()

    async def collect(self, session: AsyncSession) -> list[CollectorRunResult]:
        results: list[CollectorRunResult] = []
        sources = await self._repository.get_enabled_sources(session)

        for source in sources:
            summary = CollectorRunResult(provider=source.slug)
            provider = build_news_provider(source)
            try:
                raw_articles = await provider.fetch_latest(source)
                for raw in raw_articles:
                    article, created = await self._repository.save_article_idempotent(session, source, raw)
                    if created:
                        await self._repository.cluster_article(session, article)
                        summary.saved_count += 1
                    else:
                        summary.skipped_count += 1
            except NotImplementedError as exc:
                summary.failure_count += 1
                summary.errors.append(str(exc))
            except Exception as exc:
                summary.failure_count += 1
                summary.errors.append(str(exc))
                logger.warning("News collector failure", extra={"source": source.slug, "error": str(exc)})
            results.append(summary)

        return results
