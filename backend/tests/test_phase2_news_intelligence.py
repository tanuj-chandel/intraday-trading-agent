import pytest
from app.news.classifier import NewsClassifier, EVENT_CATEGORIES
from app.news.reliability import get_source_reliability, SourceReliability
from app.news.scorer import NewsImpactScorer

def test_news_event_categorization():
    cat1, _ = NewsClassifier.classify_headline("TCS Q1 Net Profit beats estimates, operating margin expands")
    assert cat1 == "Earnings"

    cat2, _ = NewsClassifier.classify_headline("L&T secures mega offshore order worth ₹7,500 Crore")
    assert cat2 == "Order win"

    cat3, _ = NewsClassifier.classify_headline("RBI MPC keeps repo rate steady, raises GDP outlook")
    assert cat3 == "Macro"

    cat4, _ = NewsClassifier.classify_headline("SEBI imposes revised margin requirements on derivative contracts")
    assert cat4 == "Regulatory"

def test_source_reliability_levels():
    assert get_source_reliability("NSE Announcement") == SourceReliability.LEVEL_1
    assert get_source_reliability("BSE Corporate") == SourceReliability.LEVEL_1
    assert get_source_reliability("Moneycontrol") == SourceReliability.LEVEL_2
    assert get_source_reliability("Reuters") == SourceReliability.LEVEL_2
    assert get_source_reliability("Random Telegram Channel") == SourceReliability.LEVEL_3

def test_news_impact_scorer():
    # Official exchange filing with bullish earnings
    res = NewsImpactScorer.calculate_impact(
        sentiment_score=0.85,
        event_category="Earnings",
        reliability=SourceReliability.LEVEL_1
    )
    assert res["impact_score"] > 80.0
    assert res["direction"] == "BULLISH"
    assert res["confidence"] >= 0.90
