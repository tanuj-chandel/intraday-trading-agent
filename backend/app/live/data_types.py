import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict

class LiveTick(BaseModel):
    symbol: str
    ltp: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    bid: float
    ask: float
    spread: float
    timestamp: datetime.datetime
    data_source: str = "LIVE_STREAM"
    is_live: bool = True

class LiveCandle(BaseModel):
    symbol: str
    timeframe: str  # "1m", "5m", "15m"
    timestamp: datetime.datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    is_closed: bool = False

class LiveSignalItem(BaseModel):
    id: int
    symbol: str
    direction: str  # "BUY" | "SELL"
    entry_price: float
    stop_loss: float
    target_price: float
    quantity: int
    risk_reward_ratio: float
    strategy_name: str = "VWAP_EMA_MOMENTUM_V1"
    strategy_score: float
    status: str = "PENDING_APPROVAL"  # PENDING_APPROVAL, PENDING, APPROVED, REJECTED, EXECUTED, EXPIRED, CANCELLED
    market_regime: str
    indicator_snapshot: Dict[str, Any]
    data_freshness_seconds: float
    created_at: datetime.datetime
    reason: str
    risk_passed: bool = True
    risk_notes: Optional[str] = None

class LivePaperPosition(BaseModel):
    id: int
    symbol: str
    side: str  # "BUY" | "SELL"
    quantity: int
    entry_price: float
    current_price: float
    stop_loss: float
    target_price: float
    trailing_stop: Optional[float] = None
    unrealized_pnl: float
    unrealized_pnl_pct: float
    status: str = "OPEN"  # OPEN, CLOSED
    slippage_incurred: float = 0.0
    statutory_charges: float = 0.0
    opened_at: datetime.datetime
    closed_at: Optional[datetime.datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    net_realized_pnl: Optional[float] = None
    strategy_name: str = "VWAP_EMA_MOMENTUM_V1"
    score_at_entry: float = 0.0
    market_regime: str = "TRENDING"
    reason_for_entry: str = ""
    indicators_snapshot: Optional[Dict[str, Any]] = None
    news_rationale: Optional[Dict[str, Any]] = None
    achieved_r: Optional[float] = None

class LiveAuditEvent(BaseModel):
    id: int
    event_type: str
    symbol: Optional[str] = None
    details: str
    timestamp: datetime.datetime
    metadata: Dict[str, Any] = {}
