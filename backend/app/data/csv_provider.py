import os
import datetime
import pandas as pd
from typing import List, Dict, Optional
from app.data.base import MarketDataProvider
from app.schemas.schemas import StockBase

class HistoricalCSVMarketDataProvider(MarketDataProvider):
    """
    Loads historical market data from local CSV files for reproducible backtesting/replay.
    Expects CSV directory with files formatted as: `<SYMBOL>.csv`
    Columns: `timestamp,open,high,low,close,volume`
    """
    
    def __init__(self, data_dir: str = "app/data/sample_data"):
        self.data_dir = data_dir

    async def get_universe(self) -> List[StockBase]:
        universe = []
        if os.path.exists(self.data_dir):
            for fname in os.listdir(self.data_dir):
                if fname.endswith(".csv"):
                    symbol = fname.replace(".csv", "").upper()
                    universe.append(StockBase(
                        symbol=symbol,
                        company_name=f"{symbol} India Ltd.",
                        sector="Diversified"
                    ))
        return universe

    async def get_candles(
        self,
        symbol: str,
        interval: str = "5m",
        limit: int = 100
    ) -> pd.DataFrame:
        csv_path = os.path.join(self.data_dir, f"{symbol.upper()}.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Historical CSV not found for symbol: {symbol}")
            
        df = pd.read_csv(csv_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        return df.tail(limit).reset_index(drop=True)

    async def get_quote(self, symbol: str) -> Dict[str, float]:
        df = await self.get_candles(symbol, limit=2)
        latest = df.iloc[-1]
        prev_close = df.iloc[0]["close"] if len(df) > 1 else latest["open"]
        change = latest["close"] - prev_close
        change_pct = (change / prev_close) * 100
        
        return {
            "symbol": symbol,
            "current_price": float(latest["close"]),
            "prev_close": float(prev_close),
            "open": float(latest["open"]),
            "high": float(latest["high"]),
            "low": float(latest["low"]),
            "volume": float(latest["volume"]),
            "change": round(float(change), 2),
            "change_pct": round(float(change_pct), 2)
        }

    async def get_market_index(self, index_symbol: str = "NIFTY 50") -> Dict[str, float]:
        try:
            return await self.get_quote(index_symbol)
        except Exception:
            return {
                "symbol": index_symbol,
                "current_price": 24800.0,
                "prev_close": 24700.0,
                "open": 24750.0,
                "high": 24850.0,
                "low": 24720.0,
                "volume": 5000000.0,
                "change": 100.0,
                "change_pct": 0.40
            }
