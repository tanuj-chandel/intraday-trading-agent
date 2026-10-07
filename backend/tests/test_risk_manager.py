import pytest
import datetime
from app.risk.manager import RiskManager
from app.schemas.schemas import TradeSignalCreate

@pytest.fixture
def risk_manager():
    return RiskManager(
        max_risk_per_trade_pct=0.005,  # 0.5%
        max_daily_loss_amount=10000.0, # 2.0% of 500,000
        max_open_positions=5,
        max_trades_per_day=10,
        min_risk_reward_ratio=1.5,
        max_consecutive_losses=3,
        cutoff_time_str="15:15",
        max_position_notional_pct=0.20,
        max_total_exposure_pct=1.00,
        mis_leverage=5.0,
        min_signal_score=70.0,
        max_trades_per_symbol_per_day=2,
        cooldown_after_sl_minutes=45,
        max_positions_per_sector=2
    )

def test_risk_manager_valid_signal(risk_manager):
    signal = TradeSignalCreate(
        symbol="RELIANCE",
        direction="BUY",
        entry_price=1000.0,
        stop_loss=990.0,
        target_price=1025.0,
        quantity=25,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        explanation="Test Valid Signal"
    )
    
    mock_time = datetime.datetime(2026, 1, 1, 10, 30)
    res = risk_manager.validate_trade(
        signal=signal,
        current_equity=500000.0,
        today_realized_loss=0.0,
        open_positions_count=1,
        trades_count_today=2,
        consecutive_losses=0,
        current_time=mock_time
    )
    assert res.passed is True
    assert res.rejection_reason is None
    assert res.allowed_quantity is not None
    assert res.allowed_quantity > 0

def test_risk_manager_huge_qty_capping(risk_manager):
    """
    Test huge-qty case: Price 1000, SL distance 5 (SL 995).
    Without notional cap: Qty by risk = 2500 / 5 = 500 shares.
    Position value would be 500 * 1000 = ₹5,00,000 (100% of capital!).
    With MAX_POSITION_NOTIONAL_PCT = 20%: Max notional = ₹1,00,000 -> Max qty = 100 shares.
    """
    final_qty, metrics = risk_manager.calculate_position_size(
        entry_price=1000.0,
        stop_loss=995.0,
        current_equity=500000.0,
        current_total_exposure=0.0
    )
    assert metrics["qty_risk"] == 500
    assert metrics["qty_notional"] == 100
    assert final_qty == 100  # Capped strictly at 100 shares (20% notional cap)

def test_risk_manager_insufficient_qty_rejection(risk_manager):
    """If equity is tiny so final_qty < 1, reject trade."""
    signal = TradeSignalCreate(
        symbol="MRF",
        direction="BUY",
        entry_price=120000.0,
        stop_loss=119000.0,
        target_price=123000.0,
        quantity=1,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        explanation="MRF test"
    )
    res = risk_manager.validate_trade(
        signal=signal,
        current_equity=1000.0, # Tiny equity, can't afford 1 share of MRF
        today_realized_loss=0.0,
        open_positions_count=0,
        trades_count_today=0
    )
    assert res.passed is False
    assert "0 shares" in res.rejection_reason or "insufficient" in res.rejection_reason.lower()

def test_risk_manager_sector_limit(risk_manager):
    """
    Sector limit test: MAX_POSITIONS_PER_SECTOR = 2.
    If HDFCBANK and ICICIBANK are already open (both Financial Services),
    SBIN (also Financial Services) must be rejected.
    """
    signal = TradeSignalCreate(
        symbol="SBIN",
        direction="BUY",
        entry_price=800.0,
        stop_loss=790.0,
        target_price=830.0,
        quantity=50,
        strategy_name="VWAP_EMA",
        strategy_score=80.0,
        explanation="SBIN test"
    )
    open_symbols = ["HDFCBANK", "ICICIBANK"]  # 2 Financial Services positions already open
    res = risk_manager.validate_trade(
        signal=signal,
        current_equity=500000.0,
        today_realized_loss=0.0,
        open_positions_count=2,
        trades_count_today=2,
        open_positions_symbols=open_symbols
    )
    assert res.passed is False
    assert "Sector limit reached" in res.rejection_reason
    assert "Financial Services" in res.rejection_reason

