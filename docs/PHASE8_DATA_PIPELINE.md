# Phase 8 — Data Pipeline Documentation
## Tick-to-Signal Data Flow

**Paper Trading Only. No real-money execution.**

---

## 1. Data Provider Selection

### Priority Order
When multiple broker credentials are available, the system uses the configured `MARKET_DATA_PROVIDER`:

```
ZERODHA_KITE    → Zerodha Kite Connect v3 REST API
UPSTOX          → Upstox API v2 REST 
ANGEL_ONE       → Angel One SmartAPI REST
mock            → Internal mock (blocks all signals)
```

### State Transitions
```
No credentials in .env → UNCONFIGURED → No signals
Credentials set + HTTP success → LIVE → Signals permitted
Credentials set + HTTP failure → ERROR → No signals
Mock provider → MOCK → No signals
```

### Connection Testing
```
GET  /api/live/status          → Full system status
GET  /api/live/data-health     → Provenance gate status
GET  /api/live/data-quality    → Per-symbol tick stats
POST /api/live/connect         → Connect/reconnect provider
POST /api/live/disconnect      → Clean disconnect
```

---

## 2. Tick Validation Pipeline

Every incoming tick passes through `Phase8TickValidator`:

```
Incoming Tick
    ↓
[1] Price Checks
    ├── LTP > 0, Open > 0, High > 0, Low > 0, Close > 0
    └── FAIL → reject, log TICK_REJECTED, increment invalid counter
    ↓
[2] OHLC Sanity
    ├── High ≥ Low
    ├── High ≥ Open and High ≥ Close
    └── Low ≤ Open and Low ≤ Close
    ↓
[3] Timestamp Checks
    ├── tick_time ≤ server_time + 5s (clock skew tolerance)
    └── tick_time ≠ last_seen_time[symbol] (duplicate detection)
    ↓
[4] Volume
    └── volume ≥ 0
    ↓
[5] Spike Detection (warnings, not rejection)
    ├── Price move > 20% from previous → WARNING
    └── Volume > 100× previous → WARNING
    ↓
ACCEPTED → DataQualityMonitor.record_tick(is_valid=True)
```

---

## 3. Quality Monitoring

`Phase8DataQualityMonitor` tracks per-symbol and global metrics:

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Avg latency | > 200ms | WARNING |
| Avg latency | > 1000ms | CRITICAL |
| Invalid tick rate | > 5% | WARNING |

Access via: `GET /api/live/data-quality`

---

## 4. Candle Building

`LiveCandleBuilder` aggregates validated ticks into OHLCV candles:

- Timeframes: **1m, 5m, 15m** 
- A new candle opens at the correct IST minute boundary
- Candle data is only used when **closed** (no look-ahead)
- `LiveCandleBuilder.ingest_tick()` returns only completed candles

---

## 5. Quality Gate Decision

`LiveDataQualityGate.evaluate_live_feed()` runs on every accepted tick:

```
Decision order:
1. has_credentials?   → False → UNCONFIGURED
2. provider_error?    → set   → ERROR
3. is_mock_provider?  → True  → MOCK
4. is_connected?      → False → DISCONNECTED
5. last_tick_price?   → ≤ 0  → INVALID
6. tick age > 30s?    → True  → STALE
7. All checks pass    →        LIVE ✓
```

Only LIVE returns `can_generate_signals = True`.

---

## 6. Signal Evaluation

`LiveSignalEngine.evaluate_symbol()` uses **frozen VWAP_EMA_MOMENTUM_V1** parameters:

| Parameter | Value | Frozen |
|-----------|-------|--------|
| EMA Fast | 9 | ✓ |
| EMA Slow | 21 | ✓ |
| RVOL threshold | ≥ 1.15 | ✓ |
| ATR Stop Loss | 1.5× | ✓ |
| ATR Take Profit | 3.0× | ✓ |
| Min candles required | 5 (5m TF) | ✓ |
| Min R:R ratio | 2.0 | ✓ |

**Strategy parameters cannot be changed at runtime.**

---

## 7. Paper Execution

`LivePaperExecutionEngine.execute()` simulates realistic fill:

### Slippage Model
```
IMMEDIATE_FILL: fill_price = ask (buys) or bid (sells)
TWAP_APPROX:   fill_price = (bid + ask) / 2
VWAP_APPROX:   fill_price ≈ VWAP from recent candle
```

### Indian Statutory Charges (all simulated accurately)
| Charge | Rate |
|--------|------|
| Brokerage | ₹20 flat per trade (Zerodha/Upstox model) |
| STT | 0.025% of trade value (intraday) |
| Exchange Transaction | 0.00345% (NSE) |
| SEBI | ₹10 per crore |
| GST | 18% on brokerage + exchange |
| Stamp Duty | 0.003% |

---

## 8. Position Lifecycle

```
Signal APPROVED → Entry at simulated fill price
    ↓
MTM update on every tick
    ├── Track MFE (Maximum Favorable Excursion)
    └── Track MAE (Maximum Adverse Excursion)
    ↓
Exit triggers:
    ├── SL hit (price ≤ stop_loss for BUY)
    ├── TP hit (price ≥ target for BUY)
    ├── Trailing stop hit
    ├── Manual square-off
    └── 15:15 IST mandatory square-off
    ↓
Trade Journal entry created → Phase8TradeJournal.record_trade()
    ↓
Reality-Gap Analyzer updated
```

---

## 9. Caching

All broker REST responses are cached for `CACHE_TTL_SECONDS` (default 3s):

```python
DataCacheManager.get(key)       # Memory cache lookup
DataCacheManager.set(key, val)  # Store with TTL
```

This prevents hammering broker APIs on every tick while keeping data reasonably fresh.

---

## 10. Data Quality Reporting

Full quality report available via: `GET /api/live/data-quality`

```json
{
  "provider_health": {
    "total_ticks": 12500,
    "total_invalid": 3,
    "invalid_rate_pct": 0.02,
    "avg_latency_ms": 45.2,
    "quality_status": "HEALTHY"
  },
  "per_symbol_stats": [...],
  "tick_validator_stats": {...},
  "data_provenance": "LIVE"
}
```
