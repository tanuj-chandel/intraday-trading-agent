import pandas as pd
from typing import Optional
from app.strategies.base import Strategy
from app.schemas.schemas import TradeSignalCreate
from app.technical.indicators import TechnicalAnalysis
from app.core.config import settings

class MeanReversionStrategy(Strategy):
    """
    Intraday Mean Reversion Strategy (RSI Oversold/Overbought + Bollinger Band Reversal).
    Prepared for future activation (disabled by default).
    Monitors mean-reversion setups when price tags lower/upper Bollinger Band with RSI divergence.
    """

    def __init__(self, is_enabled: bool = False, rsi_oversold: float = 30.0, rsi_overbought: float = 70.0):
        super().__init__(is_enabled=is_enabled)
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

    def get_id(self) -> str:
        return "MEAN_REVERSION_BB_RSI_V1"

    def get_name(self) -> str:
        return "Mean_Reversion_BB_RSI"

    def evaluate(
        self,
        symbol: str,
        df: pd.DataFrame,
        account_balance: float = 100000.0,
        risk_per_trade_pct: float = 0.01
    ) -> Optional[TradeSignalCreate]:
        if not self.is_enabled():
            return None

        if len(df) < 30:
            return None

        df_calc = TechnicalAnalysis.compute_all_indicators(df)
        latest = df_calc.iloc[-1]
        close = latest["close"]
        rsi = latest["rsi_14"]
        bb_lower = latest["bb_lower"]
        bb_upper = latest["bb_upper"]
        bb_middle = latest["bb_middle"]

        # Long Mean Reversion: Price touches/pierces lower band with RSI < 30
        if close <= bb_lower and rsi <= self.rsi_oversold:
            sl = round(close * 0.992, 2)
            risk = close - sl
            tp = round(bb_middle, 2)
            if tp <= close:
                return None
            qty = max(1, int((account_balance * risk_per_trade_pct) / risk))
            return TradeSignalCreate(
                symbol=symbol,
                direction="BUY",
                entry_price=close,
                stop_loss=sl,
                target_price=tp,
                quantity=qty,
                strategy_name=self.get_name(),
                strategy_score=80.0,
                explanation=f"Mean Reversion Buy: Price ₹{close:.2f} touched lower BB with RSI={rsi:.1f} oversold"
            )

        # Short Mean Reversion: Price touches/pierces upper band with RSI > 70
        elif close >= bb_upper and rsi >= self.rsi_overbought:
            sl = round(close * 1.008, 2)
            risk = sl - close
            tp = round(bb_middle, 2)
            if tp >= close:
                return None
            qty = max(1, int((account_balance * risk_per_trade_pct) / risk))
            return TradeSignalCreate(
                symbol=symbol,
                direction="SELL",
                entry_price=close,
                stop_loss=sl,
                target_price=tp,
                quantity=qty,
                strategy_name=self.get_name(),
                strategy_score=80.0,
                explanation=f"Mean Reversion Short: Price ₹{close:.2f} touched upper BB with RSI={rsi:.1f} overbought"
            )

        return None
