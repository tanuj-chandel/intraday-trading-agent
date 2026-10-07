# Phase 8 — Architecture Documentation
## Production-Grade Real-Market-Data Paper Trading & Validation

**Status**: PAPER TRADING ONLY. Zero real-money orders. No broker order placement.

---

## Module Map

```
backend/app/
├── live/
│   ├── tick_validator.py        [Phase 8] Validates every tick before processing
│   ├── data_quality_monitor.py  [Phase 8] Tracks latency, drop rates, reconnects
│   ├── alerter.py               [Phase 8] Internal alerting (16 alert types)
│   ├── trade_journal.py         [Phase 8] Full paper trade lifecycle analytics
│   ├── regime_segmenter.py      [Phase 8] Market regime classification
│   ├── backtest_loader.py       [Phase 8] Loads Phase 6 frozen baseline
│   ├── quality_gate.py          7-state DataProvenanceState gate
│   ├── kill_switch.py           5-level HierarchicalKillSwitch
│   ├── reality_gap.py           RealityGapAnalyzer (5 verdicts, 5 milestones)
│   ├── streamer.py              LiveTickStreamer central coordinator
│   ├── candle_builder.py        1m/5m/15m candle aggregation
│   ├── signal_engine.py         VWAP_EMA_MOMENTUM_V1 (frozen)
│   ├── execution.py             Paper fill simulation with slippage
│   ├── position_manager.py      Position MTM, SL/TP, trailing stops
│   ├── indicators.py            EMA, RSI, MACD, VWAP, ATR, RVOL
│   ├── deduplicator.py          Signal cooldown deduplication
│   ├── audit.py                 LiveAuditLogger (DB + memory ring)
│   ├── recovery.py              Crash recovery service
│   ├── report.py                Phase 7/8 report generator
│   └── qualification.py         Phase 7 qualification engine
├── data/adapters/
│   ├── zerodha_adapter.py       [Phase 8] Real httpx REST calls, UNCONFIGURED/ERROR
│   ├── upstox_adapter.py        [Phase 8] Real httpx REST calls
│   ├── angelone_adapter.py      [Phase 8] Real httpx REST calls
│   └── cache_manager.py         In-memory quote cache (3s TTL)
├── models/
│   └── models.py                [Phase 8+] Phase8TradeJournalRecord, Phase8Alert, Phase8TickStats
└── api/v1/endpoints/
    └── live.py                  [Phase 8] All Phase 7 + 10 new endpoints
```

---

## Data Flow Pipeline

```
Live Market Data (Zerodha / Upstox / Angel One)
         │ REST quote polling
         ▼
Phase8TickValidator
  ├── REJECTED → audit log + data quality counter + alert if rate > 5%
  └── ACCEPTED ↓
Phase8DataQualityMonitor (latency, drop count)
         │
         ▼
DataProvenanceState (7-state):
  UNCONFIGURED → no credentials
  MOCK         → mock provider
  DISCONNECTED → feed down
  STALE        → age > 30s
  INVALID      → zero/negative price
  ERROR        → HTTP failure
  LIVE         → only state that permits signal generation
         │ LIVE only
         ▼
LiveCandleBuilder (1m / 5m / 15m candles, timestamp-aware)
         │ closed candles only (no look-ahead)
         ▼
LiveSignalEngine (VWAP_EMA_MOMENTUM_V1 frozen parameters)
  ─ EMA 9/21, RSI 45–75, MACD hist > 0, RVOL ≥ 1.15, ATR SL 1.5×, TP 3.0×
         │ PENDING signal
         ▼
Human Approval via /api/live/signal/{id}/approve
         │
         ▼
RiskManager.validate_trade() (9 independent checks)
  ─ Max daily loss, max open positions, min R:R, cutoff time, consecutive losses
         │ PASSED
         ▼
LivePaperExecutionEngine
  ─ Simulated fill with bid/ask spread slippage
  ─ Indian statutory charges: Brokerage + STT + Exchange + SEBI + GST + Stamp
         │
         ▼
LivePositionManager
  ─ Real-time MTM mark-to-market on every tick
  ─ MFE / MAE tracking (Phase 8)
  ─ Dynamic trailing stop
  ─ SL/TP auto-exit
  ─ 15:15 IST mandatory square-off
         │ Position closed
         ▼
Phase8TradeJournal (DB + in-memory analytics)
         │
         ▼
RealityGapAnalyzer (5-tier milestones: 30/100/300/500 trades)
         │
         ▼
Phase8ReportGenerator → reports/phase8_paper_trading_validation.{md,json}
```

