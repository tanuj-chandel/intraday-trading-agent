from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.risk.manager import RiskManager
from app.paper_trading.engine import PaperTradingEngine

router = APIRouter()
risk_manager = RiskManager()
paper_engine = PaperTradingEngine(risk_manager)

@router.post("/start")
def start_paper_trading():
    settings.IS_PAPER_TRADING = True
    settings.EMERGENCY_STOP_TRIGGERED = False
    risk_manager.reset_emergency_stop()
    return {
        "status": "active",
        "mode": "PAPER_TRADING",
        "message": "Paper Trading engine started successfully."
    }

@router.post("/stop")
def stop_paper_trading(db: Session = Depends(get_db)):
    settings.IS_PAPER_TRADING = False
    return {
        "status": "paused",
        "mode": "PAPER_TRADING_PAUSED",
        "message": "Paper Trading engine paused. Active positions remain tracked."
    }
