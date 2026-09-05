"""Tests for RSS news provider."""

from datetime import datetime, timezone

import httpx
import pytest

from app.core.news_constants import NewsSourceType
from app.models.news import NewsSource
from app.providers.news.rss import RSSNewsProvider

SAMPLE_RSS = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Iran central bank updates FX policy</title>
      <link>https://example.com/news/1?utm_source=test</link>
      <guid>guid-1</guid>
      <pubDate>Wed, 03 Sep 2026 12:00:00 GMT</pubDate>
      <description>Policy update body</description>
    </item>
  </channel>
</rss>
"""


@pytest.mark.asyncio
async def test_rss_provider_parses_feed() -> None:
    source = NewsSource(
        id=1,
        name="Test",
        slug="test",
        source_type=NewsSourceType.OFFICIAL.value,
        base_url="https://example.com",
        feed_url="https://example.com/feed.xml",
        reliability_score=1.0,
        language="en",
        country="IR",
        enabled=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=SAMPLE_RSS)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RSSNewsProvider(client=client)
        articles = await provider.fetch_latest(source)

    assert len(articles) == 1
    assert "FX policy" in articles[0].title
    assert articles[0].published_at is not None
    assert articles[0].external_id == "guid-1"


@pytest.mark.asyncio
async def test_rss_malformed_feed_fails() -> None:
    source = NewsSource(
        id=1,
        name="Test",
        slug="test",
        source_type=NewsSourceType.OFFICIAL.value,
        base_url=None,
        feed_url="https://example.com/feed.xml",
        reliability_score=1.0,
        language="en",
        country=None,
        enabled=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<rss><channel></channel>")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RSSNewsProvider(client=client)
        with pytest.raises(ValueError):
            await provider.fetch_latest(source)
