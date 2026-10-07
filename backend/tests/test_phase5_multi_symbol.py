import pytest
from app.backtest.multi_symbol import MultiSymbolBacktestService

def test_multi_symbol_universe_backtest():
    res = MultiSymbolBacktestService.run_universe_backtest(universe_id="LIQUID_TOP_10")
    assert res["symbols_evaluated"] == 10
    assert "stock_leaderboard" in res
    assert len(res["stock_leaderboard"]) == 10
    assert "portfolio_summary" in res
    assert "survivorship_warning" in res
    assert len(res["best_performing_symbols"]) == 3
    assert len(res["worst_performing_symbols"]) == 3
