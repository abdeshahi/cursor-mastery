"""Tests for Level-2 event clustering."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.news_constants import NewsSourceType
from app.database.repositories.news_repository import NewsRepository
from app.models.news import NewsArticle, NewsEvent
from app.news.clustering import EventClusterer
from app.news.deduplication import ArticleDeduplicator
from app.schemas.news import NewsSourceCreate, RawNewsArticle


def _article(
    source_id: int,
    *,
    title: str,
    url: str,
    body: str | None = None,
    published_at: datetime | None = None,
) -> NewsArticle:
    now = datetime.now(tz=timezone.utc)
    raw = RawNewsArticle(
        external_id=url,
        url=url,
        title=title,
        body=body,
        received_at=now,
        published_at=published_at or now,
    )
    fields = ArticleDeduplicator().build_persistence_fields(raw)
    return NewsArticle(source_id=source_id, **fields)


@pytest.mark.asyncio
async def test_similar_articles_cluster_into_one_event(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    source = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="Wire",
            slug="cluster-wire",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://example.com/rss",
            reliability_score=0.95,
        ),
    )
    now = datetime.now(tz=timezone.utc)
    first = _article(
        source.id,
        title="Iran central bank announces new FX policy",
        url="https://example.com/cluster/1",
        published_at=now,
    )
    db_session.add(first)
    await db_session.flush()
    event1 = await repo.cluster_article(db_session, first)

    second = _article(
        source.id,
        title="Iran central bank unveils FX policy changes",
        url="https://example.com/cluster/2",
        published_at=now + timedelta(hours=1),
    )
    db_session.add(second)
    await db_session.flush()
    event2 = await repo.cluster_article(db_session, second)

    assert event1.id == event2.id
    assert event2.article_count >= 2


@pytest.mark.asyncio
async def test_different_categories_do_not_merge(db_session: AsyncSession) -> None:
    repo = NewsRepository(clusterer=EventClusterer(settings=Settings(news_cluster_title_similarity_threshold=0.85)))
    source = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="Wire",
            slug="cluster-cat",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://example.com/rss",
            reliability_score=0.95,
        ),
    )
    now = datetime.now(tz=timezone.utc)
    sanctions = _article(
        source.id,
        title="New sanctions on Iranian banking sector",
        url="https://example.com/cluster/s1",
        published_at=now,
    )
    db_session.add(sanctions)
    await db_session.flush()
    event_s = await repo.cluster_article(db_session, sanctions)

    military = _article(
        source.id,
        title="Military strike reported near border region",
        url="https://example.com/cluster/m1",
        published_at=now + timedelta(hours=1),
    )
    db_session.add(military)
    await db_session.flush()
    event_m = await repo.cluster_article(db_session, military)

    assert event_s.id != event_m.id
    assert event_s.category_hint == "SANCTIONS"
    assert event_m.category_hint == "MILITARY"


@pytest.mark.asyncio
async def test_event_clusterer_creates_new_event_when_no_match() -> None:
    clusterer = EventClusterer()
    now = datetime.now(tz=timezone.utc)
    article = NewsArticle(
        source_id=1,
        external_id="x",
        url="https://example.com/new",
        canonical_url="https://example.com/new",
        title="Unrelated economic report published",
        normalized_title="unrelated economic report published",
        content_hash="abc",
        received_at=now,
        published_at=now,
    )
    decision = clusterer.decide_cluster(article, [])
    assert decision.created is True
    assert decision.event is not None
    assert isinstance(decision.event, NewsEvent)
