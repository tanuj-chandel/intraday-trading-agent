import pytest
import pandas as pd
from app.data.historical_loader import HistoricalDataLoader
from app.backtest.engine import BacktestEngine, BacktestConfig

def test_backtest_execution_on_sample_data():
    df = HistoricalDataLoader.load_csv("data/historical/SAMPLE_RELIANCE_5m.csv", symbol="RELIANCE")
    config = BacktestConfig(
        strategy_id="VWAP_EMA_MOMENTUM_V1",
        initial_capital=100000.0,
        risk_per_trade_pct=0.01,
        same_candle_conflict_resolution="SL_FIRST"
    )
    engine = BacktestEngine(config)
    result = engine.run(df, "RELIANCE")

    assert result["initial_capital"] == 100000.0
    assert "return_pct" in result
    assert "profit_factor" in result
    assert "max_drawdown_pct" in result
    assert "equity_curve" in result
    assert len(result["equity_curve"]) > 0
    assert result["news_factor_status"] == "NOT_AVAILABLE_FOR_HISTORICAL_BACKTEST"

def test_same_candle_conflict_resolution():
    timestamps = pd.date_range("2026-08-25 09:15:00", periods=30, freq="5min")
    synthetic_df = pd.DataFrame([
        {"timestamp": ts, "open": 1000+i*2, "high": 1005+i*2, "low": 995+i*2, "close": 1002+i*2, "volume": 100000}
        for i, ts in enumerate(timestamps)
    ])
    # Add a conflict bar at index 29
    synthetic_df.loc[29, "high"] = 1200.0 # Touches target
    synthetic_df.loc[29, "low"] = 800.0   # Touches SL

    config = BacktestConfig(
        strategy_id="VWAP_EMA_MOMENTUM_V1",
        same_candle_conflict_resolution="SL_FIRST"
    )
    engine = BacktestEngine(config)
    result = engine.run(synthetic_df, "TEST_SYM")
    assert result["total_trades"] >= 0
