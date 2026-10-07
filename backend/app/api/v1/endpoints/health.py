from fastapi import APIRouter
import datetime
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mode": "PAPER_TRADING_ONLY",
        "emergency_stop_triggered": settings.EMERGENCY_STOP_TRIGGERED,
        "timestamp": datetime.datetime.now().isoformat()
    }
