"""Tests for prompt/model version persistence."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.news_analyzer import NewsAnalyzer
from app.analysis.prompts import NEWS_ANALYZER_PROMPT_V1
from app.providers.llm.mock_provider import MockLLMProvider
from tests.test_news_analyzer import _seed_multi_source_event


@pytest.mark.asyncio
async def test_prompt_model_version_persistence(db_session: AsyncSession) -> None:
    event_id = await _seed_multi_source_event(db_session, "version")
    provider = MockLLMProvider(model_name="mock-v2")
    analyzer = NewsAnalyzer(provider, prompt_version=NEWS_ANALYZER_PROMPT_V1)
    result = await analyzer.analyze_event(db_session, event_id)
    assert result.analysis is not None
    assert result.analysis.prompt_version == NEWS_ANALYZER_PROMPT_V1
    assert result.analysis.llm_provider == "mock"
    assert result.analysis.llm_model == "mock-v2"
