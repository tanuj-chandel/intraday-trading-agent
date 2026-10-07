import pandas as pd
from typing import Dict, Any, List, Optional
from app.technical.indicators import TechnicalAnalysis
from app.schemas.schemas import NewsItem

class StockScoringEngine:
    """
    Multi-factor intraday scoring engine (0 - 100 scale).
    Combines technical, volume, regime alignment, and news sentiment factors.
    NOTE: The score is NOT a guarantee or probability of profit; it is a structured ranking metric.
    """

    @classmethod
    def calculate_score(
        cls,
        symbol: str,
        df: pd.DataFrame,
        market_regime: str,
        sector_score: float = 50.0,
        news_items: Optional[List[NewsItem]] = None
    ) -> Dict[str, Any]:
        if len(df) < 25:
            return {
                "symbol": symbol,
                "total_score": 50.0,
                "direction": "NEUTRAL",
                "components": {},
                "reason": "Insufficient historical data for scoring."
            }

        df_calc = TechnicalAnalysis.compute_all_indicators(df)
        latest = df_calc.iloc[-1]
        close = latest["close"]
        vwap = latest["vwap"]
        rsi = latest["rsi_14"]
        macd_hist = latest["macd_hist"]
        rvol = latest["rvol"]
        ema_9 = latest["ema_9"]
        ema_21 = latest["ema_21"]
        sma_50 = latest["sma_50"]
        atr = latest["atr_14"]
        
        breakout_info = TechnicalAnalysis.detect_breakout(df_calc)

        # 1. Trend Alignment (0-15 points)
        trend_score = 7.5
        if close > ema_9 > ema_21 > sma_50:
            trend_score = 15.0
        elif close < ema_9 < ema_21 < sma_50:
            trend_score = 15.0  # Strong trend down is also tradable for short
        elif close > ema_21:
            trend_score = 10.0
        elif close < ema_21:
            trend_score = 10.0

        # 2. Market Regime Alignment (0-10 points)
        regime_score = 5.0
        if market_regime == "TRENDING_UP" and close > ema_21:
            regime_score = 10.0
        elif market_regime == "TRENDING_DOWN" and close < ema_21:
            regime_score = 10.0
        elif market_regime == "HIGH_VOLATILITY":
            regime_score = 4.0
        elif market_regime == "SIDEWAYS":
            regime_score = 5.0

        # 3. Momentum (RSI + MACD) (0-15 points)
        mom_score = 7.5
        if 55 <= rsi <= 70 and macd_hist > 0:
            mom_score = 15.0  # Healthy bullish momentum
        elif 30 <= rsi <= 45 and macd_hist < 0:
            mom_score = 15.0  # Healthy bearish momentum
        elif rsi > 75 or rsi < 25:
            mom_score = 5.0   # Overextended
        else:
            mom_score = 8.0

        # 4. Relative Volume (RVOL) (0-15 points)
        vol_score = 7.5
        if rvol >= 2.0:
            vol_score = 15.0
        elif rvol >= 1.3:
            vol_score = 12.0
        elif rvol >= 0.8:
            vol_score = 7.5
        else:
            vol_score = 3.0

        # 5. VWAP Position (0-15 points)
        vwap_score = 7.5
        dist_to_vwap_pct = abs(close - vwap) / vwap * 100.0
        if 0.1 <= dist_to_vwap_pct <= 1.2:
            # Ideal intraday entry zone near VWAP
            vwap_score = 15.0
        elif dist_to_vwap_pct < 0.1:
            vwap_score = 10.0
        elif dist_to_vwap_pct > 2.5:
            # Overextended from VWAP
            vwap_score = 4.0
        else:
            vwap_score = 8.0

        # 6. Breakout Setup (0-10 points)
        bo_score = 5.0
        if breakout_info["breakout"] or breakout_info["breakdown"]:
            bo_score = 10.0
        elif rvol > 1.2:
            bo_score = 7.0

        # 7. Sector Strength (0-10 points)
        sec_score = min(10.0, max(0.0, sector_score * 0.1))

        # 8. News Sentiment (Capped at NEWS_MAX_ALPHA_WEIGHT, default 10.0 points)
        import datetime
        from app.core.config import settings
        max_news_weight = getattr(settings, "NEWS_MAX_ALPHA_WEIGHT", 10.0)
        max_news_age_min = getattr(settings, "NEWS_MAX_AGE_MINUTES", 120)
        base_neutral_news = max_news_weight / 2.0  # e.g. 5.0 points

        news_score = base_neutral_news
        latest_headline = None
        if news_items:
            now = datetime.datetime.now()
            fresh_news = []
            for n in news_items:
                pub = n.published_at.replace(tzinfo=None) if n.published_at.tzinfo else n.published_at
                if (now - pub).total_seconds() <= max_news_age_min * 60:
                    fresh_news.append(n)
            if fresh_news:
                sentiment_scores = [n.sentiment_score for n in fresh_news]
                avg_sent = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
                # Scale -1.0..+1.0 to 0..max_news_weight
                news_score = min(max_news_weight, max(0.0, base_neutral_news + (avg_sent * base_neutral_news)))
                latest_headline = fresh_news[0].headline

        total_score = round(trend_score + regime_score + mom_score + vol_score + vwap_score + bo_score + sec_score + news_score, 1)
        total_score = min(100.0, max(0.0, total_score))

        # Determine Primary Trade Direction Bias
        direction = "BULLISH" if close >= vwap and rsi >= 50 else ("BEARISH" if close < vwap and rsi < 50 else "NEUTRAL")

        # Rationale Construction
        reasons = []
        if trend_score >= 12:
            reasons.append("Strong moving average trend alignment")
        if vol_score >= 12:
            reasons.append(f"Significant volume surge (RVOL {rvol:.2f}x)")
        if vwap_score >= 12:
            reasons.append("Optimal price proximity to intraday VWAP")
        if bo_score >= 8:
            reasons.append("Active range breakout setup")
        if news_score >= 8:
            reasons.append("Positive news catalyst")

        reason_str = " | ".join(reasons) if reasons else "Moderate momentum setup within normal range."

        return {
            "symbol": symbol,
            "total_score": float(total_score),
            "direction": direction,
            "current_price": float(close),
            "components": {
                "trend_alignment": round(trend_score, 1),
                "regime_alignment": round(regime_score, 1),
                "momentum": round(mom_score, 1),
                "relative_volume": round(vol_score, 1),
                "vwap_position": round(vwap_score, 1),
                "breakout_setup": round(bo_score, 1),
                "sector_strength": round(sec_score, 1),
                "news_sentiment": round(news_score, 1)
            },
            "latest_news_headline": latest_headline,
            "reason": reason_str,
            "atr": float(atr)
        }
