"""
Phase 9 — Paper Execution Realism & Regulatory Cost Engine

Enforces the absolute accounting equation:
GROSS P&L − TRANSACTION COST − SLIPPAGE = NET P&L

Models realistic fill prices with configurable bid/ask spread slippage and latency.
Calculates all Indian statutory and broker charges (NSE Intraday Equities).
"""
import datetime
from typing import Dict, Any, Optional, Tuple, List
from app.core.database import SessionLocal
from app.models.models import Phase9TradeEvent
import pytz

IST = pytz.timezone("Asia/Kolkata")


class Phase9CostCalculator:
    """
    Computes precise statutory charges for NSE Intraday Equity trades:
    - Brokerage: ₹20 flat per executed order
    - STT: 0.025% on sell side turnover
    - Exchange Transaction Charges: 0.00345% on total turnover
    - SEBI Turnover Fee: ₹10 per crore (0.0001%)
    - GST: 18% on (brokerage + exchange charges)
    - Stamp Duty: 0.003% on buy side turnover
    """

    BROKERAGE_PER_ORDER = 20.0
    STT_SELL_RATE = 0.00025          # 0.025% on sell turnover
    EXCHANGE_TURNOVER_RATE = 0.0000345 # 0.00345%
    SEBI_RATE = 0.000001              # ₹10 per crore = 0.0001%
    GST_RATE = 0.18                   # 18% on (brokerage + exchange)
    STAMP_DUTY_BUY_RATE = 0.00003     # 0.003% on buy turnover

    @classmethod
    def calculate_charges(
        cls,
        buy_price: float,
        sell_price: float,
        quantity: int
    ) -> Dict[str, float]:
        buy_turnover = buy_price * quantity
        sell_turnover = sell_price * quantity
        total_turnover = buy_turnover + sell_turnover

        brokerage = cls.BROKERAGE_PER_ORDER * 2.0  # Entry + Exit
        stt = sell_turnover * cls.STT_SELL_RATE
        exchange_charges = total_turnover * cls.EXCHANGE_TURNOVER_RATE
        sebi_charges = total_turnover * cls.SEBI_RATE
        gst = (brokerage + exchange_charges) * cls.GST_RATE
        stamp_duty = buy_turnover * cls.STAMP_DUTY_BUY_RATE

        total_cost = round(brokerage + stt + exchange_charges + sebi_charges + gst + stamp_duty, 2)

        return {
            "brokerage": round(brokerage, 2),
            "stt": round(stt, 2),
            "exchange_charges": round(exchange_charges, 2),
            "sebi_charges": round(sebi_charges, 4),
            "gst": round(gst, 2),
            "stamp_duty": round(stamp_duty, 2),
            "total_cost": total_cost,
        }


