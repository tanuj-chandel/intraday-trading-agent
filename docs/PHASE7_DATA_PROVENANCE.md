# Phase 7 Data Provenance Guide

## Overview

Every live data point must carry a provenance state. Signal generation is only permitted
when provenance is `LIVE`. All other states block signal generation and display a clear
`TRADING DISABLED` reason — **no silent fallback to mock data is ever permitted**.

---

## The 7 Provenance States

| State | Meaning | Can Generate Signals | Action |
|-------|---------|---------------------|--------|
| `LIVE` | Connected, fresh, real broker data | ✅ YES | Normal operation |
| `STALE` | Data is > 30 seconds old | ❌ NO | Wait for fresh tick or reconnect |
| `DISCONNECTED` | Feed connection dropped | ❌ NO | Reconnect broker feed |
| `UNCONFIGURED` | No broker API credentials set | ❌ NO | Set env vars, restart backend |
| `MOCK` | Simulated data provider active | ❌ NO | Only for development/testing |
| `INVALID` | Price data fails sanity check (≤0) | ❌ NO | Investigate broker feed quality |
| `ERROR` | Provider returned error response | ❌ NO | Check broker API status |

---

## Decision Logic

```
evaluate_live_feed() checks in order:
  1. has_credentials? → NO  → UNCONFIGURED
  2. provider_error?  → YES → ERROR
  3. is_mock?         → YES → MOCK
  4. is_connected?    → NO  → DISCONNECTED
  5. last_tick_time?  → None → DISCONNECTED
  6. ltp <= 0?        → YES → INVALID
  7. age > 30s?       → YES → STALE
  8. All checks pass  → LIVE ✅
```

---

## API Response

Every call to `GET /api/live/status` returns a `data_quality_gate` object:
```json
{
  "data_quality_gate": {
    "status": "LIVE",
    "can_generate_signals": true,
    "trading_enabled": true,
    "data_age_seconds": 1.2,
    "is_trading_hours": true,
    "reason": "Real market feed is live, continuous, and verified fresh.",
    "provenance": "LIVE — real broker feed, credentials verified, freshness confirmed"
  }
}
```

For blocked states:
```json
{
  "data_quality_gate": {
    "status": "STALE",
    "can_generate_signals": false,
    "trading_enabled": false,
    "data_age_seconds": 45.3,
    "reason": "TRADING DISABLED — Market data stale (45.3s > 30.0s threshold)"
  }
}
```

---

## Provenance Labelling in Reports

All Phase 7 reports include a `data_provenance` field:
- `LIVE` → data was confirmed from real broker
- `MOCK` → data was simulated (report verdict will reflect this)
- Any other state → report notes it as a session quality issue

---

## Freshness Threshold

Default: **30 seconds**. Configurable via `LiveDataQualityGate.MAX_FRESHNESS_SECONDS`.

During market hours (09:15–15:30 IST), normal NSE tick frequency is < 1 second for liquid stocks.
A 30-second gap indicates connectivity issues.

---

## What "No Silent Fallback" Means

In Phases 1–4, the `BrokerMarketDataProvider` silently called `MockMarketDataProvider` when credentials were present but the real API was unavailable. This is **prohibited in Phase 7**.

In Phase 7:
- If real data is unavailable → state is `DISCONNECTED` or `ERROR`
- Signal generation is blocked
- The dashboard shows `MARKET DATA STATUS: UNAVAILABLE`
- No mock data is generated or used in its place
- The report clearly records the provenance state at the time of each session
