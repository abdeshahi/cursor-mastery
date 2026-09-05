"""Tests for news deduplication and clustering."""

from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.news_constants import NewsSourceType
from app.database.repositories.news_repository import NewsRepository
from app.models.news import NewsSource
from app.news.clustering import EventClusterer
from app.news.deduplication import ArticleDeduplicator
from app.schemas.news import NewsSourceCreate, RawNewsArticle

UTC = timezone.utc


@pytest.fixture
def repository() -> NewsRepository:
    return NewsRepository()


async def _create_source(session: AsyncSession, slug: str, reliability: float = 0.8) -> NewsSource:
    repo = NewsRepository()
    created = await repo.upsert_source(
        session,
        NewsSourceCreate(
            name=slug,
            slug=slug,
            source_type=NewsSourceType.MAJOR_MEDIA.value,
            reliability_score=reliability,
            feed_url=f"https://example.com/{slug}.rss",
        ),
    )
    await session.commit()
    return (await session.get(NewsSource, created.id))


def _raw(title: str, *, external_id: str = "ext-1", url: str = "https://example.com/a/1") -> RawNewsArticle:
    now = datetime.now(tz=UTC)
    return RawNewsArticle(
        external_id=external_id,
        url=url,
        title=title,
        body="body text",
        published_at=now,
        received_at=now,
    )


@pytest.mark.asyncio
async def test_duplicate_external_id_is_idempotent(db_session: AsyncSession, repository: NewsRepository) -> None:
    source = await _create_source(db_session, "src-a")
    raw = _raw("US announces new Iran sanctions")
    article1, created1 = await repository.save_article_idempotent(db_session, source, raw)
    await db_session.commit()
    article2, created2 = await repository.save_article_idempotent(db_session, source, raw)
    assert created1 is True
    assert created2 is False
    assert article1.id == article2.id


@pytest.mark.asyncio
async def test_duplicate_content_hash(db_session: AsyncSession, repository: NewsRepository) -> None:
    source = await _create_source(db_session, "src-b")
    now = datetime.now(tz=UTC)
    raw1 = RawNewsArticle(
        external_id="e1",
        url="https://example.com/1?utm_source=x",
        title="Iran inflation rises",
        body="same",
        published_at=now,
        received_at=now,
    )
    raw2 = RawNewsArticle(
        external_id="e2",
        url="https://example.com/1",
        title="Iran inflation rises",
        body="same",
        published_at=now,
        received_at=now,
    )
    _, created1 = await repository.save_article_idempotent(db_session, source, raw1)
    _, created2 = await repository.save_article_idempotent(db_session, source, raw2)
    assert created1 is True
    assert created2 is False


@pytest.mark.asyncio
async def test_unrelated_articles_do_not_merge(db_session: AsyncSession, repository: NewsRepository) -> None:
    source = await _create_source(db_session, "src-c")
    article1, _ = await repository.save_article_idempotent(
        db_session, source, _raw("US announces new Iran sanctions", external_id="1", url="https://ex.com/1")
    )
    await repository.cluster_article(db_session, article1)
    article2, _ = await repository.save_article_idempotent(
        db_session, source, _raw("Iran inflation rises sharply", external_id="2", url="https://ex.com/2")
    )
    event2 = await repository.cluster_article(db_session, article2)
    await db_session.commit()
    events = await repository.get_recent_events(db_session)
    assert len(events) == 2
    assert events[0].category_hint != events[1].category_hint or events[0].id != event2.id


@pytest.mark.asyncio
async def test_same_event_multiple_sources_clusters(db_session: AsyncSession, repository: NewsRepository) -> None:
    source_a = await _create_source(db_session, "wire-a", 0.95)
    source_b = await _create_source(db_session, "wire-b", 0.8)
    title = "US announces new Iran sanctions package"
    article1, _ = await repository.save_article_idempotent(
        db_session, source_a, _raw(title, external_id="a1", url="https://wire-a.com/1")
    )
    await repository.cluster_article(db_session, article1)
    article2, _ = await repository.save_article_idempotent(
        db_session,
        source_b,
        _raw(title + " - updated", external_id="b1", url="https://wire-b.com/2"),
    )
    event = await repository.cluster_article(db_session, article2)
    await db_session.commit()
    articles = await repository.get_event_articles(db_session, event.id)
    assert len(articles) == 2
    assert event.source_count == 2


@pytest.mark.asyncio
async def test_first_published_at_never_moves_forward(db_session: AsyncSession, repository: NewsRepository) -> None:
    source = await _create_source(db_session, "src-d")
    earlier = datetime(2026, 1, 1, 10, tzinfo=UTC)
    later = datetime(2026, 1, 1, 14, tzinfo=UTC)
    article1, _ = await repository.save_article_idempotent(
        db_session,
        source,
        RawNewsArticle(
            external_id="t1",
            url="https://ex.com/t1",
            title="Negotiation talks continue in Geneva",
            published_at=earlier,
            received_at=earlier,
        ),
    )
    event = await repository.cluster_article(db_session, article1)
    article2, _ = await repository.save_article_idempotent(
        db_session,
        source,
        RawNewsArticle(
            external_id="t2",
            url="https://ex.com/t2",
            title="Negotiation talks continue in Geneva today",
            published_at=later,
            received_at=later,
        ),
    )
    merged = await repository.cluster_article(db_session, article2)
    await db_session.commit()
    assert merged.id == event.id
    assert merged.first_published_at == earlier


def test_clusterer_conservative_thresholds() -> None:
    clusterer = EventClusterer()
    from app.models.news import NewsArticle, NewsEvent

    article = NewsArticle(
        id=1,
        source_id=1,
        external_id="1",
        url="https://x/1",
        canonical_url="https://x/1",
        title="US announces new Iran sanctions",
        normalized_title="us announces new iran sanctions",
        body="...",
        summary=None,
        language="en",
        author=None,
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        received_at=datetime(2026, 1, 1, tzinfo=UTC),
        content_hash="abc",
    )
    event = NewsEvent(
        id=1,
        cluster_key="k",
        primary_title="Iran inflation rises",
        normalized_title="iran inflation rises",
        event_time=datetime(2026, 1, 1, tzinfo=UTC),
        first_published_at=datetime(2026, 1, 1, tzinfo=UTC),
        first_received_at=datetime(2026, 1, 1, tzinfo=UTC),
        last_updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        language="en",
        source_count=1,
        article_count=1,
        category_hint="INFLATION",
        status="active",
    )
    decision = clusterer.decide_cluster(article, [event])
    assert decision.created is True
