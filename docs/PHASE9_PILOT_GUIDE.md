# Phase 9 — Controlled Real-World Paper Trading Pilot & Evidence Engine Guide

> ⚠️ **CRITICAL NOTICE: PAPER TRADING ONLY — NO REAL MONEY ORDERS**  
> All executions, P&L figures, and fills in this system represent simulated paper trading. Real-money order placement is permanently disabled.

---

## 1. System Overview

Phase 9 establishes an **Observation → Execution → Measurement → Validation** pilot engine for the **AI Intraday Trading Agent India**.

Its primary purpose is to run the frozen Phase 6 baseline strategy (`VWAP_EMA_MOMENTUM_V1`) across multiple genuine Indian market trading sessions, gather empirical evidence, and determine if an edge exists under real market data conditions.

### Invariant Rules
1. `IS_PAPER_TRADING = True` and `TRADING_MODE = "PAPER"` remain permanently enforced.
2. Broker adapters (Zerodha, Upstox, Angel One) provide **market data only**.
3. Zero order-placement APIs exist in the codebase.
4. Strategy parameters are frozen:
   - Strategy: `VWAP_EMA_MOMENTUM_V1`
   - Fast EMA: 9
   - Slow EMA: 21
   - RVOL threshold: 1.15
   - ATR Stop Loss: 1.5×
   - ATR Take Profit: 3.0×
5. Positive P&L alone **never** produces a "validated" or "high-confidence" verdict without meeting strict sample size and statistical criteria.

---

## 2. Real Market Data Provenance & UI Modes

The system explicitly classifies data feed provenance into 7 states:

| Provenance State | Meaning | Signal Generation | UI Badge |
|---|---|---|---|
| `LIVE` | Authenticated genuine real-time market data (<30s old) | **PERMITTED** | 🟢 LIVE MARKET DATA |
| `STALE` | Feed connected, but last tick > 30s old | **BLOCKED** | 🟡 STALE DATA |
| `MOCK` | Simulated / synthetic feed active | **BLOCKED** | ⚪ MOCK / SIMULATION |
| `SAMPLE` | Demo / sample data | **BLOCKED** | ⚪ MOCK / SIMULATION |
| `MANUAL` | Injected manual test tick | **BLOCKED** | ⚪ MOCK / SIMULATION |
| `ERROR` | Feed error or invalid prices | **BLOCKED** | 🔴 NO LIVE DATA |
| `UNCONFIGURED` | No broker API credentials configured | **BLOCKED** | 🔴 NO LIVE DATA |

---

## 3. Paper Trading Session Lifecycle

A paper trading session manages the trading lifecycle for a single market date.

### Session Boundaries
- A session covers exactly one trading date (`YYYY-MM-DD`).
- Data is **never** mixed across dates.
- Closing a session automatically compiles the 20-section daily session report.

### API Controls
- Start session: `POST /api/phase9/session/start?provider=ZERODHA_KITE`
- Close session: `POST /api/phase9/session/close?reason=MANUAL_CLOSE`
- Current status: `GET /api/phase9/status`

---

## 4. Paper Execution Realism & Accounting Equation

Every paper execution tracks:
- Intended entry vs simulated fill price
- Entry slippage (bid/ask spread based)
- Intended exit vs simulated exit price
- Exit slippage
- Indian statutory regulatory charges

### Fundamental Equation
$$\text{Net P\&L} = \text{Gross P\&L} - \text{Transaction Costs} - \text{Execution Slippage}$$

### Itemized Charges (NSE Intraday Equities)
- **Brokerage**: ₹20 flat per executed order leg
- **STT (Securities Transaction Tax)**: 0.025% on sell-side turnover
- **Exchange Turnover Charges**: 0.00345% on total turnover
- **SEBI Turnover Fee**: ₹10 per crore (0.0001%)
- **GST**: 18% on (brokerage + exchange charges)
- **Stamp Duty**: 0.003% on buy-side turnover

---

## 5. Statistical Evidence & Milestone System

Paper trading validation is divided into 5 strict sample milestones:

| Trades | Milestone Stage | Scientific Interpretation |
|---|---|---|
| `< 30` | `INSUFFICIENT` | Sample size too small. Zero statistical conclusions permitted. |
| `30–99` | `VERY PRELIMINARY` | Early indicative pattern. Wide standard errors. |
| `100–299` | `PRELIMINARY` | Empirical distribution forming. Test regime dependency. |
| `300–499` | `EMPIRICAL` | Robust sample across market sessions. Adequate statistical power. |
| `500+` | `HIGH-CONFIDENCE CANDIDATE` | Candidate for institutional review. Real trading still requires separate capital clearance. |

### Statistical Battery Computed:
1. **Bootstrap 95% Confidence Intervals** for win rate and expectancy (1,000 resamples).
2. **Forward Monte Carlo Simulations** (500 runs of 100 forward trades) modeling terminal drawdown distributions.
3. **Probability of Consecutive Losses** ($P(3\text{ losses})$, $P(5\text{ losses})$, $P(8\text{ losses})$).
4. **Estimated Risk of Ruin** under fractional risk modeling.

---

## 6. Analytical Modules

1. **Backtest Comparison**:
   - Drift calculation against Phase 6 frozen baseline (`win_rate_drift`, `expectancy_drift`, `profit_factor_drift`).
   - Classification: `BETTER THAN BACKTEST`, `WITHIN EXPECTED RANGE`, `DEGRADED`, `SEVERELY DEGRADED`.
2. **Regime Performance (9 Regimes)**:
   - `TRENDING_UP`, `TRENDING_DOWN`, `RANGE_BOUND`, `HIGH_VOLATILITY`, `LOW_VOLATILITY`, `GAP_UP`, `GAP_DOWN`, `BREAKOUT`, `BREAKDOWN`.
3. **Time-of-Day Performance (5 Intraday Windows)**:
   - `09:15–10:00`, `10:00–11:30`, `11:30–13:30`, `13:30–14:30`, `14:30–15:15`.
4. **Symbol Concentration Risk**:
   - Flags `HIGH_CONCENTRATION_RISK` if Top 1 symbol contributes > 50% or Top 3 contribute > 80% of total profit.
5. **Data Quality Impact**:
   - Correlates execution latency (<100ms vs >=100ms) with execution slippage and trade expectancy.

---

## 7. Reports Generated

- **Daily Session Report**: `reports/phase9/session_<DATE>.md` and `.json`
- **Cumulative Pilot Report**: `reports/phase9/cumulative_pilot_report.md` and `.json`
- View in browser or export via `GET /api/phase9/report?report_type=cumulative`.

---

## 8. Dashboard Access

Open the research dashboard at:
`http://localhost:3000/phase9`
