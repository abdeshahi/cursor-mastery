"""Tests for LLM provider factory and configuration."""

import pytest

from app.providers.llm.base import LLMErrorCode, LLMProviderError
from app.providers.llm.factory import create_llm_provider
from app.providers.llm.mock_provider import MockLLMProvider
from app.providers.llm.openai_provider import OpenAIProvider


def test_create_mock_provider(test_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    get_settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()
    provider = create_llm_provider(get_settings())
    assert isinstance(provider, MockLLMProvider)


def test_missing_openai_api_key(test_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()
    settings = get_settings()
    with pytest.raises(LLMProviderError) as exc_info:
        create_llm_provider(settings)
    assert exc_info.value.error_code == LLMErrorCode.MISSING_API_KEY


def test_create_openai_provider_with_key(test_settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    get_settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings
    get_settings.cache_clear()
    provider = create_llm_provider(get_settings())
    assert isinstance(provider, OpenAIProvider)
    assert provider.metadata.model_name == "gpt-4o-mini"
