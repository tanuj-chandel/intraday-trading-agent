"""
Reality-Gap Analyzer — Phase 7
Compares Phase 6 backtest metrics against live paper trading results.
Emits a formal verdict with threshold-based degradation detection.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


# Minimum number of paper trades before issuing a meaningful verdict
MIN_TRADES_FOR_VERDICT = 30
MIN_TRADES_FOR_VALIDATED = 100


class RealityGapVerdict:
    """Formal verdict labels for Phase 7 paper validation."""
    INSUFFICIENT_LIVE_DATA = "INSUFFICIENT_LIVE_DATA"
    CONTINUE_PAPER_TRADING = "CONTINUE_PAPER_TRADING"
    REALITY_GAP_DETECTED = "REALITY_GAP_DETECTED"
    STRATEGY_DEGRADATION_DETECTED = "STRATEGY_DEGRADATION_DETECTED"
    PAPER_VALIDATION_PASSED = "PAPER_VALIDATION_PASSED"


@dataclass
class RealityGapThresholds:
    """
    Configurable thresholds that define acceptable degradation from backtest to live paper.
    All values represent maximum acceptable negative deviation.
    """
    max_win_rate_drop_pct: float = 15.0          # e.g. 55% backtest → 40% live = 15-point drop (warning)
    max_expectancy_drop_pct: float = 30.0         # Max 30% drop in per-trade expectancy
    max_profit_factor_drop: float = 0.5           # e.g. PF 1.8 backtest → 1.3 live = gap detected
    max_consecutive_losses_streak: int = 5        # Alert if live streak exceeds this
    min_required_trades: int = MIN_TRADES_FOR_VERDICT
    validated_trades: int = MIN_TRADES_FOR_VALIDATED


@dataclass
class RealityGapReport:
    verdict: str
    paper_trades_count: int
    backtest_win_rate: float
    live_win_rate: float
    win_rate_delta: float
    backtest_expectancy: float
    live_expectancy: float
    expectancy_delta_pct: float
    backtest_profit_factor: float
    live_profit_factor: float
    profit_factor_delta: float
    avg_slippage_per_trade_inr: float
    total_statutory_charges_inr: float
    consecutive_losses: int
    threshold_breaches: List[str] = field(default_factory=list)
    verdict_explanation: str = ""
    is_sufficient_data: bool = False
    is_validated: bool = False


class RealityGapAnalyzer:
    """
    Compares Phase 6 backtest metrics against live paper trading execution results.
    Generates a formal verdict using configurable degradation thresholds.

    Safety: paper trading only — does not gate real-money orders.
    """

    def __init__(self, thresholds: Optional[RealityGapThresholds] = None):
        self.thresholds = thresholds or RealityGapThresholds()

    def analyze(
        self,
        backtest_metrics: Dict[str, Any],
        paper_trades: List[Dict[str, Any]]
    ) -> RealityGapReport:
        """
        Core analysis method.

        Args:
            backtest_metrics: Phase 6 backtest output dict with keys:
                win_rate, expectancy, profit_factor
            paper_trades: List of closed LivePaperPosition dicts (or equivalent)

        Returns:
            RealityGapReport with verdict and full metrics
        """
        total_trades = len(paper_trades)

        if total_trades == 0:
            return RealityGapReport(
                verdict=RealityGapVerdict.INSUFFICIENT_LIVE_DATA,
                paper_trades_count=0,
                backtest_win_rate=backtest_metrics.get("win_rate", 0.0),
                live_win_rate=0.0,
                win_rate_delta=0.0,
                backtest_expectancy=backtest_metrics.get("expectancy", 0.0),
                live_expectancy=0.0,
                expectancy_delta_pct=0.0,
                backtest_profit_factor=backtest_metrics.get("profit_factor", 0.0),
                live_profit_factor=0.0,
                profit_factor_delta=0.0,
                avg_slippage_per_trade_inr=0.0,
                total_statutory_charges_inr=0.0,
                consecutive_losses=0,
                verdict_explanation=f"No live paper trades recorded. Run at least {self.thresholds.min_required_trades} paper trades to generate a verdict.",
                is_sufficient_data=False,
                is_validated=False
            )

        # ── Live metrics ──────────────────────────────────────────────────────
        wins = [t for t in paper_trades if self._get_pnl(t) > 0]
        losses = [t for t in paper_trades if self._get_pnl(t) <= 0]

        live_win_rate = round((len(wins) / total_trades) * 100.0, 2)
        live_pnl = sum(self._get_pnl(t) for t in paper_trades)
        live_expectancy = round(live_pnl / total_trades, 2)
        total_slippage = sum(t.get("slippage_incurred", 0.0) for t in paper_trades)
        total_charges = sum(t.get("statutory_charges", 0.0) for t in paper_trades)
        avg_slippage = round(total_slippage / total_trades, 2)

        # Profit factor
        gross_profit = sum(self._get_pnl(t) for t in wins) if wins else 0.0
        gross_loss = abs(sum(self._get_pnl(t) for t in losses)) if losses else 0.001
        live_profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0.0

        # Consecutive losses (trailing streak from most recent)
        consecutive_losses = 0
        for t in reversed(paper_trades):
            if self._get_pnl(t) <= 0:
                consecutive_losses += 1
            else:
                break

        # ── Backtest reference ────────────────────────────────────────────────
        bt_win_rate = backtest_metrics.get("win_rate", 50.0)
        bt_expectancy = backtest_metrics.get("expectancy", 0.0)
        bt_profit_factor = backtest_metrics.get("profit_factor", 1.0)

        # ── Deltas ────────────────────────────────────────────────────────────
        win_rate_delta = round(live_win_rate - bt_win_rate, 2)
        expectancy_delta_pct = (
            round(((live_expectancy - bt_expectancy) / abs(bt_expectancy)) * 100.0, 2)
            if bt_expectancy != 0 else 0.0
        )
        pf_delta = round(live_profit_factor - bt_profit_factor, 2)

        # ── Threshold breach detection ─────────────────────────────────────────
        breaches: List[str] = []
        if win_rate_delta < -self.thresholds.max_win_rate_drop_pct:
            breaches.append(
                f"WIN_RATE_DROP: Backtest {bt_win_rate:.1f}% → Live {live_win_rate:.1f}% "
                f"(delta={win_rate_delta:+.1f}%, threshold=-{self.thresholds.max_win_rate_drop_pct}%)"
            )
        if expectancy_delta_pct < -self.thresholds.max_expectancy_drop_pct:
            breaches.append(
                f"EXPECTANCY_DROP: {expectancy_delta_pct:.1f}% decline "
                f"(threshold=-{self.thresholds.max_expectancy_drop_pct}%)"
            )
        if pf_delta < -self.thresholds.max_profit_factor_drop:
            breaches.append(
                f"PROFIT_FACTOR_DROP: Backtest {bt_profit_factor:.2f} → Live {live_profit_factor:.2f} "
                f"(delta={pf_delta:+.2f}, threshold=-{self.thresholds.max_profit_factor_drop})"
            )
        if consecutive_losses >= self.thresholds.max_consecutive_losses_streak:
            breaches.append(
                f"CONSECUTIVE_LOSSES: {consecutive_losses} consecutive losses "
                f"(threshold={self.thresholds.max_consecutive_losses_streak})"
            )

        # ── Verdict logic ──────────────────────────────────────────────────────
        is_sufficient = total_trades >= self.thresholds.min_required_trades
        is_validated = total_trades >= self.thresholds.validated_trades

        if not is_sufficient:
            verdict = RealityGapVerdict.INSUFFICIENT_LIVE_DATA
            verdict_exp = (
                f"Only {total_trades} live paper trades recorded "
                f"(minimum {self.thresholds.min_required_trades} required for initial verdict). "
                "Continue paper trading."
            )
        elif len(breaches) == 0 and live_profit_factor >= 1.0:
            if is_validated:
                verdict = RealityGapVerdict.PAPER_VALIDATION_PASSED
                verdict_exp = (
                    f"Strategy passed live paper validation across {total_trades} trades. "
                    f"Win rate {live_win_rate:.1f}%, PF {live_profit_factor:.2f}. "
                    "No significant degradation from backtest detected."
                )
            else:
                verdict = RealityGapVerdict.CONTINUE_PAPER_TRADING
                verdict_exp = (
                    f"Early results consistent with backtest across {total_trades} trades. "
                    f"Continue collecting data towards {self.thresholds.validated_trades}-trade target."
                )
        elif len(breaches) >= 2 or consecutive_losses >= self.thresholds.max_consecutive_losses_streak:
            verdict = RealityGapVerdict.STRATEGY_DEGRADATION_DETECTED
            verdict_exp = (
                f"Multiple performance degradation signals detected across {total_trades} trades. "
                f"Breaches: {len(breaches)}. Consecutive losses: {consecutive_losses}. "
                "Strategy is NOT performing as expected in live market conditions."
            )
        else:
            verdict = RealityGapVerdict.REALITY_GAP_DETECTED
            verdict_exp = (
                f"Reality gap detected across {total_trades} trades. "
                f"Live performance deviates from backtest expectations: {breaches[0] if breaches else 'see details'}. "
                "Investigate execution quality and market conditions."
            )

        return RealityGapReport(
            verdict=verdict,
            paper_trades_count=total_trades,
            backtest_win_rate=bt_win_rate,
            live_win_rate=live_win_rate,
            win_rate_delta=win_rate_delta,
            backtest_expectancy=bt_expectancy,
            live_expectancy=live_expectancy,
            expectancy_delta_pct=expectancy_delta_pct,
            backtest_profit_factor=bt_profit_factor,
            live_profit_factor=live_profit_factor,
            profit_factor_delta=pf_delta,
            avg_slippage_per_trade_inr=avg_slippage,
            total_statutory_charges_inr=round(total_charges, 2),
            consecutive_losses=consecutive_losses,
            threshold_breaches=breaches,
            verdict_explanation=verdict_exp,
            is_sufficient_data=is_sufficient,
            is_validated=is_validated
        )

    @staticmethod
    def _get_pnl(trade: Dict[str, Any]) -> float:
        """Extract net realized PnL from a trade dict (handles both key naming conventions)."""
        return float(
            trade.get("net_realized_pnl")
            or trade.get("net_pnl")
            or trade.get("pnl", 0.0)
        )
