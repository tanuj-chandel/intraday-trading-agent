from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import TradeSignal
from app.schemas.schemas import TradeSignalResponse, SignalApprovalRequest
from app.data.mock_provider import MockMarketDataProvider
from app.strategies.vwap_ema_momentum import VWAPEMAMomentumStrategy
from app.risk.manager import RiskManager
from app.paper_trading.engine import PaperTradingEngine

router = APIRouter()
market_data_provider = MockMarketDataProvider()
strategy = VWAPEMAMomentumStrategy()
risk_manager = RiskManager()
paper_engine = PaperTradingEngine(risk_manager)

@router.get("", response_model=List[TradeSignalResponse])
def get_signals(
    status: str = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(TradeSignal)
    if status:
        query = query.filter(TradeSignal.status == status)
    return query.order_by(TradeSignal.timestamp.desc()).limit(limit).all()

@router.post("/generate", response_model=List[TradeSignalResponse])
async def generate_strategy_signals(db: Session = Depends(get_db)):
    """
    Evaluates trading strategy across the universe and saves candidate signals in PENDING state.
    """
    universe = await market_data_provider.get_universe()
    created_signals = []
    
    for stock in universe:
        candles = await market_data_provider.get_candles(stock.symbol, limit=60)
        signal_create = strategy.evaluate(stock.symbol, candles)
        if signal_create:
            risk_per_share = abs(signal_create.entry_price - signal_create.stop_loss)
            reward_per_share = abs(signal_create.target_price - signal_create.entry_price)
            rr = round(reward_per_share / (risk_per_share + 1e-10), 2)
            
            sig_model = TradeSignal(
                symbol=signal_create.symbol,
                direction=signal_create.direction,
                entry_price=signal_create.entry_price,
                stop_loss=signal_create.stop_loss,
                target_price=signal_create.target_price,
                quantity=signal_create.quantity,
                risk_amount=round(risk_per_share * signal_create.quantity, 2),
                reward_amount=round(reward_per_share * signal_create.quantity, 2),
                risk_reward_ratio=rr,
                strategy_name=signal_create.strategy_name,
                strategy_score=signal_create.strategy_score,
                status="PENDING",
                explanation=signal_create.explanation
            )
            db.add(sig_model)
            created_signals.append(sig_model)

    db.commit()
    for s in created_signals:
        db.refresh(s)
    return created_signals

@router.post("/{signal_id}/approve")
def approve_signal(
    signal_id: int,
    db: Session = Depends(get_db)
):
    sig = db.query(TradeSignal).filter(TradeSignal.id == signal_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Idempotent guard: if already processed, return safe status
    if sig.status in ("EXECUTED", "REJECTED", "EXPIRED", "CANCELLED"):
        return {
            "success": False,
            "message": f"Signal #{signal_id} has already been processed (status={sig.status}). Duplicate action ignored.",
            "status": sig.status
        }
        
    sig.status = "APPROVED"
    db.commit()
    
    # Automatically execute approved signal into paper positions
    res = paper_engine.execute_signal(db, signal_id)
    return res

@router.post("/{signal_id}/reject")
def reject_signal(
    signal_id: int,
    req: SignalApprovalRequest,
    db: Session = Depends(get_db)
):
    sig = db.query(TradeSignal).filter(TradeSignal.id == signal_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="Signal not found")
        
    sig.status = "REJECTED"
    sig.reject_reason = req.rejection_reason or "Manually rejected by operator"
    db.commit()
    return {"message": "Signal rejected", "signal_id": signal_id, "reject_reason": sig.reject_reason}
