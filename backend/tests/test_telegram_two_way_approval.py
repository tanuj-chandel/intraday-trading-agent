import pytest
import datetime
from unittest.mock import MagicMock, patch
from app.notifications.telegram_bot import TelegramNotifier
from app.live.streamer import live_streamer
from app.live.data_types import LiveCandle, LiveTick

@pytest.fixture
def mock_notifier():
    notifier = TelegramNotifier(
        bot_token="123456789:ABCDEF_mock_token",
        chat_id="999999",
        allowed_chat_id="999999",
        enabled=True
    )
    return notifier

def test_unauthorized_chat_id(mock_notifier):
    """Security check: Unauthorized chat IDs must be rejected silently."""
    assert mock_notifier.is_chat_authorized("999999") is True
    assert mock_notifier.is_chat_authorized(999999) is True
    assert mock_notifier.is_chat_authorized("888888") is False
    assert mock_notifier.is_chat_authorized("123456") is False

@pytest.mark.asyncio
async def test_unauthorized_command_rejected(mock_notifier):
    """Unauthorized user sending /status receives UNAUTHORIZED."""
    res = await mock_notifier.handle_command("/status", chat_id="111111")
    assert res == "UNAUTHORIZED"

@pytest.mark.asyncio
async def test_unauthorized_callback_rejected(mock_notifier):
    """Unauthorized callback query receives UNAUTHORIZED."""
    cb = {
        "id": "cb_1",
        "message": {"chat": {"id": 111111}},
        "data": "approve_1"
    }
    res = await mock_notifier.handle_callback_query(cb)
    assert res == "UNAUTHORIZED"

@pytest.mark.asyncio
async def test_signal_expiry():
    """Signals older than timeout must be marked EXPIRED and rejected on approve."""
    live_streamer.signal_engine._signal_counter += 1
    sig_id = live_streamer.signal_engine._signal_counter
    sig = MagicMock(
        id=sig_id,
        symbol="INFY",
        direction="BUY",
        entry_price=1500.0,
        stop_loss=1485.0,
        target_price=1540.0,
        quantity=10,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        status="PENDING_APPROVAL",
        created_at=datetime.datetime.now() - datetime.timedelta(seconds=200),  # 200s old > 120s limit
        risk_notes=None
    )
    live_streamer.signal_engine._pending_signals[sig_id] = sig

    # Attempt to approve expired signal
    pos = live_streamer.approve_signal(sig_id)
    assert pos is None
    assert sig.status == "EXPIRED"

@pytest.mark.asyncio
async def test_price_drift_rejection():
    """If market price moved > MAX_ENTRY_DRIFT_PCT (0.3%), signal entry is cancelled."""
    live_streamer.signal_engine._signal_counter += 1
    sig_id = live_streamer.signal_engine._signal_counter
    sig = MagicMock(
        id=sig_id,
        symbol="TCS",
        direction="BUY",
        entry_price=3000.0,
        stop_loss=2970.0,
        target_price=3075.0,
        quantity=10,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        status="PENDING_APPROVAL",
        created_at=datetime.datetime.now(),
        reason="Drift Test",
        risk_reward_ratio=2.5,
        risk_notes=None
    )
    live_streamer.signal_engine._pending_signals[sig_id] = sig

    # Set latest tick with 1.0% drift (3030.0 vs 3000.0 > 0.3% limit)
    live_streamer.latest_ticks["TCS"] = LiveTick(
        symbol="TCS",
        ltp=3030.0,
        open=3000.0,
        high=3035.0,
        low=2995.0,
        close=3030.0,
        volume=10000,
        bid=3029.0,
        ask=3031.0,
        spread=2.0,
        timestamp=datetime.datetime.now()
    )

    pos = live_streamer.approve_signal(sig_id)
    assert pos is None
    assert sig.status == "CANCELLED"
    assert "drifted" in sig.risk_notes.lower()

@pytest.mark.asyncio
async def test_double_approve_idempotent():
    """Double-approving an already executed signal returns safe None/False (idempotent)."""
    live_streamer.signal_engine._signal_counter += 1
    sig_id = live_streamer.signal_engine._signal_counter
    sig = MagicMock(
        id=sig_id,
        symbol="HDFCBANK",
        direction="BUY",
        entry_price=1600.0,
        stop_loss=1584.0,
        target_price=1640.0,
        quantity=10,
        strategy_name="VWAP_EMA",
        strategy_score=85.0,
        status="EXECUTED",  # Already executed!
        created_at=datetime.datetime.now(),
        risk_notes=None
    )
    live_streamer.signal_engine._pending_signals[sig_id] = sig

    # Second approve attempt
    pos = live_streamer.approve_signal(sig_id)
    assert pos is None  # Idempotently ignored

@pytest.mark.asyncio
async def test_telegram_parameter_proposal_and_rollback_commands(monkeypatch):
    """Authorized chat can list proposals, approve parameter, and rollback."""
    from app.core.database import SessionLocal, Base, engine
    from app.models.models import ParameterProposal
    from app.learning.learner import market_learner
    from app.core.config import settings
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(settings, "TELEGRAM_ALLOWED_CHAT_ID", "123456789")
    bot = TelegramNotifier()
    bot.enabled = True
    bot._authorized_chat_id = "123456789"

    db = SessionLocal()
    try:
        # Create a pending proposal
        prop = ParameterProposal(
            param_name="atr_sl_multiplier",
            old_value=1.5,
            new_value=1.6,
            tp_multiplier=3.2,
            target_rr=2.0,
            status="PENDING",
            evidence="Test proposal for Telegram approval",
            sample_size=120,
            win_rate_pct=62.0,
            created_at=datetime.datetime.utcnow()
        )
        db.add(prop)
        db.commit()
        db.refresh(prop)

        # 1. /proposals
        with patch.object(bot, "send_message") as mock_send:
            res_list = await bot.handle_command("/proposals", chat_id="123456789")
            assert res_list == "PROPOSALS_LIST"
            mock_send.assert_called_once()

        # 2. /approve_param <id>
        with patch.object(bot, "send_message") as mock_send:
            res_app = await bot.handle_command(f"/approve_param {prop.id}", chat_id="123456789")
            assert res_app == "APPROVE_PARAM_SUCCESS"
            assert market_learner.current_atr_sl_multiplier == 1.6
            mock_send.assert_called_once()

        # 3. /rollback_param
        with patch.object(bot, "send_message") as mock_send:
            res_rb = await bot.handle_command("/rollback_param", chat_id="123456789")
            assert res_rb == "ROLLBACK_PARAM_SUCCESS"
            assert market_learner.current_atr_sl_multiplier == 1.5
            mock_send.assert_called_once()
    finally:
        db.close()

