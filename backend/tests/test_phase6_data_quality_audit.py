import pytest
import pandas as pd
from app.backtest.data_quality_audit import HistoricalDataQualityAuditEngine
from app.data.historical_loader import HistoricalDataLoader

def test_data_quality_audit_clean_dataset():
    df = HistoricalDataLoader.load_csv("data/historical/SAMPLE_RELIANCE_5m.csv", symbol="RELIANCE")
    audit = HistoricalDataQualityAuditEngine.audit_dataset(df, symbol="RELIANCE")

    assert audit["data_quality_score"] >= 80.0
    assert audit["status"] == "PASSED"
    assert audit["invalid_ohlc_count"] == 0
    assert audit["corporate_action_status"] == "CORPORATE_ACTION_ADJUSTED"
    assert "unique_trading_days" in audit

def test_data_quality_audit_corrupted_dataset():
    # Corrupt High < Low
    corrupt_data = {
        "timestamp": ["2026-08-25 09:15:00", "2026-08-25 09:20:00"],
        "open": [2900.0, 2910.0],
        "high": [2850.0, 2920.0], # High < Open invalid!
        "low": [2890.0, 2900.0],
        "close": [2895.0, 2915.0],
        "volume": [1000, 1500]
    }
    df_corrupt = pd.DataFrame(corrupt_data)
    audit = HistoricalDataQualityAuditEngine.audit_dataset(df_corrupt, symbol="CORRUPT")

    assert audit["invalid_ohlc_count"] > 0
    assert audit["status"] == "FAILED_QUALITY_GATE"
    assert len(audit["audit_errors"]) > 0
