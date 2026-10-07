import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.models import Trade, ParameterProposal, ParameterVersionHistory
from app.learning.learner import MarketKnowledgeLearner
from app.core.config import settings

@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def create_sample_trades(db, count: int, regime: str = "TRENDING", exit_reason: str = "STOP_LOSS_HIT", net_pnl: float = -100.0, time_hour: int = 10):
    trades = []
    base_time = datetime.datetime(2026, 10, 5, time_hour, 0, 0)
    for i in range(count):
        t = Trade(
            symbol="RELIANCE",
            strategy="VWAP_EMA_MOMENTUM_V1",
            direction="BUY",
            entry_price=2500.0,
            exit_price=2480.0,
            stop_loss=2480.0,
            target_price=2540.0,
            quantity=10,
            gross_pnl=net_pnl,
            estimated_charges=15.0,
            net_pnl=net_pnl,
            holding_time_minutes=25.0,
            reason_for_entry="VWAP break",
            reason_for_exit=exit_reason,
            market_regime=regime,
            score_at_entry=82.0,
            entry_time=base_time - datetime.timedelta(minutes=i * 5),
            exit_time=base_time - datetime.timedelta(minutes=i * 5 - 20)
        )
        db.add(t)
    db.commit()

# ── 1. Minimum Sample Size ───────────────────────────────────────────────────

def test_learner_minimum_sample_size_blocks_parameter_changes(in_memory_db):
    """When sample size is below MIN_TRADES_FOR_LEARNING (100), no proposals are generated."""
    learner = MarketKnowledgeLearner()
    
    # Create only 40 completed trades (< 100)
    create_sample_trades(in_memory_db, count=40, regime="TRENDING", exit_reason="STOP_LOSS_HIT")

    summary = learner.learn_from_database(in_memory_db)
    assert summary["learning_status"] == "INSUFFICIENT_SAMPLE"
    assert summary["sample_met"] is False
    assert summary["total_trades_analyzed"] == 40

    # Ensure no proposals were created in the database
    proposals = in_memory_db.query(ParameterProposal).all()
    assert len(proposals) == 0
    # Parameter remains default
    assert learner.current_atr_sl_multiplier == 1.5

# ── 2. Bounds & Step Limit ───────────────────────────────────────────────────

def test_learner_bounds_and_step_limit(in_memory_db):
    """Each parameter change is at most 0.1, and ATR multiplier stays within [1.3, 2.0]."""
    learner = MarketKnowledgeLearner()
    learner.current_atr_sl_multiplier = 1.95  # Near upper bound

    # Create 110 completed trades with predominantly stop losses in trending regime
    create_sample_trades(in_memory_db, count=80, regime="TRENDING", exit_reason="STOP_LOSS_HIT", net_pnl=-150.0)
    create_sample_trades(in_memory_db, count=30, regime="TRENDING", exit_reason="TARGET_HIT", net_pnl=300.0)

    summary = learner.learn_from_database(in_memory_db)
    assert summary["sample_met"] is True

    # Should create a proposal
    proposals = in_memory_db.query(ParameterProposal).all()
    assert len(proposals) == 1
    prop = proposals[0]

    # Delta must be <= 0.1
    delta = abs(prop.new_value - prop.old_value)
    assert delta <= 0.1001

    # New value must not exceed max bound 2.0
    assert 1.3 <= prop.new_value <= 2.0

# ── 3. Fixed Risk-to-Reward (R:R) ───────────────────────────────────────────

def test_learner_keeps_rr_fixed(in_memory_db):
    """If SL multiplier changes, TP changes proportionally to maintain configured R:R."""
    learner = MarketKnowledgeLearner()
    learner.current_atr_sl_multiplier = 1.5
    target_rr = 2.0

    create_sample_trades(in_memory_db, count=80, regime="TRENDING", exit_reason="STOP_LOSS_HIT", net_pnl=-100.0)
    create_sample_trades(in_memory_db, count=30, regime="TRENDING", exit_reason="TARGET_HIT", net_pnl=200.0)

    learner.learn_from_database(in_memory_db)
    prop = in_memory_db.query(ParameterProposal).first()
    assert prop is not None

    # SL changed from 1.5 to 1.6
    assert prop.old_value == 1.5
    assert prop.new_value == 1.6

    # TP must equal new_sl * target_rr = 1.6 * 2.0 = 3.2
    assert prop.tp_multiplier == 3.2
    assert round(prop.tp_multiplier / prop.new_value, 2) == target_rr

# ── 4. Recommend-Only Mode ───────────────────────────────────────────────────

