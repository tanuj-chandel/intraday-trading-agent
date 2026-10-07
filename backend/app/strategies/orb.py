import pandas as pd
from typing import Optional
from app.strategies.base import Strategy
from app.schemas.schemas import TradeSignalCreate
from app.technical.indicators import TechnicalAnalysis
from app.core.config import settings

class OpeningRangeBreakoutStrategy(Strategy):
    """
    Opening Range Breakout (ORB) Strategy for Indian Equities.
    Prepared for future activation (disabled by default).
    Monitors high and low of the initial 15-minute / 30-minute window and triggers
    breakout entries with volume surge confirmation.
    """

    def __init__(self, is_enabled: bool = False, range_minutes: int = 15):
        super().__init__(is_enabled=is_enabled)
        self.range_minutes = range_minutes

    def get_id(self) -> str:
        return f"ORB_{self.range_minutes}M_V1"

    def get_name(self) -> str:
        return f"Opening_Range_Breakout_{self.range_minutes}M"

    def evaluate(
        self,
        symbol: str,
        df: pd.DataFrame,
        account_balance: float = 100000.0,
        risk_per_trade_pct: float = 0.01
    ) -> Optional[TradeSignalCreate]:
        if not self.is_enabled():
            return None

        if len(df) < 15:
            return None

        # 1. Establish Opening Range
        orb_candles = df.iloc[:3] if len(df) >= 3 else df
        orb_high = orb_candles["high"].max()
        orb_low = orb_candles["low"].min()

        latest = df.iloc[-1]
        close = latest["close"]
        volume = latest["volume"]
        avg_vol = df["volume"].mean()

        # Check Breakout
        if close > orb_high and volume > 1.2 * avg_vol:
            sl = round(orb_low, 2)
            risk = close - sl
            if risk <= 0:
                return None
            tp = round(close + (2.0 * risk), 2)
            qty = max(1, int((account_balance * risk_per_trade_pct) / risk))
            return TradeSignalCreate(
                symbol=symbol,
                direction="BUY",
                entry_price=close,
                stop_loss=sl,
                target_price=tp,
                quantity=qty,
                strategy_name=self.get_name(),
                strategy_score=85.0,
                explanation=f"ORB Bullish Breakout above {self.range_minutes}m high ₹{orb_high:.2f}"
            )

        elif close < orb_low and volume > 1.2 * avg_vol:
            sl = round(orb_high, 2)
            risk = sl - close
            if risk <= 0:
                return None
            tp = round(close - (2.0 * risk), 2)
            qty = max(1, int((account_balance * risk_per_trade_pct) / risk))
            return TradeSignalCreate(
                symbol=symbol,
                direction="SELL",
                entry_price=close,
                stop_loss=sl,
                target_price=tp,
                quantity=qty,
                strategy_name=self.get_name(),
                strategy_score=85.0,
                explanation=f"ORB Bearish Breakdown below {self.range_minutes}m low ₹{orb_low:.2f}"
            )

        return None
