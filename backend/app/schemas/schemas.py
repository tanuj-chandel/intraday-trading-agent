import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class StockBase(BaseModel):
    symbol: str
    company_name: str
    sector: str
    industry: Optional[str] = None
    exchange: str = "NSE"
    index_name: str = "NIFTY 50"
    lot_size: int = 1
    tick_size: float = 0.05
    liquidity_classification: str = "HIGH"
    avg_daily_volume: float = 1000000.0
    avg_daily_turnover_cr: float = 150.0
    is_active: bool = True

class StockCreate(StockBase):
    pass

class StockResponse(StockBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class Candle(BaseModel):
    timestamp: datetime.datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str = "5m"

class MarketIndexOverview(BaseModel):
    symbol: str
    current_price: float
    change: float
    change_pct: float
    open: float
    high: float
    low: float
    prev_close: float
    regime: str
    adx: Optional[float] = None
    volatility: str = "NORMAL"

class MarketOverviewResponse(BaseModel):
    indices: List[MarketIndexOverview]
    market_regime: str
    regime_description: str
    advance_decline_ratio: float
    market_status: str
    timestamp: datetime.datetime

class NewsItem(BaseModel):
    id: Optional[int] = None
    headline: str
    source: str
    source_reliability: str = "LEVEL_2"  # "LEVEL_1", "LEVEL_2", "LEVEL_3"
    published_at: datetime.datetime
    related_symbols: List[str]
    company: Optional[str] = None
    sector: Optional[str] = None
    sentiment: str = "NEUTRAL"  # "BULLISH", "BEARISH", "NEUTRAL"
    sentiment_score: float = 0.0
    impact: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW"
    impact_score: float = 50.0  # 0 to 100
    confidence: float = 0.85
    event_category: str = "Other"
    url: Optional[str] = None

class TechnicalIndicatorsResponse(BaseModel):
    symbol: str
    timestamp: datetime.datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    vwap: Optional[float] = None
    atr_14: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    rvol: Optional[float] = None
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None

class StockScoreResponse(BaseModel):
    id: Optional[int] = None
    rank: int
    symbol: str
    company_name: str
    sector: str
    current_price: float
    gap_pct: float = 0.0
    total_score: float
    direction: str  # "BULLISH", "BEARISH", "NEUTRAL"
    entry_zone: str
    stop_loss: float
    target: float
    risk_reward_ratio: float
    components: Dict[str, float]
    latest_news_headline: Optional[str] = None
    news_impact: Optional[str] = "MEDIUM"
    source_reliability: Optional[str] = "LEVEL_2"
    reason: str
    liquidity_classification: str = "HIGH"
    risk_warnings: List[str] = []
    timestamp: datetime.datetime

class CategorizedTopStocksResponse(BaseModel):
    top_overall: List[StockScoreResponse]
    top_longs: List[StockScoreResponse]
    top_shorts: List[StockScoreResponse]
    total_candidates_scanned: int
    liquidity_filtered_count: int
    timestamp: datetime.datetime

class GlobalMarketResponse(BaseModel):
    global_market_score: float
    sentiment: str
    us_trend: str
    asia_trend: str
    crude_oil_stance: str
    dollar_index_stance: str
    components: Dict[str, float]
    indices: List[Dict[str, Any]]
    summary_text: str
    timestamp: str

class GiftNiftyResponse(BaseModel):
    gift_nifty_price: float
    spot_nifty_close: float
    gap_points: float
    gap_pct: float
    gap_direction: str
    gap_magnitude: str
    source: str
    data_status: str
    timestamp: str

class DataQualityResponse(BaseModel):
    overall_status: str
    total_datasets: int
    datasets: Dict[str, Any]
    checked_at: str

class TradeSignalCreate(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    target_price: float
    quantity: int
    strategy_name: str
    strategy_score: float
    explanation: str

class TradeSignalResponse(BaseModel):
    id: int
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    target_price: float
    quantity: int
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    strategy_name: str
    strategy_score: float
    status: str
    reject_reason: Optional[str] = None
    explanation: str
    timestamp: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class SignalApprovalRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None

class RiskCheckResponse(BaseModel):
    passed: bool
    rejection_reason: Optional[str] = None
    current_daily_loss: float
    current_open_positions: int
    calculated_risk_amount: float
    allowed_quantity: Optional[int] = None
    metrics: Dict[str, Any]

class PaperPositionResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: int
    entry_price: float
    current_price: float
    stop_loss: float
    target_price: float
    trailing_stop: Optional[float] = None
    unrealized_pnl: float
    unrealized_pnl_pct: float
    status: str
    opened_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class TradeJournalResponse(BaseModel):
    id: int
    symbol: str
    strategy: str
    direction: str
    entry_price: float
    exit_price: float
    stop_loss: float
    target_price: float
    quantity: int
    gross_pnl: float
    estimated_charges: float
    net_pnl: float
    holding_time_minutes: float
    reason_for_entry: Optional[str] = None
    reason_for_exit: Optional[str] = None
    market_regime: Optional[str] = None
    score_at_entry: Optional[float] = None
    indicators_snapshot: Optional[Dict[str, Any]] = None
    news_rationale: Optional[Dict[str, Any]] = None
    slippage_incurred: float = 0.0
    achieved_r: Optional[float] = None
    entry_time: datetime.datetime
    exit_time: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class PerformanceMetricsResponse(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    gross_profit: float
    gross_loss: float
    net_pnl: float
    total_charges: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_pct: float
    average_holding_time_minutes: float
    risk_reward_achieved: float
    consecutive_wins: int
    consecutive_losses: int
    longest_losing_streak: int = 0
    average_r: float = 0.0
    expectancy_per_trade: float = 0.0
    expectancy_r: float = 0.0
    average_slippage: float = 0.0
    performance_by_strategy: Dict[str, Any] = {}
    performance_by_time_of_day: Dict[str, Any] = {}
    performance_by_symbol: Dict[str, Any] = {}
    performance_by_market_regime: Dict[str, Any] = {}
    initial_capital: float
    current_equity: float

class PreMarketAnalysisResponse(BaseModel):
    timestamp: datetime.datetime
    market_overview: str
    global_market_summary: str
    global_market_score: float
    gift_nifty: GiftNiftyResponse
    index_trend: str
    market_regime: str
    key_news: List[NewsItem]
    sector_performance: Dict[str, float]
    top_ranked_stocks: List[StockScoreResponse]
    top_long_candidates: List[StockScoreResponse]
    top_short_candidates: List[StockScoreResponse]
    risk_warnings: List[str]
    formatted_report: str

class SystemStatusResponse(BaseModel):
    trading_mode: str
    is_paper_trading: bool
    emergency_stop_triggered: bool
    market_data_provider: str
    data_quality_status: str
    portfolio_value: float
    cash_balance: float
    today_realized_pnl: float
    today_unrealized_pnl: float
    today_total_pnl: float
    daily_loss_remaining: float
    open_positions_count: int
    trades_count_today: int
    server_time: datetime.datetime
    market_status: str

class EmergencyStopRequest(BaseModel):
    reason: str
    cancel_pending_orders: bool = True
    close_open_positions: bool = True

class ManualGiftNiftyRequest(BaseModel):
    price: float

# ==========================================
# PHASE 3: BACKTESTING & VALIDATION SCHEMAS
# ==========================================

class BacktestRunRequest(BaseModel):
    strategy_id: str = "VWAP_EMA_MOMENTUM_V1"
    symbol: str = "RELIANCE"
    dataset_file: Optional[str] = None
    initial_capital: float = 100000.0
    risk_per_trade_pct: float = 0.01
    max_capital_exposure_pct: float = 0.30
    max_daily_loss_amount: float = 3000.0
    exit_time: str = "15:15"
    slippage_pct: float = 0.0005
    same_candle_conflict_resolution: str = "SL_FIRST"
    strategy_params: Optional[Dict[str, Any]] = None

class BacktestResultResponse(BaseModel):
    strategy_id: str
    symbol: str
    data_source_mode: str
    news_factor_status: str
    initial_capital: float
    final_capital: float
    net_pnl: float
    return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    expectancy: float
    average_win: float
    average_loss: float
    total_charges: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    average_holding_time_minutes: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    largest_winning_trade: float
    largest_losing_trade: float
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]
    strategy_parameters: Dict[str, Any]
    cost_assumptions: Dict[str, float]
    qualification: Optional[Dict[str, Any]] = None

class WalkForwardRequest(BaseModel):
    symbol: str = "RELIANCE"
    strategy_id: str = "VWAP_EMA_MOMENTUM_V1"
    initial_capital: float = 100000.0
    dataset_file: Optional[str] = None

class WalkForwardResponse(BaseModel):
    symbol: str
    validation_type: str
    data_source_mode: str
    is_stable: bool
    walk_forward_efficiency_ratio: float
    training_period: Dict[str, Any]
    validation_period: Dict[str, Any]
    out_of_sample_period: Dict[str, Any]
    verdict: str

class MonteCarloRequest(BaseModel):
    trades: Optional[List[Dict[str, Any]]] = None
    initial_capital: float = 100000.0
    iterations: int = 1000

class MonteCarloResponse(BaseModel):
    iterations: int
    data_source_mode: str
    trades_resampled: Optional[int] = 0
    median_max_drawdown_pct: float
    p95_max_drawdown_pct: float
    p99_max_drawdown_pct: float
    probability_of_drawdown_gt_5pct: float
    probability_of_ruin: float
    simulated_equity_distribution: Dict[str, float]
    summary: str

class ParameterAnalysisRequest(BaseModel):
    symbol: str = "RELIANCE"
    strategy_id: str = "VWAP_EMA_MOMENTUM_V1"
    initial_capital: float = 100000.0
    dataset_file: Optional[str] = None

class ParameterAnalysisResponse(BaseModel):
    symbol: str
    total_combinations_tested: int
    data_source_mode: str
    is_parameter_stable: bool
    coefficient_of_variation: float
    stability_rating: str
    best_combination: Dict[str, Any]
    median_profit_factor: float
    median_net_pnl: float
    grid_results: List[Dict[str, Any]]
    overfitting_risk: str
