import datetime
from typing import Dict, Any, Optional
from app.live.data_types import LiveSignalItem, LivePaperPosition
from app.backtest.cost_calculator import TransactionCostCalculator

class LivePaperExecutionEngine:
    """
    Executes approved signals in the paper-trading environment.
    Applies realistic bid/ask spread slippage and statutory Indian transaction charges.
    """

    @classmethod
    def execute_paper_order(
        cls,
        signal: LiveSignalItem,
        current_market_price: float,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        position_id: int = 1
    ) -> LivePaperPosition:
        # Determine realistic fill price using dynamic slippage model scaling with spread and liquidity tier
        from app.execution.slippage_model import DynamicSlippageModel
        fill_price, slippage = DynamicSlippageModel.calculate_execution_price(
            symbol=signal.symbol,
            direction=signal.direction,
            market_price=current_market_price,
            bid=bid,
            ask=ask,
            quantity=signal.quantity
        )

        # Estimate round trip charges using baseline SL
        costs = TransactionCostCalculator.calculate_round_trip_costs(
            buy_price=fill_price,
            sell_price=signal.target_price if signal.direction == "BUY" else signal.stop_loss,
            quantity=signal.quantity
        )

        return LivePaperPosition(
            id=position_id,
            symbol=signal.symbol,
            side=signal.direction,
            quantity=signal.quantity,
            entry_price=fill_price,
            current_price=fill_price,
            stop_loss=signal.stop_loss,
            target_price=signal.target_price,
            trailing_stop=signal.stop_loss,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
            status="OPEN",
            slippage_incurred=round(slippage, 2),
            statutory_charges=round(costs["total_charges"], 2),
            opened_at=datetime.datetime.now(),
            strategy_name=getattr(signal, "strategy_name", "VWAP_EMA_MOMENTUM_V1"),
            score_at_entry=getattr(signal, "strategy_score", 0.0),
            market_regime=getattr(signal, "market_regime", "TRENDING"),
            reason_for_entry=getattr(signal, "reason", "Signal Approved"),
            indicators_snapshot=getattr(signal, "indicator_snapshot", None),
            news_rationale=(getattr(signal, "indicator_snapshot", None) or {}).get("news")
        )
