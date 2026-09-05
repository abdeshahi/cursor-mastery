"""Database repositories."""

from app.database.repositories.analysis_repository import AnalysisRepository
from app.database.repositories.market_repository import MarketRepository
from app.database.repositories.news_repository import NewsRepository

__all__ = ["AnalysisRepository", "MarketRepository", "NewsRepository"]