def test_risk_manager_cooldown_after_sl(risk_manager):
    """
    Test cooldown: COOLDOWN_AFTER_SL_MINUTES = 45.
    If RELIANCE hit SL 20 minutes ago, new signal on RELIANCE must be rejected.
    """
    signal = TradeSignalCreate(
        symbol="RELIANCE",
        direction="BUY",
        entry_price=1000.0,
        stop_loss=990.0,
        target_price=1025.0,
        quantity=25,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        explanation="RELIANCE retry"
    )
    now = datetime.datetime(2026, 1, 1, 12, 0)
    last_sl_time = datetime.datetime(2026, 1, 1, 11, 40) # 20 mins ago (< 45 mins)
    
    res = risk_manager.validate_trade(
        signal=signal,
        current_equity=500000.0,
        today_realized_loss=0.0,
        open_positions_count=0,
        trades_count_today=1,
        current_time=now,
        symbol_last_sl_time=last_sl_time
    )
    assert res.passed is False
    assert "cooldown" in res.rejection_reason.lower()

def test_risk_manager_per_symbol_cap(risk_manager):
    """
    Test per-symbol daily cap: MAX_TRADES_PER_SYMBOL_PER_DAY = 2.
    If 2 trades on INFY already taken today, 3rd trade on INFY must be rejected.
    """
    signal = TradeSignalCreate(
        symbol="INFY",
        direction="BUY",
        entry_price=1500.0,
        stop_loss=1485.0,
        target_price=1540.0,
        quantity=20,
        strategy_name="VWAP_EMA",
        strategy_score=80.0,
        explanation="INFY 3rd attempt"
    )
    res = risk_manager.validate_trade(
        signal=signal,
        current_equity=500000.0,
        today_realized_loss=0.0,
        open_positions_count=0,
        trades_count_today=2,
        symbol_today_trades=2 # Cap reached
    )
    assert res.passed is False
    assert "Max daily trades for symbol" in res.rejection_reason

def test_risk_manager_daily_loss_floor_trigger(risk_manager):
    """
    Test daily loss floor: MAX_DAILY_LOSS_AMOUNT = 10,000 (2% of 500,000).
    If realized loss is -10,500, reject and lock trades for today.
    """
    signal = TradeSignalCreate(
        symbol="TCS",
        direction="BUY",
        entry_price=3500.0,
        stop_loss=3470.0,
        target_price=3600.0,
        quantity=10,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        explanation="TCS setup"
    )
    res = risk_manager.validate_trade(
        signal=signal,
        current_equity=489500.0,
        today_realized_loss=-10500.0, # Breached 10,000 loss floor
        open_positions_count=0,
        trades_count_today=3
    )
    assert res.passed is False
    assert "Max daily loss limit breached" in res.rejection_reason

def test_risk_manager_min_signal_score(risk_manager):
    """Signals below MIN_SIGNAL_SCORE (70.0) must be rejected."""
    signal = TradeSignalCreate(
        symbol="TCS",
        direction="BUY",
        entry_price=3500.0,
        stop_loss=3470.0,
        target_price=3600.0,
        quantity=10,
        strategy_name="VWAP_EMA",
        strategy_score=65.0, # Below 70.0
        explanation="Weak signal"
    )
    res = risk_manager.validate_trade(
        signal=signal,
        current_equity=500000.0,
        today_realized_loss=0.0,
        open_positions_count=0,
        trades_count_today=0
    )
    assert res.passed is False
    assert "below minimum required threshold" in res.rejection_reason

def test_risk_manager_emergency_stop(risk_manager):
    risk_manager.trigger_emergency_stop()
    signal = TradeSignalCreate(
        symbol="RELIANCE",
        direction="BUY",
        entry_price=1000.0,
        stop_loss=990.0,
        target_price=1025.0,
        quantity=25,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        explanation="Test Signal"
    )
    res = risk_manager.validate_trade(
        signal=signal,
        current_equity=500000.0,
        today_realized_loss=0.0,
        open_positions_count=0,
        trades_count_today=0
    )
    assert res.passed is False
    assert "Emergency Stop" in res.rejection_reason
