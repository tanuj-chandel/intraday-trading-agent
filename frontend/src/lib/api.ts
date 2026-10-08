import {
  MarketOverviewResponse,
  StockScore,
  CategorizedTopStocks,
  GlobalMarketResponse,
  GiftNiftyResponse,
  DataQualityResponse,
  NewsItem,
  TradeSignal,
  PaperPosition,
  TradeJournalItem,
  PerformanceMetrics,
  PreMarketAnalysis,
  SystemStatus,
  BacktestResult,
  WalkForwardResult,
  MonteCarloResult,
  ParameterSensitivityResult,
  ProviderHealthReport,
  CorporateAnnouncementItem,
  MultiSymbolResult,
  SegmentationAnalysisResult,
  OverfittingScoreResult,
  StrategyValidationReportResponse,
  Phase6ValidationResult
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const res = await fetch(`${API_BASE}/system/status`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch system status");
  return res.json();
}

export async function fetchMarketOverview(): Promise<MarketOverviewResponse> {
  const res = await fetch(`${API_BASE}/market/overview`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch market overview");
  return res.json();
}

export async function fetchGlobalMarkets(): Promise<GlobalMarketResponse> {
  const res = await fetch(`${API_BASE}/market/global`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch global market cues");
  return res.json();
}

export async function fetchGiftNifty(): Promise<GiftNiftyResponse> {
  const res = await fetch(`${API_BASE}/market/gift-nifty`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch GIFT Nifty data");
  return res.json();
}

export async function setManualGiftNifty(price: number): Promise<any> {
  const res = await fetch(`${API_BASE}/market/gift-nifty/manual`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ price })
  });
  if (!res.ok) throw new Error("Failed to update GIFT Nifty manual level");
  return res.json();
}

export async function fetchDataQuality(): Promise<DataQualityResponse> {
  const res = await fetch(`${API_BASE}/market/data-sources`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch data quality report");
  return res.json();
}

export async function fetchTopStocks(limit = 10): Promise<StockScore[]> {
  const res = await fetch(`${API_BASE}/stocks/top?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch top stocks");
  return res.json();
}

export async function fetchCategorizedTopStocks(): Promise<CategorizedTopStocks> {
  const res = await fetch(`${API_BASE}/stocks/top-categorized`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch categorized top candidates");
  return res.json();
}

export async function fetchNews(limit = 15): Promise<NewsItem[]> {
  const res = await fetch(`${API_BASE}/news?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch news");
  return res.json();
}

export async function fetchSignals(): Promise<TradeSignal[]> {
  const res = await fetch(`${API_BASE}/signals`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch signals");
  return res.json();
}

export async function generateSignals(): Promise<TradeSignal[]> {
  const res = await fetch(`${API_BASE}/signals/generate`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to generate signals");
  return res.json();
}

export async function approveSignal(signalId: number): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/signals/${signalId}/approve`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to approve signal");
  return res.json();
}

export async function rejectSignal(signalId: number): Promise<any> {
  const res = await fetch(`${API_BASE}/signals/${signalId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved: false })
  });
  if (!res.ok) throw new Error("Failed to reject signal");
  return res.json();
}

export async function fetchPositions(): Promise<PaperPosition[]> {
  const res = await fetch(`${API_BASE}/positions?status=OPEN`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch open positions");
  return res.json();
}

export async function closePosition(positionId: number): Promise<any> {
  const res = await fetch(`${API_BASE}/positions/${positionId}/close`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to close position");
  return res.json();
}

export async function fetchTrades(): Promise<TradeJournalItem[]> {
  const res = await fetch(`${API_BASE}/trades`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch trade journal");
  return res.json();
}

export async function fetchPerformance(): Promise<PerformanceMetrics> {
  const res = await fetch(`${API_BASE}/performance`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch performance");
  return res.json();
}

export async function runPreMarketAnalysis(): Promise<PreMarketAnalysis> {
  const res = await fetch(`${API_BASE}/premarket/analyze`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to run pre-market analysis");
  return res.json();
}

export async function triggerEmergencyStop(reason: string): Promise<any> {
  const res = await fetch(`${API_BASE}/system/emergency-stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason })
  });
  if (!res.ok) throw new Error("Failed to trigger emergency stop");
  return res.json();
}

// Backtesting API
export async function fetchBacktestStrategies(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/backtest/strategies`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch backtest strategies");
  return res.json();
}

export async function fetchBacktestDatasets(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/backtest/datasets`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch historical datasets");
  return res.json();
}

export async function runBacktest(payload: any): Promise<BacktestResult> {
  const res = await fetch(`${API_BASE}/backtest/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to execute backtest");
  }
  return res.json();
}

export async function fetchLatestBacktest(): Promise<BacktestResult> {
  const res = await fetch(`${API_BASE}/backtest/results`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch latest backtest");
  return res.json();
}

export async function runWalkForward(payload: any): Promise<WalkForwardResult> {
  const res = await fetch(`${API_BASE}/backtest/walk-forward`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Failed to execute walk-forward validation");
  return res.json();
}

export async function runMonteCarlo(payload: any): Promise<MonteCarloResult> {
  const res = await fetch(`${API_BASE}/backtest/monte-carlo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Failed to execute Monte Carlo analysis");
  return res.json();
}

export async function runParameterAnalysis(payload: any): Promise<ParameterSensitivityResult> {
  const res = await fetch(`${API_BASE}/backtest/parameter-analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Failed to execute parameter sensitivity analysis");
  return res.json();
}

export async function fetchStrategyComparison(symbol = "RELIANCE"): Promise<any> {
  const res = await fetch(`${API_BASE}/backtest/comparison/matrix?symbol=${symbol}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch strategy comparison matrix");
  return res.json();
}

export async function fetchDataHealthReport(): Promise<ProviderHealthReport> {
  const res = await fetch(`${API_BASE}/data/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch data health report");
  return res.json();
}

export async function testProviderConnection(provider: string): Promise<any> {
  const res = await fetch(`${API_BASE}/data/test-connection?provider=${provider}`, { method: "POST" });
  if (!res.ok) throw new Error("Connection test failed");
  return res.json();
}

export async function uploadHistoricalDataset(formData: FormData): Promise<any> {
  const res = await fetch(`${API_BASE}/data/import`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to upload and validate historical dataset");
  }
  return res.json();
}

export async function fetchMarketCalendar(): Promise<any> {
  const res = await fetch(`${API_BASE}/data/calendar`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch market calendar");
  return res.json();
}

export async function fetchCorporateAnnouncements(limit = 10): Promise<CorporateAnnouncementItem[]> {
  const res = await fetch(`${API_BASE}/data/announcements?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch corporate announcements");
  return res.json();
}

// Multi-Symbol & Segmentation APIs
export async function runMultiSymbolBacktest(universeId = "LIQUID_TOP_10"): Promise<MultiSymbolResult> {
  const res = await fetch(`${API_BASE}/backtest/multi-symbol?universe_id=${universeId}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to execute multi-symbol backtest");
  return res.json();
}

export async function fetchSegmentationAnalysis(backtestId?: number): Promise<SegmentationAnalysisResult> {
  const url = backtestId ? `${API_BASE}/backtest/segmentation?backtest_id=${backtestId}` : `${API_BASE}/backtest/segmentation`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) throw new Error("Failed to fetch segmentation analysis");
  return res.json();
}

export async function runRollingWalkForward(symbol = "RELIANCE", windows = 3): Promise<any> {
  const res = await fetch(`${API_BASE}/backtest/rolling-walk-forward?symbol=${symbol}&windows=${windows}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to execute rolling walk-forward test");
  return res.json();
}

export async function fetchOverfittingScore(symbol = "RELIANCE"): Promise<OverfittingScoreResult> {
  const res = await fetch(`${API_BASE}/backtest/overfitting-score?symbol=${symbol}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to fetch overfitting risk score");
  return res.json();
}

export async function runEnhancedMonteCarlo(iterations = 1000): Promise<any> {
  const res = await fetch(`${API_BASE}/backtest/enhanced-monte-carlo?iterations=${iterations}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to execute enhanced Monte Carlo simulation");
  return res.json();
}

export async function fetchValidationReport(symbol = "RELIANCE"): Promise<StrategyValidationReportResponse> {
  const res = await fetch(`${API_BASE}/backtest/validation-report?symbol=${symbol}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to generate validation audit report");
  return res.json();
}

export async function runPhase6Validation(symbol = "RELIANCE", universeId = "LIQUID_TOP_10"): Promise<Phase6ValidationResult> {
  const res = await fetch(`${API_BASE}/backtest/phase6/validate?symbol=${symbol}&universe_id=${universeId}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to run Phase 6 empirical validation suite");
  return res.json();
}

export async function fetchPhase6Report(): Promise<{ markdown_content: string; validation_data: Phase6ValidationResult }> {
  const res = await fetch(`${API_BASE}/backtest/phase6/report`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch Phase 6 validation report");
  return res.json();
}

export async function fetchPhase6QualityAudit(symbol = "RELIANCE"): Promise<any> {
  const res = await fetch(`${API_BASE}/backtest/phase6/quality-audit?symbol=${symbol}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch dataset quality audit");
  return res.json();
}

// ==========================================
// PHASE 7: REAL-TIME LIVE PAPER TRADING APIs
// ==========================================

export async function fetchLiveStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/live/status`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch live status");
  return res.json();
}

export async function fetchLiveDataHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/live/data-health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch live data health");
  return res.json();
}

export async function fetchLiveSignals(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/live/signals`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch live signals");
  return res.json();
}

export async function fetchLivePositions(status = "OPEN"): Promise<any[]> {
  const res = await fetch(`${API_BASE}/live/positions?status=${status}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch live positions");
  return res.json();
}

export async function fetchLivePerformance(): Promise<any> {
  const res = await fetch(`${API_BASE}/live/performance`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch live performance");
  return res.json();
}

export async function approveLiveSignal(signalId: number): Promise<any> {
  const res = await fetch(`${API_BASE}/live/signal/${signalId}/approve`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to approve live signal");
  return res.json();
}

export async function rejectLiveSignal(signalId: number, reason = "User rejected"): Promise<any> {
  const res = await fetch(`${API_BASE}/live/signal/${signalId}/reject?reason=${encodeURIComponent(reason)}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to reject live signal");
  return res.json();
}

export async function triggerLiveEmergencyStop(reason = "Manual Emergency Stop"): Promise<any> {
  const res = await fetch(`${API_BASE}/live/emergency-stop?reason=${encodeURIComponent(reason)}`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger live emergency stop");
  return res.json();
}

export async function fetchLiveAuditLog(limit = 50): Promise<any[]> {
  const res = await fetch(`${API_BASE}/live/audit?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch live audit log");
  return res.json();
}

export async function fetchLiveSession(): Promise<any> {
  const res = await fetch(`${API_BASE}/live/session`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch live session state");
  return res.json();
}

export async function fetchLiveReplay(signalId: number): Promise<any> {
  const res = await fetch(`${API_BASE}/live/replay/${signalId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch live session replay");
  return res.json();
}

export async function ingestLiveTick(tick: any): Promise<any> {
  const res = await fetch(`${API_BASE}/live/tick`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tick)
  });
  if (!res.ok) throw new Error("Failed to ingest live tick");
  return res.json();
}

export async function triggerLiveSquareOff(): Promise<any> {
  const res = await fetch(`${API_BASE}/live/square-off`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger square-off");
  return res.json();
}

export async function fetchPhase7Report(): Promise<{ markdown_content: string; session_data: any }> {
  const res = await fetch(`${API_BASE}/live/report`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch Phase 7 report");
  return res.json();
}

// ==========================================
// MOBILE NOTIFICATIONS & TELEGRAM BOT APIs
// ==========================================

export async function fetchNotificationStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/notifications/status`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch notification status");
  return res.json();
}

export async function fetchRecentAlerts(limit = 30): Promise<any> {
  const res = await fetch(`${API_BASE}/notifications/recent?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch recent notifications");
  return res.json();
}

export async function configureTelegram(bot_token: string, chat_id: string, enabled = true): Promise<any> {
  const res = await fetch(`${API_BASE}/notifications/configure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bot_token, chat_id, enabled })
  });
  if (!res.ok) throw new Error("Failed to configure Telegram bot");
  return res.json();
}

export async function sendTestNotification(custom_message?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/notifications/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ custom_message })
  });
  if (!res.ok) throw new Error("Failed to send test notification");
  return res.json();
}

// ==========================================
// PHASE 6: GO-LIVE CRITERIA & EOD REPORT APIs
// ==========================================

export async function fetchGoLiveChecklist(): Promise<any> {
  const res = await fetch(`${API_BASE}/system/go-live-checklist`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch Go-Live checklist");
  return res.json();
}

export async function toggleLiveTrading(enable: boolean): Promise<any> {
  const res = await fetch(`${API_BASE}/system/toggle-live-trading`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enable })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to toggle live trading");
  return data;
}

export async function triggerEodReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/system/trigger-eod-report`, {
    method: "POST"
  });
  if (!res.ok) throw new Error("Failed to trigger EOD report");
  return res.json();
}

// ==========================================
// PHASE 9: CUMULATIVE EVIDENCE REPORT APIs
// ==========================================

export async function fetchCumulativePilotReport(): Promise<any> {
  const res = await fetch(`${API_BASE}/phase9/report?report_type=cumulative`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch cumulative pilot report");
  return res.json();
}

export async function fetchPilotSessions(limit: number = 50): Promise<any> {
  const res = await fetch(`${API_BASE}/phase9/sessions?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch pilot sessions");
  return res.json();
}



