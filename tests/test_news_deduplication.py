"""Tests for Level-1 article deduplication."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.news_constants import NewsSourceType
from app.database.repositories.news_repository import NewsRepository
from app.models.news import NewsArticle
from app.news.deduplication import ArticleDeduplicator
from app.schemas.news import NewsSourceCreate, RawNewsArticle


def _raw(title: str = "Iran FX policy update", url: str = "https://example.com/a/1") -> RawNewsArticle:
    now = datetime.now(tz=timezone.utc)
    return RawNewsArticle(
        external_id="ext-1",
        url=url,
        title=title,
        summary="summary",
        received_at=now,
        published_at=now,
    )


@pytest.mark.asyncio
async def test_dedup_by_url(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    source = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="Test",
            slug="test-dedup-url",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://example.com/rss",
            reliability_score=0.9,
        ),
    )
    dedup = ArticleDeduplicator()
    raw = _raw(url="https://example.com/a/1?utm_source=x")
    fields = dedup.build_persistence_fields(raw)
    db_session.add(NewsArticle(source_id=source.id, **fields))
    await db_session.flush()

    duplicate = await dedup.find_duplicate(db_session, source_id=source.id, raw=_raw())
    assert duplicate is not None


@pytest.mark.asyncio
async def test_dedup_by_external_id(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    source = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="Test",
            slug="test-dedup-ext",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://example.com/rss",
            reliability_score=0.9,
        ),
    )
    dedup = ArticleDeduplicator()
    raw = _raw(url="https://example.com/a/2")
    fields = dedup.build_persistence_fields(raw)
    db_session.add(NewsArticle(source_id=source.id, **fields))
    await db_session.flush()

    other_url = _raw(url="https://example.com/a/3")
    duplicate = await dedup.find_duplicate(db_session, source_id=source.id, raw=other_url)
    assert duplicate is not None


@pytest.mark.asyncio
async def test_dedup_by_content_hash(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    source = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="Test",
            slug="test-dedup-hash",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://example.com/rss",
            reliability_score=0.9,
        ),
    )
    dedup = ArticleDeduplicator()
    raw = _raw(title="Unique title hash", url="https://example.com/a/4")
    fields = dedup.build_persistence_fields(raw)
    db_session.add(NewsArticle(source_id=source.id, **fields))
    await db_session.flush()

    same_content = _raw(title="Unique title hash", url="https://example.com/a/5")
    duplicate = await dedup.find_duplicate(db_session, source_id=source.id, raw=same_content)
    assert duplicate is not None


@pytest.mark.asyncio
async def test_dedup_by_normalized_title(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    source = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="Test",
            slug="test-dedup-title",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://example.com/rss",
            reliability_score=0.9,
        ),
    )
    dedup = ArticleDeduplicator()
    raw = _raw(title="Iran FX Policy - IRNA", url="https://example.com/a/6")
    fields = dedup.build_persistence_fields(raw)
    db_session.add(NewsArticle(source_id=source.id, **fields))
    await db_session.flush()

    title_variant = _raw(title="Iran FX Policy", url="https://example.com/a/7")
    duplicate = await dedup.find_duplicate(db_session, source_id=source.id, raw=title_variant)
    assert duplicate is not None
