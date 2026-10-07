import pytest
import datetime
import pandas as pd
from unittest.mock import patch, MagicMock

from app.core.config import settings
from app.strategies.quality_filters import TradeQualityFilterEngine, quality_filters
from app.market.regime import MarketRegimeEngine
from app.execution.slippage_model import DynamicSlippageModel
from app.news.aggregator import NewsAggregator
from app.schemas.schemas import NewsItem
from app.scoring.scorer import StockScoringEngine
from app.strategies.base import Strategy
from app.strategies.orb import OpeningRangeBreakoutStrategy
from app.strategies.mean_reversion import MeanReversionStrategy
from app.strategies.registry import StrategyRegistry
from app.live.streamer import live_streamer

# ── 1. Time Filters ──────────────────────────────────────────────────────────

def test_time_filter_early_morning_and_afternoon_blocks():
    """No new entries in first 10 minutes (09:15-09:25) and after 14:30 IST."""
    # 09:20 IST -> blocked
    dt_morning = datetime.datetime(2026, 10, 5, 9, 20, 0)
    passed, reason = TradeQualityFilterEngine.check_time_filter(dt=dt_morning, score=80.0, symbol="INFY")
    assert passed is False
    assert "opening window" in reason

    # 14:35 IST -> blocked
    dt_afternoon = datetime.datetime(2026, 10, 5, 14, 35, 0)
    passed, reason = TradeQualityFilterEngine.check_time_filter(dt=dt_afternoon, score=80.0, symbol="INFY")
    assert passed is False
    assert "late in session" in reason

    # 10:15 IST -> allowed
    dt_valid = datetime.datetime(2026, 10, 5, 10, 15, 0)
    passed, reason = TradeQualityFilterEngine.check_time_filter(dt=dt_valid, score=80.0, symbol="INFY")
    assert passed is True
    assert reason is None

def test_time_filter_lunch_chop_higher_threshold():
    """During 12:00-13:30, trades below 85 score are rejected, trades >= 85 pass."""
    dt_lunch = datetime.datetime(2026, 10, 5, 12, 30, 0)
    
    # Score 75 (< 85) -> blocked
    passed, reason = TradeQualityFilterEngine.check_time_filter(dt=dt_lunch, score=75.0, symbol="TCS")
    assert passed is False
    assert "Lunch-chop reduction active" in reason

    # Score 88 (>= 85) -> allowed
    passed, reason = TradeQualityFilterEngine.check_time_filter(dt=dt_lunch, score=88.0, symbol="TCS")
    assert passed is True

def test_time_filter_can_be_disabled():
    """When TIME_FILTER_ENABLED=False, all times pass unconditionally."""
    dt_early = datetime.datetime(2026, 10, 5, 9, 18, 0)
    with patch.object(settings, "TIME_FILTER_ENABLED", False):
        passed, _ = TradeQualityFilterEngine.check_time_filter(dt=dt_early, score=60.0)
        assert passed is True

# ── 2. Market Regime Filter ──────────────────────────────────────────────────

def test_regime_filter_choppy_and_high_vol():
    """In CHOPPY or extreme HIGH_VOL, requires higher score or blocks entries."""
    # CHOPPY with score 75 (< 85) -> blocked
    passed, reason = TradeQualityFilterEngine.check_regime_filter(regime="CHOPPY", score=75.0)
    assert passed is False
    assert "Score 75.0 < required 85.0" in reason

    # CHOPPY with score 90 -> allowed
    passed, reason = TradeQualityFilterEngine.check_regime_filter(regime="CHOPPY", score=90.0)
    assert passed is True

    # Extreme India VIX (28.0) with score 78 -> blocked
    passed, reason = TradeQualityFilterEngine.check_regime_filter(regime="TRENDING", score=78.0, india_vix=28.0)
    assert passed is False
    assert "Extreme India VIX" in reason

    # TRENDING with standard score 72 -> allowed
    passed, reason = TradeQualityFilterEngine.check_regime_filter(regime="TRENDING", score=72.0, india_vix=14.0)
    assert passed is True

