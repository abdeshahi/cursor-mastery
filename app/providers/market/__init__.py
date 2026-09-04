"""Market data provider package."""

from app.providers.market.alphavantage import AlphaVantageProvider
from app.providers.market.base import MarketDataProvider
from app.providers.market.factory import build_market_providers
from app.providers.market.fred import FREDProvider
from app.providers.market.nobitex import NobitexProvider
from app.providers.market.tgju import TGJUProvider
from app.providers.market.wallex import WallexProvider

__all__ = [
    "AlphaVantageProvider",
    "FREDProvider",
    "MarketDataProvider",
    "NobitexProvider",
    "TGJUProvider",
    "WallexProvider",
    "build_market_providers",
]
