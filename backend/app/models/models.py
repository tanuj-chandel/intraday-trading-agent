import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)  # e.g., "RELIANCE", "TCS"
    nse_symbol = Column(String, unique=True, index=True, nullable=True)
    company_name = Column(String, nullable=False)
    sector = Column(String, index=True, nullable=False)
    industry = Column(String, nullable=True)
    exchange = Column(String, default="NSE")
    index_name = Column(String, default="NIFTY 50")  # "NIFTY 50", "NIFTY NEXT 50", "NIFTY 100", "NIFTY 200"
    lot_size = Column(Integer, default=1)
    tick_size = Column(Float, default=0.05)
    liquidity_classification = Column(String, default="HIGH")  # "VERY_HIGH", "HIGH", "MEDIUM", "LOW"
    avg_daily_volume = Column(Float, default=1000000.0)
    avg_daily_turnover_cr = Column(Float, default=150.0)  # in ₹ Crores
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    interval = Column(String, default="5m")  # "1m", "5m", "15m", "1d"
    source = Column(String, default="MOCK")  # "BROKER", "HISTORICAL", "MOCK"

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    headline = Column(String, nullable=False)
    source = Column(String, nullable=False)
    source_reliability = Column(String, default="LEVEL_2")  # "LEVEL_1" (Official filing/exchange), "LEVEL_2" (Reputable media), "LEVEL_3" (Other)
    published_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    related_symbols = Column(JSON, default=list)
    company = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    sentiment = Column(String, default="NEUTRAL")  # "BULLISH", "BEARISH", "NEUTRAL"
    sentiment_score = Column(Float, default=0.0)  # -1.0 to +1.0
    impact = Column(String, default="MEDIUM")  # "HIGH", "MEDIUM", "LOW"
    impact_score = Column(Float, default=50.0)  # 0 to 100
    confidence = Column(Float, default=0.85)  # 0.0 to 1.0
    event_category = Column(String, default="General")  # "Earnings", "Order win", "M&A", "Regulatory", etc.
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MarketRegime(Base):
    __tablename__ = "market_regimes"
    
    id = Column(Integer, primary_key=True, index=True)
    index_symbol = Column(String, default="NIFTY 50", index=True)
    regime = Column(String, nullable=False)  # TRENDING_UP, TRENDING_DOWN, SIDEWAYS, HIGH_VOLATILITY, GAP_UP, GAP_DOWN, UNKNOWN
    adx_value = Column(Float, nullable=True)
    atr_value = Column(Float, nullable=True)
    trend_strength = Column(Float, nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    ema_9 = Column(Float, nullable=True)
    ema_21 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    vwap = Column(Float, nullable=True)
    atr_14 = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_middle = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    rvol = Column(Float, nullable=True)
    support_level = Column(Float, nullable=True)
    resistance_level = Column(Float, nullable=True)

class StockScore(Base):
    __tablename__ = "stock_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    total_score = Column(Float, nullable=False)  # 0 to 100
    direction = Column(String, default="BULLISH")  # "BULLISH", "BEARISH", "NEUTRAL"
    rank = Column(Integer, nullable=True)
    components = Column(JSON, default=dict)  # breakdown of sub-scores
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class TradeSignal(Base):
    __tablename__ = "trade_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False)  # "BUY", "SELL", "HOLD", "NO_TRADE"
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    risk_amount = Column(Float, nullable=False)
    reward_amount = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, nullable=False)
    strategy_name = Column(String, nullable=False)
    strategy_score = Column(Float, nullable=False)
    status = Column(String, default="PENDING")  # "PENDING", "APPROVED", "REJECTED", "EXECUTED", "EXPIRED"
    reject_reason = Column(String, nullable=True)  # Detailed reason if signal is rejected by risk or user
    explanation = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class RiskCheck(Base):
    __tablename__ = "risk_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("trade_signals.id"), nullable=True)
    passed = Column(Boolean, nullable=False)
    rejection_reason = Column(String, nullable=True)
    current_daily_loss = Column(Float, default=0.0)
    current_open_positions = Column(Integer, default=0)
    calculated_risk_amount = Column(Float, default=0.0)
    risk_metrics = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class PaperOrder(Base):
    __tablename__ = "paper_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("trade_signals.id"), nullable=True)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)  # "BUY", "SELL"
    order_type = Column(String, default="LIMIT")  # "MARKET", "LIMIT", "SL-M"
    quantity = Column(Integer, nullable=False)
    requested_price = Column(Float, nullable=False)
    executed_price = Column(Float, nullable=True)
    slippage = Column(Float, default=0.0)
    status = Column(String, default="FILLED")  # "OPEN", "FILLED", "CANCELLED", "REJECTED"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

