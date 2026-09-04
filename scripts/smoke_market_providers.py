#!/usr/bin/env python3
"""Optional live provider smoke checks (non-destructive)."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import Settings
from app.providers.market.alphavantage import AlphaVantageProvider
from app.providers.market.fred import FREDProvider
from app.providers.market.nobitex import NobitexProvider
from app.providers.market.tgju import TGJUProvider
from app.providers.market.wallex import WallexProvider


async def check(name: str, coro) -> str:
    try:
        result = await coro
        if result.success and result.quotes:
            return "PASS"
        if result.error:
            lowered = result.error.lower()
            if "not configured" in lowered or "api_key" in lowered:
                return "BLOCKED"
            if any(token in lowered for token in ("resolve", "network", "connect", "timeout", "name or service")):
                return "BLOCKED"
        return "FAIL"
    except Exception as exc:
        err = str(exc).lower()
        if "api_key" in err or "not configured" in err:
            return "BLOCKED"
        if any(token in err for token in ("resolve", "network", "connect", "timeout", "name or service")):
            return "BLOCKED"
        return "FAIL"


async def main() -> int:
    settings = Settings()
    results = {
        "TGJU": await check("TGJU", TGJUProvider().fetch_prices()),
        "NOBITEX": await check("NOBITEX", NobitexProvider().fetch_prices()),
        "WALLEX": await check("WALLEX", WallexProvider().fetch_prices()),
        "FRED": await check("FRED", FREDProvider(api_key=settings.fred_api_key).fetch_prices()),
        "ALPHAVANTAGE": await check(
            "ALPHAVANTAGE",
            AlphaVantageProvider(api_key=settings.alphavantage_api_key).fetch_prices(),
        ),
    }
    for provider, status in results.items():
        print(f"LIVE {provider}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
