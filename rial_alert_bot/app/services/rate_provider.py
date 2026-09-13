from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RateSnapshot:
    value: float | None
    source: str
    label: str


def _parse_number(raw: str) -> float | None:
    cleaned = raw.replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


async def _fetch_tgju() -> RateSnapshot:
    url = 'https://api.tgju.org/v1/market/indicator/summary-table-data/price_dollar_rl'
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    current = payload.get('current', {})
    price = current.get('price') or current.get('p')
    if isinstance(price, (int, float)):
        return RateSnapshot(value=float(price), source='tgju', label='بازار آزاد (TGJU)')
    if isinstance(price, str):
        parsed = _parse_number(price)
        if parsed is not None:
            return RateSnapshot(value=parsed, source='tgju', label='بازار آزاد (TGJU)')
    raise ValueError('tgju payload missing price')


async def _fetch_bonbast_html() -> RateSnapshot:
    url = 'https://bonbast.com/'
    headers = {'User-Agent': 'RialAlertBot/1.0'}
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), headers=headers, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        text = response.text
    match = re.search(r'id=["\']usd1["\'][^>]*>([\d,]+)<', text)
    if match is None:
        raise ValueError('bonbast usd not found')
    value = _parse_number(match.group(1))
    if value is None:
        raise ValueError('bonbast parse failed')
    return RateSnapshot(value=value, source='bonbast', label='بازار آزاد (Bonbast)')


async def get_free_market_usd_rate() -> RateSnapshot:
    providers = (_fetch_tgju, _fetch_bonbast_html)
    for provider in providers:
        try:
            snapshot = await provider()
            logger.info('USD rate from %s: %s', snapshot.source, snapshot.value)
            return snapshot
        except Exception as error:  # noqa: BLE001
            logger.warning('Rate provider failed (%s): %s', provider.__name__, error)
    return RateSnapshot(value=None, source='unknown', label='نامشخص')
