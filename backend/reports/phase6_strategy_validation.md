# PHASE 6 — STRATEGY VALIDATION AUDIT REPORT

**Generated At**: 2026-10-08 23:52:59 IST  
**Primary Symbol**: RELIANCE | **Universe**: LIQUID_TOP_10  
**Operational Status**: PAPER TRADING ONLY (Real-Money Execution Disabled)  

---

## 1. Executive Summary & Scientific Verdict

```
+-----------------------------------------------------------------------------+
| FINAL VERDICT: INSUFFICIENT DATA FOR VALIDATION                         |
+-----------------------------------------------------------------------------+
```
**Explanation**: Dataset is synthetic / short-window sample (<6 months or <50 trades). Cannot confirm empirical statistical edge.

---

## 2. Dataset Provenance & Data Quality Audit

- **Dataset Classification**: `SAMPLE`
- **Data Quality Score**: `100.0/100 (INSTITUTIONAL_GRADE)`
- **Total Candles**: 75 | **Unique Trading Days**: 1
- **Corporate Action Status**: `CORPORATE_ACTION_ADJUSTED`
- **Duplicate Candles**: 0.0% | **OHLC Violations**: 0
- **Price Jump Outliers**: 0

---

## 3. Frozen Baseline Configuration (`VWAP_EMA_MOMENTUM_V1`)

- **Fast EMA**: 9 | **Slow EMA**: 21 | **Min RVOL**: 1.15
- **ATR Multipliers**: Stop 1.5x, Target 3.0x (1:2 R:R)
- **Risk Per Trade**: 1.0% Capital | **Max Daily Loss**: ₹3,000.00 Kill-Switch
- **Same-Candle Resolution**: Stop-Loss First (Conservative)

---

## 4. Empirical Portfolio Results (After Indian Statutory Taxes & Slippage)

- **Initial Capital**: ₹100,000.00
- **Net Realized P&L**: ₹-390.63 (-0.39%)
- **Profit Factor**: 0.00 | **Win Rate**: 0.0%
- **Total Trades**: 2 | **Expectancy**: ₹-195.31
- **Maximum Drawdown**: 0.39%
- **Total Statutory Charges**: ₹62.73

---

## 5. Concentration & Outlier Risk Analysis

- **Stock Concentration**: `NO_PROFITABLE_STOCKS`
  - Top 1 Stock Contribution: 0.0%
  - Top 3 Stocks Contribution: 0.0%
- **Trade Concentration**: `INSUFFICIENT_TRADES_FOR_CONCENTRATION_AUDIT`
  - Top 5% Trades Contribution: 0.0%

---

## 6. Overfitting Risk & Out-of-Sample (OOS) Degradation

- **Overfitting Risk Score**: `0.0/100 (LOW_RISK)`
- **OOS Performance Drop**: 0.0%
- **Overfitting Assessment**: Out-of-sample performance is consistent with in-sample expectations.

---

## 7. Dual-Mode Monte Carlo Simulation (1,000 Permutations)

- **Bootstrap 95th %ile Max Drawdown**: 0.4%
- **Trade Reshuffle 95th %ile Max Drawdown**: 0.39%
- **Max Consecutive Losing Streak**: 2 trades

---

## 8. Limitations & Honest Disclosures

1. **Synthetic / Sample Dataset Limitations**: Results on sample datasets cannot be extrapolated to live market returns.
2. **Survivorship Bias**: Backtested on current liquid NSE constituents.
3. **Execution Latency**: Intraday fill prices depend on live exchange order book queue depth.
