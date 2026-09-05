"""Test helpers for news analysis fixtures."""

from datetime import datetime, timezone

from app.core.news_constants import NewsEventCategory, NewsSourceType
from app.models.news import NewsArticle, NewsEvent, NewsEventArticle, NewsSource
from app.schemas.analysis import AnalysisTimeHorizon, CategoryScores, LLMNewsAnalysisOutput
from app.schemas.news import NewsSourceCreate, RawNewsArticle


def make_valid_llm_output(**overrides) -> LLMNewsAnalysisOutput:
    data = {
        "event_type": NewsEventCategory.SANCTIONS,
        "summary": "New sanctions may pressure USD/IRR upward.",
        "direction_usd_irr": 0.3,
        "impact_score": 6.5,
        "content_confidence": 0.8,
        "event_certainty": 0.75,
        "estimated_market_novelty": 0.6,
        "time_horizon": AnalysisTimeHorizon.MULTI_DAY,
        "category_scores": CategoryScores(
            military=0.0,
            sanctions=8.0,
            negotiation=1.0,
            oil_export=2.0,
            fx_policy=3.0,
            monetary=1.0,
            inflation=1.0,
            foreign_reserves=2.0,
            regional_risk=3.0,
        ),
        "reasoning_summary": "Multiple sources report sanctions; moderate USD/IRR pressure expected.",
    }
    data.update(overrides)
    return LLMNewsAnalysisOutput(**data)


async def seed_event_with_articles(session, *, slug_prefix: str = "test") -> tuple[NewsEvent, list[NewsArticle]]:
    """Create one event with two articles from distinct sources."""
    from app.database.repositories.news_repository import NewsRepository

    repo = NewsRepository()
    now = datetime.now(tz=timezone.utc)

    source_a = await repo.upsert_source(
        session,
        NewsSourceCreate(
            name=f"{slug_prefix}-IRNA",
            slug=f"{slug_prefix}-irna",
            source_type=NewsSourceType.OFFICIAL.value,
            reliability_score=1.0,
            language="en",
        ),
    )
    source_b = await repo.upsert_source(
        session,
        NewsSourceCreate(
            name=f"{slug_prefix}-BBC",
            slug=f"{slug_prefix}-bbc",
            source_type=NewsSourceType.WIRE.value,
            reliability_score=0.95,
            language="en",
        ),
    )

    raw_a = RawNewsArticle(
        external_id=f"{slug_prefix}-a",
        url=f"https://example.com/{slug_prefix}/a",
        title="Central bank announces new FX policy measures",
        body="Policy details regarding foreign exchange controls.",
        received_at=now,
        published_at=now,
    )
    raw_b = RawNewsArticle(
        external_id=f"{slug_prefix}-b",
        url=f"https://example.com/{slug_prefix}/b",
        title="Iran adjusts FX policy amid market pressure",
        summary="Secondary wire report on the same policy shift.",
        received_at=now,
        published_at=now,
    )

    article_a, _ = await repo.save_article_idempotent(session, source_a, raw_a)
    article_b, _ = await repo.save_article_idempotent(session, source_b, raw_b)

    event_read = await repo.cluster_article(session, article_a)
    await repo.attach_article_to_event(session, await _get_event(session, event_read.id), article_b)
    await session.commit()

    event = await _get_event(session, event_read.id)
    return event, [article_a, article_b]


async def _get_event(session, event_id: int) -> NewsEvent:
    from sqlalchemy import select

    return (await session.execute(select(NewsEvent).where(NewsEvent.id == event_id))).scalar_one()
