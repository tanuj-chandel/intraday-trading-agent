# PHASE 7 REPOSITORY AUDIT

**Audit Date**: 2026-08-28
**Auditor**: Antigravity AI (automated code inspection — every file read)
**Baseline Tests**: 85 passed / 0 failed (confirmed immediately before audit)

---

## 1. DIRECTORY TREE SUMMARY

\\\
backend/app/
├── core/          config.py (101 lines), database.py, logging.py
├── models/        models.py (240 lines — 13 SQLAlchemy tables, NO live_* tables)
├── schemas/       schemas.py (399 lines — Pydantic DTOs)
├── api/v1/        api.py (23 lines — 14 routers), endpoints/ (14 endpoint files)
├── data/          18 modules — mock provider, broker adapters (ALL STUBS), health checker
│   └── adapters/  zerodha_adapter.py, upstox_adapter.py, angelone_adapter.py — all STUBS
├── risk/          manager.py (196 lines — 9 checks — FULLY FUNCTIONAL)
├── paper_trading/ engine.py (342 lines — SQLAlchemy-backed — FULLY FUNCTIONAL)
├── strategies/    vwap_ema_momentum.py (frozen VWAP_EMA_MOMENTUM_V1)
├── technical/     indicators.py (TechnicalAnalysis)
├── backtest/      17 modules — engine, walk-forward, Monte Carlo, cost engine, Phase6
├── live/          14 modules — Phase 7 code (PARTIAL — see Section 4)
└── main.py        FastAPI entrypoint + lifespan seeding

frontend/src/app/
├── page.tsx          Main trading terminal dashboard
├── backtesting/      Phase 3-6 backtest dashboard
├── data-health/      Phase 4 provider health dashboard
└── (NO /live route)  ← MISSING

docs/
├── ARCHITECTURE.md, API.md, RISK_MANAGEMENT.md, BACKTESTING.md
├── SECURITY.md, SETUP.md, TRADING_ENGINE.md
└── (NO PHASE7_* docs) ← ALL MISSING

reports/
├── phase6_strategy_validation.json/.md
└── phase7_live_paper_validation.json/.md  ← WRONG filename (required: phase7_paper_trading_validation.*)
\\\

---

## 2. BROKER ADAPTER ASSESSMENT

### ALL THREE BROKER ADAPTERS ARE STUBS — NO REAL API CALLS

| Adapter | Real HTTP Call | SDK Imported | SDK in requirements.txt | Status |
|---------|--------------|-------------|------------------------|--------|
| ZerodhaKiteAdapter | NO | NO | NO | STUB |
| UpstoxAdapter | NO | NO | NO | STUB |
| AngelOneSmartApiAdapter | NO | NO | NO | STUB |

When credentials ARE present, get_quote() returns hardcoded values (e.g., current_price: 2980.0).
BrokerMarketDataProvider.get_candles() calls mock_fallback.get_candles() in ALL code paths.

**Current market data source: 100% MOCK regardless of credential configuration.**

---

## 3. IDENTIFIED BUGS

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| B1 | CRITICAL | live/streamer.py:89 | risk_manager.check_signal() does not exist. RiskManager only has validate_trade(). This will raise AttributeError when approve_signal() is called at runtime. Test does not catch this because it tests LiveSignalEngine directly. |
| B2 | HIGH | data/broker_provider.py:76,89,101 | Even with valid credentials, candles/quotes return mock data. May show status=LIVE while returning MOCK data. |
| B3 | MEDIUM | live/report.py:102-103 | Output file paths: phase7_live_paper_validation.* but spec requires phase7_paper_trading_validation.* |
| B4 | MEDIUM | live/streamer.py + audit.py | All live session state is in-memory. Backend restart loses all signals, positions, audit log. |
| B5 | LOW | data/adapters/zerodha_adapter.py:31-37 | test_connection() returns status: LIVE without making any real network call. |

---

## 4. PHASE 7 MODULE STATUS

| Module | File | Complete? | Gap |
|--------|------|-----------|-----|
| Data types | data_types.py | YES | — |
| Candle builder | candle_builder.py | YES | — |
| Live indicators | indicators.py | YES | EMA9/21, RSI, MACD, VWAP, ATR, RVOL |
| Signal deduplicator | deduplicator.py | YES | — |
| Quality gate | quality_gate.py | YES | 30s freshness, rejects mock |
| Signal engine | signal_engine.py | YES | Frozen VWAP_EMA_MOMENTUM_V1 |
| Paper execution | execution.py | YES | bid/ask slippage + statutory costs |
| Position manager | position_manager.py | YES | Trailing stop, SL/TP, kill-switch |
| Audit logger | audit.py | PARTIAL | In-memory only — no DB write |
| Crash recovery | recovery.py | STUB | No real DB source to restore from |
| Session replay | replay.py | STUB | Works only while in-memory; lost on restart |
| Comparator | comparison.py | PARTIAL | No threshold-based Reality Gap logic |
| Report generator | report.py | PARTIAL | Wrong filename; missing verdict categories |
| Central streamer | streamer.py | PARTIAL | B1 bug in approve_signal(); no DB wiring |

