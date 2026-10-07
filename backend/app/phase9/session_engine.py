"""
Phase 9 — Paper Trading Session Engine

Manages persistent trading sessions with strict single-date boundary enforcement.
Tracks session metrics, accounting (P&L, costs, slippage), and operational events.
Never mixes data across trading dates.
"""
import datetime
import threading
from typing import Dict, List, Optional, Any
from app.core.database import SessionLocal
from app.models.models import Phase9Session
import pytz

IST = pytz.timezone("Asia/Kolkata")


class Phase9SessionEngine:
    """
    Coordinates active paper trading sessions for Phase 9.
    Thread-safe session state cache with best-effort DB persistence.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._active_session: Optional[Dict[str, Any]] = None
        self._session_counter = 1

    def _today_ist(self) -> str:
        return datetime.datetime.now(tz=IST).strftime("%Y-%m-%d")

    def start_session(
        self,
        trading_date: Optional[str] = None,
        provider: str = "ZERODHA_KITE",
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Start a new paper trading session for the given date.
        Closes any existing active session before starting a new one.
        """
        with self._lock:
            date_str = trading_date or self._today_ist()
            now = datetime.datetime.now(tz=IST)

            # If an active session exists for a different date, close it
            if self._active_session and self._active_session.get("status") == "ACTIVE":
                if self._active_session.get("trading_date") != date_str:
                    self._close_session_unlocked(reason="DATE_CHANGED")

            # Generate unique session ID
            sess_id = f"SESS-{date_str}-{self._session_counter:03d}"
            self._session_counter += 1

            session_data = {
                "session_id": sess_id,
                "trading_date": date_str,
                "market_open_time": now.isoformat(),
                "market_close_time": None,
                "provider": provider,
                "status": "ACTIVE",
                "symbols_monitored": symbols or ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "KOTAKBANK"],
                "valid_ticks": 0,
                "rejected_ticks": 0,
                "generated_signals": 0,
                "approved_signals": 0,
                "rejected_signals": 0,
                "executed_paper_trades": 0,
                "exits": 0,
                "gross_pnl": 0.0,
                "transaction_costs": 0.0,
                "slippage": 0.0,
                "net_pnl": 0.0,
                "max_drawdown": 0.0,
                "daily_loss": 0.0,
                "kill_switch_events": 0,
                "data_quality_incidents": 0,
                "running_peak_pnl": 0.0,
            }

            self._active_session = session_data

            # Persist to DB
            self._persist_session(session_data, is_new=True)

            return session_data.copy()

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Retrieve current active session or auto-initialize if market is active."""
        with self._lock:
            if not self._active_session:
                # Try loading latest active session from DB
                loaded = self._load_latest_active_from_db()
                if loaded:
                    self._active_session = loaded
                else:
                    # Auto-initialize session for today
                    return self.start_session()
            return self._active_session.copy()

    def close_session(self, reason: str = "MANUAL_CLOSE") -> Optional[Dict[str, Any]]:
        """Close the currently active paper trading session."""
        with self._lock:
            return self._close_session_unlocked(reason)

    def _close_session_unlocked(self, reason: str = "MANUAL_CLOSE") -> Optional[Dict[str, Any]]:
        if not self._active_session:
            return None

        now = datetime.datetime.now(tz=IST)
        self._active_session["status"] = "CLOSED"
        self._active_session["market_close_time"] = now.isoformat()
        self._active_session["close_reason"] = reason

        self._persist_session(self._active_session, is_new=False)
        closed_copy = self._active_session.copy()
        self._active_session = None
        return closed_copy

    def record_tick(self, is_valid: bool, date_str: Optional[str] = None):
        """Record valid or rejected tick in active session, enforcing date boundary."""
        with self._lock:
            if not self._active_session or self._active_session.get("status") != "ACTIVE":
                return
            # Strict date boundary check
            tick_date = date_str or self._today_ist()
            if tick_date != self._active_session["trading_date"]:
                # Cross-date tick ignored or recorded as incident
                self._active_session["data_quality_incidents"] += 1
                return

            if is_valid:
                self._active_session["valid_ticks"] += 1
            else:
                self._active_session["rejected_ticks"] += 1

    def record_signal_generated(self):
        with self._lock:
            if self._active_session and self._active_session.get("status") == "ACTIVE":
                self._active_session["generated_signals"] += 1

    def record_signal_decision(self, approved: bool):
        with self._lock:
            if self._active_session and self._active_session.get("status") == "ACTIVE":
                if approved:
                    self._active_session["approved_signals"] += 1
                else:
                    self._active_session["rejected_signals"] += 1

    def record_trade_opened(self, slippage: float = 0.0, charges: float = 0.0):
        with self._lock:
            if self._active_session and self._active_session.get("status") == "ACTIVE":
                self._active_session["executed_paper_trades"] += 1
                self._active_session["slippage"] += slippage
                self._active_session["transaction_costs"] += charges

    def record_trade_closed(self, gross_pnl: float, exit_slippage: float, exit_charges: float):
        with self._lock:
            if not self._active_session or self._active_session.get("status") != "ACTIVE":
                return

            self._active_session["exits"] += 1
            self._active_session["gross_pnl"] += gross_pnl
            self._active_session["slippage"] += exit_slippage
            self._active_session["transaction_costs"] += exit_charges

            # Formula: GROSS P&L - TRANSACTION COST - SLIPPAGE = NET P&L
            net = (
                self._active_session["gross_pnl"]
                - self._active_session["transaction_costs"]
                - self._active_session["slippage"]
            )
            self._active_session["net_pnl"] = round(net, 2)

            # Track daily loss and drawdown
            if net < 0:
                self._active_session["daily_loss"] = abs(round(net, 2))

            peak = self._active_session.get("running_peak_pnl", 0.0)
            if net > peak:
                self._active_session["running_peak_pnl"] = net
                peak = net
            dd = max(0.0, peak - net)
            if dd > self._active_session.get("max_drawdown", 0.0):
                self._active_session["max_drawdown"] = round(dd, 2)

            # Persist update
            self._persist_session(self._active_session, is_new=False)

    def record_kill_switch_event(self):
        with self._lock:
            if self._active_session and self._active_session.get("status") == "ACTIVE":
                self._active_session["kill_switch_events"] += 1

    def record_data_quality_incident(self):
        with self._lock:
            if self._active_session and self._active_session.get("status") == "ACTIVE":
                self._active_session["data_quality_incidents"] += 1

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List historic sessions from database."""
        db = SessionLocal()
        try:
            records = (
                db.query(Phase9Session)
                .order_by(Phase9Session.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "session_id": r.session_id,
                    "trading_date": r.trading_date,
                    "market_open_time": r.market_open_time.isoformat() if r.market_open_time else None,
                    "market_close_time": r.market_close_time.isoformat() if r.market_close_time else None,
                    "provider": r.provider,
                    "status": r.status,
                    "symbols_monitored": r.symbols_monitored,
                    "valid_ticks": r.valid_ticks,
                    "rejected_ticks": r.rejected_ticks,
                    "generated_signals": r.generated_signals,
                    "approved_signals": r.approved_signals,
                    "rejected_signals": r.rejected_signals,
                    "executed_paper_trades": r.executed_paper_trades,
                    "exits": r.exits,
                    "gross_pnl": r.gross_pnl,
                    "transaction_costs": r.transaction_costs,
                    "slippage": r.slippage,
                    "net_pnl": r.net_pnl,
                    "max_drawdown": r.max_drawdown,
                    "daily_loss": r.daily_loss,
                    "kill_switch_events": r.kill_switch_events,
                    "data_quality_incidents": r.data_quality_incidents,
                }
                for r in records
            ]
        except Exception:
            return []
        finally:
            db.close()

    def _persist_session(self, data: Dict[str, Any], is_new: bool = False):
        """Save session state to DB (best-effort, never blocks trading)."""
        db = SessionLocal()
        try:
            if is_new:
                sess = Phase9Session(
                    session_id=data["session_id"],
                    trading_date=data["trading_date"],
                    market_open_time=datetime.datetime.now(),
                    provider=data["provider"],
                    status=data["status"],
                    symbols_monitored=data.get("symbols_monitored", []),
                    valid_ticks=data["valid_ticks"],
                    rejected_ticks=data["rejected_ticks"],
                    generated_signals=data["generated_signals"],
                    approved_signals=data["approved_signals"],
                    rejected_signals=data["rejected_signals"],
                    executed_paper_trades=data["executed_paper_trades"],
                    exits=data["exits"],
                    gross_pnl=data["gross_pnl"],
                    transaction_costs=data["transaction_costs"],
                    slippage=data["slippage"],
                    net_pnl=data["net_pnl"],
                    max_drawdown=data["max_drawdown"],
                    daily_loss=data["daily_loss"],
                    kill_switch_events=data["kill_switch_events"],
                    data_quality_incidents=data["data_quality_incidents"],
                )
                db.add(sess)
            else:
                sess = (
                    db.query(Phase9Session)
                    .filter(Phase9Session.session_id == data["session_id"])
                    .first()
                )
                if sess:
                    sess.status = data["status"]
                    if data.get("market_close_time"):
                        sess.market_close_time = datetime.datetime.now()
                    sess.valid_ticks = data["valid_ticks"]
                    sess.rejected_ticks = data["rejected_ticks"]
                    sess.generated_signals = data["generated_signals"]
                    sess.approved_signals = data["approved_signals"]
                    sess.rejected_signals = data["rejected_signals"]
                    sess.executed_paper_trades = data["executed_paper_trades"]
                    sess.exits = data["exits"]
                    sess.gross_pnl = data["gross_pnl"]
                    sess.transaction_costs = data["transaction_costs"]
                    sess.slippage = data["slippage"]
                    sess.net_pnl = data["net_pnl"]
                    sess.max_drawdown = data["max_drawdown"]
                    sess.daily_loss = data["daily_loss"]
                    sess.kill_switch_events = data["kill_switch_events"]
                    sess.data_quality_incidents = data["data_quality_incidents"]
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    def _load_latest_active_from_db(self) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            today = self._today_ist()
            record = (
                db.query(Phase9Session)
                .filter(Phase9Session.trading_date == today, Phase9Session.status == "ACTIVE")
                .order_by(Phase9Session.created_at.desc())
                .first()
            )
            if not record:
                return None
            return {
                "session_id": record.session_id,
                "trading_date": record.trading_date,
                "market_open_time": record.market_open_time.isoformat() if record.market_open_time else None,
                "market_close_time": record.market_close_time.isoformat() if record.market_close_time else None,
                "provider": record.provider,
                "status": record.status,
                "symbols_monitored": record.symbols_monitored or [],
                "valid_ticks": record.valid_ticks,
                "rejected_ticks": record.rejected_ticks,
                "generated_signals": record.generated_signals,
                "approved_signals": record.approved_signals,
                "rejected_signals": record.rejected_signals,
                "executed_paper_trades": record.executed_paper_trades,
                "exits": record.exits,
                "gross_pnl": record.gross_pnl,
                "transaction_costs": record.transaction_costs,
                "slippage": record.slippage,
                "net_pnl": record.net_pnl,
                "max_drawdown": record.max_drawdown,
                "daily_loss": record.daily_loss,
                "kill_switch_events": record.kill_switch_events,
                "data_quality_incidents": record.data_quality_incidents,
                "running_peak_pnl": record.net_pnl if record.net_pnl > 0 else 0.0,
            }
        except Exception:
            return None
        finally:
            db.close()


# Global Singleton
phase9_session_engine = Phase9SessionEngine()
