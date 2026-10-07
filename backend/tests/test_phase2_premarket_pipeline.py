import pytest
from app.data.mock_provider import MockMarketDataProvider
from app.news.aggregator import NewsAggregator
from app.premarket.analyzer import PreMarketAnalyzer
from app.premarket.premarket_data import PreMarketDataService

@pytest.mark.asyncio
async def test_premarket_data_service():
    provider = MockMarketDataProvider()
    service = PreMarketDataService(provider)
    
    indices = await service.get_index_metrics()
    assert "NIFTY 50" in indices
    assert "INDIA VIX" in indices

    metrics = await service.compute_stock_premarket_metrics("RELIANCE")
    assert "gap_pct" in metrics
    assert "day_range" in metrics
    assert "atr" in metrics

@pytest.mark.asyncio
async def test_premarket_full_pipeline_categorization():
    provider = MockMarketDataProvider()
    news = NewsAggregator()
    analyzer = PreMarketAnalyzer(provider, news)

    analysis = await analyzer.analyze()
    assert len(analysis.top_ranked_stocks) == 10
    assert len(analysis.top_long_candidates) >= 1
    assert len(analysis.formatted_report) > 100
    assert "INDIAN MARKET PRE-MARKET INTELLIGENCE REPORT" in analysis.formatted_report
    assert analysis.gift_nifty.gift_nifty_price > 0
