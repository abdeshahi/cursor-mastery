from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from aiogram import Bot

from app.analysis.llm_client import LLMClient
from app.analysis.scorer import compute_weighted_score
from app.config import Settings
from app.runtime_state import RuntimeState
from app.ingest.html_sources import fetch_bbc_fallback
from app.ingest.rss import NewsItem, fetch_rss_items
from app.ingest.telegram_public import fetch_telegram_public_channels
from app.services.alert_engine import AlertEngine
from app.storage.db import Database
from app.storage.models import AnalysisRecord, ArticleRecord

logger = logging.getLogger(__name__)


async def collect_news(settings: Settings) -> list[NewsItem]:
    items = await fetch_rss_items(settings)
    if not any(item.source_id == 'bbc_persian' for item in items):
        items.extend(await fetch_bbc_fallback(settings))
    items.extend(await fetch_telegram_public_channels())
    dedup: dict[str, NewsItem] = {}
    for item in items:
        dedup[item.content_hash] = item
    return list(dedup.values())


async def poll_news_once(
    *,
    bot: Bot,
    db: Database,
    settings: Settings,
    alert_engine: AlertEngine,
    runtime: RuntimeState,
) -> int:
    if runtime.jobs_paused:
        logger.info('Jobs paused; skipping poll')
        return 0

    llm = LLMClient(settings)
    processed = 0
    news_items = await collect_news(settings)

    for item in news_items:
        try:
            if await db.article_exists_recently(item.content_hash, hours=24):
                continue

            article_id = await db.insert_article(
                ArticleRecord(
                    id=None,
                    source_id=item.source_id,
                    source_name=item.source_name,
                    title=item.title,
                    summary=item.summary,
                    link=item.link,
                    content_hash=item.content_hash,
                    published_at=item.published_at,
                    fetched_at=datetime.now(timezone.utc),
                )
            )

            analysis = await llm.analyze_news(
                source_name=item.source_name,
                title=item.title,
                summary=item.summary,
            )
            weighted = compute_weighted_score(analysis, source_id=item.source_id)
            await db.insert_analysis(
                AnalysisRecord(
                    id=None,
                    article_id=article_id,
                    direction=analysis.direction,
                    intensity=analysis.intensity,
                    horizon=analysis.horizon,
                    confidence=analysis.confidence,
                    event_type=analysis.event_type,
                    is_rumor=analysis.is_rumor,
                    summary_fa=analysis.summary_fa,
                    why_fa=analysis.why_fa,
                    weighted_score=weighted,
                    raw_json=json.dumps(analysis.model_dump(), ensure_ascii=False),
                    created_at=datetime.now(timezone.utc),
                )
            )

            if analysis.direction != 'neutral':
                await alert_engine.dispatch_for_analysis(
                    analysis,
                    source_name=item.source_name,
                    link=item.link,
                    weighted_score=weighted,
                )
            processed += 1
        except Exception as error:  # noqa: BLE001
            logger.exception('Failed processing article %s: %s', item.title, error)
            continue

    logger.info('Poll finished; processed=%s', processed)
    return processed
