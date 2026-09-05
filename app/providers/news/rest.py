"""REST JSON news provider."""

import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from app.core.logging import get_logger
from app.models.news import NewsSource
from app.providers.market.http_client import ResilientHttpClient
from app.providers.news.base import NewsProvider
from app.schemas.news import RawNewsArticle

logger = get_logger(__name__)


class RESTNewsProvider(NewsProvider):
    """Fetch articles from a JSON REST endpoint."""

    source_name = "rest"

    def __init__(self, http_client: ResilientHttpClient | None = None) -> None:
        self._http = http_client or ResilientHttpClient()

    async def fetch_latest(self, source: NewsSource, *, limit: int = 50) -> list[RawNewsArticle]:
        config = self._load_config(source)
        api_endpoint = config.get("api_endpoint") or source.base_url
        if not api_endpoint:
            raise ValueError(f"source {source.slug} has no REST api_endpoint configured")

        started = perf_counter()
        payload = await self._http.get_json(api_endpoint)
        articles = self.parse_payload(
            payload,
            source=source,
            items_path=config.get("items_path", "items"),
            id_field=config.get("id_field", "id"),
            title_field=config.get("title_field", "title"),
            url_field=config.get("url_field", "url"),
            summary_field=config.get("summary_field", "summary"),
            body_field=config.get("body_field", "body"),
            published_at_field=config.get("published_at_field", "published_at"),
            limit=limit,
        )
        logger.info(
            "REST fetch complete",
            extra={"source": source.slug, "count": len(articles), "latency_ms": int((perf_counter() - started) * 1000)},
        )
        return articles

    @classmethod
    def parse_payload(
        cls,
        payload: dict[str, Any] | list[Any],
        *,
        source: NewsSource,
        items_path: str = "items",
        id_field: str = "id",
        title_field: str = "title",
        url_field: str = "url",
        summary_field: str = "summary",
        body_field: str = "body",
        published_at_field: str = "published_at",
        limit: int = 50,
    ) -> list[RawNewsArticle]:
        items = cls._resolve_items(payload, items_path)[:limit]
        received_at = datetime.now(tz=timezone.utc)
        articles: list[RawNewsArticle] = []

        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get(title_field, "")).strip()
            url = item.get(url_field)
            if not title or not url:
                continue
            external_id = item.get(id_field)
            summary = item.get(summary_field)
            body = item.get(body_field)
            published_at = cls._parse_published_at(item.get(published_at_field))
            articles.append(
                RawNewsArticle(
                    external_id=str(external_id) if external_id is not None else None,
                    url=str(url).strip(),
                    title=title,
                    summary=str(summary).strip() if summary else None,
                    body=str(body).strip() if body else None,
                    language=source.language,
                    published_at=published_at,
                    received_at=received_at,
                    raw_metadata=item,
                )
            )
        return articles

    @staticmethod
    def _load_config(source: NewsSource) -> dict[str, Any]:
        if source.base_url and source.base_url.startswith("{"):
            try:
                parsed = json.loads(source.base_url)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    @staticmethod
    def _resolve_items(payload: dict[str, Any] | list[Any], items_path: str) -> list[Any]:
        if isinstance(payload, list):
            return payload
        current: Any = payload
        for part in items_path.split("."):
            if not isinstance(current, dict):
                return []
            current = current.get(part)
        return current if isinstance(current, list) else []

    @staticmethod
    def _parse_published_at(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        text = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None
