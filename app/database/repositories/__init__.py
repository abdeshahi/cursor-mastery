"""Database repositories."""

from app.database.repositories.market_repository import MarketRepository
from app.database.repositories.news_repository import NewsRepository

__all__ = ["MarketRepository", "NewsRepository"]
