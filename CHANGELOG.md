# CHANGELOG

## [Unreleased] - 2026-10-04

### Phase 1: Risk & Position Sizing Fixes
- **Tri-Constraint Position Sizing**:
  - Implemented `calculate_position_size` in `RiskManager` with three bounds:
    1. Risk-based quantity: `floor((Equity * risk%) / |Entry - SL|)`
    2. Notional-cap quantity: `floor((Equity * MAX_POSITION_NOTIONAL_PCT) / Entry)` (default 20% max per position) and `MAX_TOTAL_EXPOSURE_PCT` (default 100% total across open positions).
    3. Margin-based quantity: using `MIS_LEVERAGE` (default 5x).
  - Final quantity is strictly `min(qty_risk, qty_notional, qty_margin)`. If final quantity < 1, the trade is rejected with a clear explanation logged.
- **Risk Defaults**:
  - Changed `MAX_RISK_PER_TRADE_PCT` default from 2.0% to 0.5% (configurable).
  - Configured `MAX_DAILY_LOSS_PCT` to 2.0% of capital (₹10,000 on ₹5,00,000 capital).
- **Safety Enforcement**:
  - Added `LIVE_TRADING_ENABLED = False` to `Settings` (default `False`), preserving `IS_PAPER_TRADING = True`.
- **Trading Quotas, Thresholds & Cooldowns**:
  - Added `MAX_TRADES_PER_DAY` (default 10, enforced as an upper ceiling).
  - Added `MIN_SIGNAL_SCORE` (default 70.0; no signals below this threshold can be executed).
  - Added `MAX_TRADES_PER_SYMBOL_PER_DAY` (default 2 trades per symbol per day).
  - Added `COOLDOWN_AFTER_SL_MINUTES` (default 45 minutes after SL hit per symbol).
- **Sector Concentration Limits**:
  - Created `backend/app/data/sector_map.json` mapping NSE universe tickers to sectors.
  - Added `MAX_POSITIONS_PER_SECTOR` (default 2). Rejects signals when 2 positions already exist in the same sector.
- **Rejection Logging**:
  - Added `reject_reason` column to `TradeSignal` database model and schemas.
  - Updated paper engine, live streamer, and REST endpoints to save the rejection reason directly to the database.
- **Unit Tests**:
  - Updated `backend/tests/test_risk_manager.py` with 9 passing unit tests covering:
    - Huge-quantity capping (price 1000, SL distance 5)
    - Sector concentration limit
    - Post-SL cooldown
    - Per-symbol daily cap
    - Daily loss floor trigger
    - Insufficient quantity (< 1 share) rejection
    - Minimum signal score rejection

### Phase 2: Two-Way Telegram Approval for Entries Only
- **Two-Way Approval Flow**:
  - Signals generated are tagged with initial status `PENDING_APPROVAL`.
  - Dispatches formatted Telegram message with inline buttons `[✅ Approve {dir} #{id}]` and `[❌ Reject #{id}]` showing symbol, side, entry, SL, TP, qty, risk in INR, R:R, score, and technical/news rationale.
  - Implemented `APPROVAL_TIMEOUT_SECONDS = 120`. Signals unapproved past 120s are automatically marked `EXPIRED` and cancelled.
  - On approval: fetches latest price. If price drifted more than `MAX_ENTRY_DRIFT_PCT` (default 0.3%) from signal entry, or if SL/TP is already breached, entry is cancelled and logged. Otherwise recalculates quantity if needed and enters trade.
  - Exits (stop-loss, target, breakeven, trailing, 15:15 square-off, kill switch) remain 100% automated and never wait for approval.
  - Configured `AUTO_APPROVE = False` default (nothing enters without explicit approval).
- **Security & Commands**:
  - `TELEGRAM_ALLOWED_CHAT_ID`: Rejects and silently ignores any command or callback query from unauthorized chat IDs.
  - Interactive commands supported: `/status`, `/pnl`, `/positions`, `/pause`, `/resume`, `/close SYMBOL`, `/close ALL` (with inline confirmation prompt), `/help`.
- **Frontend Dashboard Alignment**:
  - Updated `LiveSignals.tsx` to handle `PENDING_APPROVAL`, show rejection/expiry notes, and support idempotent action handling where first action wins and duplicate clicks are ignored safely.
- **Unit Tests**:
  - Created `backend/tests/test_telegram_two_way_approval.py` with 6 unit tests covering:
    - Unauthorized chat ID rejection
    - Unauthorized command isolation
    - Unauthorized callback query rejection
    - Signal expiry cancellation
    - Price drift rejection (> 0.3%)
    - Double-approve idempotency

