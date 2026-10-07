import pytest
import os
import pandas as pd
from app.data.historical_loader import HistoricalDataLoader, HistoricalDataValidationError

def test_load_valid_sample_dataset():
    fpath = "data/historical/SAMPLE_RELIANCE_5m.csv"
    assert os.path.exists(fpath)
    df = HistoricalDataLoader.load_csv(fpath, symbol="RELIANCE")
    assert len(df) >= 50
    assert "open" in df.columns
    assert "close" in df.columns
    assert "volume" in df.columns

def test_ohlc_integrity_validation(tmp_path):
    # Invalid High (High < Open)
    bad_csv = tmp_path / "bad_ohlc.csv"
    bad_csv.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-08-25 09:15:00,100,90,80,95,1000\n" # High 90 < Open 100
    )
    with pytest.raises(HistoricalDataValidationError):
        HistoricalDataLoader.load_csv(str(bad_csv))

def test_negative_volume_validation(tmp_path):
    bad_vol_csv = tmp_path / "bad_vol.csv"
    bad_vol_csv.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-08-25 09:15:00,100,110,90,105,-500\n"
    )
    with pytest.raises(HistoricalDataValidationError):
        HistoricalDataLoader.load_csv(str(bad_vol_csv))
