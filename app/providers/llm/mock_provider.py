"""Deterministic mock LLM provider for tests."""

from collections.abc import Callable

from pydantic import ValidationError

from app.core.news_constants import NewsEventCategory
from app.providers.llm.base import LLMErrorCode, LLMProvider, LLMProviderError, LLMProviderMetadata
from app.schemas.analysis import (
    AnalysisTimeHorizon,
    CategoryScores,
    LLMAnalysisRequest,
    LLMNewsAnalysisOutput,
)


def default_mock_output() -> LLMNewsAnalysisOutput:
    return LLMNewsAnalysisOutput(
        event_type=NewsEventCategory.ECONOMIC,
        summary="Mock analysis of the supplied news event.",
        direction_usd_irr=0.1,
        impact_score=4.0,
        content_confidence=0.7,
        event_certainty=0.6,
        estimated_market_novelty=0.5,
        time_horizon=AnalysisTimeHorizon.SHORT_TERM,
        category_scores=CategoryScores(
            military=0.0,
            sanctions=1.0,
            negotiation=0.0,
            oil_export=0.0,
            fx_policy=2.0,
            monetary=3.0,
            inflation=2.0,
            foreign_reserves=1.0,
            regional_risk=1.0,
        ),
        reasoning_summary="Mock provider synthesized event-level assessment from supplied articles.",
    )


class MockLLMProvider(LLMProvider):
    """Configurable mock provider; no network or API keys required."""

    def __init__(
        self,
        *,
        model_name: str = "mock-model-v1",
        response_factory: Callable[[LLMAnalysisRequest], LLMNewsAnalysisOutput] | None = None,
        fail_with: LLMProviderError | None = None,
        fail_times: int = 0,
        return_invalid: bool = False,
        return_malformed_dict: dict | None = None,
        delay_seconds: float = 0.0,
    ) -> None:
        self._model_name = model_name
        self._response_factory = response_factory or (lambda _req: default_mock_output())
        self._fail_with = fail_with
        self._fail_times = fail_times
        self._return_invalid = return_invalid
        self._return_malformed_dict = return_malformed_dict
        self._delay_seconds = delay_seconds
        self._call_count = 0

    @property
    def metadata(self) -> LLMProviderMetadata:
        return LLMProviderMetadata(provider_name="mock", model_name=self._model_name)

    @property
    def call_count(self) -> int:
        return self._call_count

    async def analyze_news_event(self, request: LLMAnalysisRequest) -> LLMNewsAnalysisOutput:
        import asyncio

        self._call_count += 1
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)

        if self._fail_times > 0 and self._call_count <= self._fail_times:
            if self._fail_with:
                raise self._fail_with
            raise LLMProviderError("Mock failure", error_code=LLMErrorCode.PROVIDER_ERROR, retryable=True)

        if self._fail_with is not None:
            raise self._fail_with

        if self._return_malformed_dict is not None:
            try:
                return LLMNewsAnalysisOutput.model_validate(self._return_malformed_dict)
            except ValidationError as exc:
                raise LLMProviderError(
                    "Mock malformed response failed validation",
                    error_code=LLMErrorCode.VALIDATION_ERROR,
                    retryable=False,
                    details={"errors": exc.errors()},
                ) from exc

        if self._return_invalid:
            raise LLMProviderError(
                "Mock invalid structured response",
                error_code=LLMErrorCode.VALIDATION_ERROR,
                retryable=True,
            )

        return self._response_factory(request)
