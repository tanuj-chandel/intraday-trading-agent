import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import TradeSignal, PaperPosition, Trade, RiskCheck, PaperOrder, SystemLog
from app.risk.manager import RiskManager
from app.paper_trading.engine import PaperTradingEngine
from app.paper_trading.broker_charges import IndianBrokerageCalculator

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_brokerage_calculator():
    # Buy 100 shares @ 1000, Sell @ 1020
    charges = IndianBrokerageCalculator.calculate_intraday_charges(buy_price=1000.0, sell_price=1020.0, quantity=100)
    assert charges["total_charges"] > 0
    assert charges["brokerage"] > 0
    assert charges["stt"] > 0
    assert charges["gst"] > 0

def test_paper_trading_execution_and_exit(db_session):
    risk_mgr = RiskManager()
    engine = PaperTradingEngine(risk_mgr)

    # 1. Create a test trade signal within risk limits (exposure 25 * 1000 = 25k < 30k)
    signal = TradeSignal(
        symbol="TATAMOTORS",
        direction="BUY",
        entry_price=1000.0,
        stop_loss=990.0,
        target_price=1025.0,
        quantity=25,
        risk_amount=250.0,
        reward_amount=625.0,
        risk_reward_ratio=2.5,
        strategy_name="VWAP_EMA",
        strategy_score=90.0,
        status="APPROVED",
        explanation="Test Exec"
    )
    db_session.add(signal)
    db_session.commit()
    db_session.refresh(signal)

    # 2. Execute signal
    exec_res = engine.execute_signal(db_session, signal.id)
    assert exec_res["success"] is True

    # 3. Check position is open
    pos = db_session.query(PaperPosition).filter(PaperPosition.symbol == "TATAMOTORS", PaperPosition.status == "OPEN").first()
    assert pos is not None
    assert pos.status == "OPEN"

    # 4. Target hit update
    exit_res = engine.update_position_price(db_session, pos.id, new_price=1030.0)
    assert exit_res["success"] is True
    assert exit_res.get("exit_reason") == "TARGET_HIT"

    # 5. Check Trade Journal created
    trade = db_session.query(Trade).filter(Trade.symbol == "TATAMOTORS").first()
    assert trade is not None
    assert trade.net_pnl > 0
    assert trade.reason_for_exit == "TARGET_HIT"
