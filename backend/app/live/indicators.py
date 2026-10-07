import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from app.live.data_types import LiveCandle

class LiveIndicatorCalculator:
    """
    Computes real-time technical indicators incrementally on closed candles:
    EMA 9, EMA 21, RSI 14, MACD (12,26,9), VWAP, ATR 14, RVOL 20.
    """

    @classmethod
    def calculate_indicators(cls, candles: List[LiveCandle]) -> Dict[str, Any]:
        if not candles or len(candles) < 2:
            return {
                "ema_fast": 0.0,
                "ema_slow": 0.0,
                "rsi": 50.0,
                "macd": 0.0,
                "macd_signal": 0.0,
                "macd_hist": 0.0,
                "vwap": 0.0,
                "atr": 0.0,
                "rvol": 1.0,
                "is_valid": False
            }

        df = pd.DataFrame([c.model_dump() for c in candles])

        # 1. EMAs
        ema_fast = float(df["close"].ewm(span=9, adjust=False).mean().iloc[-1])
        ema_slow = float(df["close"].ewm(span=21, adjust=False).mean().iloc[-1])

        # 2. RSI 14
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=min(14, len(df)), min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=min(14, len(df)), min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = float(100 - (100 / (1 + rs)).fillna(50).iloc[-1])

        # 3. MACD (12, 26, 9)
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        macd_sig = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = float((macd_line - macd_sig).iloc[-1])

        # 4. VWAP
        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        vol_sum = df["volume"].sum()
        vwap = float((typical_price * df["volume"]).sum() / vol_sum) if vol_sum > 0 else float(df["close"].iloc[-1])

        # 5. ATR 14
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = float(tr.rolling(window=min(14, len(df)), min_periods=1).mean().iloc[-1])

        # 6. RVOL 20
        avg_vol = float(df["volume"].rolling(window=min(20, len(df)), min_periods=1).mean().iloc[-1])
        curr_vol = float(df["volume"].iloc[-1])
        rvol = float(curr_vol / avg_vol) if avg_vol > 0 else 1.0

        return {
            "ema_fast": round(ema_fast, 2),
            "ema_slow": round(ema_slow, 2),
            "rsi": round(rsi, 2),
            "macd": round(float(macd_line.iloc[-1]), 2),
            "macd_signal": round(float(macd_sig.iloc[-1]), 2),
            "macd_hist": round(macd_hist, 2),
            "vwap": round(vwap, 2),
            "atr": round(atr, 2),
            "rvol": round(rvol, 2),
            "is_valid": len(candles) >= 5
        }
