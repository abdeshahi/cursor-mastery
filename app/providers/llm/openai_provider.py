"""OpenAI LLM provider with structured output support."""

import asyncio
import logging
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import ValidationError

from app.providers.llm.base import LLMErrorCode, LLMProvider, LLMProviderError, LLMProviderMetadata
from app.schemas.analysis import LLMAnalysisRequest, LLMNewsAnalysisOutput

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI chat completions with native structured parsing."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
        retry_backoff_base: float = 1.0,
    ) -> None:
        if not api_key or not api_key.strip():
            raise LLMProviderError(
                "OpenAI API key is not configured",
                error_code=LLMErrorCode.MISSING_API_KEY,
                retryable=False,
            )
        self._api_key = api_key.strip()
        self._model = model.strip()
        if not self._model:
            raise LLMProviderError(
                "OpenAI model name is empty",
                error_code=LLMErrorCode.UNSUPPORTED_MODEL,
                retryable=False,
            )
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(1, max_retries)
        self._retry_backoff_base = retry_backoff_base
        self._client = AsyncOpenAI(api_key=self._api_key, timeout=timeout_seconds)

    @property
    def metadata(self) -> LLMProviderMetadata:
        return LLMProviderMetadata(provider_name="openai", model_name=self._model)

    async def analyze_news_event(self, request: LLMAnalysisRequest) -> LLMNewsAnalysisOutput:
        last_error: LLMProviderError | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return await self._call_once(request)
            except LLMProviderError as exc:
                last_error = exc
                if not exc.retryable or attempt >= self._max_retries:
                    raise
                backoff = self._retry_backoff_base * (2 ** (attempt - 1))
                logger.warning(
                    "OpenAI analysis retry",
                    extra={
                        "attempt": attempt,
                        "error_code": exc.error_code,
                        "backoff_seconds": backoff,
                        "event_id": request.event_id,
                    },
                )
                await asyncio.sleep(backoff)
        assert last_error is not None
        raise last_error

    async def _call_once(self, request: LLMAnalysisRequest) -> LLMNewsAnalysisOutput:
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_context},
        ]
        try:
            completion = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=messages,
                response_format=LLMNewsAnalysisOutput,
            )
        except APITimeoutError as exc:
            raise LLMProviderError(
                "OpenAI request timed out",
                error_code=LLMErrorCode.TIMEOUT,
                retryable=True,
            ) from exc
        except RateLimitError as exc:
            raise LLMProviderError(
                "OpenAI rate limit exceeded",
                error_code=LLMErrorCode.RATE_LIMIT,
                retryable=True,
            ) from exc
        except APIConnectionError as exc:
            raise LLMProviderError(
                "OpenAI connection failed",
                error_code=LLMErrorCode.HTTP_ERROR,
                retryable=True,
            ) from exc
        except Exception as exc:  # noqa: BLE001 — map provider errors safely
            raise self._map_generic_error(exc) from exc

        if not completion.choices:
            raise LLMProviderError(
                "OpenAI returned empty choices",
                error_code=LLMErrorCode.EMPTY_RESPONSE,
                retryable=True,
            )

        message = completion.choices[0].message
        if message.refusal:
            raise LLMProviderError(
                f"OpenAI refused request: {message.refusal}",
                error_code=LLMErrorCode.PROVIDER_ERROR,
                retryable=False,
            )

        parsed = message.parsed
        if parsed is not None:
            return parsed

        raw_content = message.content
        if not raw_content:
            raise LLMProviderError(
                "OpenAI returned empty content",
                error_code=LLMErrorCode.EMPTY_RESPONSE,
                retryable=True,
            )

        return self._parse_fallback_json(raw_content)

    def _parse_fallback_json(self, content: str) -> LLMNewsAnalysisOutput:
        """Fallback when structured parse is unavailable for the configured model."""
        import json

        try:
            data: Any = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(
                "OpenAI response is not valid JSON",
                error_code=LLMErrorCode.MALFORMED_RESPONSE,
                retryable=True,
            ) from exc

        try:
            return LLMNewsAnalysisOutput.model_validate(data)
        except ValidationError as exc:
            raise LLMProviderError(
                "OpenAI response failed schema validation",
                error_code=LLMErrorCode.VALIDATION_ERROR,
                retryable=True,
                details={"errors": exc.errors()},
            ) from exc

    def _map_generic_error(self, exc: Exception) -> LLMProviderError:
        msg = str(exc).lower()
        if "model" in msg and ("not found" in msg or "does not exist" in msg):
            return LLMProviderError(
                f"OpenAI model not supported: {self._model}",
                error_code=LLMErrorCode.UNSUPPORTED_MODEL,
                retryable=False,
            )
        return LLMProviderError(
            "OpenAI provider error",
            error_code=LLMErrorCode.PROVIDER_ERROR,
            retryable=True,
            details={"error_type": type(exc).__name__},
        )
