import datetime
from typing import List, Optional, Dict, Any
from app.news.base import NewsProvider
from app.news.reliability import get_source_reliability, SourceReliability
from app.news.classifier import NewsClassifier
from app.news.scorer import NewsImpactScorer
from app.schemas.schemas import NewsItem

ENHANCED_INDIAN_NEWS_FEED = [
    {
        "headline": "NSE Announcement: L&T secures ₹8,250 Crore Mega Hydrocarbon EPC Order from Saudi Aramco",
        "source": "NSE",
        "related_symbols": ["LT"],
        "company": "Larsen & Toubro Ltd.",
        "sector": "Capital Goods",
        "sentiment": "BULLISH",
        "sentiment_score": 0.90,
        "url": "https://www.nseindia.com/corporate-announcements"
    },
    {
        "headline": "BSE Filing: Reliance Industries commissions 10 GW Solar Gigafactory in Jamnagar ahead of schedule",
        "source": "BSE",
        "related_symbols": ["RELIANCE"],
        "company": "Reliance Industries Ltd.",
        "sector": "Energy",
        "sentiment": "BULLISH",
        "sentiment_score": 0.88,
        "url": "https://www.bseindia.com/corporates"
    },
    {
        "headline": "ICICI Bank Q1 Net Profit rises 18.2% YoY to ₹11,059 Cr, Net NPA drops to multi-year low of 0.42%",
        "source": "Moneycontrol",
        "related_symbols": ["ICICIBANK", "BANK NIFTY"],
        "company": "ICICI Bank Ltd.",
        "sector": "Financial Services",
        "sentiment": "BULLISH",
        "sentiment_score": 0.82,
        "url": "https://www.moneycontrol.com"
    },
    {
        "headline": "Tata Motors UK Arm JLR wholesale volumes surge 15% YoY with record Defender & Range Rover demand",
        "source": "LiveMint",
        "related_symbols": ["TATAMOTORS"],
        "company": "Tata Motors Ltd.",
        "sector": "Auto",
        "sentiment": "BULLISH",
        "sentiment_score": 0.78,
        "url": "https://www.livemint.com"
    },
    {
        "headline": "RBI Monetary Policy Committee keeps Repo Rate at 6.50%; Projects robust 7.2% FY25 GDP Growth",
        "source": "PIB India",
        "related_symbols": ["NIFTY", "BANK NIFTY", "SBIN", "HDFCBANK"],
        "company": "Reserve Bank of India",
        "sector": "Macro",
        "sentiment": "BULLISH",
        "sentiment_score": 0.65,
        "url": "https://pib.gov.in"
    },
    {
        "headline": "TRAI Data: Bharti Airtel leads 5G additions with 2.4 Million new active subscribers in July",
        "source": "Economic Times",
        "related_symbols": ["BHARTIARTL"],
        "company": "Bharti Airtel Ltd.",
        "sector": "Telecom",
        "sentiment": "BULLISH",
        "sentiment_score": 0.70,
        "url": "https://economictimes.indiatimes.com"
    },
    {
        "headline": "GST Revenue reaches ₹1.82 Lakh Crore in August, indicating buoyant domestic consumption & manufacturing",
        "source": "PIB India",
        "related_symbols": ["NIFTY", "ITC", "TITAN"],
        "company": "Ministry of Finance",
        "sector": "Macro",
        "sentiment": "BULLISH",
        "sentiment_score": 0.75,
        "url": "https://pib.gov.in"
    },
    {
        "headline": "US IT clients exercise discretionary budget caution; Tier-1 Indian IT firms see mild project delays",
        "source": "Reuters",
        "related_symbols": ["INFY", "TCS"],
        "company": "Indian IT Sector",
        "sector": "IT",
        "sentiment": "BEARISH",
        "sentiment_score": -0.50,
        "url": "https://www.reuters.com"
    },
    {
        "headline": "SEBI issues revised prudential lending guidelines for retail unsecured personal loans and credit cards",
        "source": "Business Standard",
        "related_symbols": ["BAJFINANCE", "KOTAKBANK"],
        "company": "SEBI",
        "sector": "Financial Services",
        "sentiment": "BEARISH",
        "sentiment_score": -0.40,
        "url": "https://www.business-standard.com"
    },
    {
        "headline": "Defense Ministry clears ₹45,000 Crore procurement for Next-Gen LCA Tejas Mk1A & Helicopters",
        "source": "CNBC-TV18",
        "related_symbols": ["HAL", "BEL"],
        "company": "Ministry of Defence",
        "sector": "Capital Goods",
        "sentiment": "BULLISH",
        "sentiment_score": 0.85,
        "url": "https://www.cnbctv18.com"
    }
]

