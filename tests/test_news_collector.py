"""Tests for news collector pipeline."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.news_collector import NewsCollector
from app.core.news_constants import NewsSourceType
from app.database.repositories.news_repository import NewsRepository
from app.providers.news.base import NewsProvider
from app.schemas.news import NewsSourceCreate, RawNewsArticle


class StubNewsProvider(NewsProvider):
    def __init__(self, articles: list[RawNewsArticle]) -> None:
        self._articles = articles

    async def fetch_latest(self, source, *, limit: int = 50) -> list[RawNewsArticle]:
        return self._articles


def _raw(title: str, url: str) -> RawNewsArticle:
    now = datetime.now(tz=timezone.utc)
    return RawNewsArticle(
        external_id=url,
        url=url,
        title=title,
        summary="summary",
        received_at=now,
        published_at=now,
    )


@pytest.mark.asyncio
async def test_collector_persists_and_clusters(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="Wire",
            slug="collector-wire",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://example.com/rss",
            reliability_score=0.95,
        ),
    )
    await db_session.commit()

    provider = StubNewsProvider(
        [
            _raw("Iran inflation rises in August", "https://example.com/collector/1"),
            _raw("Iran inflation rises in August report", "https://example.com/collector/2"),
        ]
    )
    collector = NewsCollector(repository=repo)
    with patch("app.collectors.news_collector.build_news_provider", return_value=provider):
        results = await collector.collect(db_session)
    await db_session.commit()

    assert results[0].saved_count == 2
    events = await repo.get_recent_events(db_session, limit=5)
    assert len(events) >= 1
    assert events[0].article_count >= 2


@pytest.mark.asyncio
async def test_collector_skips_duplicates(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="Wire",
            slug="collector-dedup",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://example.com/rss",
            reliability_score=0.95,
        ),
    )
    await db_session.commit()

    duplicate = _raw("Duplicate headline", "https://example.com/collector/dup")
    provider = StubNewsProvider([duplicate, duplicate])
    collector = NewsCollector(repository=repo)
    with patch("app.collectors.news_collector.build_news_provider", return_value=provider):
        results = await collector.collect(db_session)
    await db_session.commit()

    assert results[0].saved_count == 1
    assert results[0].skipped_count == 1


@pytest.mark.asyncio
async def test_stub_providers_raise_not_implemented() -> None:
    from app.providers.news.financial import FinancialNewsProvider
    from app.providers.news.official import OfficialNewsProvider
    from app.providers.news.telegram import TelegramNewsProvider

    source = AsyncMock()
    source.slug = "stub"

    for provider in (
        OfficialNewsProvider(),
        FinancialNewsProvider(),
        TelegramNewsProvider(),
    ):
        with pytest.raises(NotImplementedError):
            await provider.fetch_latest(source)
