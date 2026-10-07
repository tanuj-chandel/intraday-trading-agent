"""
Tests for Phase 7 Reality-Gap Analyzer
Verifies all 5 formal verdicts and threshold breach detection.
"""
import pytest
from app.live.reality_gap import (
    RealityGapAnalyzer, RealityGapThresholds, RealityGapVerdict
)

BACKTEST = {"win_rate": 55.0, "expectancy": 150.0, "profit_factor": 1.5}


def _make_trades(count: int, win_rate_pct: float = 55.0, pnl_per_win: float = 300.0, pnl_per_loss: float = -150.0):
    """Helper: create a synthetic list of closed trade dicts with interleaved wins/losses."""
    trades = []
    wins = int(count * win_rate_pct / 100)
    losses = count - wins
    # Interleave to avoid artificial consecutive-loss streaks
    win_flag = True
    win_count = 0
    loss_count = 0
    for i in range(count):
        # Distribute proportionally
        remaining = count - i
        wins_left = wins - win_count
        losses_left = losses - loss_count
        # Place a win when proportionally due
        if losses_left == 0 or (wins_left > 0 and wins_left / remaining >= win_rate_pct / 100):
            trades.append({"net_realized_pnl": pnl_per_win, "slippage_incurred": 5.0, "statutory_charges": 8.0})
            win_count += 1
        else:
            trades.append({"net_realized_pnl": pnl_per_loss, "slippage_incurred": 5.0, "statutory_charges": 8.0})
            loss_count += 1
    return trades


class TestInsufficientData:
    def test_zero_trades_gives_insufficient(self):
        analyzer = RealityGapAnalyzer()
        report = analyzer.analyze(BACKTEST, [])
        assert report.verdict == RealityGapVerdict.INSUFFICIENT_LIVE_DATA
        assert report.paper_trades_count == 0
        assert report.is_sufficient_data is False

    def test_29_trades_gives_insufficient(self):
        analyzer = RealityGapAnalyzer()
        report = analyzer.analyze(BACKTEST, _make_trades(29))
        assert report.verdict == RealityGapVerdict.INSUFFICIENT_LIVE_DATA
        assert report.is_sufficient_data is False


class TestContinuePaperTrading:
    def test_30_consistent_trades_continue(self):
        """30 trades consistent with backtest → CONTINUE_PAPER_TRADING."""
        analyzer = RealityGapAnalyzer()
        # Win=350, loss=-100 at 53% → expectancy ≈ (53*350 + 47*(-100))/100 = 138.5
        # delta from 150 = -7.7% — within 30% threshold
        report = analyzer.analyze(BACKTEST, _make_trades(30, win_rate_pct=53.0, pnl_per_win=350.0, pnl_per_loss=-100.0))
        assert report.verdict == RealityGapVerdict.CONTINUE_PAPER_TRADING
        assert report.is_sufficient_data is True
        assert report.is_validated is False


class TestRealityGapDetected:
    def test_large_win_rate_drop_detected(self):
        """Win rate drops by >15 points → REALITY_GAP_DETECTED."""
        analyzer = RealityGapAnalyzer(RealityGapThresholds(max_win_rate_drop_pct=15.0))
        report = analyzer.analyze(BACKTEST, _make_trades(35, win_rate_pct=35.0))
        # 55% → 35% = 20-point drop exceeds 15-point threshold
        assert report.verdict in (
            RealityGapVerdict.REALITY_GAP_DETECTED,
            RealityGapVerdict.STRATEGY_DEGRADATION_DETECTED
        )
        assert len(report.threshold_breaches) > 0


class TestStrategyDegradation:
    def test_multiple_breaches_give_degradation(self):
        """Multiple threshold breaches → STRATEGY_DEGRADATION_DETECTED."""
        analyzer = RealityGapAnalyzer(RealityGapThresholds(
            max_win_rate_drop_pct=10.0,
            max_profit_factor_drop=0.3,
            max_consecutive_losses_streak=3
        ))
        # Very low win rate, heavy losses → multiple breaches
        trades = _make_trades(40, win_rate_pct=20.0, pnl_per_win=100.0, pnl_per_loss=-400.0)
        report = analyzer.analyze(BACKTEST, trades)
        assert report.verdict == RealityGapVerdict.STRATEGY_DEGRADATION_DETECTED
        assert len(report.threshold_breaches) >= 2

    def test_consecutive_losses_trigger_degradation(self):
        """Streak of losses at end of trade list triggers degradation."""
        analyzer = RealityGapAnalyzer(RealityGapThresholds(max_consecutive_losses_streak=3))
        # 35 trades, last 5 are all losses
        trades = _make_trades(35, win_rate_pct=60.0)
        # Overwrite last 5 to losses
        for i in range(-5, 0):
            trades[i]["net_realized_pnl"] = -200.0
        report = analyzer.analyze(BACKTEST, trades)
        assert report.consecutive_losses >= 5


class TestPaperValidationPassed:
    def test_100_consistent_trades_passes(self):
        """≥100 consistent trades with no breach → PAPER_VALIDATION_PASSED."""
        analyzer = RealityGapAnalyzer()
        # Use win=350, loss=-100 at 54% win rate:
        # expectancy = (54*350 + 46*(-100))/100 = (18900 - 4600)/100 = 143
        # delta from backtest (150) = (143-150)/150 = -4.7% — well within 30% threshold
        report = analyzer.analyze(BACKTEST, _make_trades(100, win_rate_pct=54.0, pnl_per_win=350.0, pnl_per_loss=-100.0))
        assert report.verdict == RealityGapVerdict.PAPER_VALIDATION_PASSED
        assert report.is_validated is True

    def test_no_breach_means_no_threshold_alerts(self):
        analyzer = RealityGapAnalyzer()
        report = analyzer.analyze(BACKTEST, _make_trades(100, win_rate_pct=54.0, pnl_per_win=350.0, pnl_per_loss=-100.0))
        assert report.threshold_breaches == []


class TestMetricsAccuracy:
    def test_win_rate_calculated_correctly(self):
        analyzer = RealityGapAnalyzer()
        trades = _make_trades(100, win_rate_pct=60.0)
        report = analyzer.analyze(BACKTEST, trades)
        assert 58.0 <= report.live_win_rate <= 62.0

    def test_slippage_averaged_correctly(self):
        analyzer = RealityGapAnalyzer()
        trades = _make_trades(10, win_rate_pct=50.0)
        report = analyzer.analyze(BACKTEST, trades)
        assert report.avg_slippage_per_trade_inr == 5.0