### Phase 3: Execution Layer Safety
- **Broker Abstraction Layer (`backend/app/execution/broker_base.py`)**:
  - Created `AbstractBroker` base interface with `place_order`, `place_stop_loss_order`, `cancel_order`, `get_order_status`, `get_positions`, and `refresh_session_token`.
  - Created `PaperBroker`: simulates realistic market and SL orders, maintains local order books, tracks partial fills, and handles idempotency deduplication.
  - Created `LiveBroker` stub for Angel One SmartAPI / Zerodha Kite Connect, hard-locked behind `LIVE_TRADING_ENABLED=True` and `IS_PAPER_TRADING=False` with immediate `PermissionError` fail-safes.
- **Immediate Broker-Side Stop-Loss & Fail-Closed Protection**:
  - Implemented `execute_entry_with_broker_sl`: On entry, places the broker-side SL/SL-M order immediately.
  - If the broker SL order fails or is rejected, the position is immediately liquidated via a market exit order and an emergency alert is triggered.
- **Order State Machine & Idempotency**:
  - Implemented order states: `NEW -> SENT -> PARTIAL -> FILLED / REJECTED / CANCELLED`.
  - Added idempotency keys (`ENTRY_{signal_id}_{symbol}`, `SL_{signal_id}_{symbol}_{order_id}`) preventing duplicate orders from repeated signals or double approval.
  - Added partial fill quantity tracking to scale SL quantity and position records accurately.
- **Reconciliation & Watchdog Background Jobs**:
  - 60-second reconciliation worker: compares local in-memory/DB positions against broker positions. On mismatch, pauses new entries (Level 2 Kill Switch) and fires Telegram alert.
  - 30-second health watchdog: monitors data feed freshness. If feed is stale beyond `STALE_FEED_SECONDS` (15s), pauses entries; 3 consecutive failures trigger Level 2 Kill Switch.
- **Crash Recovery & Startup Guard**:
  - Startup crash recovery: reloads open positions from SQLite database on boot into memory to resume exit management without taking any new trades.
  - Hard guard: if `LIVE_TRADING_ENABLED=True`, verifies real broker feed and aborts (`RuntimeError`) if connected to synthetic, mock, or Yahoo Finance feeds.
  - Daily broker session token refresh routine on startup.
- **Unit Tests**:
  - Created `backend/tests/test_execution_safety.py` with 6 unit tests covering:
    - SL order failure triggering immediate liquidation and fail-closed state
    - Partial fill adjusting position and SL quantities
    - Duplicate signal idempotency
    - Health watchdog stale feed detection & Level 2 kill switch activation
    - Hard startup guard refusing synthetic/mock feeds in live mode
    - LiveBroker permission refusal when live mode is disabled

### Phase 4: Trade Quality Filters & Universe Logic
- **Trade Quality Filters Engine (`backend/app/strategies/quality_filters.py`)**:
  - All filters individually toggleable in `backend/app/core/config.py` and logged to `LiveAuditLogger` when blocking trades.
  - **Time Filters**:
    - `TIME_FILTER_ENABLED = True`
    - Opening window block (09:15-09:25 IST): `NO_ENTRY_BEFORE_TIME = "09:25"`.
    - Late afternoon block (> 14:30 IST): `NO_ENTRY_AFTER_TIME = "14:30"`.
    - Lunch-chop reduction (12:00-13:30 IST): `LUNCH_CHOP_FILTER_ENABLED = True`, raising required minimum score to `LUNCH_CHOP_MIN_SCORE = 85.0`.
  - **Market Regime Filter**:
    - `REGIME_FILTER_ENABLED = True`
    - Classifies market into `TRENDING`, `CHOPPY`, `HIGH_VOL` using India VIX and Nifty trend (Price vs VWAP and EMA 9/21).
    - Requires higher score threshold (85.0) or blocks entries in `CHOPPY` and `HIGH_VOL` / extreme VIX (> 26.0).
    - Exposed current market regime on live dashboard (`live_streamer.get_status()["market_regime"]`).
  - **Tradability Checks**:
    - `TRADABILITY_CHECKS_ENABLED = True`
    - Circuit limit proximity: skips stocks within 1% of Upper / Lower Circuit (`CIRCUIT_LIMIT_BUFFER_PCT = 0.01`).
    - Skips exchange-halted stocks (`SKIP_HALTED_STOCKS = True`).
    - Skips surveillance-listed stocks (`SKIP_ASM_GSM_STOCKS = True`, configurable list `ASM_GSM_SYMBOLS`).
    - Skips stocks with corporate actions / board meeting earnings results today (`SKIP_CORPORATE_ACTION_TODAY = True`).
  - **Event-Day Mode**:
    - `EVENT_DAY_FILTER_ENABLED = True`
    - Configurable event dates (`EVENT_DAYS`) for Union Budget, RBI MPC policy, and monthly expiries.
    - Configurable action: `EVENT_DAY_ACTION = "REDUCE_RISK"` (halves risk with `EVENT_DAY_RISK_MULTIPLIER = 0.5`) or `"PAUSE_TRADING"`.
