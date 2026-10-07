import pandas as pd
from typing import Optional
from app.strategies.base import Strategy
from app.technical.indicators import TechnicalAnalysis
from app.schemas.schemas import TradeSignalCreate
from app.core.config import settings

class VWAPEMAMomentumStrategy(Strategy):
    """
    Intraday Trend-Following Strategy: VWAP + EMA + Momentum + Relative Volume (RVOL).
    
    Rules:
    - Long Entry:
        1. Price crosses above or holds above VWAP.
        2. EMA 9 > EMA 21 (Short-term trend is bullish).
        3. RSI is between 52 and 72 (Healthy momentum, not overbought).
        4. RVOL >= 1.1 (Volume expansion confirms institutional participation).
        5. MACD Histogram > 0 and expanding.
    - Short Entry:
        1. Price crosses below or holds below VWAP.
        2. EMA 9 < EMA 21 (Short-term trend is bearish).
        3. RSI is between 28 and 48 (Bearish momentum, not oversold).
        4. RVOL >= 1.1.
        5. MACD Histogram < 0.
    """

    def get_id(self) -> str:
        return "VWAP_EMA_MOMENTUM_V1"

    def get_name(self) -> str:
        return "VWAP_EMA_Momentum_RVOL"

    def evaluate(
        self,
        symbol: str,
        df: pd.DataFrame,
        account_balance: float = 100000.0,
        risk_per_trade_pct: float = 0.01
    ) -> Optional[TradeSignalCreate]:
        if len(df) < 30:
            return None

        df_calc = TechnicalAnalysis.compute_all_indicators(df)
        latest = df_calc.iloc[-1]
        
        close = latest["close"]
        vwap = latest["vwap"]
        ema_9 = latest["ema_9"]
        ema_21 = latest["ema_21"]
        rsi = latest["rsi_14"]
        macd_hist = latest["macd_hist"]
        rvol = latest["rvol"]
        atr = max(latest["atr_14"], close * 0.005)

        # Bullish Setup Evaluation
        is_bullish = (
            close > vwap and
            ema_9 > ema_21 and
            52 <= rsi <= 72 and
            rvol >= 1.1 and
            macd_hist > 0
        )

        # Bearish Setup Evaluation
        is_bearish = (
            close < vwap and
            ema_9 < ema_21 and
            28 <= rsi <= 48 and
            rvol >= 1.1 and
            macd_hist < 0
        )

        max_risk_rupees = account_balance * getattr(settings, "MAX_RISK_PER_TRADE_PCT", risk_per_trade_pct)
        max_notional_pct = getattr(settings, "MAX_POSITION_NOTIONAL_PCT", 0.20)
        max_position_capital = account_balance * max_notional_pct  # Max 20% exposure per position

        if is_bullish:
            entry = round(close, 2)
            stop_loss = round(entry - (1.5 * atr), 2)
            risk_per_share = entry - stop_loss
            if risk_per_share <= 0:
                return None
                
            target = round(entry + (2.0 * risk_per_share), 2)
            
            # Position sizing constrained by risk budget and max exposure
            qty_by_risk = int(max_risk_rupees / risk_per_share)
            qty_by_exposure = int(max_position_capital / entry)
            quantity = max(1, min(qty_by_risk, qty_by_exposure))
            
            score = round(min(98.0, 60.0 + (rvol * 10) + (rsi - 50)), 1)
            explanation = (
                f"BULLISH SETUP on {symbol}: Price (₹{entry}) holding above VWAP (₹{vwap:.2f}) "
                f"with EMA9 (₹{ema_9:.2f}) > EMA21 (₹{ema_21:.2f}). Healthy momentum RSI={rsi:.1f}, "
                f"MACD histogram positive, and volume surge RVOL={rvol:.2f}x."
            )

            return TradeSignalCreate(
                symbol=symbol,
                direction="BUY",
                entry_price=entry,
                stop_loss=stop_loss,
                target_price=target,
                quantity=quantity,
                strategy_name=self.get_name(),
                strategy_score=score,
                explanation=explanation
            )

        elif is_bearish:
            entry = round(close, 2)
            stop_loss = round(entry + (1.5 * atr), 2)
            risk_per_share = stop_loss - entry
            if risk_per_share <= 0:
                return None
                
            target = round(entry - (2.0 * risk_per_share), 2)
            
            qty_by_risk = int(max_risk_rupees / risk_per_share)
            qty_by_exposure = int(max_position_capital / entry)
            quantity = max(1, min(qty_by_risk, qty_by_exposure))
            
            score = round(min(98.0, 60.0 + (rvol * 10) + (50 - rsi)), 1)
            explanation = (
                f"BEARISH SETUP on {symbol}: Price (₹{entry}) rejected below VWAP (₹{vwap:.2f}) "
                f"with EMA9 (₹{ema_9:.2f}) < EMA21 (₹{ema_21:.2f}). Bearish momentum RSI={rsi:.1f}, "
                f"MACD histogram negative, and volume surge RVOL={rvol:.2f}x."
            )

            return TradeSignalCreate(
                symbol=symbol,
                direction="SELL",
                entry_price=entry,
                stop_loss=stop_loss,
                target_price=target,
                quantity=quantity,
                strategy_name=self.get_name(),
                strategy_score=score,
                explanation=explanation
            )

        return None