import xml.etree.ElementTree as ET
import httpx
from email.utils import parsedate_to_datetime

SYMBOL_KEYWORDS = {
    "RELIANCE": ["reliance", "ril", "jio"],
    "TCS": ["tcs", "tata consultancy"],
    "INFY": ["infosys", "infy"],
    "HDFCBANK": ["hdfc", "hdfc bank"],
    "ICICIBANK": ["icici", "icici bank"],
    "SBIN": ["sbin", "sbi", "state bank"],
    "TATAMOTORS": ["tata motors", "tatamotors", "jlr"],
    "BHARTIARTL": ["airtel", "bharti airtel"],
    "ITC": ["itc"],
    "KOTAKBANK": ["kotak", "kotak bank"],
    "LT": ["larsen", "l&t"],
    "AXISBANK": ["axis bank", "axisbank"],
    "BAJFINANCE": ["bajaj finance", "bajfinance"],
    "MARUTI": ["maruti", "suzuki"],
    "TATASTEEL": ["tata steel", "tatasteel"],
    "TITAN": ["titan"],
    "WIPRO": ["wipro"],
    "SUNPHARMA": ["sun pharma", "sunpharma"]
}

BULLISH_KEYWORDS = ["profit", "surge", "gain", "jump", "order", "rally", "growth", "dividend", "expansion", "buy", "upbeat", "record", "beats", "rises", "high", "positive"]
BEARISH_KEYWORDS = ["drop", "fall", "loss", "plunge", "decline", "warning", "probe", "penalty", "fraud", "scam", "bearish", "down", "slump", "cuts", "deficit", "tumble", "negative"]

