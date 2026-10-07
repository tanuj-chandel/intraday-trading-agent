import os
import json
import datetime
from typing import Dict, Any

class Phase6ReportGenerator:
    """
    Writes formal Phase 6 Strategy Validation Reports to disk:
    - reports/phase6_strategy_validation.md
    - reports/phase6_strategy_validation.json
    """

    @classmethod
    def generate_and_save(
        cls,
        validation_data: Dict[str, Any],
        output_dir: str = "reports"
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        symbol = validation_data.get("symbol", "RELIANCE")
        verdict = validation_data.get("final_verdict", "INSUFFICIENT DATA FOR VALIDATION")
        q = validation_data.get("qualification", {})
        qa = validation_data.get("data_quality_audit", {})
        br = validation_data.get("baseline_results", {})
        sc = validation_data.get("stock_concentration", {})
        tc = validation_data.get("trade_concentration", {})
        ovf = validation_data.get("overfitting", {})
        mc = validation_data.get("monte_carlo", {})

        md_content = f"""# PHASE 6 — STRATEGY VALIDATION AUDIT REPORT

**Generated At**: {now}  
**Primary Symbol**: {symbol} | **Universe**: {validation_data.get('universe_id', 'LIQUID_TOP_10')}  
**Operational Status**: PAPER TRADING ONLY (Real-Money Execution Disabled)  

---

## 1. Executive Summary & Scientific Verdict

```
+-----------------------------------------------------------------------------+
| FINAL VERDICT: {verdict:<56} |
+-----------------------------------------------------------------------------+
```
**Explanation**: {validation_data.get('verdict_explanation')}

---

## 2. Dataset Provenance & Data Quality Audit

- **Dataset Classification**: `{q.get('dataset_classification', 'SAMPLE')}`
- **Data Quality Score**: `{qa.get('data_quality_score', 0)}/100 ({qa.get('quality_rating', 'UNRELIABLE')})`
- **Total Candles**: {qa.get('total_candles', 0):,} | **Unique Trading Days**: {qa.get('unique_trading_days', 0)}
- **Corporate Action Status**: `{qa.get('corporate_action_status', 'CORPORATE_ACTION_ADJUSTED')}`
- **Duplicate Candles**: {qa.get('duplicate_candles_pct', 0.0)}% | **OHLC Violations**: {qa.get('invalid_ohlc_count', 0)}
- **Price Jump Outliers**: {qa.get('outlier_count', 0)}

---

## 3. Frozen Baseline Configuration (`VWAP_EMA_MOMENTUM_V1`)

- **Fast EMA**: 9 | **Slow EMA**: 21 | **Min RVOL**: 1.15
- **ATR Multipliers**: Stop 1.5x, Target 3.0x (1:2 R:R)
- **Risk Per Trade**: 1.0% Capital | **Max Daily Loss**: ₹3,000.00 Kill-Switch
- **Same-Candle Resolution**: Stop-Loss First (Conservative)

---

## 4. Empirical Portfolio Results (After Indian Statutory Taxes & Slippage)

- **Initial Capital**: ₹{br.get('initial_capital', 100000):,.2f}
- **Net Realized P&L**: ₹{br.get('net_pnl', 0):,.2f} ({br.get('return_pct', 0):+0.2f}%)
- **Profit Factor**: {br.get('profit_factor', 0):.2f} | **Win Rate**: {br.get('win_rate', 0):.1f}%
- **Total Trades**: {br.get('total_trades', 0)} | **Expectancy**: ₹{br.get('expectancy', 0):,.2f}
- **Maximum Drawdown**: {br.get('max_drawdown_pct', 0):.2f}%
- **Total Statutory Charges**: ₹{br.get('total_charges', 0):,.2f}

---

## 5. Concentration & Outlier Risk Analysis

- **Stock Concentration**: `{sc.get('stock_concentration_flag', 'BALANCED_DIVERSIFICATION')}`
  - Top 1 Stock Contribution: {sc.get('top_1_stock_contribution_pct', 0)}%
  - Top 3 Stocks Contribution: {sc.get('top_3_stock_contribution_pct', 0)}%
- **Trade Concentration**: `{tc.get('trade_concentration_flag', 'HEALTHY_TRADE_DISTRIBUTION')}`
  - Top 5% Trades Contribution: {tc.get('top_5pct_trade_contribution_pct', 0)}%

---

## 6. Overfitting Risk & Out-of-Sample (OOS) Degradation

- **Overfitting Risk Score**: `{ovf.get('overfitting_risk_score', 0)}/100 ({ovf.get('risk_level', 'LOW_RISK')})`
- **OOS Performance Drop**: {ovf.get('metrics_comparison', {}).get('oos_degradation_pct', 0)}%
- **Overfitting Assessment**: {ovf.get('assessment', 'Low risk')}

---

## 7. Dual-Mode Monte Carlo Simulation (1,000 Permutations)

- **Bootstrap 95th %ile Max Drawdown**: {mc.get('mode_a_bootstrap', {}).get('p95_max_drawdown_pct', 0.0)}%
- **Trade Reshuffle 95th %ile Max Drawdown**: {mc.get('mode_b_reshuffle', {}).get('p95_max_drawdown_pct', 0.0)}%
- **Max Consecutive Losing Streak**: {mc.get('max_consecutive_losing_streak', 0)} trades

---

## 8. Limitations & Honest Disclosures

1. **Synthetic / Sample Dataset Limitations**: Results on sample datasets cannot be extrapolated to live market returns.
2. **Survivorship Bias**: Backtested on current liquid NSE constituents.
3. **Execution Latency**: Intraday fill prices depend on live exchange order book queue depth.
"""

        md_path = os.path.join(output_dir, "phase6_strategy_validation.md")
        json_path = os.path.join(output_dir, "phase6_strategy_validation.json")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(validation_data, f, indent=2, default=str)

        return {
            "markdown_path": md_path,
            "json_path": json_path,
            "markdown_content": md_content
        }
