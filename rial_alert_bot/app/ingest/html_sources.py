from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import Settings
from app.ingest.rss import NewsItem, content_hash, matches_keywords

logger = logging.getLogger(__name__)

BBC_FALLBACK_URL = 'https://www.bbc.com/persian/business'


async def fetch_bbc_fallback(settings: Settings) -> list[NewsItem]:
    timeout = httpx.Timeout(20.0)
    headers = {'User-Agent': 'RialAlertBot/1.0'}
    items: list[NewsItem] = []

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(BBC_FALLBACK_URL)
            response.raise_for_status()
        except Exception as error:  # noqa: BLE001
            logger.warning('BBC HTML fallback failed: %s', error)
            return items

        soup = BeautifulSoup(response.text, 'html.parser')
        for anchor in soup.select('a[href]')[:80]:
            href = anchor.get('href')
            title = re.sub(r'\s+', ' ', anchor.get_text(strip=True))
            if not href or not title or len(title) < 20:
                continue
            if '/persian/' not in href:
                continue
            link = urljoin(BBC_FALLBACK_URL, href)
            if not matches_keywords(title, settings.news_keywords):
                continue
            items.append(
                NewsItem(
                    source_id='bbc_persian',
                    source_name='BBC فارسی',
                    title=title,
                    summary=title,
                    link=link,
                    published_at=datetime.now(timezone.utc),
                    content_hash=content_hash('bbc_persian', title),
                )
            )
    return items[:20]
