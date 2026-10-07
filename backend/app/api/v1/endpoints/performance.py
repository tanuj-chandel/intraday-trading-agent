from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.analytics.performance import PerformanceEngine
from app.schemas.schemas import PerformanceMetricsResponse

router = APIRouter()

@router.get("", response_model=PerformanceMetricsResponse)
def get_performance(db: Session = Depends(get_db)):
    return PerformanceEngine.calculate_metrics(db)
