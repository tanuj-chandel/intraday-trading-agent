from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import pandas as pd
from app.schemas.schemas import Candle, StockBase

class MarketDataProvider(ABC):
    """
    Abstract interface for market data ingestion.
    Designed so live Indian broker APIs (Zerodha Kite, Angel One, Upstox, etc.)
    can be plugged in without changing downstream analysis or strategy engines.
    """
    
    @abstractmethod
    async def get_universe(self) -> List[StockBase]:
        """Returns the list of tradable stocks in the universe."""
        pass

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        interval: str = "5m",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Returns OHLCV DataFrame with columns:
        ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, float]:
        """
        Returns current quote dictionary:
        {'current_price': float, 'prev_close': float, 'open': float, 'high': float, 'low': float, 'volume': float, 'change_pct': float}
        """
        pass

    @abstractmethod
    async def get_market_index(self, index_symbol: str = "NIFTY 50") -> Dict[str, float]:
        """Returns index level metrics."""
        pass
