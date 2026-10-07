"""
Unit Tests for Phase 6: Metrics, Reports, Go-Live Criteria, Parquet Storage & Walk-Forward.
"""

import pytest
import datetime
from unittest.mock import MagicMock, patch
import pandas as pd
from app.core.database import SessionLocal, Base, engine
from app.models.models import Trade, TradeSignal, SystemLog
from app.analytics.performance import PerformanceEngine
from app.notifications.telegram_bot import TelegramNotifier
from app.data.parquet_storage import ParquetStorageEngine
from app.live.data_types import LiveCandle, LiveTick
from app.backtest.walk_forward import WalkForwardAnalyzer
from app.api.v1.endpoints.system import get_go_live_checklist, toggle_live_trading
from app.core.config import settings

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    from app.core.database import ensure_sqlite_columns
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_columns()
    yield

def test_performance_metrics_engine_extended_metrics():
    """Verify average R, expectancy, slippage, streaks, and segmentations."""
    db = SessionLocal()
    try:
        now = datetime.datetime.now()
        t1 = Trade(
            symbol="RELIANCE",
            strategy="VWAP_EMA",
            direction="BUY",
            entry_price=1000.0,
            exit_price=1020.0,
            stop_loss=990.0,
            target_price=1030.0,
            quantity=10,
            gross_pnl=200.0,
            estimated_charges=15.0,
            net_pnl=185.0,
            holding_time_minutes=25.0,
            reason_for_entry="RSI Bullish + EMA crossover",
            reason_for_exit="TARGET_HIT",
            market_regime="TRENDING",
            score_at_entry=88.0,
            slippage_incurred=0.50,
            achieved_r=2.0,
            entry_time=now.replace(hour=9, minute=30),  # OPEN_30M
            exit_time=now.replace(hour=9, minute=55)
        )
        t2 = Trade(
            symbol="INFY",
            strategy="ORB",
            direction="SELL",
            entry_price=500.0,
            exit_price=510.0,
            stop_loss=505.0,
            target_price=490.0,
            quantity=20,
            gross_pnl=-200.0,
            estimated_charges=15.0,
            net_pnl=-215.0,
            holding_time_minutes=40.0,
            reason_for_entry="Breakdown below low",
            reason_for_exit="STOP_LOSS_HIT",
            market_regime="CHOPPY",
            score_at_entry=75.0,
            slippage_incurred=0.80,
            achieved_r=-2.0,
            entry_time=now.replace(hour=11, minute=0),  # MID_SESSION
            exit_time=now.replace(hour=11, minute=40)
        )
        db.add_all([t1, t2])
        db.commit()

        metrics = PerformanceEngine.calculate_metrics(db)
        assert metrics.total_trades >= 2
        assert metrics.average_r is not None
        assert metrics.expectancy_per_trade is not None
        assert metrics.longest_losing_streak >= 1
        assert metrics.average_slippage >= 0.0

        # Segmented breakdowns
        assert "VWAP_EMA" in metrics.performance_by_strategy or "ORB" in metrics.performance_by_strategy
        assert "OPEN_30M" in metrics.performance_by_time_of_day
        assert "MID_SESSION" in metrics.performance_by_time_of_day
        assert "RELIANCE" in metrics.performance_by_symbol
        assert "TRENDING" in metrics.performance_by_market_regime or "CHOPPY" in metrics.performance_by_market_regime
    finally:
        db.close()

