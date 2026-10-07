"""
Tests for Phase 7 DB persistence models.
Verifies LiveSession, LiveSignalRecord, LivePositionRecord tables
are created by SQLAlchemy and CRUD operations work correctly.
"""
import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import LiveSession, LiveSignalRecord, LivePositionRecord


@pytest.fixture(scope="module")
def test_db():
    """In-memory SQLite database for testing Phase 7 persistence models."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


class TestLiveSession:
    def test_create_live_session(self, test_db):
        session = LiveSession(
            session_date="2026-08-28",
            provider_name="ZERODHA_KITE",
            is_mock=False,
            total_paper_trades=0,
            net_realized_pnl=0.0,
            reality_gap_verdict="INSUFFICIENT_LIVE_DATA"
        )
        test_db.add(session)
        test_db.commit()
        test_db.refresh(session)
        assert session.id is not None
        assert session.session_date == "2026-08-28"
        assert session.is_mock is False

    def test_update_live_session(self, test_db):
        session = test_db.query(LiveSession).filter_by(session_date="2026-08-28").first()
        assert session is not None
        session.total_paper_trades = 5
        session.net_realized_pnl = 1200.50
        session.reality_gap_verdict = "CONTINUE_PAPER_TRADING"
        test_db.commit()
        test_db.refresh(session)
        assert session.total_paper_trades == 5
        assert session.reality_gap_verdict == "CONTINUE_PAPER_TRADING"


class TestLiveSignalRecord:
    def test_create_signal_record(self, test_db):
        record = LiveSignalRecord(
            session_id=1,
            symbol="RELIANCE",
            direction="BUY",
            entry_price=2950.0,
            stop_loss=2906.5,
            target_price=3080.0,
            quantity=3,
            strategy_name="VWAP_EMA_MOMENTUM_V1",
            strategy_score=78.5,
            status="PENDING",
            risk_reward_ratio=3.0,
            market_regime="BULLISH",
            data_freshness_seconds=1.2,
            reason="EMA crossover detected",
            indicator_snapshot={"ema_fast": 2951.0, "ema_slow": 2940.0}
        )
        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)
        assert record.id is not None
        assert record.symbol == "RELIANCE"
        assert record.status == "PENDING"

    def test_update_signal_status(self, test_db):
        record = test_db.query(LiveSignalRecord).filter_by(symbol="RELIANCE").first()
        record.status = "EXECUTED"
        test_db.commit()
        test_db.refresh(record)
        assert record.status == "EXECUTED"

    def test_query_by_symbol(self, test_db):
        records = test_db.query(LiveSignalRecord).filter_by(symbol="RELIANCE").all()
        assert len(records) >= 1


class TestLivePositionRecord:
    def test_create_position_record(self, test_db):
        record = LivePositionRecord(
            session_id=1,
            symbol="RELIANCE",
            side="BUY",
            quantity=3,
            entry_price=2951.0,
            current_price=2975.0,
            stop_loss=2906.5,
            target_price=3080.0,
            trailing_stop=2920.0,
            unrealized_pnl=72.0,
            unrealized_pnl_pct=0.81,
            status="OPEN",
            slippage_incurred=2.5,
            statutory_charges=18.0
        )
        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)
        assert record.id is not None
        assert record.status == "OPEN"
        assert record.symbol == "RELIANCE"

    def test_close_position_record(self, test_db):
        record = test_db.query(LivePositionRecord).filter_by(symbol="RELIANCE").first()
        record.status = "CLOSED"
        record.exit_price = 3050.0
        record.exit_reason = "TARGET_HIT"
        record.net_realized_pnl = 270.0
        record.closed_at = datetime.datetime.now()
        test_db.commit()
        test_db.refresh(record)
        assert record.status == "CLOSED"
        assert record.exit_reason == "TARGET_HIT"
        assert record.net_realized_pnl == 270.0

    def test_query_open_positions(self, test_db):
        # Add a fresh open position
        open_pos = LivePositionRecord(
            session_id=1, symbol="TCS", side="BUY", quantity=1,
            entry_price=4100.0, current_price=4120.0, stop_loss=4050.0,
            target_price=4250.0, status="OPEN", slippage_incurred=1.0,
            statutory_charges=12.0
        )
        test_db.add(open_pos)
        test_db.commit()
        open_positions = test_db.query(LivePositionRecord).filter_by(status="OPEN").all()
        assert len(open_positions) >= 1
        assert all(p.status == "OPEN" for p in open_positions)
