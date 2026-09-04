"""Market data provider abstraction."""

from abc import ABC, abstractmethod

from app.schemas.provider import ProviderFetchResult


class MarketDataProvider(ABC):
    """Fetch and normalize external market prices."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Stable provider identifier used in persistence."""

    @property
    @abstractmethod
    def supported_symbols(self) -> frozenset[str]:
        """Internal symbols this provider can supply."""

    @abstractmethod
    async def fetch_prices(self, symbols: list[str] | None = None) -> ProviderFetchResult:
        """Fetch and normalize one or more symbols."""

    async def fetch_price(self, symbol: str) -> ProviderFetchResult:
        """Fetch a single symbol."""
        return await self.fetch_prices([symbol])
