from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import PaperPosition
from app.schemas.schemas import PaperPositionResponse
from app.risk.manager import RiskManager
from app.paper_trading.engine import PaperTradingEngine

router = APIRouter()
risk_manager = RiskManager()
paper_engine = PaperTradingEngine(risk_manager)

@router.get("", response_model=List[PaperPositionResponse])
def get_positions(status: str = "OPEN", db: Session = Depends(get_db)):
    query = db.query(PaperPosition)
    if status:
        query = query.filter(PaperPosition.status == status)
    return query.order_by(PaperPosition.opened_at.desc()).all()

@router.post("/{position_id}/close")
def close_position(
    position_id: int,
    db: Session = Depends(get_db)
):
    pos = db.query(PaperPosition).filter(PaperPosition.id == position_id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")
        
    res = paper_engine.close_position(db, position_id, exit_price=pos.current_price, exit_reason="MANUAL_CLOSE")
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/{position_id}/update-price")
def update_position_price(
    position_id: int,
    new_price: float,
    db: Session = Depends(get_db)
):
    res = paper_engine.update_position_price(db, position_id, new_price=new_price)
    return res