def test_market_regime_classification_and_dashboard_status():
    """MarketRegimeEngine classifies Nifty trend + VIX and streamer includes it in status."""
    res = MarketRegimeEngine.classify_nifty_vix_regime(
        nifty_price=25000.0,
        nifty_vwap=24900.0,
        nifty_ema_9=24950.0,
        nifty_ema_21=24920.0,
        india_vix=13.5
    )
    assert res["regime"] == "TRENDING"

    # Status contains market_regime
    status = live_streamer.get_status()
    assert "market_regime" in status
    assert status["market_regime"] in ("TRENDING", "CHOPPY", "HIGH_VOL", "SIDEWAYS")

# ── 3. Tradability Checks ───────────────────────────────────────────────────

def test_tradability_checks_circuit_halted_asm_corporate():
    """Tradability skips circuit proximity, halted stocks, ASM/GSM, and corporate actions."""
    # 1. Near Upper Circuit (within 1%)
    # Upper circuit = 1000, 1% buffer = 990. LTP = 995 -> blocked
    passed, reason = TradeQualityFilterEngine.check_tradability(
        symbol="TATAMOTORS",
        ltp=995.0,
        upper_circuit=1000.0,
        lower_circuit=800.0
    )
    assert passed is False
    assert "Upper Circuit" in reason

    # 2. Near Lower Circuit (within 1%)
    # Lower circuit = 800, 1% buffer = 808. LTP = 805 -> blocked
    passed, reason = TradeQualityFilterEngine.check_tradability(
        symbol="TATAMOTORS",
        ltp=805.0,
        upper_circuit=1000.0,
        lower_circuit=800.0
    )
    assert passed is False
    assert "Lower Circuit" in reason

    # 3. Exchange Halted
    passed, reason = TradeQualityFilterEngine.check_tradability(
        symbol="RELIANCE",
        ltp=2500.0,
        is_halted=True
    )
    assert passed is False
    assert "halted" in reason

    # 4. ASM/GSM Surveillance List
    passed, reason = TradeQualityFilterEngine.check_tradability(
        symbol="YESBANK",
        ltp=25.0
    )
    assert passed is False
    assert "ASM/GSM" in reason

    # 5. Corporate Action / Results Today
    passed, reason = TradeQualityFilterEngine.check_tradability(
        symbol="INFY",
        ltp=1800.0,
        corporate_action_today="Q2 Earnings Board Meeting & Special Dividend"
    )
    assert passed is False
    assert "corporate action today" in reason

# ── 4. Event-Day Mode ────────────────────────────────────────────────────────

def test_event_day_mode_reduces_risk_or_pauses():
    """Event day config either reduces risk or pauses trading on scheduled dates."""
    event_dt = datetime.datetime(2026, 2, 1, 10, 0, 0)  # Union Budget date

    # Default action: REDUCE_RISK
    can_trade, multiplier, reason = TradeQualityFilterEngine.check_event_day(dt=event_dt, symbol="RELIANCE")
    assert can_trade is True
    assert multiplier == 0.5
    assert "Risk scaled by 0.5x" in reason

    # Action: PAUSE_TRADING
    with patch.object(settings, "EVENT_DAY_ACTION", "PAUSE_TRADING"):
        can_trade, multiplier, reason = TradeQualityFilterEngine.check_event_day(dt=event_dt, symbol="RELIANCE")
        assert can_trade is False
        assert multiplier == 0.0
        assert "Trading paused" in reason

    # Non-event day -> normal 1.0x
    normal_dt = datetime.datetime(2026, 3, 10, 10, 0, 0)
    can_trade, multiplier, _ = TradeQualityFilterEngine.check_event_day(dt=normal_dt)
    assert can_trade is True
    assert multiplier == 1.0

# ── 5. Slippage Realism ──────────────────────────────────────────────────────

def test_dynamic_slippage_scales_with_liquidity_tier_and_spread():
    """Dynamic slippage model scales fill price with liquidity tier and bid-ask spread."""
    # RELIANCE is VERY_HIGH liquidity tier
    price_rel, slip_rel = DynamicSlippageModel.calculate_execution_price(
        symbol="RELIANCE",
        direction="BUY",
        market_price=2500.0,
        bid=2499.5,
        ask=2500.5,
        quantity=100
    )
    # TRENT is HIGH liquidity tier
    price_trent, slip_trent = DynamicSlippageModel.calculate_execution_price(
        symbol="TRENT",
        direction="BUY",
        market_price=2500.0,
        bid=2499.5,
        ask=2500.5,
        quantity=100
    )

    # VERY_HIGH should incur less slippage than HIGH
    assert slip_rel < slip_trent
    assert price_rel >= 2500.0

