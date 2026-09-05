"""Tests for MockLLMProvider."""

import pytest

from app.providers.llm.base import LLMErrorCode, LLMProviderError
from app.providers.llm.mock_provider import MockLLMProvider
from app.schemas.analysis import LLMAnalysisRequest
from tests.helpers.analysis import make_valid_llm_output


def _request() -> LLMAnalysisRequest:
    return LLMAnalysisRequest(
        event_id=1,
        prompt_version="NEWS_ANALYZER_PROMPT_V1",
        system_prompt="system",
        user_context="context",
    )


@pytest.mark.asyncio
async def test_mock_provider_valid_result() -> None:
    provider = MockLLMProvider()
    result = await provider.analyze_news_event(_request())
    assert result.summary
    assert provider.metadata.provider_name == "mock"


@pytest.mark.asyncio
async def test_mock_provider_failure() -> None:
    provider = MockLLMProvider(
        fail_with=LLMProviderError("fail", error_code=LLMErrorCode.PROVIDER_ERROR, retryable=False)
    )
    with pytest.raises(LLMProviderError):
        await provider.analyze_news_event(_request())


@pytest.mark.asyncio
async def test_mock_provider_retry_behavior() -> None:
    provider = MockLLMProvider(
        fail_times=2,
        fail_with=LLMProviderError("retry me", error_code=LLMErrorCode.RATE_LIMIT, retryable=True),
    )
    # Direct provider doesn't retry — retry is in OpenAIProvider / NewsAnalyzer layer
    with pytest.raises(LLMProviderError):
        await provider.analyze_news_event(_request())
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_mock_provider_malformed_response() -> None:
    provider = MockLLMProvider(return_malformed_dict={"summary": "incomplete"})
    with pytest.raises(LLMProviderError) as exc_info:
        await provider.analyze_news_event(_request())
    assert exc_info.value.error_code == LLMErrorCode.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_mock_provider_custom_response() -> None:
    custom = make_valid_llm_output(summary="Custom summary text")
    provider = MockLLMProvider(response_factory=lambda _req: custom)
    result = await provider.analyze_news_event(_request())
    assert result.summary == "Custom summary text"
