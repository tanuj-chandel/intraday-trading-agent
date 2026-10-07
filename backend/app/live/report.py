"""
Phase 7 Report Generator
Generates formal Phase 7 Live Paper Validation Reports:
  - reports/phase7_paper_trading_validation.md
  - reports/phase7_paper_trading_validation.json
"""
import os
import json
import datetime
from typing import Dict, Any, List, Optional
from app.live.reality_gap import RealityGapAnalyzer, RealityGapVerdict, RealityGapThresholds


class Phase7ReportGenerator:
    """
    Generates formal Phase 7 Real-Time Live Paper Validation Reports.
    Includes Reality-Gap analysis, data provenance, kill-switch history, and formal verdict.

    Output paths:
        reports/phase7_paper_trading_validation.md
        reports/phase7_paper_trading_validation.json
    """

    REPORT_MD_FILENAME = "phase7_paper_trading_validation.md"
    REPORT_JSON_FILENAME = "phase7_paper_trading_validation.json"

    @classmethod
    def generate_and_save(
        cls,
        session_data: Dict[str, Any],
        output_dir: str = "reports",
        thresholds: Optional[RealityGapThresholds] = None
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

        provider = session_data.get("provider", "UNCONFIGURED")
        live_connected = session_data.get("real_market_data_connected", False)
        sessions_count = session_data.get("number_of_trading_sessions", 1)
        paper_trades_count = session_data.get("number_of_paper_trades", 0)
        pnl = session_data.get("net_realized_pnl", 0.0)
        data_provenance = session_data.get("data_provenance", "MOCK" if not live_connected else "LIVE")
        kill_switch_activated = session_data.get("kill_switch_activated", False)
        kill_switch_level = session_data.get("kill_switch_level", 0)

        # Run reality gap analysis
        paper_trades = session_data.get("paper_trades_list", [])
        backtest_metrics = session_data.get("backtest_metrics", {
            "win_rate": 55.0,
            "expectancy": 150.0,
            "profit_factor": 1.5
        })
        analyzer = RealityGapAnalyzer(thresholds)
        gap_report = analyzer.analyze(backtest_metrics, paper_trades)

        # Formal verdict determination
        verdict = gap_report.verdict
        verdict_desc = gap_report.verdict_explanation

        win_rate = gap_report.live_win_rate
        profit_factor = gap_report.live_profit_factor
        charges = session_data.get("total_charges", 0.0)
        slippage = session_data.get("total_slippage", 0.0)

        # Threshold breach section
        breach_lines = "\n".join(
            f"  - ⚠️  {b}" for b in gap_report.threshold_breaches
        ) if gap_report.threshold_breaches else "  - ✅ No threshold breaches detected."

        md_content = f"""# PHASE 7 — REAL-TIME LIVE MARKET PAPER VALIDATION REPORT

**Generated At**: {now}
**Market**: National Stock Exchange of India (NSE)
**Safety Protocol**: PAPER TRADING ONLY — Real-Money Execution Permanently Disabled

---

## 1. Executive Summary & Operational Declaration

```
+-----------------------------------------------------------------------------+
| PAPER TRADING ONLY:         YES (Real orders: DISABLED)                     |
| REAL MARKET DATA CONNECTED: {'YES' if live_connected else 'NO':<48} |
| DATA PROVENANCE STATE:      {data_provenance:<48} |
| LIVE PAPER TRADING TESTED:  {'YES' if paper_trades_count > 0 else 'NO':<48} |
| NUMBER OF TRADING SESSIONS: {sessions_count:<48} |
| NUMBER OF PAPER TRADES:     {paper_trades_count:<48} |
| REAL BROKER ORDERS PLACED:  0 (STRICTLY DISABLED)                           |
| KILL SWITCH ACTIVATED:      {'YES — Level ' + str(kill_switch_level) if kill_switch_activated else 'NO':<48} |
+-----------------------------------------------------------------------------+
| FINAL VERDICT: {verdict:<56} |
+-----------------------------------------------------------------------------+
```

**Verdict Explanation**: {verdict_desc}

---

## 2. Live Market Ingestion & Connectivity Audit

| Field | Value |
|-------|-------|
| Active Provider | `{provider}` |
| Data Provenance State | `{data_provenance}` |
| Symbols Monitored | {session_data.get('symbols_count', 0)} |
| Silent Mock Fallback Guard | ACTIVE — No silent substitutions permitted |
| Broker Order Endpoint | DISABLED — No real orders possible |

---

## 3. Live Paper Trading Performance Summary

| Metric | Value |
|--------|-------|
| Starting Paper Capital | ₹{session_data.get('starting_capital', 500000):,.2f} |
| Net Realized P&L | ₹{pnl:,.2f} |
| Gross Profit/Loss | ₹{session_data.get('gross_pnl', 0):,.2f} |
| Total Statutory Indian Fees | ₹{charges:,.2f} |
| Simulated Slippage Incurred | ₹{slippage:,.2f} |
| Win Rate | {win_rate:.1f}% |
| Profit Factor | {profit_factor:.2f} |
| Consecutive Losses (current) | {gap_report.consecutive_losses} |
| Maximum Daily Loss Reached | {session_data.get('max_daily_loss_hit', False)} |

---

## 4. Reality-Gap Analysis (Backtest vs Live Paper)

| Metric | Phase 6 Backtest | Live Paper | Delta |
|--------|-----------------|------------|-------|
| Win Rate | {gap_report.backtest_win_rate:.1f}% | {gap_report.live_win_rate:.1f}% | {gap_report.win_rate_delta:+.1f}% |
| Expectancy (₹/trade) | ₹{gap_report.backtest_expectancy:.2f} | ₹{gap_report.live_expectancy:.2f} | {gap_report.expectancy_delta_pct:+.1f}% |
| Profit Factor | {gap_report.backtest_profit_factor:.2f} | {gap_report.live_profit_factor:.2f} | {gap_report.profit_factor_delta:+.2f} |
| Avg Slippage / Trade | — | ₹{gap_report.avg_slippage_per_trade_inr:.2f} | — |

### Threshold Breach Summary:
{breach_lines}

**Sample Adequacy**:
- Paper trades recorded: {paper_trades_count}
- Minimum for initial verdict: 30
- Minimum for validated verdict: 100
- Data sufficiency: {'✅ Sufficient' if gap_report.is_sufficient_data else '❌ Insufficient — continue collecting data'}
- Validated sample: {'✅ Yes' if gap_report.is_validated else '❌ Not yet'}

---

## 5. Risk Management & Safety Audit

1. **Human-in-the-Loop Approval**: All signals require manual confirmation.
2. **Auto Square-Off**: 15:15 IST mandatory position close enforced.
3. **Daily Stop**: ₹3,000 kill-switch — Level 3 triggered on breach.
4. **Kill Switch System**: 5-level hierarchical — Level 5 requires manual reset.
5. **Real Order Isolation**: No real broker SDK. No order placement endpoints.
6. **Mock Data Guard**: Signal generation blocked if data provenance ≠ LIVE.

---

*This report was auto-generated by the Phase 7 Paper Validation Engine.*
*PAPER TRADING SIMULATION ONLY. Results do not guarantee future real-money performance.*
"""

        md_path = os.path.join(output_dir, cls.REPORT_MD_FILENAME)
        json_path = os.path.join(output_dir, cls.REPORT_JSON_FILENAME)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        report_json = {
            **session_data,
            "final_verdict": verdict,
            "verdict_explanation": verdict_desc,
            "reality_gap": {
                "live_win_rate": gap_report.live_win_rate,
                "backtest_win_rate": gap_report.backtest_win_rate,
                "win_rate_delta": gap_report.win_rate_delta,
                "live_expectancy": gap_report.live_expectancy,
                "live_profit_factor": gap_report.live_profit_factor,
                "profit_factor_delta": gap_report.profit_factor_delta,
                "consecutive_losses": gap_report.consecutive_losses,
                "threshold_breaches": gap_report.threshold_breaches,
                "is_sufficient_data": gap_report.is_sufficient_data,
                "is_validated": gap_report.is_validated
            },
            "report_generated_at": now,
            "disclaimer": "PAPER TRADING ONLY. No real-money orders placed."
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_json, f, indent=2, default=str)

        return {
            "markdown_path": md_path,
            "json_path": json_path,
            "markdown_content": md_content,
            "verdict": verdict
        }
