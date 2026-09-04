"""Build configured market data providers from application settings."""

from app.core.config import Settings, get_settings
from app.providers.market.alphavantage import AlphaVantageProvider
from app.providers.market.base import MarketDataProvider
from app.providers.market.fred import FREDProvider
from app.providers.market.http_client import build_http_client
from app.providers.market.nobitex import NobitexProvider
from app.providers.market.tgju import TGJUProvider
from app.providers.market.wallex import WallexProvider


def build_market_providers(settings: Settings | None = None) -> list[MarketDataProvider]:
    """Return all configured market data providers."""
    resolved = settings or get_settings()
    http_client = build_http_client(lambda: resolved)

    providers: list[MarketDataProvider] = [
        TGJUProvider(http_client=http_client, stale_after_seconds=resolved.market_stale_after_seconds),
        NobitexProvider(http_client=http_client),
        WallexProvider(http_client=http_client),
        FREDProvider(api_key=resolved.fred_api_key, http_client=http_client),
        AlphaVantageProvider(api_key=resolved.alphavantage_api_key, http_client=http_client),
    ]
    return providers