- **Dynamic Slippage Realism (`backend/app/execution/slippage_model.py`)**:
  - Paper fills use the next tick/candle price after approval rather than signal entry price.
  - Slippage scales with bid-ask spread and stock liquidity tier (`VERY_HIGH`: 0.02%, `HIGH`: 0.05%, `MEDIUM`: 0.10%, `LOW`: 0.20%).
- **News Sentiment Pipeline**:
  - News older than `NEWS_MAX_AGE_MINUTES` (default 120 minutes) is marked stale and ignored for trade signals.
  - Capped maximum news weight in multi-factor Alpha Score to `NEWS_MAX_ALPHA_WEIGHT = 10.0` points out of 100.
  - Authored comprehensive documentation in `backend/docs/NEWS_SENTIMENT_PIPELINE.md`.
- **Strategy Interface (ORB & Mean Reversion)**:
  - Extended `Strategy` base interface with `get_id()`, `is_enabled()`, `record_trade_result()`, and `get_performance_summary()`.
  - Implemented `OpeningRangeBreakoutStrategy` (`app/strategies/orb.py`) and `MeanReversionStrategy` (`app/strategies/mean_reversion.py`), registered as inactive (`is_enabled=False`) in `StrategyRegistry` for future activation.
- **Unit Tests**:
  - Created `backend/tests/test_trade_quality_filters.py` with 10 unit tests covering time filters, lunch chop, regime filters, tradability checks, event-day mode, dynamic slippage scaling, news freshness & alpha capping, and disabled strategy interfaces.

### Phase 5: Safe Online Learner Architecture
- **Sample Size Safeguards**:
  - Enforced `MIN_TRADES_FOR_LEARNING = 100` (configurable in `config.py`). Parameter proposals are strictly blocked if completed trade sample count is below 100.
- **Strict Parameter Bounds & Step Constraints**:
  - ATR Stop-Loss multiplier is clamped strictly within `[MIN_ATR_SL_MULTIPLIER = 1.3, MAX_ATR_SL_MULTIPLIER = 2.0]`.
  - Maximum incremental step per update capped at `MAX_ATR_PARAM_STEP = 0.1`.
- **Fixed Risk-to-Reward Ratio Invariance**:
  - Stop-loss multiplier adjustments dynamically adjust target-profit multiplier (`tp_multiplier = round(sl_multiplier * TARGET_RISK_REWARD_RATIO, 2)`) maintaining fixed R:R (`TARGET_RISK_REWARD_RATIO = 2.0`).
- **Recommend-Only Mode & Human-in-the-Loop Governance**:
  - `LEARNER_RECOMMEND_ONLY = True` by default: the learner never applies parameter adjustments autonomously.
  - Proposals are saved into new database table `parameter_proposals` containing `old_value`, `new_value`, `tp_multiplier`, `target_rr`, `status`, `evidence`, `sample_size`, and `win_rate_pct`.
  - Approval and rejection workflows supported via Telegram commands (`/approve_param <id>`, `/reject_param <id>`, `/proposals`) and REST API (`/api/v1/learning/proposals`).
- **Audit Version History & One-Command Rollback**:
  - Applied parameter changes are logged in `parameter_version_history` with full audit timestamps, old/new values, and author.
  - One-command rollback supported via Telegram (`/rollback_param`) and REST API (`POST /api/v1/learning/rollback`), restoring previous multipliers and recording rollback history.
- **Regime & Time-of-Day Segmented Statistics**:
  - Implemented `Phase8RegimeSegmenter` partitioning performance stats by market regime (`TRENDING`, `CHOPPY`, `HIGH_VOL`) and time windows (`OPEN_30M`, `MID_SESSION`, `CLOSE_1H`).
  - Protects core parameters from noisy stop-outs during choppy or high-volatility sessions.
