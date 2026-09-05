"""Tests for news repository persistence."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.news_constants import NewsSourceType
from app.database.repositories.news_repository import NewsRepository
from app.schemas.news import NewsSourceCreate, RawNewsArticle


@pytest.mark.asyncio
async def test_upsert_source_and_save_article(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    source = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="IRNA",
            slug="repo-irna",
            source_type=NewsSourceType.OFFICIAL.value,
            feed_url="https://en.irna.ir/rss",
            reliability_score=1.0,
            language="en",
            country="IR",
        ),
    )
    now = datetime.now(tz=timezone.utc)
    raw = RawNewsArticle(
        external_id="repo-1",
        url="https://example.com/repo/1",
        title="Test headline",
        received_at=now,
        published_at=now,
    )
    article, created = await repo.save_article_idempotent(db_session, source, raw)
    assert created is True
    assert article.id is not None

    again, created_again = await repo.save_article_idempotent(db_session, source, raw)
    assert created_again is False
    assert again.id == article.id


@pytest.mark.asyncio
async def test_reliability_score_persisted(db_session: AsyncSession) -> None:
    repo = NewsRepository()
    source = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="BBC",
            slug="repo-bbc",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://feeds.bbci.co.uk/news/world/rss.xml",
            reliability_score=0.95,
        ),
    )
    assert source.reliability_score == 0.95

    updated = await repo.upsert_source(
        db_session,
        NewsSourceCreate(
            name="BBC World",
            slug="repo-bbc",
            source_type=NewsSourceType.WIRE.value,
            feed_url="https://feeds.bbci.co.uk/news/world/rss.xml",
            reliability_score=0.80,
        ),
    )
    assert updated.reliability_score == 0.80