class Phase9ExecutionEngine:
    """
    Simulates realistic paper executions with bid/ask spread slippage,
    cost attribution, and excursions.
    """

    _trade_counter = 0

    @classmethod
    def simulate_entry_fill(
        cls,
        direction: str,
        intended_price: float,
        bid: float = 0.0,
        ask: float = 0.0,
        spread_bps: float = 2.0
    ) -> Tuple[float, float]:
        """
        Determine fill price and entry slippage.
        Buys fill at ask (or intended + spread).
        Sells fill at bid (or intended - spread).
        """
        intended = float(intended_price)
        half_spread = (intended * (spread_bps / 10000.0))

        if direction.upper() == "BUY":
            fill_price = ask if ask > intended else (intended + half_spread)
            slippage = max(0.0, fill_price - intended)
        else:
            fill_price = bid if (bid > 0 and bid < intended) else (intended - half_spread)
            slippage = max(0.0, intended - fill_price)

        return round(fill_price, 2), round(slippage, 2)

    @classmethod
    def simulate_exit_fill(
        cls,
        direction: str,
        intended_price: float,
        bid: float = 0.0,
        ask: float = 0.0,
        spread_bps: float = 2.0
    ) -> Tuple[float, float]:
        """
        Determine exit fill price and exit slippage.
        Closing a BUY fills at bid. Closing a SELL fills at ask.
        """
        intended = float(intended_price)
        half_spread = (intended * (spread_bps / 10000.0))

        if direction.upper() == "BUY":  # Exiting a buy position means selling
            fill_price = bid if (bid > 0 and bid < intended) else (intended - half_spread)
            slippage = max(0.0, intended - fill_price)
        else:  # Exiting a sell position means buying
            fill_price = ask if ask > intended else (intended + half_spread)
            slippage = max(0.0, fill_price - intended)

        return round(fill_price, 2), round(slippage, 2)

    @classmethod
    def compute_trade_pnl(
        cls,
        direction: str,
        intended_entry: float,
        fill_entry: float,
        intended_exit: float,
        fill_exit: float,
        quantity: int
    ) -> Dict[str, float]:
        """
        Compute P&L according to: GROSS P&L - TRANSACTION COST - SLIPPAGE = NET P&L.
        """
        qty = int(quantity)

        # Gross P&L based on simulated fill prices
        if direction.upper() == "BUY":
            gross_pnl = (fill_exit - fill_entry) * qty
            buy_price = fill_entry
            sell_price = fill_exit
            entry_slip = max(0.0, fill_entry - intended_entry) * qty
            exit_slip = max(0.0, intended_exit - fill_exit) * qty
        else:
            gross_pnl = (fill_entry - fill_exit) * qty
            buy_price = fill_exit
            sell_price = fill_entry
            entry_slip = max(0.0, intended_entry - fill_entry) * qty
            exit_slip = max(0.0, fill_exit - intended_exit) * qty

        total_slippage = round(entry_slip + exit_slip, 2)

        # Statutory Charges
        charges = Phase9CostCalculator.calculate_charges(buy_price, sell_price, qty)
        total_costs = charges["total_cost"]

        # Final Net P&L (gross minus charges; note fill prices already include execution slippage)
        net_pnl = round(gross_pnl - total_costs, 2)

        return {
            "gross_pnl": round(gross_pnl, 2),
            "entry_slippage": round(entry_slip, 2),
            "exit_slippage": round(exit_slip, 2),
            "total_slippage": total_slippage,
            "charges": charges,
            "total_cost": total_costs,
            "net_pnl": net_pnl,
        }

    @classmethod
    def record_completed_trade(
        cls,
        session_id: str,
        symbol: str,
        direction: str,
        intended_entry_price: float,
        simulated_fill_price: float,
        intended_exit_price: float,
        simulated_exit_price: float,
        quantity: int,
        signal_id: Optional[int] = None,
        latency_ms: float = 0.0,
        mfe: float = 0.0,
        mae: float = 0.0,
        market_regime: str = "UNKNOWN",
        time_of_day_bucket: str = "MID_SESSION",
        holding_minutes: float = 0.0,
        exit_reason: str = "TARGET_HIT",
        data_provenance: str = "LIVE",
        opened_at: Optional[datetime.datetime] = None,
        closed_at: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Record a fully realized paper trade with itemized charges and metrics into the DB.
        """
        cls._trade_counter += 1
        now = datetime.datetime.now(tz=IST)

        pnl_data = cls.compute_trade_pnl(
            direction=direction,
            intended_entry=intended_entry_price,
            fill_entry=simulated_fill_price,
            intended_exit=intended_exit_price,
            fill_exit=simulated_exit_price,
            quantity=quantity
        )

        charges = pnl_data["charges"]

        trade_dict = {
            "trade_id": cls._trade_counter,
            "session_id": session_id,
            "signal_id": signal_id,
            "symbol": symbol,
            "direction": direction.upper(),
            "intended_entry_price": float(intended_entry_price),
            "simulated_fill_price": float(simulated_fill_price),
            "entry_slippage": pnl_data["entry_slippage"],
            "intended_exit_price": float(intended_exit_price),
            "simulated_exit_price": float(simulated_exit_price),
            "exit_slippage": pnl_data["exit_slippage"],
            "latency_ms": float(latency_ms),
            "quantity": int(quantity),
            "brokerage": charges["brokerage"],
            "stt": charges["stt"],
            "gst": charges["gst"],
            "sebi_charges": charges["sebi_charges"],
            "exchange_charges": charges["exchange_charges"],
            "stamp_duty": charges["stamp_duty"],
            "total_cost": charges["total_cost"],
            "gross_pnl": pnl_data["gross_pnl"],
            "net_pnl": pnl_data["net_pnl"],
            "mfe": float(mfe),
            "mae": float(mae),
            "market_regime": market_regime,
            "time_of_day_bucket": time_of_day_bucket,
            "holding_minutes": float(holding_minutes),
            "exit_reason": exit_reason,
            "data_provenance": data_provenance,
            "opened_at": (opened_at or now).isoformat(),
            "closed_at": (closed_at or now).isoformat(),
        }

        # Persist to database
        cls._persist_to_db(trade_dict, opened_at or now, closed_at or now)

        # Notify Session Engine
        from app.phase9.session_engine import phase9_session_engine
        phase9_session_engine.record_trade_closed(
            gross_pnl=pnl_data["gross_pnl"],
            exit_slippage=pnl_data["total_slippage"],
            exit_charges=charges["total_cost"]
        )

        return trade_dict

    @classmethod
    def list_trades(cls, session_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            q = db.query(Phase9TradeEvent)
            if session_id:
                q = q.filter(Phase9TradeEvent.session_id == session_id)
            records = q.order_by(Phase9TradeEvent.closed_at.desc()).limit(limit).all()
            return [
                {
                    "trade_id": r.trade_id,
                    "session_id": r.session_id,
                    "symbol": r.symbol,
                    "direction": r.direction,
                    "intended_entry_price": r.intended_entry_price,
                    "simulated_fill_price": r.simulated_fill_price,
                    "entry_slippage": r.entry_slippage,
                    "intended_exit_price": r.intended_exit_price,
                    "simulated_exit_price": r.simulated_exit_price,
                    "exit_slippage": r.exit_slippage,
                    "quantity": r.quantity,
                    "brokerage": r.brokerage,
                    "stt": r.stt,
                    "gst": r.gst,
                    "sebi_charges": r.sebi_charges,
                    "exchange_charges": r.exchange_charges,
                    "stamp_duty": r.stamp_duty,
                    "total_cost": r.total_cost,
                    "gross_pnl": r.gross_pnl,
                    "net_pnl": r.net_pnl,
                    "mfe": r.mfe,
                    "mae": r.mae,
                    "market_regime": r.market_regime,
                    "time_of_day_bucket": r.time_of_day_bucket,
                    "holding_minutes": r.holding_minutes,
                    "exit_reason": r.exit_reason,
                    "opened_at": r.opened_at.isoformat() if r.opened_at else None,
                    "closed_at": r.closed_at.isoformat() if r.closed_at else None,
                }
                for r in records
            ]
        except Exception:
            return []
        finally:
            db.close()

    @classmethod
    def _persist_to_db(cls, d: Dict[str, Any], opened_dt: datetime.datetime, closed_dt: datetime.datetime):
        db = SessionLocal()
        try:
            te = Phase9TradeEvent(
                trade_id=d["trade_id"],
                session_id=d["session_id"],
                signal_id=d.get("signal_id"),
                symbol=d["symbol"],
                direction=d["direction"],
                intended_entry_price=d["intended_entry_price"],
                simulated_fill_price=d["simulated_fill_price"],
                entry_slippage=d["entry_slippage"],
                intended_exit_price=d["intended_exit_price"],
                simulated_exit_price=d["simulated_exit_price"],
                exit_slippage=d["exit_slippage"],
                latency_ms=d["latency_ms"],
                quantity=d["quantity"],
                brokerage=d["brokerage"],
                stt=d["stt"],
                gst=d["gst"],
                sebi_charges=d["sebi_charges"],
                exchange_charges=d["exchange_charges"],
                stamp_duty=d["stamp_duty"],
                total_cost=d["total_cost"],
                gross_pnl=d["gross_pnl"],
                net_pnl=d["net_pnl"],
                mfe=d["mfe"],
                mae=d["mae"],
                market_regime=d["market_regime"],
                time_of_day_bucket=d["time_of_day_bucket"],
                holding_minutes=d["holding_minutes"],
                exit_reason=d["exit_reason"],
                data_provenance=d["data_provenance"],
                opened_at=opened_dt,
                closed_at=closed_dt,
            )
            db.add(te)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
