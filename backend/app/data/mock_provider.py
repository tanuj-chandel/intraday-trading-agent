import datetime
import numpy as np
import pandas as pd
from typing import List, Dict
from app.data.base import MarketDataProvider
from app.schemas.schemas import StockBase

INDIAN_UNIVERSE = [
    StockBase(symbol="RELIANCE", company_name="Reliance Industries Ltd.", sector="Energy", industry="Oil & Gas", lot_size=1, tick_size=0.05),
    StockBase(symbol="HDFCBANK", company_name="HDFC Bank Ltd.", sector="Financial Services", industry="Private Banking", lot_size=1, tick_size=0.05),
    StockBase(symbol="TCS", company_name="Tata Consultancy Services Ltd.", sector="IT", industry="IT Services", lot_size=1, tick_size=0.05),
    StockBase(symbol="INFY", company_name="Infosys Ltd.", sector="IT", industry="IT Services", lot_size=1, tick_size=0.05),
    StockBase(symbol="ICICIBANK", company_name="ICICI Bank Ltd.", sector="Financial Services", industry="Private Banking", lot_size=1, tick_size=0.05),
    StockBase(symbol="TATAMOTORS", company_name="Tata Motors Ltd.", sector="Auto", industry="Automobiles", lot_size=1, tick_size=0.05),
    StockBase(symbol="SBIN", company_name="State Bank of India", sector="Financial Services", industry="PSU Banking", lot_size=1, tick_size=0.05),
    StockBase(symbol="BHARTIARTL", company_name="Bharti Airtel Ltd.", sector="Telecom", industry="Telecom Services", lot_size=1, tick_size=0.05),
    StockBase(symbol="ITC", company_name="ITC Ltd.", sector="FMCG", industry="Diversified FMCG", lot_size=1, tick_size=0.05),
    StockBase(symbol="LT", company_name="Larsen & Toubro Ltd.", sector="Capital Goods", industry="Engineering & Construction", lot_size=1, tick_size=0.05),
    StockBase(symbol="KOTAKBANK", company_name="Kotak Mahindra Bank Ltd.", sector="Financial Services", industry="Private Banking", lot_size=1, tick_size=0.05),
    StockBase(symbol="AXISBANK", company_name="Axis Bank Ltd.", sector="Financial Services", industry="Private Banking", lot_size=1, tick_size=0.05),
    StockBase(symbol="SUNPHARMA", company_name="Sun Pharmaceutical Industries", sector="Healthcare", industry="Pharmaceuticals", lot_size=1, tick_size=0.05),
    StockBase(symbol="BAJFINANCE", company_name="Bajaj Finance Ltd.", sector="Financial Services", industry="NBFC", lot_size=1, tick_size=0.05),
    StockBase(symbol="TITAN", company_name="Titan Company Ltd.", sector="Consumer Durables", industry="Gems & Jewellery", lot_size=1, tick_size=0.05)
]

BASE_PRICES = {
    "RELIANCE": 2980.50,
    "HDFCBANK": 1640.25,
    "TCS": 4120.00,
    "INFY": 1820.75,
    "ICICIBANK": 1180.40,
    "TATAMOTORS": 1040.60,
    "SBIN": 820.10,
    "BHARTIARTL": 1490.00,
    "ITC": 490.50,
    "LT": 3650.00,
    "KOTAKBANK": 1780.00,
    "AXISBANK": 1210.00,
    "SUNPHARMA": 1730.00,
    "BAJFINANCE": 7150.00,
    "TITAN": 3540.00,
    "NIFTY 50": 24850.00,
    "BANK NIFTY": 51200.00
}

class MockMarketDataProvider(MarketDataProvider):
    """
    Simulates high fidelity intraday and daily Indian stock market data.
    """
    
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.universe = INDIAN_UNIVERSE
        self.base_prices = BASE_PRICES

    async def get_universe(self) -> List[StockBase]:
        return self.universe

    async def get_candles(
        self,
        symbol: str,
        interval: str = "5m",
        limit: int = 100
    ) -> pd.DataFrame:
        base_price = self.base_prices.get(symbol.upper(), 1000.0)
        
        # Determine trend drift based on symbol for varied realistic setups
        trend_drift = 0.0003 if symbol in ["RELIANCE", "TATAMOTORS", "BHARTIARTL", "ICICIBANK"] else (-0.0002 if symbol in ["INFY", "TCS"] else 0.0)
        volatility = 0.0035
        
        now = datetime.datetime.now().replace(second=0, microsecond=0)
        delta = datetime.timedelta(minutes=5)
        timestamps = [now - (limit - 1 - i) * delta for i in range(limit)]
        
        closes = []
        highs = []
        lows = []
        opens = []
        volumes = []
        
        curr_price = base_price * (1 - 0.01 * limit * 0.02)
        for i in range(limit):
            # Geometric Brownian Motion step
            ret = self.rng.normal(trend_drift, volatility)
            open_p = curr_price
            close_p = open_p * (1 + ret)
            high_p = max(open_p, close_p) * (1 + abs(self.rng.normal(0, volatility * 0.5)))
            low_p = min(open_p, close_p) * (1 - abs(self.rng.normal(0, volatility * 0.5)))
            
            # Base volume with occasional spikes
            vol = int(self.rng.lognormal(mean=10.5, sigma=0.6))
            if i > limit - 10 and symbol in ["TATAMOTORS", "RELIANCE", "ICICIBANK"]:
                vol = int(vol * 2.5)  # RVOL surge simulation
                
            opens.append(round(open_p, 2))
            highs.append(round(high_p, 2))
            lows.append(round(low_p, 2))
            closes.append(round(close_p, 2))
            volumes.append(vol)
            curr_price = close_p

        df = pd.DataFrame({
            "timestamp": timestamps,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes
        })
        return df

    async def get_quote(self, symbol: str) -> Dict[str, float]:
        df = await self.get_candles(symbol, limit=20)
        latest = df.iloc[-1]
        prev_close = df.iloc[0]["open"]
        change = latest["close"] - prev_close
        change_pct = (change / prev_close) * 100
        
        return {
            "symbol": symbol,
            "current_price": float(latest["close"]),
            "prev_close": float(prev_close),
            "open": float(df.iloc[0]["open"]),
            "high": float(df["high"].max()),
            "low": float(df["low"].min()),
            "volume": float(df["volume"].sum()),
            "change": round(float(change), 2),
            "change_pct": round(float(change_pct), 2)
        }

    async def get_market_index(self, index_symbol: str = "NIFTY 50") -> Dict[str, float]:
        df = await self.get_candles(index_symbol, limit=50)
        latest = df.iloc[-1]
        prev_close = df.iloc[0]["open"]
        change = latest["close"] - prev_close
        change_pct = (change / prev_close) * 100
        
        return {
            "symbol": index_symbol,
            "current_price": float(latest["close"]),
            "prev_close": float(prev_close),
            "open": float(df.iloc[0]["open"]),
            "high": float(df["high"].max()),
            "low": float(df["low"].min()),
            "volume": float(df["volume"].sum()),
            "change": round(float(change), 2),
            "change_pct": round(float(change_pct), 2)
        }
