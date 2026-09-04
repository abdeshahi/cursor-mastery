"""Resilient async HTTP client for market data providers."""

import asyncio
from collections.abc import Callable
from typing import Any

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

RetryableStatusCodes = {408, 429, 500, 502, 503, 504}


class ResilientHttpClient:
    """httpx wrapper with explicit timeouts, bounded retries, and exponential backoff."""

    def __init__(
        self,
        *,
        connect_timeout: float = 5.0,
        read_timeout: float = 15.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        backoff_max: float = 4.0,
    ) -> None:
        self._timeout = httpx.Timeout(connect=connect_timeout, read=read_timeout, write=read_timeout, pool=connect_timeout)
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._backoff_max = backoff_max

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | list[Any]:
        response = await self.request("GET", url, params=params, headers=headers, client=client)
        payload = response.json()
        if not isinstance(payload, (dict, list)):
            raise ValueError("expected JSON object or array from provider")
        return payload

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> httpx.Response:
        attempt = 0
        last_error: Exception | None = None

        while attempt <= self._max_retries:
            try:
                if client is None:
                    async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as owned:
                        response = await owned.request(method, url, params=params, headers=headers)
                else:
                    response = await client.request(method, url, params=params, headers=headers)

                if response.status_code in RetryableStatusCodes and attempt < self._max_retries:
                    await self._sleep_backoff(attempt)
                    attempt += 1
                    continue

                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                retryable = isinstance(exc, httpx.TimeoutException | httpx.NetworkError) or (
                    isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in RetryableStatusCodes
                )
                if not retryable or attempt >= self._max_retries:
                    raise
                logger.warning(
                    "Retrying provider HTTP request",
                    extra={"url": url, "attempt": attempt + 1, "error": str(exc)},
                )
                await self._sleep_backoff(attempt)
                attempt += 1

        assert last_error is not None
        raise last_error

    async def _sleep_backoff(self, attempt: int) -> None:
        delay = min(self._backoff_base * (2**attempt), self._backoff_max)
        await asyncio.sleep(delay)


def build_http_client(settings_getter: Callable[[], Any] | None = None) -> ResilientHttpClient:
    if settings_getter is None:
        from app.core.config import get_settings

        settings_getter = get_settings
    settings = settings_getter()
    return ResilientHttpClient(
        connect_timeout=settings.provider_connect_timeout,
        read_timeout=settings.provider_read_timeout,
        max_retries=settings.provider_max_retries,
        backoff_base=settings.provider_retry_backoff_base,
        backoff_max=settings.provider_retry_backoff_max,
    )
