"""LLM provider abstraction for news analysis."""

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel

from app.core.exceptions import AppError
from app.schemas.analysis import LLMAnalysisRequest, LLMNewsAnalysisOutput


class LLMErrorCode(StrEnum):
    MISSING_API_KEY = "missing_api_key"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    PROVIDER_ERROR = "provider_error"
    HTTP_ERROR = "http_error"
    MALFORMED_RESPONSE = "malformed_response"
    VALIDATION_ERROR = "validation_error"
    EMPTY_RESPONSE = "empty_response"
    UNSUPPORTED_MODEL = "unsupported_model"
    UNKNOWN = "unknown"


class LLMProviderError(AppError):
    """Raised when LLM provider fails; safe for business logic."""

    def __init__(
        self,
        message: str,
        *,
        error_code: LLMErrorCode = LLMErrorCode.UNKNOWN,
        retryable: bool = False,
        details: dict | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.error_code = error_code
        self.retryable = retryable


class LLMProviderMetadata(BaseModel):
    provider_name: str
    model_name: str


class LLMProvider(ABC):
    """Abstract interface for structured news event analysis."""

    @property
    @abstractmethod
    def metadata(self) -> LLMProviderMetadata:
        """Provider and model identification."""

    @abstractmethod
    async def analyze_news_event(self, request: LLMAnalysisRequest) -> LLMNewsAnalysisOutput:
        """Analyze one news event and return validated structured output."""