class PaperPosition(Base):
    __tablename__ = "paper_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)  # "BUY" (Long) or "SELL" (Short)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    trailing_stop = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)
    status = Column(String, default="OPEN")  # "OPEN", "CLOSED"
    opened_at = Column(DateTime, default=datetime.datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    strategy = Column(String, nullable=False)
    direction = Column(String, nullable=False)  # "BUY", "SELL"
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    gross_pnl = Column(Float, nullable=False)
    estimated_charges = Column(Float, nullable=False)
    net_pnl = Column(Float, nullable=False)
    holding_time_minutes = Column(Float, default=0.0)
    reason_for_entry = Column(Text, nullable=True)
    reason_for_exit = Column(Text, nullable=True)
    market_regime = Column(String, nullable=True)
    score_at_entry = Column(Float, nullable=True)
    indicators_snapshot = Column(JSON, nullable=True)
    news_rationale = Column(JSON, nullable=True)
    slippage_incurred = Column(Float, default=0.0)
    achieved_r = Column(Float, nullable=True)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    total_capital = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_capital = Column(Float, default=0.0)
    realized_pnl_today = Column(Float, default=0.0)
    unrealized_pnl_today = Column(Float, default=0.0)
    total_pnl_today = Column(Float, default=0.0)
    open_positions_count = Column(Integer, default=0)
    trades_count_today = Column(Integer, default=0)

class StrategyRun(Base):
    __tablename__ = "strategy_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String, nullable=False)
    run_timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    candidates_analyzed = Column(Integer, default=0)
    signals_generated = Column(Integer, default=0)
    status = Column(String, default="COMPLETED")
    metadata_json = Column(JSON, default=dict)

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    level = Column(String, default="INFO")
    module = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)


# ─── Phase 7: Live Paper Trading Tables ───────────────────────────────────────

class LiveSession(Base):
    """Tracks each live paper trading session (one per trading day)."""
    __tablename__ = "live_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_date = Column(String, index=True, nullable=False)  # "YYYY-MM-DD"
    provider_name = Column(String, default="MOCK")
    is_mock = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_paper_trades = Column(Integer, default=0)
    net_realized_pnl = Column(Float, default=0.0)
    total_charges = Column(Float, default=0.0)
    kill_switch_activated = Column(Boolean, default=False)
    kill_switch_level = Column(Integer, default=0)
    reality_gap_verdict = Column(String, nullable=True)
    metadata_json = Column(JSON, default=dict)


class LiveSignalRecord(Base):
    """Persists live signals for crash recovery and audit."""
    __tablename__ = "live_signals"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=True)
    symbol = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False)  # "BUY" | "SELL"
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    strategy_name = Column(String, default="VWAP_EMA_MOMENTUM_V1")
    strategy_score = Column(Float, default=0.0)
    status = Column(String, default="PENDING")  # PENDING, EXECUTED, REJECTED, REJECTED_BY_RISK, EXPIRED
    risk_reward_ratio = Column(Float, default=2.0)
    market_regime = Column(String, nullable=True)
    data_freshness_seconds = Column(Float, default=0.0)
    reason = Column(Text, nullable=True)
    indicator_snapshot = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)


class LivePositionRecord(Base):
    """Persists live paper positions for crash recovery and audit."""
    __tablename__ = "live_positions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=True)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)  # "BUY" | "SELL"
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    trailing_stop = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)
    status = Column(String, default="OPEN")  # OPEN | CLOSED
    slippage_incurred = Column(Float, default=0.0)
    statutory_charges = Column(Float, default=0.0)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)
    net_realized_pnl = Column(Float, nullable=True)
    opened_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    closed_at = Column(DateTime, nullable=True)


# ─── Phase 8: Production-Grade Validation Tables ──────────────────────────────
# Note: SystemLog table already exists above (system_logs). Phase 8 alerter
# writes to that table using the existing SystemLog model.


