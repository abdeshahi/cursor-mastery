"""Tests for REST news provider parsing."""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.core.news_constants import NewsSourceType
from app.models.news import NewsSource
from app.providers.market.http_client import ResilientHttpClient
from app.providers.news.rest import RESTNewsProvider

FIXTURES = Path(__file__).parent / "fixtures" / "news"


def _source() -> NewsSource:
    return NewsSource(
        id=1,
        name="Test REST",
        slug="test-rest",
        source_type=NewsSourceType.WIRE.value,
        base_url='{"api_endpoint":"https://example.com/api/news"}',
        reliability_score=0.9,
        enabled=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


def test_parse_rest_fixture() -> None:
    payload = json.loads((FIXTURES / "rest_sample.json").read_text(encoding="utf-8"))
    articles = RESTNewsProvider.parse_payload(payload, source=_source())
    assert len(articles) == 1
    assert articles[0].external_id == "rest-001"


@pytest.mark.asyncio
async def test_rest_provider_fetch_latest() -> None:
    payload = json.loads((FIXTURES / "rest_sample.json").read_text(encoding="utf-8"))
    http_client = AsyncMock(spec=ResilientHttpClient)
    http_client.get_json = AsyncMock(return_value=payload)

    provider = RESTNewsProvider(http_client=http_client)
    articles = await provider.fetch_latest(_source())
    assert len(articles) == 1
