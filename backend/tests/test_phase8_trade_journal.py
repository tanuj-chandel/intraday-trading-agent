"""
Phase 8 — Trade Journal Tests
Tests for analytics, milestone tracking, regime/symbol breakdown,
consecutive streak counting, expectancy, and drawdown calculations.
"""
import datetime
import pytest
from app.live.trade_journal import Phase8TradeJournal, TradeJournalEntry


def make_journal():
    j = Phase8TradeJournal()
    # Override _persist to avoid DB calls in tests
    j._persist = lambda entry: None
    return j


def make_entry(symbol="RELIANCE", direction="BUY", net_pnl=200.0,
               regime="TRENDING_UP", mfe=300.0, mae=50.0):
    return TradeJournalEntry(
        trade_id=0,
        session_date="2026-08-31",
        symbol=symbol,
        direction=direction,
        net_pnl=net_pnl,
        gross_pnl=net_pnl + 30.0,
        total_charges=30.0,
        entry_slippage_inr=5.0,
        mfe_inr=mfe,
        mae_inr=mae,
        market_regime=regime,
        intended_entry_price=2980.0,
        simulated_fill_price=2982.0,
        quantity=10,
        stop_loss=2950.0,
        target_price=3050.0,
        exit_price=3010.0,
        exit_reason="TARGET_HIT",
        opened_at=datetime.datetime(2026, 8, 31, 10, 0, 0),
        closed_at=datetime.datetime(2026, 8, 31, 10, 45, 0),
        holding_minutes=45.0,
        risk_reward_ratio=2.0,
    )


def test_empty_journal_analytics():
    j = make_journal()
    analytics = j.compute_analytics()
    assert analytics["total_trades"] == 0
    assert analytics["status"] == "NO_TRADES_RECORDED"


def test_record_trade_increments_count():
    j = make_journal()
    j.record_trade(make_entry())
    analytics = j.compute_analytics()
    assert analytics["total_trades"] == 1


def test_win_rate_calculation():
    j = make_journal()
    for _ in range(3):
        j.record_trade(make_entry(net_pnl=200.0))
    for _ in range(2):
        j.record_trade(make_entry(net_pnl=-100.0))
    analytics = j.compute_analytics()
    assert analytics["winning_trades"] == 3
    assert analytics["losing_trades"] == 2
    assert analytics["win_rate_pct"] == 60.0


def test_expectancy_positive_for_profitable_strategy():
    j = make_journal()
    for _ in range(6):
        j.record_trade(make_entry(net_pnl=300.0))
    for _ in range(4):
        j.record_trade(make_entry(net_pnl=-150.0))
    analytics = j.compute_analytics()
    # 60% win rate, avg win=300, avg loss=150
    # expectancy = 0.6*300 - 0.4*150 = 180 - 60 = 120
    assert analytics["expectancy_inr"] > 0


def test_profit_factor_calculation():
    j = make_journal()
    for _ in range(3):
        j.record_trade(make_entry(net_pnl=200.0))   # gross wins = 600
    for _ in range(2):
        j.record_trade(make_entry(net_pnl=-100.0))  # gross losses = 200
    analytics = j.compute_analytics()
    assert abs(analytics["profit_factor"] - 3.0) < 0.01


def test_max_drawdown_calculation():
    j = make_journal()
    j.record_trade(make_entry(net_pnl=100.0))
    j.record_trade(make_entry(net_pnl=100.0))
    j.record_trade(make_entry(net_pnl=-300.0))  # drawdown of 300
    j.record_trade(make_entry(net_pnl=200.0))
    analytics = j.compute_analytics()
    assert analytics["max_drawdown_inr"] == 300.0


def test_consecutive_losses():
    j = make_journal()
    for _ in range(5):
        j.record_trade(make_entry(net_pnl=-100.0))
    j.record_trade(make_entry(net_pnl=200.0))
    j.record_trade(make_entry(net_pnl=-100.0))
    analytics = j.compute_analytics()
    assert analytics["max_consecutive_losses"] == 5


def test_consecutive_wins():
    j = make_journal()
    for _ in range(4):
        j.record_trade(make_entry(net_pnl=100.0))
    j.record_trade(make_entry(net_pnl=-50.0))
    analytics = j.compute_analytics()
    assert analytics["max_consecutive_wins"] == 4


def test_regime_breakdown():
    j = make_journal()
    j.record_trade(make_entry(regime="TRENDING_UP", net_pnl=200.0))
    j.record_trade(make_entry(regime="TRENDING_UP", net_pnl=-100.0))
    j.record_trade(make_entry(regime="SIDEWAYS", net_pnl=-150.0))
    analytics = j.compute_analytics()
    regime_perf = analytics["regime_performance"]
    assert "TRENDING_UP" in regime_perf
    assert regime_perf["TRENDING_UP"]["trades"] == 2
    assert "SIDEWAYS" in regime_perf


def test_symbol_concentration():
    j = make_journal()
    for _ in range(8):
        j.record_trade(make_entry(symbol="RELIANCE", net_pnl=100.0))
    for _ in range(2):
        j.record_trade(make_entry(symbol="TCS", net_pnl=50.0))
    analytics = j.compute_analytics()
    concentration = analytics["symbol_concentration"]
    assert concentration[0]["symbol"] == "RELIANCE"  # Top contributor
    assert concentration[0]["contribution_pct"] > 50.0  # Dominant


def test_milestone_insufficient():
    j = make_journal()
    for _ in range(15):
        j.record_trade(make_entry())
    analytics = j.compute_analytics()
    assert analytics["validation_milestone"]["stage"] == "INSUFFICIENT_LIVE_DATA"
    assert analytics["validation_milestone"]["next_milestone"] == 30


def test_milestone_early():
    j = make_journal()
    for _ in range(50):
        j.record_trade(make_entry())
    analytics = j.compute_analytics()
    assert analytics["validation_milestone"]["stage"] == "EARLY_PAPER_ASSESSMENT"


def test_avg_hold_time():
    j = make_journal()
    for mins in [30.0, 45.0, 60.0]:
        e = make_entry()
        e.holding_minutes = mins
        j.record_trade(e)
    analytics = j.compute_analytics()
    assert analytics["avg_hold_time_minutes"] == 45.0


def test_disclaimer_always_present():
    j = make_journal()
    j.record_trade(make_entry())
    analytics = j.compute_analytics()
    assert "PAPER TRADING" in analytics["disclaimer"]
    assert analytics["paper_trading_only"] is True


def test_get_entry_by_id():
    j = make_journal()
    tid = j.record_trade(make_entry())
    entry = j.get_entry(tid)
    assert entry is not None
    assert entry["symbol"] == "RELIANCE"
