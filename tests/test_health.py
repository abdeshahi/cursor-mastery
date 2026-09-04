"""Tests for health endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.constants import HEALTH_STATUS_DEGRADED, HEALTH_STATUS_HEALTHY


@pytest.mark.asyncio
async def test_health_endpoint_database_healthy(async_client: AsyncClient) -> None:
    with patch(
        "app.api.routes_health.check_database_connection",
        new=AsyncMock(return_value=(True, None)),
    ):
        response = await async_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == HEALTH_STATUS_HEALTHY
    assert payload["paper_mode"] is True
    assert payload["checks"]["database"]["status"] == HEALTH_STATUS_HEALTHY
    assert "app" in payload
    assert "version" in payload


@pytest.mark.asyncio
async def test_health_endpoint_database_unavailable(async_client: AsyncClient) -> None:
    with patch(
        "app.api.routes_health.check_database_connection",
        new=AsyncMock(return_value=(False, "connection refused")),
    ):
        response = await async_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == HEALTH_STATUS_DEGRADED
    assert payload["checks"]["database"]["status"] == "unhealthy"
    assert payload["checks"]["database"]["error"] == "connection refused"