def test_trade_reason_log_storage():
    """Verify indicators snapshot, news rationale, slippage, and achieved R persist into Trade."""
    db = SessionLocal()
    try:
        now = datetime.datetime.now()
        indicators = {"rsi": 63.5, "vwap": 1500.2, "ema_fast": 1502.0}
        news = {"headline": "Record Quarterly Earnings", "sentiment": "BULLISH", "score": 0.9}

        trade = Trade(
            symbol="TCS",
            strategy="VWAP_EMA_MOMENTUM_V1",
            direction="BUY",
            entry_price=3500.0,
            exit_price=3550.0,
            stop_loss=3480.0,
            target_price=3560.0,
            quantity=5,
            gross_pnl=250.0,
            estimated_charges=22.5,
            net_pnl=227.5,
            holding_time_minutes=35.0,
            reason_for_entry="VWAP + Momentum breakout",
            reason_for_exit="TRAILING_STOP_HIT",
            market_regime="TRENDING",
            score_at_entry=91.0,
            indicators_snapshot=indicators,
            news_rationale=news,
            slippage_incurred=1.20,
            achieved_r=2.5,
            entry_time=now,
            exit_time=now + datetime.timedelta(minutes=35)
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        saved = db.query(Trade).filter(Trade.id == trade.id).first()
        assert saved is not None
        assert saved.indicators_snapshot["rsi"] == 63.5
        assert saved.news_rationale["sentiment"] == "BULLISH"
        assert saved.reason_for_exit == "TRAILING_STOP_HIT"
        assert saved.achieved_r == 2.5
        assert saved.slippage_incurred == 1.20
    finally:
        db.close()

@pytest.mark.asyncio
async def test_end_of_day_telegram_report(monkeypatch):
    """Verify 15:45 IST EOD Telegram report compiles trades, net P&L, rejections, and warnings."""
    monkeypatch.setattr(settings, "TELEGRAM_ALLOWED_CHAT_ID", "987654321")
    bot = TelegramNotifier()
    bot.enabled = True
    bot._authorized_chat_id = "987654321"

    db = SessionLocal()
    try:
        now = datetime.datetime.now()
        # Seed rejected signal
        rej_sig = TradeSignal(
            symbol="SBIN",
            direction="BUY",
            entry_price=600.0,
            stop_loss=595.0,
            target_price=612.0,
            quantity=100,
            risk_amount=500.0,
            reward_amount=1200.0,
            risk_reward_ratio=2.4,
            strategy_name="VWAP_EMA",
            strategy_score=68.0,
            status="REJECTED",
            reject_reason="Signal score 68.0 below MIN_SIGNAL_SCORE (70.0)",
            explanation="Low volume momentum",
            timestamp=now
        )
        # Seed warning log
        log_warn = SystemLog(
            level="WARNING",
            module="WATCHDOG",
            message="Data feed latency elevated (12s)",
            timestamp=now
        )
        db.add_all([rej_sig, log_warn])
        db.commit()

        with patch.object(bot, "send_message", return_value=True) as mock_send:
            res = await bot.send_end_of_day_report(target_chat_id="987654321")
            assert res["success"] is True
            assert res["rejected_count"] >= 1
            assert res["warnings_count"] >= 1
            assert "END-OF-DAY TRADING REPORT" in res["report_text"]
            assert "Signal score 68.0" in res["report_text"]
            mock_send.assert_called_once()

            # Test command handler
            res_cmd = await bot.handle_command("/eod_report", chat_id="987654321")
            assert res_cmd == "EOD_REPORT_SENT"
    finally:
        db.close()

def test_parquet_storage_roundtrip(tmp_path):
    """Verify ticks and candles persist to Parquet and reload identically."""
    engine = ParquetStorageEngine(base_dir=tmp_path)
    now = datetime.datetime.now()

    # 1. Candles round-trip
    c1 = LiveCandle(
        symbol="TATASTEEL",
        timeframe="5m",
        timestamp=now.replace(second=0, microsecond=0),
        open=140.0,
        high=142.0,
        low=139.5,
        close=141.5,
        volume=12000,
        is_closed=True
    )
    c2 = LiveCandle(
        symbol="TATASTEEL",
        timeframe="5m",
        timestamp=(now + datetime.timedelta(minutes=5)).replace(second=0, microsecond=0),
        open=141.5,
        high=143.0,
        low=141.0,
        close=142.8,
        volume=15000,
        is_closed=True
    )
    engine.save_candles([c1, c2], timeframe="5m")

    loaded_df = engine.load_candles("TATASTEEL", timeframe="5m")
    assert not loaded_df.empty
    assert len(loaded_df) == 2
    assert "close" in loaded_df.columns
    assert float(loaded_df.iloc[0]["open"]) == 140.0
    assert float(loaded_df.iloc[1]["close"]) == 142.8

    # 2. Ticks round-trip
    t1 = LiveTick(
        symbol="TATASTEEL",
        ltp=141.5,
        open=140.0,
        high=142.0,
        low=139.5,
        close=141.5,
        volume=500,
        bid=141.45,
        ask=141.55,
        spread=0.10,
        timestamp=now
    )
    engine.save_ticks([t1])
    date_str = now.strftime("%Y-%m-%d")
    ticks_df = engine.load_ticks("TATASTEEL", date_str)
    assert not ticks_df.empty
    assert len(ticks_df) == 1
    assert float(ticks_df.iloc[0]["ltp"]) == 141.5

def test_walk_forward_and_out_of_sample_split():
    """Verify Walk-Forward and Out-of-Sample split with dynamic slippage model."""
    dates = pd.date_range("2026-01-01", periods=60, freq="5min")
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [100.0 + i * 0.2 for i in range(60)],
        "high": [101.0 + i * 0.2 for i in range(60)],
        "low": [99.5 + i * 0.2 for i in range(60)],
        "close": [100.5 + i * 0.2 for i in range(60)],
        "volume": [10000 + i * 50 for i in range(60)]
    })

    # Out-of-Sample Split
    res_oos = WalkForwardAnalyzer.out_of_sample_split(df, symbol="RELIANCE", train_pct=0.70)
    assert "in_sample" in res_oos
    assert "out_of_sample" in res_oos
    assert "DYNAMIC_TIER_" in res_oos["slippage_model"]
    assert res_oos["in_sample"]["candles"] == 42
    assert res_oos["out_of_sample"]["candles"] == 18

    # Rolling Walk-Forward
    res_roll = WalkForwardAnalyzer.rolling_walk_forward(df, symbol="RELIANCE", windows=3)
    assert res_roll["total_windows"] == 3
    assert len(res_roll["windows"]) == 3
    assert "DYNAMIC_TIER_" in res_roll["slippage_model"]

def test_go_live_checklist_refusal_when_insufficient_trades():
    """Verify Go-Live checklist fails and prevents toggling LIVE_TRADING_ENABLED when < 150 trades."""
    db = SessionLocal()
    try:
        from fastapi import HTTPException
        checklist = get_go_live_checklist(db)
        
        # Check item requirements
        sample_item = next(i for i in checklist["items"] if i["id"] == "MIN_PAPER_TRADES")
        assert sample_item["target"] == "≥ 150"

        # If trades < 150, checklist must NOT be ready
        if checklist["total_trades"] < 150:
            assert checklist["all_passed"] is False
            assert checklist["overall_status"] == "NOT_READY"

            # Attempting to turn on LIVE_TRADING_ENABLED must raise HTTPException 400
            with pytest.raises(HTTPException) as exc_info:
                toggle_live_trading({"enable": True}, db)
            assert exc_info.value.status_code == 400
            assert "Go-live checklist failed" in exc_info.value.detail
    finally:
        db.close()
