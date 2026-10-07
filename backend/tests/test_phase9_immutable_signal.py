"""
Phase 9 — Signal Immutability Tests

Verifies that signal records capture the complete technical and macro context
and are immutable after generation.
"""
import datetime
import pytest
from app.phase9.immutable_signal import Phase9ImmutableSignalEngine


def test_create_and_retrieve_signal():
    sig = Phase9ImmutableSignalEngine.create_signal(
        session_id="SESS-2026-09-04-001",
        symbol="RELIANCE",
        direction="BUY",
        price=2980.0,
        ema_9=2982.0,
        ema_21=2975.0,
        vwap=2978.0,
        rvol=1.35,
        atr=22.5,
        market_regime="TRENDING_UP",
        time_of_day_bucket="10:00–11:30",
        intended_entry=2980.0,
        stop_loss=2950.0,
        target_price=3040.0,
        position_size=10,
        risk_amount=300.0,
        data_provenance="LIVE",
        news_context={"sentiment_score": 0.65},
        global_market_context={"us_trend": "BULLISH"},
        gift_nifty_context={"gap_pct": 0.4},
        confidence_score=85.0
    )

    assert sig["signal_id"] > 0
    assert sig["symbol"] == "RELIANCE"
    assert sig["direction"] == "BUY"
    assert sig["price"] == 2980.0
    assert sig["rvol"] == 1.35
    assert sig["strategy_version"] == "VWAP_EMA_MOMENTUM_V1"
    assert sig["news_context"]["sentiment_score"] == 0.65
    assert sig["is_immutable"] is True

    # Retrieve from DB
    retrieved = Phase9ImmutableSignalEngine.get_signal(sig["signal_id"])
    assert retrieved is not None
    assert retrieved["symbol"] == "RELIANCE"
    assert retrieved["market_regime"] == "TRENDING_UP"


def test_signal_status_transition():
    sig = Phase9ImmutableSignalEngine.create_signal(
        session_id="SESS-2026-09-04-001",
        symbol="TCS",
        direction="SELL",
        price=3500.0,
        ema_9=3490.0,
        ema_21=3510.0,
        vwap=3505.0,
        rvol=1.2,
        atr=30.0,
        market_regime="TRENDING_DOWN",
        time_of_day_bucket="10:00–11:30",
        intended_entry=3500.0,
        stop_loss=3545.0,
        target_price=3410.0
    )

    # Initial status is PENDING
    assert sig["status"] == "PENDING"

    # Transition status to APPROVED
    ok = Phase9ImmutableSignalEngine.update_status(sig["signal_id"], "APPROVED")
    assert ok is True

    retrieved = Phase9ImmutableSignalEngine.get_signal(sig["signal_id"])
    assert retrieved["status"] == "APPROVED"
    # Key inputs remain intact
    assert retrieved["intended_entry"] == 3500.0
    assert retrieved["stop_loss"] == 3545.0
