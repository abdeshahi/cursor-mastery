"""Base collector abstractions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class CollectorRunResult:
    """Summary of a collector execution."""

    provider: str
    saved_count: int = 0
    skipped_count: int = 0
    failure_count: int = 0
    errors: list[str] = field(default_factory=list)


class BaseCollector(ABC):
    """Base class for asynchronous data collectors."""

    @abstractmethod
    async def collect(self, session: AsyncSession) -> list[CollectorRunResult]:
        """Execute collection and return per-provider summaries."""
