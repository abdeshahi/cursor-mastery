"""Tests for RSS news provider parsing."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import feedparser
import pytest

from app.core.news_constants import NewsSourceType
from app.models.news import NewsSource
from app.providers.market.http_client import ResilientHttpClient
from app.providers.news.rss import RSSNewsProvider

FIXTURES = Path(__file__).parent / "fixtures" / "news"


def _source() -> NewsSource:
    return NewsSource(
        id=1,
        name="Test RSS",
        slug="test-rss",
        source_type=NewsSourceType.WIRE.value,
        feed_url="https://example.com/rss",
        reliability_score=0.9,
        enabled=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


def test_feedparser_parses_fixture() -> None:
    xml_text = (FIXTURES / "rss_sample.xml").read_text(encoding="utf-8")
    parsed = feedparser.parse(xml_text)
    assert len(parsed.entries) == 2
    assert "Iran central bank" in parsed.entries[0].title


@pytest.mark.asyncio
async def test_rss_provider_fetch_latest() -> None:
    xml_text = (FIXTURES / "rss_sample.xml").read_text(encoding="utf-8")
    response = AsyncMock()
    response.text = xml_text
    http_client = AsyncMock(spec=ResilientHttpClient)
    http_client.request = AsyncMock(return_value=response)

    provider = RSSNewsProvider(http_client=http_client)
    articles = await provider.fetch_latest(_source())
    assert len(articles) == 2
    assert articles[0].external_id == "fx-policy-001"
    assert articles[0].received_at.tzinfo is not None