---

## API Surface (Phase 8 Complete)

### Phase 7 Endpoints (all preserved)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/live/status` | Full system status |
| GET | `/api/live/data-health` | Data quality gate status |
| GET | `/api/live/signals` | Pending signals |
| GET | `/api/live/positions` | Open/closed positions |
| GET | `/api/live/performance` | Session performance |
| POST | `/api/live/signal/{id}/approve` | Human-approve signal |
| POST | `/api/live/signal/{id}/reject` | Reject signal |
| POST | `/api/live/emergency-stop` | L3 kill switch |
| POST | `/api/live/kill-switch/{1-5}` | Level-specific kill switch |
| POST | `/api/live/kill-switch/reset` | Reset kill switch |
| GET | `/api/live/kill-switch/status` | Kill switch state |
| GET | `/api/live/audit` | Audit log |
| GET | `/api/live/session` | Session summary |
| GET | `/api/live/reality-gap` | Reality-gap analysis |
| POST | `/api/live/tick` | Ingest tick (test/simulation) |
| POST | `/api/live/square-off` | 15:15 mandatory square-off |
| GET | `/api/live/report` | Generate Phase 7 report |

### Phase 8 New Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/live/trade-journal` | Full paper trade analytics |
| GET | `/api/live/execution-quality` | Slippage, fill, latency quality |
| GET | `/api/live/validation-progress` | 30/100/300/500 milestones |
| GET | `/api/live/backtest-vs-paper` | Phase 6 vs paper comparison |
| GET | `/api/live/regime-performance` | Performance by market regime |
| GET | `/api/live/alerts` | System alerts |
| GET | `/api/live/data-quality` | Tick validator & monitor stats |
| GET | `/api/live/concentration` | Symbol concentration analysis |
| POST | `/api/live/connect` | Connect data provider |
| POST | `/api/live/disconnect` | Disconnect cleanly |

---

## Database Tables (all phases)

| Table | Purpose | Phase |
|-------|---------|-------|
| `live_sessions` | Per-day session metadata | P7 |
| `live_signals` | Signal persistence for recovery | P7 |
| `live_positions` | Position persistence for recovery | P7 |
| `system_logs` | General audit log | P1+ |
| `phase8_trade_journal` | Full paper trade records with MFE/MAE | P8 |
| `phase8_alerts` | Internal alert records | P8 |
| `phase8_tick_stats` | Per-symbol tick quality statistics | P8 |

---

## Validation Milestone System

| Trades | Stage | Interpretation |
|--------|-------|----------------|
| 0–29 | INSUFFICIENT_LIVE_DATA | Cannot draw any conclusions |
| 30–99 | EARLY_PAPER_ASSESSMENT | Very preliminary only |
| 100–299 | PRELIMINARY_PAPER_ASSESSMENT | Initial pattern forming |
| 300–499 | EMPIRICAL_PAPER_ASSESSMENT | Meaningful but not final |
| 500+ | HIGH_CONFIDENCE_CANDIDATE | Sufficient for evaluation |

**Scientific Rule**: Even at 500+ trades, strategy is only a "candidate" for further evaluation.
Do NOT call the strategy "profitable" or "validated" based on paper trading results alone.

---

## Safety Boundaries

1. `IS_PAPER_TRADING = True` enforced in config (cannot be changed at runtime)
2. `TRADING_MODE = "PAPER"` enforced in config
3. Zero `place_order` / `create_order` / `submit_order` / `execute_order` calls anywhere
4. Kill Switch L5 requires `CONFIRM_MANUAL_RESET` code for reset
5. Kill Switch is escalation-only (cannot reduce level via `activate()`)
6. All 7 DataProvenanceState values except LIVE block signal generation
7. RiskManager has 9 independent checks — no bypass path
8. 15:15 IST mandatory square-off enforced in `LivePositionManager`
9. Tick validator rejects corrupted/invalid ticks before they enter the pipeline
10. DB failures in alerter/audit are best-effort (never block trading)
