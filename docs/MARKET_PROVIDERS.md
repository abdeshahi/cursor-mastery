# Market Data Providers (Phase 3)

This document describes external market data providers, authentication requirements, units, and known fragility.

## Architecture

```
Provider -> Collector -> MarketRepository -> PostgreSQL
```

Providers return normalized internal schemas (`NormalizedQuote`). Provider-specific parsing stays inside each adapter.

## Authentication

| Provider | Auth Required | Env Variable |
|----------|---------------|--------------|
| TGJU | No | `TGJU_BASE_URL` (optional) |
| Nobitex | No | — |
| Wallex | No | — |
| FRED | Yes | `FRED_API_KEY` |
| Alpha Vantage | Yes | `ALPHAVANTAGE_API_KEY` |

Never commit API keys. Configure via environment variables only.

## Symbol / Unit Mapping

| Internal Symbol | Provider(s) | Stored Unit | Notes |
|-----------------|-------------|-------------|-------|
| `USD_IRR` | TGJU | IRR per USD | TGJU `price_dollar_rl` |
| `AED_IRR` | TGJU | IRR per AED | TGJU `price_aed` |
| `GOLD_18K_IRR` | TGJU | IRR per gram | TGJU `geram18` (18k gold gram) |
| `USDT_IRR` | Nobitex, Wallex | IRR per USDT | Source quotes in **TOMAN**, converted via `1 TOMAN = 10 IRR` |
| `BRENT_USD` | FRED | USD per barrel | FRED series `DCOILBRENTEU` |
| `USD_BROAD_INDEX` | FRED | index | FRED `DTWEXBGS` — **not DXY** |
| `GOLD_OUNCE_USD` | Alpha Vantage | USD per troy oz | XAU/USD exchange rate |

## TOMAN vs IRR (Critical)

Iranian exchanges Nobitex and Wallex expose USDT prices in **Toman** (`IRT` / `TMN`).

Conversion rule (explicit and tested):

```
IRR = TOMAN × 10
```

The system never assumes quote units silently.

## TGJU Fragility

TGJU integration uses public JSON summary-table endpoints:

```
https://api.tgju.org/v1/market/indicator/summary-table-data/{indicator_key}
```

TGJU may change response structure without notice. All TGJU parsing is isolated in `TGJUProvider`.

## Health Statuses

Collector updates `market_source_health` with:

- `healthy` — fetch, parse, and validation succeeded
- `degraded` — saved but stale timestamp detected
- `failed` — fetch/parse/validation failed

HTTP 200 alone does not mark a source healthy.

## Timeouts and Retries

Configured via:

- `PROVIDER_CONNECT_TIMEOUT`
- `PROVIDER_READ_TIMEOUT`
- `PROVIDER_MAX_RETRIES`

Uses bounded exponential backoff for transient network failures.

## Phase 3 Boundaries

Not implemented in Phase 3:

- Median/consensus price aggregation
- Cross-market confirmation
- Scheduler automation
- Signal generation

Each provider observation is stored independently.