class Phase8TradeJournalRecord(Base):
    """Full auditable paper trade journal entry with MFE/MAE, regime, all costs."""
    __tablename__ = "phase8_trade_journal"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, index=True, nullable=False)
    session_date = Column(String, index=True, nullable=False)

    # Identity
    symbol = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False)
    strategy_name = Column(String, default="VWAP_EMA_MOMENTUM_V1")
    data_provenance = Column(String, default="UNKNOWN")

    # Context
    market_regime = Column(String, nullable=True)
    time_of_day_bucket = Column(String, nullable=True)   # OPEN_30M, MID_SESSION, CLOSE_1H

    # Execution
    intended_entry_price = Column(Float, nullable=False)
    simulated_fill_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, default=2.0)

    # Exit
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)
    holding_minutes = Column(Float, default=0.0)

    # P&L (all in ₹)
    gross_pnl = Column(Float, default=0.0)
    total_charges = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    entry_slippage_inr = Column(Float, default=0.0)

    # Excursions
    mfe_inr = Column(Float, default=0.0)
    mae_inr = Column(Float, default=0.0)

    opened_at = Column(DateTime, index=True, nullable=True)
    closed_at = Column(DateTime, nullable=True)


class Phase8Alert(Base):
    """Internal alert records for Phase 8 system health and trading events."""
    __tablename__ = "phase8_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, index=True, nullable=False)
    severity = Column(String, default="WARNING")          # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)
    symbol = Column(String, nullable=True, index=True)
    resolved = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)


class Phase8TickStats(Base):
    """Per-symbol tick quality statistics for a session."""
    __tablename__ = "phase8_tick_stats"

    id = Column(Integer, primary_key=True, index=True)
    session_date = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    tick_count = Column(Integer, default=0)
    invalid_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)
    reconnect_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)


# ─── Phase 9: Controlled Real-World Paper Trading Pilot Tables ────────────────

class Phase9Session(Base):
    """
    Tracks each Phase 9 controlled paper trading session.
    Strict single-date boundary enforcement; prevents mixing cross-date records.
    """
    __tablename__ = "phase9_sessions"

    session_id = Column(String, primary_key=True, index=True)  # e.g., "SESS-2026-09-04-001"
    trading_date = Column(String, index=True, nullable=False)   # "YYYY-MM-DD"
    market_open_time = Column(DateTime, default=datetime.datetime.utcnow)
    market_close_time = Column(DateTime, nullable=True)
    provider = Column(String, default="MOCK")
    status = Column(String, default="ACTIVE")                   # "ACTIVE" | "CLOSED"
    symbols_monitored = Column(JSON, default=list)

    # Accounting & Flow Counters
    valid_ticks = Column(Integer, default=0)
    rejected_ticks = Column(Integer, default=0)
    generated_signals = Column(Integer, default=0)
    approved_signals = Column(Integer, default=0)
    rejected_signals = Column(Integer, default=0)
    executed_paper_trades = Column(Integer, default=0)
    exits = Column(Integer, default=0)

    # Financial Performance
    gross_pnl = Column(Float, default=0.0)
    transaction_costs = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)                       # gross_pnl - transaction_costs - slippage
    max_drawdown = Column(Float, default=0.0)
    daily_loss = Column(Float, default=0.0)

    # Operational Health
    kill_switch_events = Column(Integer, default=0)
    data_quality_incidents = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Phase9Signal(Base):
    """
    Immutable Phase 9 signal record capturing complete decision context.
    Never modified after generation for forensic reproducibility.
    """
    __tablename__ = "phase9_signals"

    signal_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    symbol = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    price = Column(Float, nullable=False)

    # Technical Indicators Snapshot
    ema_9 = Column(Float, default=0.0)
    ema_21 = Column(Float, default=0.0)
    vwap = Column(Float, default=0.0)
    rvol = Column(Float, default=0.0)
    atr = Column(Float, default=0.0)

    # Market State Context
    market_regime = Column(String, default="UNKNOWN")
    time_of_day_bucket = Column(String, default="MID_SESSION")
    strategy_version = Column(String, default="VWAP_EMA_MOMENTUM_V1")

    # Order Specification
    direction = Column(String, nullable=False)                 # "BUY" | "SELL"
    intended_entry = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    position_size = Column(Integer, default=1)
    risk_amount = Column(Float, default=0.0)

    # Provenance & Macro Context
    data_provenance = Column(String, default="UNKNOWN")
    news_context = Column(JSON, default=dict)
    global_market_context = Column(JSON, default=dict)
    gift_nifty_context = Column(JSON, default=dict)
    confidence_score = Column(Float, default=0.0)

    status = Column(String, default="PENDING")                 # PENDING, APPROVED, REJECTED, EXECUTED, EXPIRED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)


