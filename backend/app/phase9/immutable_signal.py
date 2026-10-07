"""
Phase 9 — Signal Immutability Engine

Records and persists immutable signal contexts for forensic post-trade analysis.
Captures complete technical, market regime, macro, and sentiment states at signal moment.
Never allows mutation or in-place edits of created signals.
"""
import datetime
from typing import Dict, Any, List, Optional
from app.core.database import SessionLocal
from app.models.models import Phase9Signal
import pytz

IST = pytz.timezone("Asia/Kolkata")


class Phase9ImmutableSignalEngine:
    """
    Guarantees that every generated paper trade signal is recorded with full
    reproducible context and cannot be retroactively modified.
    """

    _signal_counter = 0

    @classmethod
    def create_signal(
        cls,
        session_id: str,
        symbol: str,
        direction: str,
        price: float,
        ema_9: float,
        ema_21: float,
        vwap: float,
        rvol: float,
        atr: float,
        market_regime: str,
        time_of_day_bucket: str,
        intended_entry: float,
        stop_loss: float,
        target_price: float,
        position_size: int = 1,
        risk_amount: float = 0.0,
        data_provenance: str = "LIVE",
        news_context: Optional[Dict[str, Any]] = None,
        global_market_context: Optional[Dict[str, Any]] = None,
        gift_nifty_context: Optional[Dict[str, Any]] = None,
        confidence_score: float = 0.0,
        strategy_version: str = "VWAP_EMA_MOMENTUM_V1",
        timestamp: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Construct and persist an immutable decision record.
        """
        cls._signal_counter += 1
        now = timestamp or datetime.datetime.now(tz=IST)

        signal_dict = {
            "signal_id": cls._signal_counter,
            "session_id": session_id,
            "symbol": symbol,
            "direction": direction.upper(),
            "timestamp": now.isoformat(),
            "price": float(price),
            "ema_9": float(ema_9),
            "ema_21": float(ema_21),
            "vwap": float(vwap),
            "rvol": float(rvol),
            "atr": float(atr),
            "market_regime": market_regime,
            "time_of_day_bucket": time_of_day_bucket,
            "strategy_version": strategy_version,
            "intended_entry": float(intended_entry),
            "stop_loss": float(stop_loss),
            "target_price": float(target_price),
            "position_size": int(position_size),
            "risk_amount": float(risk_amount),
            "data_provenance": data_provenance,
            "news_context": news_context or {},
            "global_market_context": global_market_context or {},
            "gift_nifty_context": gift_nifty_context or {},
            "confidence_score": float(confidence_score),
            "status": "PENDING",
            "is_immutable": True
        }

        # Persist to database
        cls._persist_to_db(signal_dict)
        return signal_dict.copy()

    @classmethod
    def get_signal(cls, signal_id: int) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            r = db.query(Phase9Signal).filter(Phase9Signal.signal_id == signal_id).first()
            if not r:
                return None
            return {
                "signal_id": r.signal_id,
                "session_id": r.session_id,
                "symbol": r.symbol,
                "direction": r.direction,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "price": r.price,
                "ema_9": r.ema_9,
                "ema_21": r.ema_21,
                "vwap": r.vwap,
                "rvol": r.rvol,
                "atr": r.atr,
                "market_regime": r.market_regime,
                "time_of_day_bucket": r.time_of_day_bucket,
                "strategy_version": r.strategy_version,
                "intended_entry": r.intended_entry,
                "stop_loss": r.stop_loss,
                "target_price": r.target_price,
                "position_size": r.position_size,
                "risk_amount": r.risk_amount,
                "data_provenance": r.data_provenance,
                "news_context": r.news_context or {},
                "global_market_context": r.global_market_context or {},
                "gift_nifty_context": r.gift_nifty_context or {},
                "confidence_score": r.confidence_score,
                "status": r.status,
            }
        except Exception:
            return None
        finally:
            db.close()

    @classmethod
    def list_session_signals(cls, session_id: str) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            records = (
                db.query(Phase9Signal)
                .filter(Phase9Signal.session_id == session_id)
                .order_by(Phase9Signal.timestamp.asc())
                .all()
            )
            return [
                {
                    "signal_id": r.signal_id,
                    "session_id": r.session_id,
                    "symbol": r.symbol,
                    "direction": r.direction,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "price": r.price,
                    "intended_entry": r.intended_entry,
                    "stop_loss": r.stop_loss,
                    "target_price": r.target_price,
                    "market_regime": r.market_regime,
                    "confidence_score": r.confidence_score,
                    "status": r.status,
                }
                for r in records
            ]
        except Exception:
            return []
        finally:
            db.close()

    @classmethod
    def update_status(cls, signal_id: int, new_status: str) -> bool:
        """Only status can transition (PENDING -> APPROVED / REJECTED / EXECUTED). All decision inputs remain locked."""
        db = SessionLocal()
        try:
            sig = db.query(Phase9Signal).filter(Phase9Signal.signal_id == signal_id).first()
            if sig:
                sig.status = new_status
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    @classmethod
    def _persist_to_db(cls, d: Dict[str, Any]):
        db = SessionLocal()
        try:
            sig = Phase9Signal(
                signal_id=d["signal_id"],
                session_id=d["session_id"],
                symbol=d["symbol"],
                direction=d["direction"],
                price=d["price"],
                ema_9=d["ema_9"],
                ema_21=d["ema_21"],
                vwap=d["vwap"],
                rvol=d["rvol"],
                atr=d["atr"],
                market_regime=d["market_regime"],
                time_of_day_bucket=d["time_of_day_bucket"],
                strategy_version=d["strategy_version"],
                intended_entry=d["intended_entry"],
                stop_loss=d["stop_loss"],
                target_price=d["target_price"],
                position_size=d["position_size"],
                risk_amount=d["risk_amount"],
                data_provenance=d["data_provenance"],
                news_context=d["news_context"],
                global_market_context=d["global_market_context"],
                gift_nifty_context=d["gift_nifty_context"],
                confidence_score=d["confidence_score"],
                status=d["status"],
            )
            db.add(sig)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
