import pytest
from app.data.global_market import GlobalMarketAnalyzer
from app.data.gift_nifty_provider import GiftNiftyProvider

def test_global_market_analysis():
    global_res = GlobalMarketAnalyzer.get_global_market_summary()
    assert -100.0 <= global_res["global_market_score"] <= 100.0
    assert global_res["sentiment"] in ["BULLISH", "BEARISH", "NEUTRAL_MIXED"]
    assert "us_markets" in global_res["components"]
    assert "commodities_crude" in global_res["components"]
    assert len(global_res["indices"]) >= 5

def test_gift_nifty_gap_calculation():
    # Test gap calculation with spot nifty @ 24800
    gap_res = GiftNiftyProvider.get_gap_analysis(spot_nifty_close=24800.0)
    assert "gap_points" in gap_res
    assert "gap_pct" in gap_res
    assert gap_res["gap_direction"] in ["GAP_UP", "GAP_DOWN", "FLAT"]
    assert gap_res["data_status"] in ["LIVE", "MOCK", "DELAYED"]

def test_gift_nifty_manual_override():
    GiftNiftyProvider.set_manual_price(25000.0)
    gap_res = GiftNiftyProvider.get_gap_analysis(spot_nifty_close=24800.0)
    assert gap_res["gift_nifty_price"] == 25000.0
    assert gap_res["gap_points"] == 200.0
    assert gap_res["gap_direction"] == "GAP_UP"
    assert gap_res["source"] == "OPERATOR_MANUAL_INPUT"
