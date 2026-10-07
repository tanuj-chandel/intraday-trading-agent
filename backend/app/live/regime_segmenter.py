"""
Phase 8 — Market Regime Segmenter
Classifies each paper trade into regime and time-of-day buckets
for performance attribution analysis.
"""
import datetime
from typing import Dict, Optional, Any


class Phase8RegimeSegmenter:
    """
    Classifies live market conditions into discrete regime and time buckets.
    Used to segment paper trade performance by market environment.
    """

    # Time-of-day buckets (IST)
    OPEN_30M_END = datetime.time(9, 45)
    CLOSE_1H_START = datetime.time(14, 30)
    MARKET_OPEN = datetime.time(9, 15)
    MARKET_CLOSE = datetime.time(15, 30)

    @classmethod
    def classify_time_bucket(cls, dt: Optional[datetime.datetime] = None) -> str:
        """Classify time of day into trading bucket."""
        t = (dt or datetime.datetime.now()).time()
        if t < cls.MARKET_OPEN:
            return "PRE_MARKET"
        elif t <= cls.OPEN_30M_END:
            return "OPEN_30M"
        elif t >= cls.CLOSE_1H_START:
            return "CLOSE_1H"
        elif t >= cls.MARKET_CLOSE:
            return "POST_MARKET"
        else:
            return "MID_SESSION"

    @classmethod
    def classify_regime(
        cls,
        ema_fast: float,
        ema_slow: float,
        atr: float,
        prev_close: float,
        open_price: float,
        vwap: float,
        current_price: float,
        adx: Optional[float] = None,
    ) -> str:
        """
        Classify current market regime from indicator snapshot.
        Returns one of: TRENDING_UP, TRENDING_DOWN, SIDEWAYS, HIGH_VOL,
        LOW_VOL, GAP_UP, GAP_DOWN, BULLISH, BEARISH.
        """
        # Gap detection (>0.5% gap from prev close)
        gap_pct = 0.0
        if prev_close > 0:
            gap_pct = (open_price - prev_close) / prev_close * 100.0
        if gap_pct > 0.5:
            return "GAP_UP"
        if gap_pct < -0.5:
            return "GAP_DOWN"

        # Trend direction from EMAs
        bullish = ema_fast > ema_slow
        bearish = ema_fast < ema_slow
        ema_diff_pct = abs(ema_fast - ema_slow) / ema_slow * 100.0 if ema_slow > 0 else 0.0

        # Volatility regime from ATR
        atr_pct = atr / current_price * 100.0 if current_price > 0 else 0.0
        high_vol = atr_pct > 1.5   # ATR > 1.5% of price = high volatility
        low_vol = atr_pct < 0.3    # ATR < 0.3% = low volatility

        if high_vol:
            return "HIGH_VOL"
        if low_vol:
            return "LOW_VOL"

        # Sideways: EMAs close together
        if ema_diff_pct < 0.2:
            return "SIDEWAYS"

        # Trend
        if bullish and adx and adx > 25:
            return "TRENDING_UP"
        if bearish and adx and adx > 25:
            return "TRENDING_DOWN"

        return "BULLISH" if bullish else "BEARISH"

    @classmethod
    def classify_from_snapshot(cls, indicator_snapshot: Dict[str, Any],
                                open_price: float = 0.0,
                                prev_close: float = 0.0) -> str:
        """Classify regime from a live indicator snapshot dict."""
        try:
            return cls.classify_regime(
                ema_fast=indicator_snapshot.get("ema_fast", 0.0),
                ema_slow=indicator_snapshot.get("ema_slow", 0.0),
                atr=indicator_snapshot.get("atr", 0.0),
                prev_close=prev_close,
                open_price=open_price,
                vwap=indicator_snapshot.get("vwap", 0.0),
                current_price=indicator_snapshot.get("ema_fast", 0.0),  # approximation
                adx=indicator_snapshot.get("adx", None),
            )
        except Exception:
            return "UNKNOWN"
