from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.learning.learner import market_learner

router = APIRouter()

@router.get("/summary")
def get_learning_summary(db: Session = Depends(get_db)):
    """
    Returns current Market Knowledge & Adaptive Learning insights,
    including win rate, optimal ATR multipliers, best/caution tickers,
    and recommended stop-loss adjustments.
    """
    summary = market_learner.learn_from_database(db)
    return summary

@router.post("/recalibrate")
def recalibrate_learning(db: Session = Depends(get_db)):
    """
    Manually triggers an immediate learning recalibration cycle.
    """
    summary = market_learner.learn_from_database(db)
    return {"status": "SUCCESS", "message": "Strategy self-analysis recalibrated successfully", "summary": summary}

@router.get("/proposals")
def get_pending_proposals(db: Session = Depends(get_db)):
    """
    Returns list of pending parameter change proposals.
    """
    return market_learner.get_pending_proposals(db)

@router.post("/proposals/{proposal_id}/approve")
def approve_parameter_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """
    Approves a parameter change proposal and applies it to active strategy parameters.
    """
    res = market_learner.approve_proposal(db, proposal_id, approved_by="DASHBOARD")
    return res

@router.post("/proposals/{proposal_id}/reject")
def reject_parameter_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """
    Rejects a parameter change proposal.
    """
    res = market_learner.reject_proposal(db, proposal_id, reason="Dashboard rejected")
    return res

@router.get("/versions")
def get_parameter_versions(db: Session = Depends(get_db)):
    """
    Returns full version history of applied parameter sets.
    """
    return market_learner.get_version_history(db)

@router.post("/rollback")
def rollback_parameter_version(db: Session = Depends(get_db)):
    """
    Rolls back parameters to the previous version in history.
    """
    res = market_learner.rollback_to_previous_version(db, approved_by="DASHBOARD")
    return res
