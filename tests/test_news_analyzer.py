"""Tests for NewsAnalyzer service."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.news_analyzer import NewsAnalyzer
from app.analysis.prompts import NEWS_ANALYZER_PROMPT_V1, SYSTEM_PROMPT_V1
from app.core.news_constants import NewsEventCategory, NewsSourceType
from app.database.repositories.news_repository import NewsRepository
from app.providers.llm.base import LLMErrorCode, LLMProviderError
from app.providers.llm.mock_provider import MockLLMProvider
from app.schemas.analysis import AnalysisTimeHorizon, CategoryScores
from app.schemas.news import NewsSourceCreate, RawNewsArticle
from tests.helpers.analysis import make_valid_llm_output


async def _seed_multi_source_event(session: AsyncSession, slug: str) -> int:
    repo = NewsRepository()
    now = datetime.now(tz=timezone.utc)

    source_a = await repo.upsert_source(
        session,
        NewsSourceCreate(
            name=f"{slug}-IRNA",
            slug=f"{slug}-irna",
            source_type=NewsSourceType.OFFICIAL.value,
            reliability_score=1.0,
        ),
    )
    source_b = await repo.upsert_source(
        session,
        NewsSourceCreate(
            name=f"{slug}-BBC",
            slug=f"{slug}-bbc",
            source_type=NewsSourceType.WIRE.value,
            reliability_score=0.95,
        ),
    )

    raw_a = RawNewsArticle(
        external_id=f"{slug}-a",
        url=f"https://example.com/{slug}/a",
        title="Sanctions announced on financial sector",
        body="Official confirmation of new sanctions.",
        received_at=now,
        published_at=now,
    )
    raw_b = RawNewsArticle(
        external_id=f"{slug}-b",
        url=f"https://example.com/{slug}/b",
        title="Conflicting report denies sanctions",
        body="Wire source claims sanctions were not implemented.",
        received_at=now,
        published_at=now,
    )

    from sqlalchemy import select
    from app.models.news import NewsSource, NewsEvent

    src_a = (await session.execute(select(NewsSource).where(NewsSource.id == source_a.id))).scalar_one()
    article_a, _ = await repo.save_article_idempotent(session, src_a, raw_a)
    event_read = await repo.cluster_article(session, article_a)

    src_b = (await session.execute(select(NewsSource).where(NewsSource.id == source_b.id))).scalar_one()
    article_b, _ = await repo.save_article_idempotent(session, src_b, raw_b)
    event = (await session.execute(select(NewsEvent).where(NewsEvent.id == event_read.id))).scalar_one()
    await repo.attach_article_to_event(session, event, article_b)
    await session.commit()
    return event.id


@pytest.mark.asyncio
async def test_analyze_event_persists_result(db_session: AsyncSession) -> None:
    event_id = await _seed_multi_source_event(db_session, "persist")
    provider = MockLLMProvider()
    analyzer = NewsAnalyzer(provider)
    result = await analyzer.analyze_event(db_session, event_id)
    assert result.success is True
    assert result.cached is False
    assert result.analysis is not None
    assert result.analysis.prompt_version == NEWS_ANALYZER_PROMPT_V1
    assert result.analysis.llm_provider == "mock"
    assert result.analysis.llm_model == "mock-model-v1"


@pytest.mark.asyncio
async def test_idempotent_analysis(db_session: AsyncSession) -> None:
    event_id = await _seed_multi_source_event(db_session, "idempotent")
    provider = MockLLMProvider()
    analyzer = NewsAnalyzer(provider)
    first = await analyzer.analyze_event(db_session, event_id)
    second = await analyzer.analyze_event(db_session, event_id)
    assert first.success and second.success
    assert second.cached is True
    assert first.analysis is not None and second.analysis is not None
    assert first.analysis.id == second.analysis.id


@pytest.mark.asyncio
async def test_force_reanalysis(db_session: AsyncSession) -> None:
    event_id = await _seed_multi_source_event(db_session, "force")
    call_counter = {"n": 0}

    def factory(_req):
        call_counter["n"] += 1
        return make_valid_llm_output(summary=f"Run {call_counter['n']}")

    provider = MockLLMProvider(response_factory=factory)
    analyzer = NewsAnalyzer(provider)
    first = await analyzer.analyze_event(db_session, event_id)
    second = await analyzer.analyze_event(db_session, event_id, force=True)
    assert first.success and second.success
    assert second.cached is False
    assert first.analysis is not None and second.analysis is not None
    assert first.analysis.id == second.analysis.id
    assert second.analysis.summary == "Run 2"
    assert call_counter["n"] == 2


@pytest.mark.asyncio
async def test_provider_failure_no_persistence(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy import select, func
    from app.models.news import NewsAnalysis

    event_id = await _seed_multi_source_event(db_session, "fail")
    provider = MockLLMProvider(
        fail_with=LLMProviderError("down", error_code=LLMErrorCode.PROVIDER_ERROR, retryable=False)
    )
    analyzer = NewsAnalyzer(provider)
    result = await analyzer.analyze_event(db_session, event_id)
    assert result.success is False
    count = (await db_session.execute(select(func.count()).select_from(NewsAnalysis))).scalar_one()
    assert count == 0


@pytest.mark.asyncio
async def test_multi_source_analyzed_once(db_session: AsyncSession) -> None:
    captured: list[str] = []

    def factory(req):
        captured.append(req.user_context)
        return make_valid_llm_output()

    event_id = await _seed_multi_source_event(db_session, "multi")
    provider = MockLLMProvider(response_factory=factory)
    analyzer = NewsAnalyzer(provider)
    await analyzer.analyze_event(db_session, event_id)
    assert len(captured) == 1
    assert "IRNA" in captured[0] or "Official" in captured[0] or "Wire" in captured[0]


@pytest.mark.asyncio
async def test_conflicting_source_context(db_session: AsyncSession) -> None:
    def factory(_req):
        return make_valid_llm_output(
            event_certainty=0.3,
            reasoning_summary="Sources conflict on whether sanctions were implemented.",
        )

    event_id = await _seed_multi_source_event(db_session, "conflict")
    provider = MockLLMProvider(response_factory=factory)
    analyzer = NewsAnalyzer(provider)
    result = await analyzer.analyze_event(db_session, event_id)
    assert result.analysis is not None
    assert result.analysis.event_certainty == 0.3
    assert "conflict" in result.analysis.reasoning_summary.lower()


@pytest.mark.asyncio
async def test_prompt_injection_in_system_prompt() -> None:
    assert "PROMPT INJECTION" in SYSTEM_PROMPT_V1 or "UNTRUSTED" in SYSTEM_PROMPT_V1
    assert "BUY" in SYSTEM_PROMPT_V1
    assert "NEVER" in SYSTEM_PROMPT_V1


@pytest.mark.asyncio
async def test_missing_event(db_session: AsyncSession) -> None:
    provider = MockLLMProvider()
    analyzer = NewsAnalyzer(provider)
    result = await analyzer.analyze_event(db_session, 999999)
    assert result.success is False
    assert result.error_code == "event_not_found"
