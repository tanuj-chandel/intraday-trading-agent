export interface MarketIndexOverview {
  symbol: string;
  current_price: number;
  change: number;
  change_pct: number;
  open: number;
  high: number;
  low: number;
  prev_close: number;
  regime: string;
  adx?: number;
  volatility: string;
}

export interface MarketOverviewResponse {
  indices: MarketIndexOverview[];
  market_regime: string;
  regime_description: string;
  advance_decline_ratio: number;
  market_status: string;
  timestamp: string;
}

export interface NewsItem {
  id?: number;
  headline: string;
  source: string;
  source_reliability: "LEVEL_1" | "LEVEL_2" | "LEVEL_3";
  published_at: string;
  related_symbols: string[];
  company?: string;
  sector?: string;
  sentiment: "BULLISH" | "BEARISH" | "NEUTRAL";
  sentiment_score: number;
  impact: "HIGH" | "MEDIUM" | "LOW";
  impact_score: number;
  confidence: number;
  event_category: string;
  url?: string;
}

export interface StockScore {
  id?: number;
  rank: number;
  symbol: string;
  company_name: string;
  sector: string;
  current_price: number;
  gap_pct: number;
  total_score: number;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  entry_zone: string;
  stop_loss: number;
  target: number;
  risk_reward_ratio: number;
  components: Record<string, number>;
  latest_news_headline?: string;
  news_impact?: string;
  source_reliability?: string;
  reason: string;
  liquidity_classification: string;
  risk_warnings?: string[];
  timestamp: string;
}

export interface CategorizedTopStocks {
  top_overall: StockScore[];
  top_longs: StockScore[];
  top_shorts: StockScore[];
  total_candidates_scanned: number;
  liquidity_filtered_count: number;
  timestamp: string;
}

export interface GlobalMarketResponse {
  global_market_score: number;
  sentiment: string;
  us_trend: string;
  asia_trend: string;
  crude_oil_stance: string;
  dollar_index_stance: string;
  components: Record<string, number>;
  indices: Array<{
    name: string;
    region: string;
    price: number;
    change_pct: number;
    status: string;
  }>;
  summary_text: string;
  timestamp: string;
}

export interface GiftNiftyResponse {
  gift_nifty_price: number;
  spot_nifty_close: number;
  gap_points: number;
  gap_pct: number;
  gap_direction: "GAP_UP" | "GAP_DOWN" | "FLAT";
  gap_magnitude: string;
  source: string;
  data_status: "LIVE" | "DELAYED" | "MOCK" | "MANUAL" | "UNAVAILABLE";
  timestamp: string;
}

export interface DataQualityDataset {
  dataset_name: string;
  source: string;
  status: "LIVE" | "DELAYED" | "MOCK" | "STALE" | "ERROR";
  age_seconds: number;
  freshness: string;
  latency_ms: number;
  completeness_pct: number;
  error_message?: string;
  timestamp: string;
}

export interface DataQualityResponse {
  overall_status: "HEALTHY" | "WARNING_STALE" | "ERROR";
  total_datasets: number;
  datasets: Record<string, DataQualityDataset>;
  checked_at: string;
}

export interface TradeSignal {
  id: number;
  symbol: string;
  direction: "BUY" | "SELL";
  entry_price: number;
  stop_loss: number;
  target_price: number;
  quantity: number;
  risk_amount: number;
  reward_amount: number;
  risk_reward_ratio: number;
  strategy_name: string;
  strategy_score: number;
  status: "PENDING_APPROVAL" | "PENDING" | "APPROVED" | "REJECTED" | "EXECUTED" | "EXPIRED" | "CANCELLED";
  reject_reason?: string;
  explanation: string;
  timestamp: string;
}

export interface PaperPosition {
  id: number;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  entry_price: number;
  current_price: number;
  stop_loss: number;
  target_price: number;
  trailing_stop?: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  status: "OPEN" | "CLOSED";
  opened_at: string;
}

export interface TradeJournalItem {
  id: number;
  symbol: string;
  strategy: string;
  direction: "BUY" | "SELL";
  entry_price: number;
  exit_price: number;
  stop_loss: number;
  target_price: number;
  quantity: number;
  gross_pnl: number;
  estimated_charges: number;
  net_pnl: number;
  holding_time_minutes: number;
  reason_for_entry?: string;
  reason_for_exit?: string;
  market_regime?: string;
  score_at_entry?: number;
  entry_time: string;
  exit_time: string;
}

export interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  gross_profit: number;
  gross_loss: number;
  net_pnl: number;
  total_charges: number;
  average_win: number;
  average_loss: number;
  profit_factor: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  average_holding_time_minutes: number;
  risk_reward_achieved: number;
  consecutive_wins: number;
  consecutive_losses: number;
  initial_capital: number;
  current_equity: number;
}

export interface PreMarketAnalysis {
  timestamp: string;
  market_overview: string;
  global_market_summary: string;
  global_market_score: number;
  gift_nifty: GiftNiftyResponse;
  index_trend: string;
  market_regime: string;
  key_news: NewsItem[];
  sector_performance: Record<string, number>;
  top_ranked_stocks: StockScore[];
  top_long_candidates: StockScore[];
  top_short_candidates: StockScore[];
  risk_warnings: string[];
  formatted_report: string;
}

