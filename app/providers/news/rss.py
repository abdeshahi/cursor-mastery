"""Generic RSS/Atom news provider."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import perf_counter
from typing import Any

import feedparser
import httpx

from app.core.logging import get_logger
from app.models.news import NewsSource
from app.providers.market.http_client import ResilientHttpClient
from app.providers.news.base import NewsProvider
from app.schemas.news import RawNewsArticle

logger = get_logger(__name__)


class RSSNewsProvider(NewsProvider):
    """Fetch articles from RSS/Atom feeds."""

    source_name = "rss"

    def __init__(
        self,
        http_client: ResilientHttpClient | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._http = http_client or ResilientHttpClient()
        self._client = client

    async def fetch_latest(self, source: NewsSource, *, limit: int = 50) -> list[RawNewsArticle]:
        if not source.feed_url:
            raise ValueError(f"source {source.slug} has no feed_url configured")

        started = perf_counter()
        response = await self._http.request("GET", source.feed_url, client=self._client)
        parsed = feedparser.parse(response.text)
        if parsed.bozo and not parsed.entries:
            raise ValueError(f"malformed RSS feed for {source.slug}: {parsed.bozo_exception}")

        received_at = datetime.now(tz=timezone.utc)
        articles: list[RawNewsArticle] = []
        for entry in parsed.entries[:limit]:
            try:
                articles.append(self._normalize_entry(source, entry, received_at))
            except Exception as exc:
                logger.warning(
                    "Skipping malformed RSS entry",
                    extra={"source": source.slug, "error": str(exc)},
                )
        logger.info(
            "RSS fetch complete",
            extra={"source": source.slug, "count": len(articles), "latency_ms": int((perf_counter() - started) * 1000)},
        )
        return articles

    def _normalize_entry(self, source: NewsSource, entry: Any, received_at: datetime) -> RawNewsArticle:
        title = (entry.get("title") or "").strip()
        if not title:
            raise ValueError("RSS entry missing title")

        url = (entry.get("link") or entry.get("id") or "").strip()
        if not url:
            raise ValueError("RSS entry missing url/id")

        body = self._extract_body(entry)
        summary = entry.get("summary") or entry.get("description")
        external_id = entry.get("id") or entry.get("guid") or url
        published_at = self._parse_published(entry)

        return RawNewsArticle(
            external_id=str(external_id)[:512],
            url=url,
            title=title,
            body=body,
            summary=str(summary) if summary else None,
            language=source.language,
            author=entry.get("author"),
            published_at=published_at,
            received_at=received_at,
            raw_metadata={"feed": source.feed_url},
        )

    @staticmethod
    def _extract_body(entry: Any) -> str | None:
        if entry.get("content"):
            value = entry.content[0].get("value")
            if value:
                return str(value)
        for key in ("summary", "description"):
            if isinstance(entry.get(key), str):
                return entry[key]
        return None

    @staticmethod
    def _parse_published(entry: Any) -> datetime | None:
        for key in ("published_parsed", "updated_parsed"):
            parsed = entry.get(key)
            if parsed:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
        for key in ("published", "updated"):
            raw = entry.get(key)
            if not raw:
                continue
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (TypeError, ValueError):
                continue
        return None
