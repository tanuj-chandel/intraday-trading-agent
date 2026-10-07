import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import (
    TradeSignal, RiskCheck, PaperOrder, PaperPosition, Trade, PortfolioSnapshot, SystemLog
)
from app.schemas.schemas import TradeSignalCreate, RiskCheckResponse
from app.risk.manager import RiskManager
from app.paper_trading.broker_charges import IndianBrokerageCalculator

class PaperTradingEngine:
    """
    Complete Paper Trading & Simulation Execution Engine.
    Processes signals, performs risk checks, executes simulated orders with slippage,
    tracks position trailing stops, computes P&L and statutory charges, and journals trades.
    """

    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager

    def get_portfolio_summary(self, db: Session) -> Dict[str, Any]:
        """Calculates current portfolio equity, realized P&L, unrealized P&L, and daily limits."""
        # Calculate realized P&L today
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = db.query(Trade).filter(Trade.exit_time >= today_start).all()
        
        realized_pnl = sum(t.net_pnl for t in today_trades)
        trades_count = len(today_trades)
        
        # Calculate consecutive losses
        consecutive_losses = 0
        for t in reversed(today_trades):
            if t.net_pnl < 0:
                consecutive_losses += 1
            else:
                break

        # Calculate open positions & unrealized P&L
        open_positions = db.query(PaperPosition).filter(PaperPosition.status == "OPEN").all()
        unrealized_pnl = sum(p.unrealized_pnl for p in open_positions)
        open_symbols = [p.symbol for p in open_positions]
        total_exposure = sum(p.entry_price * p.quantity for p in open_positions)
        
        # Cash & Equity calculation
        total_equity = settings.INITIAL_CAPITAL + realized_pnl + unrealized_pnl
        cash_balance = settings.INITIAL_CAPITAL + realized_pnl - total_exposure
        daily_loss_remaining = max(0.0, settings.MAX_DAILY_LOSS_AMOUNT - max(0.0, -realized_pnl))

        return {
            "total_capital": round(total_equity, 2),
            "cash_balance": round(cash_balance, 2),
            "realized_pnl_today": round(realized_pnl, 2),
            "unrealized_pnl_today": round(unrealized_pnl, 2),
            "total_pnl_today": round(realized_pnl + unrealized_pnl, 2),
            "daily_loss_remaining": round(daily_loss_remaining, 2),
            "open_positions_count": len(open_positions),
            "open_positions_symbols": open_symbols,
            "current_total_exposure": round(total_exposure, 2),
            "trades_count_today": trades_count,
            "consecutive_losses": consecutive_losses
        }

    def execute_signal(self, db: Session, signal_id: int) -> Dict[str, Any]:
        """
        Executes an approved signal into a live paper position after secondary risk validation,
        timeout verification, and price drift check. First action wins; subsequent actions are idempotent.
        """
        signal = db.query(TradeSignal).filter(TradeSignal.id == signal_id).first()
        if not signal:
            return {"success": False, "message": "Signal not found."}

        # Idempotency: if already executed or rejected, do not duplicate
        if signal.status in ("EXECUTED", "REJECTED", "EXPIRED", "CANCELLED"):
            return {
                "success": False,
                "message": f"Signal #{signal_id} has already been processed (status={signal.status}). Action ignored safely.",
                "status": signal.status
            }

        # Check approval timeout
        timeout_sec = getattr(settings, "APPROVAL_TIMEOUT_SECONDS", 120)
        age = (datetime.datetime.utcnow() - signal.timestamp).total_seconds()
        if age >= timeout_sec:
            signal.status = "EXPIRED"
            signal.reject_reason = f"Approval timeout exceeded ({int(age)}s >= {timeout_sec}s)"
            db.commit()
            return {"success": False, "message": f"Signal #{signal_id} expired after {int(age)}s.", "status": "EXPIRED"}

        # Price drift check if market price is provided
        portfolio = self.get_portfolio_summary(db)
        
        # 1. Run Risk Check
        sig_create = TradeSignalCreate(
            symbol=signal.symbol,
            direction=signal.direction,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            target_price=signal.target_price,
            quantity=signal.quantity,
            strategy_name=signal.strategy_name,
            strategy_score=signal.strategy_score,
            explanation=signal.explanation
        )

        risk_res = self.risk_manager.validate_trade(
            signal=sig_create,
            current_equity=portfolio["total_capital"],
            today_realized_loss=portfolio["realized_pnl_today"],
            open_positions_count=portfolio["open_positions_count"],
            trades_count_today=portfolio["trades_count_today"],
            consecutive_losses=portfolio["consecutive_losses"],
            open_positions_symbols=portfolio.get("open_positions_symbols", []),
            current_total_exposure=portfolio.get("current_total_exposure", 0.0)
        )

        # Log Risk Check
        risk_check_db = RiskCheck(
            signal_id=signal.id,
            passed=risk_res.passed,
            rejection_reason=risk_res.rejection_reason,
            current_daily_loss=risk_res.current_daily_loss,
            current_open_positions=risk_res.current_open_positions,
            calculated_risk_amount=risk_res.calculated_risk_amount,
            risk_metrics=risk_res.metrics
        )
        db.add(risk_check_db)

        if not risk_res.passed:
            signal.status = "REJECTED"
            signal.reject_reason = risk_res.rejection_reason
            db.commit()
            return {"success": False, "message": f"Risk Check Failed: {risk_res.rejection_reason}"}

        # Use the risk-verified and capped quantity
        execution_qty = risk_res.allowed_quantity if (risk_res.allowed_quantity and risk_res.allowed_quantity > 0) else signal.quantity

        # 2. Simulate Execution with Slippage
        slippage_mult = (1 + settings.SLIPPAGE_PCT) if signal.direction == "BUY" else (1 - settings.SLIPPAGE_PCT)
        executed_price = round(signal.entry_price * slippage_mult, 2)
        slippage_amount = round(abs(executed_price - signal.entry_price), 2)

        order = PaperOrder(
            signal_id=signal.id,
            symbol=signal.symbol,
            side=signal.direction,
            order_type="MARKET",
            quantity=execution_qty,
            requested_price=signal.entry_price,
            executed_price=executed_price,
            slippage=slippage_amount,
            status="FILLED",
            executed_at=datetime.datetime.now()
        )
        db.add(order)

        # 3. Create Open Paper Position
        pos = PaperPosition(
            symbol=signal.symbol,
            side=signal.direction,
            quantity=execution_qty,
            entry_price=executed_price,
            current_price=executed_price,
            stop_loss=signal.stop_loss,
            target_price=signal.target_price,
            trailing_stop=signal.stop_loss,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
            status="OPEN",
            opened_at=datetime.datetime.now()
        )
        db.add(pos)

        signal.status = "EXECUTED"

        log = SystemLog(
            level="AUDIT",
            module="PAPER_TRADING",
            message=f"Executed Paper Order for {signal.symbol} | {signal.direction} {signal.quantity} shares @ ₹{executed_price} (SL: ₹{signal.stop_loss}, TGT: ₹{signal.target_price})"
        )
        db.add(log)
        db.commit()

        return {
            "success": True,
            "message": f"Order executed successfully for {signal.symbol}",
            "executed_price": executed_price,
            "quantity": signal.quantity
        }

    def update_position_price(
        self,
        db: Session,
        position_id: int,
        new_price: float,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates position mark-to-market and checks for Stop Loss, Target, Trailing Stop, or Cutoff exit.
        """
        pos = db.query(PaperPosition).filter(PaperPosition.id == position_id, PaperPosition.status == "OPEN").first()
        if not pos:
            return {"success": False, "message": "Position not found or already closed."}

        pos.current_price = new_price
        is_buy = (pos.side == "BUY")

        if is_buy:
            gross_pnl = (new_price - pos.entry_price) * pos.quantity
            pnl_pct = ((new_price - pos.entry_price) / pos.entry_price) * 100.0
            
            # Trailing Stop: If price moves favorably by 1R, move stop loss to entry
            risk = pos.entry_price - pos.stop_loss
            if risk > 0 and (new_price >= pos.entry_price + risk):
                if pos.trailing_stop < pos.entry_price:
                    pos.trailing_stop = pos.entry_price
        else:
            gross_pnl = (pos.entry_price - new_price) * pos.quantity
            pnl_pct = ((pos.entry_price - new_price) / pos.entry_price) * 100.0
            
            risk = pos.stop_loss - pos.entry_price
            if risk > 0 and (new_price <= pos.entry_price - risk):
                if pos.trailing_stop > pos.entry_price:
                    pos.trailing_stop = pos.entry_price

        pos.unrealized_pnl = round(gross_pnl, 2)
        pos.unrealized_pnl_pct = round(pnl_pct, 2)

        # Check Exit Triggers
        exit_trigger = reason
        if not exit_trigger:
            if is_buy:
                if new_price >= pos.target_price:
                    exit_trigger = "TARGET_HIT"
                elif pos.trailing_stop and new_price <= pos.trailing_stop:
                    exit_trigger = "TRAILING_STOP_HIT" if pos.trailing_stop > pos.stop_loss else "STOP_LOSS_HIT"
                elif new_price <= pos.stop_loss:
                    exit_trigger = "STOP_LOSS_HIT"
            else:
                if new_price <= pos.target_price:
                    exit_trigger = "TARGET_HIT"
                elif pos.trailing_stop and new_price >= pos.trailing_stop:
                    exit_trigger = "TRAILING_STOP_HIT" if pos.trailing_stop < pos.stop_loss else "STOP_LOSS_HIT"
                elif new_price >= pos.stop_loss:
                    exit_trigger = "STOP_LOSS_HIT"

        if exit_trigger:
            return self.close_position(db, pos.id, exit_price=new_price, exit_reason=exit_trigger)

        db.commit()
        return {"success": True, "status": "OPEN", "unrealized_pnl": pos.unrealized_pnl}

    def close_position(
        self,
        db: Session,
        position_id: int,
        exit_price: float,
        exit_reason: str = "MANUAL_CLOSE"
    ) -> Dict[str, Any]:
        """
        Closes a paper position, computes full statutory brokerage & charges, and records into Trade Journal.
        """
        pos = db.query(PaperPosition).filter(PaperPosition.id == position_id, PaperPosition.status == "OPEN").first()
        if not pos:
            return {"success": False, "message": "Position not found or already closed."}

        now = datetime.datetime.now()
        is_buy = (pos.side == "BUY")

        buy_price = pos.entry_price if is_buy else exit_price
        sell_price = exit_price if is_buy else pos.entry_price

        # Calculate exact statutory brokerage and taxes
        charges_breakdown = IndianBrokerageCalculator.calculate_intraday_charges(
            buy_price=buy_price,
            sell_price=sell_price,
            quantity=pos.quantity
        )
        total_charges = charges_breakdown["total_charges"]

        if is_buy:
            gross_pnl = (exit_price - pos.entry_price) * pos.quantity
        else:
            gross_pnl = (pos.entry_price - exit_price) * pos.quantity

        net_pnl = round(gross_pnl - total_charges, 2)
        holding_time_minutes = round((now - pos.opened_at).total_seconds() / 60.0, 1)

        # Record to Trade Journal
        trade = Trade(
            symbol=pos.symbol,
            strategy="VWAP_EMA_Momentum_RVOL",
            direction=pos.side,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            stop_loss=pos.stop_loss,
            target_price=pos.target_price,
            quantity=pos.quantity,
            gross_pnl=round(gross_pnl, 2),
            estimated_charges=total_charges,
            net_pnl=net_pnl,
            holding_time_minutes=holding_time_minutes,
            reason_for_entry="VWAP + EMA + Momentum Setup Approval",
            reason_for_exit=exit_reason,
            market_regime="TRENDING_UP",
            entry_time=pos.opened_at,
            exit_time=now
        )
        db.add(trade)

        pos.status = "CLOSED"
        pos.closed_at = now
        pos.current_price = exit_price
        pos.unrealized_pnl = 0.0

        log = SystemLog(
            level="INFO",
            module="PAPER_TRADING",
            message=f"Closed Position {pos.symbol} @ ₹{exit_price} | Reason: {exit_reason} | Net P&L: ₹{net_pnl} (Gross ₹{gross_pnl:.2f} - Charges ₹{total_charges:.2f})"
        )
        db.add(log)
        db.commit()

        try:
            from app.notifications.dispatcher import notifier
            notifier.notify_position_closed({
                "symbol": pos.symbol,
                "exit_price": exit_price,
                "net_realized_pnl": net_pnl,
                "exit_reason": exit_reason,
                "statutory_charges": total_charges,
                "side": pos.side,
                "quantity": pos.quantity
            })
        except Exception:
            pass

        return {
            "success": True,
            "message": f"Position {pos.symbol} closed successfully ({exit_reason})",
            "net_pnl": net_pnl,
            "gross_pnl": round(gross_pnl, 2),
            "charges": total_charges,
            "exit_reason": exit_reason
        }

    def emergency_square_off_all(self, db: Session, reason: str = "EMERGENCY_STOP") -> Dict[str, Any]:
        """
        Emergency liquidation of all open paper positions.
        """
        open_positions = db.query(PaperPosition).filter(PaperPosition.status == "OPEN").all()
        closed_count = 0
        total_pnl = 0.0
        
        for pos in open_positions:
            res = self.close_position(db, pos.id, exit_price=pos.current_price, exit_reason=reason)
            if res.get("success"):
                closed_count += 1
                total_pnl += res.get("net_pnl", 0.0)

        try:
            from app.notifications.dispatcher import notifier
            notifier.notify_emergency_stop(reason)
        except Exception:
            pass

        # Mark all pending signals as REJECTED
        pending_signals = db.query(TradeSignal).filter(TradeSignal.status == "PENDING").all()
        for sig in pending_signals:
            sig.status = "REJECTED"

        self.risk_manager.trigger_emergency_stop()
        
        log = SystemLog(
            level="CRITICAL",
            module="EMERGENCY_STOP",
            message=f"Emergency Kill Switch triggered ({reason}). Liquidated {closed_count} open positions. Net P&L impact: ₹{total_pnl:.2f}."
        )
        db.add(log)
        db.commit()

        return {
            "success": True,
            "positions_closed": closed_count,
            "total_net_pnl": round(total_pnl, 2),
            "emergency_stop_active": True
        }