# ── 6. News Sentiment Pipeline ──────────────────────────────────────────────

def test_news_pipeline_ignores_stale_news_and_caps_alpha_weight():
    """News older than NEWS_MAX_AGE_MINUTES is ignored; news weight in score is capped."""
    aggregator = NewsAggregator()
    now = datetime.datetime.now()

    # Create one fresh news item (30 mins old) and one stale news item (180 mins old)
    stale_item = NewsItem(
        id=991,
        headline="Old quarterly results announced for TCS",
        source="BSE",
        source_reliability="HIGH",
        published_at=now - datetime.timedelta(minutes=180),
        related_symbols=["TCS"],
        company="TCS",
        sector="IT",
        sentiment="BEARISH",
        sentiment_score=-0.80,
        impact="HIGH",
        impact_score=-70.0,
        confidence=90.0,
        event_category="EARNINGS",
        url="http://example.com"
    )
    aggregator.news_items = [stale_item]

    # Stale news should be ignored
    res = aggregator.get_sentiment_for_symbol("TCS")
    assert res["sentiment_score"] == 0.0
    assert res.get("is_stale") is True

    # Test Scorer caps news weight
    df = pd.DataFrame({
        "open": [100.0 + i for i in range(40)],
        "high": [102.0 + i for i in range(40)],
        "low": [99.0 + i for i in range(40)],
        "close": [101.0 + i for i in range(40)],
        "volume": [100000 + (i * 1000) for i in range(40)]
    })

    fresh_item = NewsItem(
        id=992,
        headline="Massive mega deal secured by TCS",
        source="NSE",
        source_reliability="HIGH",
        published_at=now - datetime.timedelta(minutes=10),
        related_symbols=["TCS"],
        company="TCS",
        sector="IT",
        sentiment="BULLISH",
        sentiment_score=1.0,
        impact="HIGH",
        impact_score=90.0,
        confidence=95.0,
        event_category="ORDER_WIN",
        url="http://example.com"
    )

    scored = StockScoringEngine.calculate_score(
        symbol="TCS",
        df=df,
        market_regime="TRENDING_UP",
        news_items=[fresh_item]
    )
    # News component must be <= NEWS_MAX_ALPHA_WEIGHT (10.0)
    assert scored["components"]["news_sentiment"] <= 10.0

# ── 7. Strategy Interface (ORB & Mean Reversion) ─────────────────────────────

def test_orb_and_mean_reversion_strategy_interfaces_disabled_by_default():
    """ORB and Mean Reversion are prepared, registered, and disabled by default."""
    orb = OpeningRangeBreakoutStrategy()
    mr = MeanReversionStrategy()

    assert isinstance(orb, Strategy)
    assert isinstance(mr, Strategy)
    assert orb.is_enabled() is False
    assert mr.is_enabled() is False

    # Calling evaluate when disabled returns None
    df = pd.DataFrame({
        "open": [100.0] * 35,
        "high": [105.0] * 35,
        "low": [95.0] * 35,
        "close": [104.0] * 35,
        "volume": [500000] * 35
    })
    assert orb.evaluate("INFY", df) is None
    assert mr.evaluate("INFY", df) is None

    # Performance summary starts clean
    perf = orb.get_performance_summary()
    assert perf["strategy_id"] == "ORB_15M_V1"
    assert perf["is_enabled"] is False
    assert perf["total_trades"] == 0

    # Registry has them registered as inactive
    strat_orb = StrategyRegistry.get("ORB_15M_V1")
    assert strat_orb is not None
    assert strat_orb.is_enabled is False

    strat_mr = StrategyRegistry.get("MEAN_REVERSION_BB_RSI_V1")
    assert strat_mr is not None
    assert strat_mr.is_enabled is False
