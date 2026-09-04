"""Validation helpers for provider-normalized quotes."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.schemas.market import MarketPriceCreate
from app.schemas.provider import NormalizedQuote


def quote_to_market_price_create(quote: NormalizedQuote) -> MarketPriceCreate:
    """Convert a normalized provider quote into a persistence schema."""
    return MarketPriceCreate(
        symbol=quote.symbol,
        price=quote.price,
        bid=quote.bid,
        ask=quote.ask,
        source=quote.source,
        market_timestamp=quote.market_timestamp,
        received_at=quote.received_at,
    )


def is_quote_stale(quote: NormalizedQuote, *, max_age: timedelta) -> bool:
    """Detect stale provider timestamps relative to received_at."""
    if quote.is_stale:
        return True
    return quote.received_at - quote.market_timestamp > max_age


def utc_now() -> datetime:
    return datetime.now(tz=ZoneInfo("UTC"))
