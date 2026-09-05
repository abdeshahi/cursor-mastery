"""One-shot live OpenAI smoke test for NewsAnalyzer. Requires OPENAI_API_KEY env var."""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import select, func

from app.analysis.news_analyzer import NewsAnalyzer
from app.core.config import get_settings
from app.core.news_constants import NewsSourceType
from app.database.db import create_engine, dispose_engine, get_session_factory
from app.database.repositories.news_repository import NewsRepository
from app.models.news import NewsAnalysis, NewsEvent, NewsSource
from app.providers.llm.factory import create_llm_provider
from app.schemas.analysis import LLMNewsAnalysisOutput
from app.schemas.news import NewsSourceCreate, RawNewsArticle


FORBIDDEN_SIGNALS = frozenset({"buy", "sell", "strong_buy", "strong_sell", "signal", "source_reliability"})


async def _ensure_test_event(session) -> int:
    repo = NewsRepository()
    existing = (
        await session.execute(select(NewsEvent).order_by(NewsEvent.id.desc()).limit(1))
    ).scalar_one_or_none()
    if existing is not None:
        return existing.id

    now = datetime.now(tz=timezone.utc)
    source = await repo.upsert_source(
        session,
        NewsSourceCreate(
            name="Smoke IRNA",
            slug="smoke-irna-live",
            source_type=NewsSourceType.OFFICIAL.value,
            reliability_score=1.0,
            language="en",
        ),
    )
    src = (await session.execute(select(NewsSource).where(NewsSource.id == source.id))).scalar_one()
    raw = RawNewsArticle(
        external_id="smoke-live-1",
        url="https://example.com/smoke/live/1",
        title="Iran central bank reviews foreign exchange policy amid market volatility",
        summary=(
            "Official sources report a review of FX policy measures. "
            "No trading recommendation is implied by this test headline."
        ),
        body="Policy review context only for smoke testing structured LLM analysis output.",
        received_at=now,
        published_at=now,
    )
    article, _ = await repo.save_article_idempotent(session, src, raw)
    event_read = await repo.cluster_article(session, article)
    await session.commit()
    return event_read.id


async def main() -> int:
    get_settings.cache_clear()
    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("OPENAI LIVE: CREDENTIAL_REQUIRED")
        return 2

    settings = get_settings()
    model = settings.openai_model
    create_engine(settings)
    session_factory = get_session_factory()

    try:
        provider = create_llm_provider(settings)
        analyzer = NewsAnalyzer(provider, settings=settings)

        async with session_factory() as session:
            event_id = await _ensure_test_event(session)
            result = await analyzer.analyze_event(session, event_id, force=True)

        if not result.success or result.analysis is None:
            print("OPENAI LIVE: FAIL")
            print(f"error_code={result.error_code}")
            print(f"error_message={result.error_message}")
            return 1

        analysis = result.analysis
        schema_fields = set(LLMNewsAnalysisOutput.model_fields.keys())
        output_text = f"{analysis.summary} {analysis.reasoning_summary}".lower()

        checks = {
            "schema_persisted": bool(analysis.id),
            "prompt_version": bool(analysis.prompt_version),
            "llm_provider": analysis.llm_provider == "openai",
            "llm_model": analysis.llm_model == model,
            "no_forbidden_fields": schema_fields.isdisjoint(FORBIDDEN_SIGNALS),
            "no_buy_sell_text": not any(
                token in output_text for token in (" strong buy", " strong sell", " buy dollars", " sell dollars")
            ),
            "direction_in_range": -1.0 <= analysis.direction_usd_irr <= 1.0,
            "impact_in_range": 0.0 <= analysis.impact_score <= 10.0,
        }

        async with session_factory() as session:
            count = (
                await session.execute(
                    select(func.count()).select_from(NewsAnalysis).where(NewsAnalysis.event_id == event_id)
                )
            ).scalar_one()

        checks["persistence_count"] = count >= 1

        if all(checks.values()):
            print("OPENAI LIVE: PASS")
            print(f"OPENAI MODEL: {model}")
            print(f"event_id={event_id}")
            print(f"analysis_id={analysis.id}")
            print(f"prompt_version={analysis.prompt_version}")
            print(f"llm_provider={analysis.llm_provider}")
            print(f"llm_model={analysis.llm_model}")
            print(f"event_type={analysis.event_type}")
            return 0

        print("OPENAI LIVE: FAIL")
        for name, ok in checks.items():
            if not ok:
                print(f"failed_check={name}")
        return 1
    except Exception:
        print("OPENAI LIVE: FAIL")
        return 1
    finally:
        await dispose_engine()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