export interface SystemStatus {
  trading_mode: string;
  is_paper_trading: boolean;
  emergency_stop_triggered: boolean;
  market_data_provider: string;
  data_quality_status: string;
  portfolio_value: number;
  cash_balance: number;
  today_realized_pnl: number;
  today_unrealized_pnl: number;
  today_total_pnl: number;
  daily_loss_remaining: number;
  open_positions_count: number;
  trades_count_today: number;
  server_time: string;
  market_status: string;
}

// Backtesting Types
export interface BacktestTradeItem {
  trade_id: number;
  symbol: string;
  direction: "BUY" | "SELL";
  entry_time: string;
  entry_price: number;
  exit_time: string;
  exit_price: number;
  stop_loss: number;
  target_price: number;
  quantity: number;
  gross_pnl: number;
  charges: number;
  net_pnl: number;
  holding_time_minutes: number;
  reason_for_entry: string;
  reason_for_exit: string;
  strategy_score: number;
}

export interface BacktestEquityPoint {
  timestamp: string;
  equity: number;
  drawdown: number;
  drawdown_pct: number;
  open_trades: number;
}

export interface BacktestResult {
  strategy_id: string;
  symbol: string;
  data_source_mode: string;
  news_factor_status: string;
  initial_capital: number;
  final_capital: number;
  net_pnl: number;
  return_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  gross_profit: number;
  gross_loss: number;
  profit_factor: number;
  expectancy: number;
  average_win: number;
  average_loss: number;
  total_charges: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  average_holding_time_minutes: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  largest_winning_trade: number;
  largest_losing_trade: number;
  trades: BacktestTradeItem[];
  equity_curve: BacktestEquityPoint[];
  strategy_parameters: Record<string, any>;
  cost_assumptions: Record<string, number>;
  qualification?: {
    dataset_classification: string;
    provenance_description: string;
    is_sufficient_for_validation: boolean;
    total_candles: number;
    date_range_days: number;
    minimum_target: string;
    warning?: string;
  };
}

export interface WalkForwardResult {
  symbol: string;
  validation_type: string;
  data_source_mode: string;
  is_stable: boolean;
  walk_forward_efficiency_ratio: number;
  training_period: {
    candle_count: number;
    net_pnl: number;
    return_pct: number;
    win_rate: number;
    profit_factor: number;
    total_trades: number;
    max_drawdown_pct: number;
  };
  validation_period: {
    candle_count: number;
    net_pnl: number;
    return_pct: number;
    win_rate: number;
    profit_factor: number;
    total_trades: number;
    max_drawdown_pct: number;
  };
  out_of_sample_period: {
    candle_count: number;
    net_pnl: number;
    return_pct: number;
    win_rate: number;
    profit_factor: number;
    total_trades: number;
    max_drawdown_pct: number;
  };
  verdict: string;
}

export interface MonteCarloResult {
  iterations: number;
  data_source_mode: string;
  trades_resampled: number;
  median_max_drawdown_pct: number;
  p95_max_drawdown_pct: number;
  p99_max_drawdown_pct: number;
  probability_of_drawdown_gt_5pct: number;
  probability_of_ruin: number;
  simulated_equity_distribution: {
    p05_final_equity: number;
    p50_final_equity: number;
    p95_final_equity: number;
  };
  summary: string;
}

export interface ParameterSensitivityResult {
  symbol: string;
  total_combinations_tested: number;
  data_source_mode: string;
  is_parameter_stable: boolean;
  coefficient_of_variation: number;
  stability_rating: string;
  best_combination: Record<string, any>;
  median_profit_factor: number;
  median_net_pnl: number;
  grid_results: Array<{
    ema_fast: number;
    ema_slow: number;
    min_rvol: number;
    total_trades: number;
    win_rate: number;
    profit_factor: number;
    net_pnl: number;
    max_drawdown_pct: number;
  }>;
  overfitting_risk: string;
}

export interface ProviderHealthReport {
  checked_at: string;
  market_data: {
    provider: string;
    connected: boolean;
    status: string;
    latency_ms: number;
    error?: string;
    note?: string;
  };
  news: {
    provider: string;
    connected: boolean;
    status: string;
    latency_ms: number;
    data_age_seconds: number;
    quality: string;
  };
  global_markets: {
    provider: string;
    connected: boolean;
    status: string;
    latency_ms: number;
    data_age_seconds: number;
    score: number;
  };
  gift_nifty: {
    provider: string;
    connected: boolean;
    status: string;
    latency_ms: number;
    gap_points: number;
    gap_pct: number;
  };
  corporate_announcements: {
    provider: string;
    connected: boolean;
    status: string;
    latency_ms: number;
    category: string;
  };
  market_calendar: {
    current_time_ist: string;
    is_trading_day: boolean;
    is_market_open: boolean;
    status: string;
    holiday_name?: string;
    regular_market_hours: string;
    upcoming_holidays: Array<{ date: string; holiday: string }>;
  };
  overall_health: "HEALTHY" | "DEGRADED";
}

