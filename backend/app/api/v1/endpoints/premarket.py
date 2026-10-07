from fastapi import APIRouter
from app.data.factory import get_market_data_provider
from app.news.aggregator import NewsAggregator
from app.premarket.analyzer import PreMarketAnalyzer
from app.schemas.schemas import PreMarketAnalysisResponse

router = APIRouter()
news_provider = NewsAggregator()

def get_premarket_analyzer() -> PreMarketAnalyzer:
    return PreMarketAnalyzer(get_market_data_provider(), news_provider)

@router.post("/analyze", response_model=PreMarketAnalysisResponse)
async def run_premarket_analysis():
    """
    Triggers automated pre-market analysis:
    - Global cues
    - Sector ranking
    - GIFT Nifty gap projection
    - Liquidity filtering
    - Top 10 Overall, Top 10 Longs, Top 10 Shorts setups
    - Formatted Pre-Market Report
    """
    analyzer = get_premarket_analyzer()
    return await analyzer.analyze()

@router.get("/report")
async def get_premarket_formatted_report():
    """
    Returns the latest formatted text pre-market report.
    """
    analyzer = get_premarket_analyzer()
    analysis = await analyzer.analyze()
    return {
        "report_text": analysis.formatted_report,
        "timestamp": analysis.timestamp.isoformat()
    }
