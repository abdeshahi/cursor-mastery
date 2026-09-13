from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import feedparser
import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

SOURCE_NAMES = {
    'bbc.com': ('bbc_persian', 'BBC فارسی'),
    'tejaratnews.com': ('tejaratnews', 'تجارت‌نیوز'),
    'donya-e-eqtesad.com': ('donya_e_eqtesad', 'دنیای اقتصاد'),
    'eghtesadonline.com': ('eghtesadonline', 'اقتصاد آنلاین'),
    'isna.ir': ('isna_economy', 'ایسنا اقتصاد'),
}


@dataclass(slots=True)
class NewsItem:
    source_id: str
    source_name: str
    title: str
    summary: str
    link: str
    published_at: datetime | None
    content_hash: str


def _hostname(url: str) -> str:
    return urlparse(url).hostname.replace('www.', '') if urlparse(url).hostname else 'unknown'


def _resolve_source(url: str) -> tuple[str, str]:
    host = _hostname(url)
    for key, value in SOURCE_NAMES.items():
        if host.endswith(key):
            return value
    return host.replace('.', '_'), host


def _strip_html(value: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', value)).strip()


def _parse_date(entry: feedparser.FeedParserDict) -> datetime | None:
    for key in ('published_parsed', 'updated_parsed'):
        parsed = entry.get(key)
        if parsed is not None:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    for key in ('published', 'updated'):
        raw = entry.get(key)
        if isinstance(raw, str) and raw.strip():
            try:
                return parsedate_to_datetime(raw)
            except (TypeError, ValueError):
                continue
    return None


def content_hash(source_id: str, title: str) -> str:
    digest = hashlib.sha256(f'{source_id}:{title.strip()}'.encode('utf-8')).hexdigest()
    return digest[:32]


def matches_keywords(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


async def fetch_rss_items(settings: Settings) -> list[NewsItem]:
    items: list[NewsItem] = []
    timeout = httpx.Timeout(20.0)
    headers = {
        'User-Agent': 'RialAlertBot/1.0 (+https://github.com/local/rial_alert_bot)',
        'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8',
    }

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        for feed_url in settings.news_rss_urls:
            source_id, source_name = _resolve_source(feed_url)
            try:
                response = await client.get(feed_url)
                response.raise_for_status()
                parsed = feedparser.parse(response.text)
            except Exception as error:  # noqa: BLE001
                logger.warning('RSS fetch failed for %s: %s', feed_url, error)
                continue

            for entry in parsed.entries[:30]:
                title = _strip_html(entry.get('title', ''))
                link = entry.get('link') or entry.get('id') or ''
                summary = _strip_html(
                    entry.get('summary') or entry.get('description') or entry.get('content', [{}])[0].get('value', '')
                )
                if not title or not link:
                    continue
                blob = f'{title} {summary}'
                if not matches_keywords(blob, settings.news_keywords):
                    continue
                items.append(
                    NewsItem(
                        source_id=source_id,
                        source_name=source_name,
                        title=title,
                        summary=summary or title,
                        link=link,
                        published_at=_parse_date(entry),
                        content_hash=content_hash(source_id, title),
                    )
                )
    return items
