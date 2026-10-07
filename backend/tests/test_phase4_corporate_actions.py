import pytest
import pandas as pd
from app.data.corporate_actions import CorporateActionAdjuster, CorporateAction

def test_corporate_action_split_adjustment():
    df = pd.DataFrame([
        {"timestamp": pd.to_datetime("2026-08-20 10:00:00"), "open": 2000.0, "high": 2020.0, "low": 1990.0, "close": 2010.0, "volume": 10000},
        {"timestamp": pd.to_datetime("2026-08-25 10:00:00"), "open": 205.0, "high": 210.0, "low": 200.0, "close": 208.0, "volume": 100000}
    ])
    # 1:10 Stock Split on 2026-08-24
    split_action = CorporateAction(symbol="TEST", ex_date="2026-08-24", action_type="SPLIT", ratio=10.0)
    df_adj = CorporateActionAdjuster.adjust_series(df, [split_action])

    # Past price (before ex-date) must be adjusted by /10
    assert df_adj.iloc[0]["close"] == 201.0
    # Past volume must be adjusted by *10
    assert df_adj.iloc[0]["volume"] == 100000.0
    # Current price (after ex-date) remains unchanged
    assert df_adj.iloc[1]["close"] == 208.0