class Phase9TradeEvent(Base):
    """
    Phase 9 paper execution event recording complete cost breakdown and excursions.
    Enforces: GROSS P&L - TRANSACTION COST - SLIPPAGE = NET P&L.
    """
    __tablename__ = "phase9_trade_events"

    trade_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    signal_id = Column(Integer, nullable=True)
    symbol = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False)                 # "BUY" | "SELL"

    # Execution Realism & Slippage
    intended_entry_price = Column(Float, nullable=False)
    simulated_fill_price = Column(Float, nullable=False)
    entry_slippage = Column(Float, default=0.0)
    intended_exit_price = Column(Float, nullable=True)
    simulated_exit_price = Column(Float, nullable=True)
    exit_slippage = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    quantity = Column(Integer, nullable=False)

    # Itemized Indian Statutory Charges
    brokerage = Column(Float, default=0.0)
    stt = Column(Float, default=0.0)
    gst = Column(Float, default=0.0)
    sebi_charges = Column(Float, default=0.0)
    exchange_charges = Column(Float, default=0.0)
    stamp_duty = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    # Performance
    gross_pnl = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)

    # Excursion Tracking
    mfe = Column(Float, default=0.0)                           # Maximum Favorable Excursion
    mae = Column(Float, default=0.0)                           # Maximum Adverse Excursion

    # Context & Attribution
    market_regime = Column(String, nullable=True)
    time_of_day_bucket = Column(String, nullable=True)
    holding_minutes = Column(Float, default=0.0)
    exit_reason = Column(String, nullable=True)
    data_provenance = Column(String, default="UNKNOWN")

    opened_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    closed_at = Column(DateTime, nullable=True)


class Phase9Statistics(Base):
    """
    Aggregated statistical evidence cache including bootstrap CIs, Monte Carlo, and milestones.
    """
    __tablename__ = "phase9_statistics"

    id = Column(Integer, primary_key=True, index=True)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    total_sessions = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    expectancy = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    verdict = Column(String, default="INSUFFICIENT LIVE PAPER DATA")
    milestone_stage = Column(String, default="INSUFFICIENT")
    summary_json = Column(Text, nullable=True)                 # Serialized statistical metrics


class Phase9DailyReport(Base):
    """
    Persistent registry of Phase 9 automated daily session reports and verdicts.
    """
    __tablename__ = "phase9_daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    trading_date = Column(String, index=True, nullable=False)
    markdown_path = Column(String, nullable=False)
    json_path = Column(String, nullable=False)
    verdict = Column(String, nullable=False)
    metrics_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)


class ParameterProposal(Base):
    """
    Phase 5: Parameter Proposals generated by safe learning engine.
    Recommend-only mode: Stored in table until approved by operator via Telegram or Dashboard.
    """
    __tablename__ = "parameter_proposals"

    id = Column(Integer, primary_key=True, index=True)
    param_name = Column(String, nullable=False)           # e.g., "atr_sl_multiplier"
    old_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    tp_multiplier = Column(Float, nullable=False)
    target_rr = Column(Float, default=2.0)
    status = Column(String, default="PENDING")            # PENDING, APPROVED, REJECTED, APPLIED
    evidence = Column(Text, nullable=False)
    stats_json = Column(Text, nullable=True)
    sample_size = Column(Integer, default=0)
    win_rate_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)


class ParameterVersionHistory(Base):
    """
    Phase 5: Version history of applied parameters.
    Enables single-command rollback to any previous version.
    """
    __tablename__ = "parameter_version_history"

    id = Column(Integer, primary_key=True, index=True)
    version_number = Column(Integer, index=True, nullable=False)
    param_name = Column(String, nullable=False)
    applied_value = Column(Float, nullable=False)
    tp_multiplier = Column(Float, nullable=False)
    previous_value = Column(Float, nullable=False)
    applied_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    approved_by = Column(String, default="TELEGRAM")      # "TELEGRAM", "DASHBOARD", "SYSTEM"
    change_summary = Column(Text, nullable=False)
