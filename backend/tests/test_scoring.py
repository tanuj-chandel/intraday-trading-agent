import pytest
import pandas as pd
from app.scoring.scorer import StockScoringEngine
from app.schemas.schemas import NewsItem
import datetime

def test_stock_scoring_calculation():
    dates = pd.date_range(start="2026-01-01 09:15", periods=50, freq="5min")
    prices = [500.0 + i * 2.0 for i in range(50)]
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [p - 1.0 for p in prices],
        "high": [p + 2.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": [10000 + i * 500 for i in range(50)]
    })
    
    news = [
        NewsItem(
            headline="Record quarterly profit announced",
            source="Moneycontrol",
            published_at=datetime.datetime.now(),
            related_symbols=["TEST"],
            sentiment="BULLISH",
            sentiment_score=0.8,
            importance="HIGH"
        )
    ]
    
    score_res = StockScoringEngine.calculate_score(
        symbol="TEST",
        df=df,
        market_regime="TRENDING_UP",
        sector_score=80.0,
        news_items=news
    )
    
    assert 0.0 <= score_res["total_score"] <= 100.0
    assert score_res["direction"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert "trend_alignment" in score_res["components"]
    assert "relative_volume" in score_res["components"]
    assert len(score_res["reason"]) > 0