export interface CorporateAnnouncementItem {
  id: number;
  symbol: string;
  company_name: string;
  category: string;
  headline: string;
  details: string;
  source: string;
  reliability: string;
  published_at: string;
  source_url: string;
}

export interface MultiSymbolResult {
  universe_id: string;
  symbols_evaluated: number;
  symbols_list: string[];
  portfolio_summary: {
    total_trades: number;
    portfolio_net_pnl: number;
    portfolio_return_pct: number;
    portfolio_win_rate: number;
  };
  stock_leaderboard: Array<{
    symbol: string;
    trades: number;
    win_rate: number;
    net_pnl: number;
    profit_factor: number;
    max_drawdown_pct: number;
    expectancy: number;
  }>;
  best_performing_symbols: any[];
  worst_performing_symbols: any[];
  survivorship_warning: string;
  data_mode: string;
}

export interface SegmentationAnalysisResult {
  regimes: {
    regime_matrix: Record<string, {
      trade_count: number;
      profit_factor: number;
      net_pnl: number;
      win_rate: number;
      max_drawdown_pct: number;
    }>;
    regime_dependency_note: string;
  };
  time_of_day: {
    time_of_day_breakdown: Array<{
      window: string;
      session: string;
      trades: number;
      win_rate: number;
      profit_factor: number;
      net_pnl: number;
      expectancy: number;
    }>;
  };
  long_short: {
    long_trades: {
      trades: number;
      win_rate: number;
      profit_factor: number;
      net_pnl: number;
      expectancy: number;
    };
    short_trades: {
      trades: number;
      win_rate: number;
      profit_factor: number;
      net_pnl: number;
      expectancy: number;
    };
  };
  cost_slippage: {
    gross_pnl: number;
    cost_scenarios: Array<{ tier: string; charges: number; net_pnl: number }>;
    slippage_matrix: Array<{ slippage_pct: number; slippage_cost_inr: number; net_pnl: number; return_pct: number }>;
  };
  benchmarks: {
    strategy: { name: string; return_pct: number; profit_factor: number; trades: number };
    benchmarks: Array<{ name: string; return_pct: number; profit_factor: number; trades: number; description: string }>;
    alpha_assessment: string;
  };
}

export interface OverfittingScoreResult {
  overfitting_risk_score: number;
  risk_level: string;
  assessment: string;
  metrics_comparison: {
    train_profit_factor: number;
    val_profit_factor: number;
    oos_profit_factor: number;
    train_return_pct: number;
    oos_return_pct: number;
    oos_degradation_pct: number;
  };
}

export interface StrategyValidationReportResponse {
  report_title: string;
  generated_at: string;
  symbol: string;
  markdown_content: string;
  qualification: any;
  overfitting: any;
  backtest_summary: any;
}

// ==========================================
// PHASE 6: EMPIRICAL VALIDATION & QUALITY TYPES
// ==========================================

export interface Phase6ValidationResult {
  symbol: string;
  universe_id: string;
  final_verdict:
    | "VALIDATED ROBUST OOS EDGE"
    | "PROMISING BUT NEEDS MORE DATA"
    | "PROMISING BUT OVERFITTED"
    | "NO RELIABLE EDGE FOUND"
    | "INSUFFICIENT DATA FOR VALIDATION";
  verdict_explanation: string;
  frozen_baseline_config: Record<string, any>;
  data_quality_audit: {
    data_quality_score: number;
    quality_rating: string;
    status: string;
    total_candles: number;
    unique_trading_days: number;
    duplicate_candles_pct: number;
    invalid_ohlc_count: number;
    outlier_count: number;
    corporate_action_status: string;
    timezone: string;
    audit_errors: string[];
  };
  qualification: {
    dataset_classification: string;
    provenance_description: string;
    is_sufficient_for_validation: boolean;
    warning?: string;
  };
  baseline_results: {
    initial_capital: number;
    final_capital: number;
    net_pnl: number;
    return_pct: number;
    total_trades: number;
    win_rate: number;
    profit_factor: number;
    expectancy: number;
    max_drawdown_pct: number;
    total_charges: number;
  };
  stock_concentration: {
    top_1_stock_contribution_pct: number;
    top_3_stock_contribution_pct: number;
    top_5_stock_contribution_pct: number;
    stock_concentration_flag: string;
    profit_concentration_note: string;
  };
  trade_concentration: {
    top_1pct_trade_contribution_pct: number;
    top_5pct_trade_contribution_pct: number;
    top_10pct_trade_contribution_pct: number;
    trade_concentration_flag: string;
    profit_concentration_note?: string;
  };
  slippage_grid: Array<{
    slippage_pct: number;
    slippage_cost_inr: number;
    net_pnl: number;
    return_pct: number;
  }>;
  overfitting: OverfittingScoreResult;
  monte_carlo: any;
  benchmark_comparison: any;
  multi_symbol_summary: any;
  report_files?: {
    markdown_path: string;
    json_path: string;
    markdown_content: string;
  };
}