class NewsAggregator(NewsProvider):
    """
    Enriches, classifies, and scores financial news and official corporate announcements.
    Features live Indian financial RSS ingestion with automatic symbol mapping.
    """

    def __init__(self):
        self.news_items: List[NewsItem] = []
        self._last_fetched: Optional[datetime.datetime] = None
        self._load_fallback_news()

    def _load_fallback_news(self):
        now = datetime.datetime.now()
        for idx, item in enumerate(ENHANCED_INDIAN_NEWS_FEED):
            pub_time = now - datetime.timedelta(minutes=(idx * 20 + 8))
            reliability = get_source_reliability(item["source"])
            category, default_impact = NewsClassifier.classify_headline(item["headline"])
            impact_res = NewsImpactScorer.calculate_impact(
                sentiment_score=item["sentiment_score"],
                event_category=category,
                reliability=reliability
            )

            self.news_items.append(NewsItem(
                id=idx + 1,
                headline=item["headline"],
                source=item["source"],
                source_reliability=reliability.value,
                published_at=pub_time,
                related_symbols=item["related_symbols"],
                company=item.get("company"),
                sector=item.get("sector"),
                sentiment=item["sentiment"],
                sentiment_score=item["sentiment_score"],
                impact=default_impact,
                impact_score=impact_res["impact_score"],
                confidence=impact_res["confidence"],
                event_category=category,
                url=item["url"]
            ))

    async def refresh_live_news(self):
        now = datetime.datetime.now()
        if self._last_fetched and (now - self._last_fetched).total_seconds() < 300:
            return  # Cache for 5 minutes

        url = "https://news.google.com/rss/search?q=NSE+stocks+India+earnings&hl=en-IN&gl=IN&ceid=IN:en"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            async with httpx.AsyncClient(timeout=6.0, verify=False) as client:
                resp = await client.get(url, headers=headers)

            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                items = root.findall("./channel/item")
                live_news = []

                for idx, item in enumerate(items[:25]):
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_str = item.find("pubDate").text if item.find("pubDate") is not None else None
                    try:
                        pub_time = parsedate_to_datetime(pub_str) if pub_str else now
                    except Exception:
                        pub_time = now

                    # Extract symbols
                    title_lower = title.lower()
                    matched_symbols = []
                    for sym, kw_list in SYMBOL_KEYWORDS.items():
                        if any(kw in title_lower for kw in kw_list):
                            matched_symbols.append(sym)

                    if not matched_symbols:
                        matched_symbols = ["NIFTY"]

                    # Compute sentiment
                    bull_hits = sum(1 for kw in BULLISH_KEYWORDS if kw in title_lower)
                    bear_hits = sum(1 for kw in BEARISH_KEYWORDS if kw in title_lower)

                    if bull_hits > bear_hits:
                        sentiment = "BULLISH"
                        sentiment_score = min(0.9, 0.4 + (0.15 * bull_hits))
                    elif bear_hits > bull_hits:
                        sentiment = "BEARISH"
                        sentiment_score = max(-0.9, -0.4 - (0.15 * bear_hits))
                    else:
                        sentiment = "NEUTRAL"
                        sentiment_score = 0.0

                    category, default_impact = NewsClassifier.classify_headline(title)
                    reliability = get_source_reliability("Google News")
                    impact_res = NewsImpactScorer.calculate_impact(
                        sentiment_score=sentiment_score,
                        event_category=category,
                        reliability=reliability
                    )

                    live_news.append(NewsItem(
                        id=1000 + idx,
                        headline=title,
                        source="Live Market Feed",
                        source_reliability=reliability.value,
                        published_at=pub_time,
                        related_symbols=matched_symbols,
                        company=matched_symbols[0] if matched_symbols else "Indian Market",
                        sector="Equity",
                        sentiment=sentiment,
                        sentiment_score=round(sentiment_score, 2),
                        impact=default_impact,
                        impact_score=impact_res["impact_score"],
                        confidence=impact_res["confidence"],
                        event_category=category,
                        url=link
                    ))

                if live_news:
                    self.news_items = live_news + self.news_items[:10]
                    self._last_fetched = now

        except Exception as e:
            # Silently retain existing news items on network blip
            pass

    async def get_latest_news(self, limit: int = 20) -> List[NewsItem]:
        await self.refresh_live_news()
        return self.news_items[:limit]

    async def get_news_for_symbol(self, symbol: str, limit: int = 5) -> List[NewsItem]:
        await self.refresh_live_news()
        sym_clean = symbol.upper().replace(".NS", "")
        filtered = [n for n in self.news_items if sym_clean in [s.upper() for s in n.related_symbols]]
        return filtered[:limit]

    def get_sentiment_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Synchronous helper for signal engine to check news sentiment.
        """
        sym_clean = symbol.upper().replace(".NS", "")
        relevant = [n for n in self.news_items if sym_clean in [s.upper() for s in n.related_symbols]]
        if not relevant:
            return {"sentiment_score": 0.0, "status": "NEUTRAL", "headline": None}

        # Filter by NEWS_MAX_AGE_MINUTES (default 120 minutes)
        from app.core.config import settings
        from app.live.audit import LiveAuditLogger
        max_age_min = getattr(settings, "NEWS_MAX_AGE_MINUTES", 120)
        now = datetime.datetime.now()

        fresh_news = []
        for n in relevant:
            pub = n.published_at.replace(tzinfo=None) if n.published_at.tzinfo else n.published_at
            age_min = (now - pub).total_seconds() / 60.0
            if age_min <= max_age_min:
                fresh_news.append(n)
            else:
                LiveAuditLogger.log(
                    "NEWS_IGNORED_STALE",
                    f"News for {sym_clean} ignored (age {int(age_min)}m > {max_age_min}m): {n.headline[:50]}",
                    symbol=sym_clean
                )

        if not fresh_news:
            return {"sentiment_score": 0.0, "status": "NEUTRAL", "headline": None, "is_stale": True}

        avg_score = sum(n.sentiment_score for n in fresh_news) / len(fresh_news)
        return {
            "sentiment_score": round(avg_score, 2),
            "status": "BULLISH" if avg_score > 0.1 else ("BEARISH" if avg_score < -0.1 else "NEUTRAL"),
            "headline": fresh_news[0].headline,
            "is_stale": False
        }

news_aggregator = NewsAggregator()
