"""
Phase 9 — Automated Reporting Engine

Generates comprehensive markdown and JSON validation reports:
1. Daily Session Report: reports/phase9/session_<DATE>.md & .json (20 mandatory sections)
2. Cumulative Pilot Report: reports/phase9/cumulative_pilot_report.md & .json

Every report prominently displays: PAPER TRADING ONLY — NO REAL MONEY ORDERS.
"""
import os
import json
import datetime
from typing import Dict, Any, List, Optional
from app.core.database import SessionLocal
from app.models.models import Phase9DailyReport, Phase9Session, Phase9TradeEvent
from app.phase9.backtest_comparison import Phase9BacktestComparator
from app.phase9.statistical_evidence import Phase9StatisticalEvidenceEngine
from app.phase9.regime_analyzer import Phase9RegimeAnalyzer
from app.phase9.time_of_day_analyzer import Phase9TimeOfDayAnalyzer
from app.phase9.symbol_concentration import Phase9SymbolConcentrationEngine
from app.phase9.data_quality_impact import Phase9DataQualityImpactEngine
from app.phase9.verdict_engine import Phase9VerdictEngine


class Phase9ReportGenerator:
    """
    Constructs and persists daily session and cumulative pilot reports.
    """

    REPORTS_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "reports", "phase9")
    )

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)

    @classmethod
    def generate_daily_report(
        cls,
        session_data: Dict[str, Any],
        paper_trades: List[Dict[str, Any]],
        data_quality_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate 20-section daily session report for a completed session.
        """
        cls._ensure_dir()
        date_str = session_data.get("trading_date", datetime.datetime.now().strftime("%Y-%m-%d"))
        session_id = session_data.get("session_id", f"SESS-{date_str}-001")

        # Analytical Modules Execution
        comparison = Phase9BacktestComparator.compare(paper_trades)
        evidence = Phase9StatisticalEvidenceEngine.compute_evidence(paper_trades)
        regime = Phase9RegimeAnalyzer.analyze(paper_trades)
        tod = Phase9TimeOfDayAnalyzer.analyze(paper_trades)
        concentration = Phase9SymbolConcentrationEngine.analyze(paper_trades)
        dq_impact = Phase9DataQualityImpactEngine.analyze(paper_trades, data_quality_stats)

        # Verdict
        metrics = evidence.get("metrics", {})
        verdict = Phase9VerdictEngine.determine_verdict(
            total_trades=len(paper_trades),
            expectancy=metrics.get("expectancy_inr", 0.0),
            win_rate=metrics.get("win_rate_pct", 0.0),
            profit_factor=metrics.get("profit_factor", 0.0),
            reality_gap_verdict=comparison.get("classification", "WITHIN EXPECTED RANGE")
        )

        report_dict = {
            "title": f"Phase 9 Controlled Paper Trading Daily Session Report — {date_str}",
            "disclaimer": "PAPER TRADING ONLY — NO REAL MONEY ORDERS",
            "session_id": session_id,
            "trading_date": date_str,
            "generated_at": datetime.datetime.now().isoformat(),
            # 20 Mandatory Sections
            "1_data_provenance": {
                "provider": session_data.get("provider", "UNKNOWN"),
                "provenance_state": session_data.get("provenance_state", "LIVE"),
                "is_genuine_live": session_data.get("provider") != "MOCK",
            },
            "2_session_health": {
                "status": session_data.get("status", "CLOSED"),
                "valid_ticks": session_data.get("valid_ticks", 0),
                "rejected_ticks": session_data.get("rejected_ticks", 0),
            },
            "3_signals": {
                "generated": session_data.get("generated_signals", 0),
                "approved": session_data.get("approved_signals", 0),
                "rejected": session_data.get("rejected_signals", 0),
            },
            "4_trades": {
                "executed": len(paper_trades),
                "winning": metrics.get("winning_trades", 0),
                "losing": metrics.get("losing_trades", 0),
            },
            "5_gross_pnl": session_data.get("gross_pnl", 0.0),
            "6_transaction_costs": session_data.get("transaction_costs", 0.0),
            "7_slippage": session_data.get("slippage", 0.0),
            "8_net_pnl": session_data.get("net_pnl", 0.0),
            "9_drawdown": session_data.get("max_drawdown", 0.0),
            "10_win_rate_pct": metrics.get("win_rate_pct", 0.0),
            "11_expectancy_inr": metrics.get("expectancy_inr", 0.0),
            "12_regime_performance": regime.get("regimes", {}),
            "13_time_of_day_performance": tod.get("time_slots", {}),
            "14_symbol_concentration": concentration,
            "15_data_quality_incidents": session_data.get("data_quality_incidents", 0),
            "16_kill_switch_events": session_data.get("kill_switch_events", 0),
            "17_comparison_with_phase6": comparison,
            "18_statistical_evidence": evidence,
            "19_validation_milestone": evidence.get("milestone", {}),
            "20_scientific_interpretation": verdict,
        }

        # Build Markdown
        md_content = f"""# {report_dict['title']}

> ⚠️ **CRITICAL MANDATORY NOTICE: PAPER TRADING ONLY — NO REAL MONEY ORDERS**  
> All executions, P&L figures, and fills in this report represent simulated paper trading. Real-money order placement is permanently disabled.

---

## 1. Executive Summary & Verdict

| Metric | Result |
|---|---|
| **Scientific Verdict** | **{verdict['verdict']}** |
| **Session ID** | `{session_id}` |
| **Trading Date** | `{date_str}` |
| **Provider** | `{session_data.get('provider', 'UNKNOWN')}` |
| **Total Paper Trades** | `{len(paper_trades)}` |
| **Net Realized P&L** | **₹{session_data.get('net_pnl', 0.0):.2f}** |
| **Gross P&L** | ₹{session_data.get('gross_pnl', 0.0):.2f} |
| **Transaction Costs** | ₹{session_data.get('transaction_costs', 0.0):.2f} |
| **Execution Slippage** | ₹{session_data.get('slippage', 0.0):.2f} |
| **Win Rate** | `{metrics.get('win_rate_pct', 0.0):.1f}%` |
| **Expectancy** | `₹{metrics.get('expectancy_inr', 0.0):.2f} / trade` |
| **Validation Milestone** | `{evidence.get('milestone', {}).get('stage', 'INSUFFICIENT')}` |

**Interpretation**: {verdict['explanation']}

---

## 2. P&L & Cost Attribution (Gross − Costs − Slippage = Net)

```
  Gross P&L:          ₹{session_data.get('gross_pnl', 0.0):>10.2f}
− Transaction Costs:  ₹{session_data.get('transaction_costs', 0.0):>10.2f} (Brokerage, STT, Exchange, GST, SEBI, Stamp)
− Execution Slippage: ₹{session_data.get('slippage', 0.0):>10.2f}
==========================================
  Net Realized P&L:   ₹{session_data.get('net_pnl', 0.0):>10.2f}
```

---

## 3. Comparison with Phase 6 Frozen Backtest Baseline

- **Baseline Source**: {comparison.get('baseline_source', 'Phase 6')}
- **Drift Classification**: **{comparison.get('classification', 'UNKNOWN')}**

| Metric | Phase 6 Backtest | Phase 9 Paper | Drift | Status |
|---|---|---|---|---|
| Win Rate | {comparison.get('comparison', {}).get('win_rate', {}).get('backtest', 55.0)}% | {comparison.get('comparison', {}).get('win_rate', {}).get('paper', 0.0)}% | {comparison.get('comparison', {}).get('win_rate', {}).get('drift', 0.0):+}% | {comparison.get('comparison', {}).get('win_rate', {}).get('status', 'N/A')} |
| Expectancy | ₹{comparison.get('comparison', {}).get('expectancy', {}).get('backtest', 150.0)} | ₹{comparison.get('comparison', {}).get('expectancy', {}).get('paper', 0.0)} | ₹{comparison.get('comparison', {}).get('expectancy', {}).get('drift', 0.0):+} | {comparison.get('comparison', {}).get('expectancy', {}).get('status', 'N/A')} |
| Profit Factor | {comparison.get('comparison', {}).get('profit_factor', {}).get('backtest', 1.5)} | {comparison.get('comparison', {}).get('profit_factor', {}).get('paper', 0.0)} | {comparison.get('comparison', {}).get('profit_factor', {}).get('drift', 0.0):+} | {comparison.get('comparison', {}).get('profit_factor', {}).get('status', 'N/A')} |

---

## 4. Market Regime Breakdown

| Regime | Trades | Win Rate | Net P&L | Expectancy | Profit Factor |
|---|---|---|---|---|---|
"""
        for r_name, r_data in regime.get("regimes", {}).items():
            if r_data["trade_count"] > 0:
                md_content += f"| {r_name} | {r_data['trade_count']} | {r_data['win_rate_pct']}% | ₹{r_data['net_pnl']:.2f} | ₹{r_data['expectancy_inr']:.2f} | {r_data['profit_factor']} |\n"

        md_content += """
---

## 5. Intraday Time-of-Day Distribution

| Time Slot | Trades | Win Rate | Net P&L | Avg Slippage | Expectancy |
|---|---|---|---|---|---|
"""
        for s_name, s_data in tod.get("time_slots", {}).items():
            if s_data["trade_count"] > 0:
                md_content += f"| {s_name} | {s_data['trade_count']} | {s_data['win_rate_pct']}% | ₹{s_data['net_pnl']:.2f} | ₹{s_data['avg_slippage_inr']:.2f} | ₹{s_data['expectancy_inr']:.2f} |\n"

        md_content += f"""
---

## 6. Symbol Concentration Risk

- **Status**: **{concentration.get('concentration_risk', 'LOW')}**
- **Top 1 Symbol Contribution**: {concentration.get('top1_contribution_pct', 0.0)}%
- **Top 3 Symbol Contribution**: {concentration.get('top3_contribution_pct', 0.0)}%

---

## 7. Data Quality & Operational Incidents

- **Valid Ticks**: {session_data.get('valid_ticks', 0)} | **Rejected Ticks**: {session_data.get('rejected_ticks', 0)}
- **Data Quality Incidents**: {session_data.get('data_quality_incidents', 0)}
- **Kill Switch Events**: {session_data.get('kill_switch_events', 0)}

---

> **Audit Disclaimer**:  
> PAPER TRADING ONLY. No real-money trades were submitted to any broker.  
> The strategy parameters remain frozen from Phase 6 (`VWAP_EMA_MOMENTUM_V1`).  
> Past performance during paper simulation does not guarantee future live trading results.
"""

        # Save files
        md_file = os.path.join(cls.REPORTS_DIR, f"session_{date_str}.md")
        json_file = os.path.join(cls.REPORTS_DIR, f"session_{date_str}.json")

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        # Record in database
        cls._persist_report_record(session_id, date_str, md_file, json_file, verdict["verdict"], report_dict)

        return {
            "markdown_path": md_file,
            "json_path": json_file,
            "verdict": verdict["verdict"],
            "summary": report_dict,
        }

    @classmethod
    def generate_cumulative_report(cls) -> Dict[str, Any]:
        """
        Aggregate all historic Phase 9 paper trading sessions into a cumulative pilot report.
        """
        cls._ensure_dir()
        db = SessionLocal()
        try:
            sessions = db.query(Phase9Session).all()
            trades = db.query(Phase9TradeEvent).all()
        finally:
            db.close()

        trade_dicts = [
            {
                "symbol": t.symbol,
                "gross_pnl": t.gross_pnl,
                "net_pnl": t.net_pnl,
                "total_cost": t.total_cost,
                "entry_slippage": t.entry_slippage,
                "exit_slippage": t.exit_slippage,
                "market_regime": t.market_regime,
                "time_of_day_bucket": t.time_of_day_bucket,
                "holding_minutes": t.holding_minutes,
                "latency_ms": t.latency_ms,
            }
            for t in trades
        ]

        total_sessions = len(sessions)
        total_trades = len(trades)

        comparison = Phase9BacktestComparator.compare(trade_dicts)
        evidence = Phase9StatisticalEvidenceEngine.compute_evidence(trade_dicts)
        regime = Phase9RegimeAnalyzer.analyze(trade_dicts)
        tod = Phase9TimeOfDayAnalyzer.analyze(trade_dicts)
        concentration = Phase9SymbolConcentrationEngine.analyze(trade_dicts)

        metrics = evidence.get("metrics", {})
        verdict = Phase9VerdictEngine.determine_verdict(
            total_trades=total_trades,
            expectancy=metrics.get("expectancy_inr", 0.0),
            win_rate=metrics.get("win_rate_pct", 0.0),
            profit_factor=metrics.get("profit_factor", 0.0),
            reality_gap_verdict=comparison.get("classification", "WITHIN EXPECTED RANGE")
        )

        total_gross = sum(t.gross_pnl for t in trades)
        total_costs = sum(t.total_cost for t in trades)
        total_slip = sum(t.entry_slippage + t.exit_slippage for t in trades)
        total_net = sum(t.net_pnl for t in trades)

        report_dict = {
            "title": "Phase 9 Cumulative Controlled Paper Trading Pilot Report",
            "disclaimer": "PAPER TRADING ONLY — NO REAL MONEY ORDERS",
            "generated_at": datetime.datetime.now().isoformat(),
            "total_sessions": total_sessions,
            "total_trades": total_trades,
            "financial_summary": {
                "gross_pnl": round(total_gross, 2),
                "transaction_costs": round(total_costs, 2),
                "slippage": round(total_slip, 2),
                "net_pnl": round(total_net, 2),
            },
            "performance_metrics": metrics,
            "milestone": evidence.get("milestone", {}),
            "verdict": verdict,
            "backtest_comparison": comparison,
            "regime_performance": regime,
            "time_performance": tod,
            "concentration": concentration,
        }

        # Write markdown
        md_file = os.path.join(cls.REPORTS_DIR, "cumulative_pilot_report.md")
        json_file = os.path.join(cls.REPORTS_DIR, "cumulative_pilot_report.json")

        md_content = f"""# Phase 9 Cumulative Controlled Paper Trading Pilot Report

> ⚠️ **CRITICAL MANDATORY NOTICE: PAPER TRADING ONLY — NO REAL MONEY ORDERS**  
> All executions, P&L figures, and fills in this report represent simulated paper trading. Real-money order placement is permanently disabled.

---

## 1. Cumulative Verdict & Status

| Metric | Cumulative Value |
|---|---|
| **Scientific Verdict** | **{verdict['verdict']}** |
| **Milestone Stage** | **{evidence.get('milestone', {}).get('stage', 'INSUFFICIENT')}** |
| **Total Pilot Sessions** | `{total_sessions}` |
| **Total Cumulative Trades** | `{total_trades}` |
| **Total Net Realized P&L** | **₹{total_net:.2f}** |
| **Total Gross P&L** | ₹{total_gross:.2f} |
| **Total Transaction Costs** | ₹{total_costs:.2f} |
| **Total Slippage** | ₹{total_slip:.2f} |
| **Win Rate** | `{metrics.get('win_rate_pct', 0.0):.1f}%` |
| **Expectancy** | `₹{metrics.get('expectancy_inr', 0.0):.2f} / trade` |
| **Profit Factor** | `{metrics.get('profit_factor', 0.0):.2f}` |

---

## 2. Statistical Evidence Battery

- **Win Rate 95% CI (Bootstrap)**: `{evidence.get('bootstrap_95ci', {}).get('win_rate', {}).get('low', 0.0)}% – {evidence.get('bootstrap_95ci', {}).get('win_rate', {}).get('high', 0.0)}%`
- **Expectancy 95% CI (Bootstrap)**: `₹{evidence.get('bootstrap_95ci', {}).get('expectancy_inr', {}).get('low', 0.0)} – ₹{evidence.get('bootstrap_95ci', {}).get('expectancy_inr', {}).get('high', 0.0)}`
- **Forward Monte Carlo Median Max Drawdown**: `₹{evidence.get('monte_carlo_forward', {}).get('median_max_drawdown_inr', 0.0)}`
- **Forward Monte Carlo 95th Percentile Drawdown**: `₹{evidence.get('monte_carlo_forward', {}).get('p95_max_drawdown_inr', 0.0)}`
- **Probability of 5 Consecutive Losses**: `{evidence.get('probabilities', {}).get('prob_5_consecutive_losses_pct', 0.0)}%`
- **Estimated Risk of Ruin**: `{evidence.get('probabilities', {}).get('prob_ruin_pct', 0.0)}%`

---

## 3. Backtest Drift Summary

- **Baseline Strategy**: `VWAP_EMA_MOMENTUM_V1` (Frozen)
- **Classification**: **{comparison.get('classification', 'UNKNOWN')}**

---

> **Audit Disclaimer**:  
> PAPER TRADING ONLY. No real-money trades were submitted to any broker.  
> Past performance during paper simulation does not guarantee future live trading results.
"""

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        return {
            "markdown_path": md_file,
            "json_path": json_file,
            "verdict": verdict["verdict"],
            "summary": report_dict,
        }

    @classmethod
    def _persist_report_record(cls, session_id: str, date_str: str, md_path: str, json_path: str, verdict: str, report_data: Dict[str, Any]):
        db = SessionLocal()
        try:
            r = Phase9DailyReport(
                session_id=session_id,
                trading_date=date_str,
                markdown_path=md_path,
                json_path=json_path,
                verdict=verdict,
                metrics_json=json.dumps(report_data),
            )
            db.add(r)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
