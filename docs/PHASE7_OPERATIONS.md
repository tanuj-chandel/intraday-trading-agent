# Phase 7 Operations Guide

## Starting the System

### Backend
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm run dev
```

Live Paper Dashboard: http://localhost:3000/live

---

## Pre-Session Checklist

Before each live paper trading session:

1. **Verify trading mode**: `GET /api/live/status` → confirm `trading_mode: PAPER_TRADING_ONLY`
2. **Check data provenance**: `data_quality_gate.status` must be `LIVE` (not MOCK, STALE, UNCONFIGURED)
3. **Confirm kill switch off**: `kill_switch.current_level` must be 0
4. **Confirm emergency stop not triggered**: `RiskManager.emergency_stop_triggered` must be False
5. **Verify strategy frozen**: Strategy version shown as `VWAP_EMA_MOMENTUM_V1`

---

## Connecting a Live Data Feed

### Zerodha Kite Connect (when credentials available)

Set in `.env`:
```
MARKET_DATA_PROVIDER=zerodha
ZERODHA_API_KEY=your_api_key
ZERODHA_ACCESS_TOKEN=your_access_token_after_daily_login
```

Then call:
```bash
curl -X POST "http://localhost:8000/api/live/tick" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"RELIANCE","ltp":2950.0,"open":2940.0,"high":2960.0,"low":2935.0,"close":2950.0,"volume":50000,"bid":2949.5,"ask":2950.5,"spread":1.0}'
```

### Manual Tick Injection (for testing)

POST ticks to `/api/live/tick` — the quality gate will show `LIVE` if `is_mock=False` and credentials are set.

---

## Signal Approval Workflow

1. Signal appears at `GET /api/live/signals`
2. Analyst reviews: direction, entry, SL, TP, risk-reward, market regime
3. Approve: `POST /api/live/signal/{id}/approve`
4. Or reject: `POST /api/live/signal/{id}/reject?reason=...`
5. Approved signal goes through RiskManager → execution → position opened

---

## Kill Switch Usage

| Situation | Command | Level |
|-----------|---------|-------|
| Pause new signals temporarily | `POST /api/live/kill-switch/1` | L1 |
| Stop new entries, manage exits | `POST /api/live/kill-switch/2` | L2 |
| Emergency — close all now | `POST /api/live/emergency-stop` | L3 |
| Freeze everything, investigate | `POST /api/live/kill-switch/4` | L4 |
| Full system halt | `POST /api/live/kill-switch/5` | L5 |
| Resume after L1–L4 | `POST /api/live/kill-switch/reset` | — |
| Resume after L5 | `POST /api/live/kill-switch/reset?manual_operator_code=CONFIRM_MANUAL_RESET` | — |

---

## 15:15 IST Mandatory Square-Off

At 15:15 IST, manually trigger:
```bash
curl -X POST "http://localhost:8000/api/live/square-off"
```

Or the position manager's trailing stop and SL/TP checks will continue until you call this.

---

## Generating the Phase 7 Report

```bash
curl "http://localhost:8000/api/live/report"
```

Output files:
- `backend/reports/phase7_paper_trading_validation.md`
- `backend/reports/phase7_paper_trading_validation.json`

---

## Reality-Gap Monitoring

Check verdict at any time:
```bash
curl "http://localhost:8000/api/live/reality-gap"
```

Verdicts:
- `INSUFFICIENT_LIVE_DATA` → < 30 trades — keep running
- `CONTINUE_PAPER_TRADING` → 30–99 trades, consistent — keep running
- `REALITY_GAP_DETECTED` → one threshold breach — investigate
- `STRATEGY_DEGRADATION_DETECTED` → multiple breaches — review strategy
- `PAPER_VALIDATION_PASSED` → ≥ 100 trades, no gap — ready for review

---

## Audit Log

```bash
curl "http://localhost:8000/api/live/audit?limit=100"
```

All events are also written to `system_logs` table in `trading_agent.db`.