def test_learner_recommend_only_mode_does_not_auto_apply(in_memory_db):
    """Learner writes proposal to parameter_proposals with status PENDING without auto-applying."""
    learner = MarketKnowledgeLearner()

    create_sample_trades(in_memory_db, count=80, regime="TRENDING", exit_reason="STOP_LOSS_HIT", net_pnl=-100.0)
    create_sample_trades(in_memory_db, count=30, regime="TRENDING", exit_reason="TARGET_HIT", net_pnl=200.0)

    learner.learn_from_database(in_memory_db)

    # Active runtime parameters must remain unchanged
    assert learner.current_atr_sl_multiplier == 1.5
    assert learner.current_atr_tp_multiplier == 3.0

    # Proposal is saved with status PENDING
    prop = in_memory_db.query(ParameterProposal).first()
    assert prop.status == "PENDING"
    assert "Recommend widening ATR SL" in prop.evidence

# ── 5. Approval & Version History ───────────────────────────────────────────

def test_learner_proposal_approval_and_version_history(in_memory_db):
    """Approving proposal updates status to APPLIED, logs version history, and activates parameters."""
    learner = MarketKnowledgeLearner()

    create_sample_trades(in_memory_db, count=80, regime="TRENDING", exit_reason="STOP_LOSS_HIT", net_pnl=-100.0)
    create_sample_trades(in_memory_db, count=30, regime="TRENDING", exit_reason="TARGET_HIT", net_pnl=200.0)

    learner.learn_from_database(in_memory_db)
    prop = in_memory_db.query(ParameterProposal).first()

    # Approve proposal
    res = learner.approve_proposal(in_memory_db, proposal_id=prop.id, approved_by="TELEGRAM")
    assert res["success"] is True
    assert res["version"] == 2
    assert res["new_value"] == 1.6

    # Verify DB state
    updated_prop = in_memory_db.query(ParameterProposal).filter(ParameterProposal.id == prop.id).first()
    assert updated_prop.status == "APPLIED"

    history = in_memory_db.query(ParameterVersionHistory).all()
    assert len(history) == 1
    assert history[0].version_number == 2
    assert history[0].applied_value == 1.6
    assert history[0].approved_by == "TELEGRAM"

    # Runtime learner parameter updated
    assert learner.current_atr_sl_multiplier == 1.6
    assert learner.current_atr_tp_multiplier == 3.2

# ── 6. Single-Command Rollback ───────────────────────────────────────────────

def test_learner_single_command_rollback(in_memory_db):
    """Rollback restores parameters to previous version and records rollback entry."""
    learner = MarketKnowledgeLearner()

    create_sample_trades(in_memory_db, count=80, regime="TRENDING", exit_reason="STOP_LOSS_HIT", net_pnl=-100.0)
    create_sample_trades(in_memory_db, count=30, regime="TRENDING", exit_reason="TARGET_HIT", net_pnl=200.0)

    learner.learn_from_database(in_memory_db)
    prop = in_memory_db.query(ParameterProposal).first()
    learner.approve_proposal(in_memory_db, proposal_id=prop.id, approved_by="TELEGRAM")

    assert learner.current_atr_sl_multiplier == 1.6

    # Execute Rollback
    rollback_res = learner.rollback_to_previous_version(in_memory_db, approved_by="TELEGRAM")
    assert rollback_res["success"] is True
    assert rollback_res["restored_value"] == 1.5
    assert rollback_res["version"] == 3

    # Active parameters restored
    assert learner.current_atr_sl_multiplier == 1.5
    assert learner.current_atr_tp_multiplier == 3.0

    # History contains both application and rollback
    versions = learner.get_version_history(in_memory_db)
    assert len(versions) == 2

# ── 7. Segmentation by Regime and Time of Day ───────────────────────────────

def test_learner_segmentation_separates_trending_and_choppy_days(in_memory_db):
    """Choppy regime losses must be isolated and not corrupt trending regime statistics."""
    learner = MarketKnowledgeLearner()

    # 60 Trending trades (50 wins, 10 losses) -> high win rate
    create_sample_trades(in_memory_db, count=50, regime="TRENDING", exit_reason="TARGET_HIT", net_pnl=500.0, time_hour=10)
    create_sample_trades(in_memory_db, count=10, regime="TRENDING", exit_reason="STOP_LOSS_HIT", net_pnl=-100.0, time_hour=10)

    # 50 Choppy trades (10 wins, 40 losses) -> low win rate
    create_sample_trades(in_memory_db, count=10, regime="CHOPPY", exit_reason="TARGET_HIT", net_pnl=100.0, time_hour=13)
    create_sample_trades(in_memory_db, count=40, regime="CHOPPY", exit_reason="STOP_LOSS_HIT", net_pnl=-200.0, time_hour=13)

    summary = learner.learn_from_database(in_memory_db)
    assert summary["total_trades_analyzed"] == 110

    regimes = summary["regime_segments"]
    assert "TRENDING" in regimes
    assert "CHOPPY" in regimes

    # Trending segment reflects high win rate
    assert regimes["TRENDING"]["win_rate_pct"] > 80.0
    # Choppy segment reflects low win rate
    assert regimes["CHOPPY"]["win_rate_pct"] < 30.0

    # Time segments present
    time_segs = summary["time_segments"]
    assert len(time_segs) > 0
