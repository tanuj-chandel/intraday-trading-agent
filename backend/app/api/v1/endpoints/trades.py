from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Trade
from app.schemas.schemas import TradeJournalResponse

router = APIRouter()

@router.get("", response_model=List[TradeJournalResponse])
def get_trades(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    return db.query(Trade).order_by(Trade.exit_time.desc()).limit(limit).all()
