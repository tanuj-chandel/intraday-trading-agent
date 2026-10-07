"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import {
  runBacktest,
  fetchLatestBacktest,
  fetchBacktestStrategies,
  fetchSystemStatus,
  runMultiSymbolBacktest,
  fetchSegmentationAnalysis,
  runRollingWalkForward,
  fetchOverfittingScore,
  runEnhancedMonteCarlo,
  fetchValidationReport,
  runPhase6Validation,
  fetchPhase6Report,
  fetchPhase6QualityAudit
} from "@/lib/api";
import {
  BacktestResult,
  SystemStatus,
  MultiSymbolResult,
  SegmentationAnalysisResult,
  OverfittingScoreResult,
  StrategyValidationReportResponse,
  Phase6ValidationResult
} from "@/types";
import { formatINR, formatPercent } from "@/lib/utils";
import {
  BarChart3,
  Play,
  Sliders,
  FileSpreadsheet,
  Activity,
  Layers,
  Sparkles,
  Award,
  AlertTriangle,
  Clock,
  ArrowUpDown,
  TrendingUp,
  Percent,
  Download,
  FileText,
  ShieldAlert,
  HelpCircle,
  CheckCircle2,
  XCircle,
  Flame
} from "lucide-react";

export default function BacktestingPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [strategies, setStrategies] = useState<any[]>([]);

  // Form State
  const [selectedStrategy, setSelectedStrategy] = useState("VWAP_EMA_MOMENTUM_V1");
  const [selectedSymbol, setSelectedSymbol] = useState("RELIANCE");
  const [initialCapital, setInitialCapital] = useState(100000);
  const [riskPerTrade, setRiskPerTrade] = useState(0.01);
  const [slippagePct, setSlippagePct] = useState(0.05);
  const [fastEma, setFastEma] = useState(9);
  const [slowEma, setSlowEma] = useState(21);
  const [minRvol, setMinRvol] = useState(1.15);

  // Core Result State
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [multiSymbolRes, setMultiSymbolRes] = useState<MultiSymbolResult | null>(null);
  const [segmentationRes, setSegmentationRes] = useState<SegmentationAnalysisResult | null>(null);
  const [rollingWfRes, setRollingWfRes] = useState<any>(null);
  const [overfittingRes, setOverfittingRes] = useState<OverfittingScoreResult | null>(null);
  const [enhancedMcRes, setEnhancedMcRes] = useState<any>(null);
  const [validationReport, setValidationReport] = useState<StrategyValidationReportResponse | null>(null);
  const [phase6Res, setPhase6Res] = useState<Phase6ValidationResult | null>(null);

  // UI Tabs
  const [activeTab, setActiveTab] = useState<
    "PHASE6_OVERVIEW" | "TRADES" | "MULTI_SYMBOL" | "REGIMES" | "TIME_OF_DAY" | "LONG_SHORT" | "COST_SLIPPAGE" | "ROLLING_WF" | "MONTE_CARLO" | "BENCHMARKS" | "REPORT"
  >("PHASE6_OVERVIEW");

  const [isRunning, setIsRunning] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  useEffect(() => {
    fetchSystemStatus().then(setStatus).catch(() => {});
    fetchBacktestStrategies().then(setStrategies).catch(() => {});
    fetchLatestBacktest().then((res) => {
      setResult(res);
      fetchSegmentationAnalysis().then(setSegmentationRes).catch(() => {});
      fetchOverfittingScore("RELIANCE").then(setOverfittingRes).catch(() => {});
    }).catch(() => {});

    // Initial Phase 6 Validation Run
    runPhase6Validation("RELIANCE", "LIQUID_TOP_10").then(setPhase6Res).catch(() => {});
  }, []);

  const handleRunBacktest = async () => {
    setIsRunning(true);
    try {
      const res = await runBacktest({
        strategy_id: selectedStrategy,
        symbol: selectedSymbol,
        initial_capital: initialCapital,
        risk_per_trade_pct: riskPerTrade,
        slippage_pct: slippagePct / 100.0,
        strategy_params: {
          ema_fast: fastEma,
          ema_slow: slowEma,
          min_rvol: minRvol
        }
      });
      setResult(res);
      const [seg, ovf, p6] = await Promise.all([
        fetchSegmentationAnalysis(),
        fetchOverfittingScore(selectedSymbol),
        runPhase6Validation(selectedSymbol, "LIQUID_TOP_10")
      ]);
      setSegmentationRes(seg);
      setOverfittingRes(ovf);
      setPhase6Res(p6);
      showNotification(`Backtest Complete! Net P&L: ₹${res.net_pnl}`);
    } catch (err: any) {
      showNotification(`Backtest failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunMultiSymbol = async (universeId: string) => {
    setIsValidating(true);
    try {
      const res = await runMultiSymbolBacktest(universeId);
      setMultiSymbolRes(res);
      setActiveTab("MULTI_SYMBOL");
      showNotification(`Multi-symbol backtest across ${res.symbols_evaluated} stocks complete.`);
    } catch (err: any) {
      showNotification(`Multi-symbol failed: ${err.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  const handleRunRollingWf = async () => {
    setIsValidating(true);
    try {
      const res = await runRollingWalkForward(selectedSymbol, 3);
      setRollingWfRes(res);
      setActiveTab("ROLLING_WF");
      showNotification("Rolling Walk-Forward (3 windows) complete.");
    } catch (err: any) {
      showNotification(`Rolling WF failed: ${err.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  const handleRunEnhancedMc = async () => {
    setIsValidating(true);
    try {
      const res = await runEnhancedMonteCarlo(1000);
      setEnhancedMcRes(res);
      setActiveTab("MONTE_CARLO");
      showNotification("Dual-Mode Monte Carlo (1,000x) complete.");
    } catch (err: any) {
      showNotification(`Monte Carlo failed: ${err.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  const handleGenerateReport = async () => {
    setIsValidating(true);
    try {
      const rep = await fetchValidationReport(selectedSymbol);
      setValidationReport(rep);
      setActiveTab("REPORT");
      showNotification("Strategy Validation Audit Report generated!");
    } catch (err: any) {
      showNotification(`Report generation failed: ${err.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090c10]">
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 bg-purple-600 text-white px-4 py-2.5 rounded-lg shadow-xl border border-purple-400 font-semibold text-xs animate-bounce">
          {notification}
        </div>
      )}

      {/* Header */}
      <Header status={status} />

      <main className="max-w-[1600px] w-full mx-auto p-4 flex-1 space-y-4">
        {/* Phase 6 Final Verdict Banner */}
        {phase6Res && (
          <div className="bg-gradient-to-r from-purple-950/60 via-[#121721] to-slate-900 border-2 border-purple-600/50 rounded-xl p-4 shadow-2xl flex flex-col lg:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/40">
                <ShieldAlert className="h-7 w-7 animate-pulse text-amber-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold text-gray-400 tracking-widest">
                    Phase 6 Empirical Validation Verdict
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    STATUS = NO GENUINE HISTORICAL DATA AVAILABLE
                  </span>
                </div>
                <h1 className="text-xl font-black text-white tracking-wide mt-0.5">
                  {phase6Res.final_verdict}
                </h1>
                <p className="text-xs text-gray-300 max-w-3xl mt-0.5">
                  {phase6Res.verdict_explanation}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 flex-wrap justify-end">
              <div className="bg-[#090c10] border border-[#1e2638] px-3 py-2 rounded-lg text-center min-w-[110px]">
                <span className="text-[9px] uppercase text-gray-400 font-bold block">Data Quality</span>
                <span className="text-sm font-black text-amber-400">
                  {phase6Res.data_quality_audit.data_quality_score}/100
                </span>
              </div>

              <div className="bg-[#090c10] border border-[#1e2638] px-3 py-2 rounded-lg text-center min-w-[110px]">
                <span className="text-[9px] uppercase text-gray-400 font-bold block">Overfitting Risk</span>
                <span className="text-sm font-black text-blue-400">
                  {phase6Res.overfitting.overfitting_risk_score}/100
                </span>
              </div>

              <div className="bg-[#090c10] border border-[#1e2638] px-3 py-2 rounded-lg text-center min-w-[110px]">
                <span className="text-[9px] uppercase text-gray-400 font-bold block">Stock Conc.</span>
                <span className="text-xs font-bold text-emerald-400">
                  {phase6Res.stock_concentration.stock_concentration_flag === "BALANCED_DIVERSIFICATION" ? "BALANCED" : "CONCENTRATED"}
                </span>
              </div>

              <button
                onClick={handleGenerateReport}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs transition-all shadow-lg hover:shadow-emerald-600/30"
              >
                <Download className="h-4 w-4" /> Download Report (.md)
              </button>
            </div>
          </div>
        )}

        {/* Configuration Bar */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sliders className="h-4 w-4 text-purple-400" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
                Frozen Baseline Parameters & Empirical Scans
              </h2>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
              <span>Baseline: <strong>VWAP_EMA_MOMENTUM_V1</strong></span>
              <span>|</span>
              <span>SL: <strong>1.5x ATR</strong></span>
              <span>|</span>
              <span>TP: <strong>3.0x ATR</strong></span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
            <div>
              <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Strategy</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-white w-full font-mono text-xs focus:outline-none"
              >
                <option value="VWAP_EMA_MOMENTUM_V1">VWAP + EMA Dynamic v1.0 (Frozen)</option>
              </select>
            </div>

            <div>
              <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Symbol</label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-white w-full font-mono text-xs focus:outline-none"
              >
                <option value="RELIANCE">RELIANCE (5m Sample)</option>
                <option value="HDFCBANK">HDFCBANK (5m Sample)</option>
                <option value="TATAMOTORS">TATAMOTORS (5m Sample)</option>
                <option value="INFY">INFY (5m Sample)</option>
              </select>
            </div>

            <div>
              <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Fast EMA ({fastEma})</label>
              <input
                type="number"
                value={fastEma}
                onChange={(e) => setFastEma(Number(e.target.value))}
                className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-white w-full font-mono text-xs focus:outline-none"
              />
            </div>

            <div>
              <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Slow EMA ({slowEma})</label>
              <input
                type="number"
                value={slowEma}
                onChange={(e) => setSlowEma(Number(e.target.value))}
                className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-white w-full font-mono text-xs focus:outline-none"
              />
            </div>

            <div>
              <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Min RVOL ({minRvol})</label>
              <input
                type="number"
                step="0.05"
                value={minRvol}
                onChange={(e) => setMinRvol(Number(e.target.value))}
                className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-white w-full font-mono text-xs focus:outline-none"
              />
            </div>

            <div>
              <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Slippage ({slippagePct}%)</label>
              <input
                type="number"
                step="0.01"
                value={slippagePct}
                onChange={(e) => setSlippagePct(Number(e.target.value))}
                className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-white w-full font-mono text-xs focus:outline-none"
              />
            </div>
          </div>

          <div className="flex items-center justify-between mt-4 pt-3 border-t border-[#1e2638] flex-wrap gap-2">
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={() => handleRunMultiSymbol("LIQUID_TOP_10")}
                disabled={isValidating}
                className="px-3 py-1.5 rounded-lg bg-[#1e2638] hover:bg-[#2a364f] text-gray-200 text-xs font-semibold border border-[#2e3a52] transition-colors"
              >
                Liquid Top 10 Universe
              </button>

              <button
                onClick={handleRunRollingWf}
                disabled={isValidating}
                className="px-3 py-1.5 rounded-lg bg-[#1e2638] hover:bg-[#2a364f] text-gray-200 text-xs font-semibold border border-[#2e3a52] transition-colors"
              >
                Rolling Walk-Forward
              </button>

              <button
                onClick={handleRunEnhancedMc}
                disabled={isValidating}
                className="px-3 py-1.5 rounded-lg bg-[#1e2638] hover:bg-[#2a364f] text-gray-200 text-xs font-semibold border border-[#2e3a52] transition-colors"
              >
                Dual Monte Carlo
              </button>
            </div>

            <button
              onClick={handleRunBacktest}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition-colors disabled:opacity-50"
            >
              <Play className={`h-3.5 w-3.5 ${isRunning ? "animate-spin" : ""}`} />
              {isRunning ? "Simulating..." : "Run Baseline Backtest"}
            </button>
          </div>
        </div>

        {/* Scorecard */}
        {result && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            <div className="bg-[#121721] border border-[#1e2638] p-3 rounded-xl">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Total Return</span>
              <span className={`text-base font-black ${result.return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {formatPercent(result.return_pct)}
              </span>
            </div>

            <div className="bg-[#121721] border border-[#1e2638] p-3 rounded-xl">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Net P&L</span>
              <span className={`text-base font-black ${result.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {formatINR(result.net_pnl)}
              </span>
            </div>

            <div className="bg-[#121721] border border-[#1e2638] p-3 rounded-xl">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Profit Factor</span>
              <span className="text-base font-black text-blue-400">{result.profit_factor.toFixed(2)}</span>
            </div>

            <div className="bg-[#121721] border border-[#1e2638] p-3 rounded-xl">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Win Rate</span>
              <span className="text-base font-black text-white">{result.win_rate.toFixed(1)}%</span>
            </div>

            <div className="bg-[#121721] border border-[#1e2638] p-3 rounded-xl">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Max Drawdown</span>
              <span className="text-base font-black text-rose-400">{result.max_drawdown_pct.toFixed(2)}%</span>
            </div>

            <div className="bg-[#121721] border border-[#1e2638] p-3 rounded-xl">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Expectancy</span>
              <span className="text-base font-black text-purple-400">{formatINR(result.expectancy)}</span>
            </div>

            <div className="bg-[#121721] border border-[#1e2638] p-3 rounded-xl">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Trades Count</span>
              <span className="text-base font-black text-white">{result.total_trades}</span>
            </div>

            <div className="bg-[#121721] border border-[#1e2638] p-3 rounded-xl">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Statutory Taxes</span>
              <span className="text-base font-black text-amber-400">{formatINR(result.total_charges)}</span>
            </div>
          </div>
        )}

        {/* Tabbed Analytical Section */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
          <div className="flex items-center justify-between border-b border-[#1e2638] pb-3 mb-3 overflow-x-auto gap-2">
            <div className="flex items-center gap-1 bg-[#090c10] p-1 rounded-lg border border-[#1e2638]">
              <button
                onClick={() => setActiveTab("PHASE6_OVERVIEW")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "PHASE6_OVERVIEW" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Phase 6 Scorecard
              </button>

              <button
                onClick={() => setActiveTab("TRADES")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "TRADES" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Trade Journal
              </button>

              <button
                onClick={() => setActiveTab("MULTI_SYMBOL")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "MULTI_SYMBOL" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Universe Leaderboard
              </button>

              <button
                onClick={() => setActiveTab("REGIMES")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "REGIMES" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Regime Matrix
              </button>

              <button
                onClick={() => setActiveTab("TIME_OF_DAY")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "TIME_OF_DAY" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Time of Day
              </button>

              <button
                onClick={() => setActiveTab("LONG_SHORT")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "LONG_SHORT" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Long vs Short
              </button>

              <button
                onClick={() => setActiveTab("COST_SLIPPAGE")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "COST_SLIPPAGE" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Cost & Slippage
              </button>

              <button
                onClick={() => setActiveTab("ROLLING_WF")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "ROLLING_WF" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Rolling Walk-Forward
              </button>

              <button
                onClick={() => setActiveTab("MONTE_CARLO")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "MONTE_CARLO" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Dual Monte Carlo
              </button>

              <button
                onClick={() => setActiveTab("BENCHMARKS")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "BENCHMARKS" ? "bg-purple-600 text-white" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                Benchmarks
              </button>

              <button
                onClick={() => setActiveTab("REPORT")}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  activeTab === "REPORT" ? "bg-emerald-600 text-white" : "text-emerald-400 hover:text-emerald-300"
                }`}
              >
                Audit Report
              </button>
            </div>
          </div>

          {/* TAB: PHASE 6 SCORECARD */}
          {activeTab === "PHASE6_OVERVIEW" && phase6Res && (
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-xl space-y-2">
                  <span className="font-bold text-amber-400 uppercase text-xs block">Data Quality Audit</span>
                  <div className="space-y-1 text-gray-300">
                    <div className="flex justify-between"><span>Score:</span> <strong className="text-white font-mono">{phase6Res.data_quality_audit.data_quality_score}/100 ({phase6Res.data_quality_audit.quality_rating})</strong></div>
                    <div className="flex justify-between"><span>Total Candles:</span> <strong className="text-white font-mono">{phase6Res.data_quality_audit.total_candles}</strong></div>
                    <div className="flex justify-between"><span>Trading Days:</span> <strong className="text-white font-mono">{phase6Res.data_quality_audit.unique_trading_days}</strong></div>
                    <div className="flex justify-between"><span>Duplicates:</span> <strong className="text-white font-mono">{phase6Res.data_quality_audit.duplicate_candles_pct}%</strong></div>
                    <div className="flex justify-between"><span>OHLC Violations:</span> <strong className="text-emerald-400 font-mono">{phase6Res.data_quality_audit.invalid_ohlc_count}</strong></div>
                  </div>
                </div>

                <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-xl space-y-2">
                  <span className="font-bold text-purple-400 uppercase text-xs block">Concentration Risks</span>
                  <div className="space-y-1 text-gray-300">
                    <div className="flex justify-between"><span>Stock Concentration:</span> <strong className="text-emerald-400 font-mono">{phase6Res.stock_concentration.stock_concentration_flag}</strong></div>
                    <div className="flex justify-between"><span>Top 3 Stocks Contribution:</span> <strong className="text-white font-mono">{phase6Res.stock_concentration.top_3_stock_contribution_pct}%</strong></div>
                    <div className="flex justify-between"><span>Trade Concentration:</span> <strong className="text-emerald-400 font-mono">{phase6Res.trade_concentration.trade_concentration_flag}</strong></div>
                    <div className="flex justify-between"><span>Top 5% Trades Gain:</span> <strong className="text-white font-mono">{phase6Res.trade_concentration.top_5pct_trade_contribution_pct}%</strong></div>
                  </div>
                </div>

                <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-xl space-y-2">
                  <span className="font-bold text-blue-400 uppercase text-xs block">Overfitting & OOS Stability</span>
                  <div className="space-y-1 text-gray-300">
                    <div className="flex justify-between"><span>Risk Index:</span> <strong className="text-white font-mono">{phase6Res.overfitting.overfitting_risk_score}/100 ({phase6Res.overfitting.risk_level})</strong></div>
                    <div className="flex justify-between"><span>OOS Performance Drop:</span> <strong className="text-white font-mono">{phase6Res.overfitting.metrics_comparison.oos_degradation_pct}%</strong></div>
                    <div className="flex justify-between"><span>Train Profit Factor:</span> <strong className="text-white font-mono">{phase6Res.overfitting.metrics_comparison.train_profit_factor.toFixed(2)}</strong></div>
                    <div className="flex justify-between"><span>OOS Profit Factor:</span> <strong className="text-white font-mono">{phase6Res.overfitting.metrics_comparison.oos_profit_factor.toFixed(2)}</strong></div>
                  </div>
                </div>
              </div>

              {/* 6-Level Slippage Grid */}
              <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-xl space-y-3">
                <span className="font-bold text-cyan-400 uppercase text-xs block">
                  6-Level Slippage Sensitivity Degradation Scan
                </span>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#1e2638] text-gray-400 uppercase text-[10px]">
                        <th className="py-2 px-3">Slippage Level</th>
                        <th className="py-2 px-3 text-right">Slippage Cost (INR)</th>
                        <th className="py-2 px-3 text-right">Net P&L (INR)</th>
                        <th className="py-2 px-3 text-right">Net Return %</th>
                        <th className="py-2 px-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1e2638]/50 font-mono">
                      {phase6Res.slippage_grid.map((s, idx) => (
                        <tr key={idx} className="hover:bg-[#182030]/60">
                          <td className="py-2 px-3 text-white font-bold">{s.slippage_pct}%</td>
                          <td className="py-2 px-3 text-right text-gray-300">{formatINR(s.slippage_cost_inr)}</td>
                          <td className={`py-2 px-3 text-right font-bold ${s.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatINR(s.net_pnl)}</td>
                          <td className={`py-2 px-3 text-right font-bold ${s.return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatPercent(s.return_pct)}</td>
                          <td className="py-2 px-3 text-center">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${s.net_pnl >= 0 ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>
                              {s.net_pnl >= 0 ? "PROFITABLE" : "UNPROFITABLE"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB: TRADES */}
          {activeTab === "TRADES" && result && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1e2638] text-gray-400 uppercase text-[10px] bg-[#090c10]">
                    <th className="py-2.5 px-3">#</th>
                    <th className="py-2.5 px-3">Side</th>
                    <th className="py-2.5 px-3">Entry Time / Price</th>
                    <th className="py-2.5 px-3">Exit Time / Price</th>
                    <th className="py-2.5 px-3">Qty</th>
                    <th className="py-2.5 px-3 text-right">Net P&L</th>
                    <th className="py-2.5 px-3">Exit Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2638]/50 font-mono">
                  {result.trades.map((t) => (
                    <tr key={t.trade_id} className="hover:bg-[#182030]/60">
                      <td className="py-2 px-3 text-gray-400">{t.trade_id}</td>
                      <td className="py-2 px-3">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${t.direction === "BUY" ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"}`}>
                          {t.direction}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-gray-300">{new Date(t.entry_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} @ ₹{t.entry_price}</td>
                      <td className="py-2 px-3 text-gray-300">{new Date(t.exit_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} @ ₹{t.exit_price}</td>
                      <td className="py-2 px-3 text-white">{t.quantity}</td>
                      <td className={`py-2 px-3 text-right font-bold ${t.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatINR(t.net_pnl)}</td>
                      <td className="py-2 px-3 text-[11px] text-gray-400 font-sans">{t.reason_for_exit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB: MULTI-SYMBOL */}
          {activeTab === "MULTI_SYMBOL" && multiSymbolRes && (
            <div className="space-y-4 text-xs">
              <div className="p-3 bg-[#090c10] border border-[#1e2638] rounded-lg flex justify-between items-center text-xs">
                <span>Universe: <strong className="text-white">{multiSymbolRes.universe_id}</strong> ({multiSymbolRes.symbols_evaluated} Stocks)</span>
                <span>Portfolio Return: <strong className={multiSymbolRes.portfolio_summary.portfolio_return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}>{formatPercent(multiSymbolRes.portfolio_summary.portfolio_return_pct)}</strong></span>
                <span>Portfolio Win Rate: <strong className="text-white">{multiSymbolRes.portfolio_summary.portfolio_win_rate}%</strong></span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[#1e2638] text-gray-400 uppercase text-[10px] bg-[#090c10]">
                      <th className="py-2 px-3">Symbol</th>
                      <th className="py-2 px-3 text-center">Trades</th>
                      <th className="py-2 px-3 text-center">Win Rate</th>
                      <th className="py-2 px-3 text-center">Profit Factor</th>
                      <th className="py-2 px-3 text-right">Net P&L</th>
                      <th className="py-2 px-3 text-right">Max Drawdown</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2638]/50 font-mono">
                    {multiSymbolRes.stock_leaderboard.map((s, idx) => (
                      <tr key={idx} className="hover:bg-[#182030]/60">
                        <td className="py-2 px-3 text-white font-bold">{s.symbol}</td>
                        <td className="py-2 px-3 text-center text-gray-300">{s.trades}</td>
                        <td className="py-2 px-3 text-center text-gray-300">{s.win_rate}%</td>
                        <td className="py-2 px-3 text-center text-purple-400 font-bold">{s.profit_factor.toFixed(2)}</td>
                        <td className={`py-2 px-3 text-right font-bold ${s.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatINR(s.net_pnl)}</td>
                        <td className="py-2 px-3 text-right text-rose-400">{s.max_drawdown_pct.toFixed(2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB: REGIMES */}
          {activeTab === "REGIMES" && segmentationRes && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
              {Object.entries(segmentationRes.regimes.regime_matrix).map(([regime, data]) => (
                <div key={regime} className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg space-y-1">
                  <span className="font-bold text-white uppercase text-[10px] block text-purple-400">{regime}</span>
                  <div className="flex justify-between text-gray-300"><span>Trades:</span> <strong className="text-white font-mono">{data.trade_count}</strong></div>
                  <div className="flex justify-between text-gray-300"><span>Profit Factor:</span> <strong className="text-white font-mono">{data.profit_factor.toFixed(2)}</strong></div>
                  <div className="flex justify-between text-gray-300"><span>Win Rate:</span> <strong className="text-white font-mono">{data.win_rate}%</strong></div>
                  <div className="flex justify-between text-gray-300"><span>Net P&L:</span> <strong className={`font-mono ${data.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatINR(data.net_pnl)}</strong></div>
                </div>
              ))}
            </div>
          )}

          {/* TAB: TIME OF DAY */}
          {activeTab === "TIME_OF_DAY" && segmentationRes && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1e2638] text-gray-400 uppercase text-[10px] bg-[#090c10]">
                    <th className="py-2 px-3">Window</th>
                    <th className="py-2 px-3">Session Label</th>
                    <th className="py-2 px-3 text-center">Trades</th>
                    <th className="py-2 px-3 text-center">Win Rate</th>
                    <th className="py-2 px-3 text-center">PF</th>
                    <th className="py-2 px-3 text-right">Net P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2638]/50 font-mono">
                  {segmentationRes.time_of_day.time_of_day_breakdown.map((t, idx) => (
                    <tr key={idx} className="hover:bg-[#182030]/60">
                      <td className="py-2 px-3 text-white font-bold">{t.window}</td>
                      <td className="py-2 px-3 text-gray-300 font-sans">{t.session}</td>
                      <td className="py-2 px-3 text-center text-gray-400">{t.trades}</td>
                      <td className="py-2 px-3 text-center text-gray-300">{t.win_rate}%</td>
                      <td className="py-2 px-3 text-center text-purple-400 font-bold">{t.profit_factor.toFixed(2)}</td>
                      <td className={`py-2 px-3 text-right font-bold ${t.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatINR(t.net_pnl)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB: LONG VS SHORT */}
          {activeTab === "LONG_SHORT" && segmentationRes && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="bg-[#090c10] border border-emerald-500/30 p-4 rounded-lg space-y-2">
                <span className="font-bold text-emerald-400 block uppercase text-xs">Long Trades (BUY)</span>
                <div className="space-y-1 text-gray-300">
                  <div className="flex justify-between"><span>Trades Count:</span> <strong className="text-white font-mono">{segmentationRes.long_short.long_trades.trades}</strong></div>
                  <div className="flex justify-between"><span>Win Rate:</span> <strong className="text-white font-mono">{segmentationRes.long_short.long_trades.win_rate}%</strong></div>
                  <div className="flex justify-between"><span>Profit Factor:</span> <strong className="text-white font-mono">{segmentationRes.long_short.long_trades.profit_factor.toFixed(2)}</strong></div>
                  <div className="flex justify-between"><span>Net P&L:</span> <strong className="text-emerald-400 font-mono">{formatINR(segmentationRes.long_short.long_trades.net_pnl)}</strong></div>
                </div>
              </div>

              <div className="bg-[#090c10] border border-rose-500/30 p-4 rounded-lg space-y-2">
                <span className="font-bold text-rose-400 block uppercase text-xs">Short Trades (SELL)</span>
                <div className="space-y-1 text-gray-300">
                  <div className="flex justify-between"><span>Trades Count:</span> <strong className="text-white font-mono">{segmentationRes.long_short.short_trades.trades}</strong></div>
                  <div className="flex justify-between"><span>Win Rate:</span> <strong className="text-white font-mono">{segmentationRes.long_short.short_trades.win_rate}%</strong></div>
                  <div className="flex justify-between"><span>Profit Factor:</span> <strong className="text-white font-mono">{segmentationRes.long_short.short_trades.profit_factor.toFixed(2)}</strong></div>
                  <div className="flex justify-between"><span>Net P&L:</span> <strong className="text-rose-400 font-mono">{formatINR(segmentationRes.long_short.short_trades.net_pnl)}</strong></div>
                </div>
              </div>
            </div>
          )}

          {/* TAB: COST & SLIPPAGE */}
          {activeTab === "COST_SLIPPAGE" && segmentationRes && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-lg space-y-3">
                <span className="font-bold text-amber-400 block uppercase text-[10px]">Brokerage & Tax Scenarios</span>
                <div className="space-y-2 font-mono">
                  {segmentationRes.cost_slippage.cost_scenarios.map((c, idx) => (
                    <div key={idx} className="flex justify-between border-b border-gray-800 pb-1">
                      <span className="text-gray-300 font-sans">{c.tier}</span>
                      <span>Net: <strong className={c.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}>{formatINR(c.net_pnl)}</strong></span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-lg space-y-3">
                <span className="font-bold text-cyan-400 block uppercase text-[10px]">Slippage Degradation Matrix</span>
                <div className="space-y-2 font-mono">
                  {segmentationRes.cost_slippage.slippage_matrix.map((s, idx) => (
                    <div key={idx} className="flex justify-between border-b border-gray-800 pb-1">
                      <span className="text-gray-300">{s.slippage_pct}% Slippage</span>
                      <span>Cost: {formatINR(s.slippage_cost_inr)} | Net: <strong className={s.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}>{formatINR(s.net_pnl)}</strong></span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB: ROLLING WALK FORWARD */}
          {activeTab === "ROLLING_WF" && (
            <div className="space-y-3 text-xs">
              {!rollingWfRes ? (
                <div className="text-center py-6 text-gray-400">Click "Rolling Walk-Forward" above to generate rolling windows.</div>
              ) : (
                <div className="space-y-2">
                  <div className="p-3 bg-[#090c10] border border-purple-500/40 rounded-lg flex justify-between items-center text-xs">
                    <span>Overall Stability: <strong className="text-emerald-400">{rollingWfRes.overall_stability}</strong></span>
                    <span>Aggregate WFE Ratio: <strong className="text-white font-mono">{rollingWfRes.aggregate_wfe_ratio}</strong></span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {rollingWfRes.rolling_windows.map((w: any, idx: number) => (
                      <div key={idx} className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg space-y-1">
                        <span className="font-bold text-purple-400 block">{w.window}</span>
                        <div className="text-gray-300">Train PF: <strong className="text-white font-mono">{w.train_period.profit_factor.toFixed(2)}</strong></div>
                        <div className="text-gray-300">Val PF: <strong className="text-white font-mono">{w.validation_period.profit_factor.toFixed(2)}</strong></div>
                        <div className="text-gray-300">OOS PF: <strong className="text-white font-mono">{w.oos_period.profit_factor.toFixed(2)}</strong></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: DUAL MONTE CARLO */}
          {activeTab === "MONTE_CARLO" && (
            <div className="space-y-3 text-xs">
              {!enhancedMcRes ? (
                <div className="text-center py-6 text-gray-400">Click "Dual Monte Carlo" above to run bootstrap and reshuffling simulations.</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-lg space-y-2">
                    <span className="font-bold text-blue-400 block uppercase text-xs">Mode A: Bootstrap (With Replacement)</span>
                    <div className="space-y-1 text-gray-300 font-mono">
                      <div className="flex justify-between"><span>Median Return:</span> <strong className="text-white">{formatPercent(enhancedMcRes.mode_a_bootstrap.median_return_pct)}</strong></div>
                      <div className="flex justify-between"><span>95th %ile Max DD:</span> <strong className="text-rose-400">{enhancedMcRes.mode_a_bootstrap.p95_max_drawdown_pct.toFixed(2)}%</strong></div>
                      <div className="flex justify-between"><span>Worst Simulated DD:</span> <strong className="text-rose-400">{enhancedMcRes.mode_a_bootstrap.worst_simulated_drawdown_pct.toFixed(2)}%</strong></div>
                    </div>
                  </div>

                  <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-lg space-y-2">
                    <span className="font-bold text-purple-400 block uppercase text-xs">Mode B: Trade Reshuffle (Without Replacement)</span>
                    <div className="space-y-1 text-gray-300 font-mono">
                      <div className="flex justify-between"><span>Median Max DD:</span> <strong className="text-white">{enhancedMcRes.mode_b_reshuffle.median_max_drawdown_pct.toFixed(2)}%</strong></div>
                      <div className="flex justify-between"><span>95th %ile Max DD:</span> <strong className="text-rose-400">{enhancedMcRes.mode_b_reshuffle.p95_max_drawdown_pct.toFixed(2)}%</strong></div>
                      <div className="flex justify-between"><span>Max Losing Streak:</span> <strong className="text-amber-400">{enhancedMcRes.max_consecutive_losing_streak} trades</strong></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: BENCHMARKS */}
          {activeTab === "BENCHMARKS" && segmentationRes && (
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-[#090c10] border border-blue-500/30 rounded-lg text-blue-300 text-xs">
                {segmentationRes.benchmarks.alpha_assessment}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[#1e2638] text-gray-400 uppercase text-[10px] bg-[#090c10]">
                      <th className="py-2 px-3">Benchmark Name</th>
                      <th className="py-2 px-3 text-center">Return %</th>
                      <th className="py-2 px-3 text-center">Profit Factor</th>
                      <th className="py-2 px-3">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2638]/50 font-mono">
                    <tr className="bg-purple-950/20 font-bold">
                      <td className="py-2 px-3 text-purple-300">{segmentationRes.benchmarks.strategy.name} (Active Strategy)</td>
                      <td className={`py-2 px-3 text-center ${segmentationRes.benchmarks.strategy.return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {formatPercent(segmentationRes.benchmarks.strategy.return_pct)}
                      </td>
                      <td className="py-2 px-3 text-center text-white">{segmentationRes.benchmarks.strategy.profit_factor.toFixed(2)}</td>
                      <td className="py-2 px-3 text-gray-400 font-sans">Active intraday momentum model</td>
                    </tr>
                    {segmentationRes.benchmarks.benchmarks.map((b, idx) => (
                      <tr key={idx} className="hover:bg-[#182030]/60">
                        <td className="py-2 px-3 text-white">{b.name}</td>
                        <td className={`py-2 px-3 text-center ${b.return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{formatPercent(b.return_pct)}</td>
                        <td className="py-2 px-3 text-center text-gray-300">{b.profit_factor.toFixed(2)}</td>
                        <td className="py-2 px-3 text-gray-400 font-sans">{b.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB: VALIDATION AUDIT REPORT */}
          {activeTab === "REPORT" && (
            <div className="space-y-4 text-xs">
              <div className="flex justify-between items-center bg-[#090c10] p-3 rounded-lg border border-emerald-500/40">
                <span className="font-bold text-emerald-400">
                  {validationReport ? validationReport.report_title : "Phase 6 Strategy Validation Report"}
                </span>
                <button
                  onClick={() => {
                    const content = validationReport?.markdown_content || phase6Res?.report_files?.markdown_content || "# Phase 6 Report";
                    const blob = new Blob([content], { type: "text/markdown" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `phase6_strategy_validation.md`;
                    a.click();
                  }}
                  className="flex items-center gap-1.5 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs"
                >
                  <Download className="h-3.5 w-3.5" /> Download Report (.md)
                </button>
              </div>

              <pre className="bg-[#090c10] border border-[#1e2638] p-4 rounded-xl font-mono text-xs text-gray-300 whitespace-pre-wrap max-h-[500px] overflow-y-auto">
                {validationReport?.markdown_content || phase6Res?.report_files?.markdown_content || "Report loading..."}
              </pre>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
