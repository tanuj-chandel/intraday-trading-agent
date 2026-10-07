from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
from app.schemas.schemas import TradeSignalCreate

class Strategy(ABC):
    """
    Abstract Strategy Interface.
    All strategies analyze market candles and output actionable signals with complete rationale.
    Supports individual performance tracking and toggle state.
    """

    def __init__(self, is_enabled: bool = True):
        self._is_enabled = is_enabled
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.total_pnl: float = 0.0

    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    def is_enabled(self) -> bool:
        return self._is_enabled

    def set_enabled(self, enabled: bool):
        self._is_enabled = enabled

    @abstractmethod
    def evaluate(
        self,
        symbol: str,
        df: pd.DataFrame,
        account_balance: float = 100000.0,
        risk_per_trade_pct: float = 0.01
    ) -> Optional[TradeSignalCreate]:
        pass

    def record_trade_result(self, pnl: float, won: bool):
        self.total_trades += 1
        if won:
            self.winning_trades += 1
        self.total_pnl += pnl

    def get_performance_summary(self) -> Dict[str, Any]:
        win_rate = (self.winning_trades / self.total_trades * 100.0) if self.total_trades > 0 else 0.0
        return {
            "strategy_id": self.get_id(),
            "strategy_name": self.get_name(),
            "is_enabled": self.is_enabled(),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate_pct": round(win_rate, 2),
            "total_pnl": round(self.total_pnl, 2)
        }
