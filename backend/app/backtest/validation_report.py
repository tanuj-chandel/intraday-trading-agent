import datetime
from typing import Dict, Any

class StrategyValidationReportGenerator:
    """
    Generates downloadable and printable institutional-grade Strategy Validation Audit Reports.
    """

    @classmethod
    def generate_report(
        cls,
        backtest_result: Dict[str, Any],
        qualification: Dict[str, Any],
        overfitting: Dict[str, Any],
        walk_forward: Dict[str, Any],
        monte_carlo: Dict[str, Any]
    ) -> Dict[str, Any]:
        now = datetime.datetime.now()
        symbol = backtest_result.get("symbol", "RELIANCE")
        strategy_id = backtest_result.get("strategy_id", "VWAP_EMA_MOMENTUM_V1")

        md_report = f"""# Strategy Validation Audit Report: {strategy_id}

**Generated At**: {now.strftime("%Y-%m-%d %H:%M:%S IST")}  
**Symbol**: {symbol} | **Timeframe**: 5m | **Market**: NSE Equities  
**Operational Status**: PAPER TRADING / SIMULATION ONLY  

---

## 1. Executive Summary & Provenance Gate

- **Dataset Classification**: `{qualification.get('dataset_classification', 'SAMPLE')}`
- **Sample Size Rating**: `{qualification.get('sample_size_rating', 'INSUFFICIENT_SAMPLE')}`
- **Statistical Edge Classification**: `{qualification.get('profitability_classification', 'NO_EDGE_OR_MARGINAL')}`
- **Overfitting Assessment**: `{overfitting.get('risk_level', 'MODERATE_RISK')} (Score: {overfitting.get('overfitting_risk_score', 0)}/100)`

> [!WARNING]
> **Scientific Integrity Notice**:
> {qualification.get('provenance_description', 'Sample dataset.')}

---

## 2. In-Sample vs Out-of-Sample (OOS) Performance

| Metric | Training (IS) | Validation | Out-of-Sample (OOS) | Degradation % |
| :--- | :--- | :--- | :--- | :--- |
| **Profit Factor** | {overfitting.get('metrics_comparison', {}).get('train_profit_factor', 1.0)} | {overfitting.get('metrics_comparison', {}).get('val_profit_factor', 1.0)} | {overfitting.get('metrics_comparison', {}).get('oos_profit_factor', 1.0)} | {overfitting.get('metrics_comparison', {}).get('oos_degradation_pct', 0.0)}% |
| **Return %** | {overfitting.get('metrics_comparison', {}).get('train_return_pct', 0.0)}% | N/A | {overfitting.get('metrics_comparison', {}).get('oos_return_pct', 0.0)}% | N/A |

- **Walk-Forward Efficiency Ratio (WFE)**: `{walk_forward.get('walk_forward_efficiency_ratio', 1.0)}`

---

## 3. Financial Performance & Statutory Costs

- **Initial Capital**: ₹{backtest_result.get('initial_capital', 100000):,.2f}
- **Final Simulated Capital**: ₹{backtest_result.get('final_capital', 100000):,.2f}
- **Net Realized P&L**: ₹{backtest_result.get('net_pnl', 0):,.2f} ({backtest_result.get('return_pct', 0):+0.2f}%)
- **Total Trades**: {backtest_result.get('total_trades', 0)} | **Win Rate**: {backtest_result.get('win_rate', 0):.1f}%
- **Profit Factor**: {backtest_result.get('profit_factor', 0):.2f} | **Expectancy**: ₹{backtest_result.get('expectancy', 0):,.2f}
- **Maximum Drawdown**: ₹{backtest_result.get('max_drawdown', 0):,.2f} ({backtest_result.get('max_drawdown_pct', 0):.2f}%)
- **Total Indian Taxes & Statutory Fees**: ₹{backtest_result.get('total_charges', 0):,.2f}
- **Sharpe Ratio**: {backtest_result.get('sharpe_ratio', 0):.2f} | **Sortino Ratio**: {backtest_result.get('sortino_ratio', 0):.2f}

---

## 4. Monte Carlo Risk & Extreme Drawdowns (1,000 Permutations)

- **Median Simulated Max Drawdown**: {monte_carlo.get('mode_a_bootstrap', {}).get('median_max_drawdown_pct', 0.0)}%
- **95th Percentile Max Drawdown**: {monte_carlo.get('mode_a_bootstrap', {}).get('p95_max_drawdown_pct', 0.0)}%
- **Worst Case Simulated Drawdown**: {monte_carlo.get('mode_a_bootstrap', {}).get('worst_simulated_drawdown_pct', 0.0)}%
- **Max Consecutive Losing Streak**: {monte_carlo.get('max_consecutive_losing_streak', 0)} trades

---

## 5. Limitations & Caveats

1. **Paper Trading Simulation Only**: Past simulation results are not indicative of future market returns. Real money orders remain disabled.
2. **Survivorship Bias Disclosure**: Backtested against fixed current index constituents.
3. **Execution Realism**: Real execution is subject to exchange order queues, market depth, and timing latencies.
"""

        return {
            "report_title": f"Strategy Validation Audit Report — {strategy_id}",
            "generated_at": now.isoformat(),
            "symbol": symbol,
            "markdown_content": md_report,
            "qualification": qualification,
            "overfitting": overfitting,
            "backtest_summary": {
                "net_pnl": backtest_result.get("net_pnl", 0),
                "profit_factor": backtest_result.get("profit_factor", 0),
                "total_trades": backtest_result.get("total_trades", 0),
                "max_drawdown_pct": backtest_result.get("max_drawdown_pct", 0)
            }
        }
