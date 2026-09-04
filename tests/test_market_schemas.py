"""Tests for market data schemas."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.market import MarketPriceCreate, MarketSourceHealthCreate
from app.core.constants import MarketSourceStatus


def _aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc)


def test_market_price_create_requires_explicit_timestamps() -> None:
    with pytest.raises(ValidationError):
        MarketPriceCreate(
            symbol="USD_IRR",
            price=Decimal("950000"),
            source="test_source",
            market_timestamp=_aware(datetime(2026, 1, 1, 12, 0, 0)),
        )


def test_market_price_rejects_non_positive_price() -> None:
    with pytest.raises(ValidationError, match="price must be greater than zero"):
        MarketPriceCreate(
            symbol="USD_IRR",
            price=Decimal("0"),
            source="test_source",
            market_timestamp=_aware(datetime(2026, 1, 1, 12, 0, 0)),
            received_at=_aware(datetime(2026, 1, 1, 12, 0, 1)),
        )


def test_market_price_rejects_negative_bid() -> None:
    with pytest.raises(ValidationError, match="bid and ask must be positive"):
        MarketPriceCreate(
            symbol="USD_IRR",
            price=Decimal("950000"),
            bid=Decimal("-1"),
            source="test_source",
            market_timestamp=_aware(datetime(2026, 1, 1, 12, 0, 0)),
            received_at=_aware(datetime(2026, 1, 1, 12, 0, 1)),
        )


def test_market_price_allows_missing_bid_ask() -> None:
    payload = MarketPriceCreate(
        symbol="USD_IRR",
        price=Decimal("950000.1234567890"),
        source="test_source",
        market_timestamp=_aware(datetime(2026, 1, 1, 12, 0, 0)),
        received_at=_aware(datetime(2026, 1, 1, 12, 0, 1)),
    )
    assert payload.bid is None
    assert payload.ask is None


def test_market_price_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        MarketPriceCreate(
            symbol="USD_IRR",
            price=Decimal("950000"),
            source="test_source",
            market_timestamp=datetime(2026, 1, 1, 12, 0, 0),
            received_at=_aware(datetime(2026, 1, 1, 12, 0, 1)),
        )


def test_market_source_health_create() -> None:
    payload = MarketSourceHealthCreate(
        source="provider_a",
        symbol="USD_IRR",
        status=MarketSourceStatus.HEALTHY,
        last_success_at=_aware(datetime(2026, 1, 1, 12, 0, 0)),
        last_latency_ms=120,
    )
    assert payload.status == MarketSourceStatus.HEALTHY
