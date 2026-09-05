"""Unit tests for OpenAI provider (no live API calls)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.providers.llm.base import LLMErrorCode, LLMProviderError
from app.providers.llm.openai_provider import OpenAIProvider
from app.schemas.analysis import LLMAnalysisRequest
from tests.helpers.analysis import make_valid_llm_output


def _request() -> LLMAnalysisRequest:
    return LLMAnalysisRequest(
        event_id=1,
        prompt_version="NEWS_ANALYZER_PROMPT_V1",
        system_prompt="system",
        user_context="context",
    )


def test_missing_api_key_raises() -> None:
    with pytest.raises(LLMProviderError) as exc_info:
        OpenAIProvider(api_key="", model="gpt-4o-mini")
    assert exc_info.value.error_code == LLMErrorCode.MISSING_API_KEY


def test_empty_model_raises() -> None:
    with pytest.raises(LLMProviderError) as exc_info:
        OpenAIProvider(api_key="sk-test", model="  ")
    assert exc_info.value.error_code == LLMErrorCode.UNSUPPORTED_MODEL


@pytest.mark.asyncio
async def test_openai_successful_parse() -> None:
    provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini", max_retries=1)
    parsed = make_valid_llm_output()
    message = MagicMock()
    message.refusal = None
    message.parsed = parsed
    message.content = None
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]

    with patch.object(provider._client.beta.chat.completions, "parse", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = completion
        result = await provider.analyze_news_event(_request())
    assert result.summary == parsed.summary


@pytest.mark.asyncio
async def test_openai_timeout() -> None:
    from openai import APITimeoutError

    provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini", max_retries=1)
    with patch.object(
        provider._client.beta.chat.completions,
        "parse",
        new_callable=AsyncMock,
        side_effect=APITimeoutError("timeout"),
    ):
        with pytest.raises(LLMProviderError) as exc_info:
            await provider.analyze_news_event(_request())
    assert exc_info.value.error_code == LLMErrorCode.TIMEOUT


@pytest.mark.asyncio
async def test_openai_retry_on_rate_limit() -> None:
    from openai import RateLimitError

    provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini", max_retries=2, retry_backoff_base=0.01)
    parsed = make_valid_llm_output()
    message = MagicMock()
    message.refusal = None
    message.parsed = parsed
    message.content = None
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]

    rate_err = RateLimitError("rate limit", response=MagicMock(), body=None)
    with patch.object(provider._client.beta.chat.completions, "parse", new_callable=AsyncMock) as mock_parse:
        mock_parse.side_effect = [rate_err, completion]
        result = await provider.analyze_news_event(_request())
    assert result.summary == parsed.summary
    assert mock_parse.call_count == 2


@pytest.mark.asyncio
async def test_openai_malformed_json_fallback() -> None:
    provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini", max_retries=1)
    message = MagicMock()
    message.refusal = None
    message.parsed = None
    message.content = "not-json"
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]

    with patch.object(provider._client.beta.chat.completions, "parse", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = completion
        with pytest.raises(LLMProviderError) as exc_info:
            await provider.analyze_news_event(_request())
    assert exc_info.value.error_code == LLMErrorCode.MALFORMED_RESPONSE


@pytest.mark.asyncio
async def test_openai_empty_response() -> None:
    provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini", max_retries=1)
    completion = MagicMock()
    completion.choices = []
    with patch.object(provider._client.beta.chat.completions, "parse", new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = completion
        with pytest.raises(LLMProviderError) as exc_info:
            await provider.analyze_news_event(_request())
    assert exc_info.value.error_code == LLMErrorCode.EMPTY_RESPONSE
