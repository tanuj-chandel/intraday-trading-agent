# Phase 8 — Operations Guide
## Production-Grade Real-Market-Data Paper Trading

> ⚠️ **PAPER TRADING ONLY** — This guide is for simulation validation. Zero real-money orders.

---

## Daily Operating Checklist

### Pre-Market (Before 9:00 IST)
- [ ] Verify `.env` credentials are set if using a real broker feed
- [ ] Start backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [ ] Start frontend: `npm run dev` in `/frontend`
- [ ] Check dashboard at `http://localhost:3000/live`
- [ ] Confirm Data Provenance Banner shows correct state (UNCONFIGURED/MOCK/LIVE)
- [ ] If UNCONFIGURED: System will not generate signals (expected, safe)

### Market Hours (9:15–15:30 IST)
- [ ] Monitor `/live` dashboard — signals require human approval
- [ ] Review each signal before clicking APPROVE
- [ ] Alert banners fire automatically for: disconnect, stale data, high latency
- [ ] Kill Switch Level 1 (Pause Signals) if seeing too many bad signals
- [ ] Kill Switch Level 3 (Close All) only if strategy misbehaves

### Post-Market (After 15:30 IST)
- [ ] Verify 15:15 mandatory square-off fired (check `/api/live/positions?status=CLOSED`)
- [ ] Download Phase 8 report: `GET /api/live/report`
- [ ] Review validation progress: `GET /api/live/validation-progress`

---

## Connect to Real Data Feed

```bash
# Option 1: Zerodha Kite Connect
POST /api/live/connect?provider=ZERODHA_KITE&is_mock=false

# Option 2: Upstox v2
POST /api/live/connect?provider=UPSTOX&is_mock=false

# Option 3: Angel One SmartAPI
POST /api/live/connect?provider=ANGEL_ONE&is_mock=false

# Option 4: Explicit mock mode (for testing without credentials)
POST /api/live/connect?provider=ZERODHA_KITE&is_mock=true
```

**Without credentials**: The system shows `UNCONFIGURED` state and blocks all signal generation. This is safe and expected behaviour.

---

## Environment Variables (`.env`)

```env
# Zerodha Kite Connect v3 (read-only market data)
ZERODHA_API_KEY=your_api_key_here
ZERODHA_ACCESS_TOKEN=your_access_token_here

# Upstox v2 (read-only market data)  
UPSTOX_API_KEY=your_api_key
UPSTOX_ACCESS_TOKEN=your_access_token

# Angel One SmartAPI (read-only market data)
ANGELONE_API_KEY=your_api_key
ANGELONE_CLIENT_CODE=your_client_code
ANGELONE_JWT_TOKEN=your_jwt_token

# Safety controls (do NOT change)
IS_PAPER_TRADING=True
TRADING_MODE=PAPER
AUTO_PAPER_EXECUTION=False
```

---

## Kill Switch Usage

| Level | Command | Effect |
|-------|---------|--------|
| L1 | `POST /api/live/kill-switch/1` | Pause new signal generation |
| L2 | `POST /api/live/kill-switch/2` | No new position entries |
| L3 | `POST /api/live/kill-switch/3` | Close all open positions immediately |
| L4 | `POST /api/live/kill-switch/4` | Freeze all operations |
| L5 | `POST /api/live/kill-switch/5` | Full halt, requires manual reset code |
| Reset | `POST /api/live/kill-switch/reset?manual_operator_code=CONFIRM_MANUAL_RESET` | Reset (L5 requires code) |

---

## Alert Types Reference

| Alert | Severity | Auto-fired when |
|-------|---------|----------------|
| DATA_DISCONNECT | CRITICAL | Feed drops |
| STALE_DATA | WARNING | Tick age > 30s |
| HIGH_LATENCY | WARNING/CRITICAL | Latency > 200ms / > 1000ms |
| REPEATED_API_ERROR | WARNING | Consecutive HTTP errors |
| CONSECUTIVE_LOSSES | WARNING/CRITICAL | 3+ / 5+ consecutive losses |
| DAILY_LOSS_THRESHOLD | CRITICAL | Daily loss approaching limit |
| STRATEGY_DEGRADATION | CRITICAL | Reality-gap breach detected |
| KILL_SWITCH_ACTIVATED | CRITICAL | Any KS level activated |
| INVALID_TICK_RATE | WARNING | > 5% ticks invalid |

---

## Validation Milestones

Progress tracked at: `GET /api/live/validation-progress`

| Trades | Stage | Permitted Claim |
|--------|-------|-----------------|
| < 30 | INSUFFICIENT | No claims permitted |
| 30–99 | EARLY | "Early preliminary indication only" |
| 100–299 | PRELIMINARY | "Preliminary assessment" |
| 300–499 | EMPIRICAL | "Empirical assessment, not conclusive" |
| 500+ | HIGH_CONFIDENCE | "High-confidence candidate for review" |

**Never claim strategy is profitable or validated based on paper trading alone.**

---

## Mandatory Square-Off

The position manager auto-triggers at **15:15 IST** for all open positions.

To manually trigger early: `POST /api/live/square-off`

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Status shows UNCONFIGURED | No credentials in `.env` | Add broker credentials |
| Status shows STALE | Feed not receiving ticks | Check broker WebSocket / REST polling |
| Signals not generating | Quality gate blocking (not LIVE) | Check /api/live/data-health |
| Kill switch won't reset | Level 5 needs code | Use `CONFIRM_MANUAL_RESET` |
| MOCK data showing in prod | `is_mock=true` in connect call | Use `is_mock=false` with real creds |