### MISSING ENTIRELY:
- Reality-Gap Analyzer (REALITY_GAP_DETECTED verdict engine)
- Kill Switch Levels 1-5 (only Level 3 emergency stop exists)
- DB persistence for live ticks, candles, signals, positions
- Phase 7 qualification engine with formal verdict rules
- Frontend /live route (Live Paper Dashboard)
- WebSocket/SSE for real-time frontend push
- docs/PHASE7_ARCHITECTURE.md
- docs/PHASE7_OPERATIONS.md
- docs/PHASE7_DATA_PROVENANCE.md
- docs/PHASE7_SAFETY.md

---

## 5. DATABASE SCHEMA (models.py)

13 tables exist: users, stocks, market_data, news, market_regimes, technical_indicators,
stock_scores, trade_signals, risk_checks, paper_orders, paper_positions, trades,
portfolio_snapshots, strategy_runs, system_logs.

NO live_* tables — all Phase 7 state is in-memory only.

---

## 6. SAFETY AUDIT

| Control | Status | Notes |
|---------|--------|-------|
| IS_PAPER_TRADING = True | ENFORCED | config.py |
| Real broker SDK not installed | SAFE | Not in requirements.txt |
| No real order endpoints | SAFE | live.py hardcodes real_orders_placed: 0 |
| Human approval workflow | FUNCTIONAL | Signals stay PENDING until approved |
| RiskManager as final gate | BROKEN FOR LIVE PATH | B1 bug; DB path works |
| 15:15 IST square-off | FUNCTIONAL | Both engines |
| Daily kill-switch 3000 INR | FUNCTIONAL | Both engines |
| Mock data quality gate | FUNCTIONAL | quality_gate.py blocks is_mock=True |
| No silent mock fallback | FUNCTIONAL FOR LIVE PATH | quality_gate rejects mock |

---

## 7. IMPLEMENTATION PLAN FOR PHASE 7 (Steps A-L)

### Step A — Fix B1: RiskManager Integration in live/streamer.py
- Replace check_signal() call with validate_trade() with correct parameters

### Step B — Extended Data Provenance States
- Extend LiveDataQualityGate to emit all 7 states: LIVE, STALE, DISCONNECTED, UNCONFIGURED, MOCK, INVALID, ERROR

### Step C — Reality-Gap Analyzer
- New class RealityGapAnalyzer in live/reality_gap.py
- Configurable thresholds: win_rate_threshold_pct, expectancy_threshold, sharpe_threshold
- Verdicts: INSUFFICIENT_LIVE_DATA, CONTINUE_PAPER_TRADING, REALITY_GAP_DETECTED, STRATEGY_DEGRADATION_DETECTED, PAPER_VALIDATION_PASSED

### Step D — Hierarchical Kill Switch (5 Levels)
- New class HierarchicalKillSwitch in live/kill_switch.py
- Level 1: Pause signal generation
- Level 2: No new entries (allow exits only)
- Level 3: Close all positions (existing emergency stop)
- Level 4: Freeze all activity + alert
- Level 5: Full system halt + require manual reset

### Step E — DB Models for Live State
- Add to models.py: LiveSession, LiveSignalRecord, LivePositionRecord, LiveAuditRecord
- Use Alembic migration to avoid existing table loss

### Step F — Wire Audit Logger to DB
- Extend LiveAuditLogger.log() to also write to SystemLog table

### Step G — Fix Report Paths
- Change report.py output to phase7_paper_trading_validation.md/.json

### Step H — Phase 7 Documentation
- Create docs/PHASE7_ARCHITECTURE.md
- Create docs/PHASE7_OPERATIONS.md
- Create docs/PHASE7_DATA_PROVENANCE.md
- Create docs/PHASE7_SAFETY.md

### Step I — Frontend Live Paper Dashboard
- New route: frontend/src/app/live/page.tsx
- Components: DataQualityBanner, PendingSignalsPanel, LivePositionsPanel, RealityGapPanel, KillSwitchPanel, AuditLogStream
- Add /live nav link to Header.tsx

### Step J — WebSocket/SSE for Real-Time Push
- Add FastAPI SSE endpoint /api/live/stream
- Frontend EventSource client for live updates

### Step K — One Real Broker Integration (Zerodha)
- Add kiteconnect to requirements.txt
- Implement actual HTTP call in ZerodhaKiteAdapter
- If unconfigured: return status UNCONFIGURED (not MOCK, not LIVE)

### Step L — Phase 7 Tests
- test_phase7_reality_gap.py (Reality-Gap Analyzer)
- test_phase7_kill_switch.py (Hierarchical Kill Switch)
- test_phase7_streamer_approve.py (full approve_signal() flow with fixed RiskManager)
- test_phase7_db_persistence.py (verify live state survives restart simulation)

---

## 8. TEST BASELINE

41 test files. 85 passed. 0 failed. 16 warnings (SQLAlchemy utcnow deprecation).
No regression is permitted. All new code must preserve this count.

---

*End of audit. Awaiting user approval before any code changes.*
