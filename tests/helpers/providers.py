"""Shared helpers for provider tests."""

import json
from pathlib import Path

import httpx


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "market"


def load_fixture(name: str) -> dict | list:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def mock_transport(routes: dict[str, dict | list]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        for key, payload in routes.items():
            if key in str(request.url):
                return httpx.Response(200, json=payload)
        return httpx.Response(404, json={"error": "not found in mock transport"})

    return httpx.MockTransport(handler)
