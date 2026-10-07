import datetime
from typing import List
from app.news.base import NewsProvider
from app.schemas.schemas import NewsItem

MOCK_NEWS_DATA = [
    {
        "headline": "GIFT Nifty indicates strong opening for Indian benchmarks; Asian markets trade higher",
        "source": "Moneycontrol",
        "related_symbols": ["NIFTY", "BANK NIFTY"],
        "sentiment": "BULLISH",
        "sentiment_score": 0.75,
        "importance": "HIGH",
        "url": "https://moneycontrol.com/news/business/markets"
    },
    {
        "headline": "Reliance Industries expands AI infrastructure partnership with Nvidia, pledges ₹20,000 Cr capex",
        "source": "Economic Times",
        "related_symbols": ["RELIANCE"],
        "sentiment": "BULLISH",
        "sentiment_score": 0.85,
        "importance": "HIGH",
        "url": "https://economictimes.indiatimes.com/markets"
    },
    {
        "headline": "Tata Motors UK arm JLR reports 14% YoY surge in quarterly wholesale volumes",
        "source": "LiveMint",
        "related_symbols": ["TATAMOTORS"],
        "sentiment": "BULLISH",
        "sentiment_score": 0.80,
        "importance": "HIGH",
        "url": "https://livemint.com/market"
    },
    {
        "headline": "ICICI Bank posts 17.5% net profit growth, gross NPA drops to multi-year low of 2.15%",
        "source": "CNBC-TV18",
        "related_symbols": ["ICICIBANK", "BANK NIFTY"],
        "sentiment": "BULLISH",
        "sentiment_score": 0.78,
        "importance": "HIGH",
        "url": "https://cnbctv18.com/market"
    },
    {
        "headline": "RBI keeps repo rate unchanged at 6.50%; highlights robust GDP outlook of 7.2%",
        "source": "Business Standard",
        "related_symbols": ["NIFTY", "BANK NIFTY", "SBIN", "HDFCBANK"],
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.30,
        "importance": "HIGH",
        "url": "https://business-standard.com/economy"
    },
    {
        "headline": "Bharti Airtel adds 2.1M mobile broadband subscribers in latest monthly TRAI data",
        "source": "Financial Express",
        "related_symbols": ["BHARTIARTL"],
        "sentiment": "BULLISH",
        "sentiment_score": 0.65,
        "importance": "MEDIUM",
        "url": "https://financialexpress.com/market"
    },
    {
        "headline": "IT Sector faces mild margin headwind as US client discretionary spending stays cautious",
        "source": "Reuters",
        "related_symbols": ["INFY", "TCS"],
        "sentiment": "BEARISH",
        "sentiment_score": -0.45,
        "importance": "MEDIUM",
        "url": "https://reuters.com/markets"
    },
    {
        "headline": "Larsen & Toubro secures mega offshore hydrocarbon order worth ₹7,500 Crore from Middle East",
        "source": "NDTV Profit",
        "related_symbols": ["LT"],
        "sentiment": "BULLISH",
        "sentiment_score": 0.70,
        "importance": "HIGH",
        "url": "https://ndtvprofit.com"
    },
    {
        "headline": "GST collections hit ₹1.82 Lakh Crore in August, underscoring resilient domestic consumption",
        "source": "PIB India",
        "related_symbols": ["NIFTY", "ITC", "TITAN"],
        "sentiment": "BULLISH",
        "sentiment_score": 0.60,
        "importance": "HIGH",
        "url": "https://pib.gov.in"
    }
]

class MockNewsProvider(NewsProvider):
    def __init__(self):
        self.news_items = []
        now = datetime.datetime.now()
        for idx, item in enumerate(MOCK_NEWS_DATA):
            pub_time = now - datetime.timedelta(minutes=(idx * 25 + 10))
            self.news_items.append(NewsItem(
                id=idx + 1,
                headline=item["headline"],
                source=item["source"],
                published_at=pub_time,
                related_symbols=item["related_symbols"],
                sentiment=item["sentiment"],
                sentiment_score=item["sentiment_score"],
                importance=item["importance"],
                url=item["url"]
            ))

    async def get_latest_news(self, limit: int = 20) -> List[NewsItem]:
        return self.news_items[:limit]

    async def get_news_for_symbol(self, symbol: str, limit: int = 5) -> List[NewsItem]:
        filtered = [n for n in self.news_items if symbol.upper() in [s.upper() for s in n.related_symbols]]
        return filtered[:limit]
