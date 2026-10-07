# Phase 7 Architecture

## Overview

Phase 7 implements real-time live paper trading validation against genuine Indian NSE market data. All positions are executed only in the paper trading engine — no real-money orders are placed at any time.

## Module Graph

```
Live Market Feed (Broker API or Manual Tick Injection)
         │
         ▼
  LiveDataQualityGate ──── Rejects MOCK, STALE, DISCONNECTED, UNCONFIGURED, INVALID, ERROR
         │ (LIVE only)
         ▼
  LiveCandleBuilder ──────── 1m / 5m / 15m OHLCV candles (no look-ahead)
         │
         ▼
  LiveIndicatorCalculator ── EMA9/21, RSI, MACD, VWAP, ATR, RVOL
         │
         ▼
  LiveSignalEngine ──────────── Frozen VWAP_EMA_MOMENTUM_V1 strategy
  (DuplicateSignalDeduplicator — 15-min cooldown)
         │
         ▼ (PENDING signal)
  ┌─────────────────────────────────────────────┐
  │   HUMAN APPROVAL REQUIRED                  │
  │   POST /api/live/signal/{id}/approve        │
  └─────────────────────────────────────────────┘
         │ (Approved)
         ▼
  RiskManager.validate_trade() ─── 9 mandatory checks
         │ (Passed)
         ▼
  LivePaperExecutionEngine ──── Fill with bid/ask spread slippage
         │
         ▼
  LivePositionManager ──────── MTM updates, trailing stop, SL/TP, 15:15 square-off
         │
         ▼
  LiveAuditLogger ──────────── In-memory + system_logs DB table
         │
         ▼
  RealityGapAnalyzer ───────── Verdict vs Phase 6 backtest metrics
         │
         ▼
  Phase7ReportGenerator ────── reports/phase7_paper_trading_validation.md/.json
```

## Kill Switch Architecture

```
HierarchicalKillSwitch
├── Level 1: PAUSE_SIGNALS     → Blocks LiveSignalEngine.evaluate_symbol()
├── Level 2: NO_NEW_ENTRIES    → Blocks approve_signal() path
├── Level 3: CLOSE_ALL         → Calls position_manager.square_off_all_positions()
│                                + RiskManager.trigger_emergency_stop()
├── Level 4: FREEZE_ALL        → Blocks all live activity + fires alert
└── Level 5: FULL_HALT         → System halt; requires CONFIRM_MANUAL_RESET code
```

## Data Flow for Each Tick

1. **Tick arrives** → `LiveTickStreamer.ingest_tick(tick: LiveTick)`
2. **Quality gate** → `LiveDataQualityGate.evaluate_live_feed()` — blocks if not LIVE
3. **Position MTM** → `LivePositionManager.update_market_price()` — checks SL/TP
4. **Candle build** → `LiveCandleBuilder.ingest_tick()` — builds 1m/5m/15m candles
5. **Signal eval** → `LiveSignalEngine.evaluate_symbol()` if gate passes & ≥5 candles
6. **Signal pending** → Stored in-memory, also persisted to `live_signals` table
7. **Human approves** → `approve_signal()` → `RiskManager.validate_trade()` → execution
8. **Position opened** → Stored in `live_positions` table
9. **Audit logged** → `LiveAuditLogger.log()` → in-memory + `system_logs` table

## DB Tables (Phase 7)

| Table | Purpose |
|-------|---------|
| `live_sessions` | One row per trading day — session metadata and verdict |
| `live_signals` | All generated signals — persistent across restarts |
| `live_positions` | All paper positions (open and closed) — persistent across restarts |
| `system_logs` | All audit events (shared with Phases 1–6) |

## Singleton

`live_streamer = LiveTickStreamer()` in `live/streamer.py` is the global singleton.
It owns: `candle_builder`, `signal_engine`, `position_manager`, `kill_switch`, `reality_gap`, `risk_manager`.

## API Endpoints (Phase 7)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/live/status` | Full system status including gate, kill switch, reality gap |
| GET | `/api/live/signals` | Pending signals awaiting approval |
| GET | `/api/live/positions` | Open and closed positions |
| POST | `/api/live/signal/{id}/approve` | Human approval → paper execution |
| POST | `/api/live/signal/{id}/reject` | Reject signal |
| POST | `/api/live/tick` | Ingest live tick (manual or webhook) |
| POST | `/api/live/emergency-stop` | Level 3 kill switch (backward compatible) |
| POST | `/api/live/kill-switch/{1-5}` | Hierarchical kill switch activation |
| POST | `/api/live/kill-switch/reset` | Reset kill switch |
| GET | `/api/live/kill-switch/status` | Kill switch state |
| GET | `/api/live/reality-gap` | Full reality-gap analysis |
| GET | `/api/live/report` | Generate Phase 7 validation report |
| GET | `/api/live/audit` | Audit log stream |
| GET | `/api/live/session` | Current session summary |
| POST | `/api/live/square-off` | 15:15 mandatory square-off |
