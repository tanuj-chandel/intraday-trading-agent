"""
Phase 7 Qualification Verdict Engine
Generates a formal Phase 7 qualification verdict based on live paper trading results
and reality-gap analysis. Uses minimum sample rules and scientific thresholds.
"""
import datetime
from typing import Dict, Any, Optional
from app.live.reality_gap import RealityGapAnalyzer, RealityGapVerdict


class Phase7QualificationEngine:
    """
    Formal Phase 7 qualification engine.
    Produces a standardized verdict after evaluating:
    - Minimum sample requirement (≥30 for initial, ≥100 for validated)
    - Reality-Gap analysis vs Phase 6 backtest metrics
    - Data quality provenance
    - Kill switch events during session

    Verdicts (in order of severity):
        INSUFFICIENT_LIVE_DATA   → < 30 paper trades
        CONTINUE_PAPER_TRADING   → 30–99 trades, consistent with backtest
        REALITY_GAP_DETECTED     → threshold breach detected
        STRATEGY_DEGRADATION_DETECTED → multiple breaches or streak of losses
        PAPER_VALIDATION_PASSED  → ≥ 100 trades, no gap detected, PF ≥ 1.0
    """

    MIN_INITIAL_TRADES = 30
    MIN_VALIDATED_TRADES = 100

    def __init__(self, backtest_metrics: Optional[Dict[str, Any]] = None):
        """
        Args:
            backtest_metrics: Phase 6 reference metrics.
                Expected keys: win_rate (%), expectancy (₹), profit_factor (ratio)
        """
        self._backtest_metrics = backtest_metrics or {
            "win_rate": 55.0,
            "expectancy": 150.0,
            "profit_factor": 1.5
        }
        self._analyzer = RealityGapAnalyzer()

    def evaluate(
        self,
        paper_trades: list,
        kill_switch_activated: bool = False,
        kill_switch_level: int = 0,
        data_quality_provenance: str = "MOCK"
    ) -> Dict[str, Any]:
        """
        Run full qualification evaluation.

        Returns dict with:
            verdict, verdict_explanation, is_qualified,
            phase7_report_ready, sample_adequacy, reality_gap
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        total_trades = len(paper_trades)

        # Reality-gap analysis
        gap_report = self._analyzer.analyze(
            backtest_metrics=self._backtest_metrics,
            paper_trades=paper_trades
        )

        # Sample adequacy
        is_initial = total_trades >= self.MIN_INITIAL_TRADES
        is_validated = total_trades >= self.MIN_VALIDATED_TRADES

        sample_adequacy = {
            "total_paper_trades": total_trades,
            "initial_threshold": self.MIN_INITIAL_TRADES,
            "validated_threshold": self.MIN_VALIDATED_TRADES,
            "has_initial_sample": is_initial,
            "has_validated_sample": is_validated,
            "trades_needed_for_initial": max(0, self.MIN_INITIAL_TRADES - total_trades),
            "trades_needed_for_validated": max(0, self.MIN_VALIDATED_TRADES - total_trades)
        }

        # Safety events
        safety_events = []
        if kill_switch_activated:
            safety_events.append(f"Kill switch Level {kill_switch_level} was activated during session")
        if data_quality_provenance not in ("LIVE",):
            safety_events.append(f"Data provenance was {data_quality_provenance} (not LIVE)")

        # Final verdict
        verdict = gap_report.verdict
        is_qualified = (
            verdict == RealityGapVerdict.PAPER_VALIDATION_PASSED
            and not kill_switch_activated
            and data_quality_provenance == "LIVE"
        )

        return {
            "evaluated_at": now,
            "verdict": verdict,
            "verdict_explanation": gap_report.verdict_explanation,
            "is_qualified": is_qualified,
            "phase7_report_ready": is_initial,
            "trading_mode": "PAPER_TRADING_ONLY",
            "real_orders_placed": 0,
            "sample_adequacy": sample_adequacy,
            "reality_gap": {
                "live_win_rate": gap_report.live_win_rate,
                "backtest_win_rate": gap_report.backtest_win_rate,
                "win_rate_delta": gap_report.win_rate_delta,
                "live_profit_factor": gap_report.live_profit_factor,
                "backtest_profit_factor": gap_report.backtest_profit_factor,
                "consecutive_losses": gap_report.consecutive_losses,
                "threshold_breaches": gap_report.threshold_breaches,
                "is_sufficient_data": gap_report.is_sufficient_data,
                "is_validated": gap_report.is_validated
            },
            "safety_events": safety_events,
            "data_provenance": data_quality_provenance,
            "disclaimer": (
                "PAPER TRADING ONLY. All results are simulation. "
                "No real-money orders were placed. "
                "Past paper results do not guarantee future real-money performance."
            )
        }
