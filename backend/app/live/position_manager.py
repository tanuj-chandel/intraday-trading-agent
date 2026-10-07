import datetime
from typing import Dict, Any, List, Optional
from app.live.data_types import LivePaperPosition

class LivePositionManager:
    """
    Manages active live paper trading positions:
    - Real-time P&L mark-to-market
    - Dynamic trailing stops
    - Stop-Loss & Target trigger evaluations
    - 15:15 IST mandatory square-off
    """

    def __init__(self, max_daily_loss: float = 15000.0):
        self.max_daily_loss = max_daily_loss
        self._open_positions: Dict[int, LivePaperPosition] = {}
        self._closed_positions: List[LivePaperPosition] = []
        self._today_realized_pnl = 0.0

    def add_position(self, pos: LivePaperPosition):
        self._open_positions[pos.id] = pos

    def update_market_price(self, symbol: str, current_price: float) -> List[LivePaperPosition]:
        exited = []
        for pos in list(self._open_positions.values()):
            if pos.symbol != symbol:
                continue

            pos.current_price = current_price
            if pos.side == "BUY":
                gross = (current_price - pos.entry_price) * pos.quantity
                initial_risk = max(1.0, pos.entry_price - pos.stop_loss)

                # 1. Breakeven Protection: When +0.8R in profit, move stop loss to Entry Price
                if current_price >= pos.entry_price + (0.8 * initial_risk):
                    if not pos.trailing_stop or pos.trailing_stop < pos.entry_price:
                        try:
                            from app.notifications.dispatcher import notifier
                            notifier.notify_breakeven(pos.symbol, pos.entry_price, current_price)
                        except Exception:
                            pass
                    pos.trailing_stop = max(pos.trailing_stop or pos.stop_loss, pos.entry_price)

                # 2. Profit Locking: When +1.5R in profit, lock in at least +0.75R profit
                if current_price >= pos.entry_price + (1.5 * initial_risk):
                    pos.trailing_stop = max(pos.trailing_stop or pos.stop_loss, pos.entry_price + (0.75 * initial_risk))

                # 3. High-Water Trail: Trail 1R behind current peak
                new_trail = current_price - initial_risk
                if new_trail > pos.entry_price:
                    pos.trailing_stop = max(pos.trailing_stop or pos.stop_loss, new_trail)

                effective_sl = pos.trailing_stop or pos.stop_loss
                if current_price <= effective_sl:
                    reason = "TRAILING_STOP_HIT" if pos.trailing_stop and pos.trailing_stop > pos.stop_loss else "STOP_LOSS_HIT"
                    exited.append(self.close_position(pos.id, current_price, reason))
                elif current_price >= pos.target_price:
                    exited.append(self.close_position(pos.id, current_price, "TARGET_HIT"))
            else:  # SELL
                gross = (pos.entry_price - current_price) * pos.quantity
                initial_risk = max(1.0, pos.stop_loss - pos.entry_price)

                # 1. Breakeven Protection: When +0.8R in profit, move stop to Entry Price
                if current_price <= pos.entry_price - (0.8 * initial_risk):
                    pos.trailing_stop = min(pos.trailing_stop or pos.stop_loss, pos.entry_price)

                # 2. Profit Locking: When +1.5R in profit, lock in +0.75R profit
                if current_price <= pos.entry_price - (1.5 * initial_risk):
                    pos.trailing_stop = min(pos.trailing_stop or pos.stop_loss, pos.entry_price - (0.75 * initial_risk))

                # 3. High-Water Trail
                new_trail = current_price + initial_risk
                if new_trail < pos.entry_price:
                    pos.trailing_stop = min(pos.trailing_stop or pos.stop_loss, new_trail)

                effective_sl = pos.trailing_stop or pos.stop_loss
                if current_price >= effective_sl:
                    reason = "TRAILING_STOP_HIT" if pos.trailing_stop and pos.trailing_stop < pos.stop_loss else "STOP_LOSS_HIT"
                    exited.append(self.close_position(pos.id, current_price, reason))
                elif current_price <= pos.target_price:
                    exited.append(self.close_position(pos.id, current_price, "TARGET_HIT"))

            pos.unrealized_pnl = round(gross - pos.statutory_charges, 2)
            invested = pos.entry_price * pos.quantity
            pos.unrealized_pnl_pct = round((pos.unrealized_pnl / invested) * 100.0, 2) if invested > 0 else 0.0

        return exited

    def close_position(self, position_id: int, exit_price: float, reason: str = "MANUAL_CLOSE") -> Optional[LivePaperPosition]:
        pos = self._open_positions.pop(position_id, None)
        if not pos:
            return None

        pos.status = "CLOSED"
        pos.closed_at = datetime.datetime.now()
        pos.exit_price = exit_price
        pos.exit_reason = reason

        if pos.side == "BUY":
            gross = (exit_price - pos.entry_price) * pos.quantity
        else:
            gross = (pos.entry_price - exit_price) * pos.quantity

        pos.net_realized_pnl = round(gross - pos.statutory_charges, 2)
        initial_risk = abs(pos.entry_price - pos.stop_loss)
        if initial_risk > 1e-4:
            pos.achieved_r = round(((exit_price - pos.entry_price) if pos.side == "BUY" else (pos.entry_price - exit_price)) / initial_risk, 2)
        else:
            pos.achieved_r = 0.0

        self._today_realized_pnl += pos.net_realized_pnl
        self._closed_positions.append(pos)

        # Persist full auditable trade with reason log to SQLite DB
        try:
            from app.core.database import SessionLocal
            from app.models.models import Trade
            db = SessionLocal()
            try:
                holding_time = round((pos.closed_at - pos.opened_at).total_seconds() / 60.0, 1) if pos.opened_at else 0.0
                trade_record = Trade(
                    symbol=pos.symbol,
                    strategy=getattr(pos, "strategy_name", "VWAP_EMA_MOMENTUM_V1"),
                    direction=pos.side,
                    entry_price=pos.entry_price,
                    exit_price=exit_price,
                    stop_loss=pos.stop_loss,
                    target_price=pos.target_price,
                    quantity=pos.quantity,
                    gross_pnl=round(gross, 2),
                    estimated_charges=pos.statutory_charges,
                    net_pnl=pos.net_realized_pnl,
                    holding_time_minutes=holding_time,
                    reason_for_entry=getattr(pos, "reason_for_entry", "Technical Setup Approval"),
                    reason_for_exit=pos.exit_reason,
                    market_regime=getattr(pos, "market_regime", "TRENDING"),
                    score_at_entry=getattr(pos, "score_at_entry", 80.0),
                    indicators_snapshot=getattr(pos, "indicators_snapshot", None),
                    news_rationale=getattr(pos, "news_rationale", None),
                    slippage_incurred=getattr(pos, "slippage_incurred", 0.0),
                    achieved_r=pos.achieved_r,
                    entry_time=pos.opened_at or datetime.datetime.now(),
                    exit_time=pos.closed_at
                )
                db.add(trade_record)
                db.commit()
            finally:
                db.close()
        except Exception:
            pass

        try:
            from app.notifications.dispatcher import notifier
            notifier.notify_position_closed(pos.model_dump())
        except Exception:
            pass
        return pos

    def square_off_all_positions(self, current_prices: Dict[str, float], reason: str = "15:15_MANDATORY_SQUARE_OFF") -> List[LivePaperPosition]:
        exited = []
        for pid, pos in list(self._open_positions.items()):
            px = current_prices.get(pos.symbol, pos.current_price)
            closed = self.close_position(pid, px, reason)
            if closed:
                exited.append(closed)
        return exited

    def get_open_positions(self) -> List[LivePaperPosition]:
        return list(self._open_positions.values())

    def get_closed_positions(self) -> List[LivePaperPosition]:
        return self._closed_positions

    def get_portfolio_summary(self) -> Dict[str, Any]:
        unrealized = sum(p.unrealized_pnl for p in self._open_positions.values())
        total_pnl = self._today_realized_pnl + unrealized
        remaining_loss = max(0.0, self.max_daily_loss + total_pnl) if total_pnl < 0 else self.max_daily_loss
        open_symbols = [p.symbol for p in self._open_positions.values()]
        total_exposure = sum(p.entry_price * p.quantity for p in self._open_positions.values())

        return {
            "open_positions_count": len(self._open_positions),
            "open_positions_symbols": open_symbols,
            "current_total_exposure": round(total_exposure, 2),
            "today_realized_pnl": round(self._today_realized_pnl, 2),
            "today_unrealized_pnl": round(unrealized, 2),
            "today_total_pnl": round(total_pnl, 2),
            "daily_loss_remaining": round(remaining_loss, 2),
            "is_kill_switch_triggered": total_pnl <= -self.max_daily_loss
        }
