"""Application-wide constants."""

from enum import StrEnum

APP_NAME = "CTTEL Dollar Intelligence Bot"
DEFAULT_TIMEZONE = "Asia/Tehran"
DEFAULT_PAPER_MODE = True

# Health check identifiers
HEALTH_STATUS_HEALTHY = "healthy"
HEALTH_STATUS_DEGRADED = "degraded"
HEALTH_STATUS_UNHEALTHY = "unhealthy"


class MarketSymbol(StrEnum):
    """Known market symbols at launch. New symbols can be stored without enum changes."""

    USD_IRR = "USD_IRR"
    USDT_IRR = "USDT_IRR"
    AED_IRR = "AED_IRR"
    GOLD_18K_IRR = "GOLD_18K_IRR"
    GOLD_OUNCE_USD = "GOLD_OUNCE_USD"
    BRENT_USD = "BRENT_USD"
    DXY = "DXY"


INITIAL_MARKET_SYMBOLS: frozenset[str] = frozenset(symbol.value for symbol in MarketSymbol)


class MarketSourceStatus(StrEnum):
    """Health status for a market data source."""

    HEALTHY = "healthy"
    STALE = "stale"
    FAILING = "failing"
    UNKNOWN = "unknown"
