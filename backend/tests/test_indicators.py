import pytest
import pandas as pd
import numpy as np
from app.technical.indicators import TechnicalAnalysis

@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range(start="2026-01-01 09:15", periods=50, freq="5min")
    prices = [100.0 + i * 0.5 + np.sin(i) * 2 for i in range(50)]
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [p - 0.2 for p in prices],
        "high": [p + 0.8 for p in prices],
        "low": [p - 0.7 for p in prices],
        "close": prices,
        "volume": [1000 + i * 50 for i in range(50)]
    })
    return df

def test_sma_calculation(sample_ohlcv):
    sma20 = TechnicalAnalysis.calculate_sma(sample_ohlcv["close"], 20)
    assert len(sma20) == 50
    assert not np.isnan(sma20.iloc[-1])
    assert sma20.iloc[-1] > 0

def test_ema_calculation(sample_ohlcv):
    ema9 = TechnicalAnalysis.calculate_ema(sample_ohlcv["close"], 9)
    assert len(ema9) == 50
    assert not np.isnan(ema9.iloc[-1])
    assert ema9.iloc[-1] > 0

def test_rsi_calculation(sample_ohlcv):
    rsi = TechnicalAnalysis.calculate_rsi(sample_ohlcv["close"], 14)
    assert len(rsi) == 50
    assert 0 <= rsi.iloc[-1] <= 100

def test_macd_calculation(sample_ohlcv):
    macd, signal, hist = TechnicalAnalysis.calculate_macd(sample_ohlcv["close"])
    assert len(macd) == 50
    assert len(signal) == 50
    assert len(hist) == 50
    assert not np.isnan(macd.iloc[-1])

def test_vwap_calculation(sample_ohlcv):
    vwap = TechnicalAnalysis.calculate_vwap(sample_ohlcv)
    assert len(vwap) == 50
    assert vwap.iloc[-1] > 0
    # VWAP should be roughly within price range
    assert sample_ohlcv["low"].min() <= vwap.iloc[-1] <= sample_ohlcv["high"].max()

def test_atr_calculation(sample_ohlcv):
    atr = TechnicalAnalysis.calculate_atr(sample_ohlcv, 14)
    assert len(atr) == 50
    assert atr.iloc[-1] > 0

def test_bollinger_bands(sample_ohlcv):
    upper, middle, lower = TechnicalAnalysis.calculate_bollinger_bands(sample_ohlcv["close"], 20, 2.0)
    assert len(upper) == 50
    assert upper.iloc[-1] >= middle.iloc[-1] >= lower.iloc[-1]

def test_rvol_calculation(sample_ohlcv):
    rvol = TechnicalAnalysis.calculate_rvol(sample_ohlcv["volume"], 20)
    assert len(rvol) == 50
    assert rvol.iloc[-1] > 0
