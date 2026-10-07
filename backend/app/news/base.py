from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.schemas import NewsItem

class NewsProvider(ABC):
    """
    Abstract interface for financial news & sentiment data.
    Designed for future ingestion from Reuters, Bloomberg, Moneycontrol, NSE announcements, etc.
    """
    
    @abstractmethod
    async def get_latest_news(self, limit: int = 20) -> List[NewsItem]:
        """Fetch latest market and corporate news."""
        pass

    @abstractmethod
    async def get_news_for_symbol(self, symbol: str, limit: int = 5) -> List[NewsItem]:
        """Fetch news specific to a particular stock symbol."""
        pass
