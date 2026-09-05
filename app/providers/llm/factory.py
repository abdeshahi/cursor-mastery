"""Factory helpers for LLM providers."""

from app.core.config import Settings, get_settings
from app.providers.llm.base import LLMProvider, LLMProviderError, LLMErrorCode
from app.providers.llm.mock_provider import MockLLMProvider
from app.providers.llm.openai_provider import OpenAIProvider


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Create configured LLM provider from settings."""
    cfg = settings or get_settings()
    provider_name = cfg.llm_provider.strip().lower()
    if provider_name == "mock":
        return MockLLMProvider(model_name=cfg.llm_mock_model)
    if provider_name == "openai":
        if not cfg.openai_api_key:
            raise LLMProviderError(
                "OpenAI API key is not configured",
                error_code=LLMErrorCode.MISSING_API_KEY,
                retryable=False,
            )
        return OpenAIProvider(
            api_key=cfg.openai_api_key,
            model=cfg.openai_model,
            timeout_seconds=cfg.llm_timeout_seconds,
            max_retries=cfg.llm_max_retries,
            retry_backoff_base=cfg.llm_retry_backoff_base,
        )
    raise LLMProviderError(
        f"Unsupported LLM provider: {provider_name}",
        error_code=LLMErrorCode.UNKNOWN,
        retryable=False,
    )
