import pytest
from app.data.universe import EXPANDED_INDIAN_UNIVERSE, IndianStockMetadata
from app.data.liquidity_filter import LiquidityFilter

def test_expanded_universe_size():
    assert len(EXPANDED_INDIAN_UNIVERSE) >= 25
    symbols = [s.symbol for s in EXPANDED_INDIAN_UNIVERSE]
    assert "RELIANCE" in symbols
    assert "HDFCBANK" in symbols
    assert "ZOMATO" in symbols
    assert "HAL" in symbols

def test_liquidity_filter_criteria():
    filter_engine = LiquidityFilter(
        min_avg_daily_volume=100000,
        min_daily_turnover_inr=50000000.0,
        min_price=50.0,
        max_price=10000.0
    )

    # Valid liquid stock
    stock_valid = IndianStockMetadata(
        symbol="VALID_STOCK", nse_symbol="VALID_STOCK", company_name="Valid Ltd.",
        sector="IT", index_name="NIFTY 50", avg_daily_volume=2000000.0,
        avg_daily_turnover_cr=100.0, is_active=True
    )
    res_valid = filter_engine.evaluate_stock(stock_valid, current_price=1500.0)
    assert res_valid["passed"] is True

    # Low volume stock
    stock_low_vol = IndianStockMetadata(
        symbol="ILLIQUID", nse_symbol="ILLIQUID", company_name="Illiquid Ltd.",
        sector="IT", index_name="NIFTY 500", avg_daily_volume=10000.0,  # Below 100k
        avg_daily_turnover_cr=2.0, is_active=True
    )
    res_low_vol = filter_engine.evaluate_stock(stock_low_vol, current_price=500.0)
    assert res_low_vol["passed"] is False
    assert any("volume" in r for r in res_low_vol["reasons"])

    # Penny stock under ₹50
    res_penny = filter_engine.evaluate_stock(stock_valid, current_price=15.0)
    assert res_penny["passed"] is False
    assert any("penny stock" in r for r in res_penny["reasons"])
