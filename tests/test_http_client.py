"""Tests for resilient HTTP client."""

import httpx
import pytest

from app.providers.market.http_client import ResilientHttpClient


@pytest.mark.asyncio
async def test_http_client_retries_transient_503() -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json={"ok": True})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    http = ResilientHttpClient(max_retries=3, backoff_base=0.01, backoff_max=0.05)
    payload = await http.get_json("https://example.test/retry", client=client)
    assert payload == {"ok": True}
    assert attempts["count"] == 3


@pytest.mark.asyncio
async def test_http_client_timeout_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    http = ResilientHttpClient(max_retries=1, backoff_base=0.01, backoff_max=0.02)
    with pytest.raises(httpx.ReadTimeout):
        await http.get_json("https://example.test/timeout", client=client)
