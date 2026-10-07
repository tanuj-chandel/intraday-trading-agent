import pytest
from app.backtest.concentration import ConcentrationRiskAnalyzer

def test_stock_concentration_balanced():
    stocks = [
        {"symbol": "RELIANCE", "net_pnl": 500.0},
        {"symbol": "HDFCBANK", "net_pnl": 450.0},
        {"symbol": "INFY", "net_pnl": 400.0},
        {"symbol": "TCS", "net_pnl": 350.0},
        {"symbol": "ICICIBANK", "net_pnl": 300.0}
    ]
    res = ConcentrationRiskAnalyzer.analyze_stock_concentration(stocks)
    assert res["stock_concentration_flag"] == "BALANCED_DIVERSIFICATION"
    assert res["top_1_stock_contribution_pct"] < 50.0

def test_stock_concentration_high_risk():
    # 1 stock dominates 90% of profits
    stocks = [
        {"symbol": "RELIANCE", "net_pnl": 9000.0},
        {"symbol": "HDFCBANK", "net_pnl": 50.0},
        {"symbol": "INFY", "net_pnl": 50.0}
    ]
    res = ConcentrationRiskAnalyzer.analyze_stock_concentration(stocks)
    assert res["stock_concentration_flag"] == "HIGH_STOCK_CONCENTRATION_RISK"
    assert res["top_1_stock_contribution_pct"] > 50.0

def test_trade_concentration_risk():
    # 20 trades, one giant trade
    trades = [{"trade_id": i, "net_pnl": 10.0} for i in range(19)]
    trades.append({"trade_id": 20, "net_pnl": 5000.0})

    res = ConcentrationRiskAnalyzer.analyze_trade_concentration(trades)
    assert res["trade_concentration_flag"] == "PROFIT_CONCENTRATION_RISK"
    assert res["top_5pct_trade_contribution_pct"] > 60.0
