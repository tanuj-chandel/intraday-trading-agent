import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from app.technical.indicators import TechnicalAnalysis

class MarketRegimeEngine:
    """
    Classifies market conditions using objective, measurable mathematical rules.
    Regimes: TRENDING_UP, TRENDING_DOWN, SIDEWAYS, HIGH_VOLATILITY, GAP_UP, GAP_DOWN, UNKNOWN
    """

    @classmethod
    def classify_regime(cls, df: pd.DataFrame, prev_day_close: float = None) -> Dict[str, Any]:
        if len(df) < 30:
            return {
                "regime": "UNKNOWN",
                "trend_strength": 0.0,
                "volatility_score": 0.0,
                "adx_value": 0.0,
                "atr_value": 0.0,
                "description": "Insufficient candle data for reliable market regime classification"
            }

        df_calc = TechnicalAnalysis.compute_all_indicators(df)
        latest = df_calc.iloc[-1]
        first = df_calc.iloc[0]
        
        close = latest["close"]
        open_price = first["open"]
        ema_9 = latest["ema_9"]
        ema_21 = latest["ema_21"]
        sma_50 = latest["sma_50"]
        vwap = latest["vwap"]
        atr = latest["atr_14"]
        bb_upper = latest["bb_upper"]
        bb_lower = latest["bb_lower"]
        bb_middle = latest["bb_middle"]
        
        # Calculate Bollinger Bandwidth (volatility proxy)
        bb_bandwidth = (bb_upper - bb_lower) / (bb_middle + 1e-10) * 100.0
        
        # Calculate ATR % of price
        atr_pct = (atr / close) * 100.0
        
        # Gap analysis
        reference_prev_close = prev_day_close if prev_day_close else first["open"]
        gap_pct = ((open_price - reference_prev_close) / reference_prev_close) * 100.0
        
        # Trend indicators
        ema_slope = (latest["ema_21"] - df_calc.iloc[-10]["ema_21"]) / df_calc.iloc[-10]["ema_21"] * 100.0
        trend_strength = min(100.0, max(0.0, abs(ema_slope) * 20.0 + (abs(latest["rsi_14"] - 50.0) * 1.5)))

        # Rule evaluation
        if abs(gap_pct) >= 0.7:
            if gap_pct > 0:
                regime = "GAP_UP"
                desc = f"Strong gap up open (+{gap_pct:.2f}%). Watch for opening range breakout or gap fill."
            else:
                regime = "GAP_DOWN"
                desc = f"Strong gap down open ({gap_pct:.2f}%). Watch for continuation or mean reversion."
        elif atr_pct > 1.8 or bb_bandwidth > 3.5:
            regime = "HIGH_VOLATILITY"
            desc = f"Elevated intraday volatility (ATR {atr_pct:.2f}%, BB Width {bb_bandwidth:.2f}%). Use wider stops and conservative position sizes."
        elif close > ema_9 and ema_9 > ema_21 and close > vwap and latest["rsi_14"] > 55:
            regime = "TRENDING_UP"
            desc = "Bullish momentum: Price trading firmly above EMA9, EMA21 and VWAP with RSI > 55."
        elif close < ema_9 and ema_9 < ema_21 and close < vwap and latest["rsi_14"] < 45:
            regime = "TRENDING_DOWN"
            desc = "Bearish momentum: Price trading below EMA9, EMA21 and VWAP with RSI < 45."
        else:
            regime = "SIDEWAYS"
            desc = "Consolidation / Range-bound: Price oscillating near VWAP within contracting moving averages."

        return {
            "regime": regime,
            "trend_strength": round(float(trend_strength), 2),
            "volatility_score": round(float(atr_pct), 2),
            "adx_value": round(float(trend_strength * 0.4), 2),
            "atr_value": round(float(atr), 2),
            "bb_bandwidth": round(float(bb_bandwidth), 2),
            "gap_pct": round(float(gap_pct), 2),
            "description": desc
        }

    _current_regime: str = "TRENDING"
    _current_vix: float = 14.5

    @classmethod
    def set_current_regime(cls, regime: str, vix: float = 14.5):
        cls._current_regime = regime
        cls._current_vix = vix

    @classmethod
    def get_current_regime_info(cls) -> Dict[str, Any]:
        return {
            "regime": cls._current_regime,
            "india_vix": cls._current_vix,
            "is_choppy": cls._current_regime in ("CHOPPY", "SIDEWAYS"),
            "is_high_vol": cls._current_regime in ("HIGH_VOL", "HIGH_VOLATILITY"),
            "is_trending": "TRENDING" in cls._current_regime
        }

    @classmethod
    def classify_nifty_vix_regime(
        cls,
        nifty_price: float,
        nifty_vwap: float,
        nifty_ema_9: float,
        nifty_ema_21: float,
        india_vix: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Classifies market regime into TRENDING / CHOPPY / HIGH_VOL using:
        - India VIX (volatility risk gauge)
        - Nifty 50 trend (Price vs VWAP and EMA 9/21 cross)
        """
        from app.core.config import settings
        vix = india_vix if india_vix is not None else cls._current_vix
        high_vol_thresh = getattr(settings, "INDIA_VIX_HIGH_VOL_THRESHOLD", 22.0)

        # 1. High Volatility Check
        if vix >= high_vol_thresh:
            regime = "HIGH_VOL"
            desc = f"Elevated market-wide volatility (India VIX {vix:.1f} >= {high_vol_thresh:.1f})."
        # 2. Bullish or Bearish Trending Check
        elif (nifty_price > nifty_vwap and nifty_ema_9 > nifty_ema_21) or (nifty_price < nifty_vwap and nifty_ema_9 < nifty_ema_21):
            regime = "TRENDING"
            trend_side = "Bullish" if nifty_price > nifty_vwap else "Bearish"
            desc = f"{trend_side} intraday trend: Nifty aligned with VWAP and EMA 9/21."
        # 3. Choppy / Sideways Market
        else:
            regime = "CHOPPY"
            desc = "Choppy / non-trending market: Nifty oscillating around VWAP with contracting moving averages."

        cls.set_current_regime(regime, vix)
        return {
            "regime": regime,
            "india_vix": vix,
            "description": desc
        }