- **Unit Tests**:
  - Created `backend/tests/test_safe_learner.py` with 7 unit tests covering:
    - Minimum sample size blocking (< 100 trades)
    - ATR multiplier bounds `[1.3, 2.0]` and step cap `<= 0.1`
    - Fixed R:R invariance enforcement
    - Recommend-only proposal generation
    - Human approval and version history tracking
    - One-command rollback to previous parameter sets
    - Market regime & time-of-day segmentation isolation

### Phase 6: Metrics, Reports, Go-Live Criteria & Historical Parquet Persistence
- **Comprehensive Quant Metrics Engine (`backend/app/analytics/performance.py`)**:
  - Added average R achieved (`average_r`), net expectancy per trade after all statutory costs (`expectancy_per_trade`), expectancy in R units (`expectancy_r`), longest losing streak (`longest_losing_streak`), and average slippage (`average_slippage`).
  - Added multi-dimensional segmented performance breakdowns:
    - `performance_by_strategy` (trades, win rate, net P&L, profit factor)
    - `performance_by_time_of_day` (`OPEN_30M`, `MID_SESSION`, `CLOSE_1H`)
    - `performance_by_symbol`
    - `performance_by_market_regime` (`TRENDING`, `CHOPPY`, `HIGH_VOL`).
- **Complete Trade Reason Log (`backend/app/models/models.py`)**:
  - Enhanced `Trade` model and `LivePaperPosition` lifecycle to record:
    - `reason_for_entry` (technical + news + score rationale)
    - `reason_for_exit` (`STOP_LOSS_HIT`, `TARGET_HIT`, `TRAILING_STOP_HIT`, `15:15_MANDATORY_SQUARE_OFF`, `MANUAL_CLOSE`)
    - `indicators_snapshot` (RSI, VWAP, EMA, etc.)
    - `news_rationale` (headline, sentiment, impact score)
    - `slippage_incurred` (points/INR)
    - `achieved_r` (realized R-multiple).
- **Automated End-of-Day Telegram Report (15:45 IST)**:
  - Added `send_end_of_day_report` in `TelegramNotifier` and scheduled event at 15:45 IST.
  - Report compiles: daily trades executed, win rate %, realized net P&L, statutory charges, key metrics (average R, profit factor, net expectancy, max drawdown), rejected signal counts with top reasons, and watchdog system warnings.
  - Added on-demand Telegram command `/eod_report`.
- **Backtesting Walk-Forward Upgrade (`backend/app/backtest/walk_forward.py`)**:
  - Enhanced `WalkForwardAnalyzer` with out-of-sample holdout split (`out_of_sample_split`) and multi-window rolling walk-forward (`rolling_walk_forward`).
  - Configured to use the exact same dynamic liquidity-tiered slippage model (`DynamicSlippageModel`) and statutory transaction cost schedule as paper trading.
- **Go-Live Checklist & Hardware Safety Guard**:
  - Added backend endpoint `GET /api/v1/system/go-live-checklist` evaluating:
    1. Sample size reliability: ≥ 150 completed paper trades (`GO_LIVE_MIN_TRADES = 150`).
    2. Positive net expectancy after costs: > ₹0.00.
    3. Drawdown ceiling: Max drawdown ≤ 5.0% (`GO_LIVE_MAX_DRAWDOWN_PCT = 5.0`).
    4. Operational resilience: Zero unresolved reconciliation or stale-feed watchdog incidents in last 10 trading days (`GO_LIVE_INCIDENT_WINDOW_DAYS = 10`).
  - Added backend endpoint `POST /api/v1/system/toggle-live-trading` refusing activation with HTTP 400 unless all 4 criteria pass.
  - Created Next.js dashboard page (`frontend/src/app/go-live/page.tsx`) with PASS/FAIL indicator cards and live order placement lock.
  - Added `Go-Live Readiness` navigation tab to `Header.tsx`.
- **Parquet Columnar Historical Storage (`backend/app/data/parquet_storage.py`)**:
  - Created `ParquetStorageEngine` using `pyarrow` for compressed Snappy columnar persistence.
  - Partitioned storage: `backend/app/data/storage/candles/{timeframe}/{symbol}/{date}.parquet` and `storage/ticks/{symbol}/{date}.parquet`.
  - Integrated into `LiveCandleBuilder` to automatically persist completed candles in real time.
- **Unit Tests**:
  - Created `backend/tests/test_phase6_metrics_and_golive.py` with 6 unit tests covering:
    - Performance engine extended metrics & multi-dimensional segmentations
    - Trade reason log storage & JSON persistence
    - End-of-Day Telegram report generation & `/eod_report` command
    - Parquet storage tick and candle round-trip persistence
    - Walk-Forward and Out-of-Sample split evaluation
    - Go-Live checklist validation and live order placement guard refusal.


