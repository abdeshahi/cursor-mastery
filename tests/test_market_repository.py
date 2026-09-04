"""Tests for market data repository."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MarketSourceStatus
from app.database.repositories.market_repository import MarketRepository
from app.schemas.market import MarketPriceCreate, MarketSourceHealthCreate

UTC = timezone.utc


def _ts(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


@pytest.fixture
def repository() -> MarketRepository:
    return MarketRepository()


@pytest.mark.asyncio
async def test_save_market_price(db_session: AsyncSession, repository: MarketRepository) -> None:
    payload = MarketPriceCreate(
        symbol="USD_IRR",
        price=Decimal("950000.50"),
        bid=Decimal("949900.00"),
        ask=Decimal("950100.00"),
        source="provider_a",
        market_timestamp=_ts(2026, 1, 1, 10),
        received_at=_ts(2026, 1, 1, 10, 1),
    )
    saved = await repository.save_price(db_session, payload)
    await db_session.commit()

    assert saved.id is not None
    assert saved.symbol == "USD_IRR"
    assert saved.price == Decimal("950000.50")
    assert saved.bid == Decimal("949900.00")
    assert saved.ask == Decimal("950100.00")


@pytest.mark.asyncio
async def test_get_latest_price(db_session: AsyncSession, repository: MarketRepository) -> None:
    older = MarketPriceCreate(
        symbol="USD_IRR",
        price=Decimal("940000"),
        source="provider_a",
        market_timestamp=_ts(2026, 1, 1, 9),
        received_at=_ts(2026, 1, 1, 9, 1),
    )
    newer = MarketPriceCreate(
        symbol="USD_IRR",
        price=Decimal("955000"),
        source="provider_b",
        market_timestamp=_ts(2026, 1, 1, 11),
        received_at=_ts(2026, 1, 1, 11, 1),
    )
    await repository.save_price(db_session, older)
    await repository.save_price(db_session, newer)
    await db_session.commit()

    latest = await repository.get_latest_price(db_session, "USD_IRR")
    assert latest is not None
    assert latest.price == Decimal("955000")
    assert latest.source == "provider_b"


@pytest.mark.asyncio
async def test_get_price_history_chronological_order(
    db_session: AsyncSession,
    repository: MarketRepository,
) -> None:
    timestamps = [_ts(2026, 1, 1, h) for h in (8, 10, 9)]
    for index, ts in enumerate(timestamps):
        await repository.save_price(
            db_session,
            MarketPriceCreate(
                symbol="USDT_IRR",
                price=Decimal(f"96000{index}"),
                source="provider_a",
                market_timestamp=ts,
                received_at=ts + timedelta(seconds=1),
            ),
        )
    await db_session.commit()

    history = await repository.get_price_history(
        db_session,
        symbol="USDT_IRR",
        start_time=_ts(2026, 1, 1, 8),
        end_time=_ts(2026, 1, 1, 10),
    )
    assert len(history) == 3
    assert history[0].market_timestamp == _ts(2026, 1, 1, 8)
    assert history[1].market_timestamp == _ts(2026, 1, 1, 9)
    assert history[2].market_timestamp == _ts(2026, 1, 1, 10)
    assert [row.price for row in history] == [
        Decimal("960000"),
        Decimal("960002"),
        Decimal("960001"),
    ]


@pytest.mark.asyncio
async def test_symbol_isolation(db_session: AsyncSession, repository: MarketRepository) -> None:
    await repository.save_price(
        db_session,
        MarketPriceCreate(
            symbol="USD_IRR",
            price=Decimal("950000"),
            source="provider_a",
            market_timestamp=_ts(2026, 1, 1, 10),
            received_at=_ts(2026, 1, 1, 10, 1),
        ),
    )
    await repository.save_price(
        db_session,
        MarketPriceCreate(
            symbol="AED_IRR",
            price=Decimal("260000"),
            source="provider_a",
            market_timestamp=_ts(2026, 1, 1, 10),
            received_at=_ts(2026, 1, 1, 10, 1),
        ),
    )
    await db_session.commit()

    usd_latest = await repository.get_latest_price(db_session, "USD_IRR")
    aed_latest = await repository.get_latest_price(db_session, "AED_IRR")

    assert usd_latest is not None and usd_latest.price == Decimal("950000")
    assert aed_latest is not None and aed_latest.price == Decimal("260000")


@pytest.mark.asyncio
async def test_decimal_precision_preservation(
    db_session: AsyncSession,
    repository: MarketRepository,
) -> None:
    precise_price = Decimal("950123.1234567890")
    saved = await repository.save_price(
        db_session,
        MarketPriceCreate(
            symbol="GOLD_OUNCE_USD",
            price=precise_price,
            source="provider_global",
            market_timestamp=_ts(2026, 1, 1, 10),
            received_at=_ts(2026, 1, 1, 10, 1),
        ),
    )
    await db_session.commit()

    latest = await repository.get_latest_price(db_session, "GOLD_OUNCE_USD")
    assert latest is not None
    assert latest.price == precise_price


@pytest.mark.asyncio
async def test_optional_bid_ask(db_session: AsyncSession, repository: MarketRepository) -> None:
    saved = await repository.save_price(
        db_session,
        MarketPriceCreate(
            symbol="DXY",
            price=Decimal("104.25"),
            source="provider_global",
            market_timestamp=_ts(2026, 1, 1, 10),
            received_at=_ts(2026, 1, 1, 10, 1),
        ),
    )
    await db_session.commit()

    assert saved.bid is None
    assert saved.ask is None


def test_invalid_non_positive_price_rejection() -> None:
    with pytest.raises(ValidationError):
        MarketPriceCreate(
            symbol="USD_IRR",
            price=Decimal("-100"),
            source="provider_a",
            market_timestamp=_ts(2026, 1, 1, 10),
            received_at=_ts(2026, 1, 1, 10, 1),
        )


@pytest.mark.asyncio
async def test_get_latest_prices_for_multiple_symbols(
    db_session: AsyncSession,
    repository: MarketRepository,
) -> None:
    samples = [
        ("USD_IRR", Decimal("950000"), _ts(2026, 1, 1, 10)),
        ("USDT_IRR", Decimal("965000"), _ts(2026, 1, 1, 11)),
        ("AED_IRR", Decimal("260000"), _ts(2026, 1, 1, 9)),
    ]
    for symbol, price, ts in samples:
        await repository.save_price(
            db_session,
            MarketPriceCreate(
                symbol=symbol,
                price=price,
                source="provider_a",
                market_timestamp=ts,
                received_at=ts + timedelta(seconds=1),
            ),
        )
        # Older observation that must not be selected
        await repository.save_price(
            db_session,
            MarketPriceCreate(
                symbol=symbol,
                price=price - Decimal("1000"),
                source="provider_a",
                market_timestamp=ts - timedelta(hours=1),
                received_at=ts - timedelta(hours=1) + timedelta(seconds=1),
            ),
        )
    await db_session.commit()

    latest = await repository.get_latest_prices_for_symbols(
        db_session,
        ["USD_IRR", "USDT_IRR", "AED_IRR", "BRENT_USD"],
    )

    assert latest["USD_IRR"] is not None and latest["USD_IRR"].price == Decimal("950000")
    assert latest["USDT_IRR"] is not None and latest["USDT_IRR"].price == Decimal("965000")
    assert latest["AED_IRR"] is not None and latest["AED_IRR"].price == Decimal("260000")
    assert latest["BRENT_USD"] is None


@pytest.mark.asyncio
async def test_market_source_health_persistence(
    db_session: AsyncSession,
    repository: MarketRepository,
) -> None:
    created = await repository.upsert_source_health(
        db_session,
        MarketSourceHealthCreate(
            source="provider_a",
            symbol="USD_IRR",
            status=MarketSourceStatus.HEALTHY,
            last_success_at=_ts(2026, 1, 1, 10),
            consecutive_failures=0,
            last_latency_ms=85,
        ),
    )
    await db_session.commit()

    assert created.status == MarketSourceStatus.HEALTHY.value
    assert created.last_latency_ms == 85

    updated = await repository.upsert_source_health(
        db_session,
        MarketSourceHealthCreate(
            source="provider_a",
            symbol="USD_IRR",
            status=MarketSourceStatus.FAILING,
            last_failure_at=_ts(2026, 1, 1, 12),
            consecutive_failures=3,
            last_error="timeout",
            last_latency_ms=5000,
        ),
    )
    await db_session.commit()

    fetched = await repository.get_source_health(db_session, "provider_a", "USD_IRR")
    assert fetched is not None
    assert fetched.status == MarketSourceStatus.FAILING.value
    assert fetched.consecutive_failures == 3
    assert fetched.last_error == "timeout"
    assert updated.id == created.id
