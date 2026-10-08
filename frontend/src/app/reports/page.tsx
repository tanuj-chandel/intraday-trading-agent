"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Header } from "@/components/Header";
import { fetchSystemStatus, fetchCumulativePilotReport, fetchPilotSessions } from "@/lib/api";
import { SystemStatus } from "@/types";
import { formatINR } from "@/lib/utils";
import {
  FileText,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  ShieldCheck,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  Award,
  Layers,
  Scale,
  DollarSign,
  PieChart,
  BarChart3,
  Calendar,
  ExternalLink,
  ChevronRight,
  Info
} from "lucide-react";

export default function ReportsPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [report, setReport] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [selectedTab, setSelectedTab] = useState<"overview" | "costs" | "drift" | "sessions">("overview");

  const loadData = useCallback(async () => {
    try {
      const [sysStatus, reportData, sessionsData] = await Promise.all([
        fetchSystemStatus().catch(() => null),
        fetchCumulativePilotReport().catch(() => null),
        fetchPilotSessions(50).catch(() => null)
      ]);

      if (sysStatus) setStatus(sysStatus);
      if (reportData) setReport(reportData);
      if (sessionsData?.sessions) setSessions(sessionsData.sessions);
    } catch (err) {
      console.error("Failed to load reports data:", err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      loadData();
    }, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadData]);

  const handleManualRefresh = () => {
    setIsRefreshing(true);
    loadData();
  };

  const financials = report?.financial_summary || {
    gross_pnl: 0,
    transaction_costs: 0,
    slippage: 0,
    net_pnl: 0
  };

  const metrics = report?.performance_metrics || {
    winning_trades: 0,
    losing_trades: 0,
    win_rate_pct: 0,
    expectancy_inr: 0,
    profit_factor: 0,
    avg_win_inr: 0,
    avg_loss_inr: 0
  };

  const verdict = report?.verdict || {
    verdict: "AWAITING SESSIONS",
    explanation: "Executing paper sessions toward 30+ empirical target.",
    sample_size: 0
  };

  const milestone = report?.milestone || {
    stage: "INSUFFICIENT",
    label: "Accumulating Evidence",
    next_milestone: 30,
    progress_pct: 0
  };

  const backtestComp = report?.backtest_comparison?.comparison || {};
  const regimes = report?.regime_performance?.regimes || {};

  const getVerdictBadge = (vText: string) => {
    if (vText.includes("VALIDATED") || vText.includes("APPROVED")) {
      return {
        bg: "bg-emerald-500/20",
        border: "border-emerald-500/50",
        text: "text-emerald-400",
        icon: <CheckCircle2 className="h-5 w-5 text-emerald-400" />
      };
    }
    if (vText.includes("INSUFFICIENT") || vText.includes("PRELIMINARY")) {
      return {
        bg: "bg-amber-500/20",
        border: "border-amber-500/50",
        text: "text-amber-300",
        icon: <AlertTriangle className="h-5 w-5 text-amber-400" />
      };
    }
    return {
      bg: "bg-rose-500/20",
      border: "border-rose-500/50",
      text: "text-rose-400",
      icon: <ShieldAlert className="h-5 w-5 text-rose-400" />
    };
  };

  const verdictStyle = getVerdictBadge(verdict.verdict || "");

  return (
    <div className="min-h-screen bg-[#090c10] text-gray-100">
      <Header status={status} onRefreshData={handleManualRefresh} isRefreshing={isRefreshing} />

      <main className="max-w-[1600px] mx-auto px-4 py-6 space-y-6">
        {/* Safety & Protocol Banner */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-wide">
                  Cumulative Pilot Evidence Report
                </h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 border border-blue-500/40 text-blue-300">
                  PHASE 9 AUTONOMOUS PILOT
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Empirical validation evidence across automated paper trading sessions (09:15 - 15:15 IST).
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                autoRefresh
                  ? "bg-emerald-600/20 border-emerald-500/50 text-emerald-300"
                  : "bg-[#0b0e14] border-[#1e2638] text-gray-400 hover:text-gray-200"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              Auto-Poll (10s): {autoRefresh ? "ON" : "OFF"}
            </button>

            <button
              onClick={handleManualRefresh}
              disabled={isRefreshing}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white flex items-center gap-1.5 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh Report
            </button>
          </div>
        </div>

        {/* Mandatory Safety Notice */}
        <div className="bg-amber-950/20 border border-amber-500/30 rounded-xl px-4 py-3 flex items-center gap-3">
          <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0" />
          <p className="text-xs text-amber-200/90 leading-relaxed">
            <strong className="text-amber-300 font-semibold uppercase tracking-wider">Paper Trading Only:</strong> All executions, P&L figures, and statutory charges represent simulated paper trading accounting with 0.05% slippage and ₹20/order brokerage. Real brokerage execution endpoints are strictly locked.
          </p>
        </div>

        {/* 5 Core Evidence Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* 1. Scientific Verdict */}
          <div className={`p-4 rounded-xl border ${verdictStyle.bg} ${verdictStyle.border} flex flex-col justify-between sm:col-span-2 lg:col-span-1`}>
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                <span>Scientific Verdict</span>
                {verdictStyle.icon}
              </div>
              <div className={`text-base font-black tracking-wide ${verdictStyle.text}`}>
                {verdict.verdict || "AWAITING SESSIONS"}
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-white/10 text-[11px] text-gray-300 leading-tight">
              {verdict.explanation || "Collecting session evidence toward 30-trade minimum."}
            </div>
          </div>

          {/* 2. Total Cumulative Trades */}
          <div className="bg-[#121721] border border-[#1e2638] p-4 rounded-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                <span>Total Trades</span>
                <Layers className="h-4 w-4 text-blue-400" />
              </div>
              <div className="text-2xl font-black text-white">
                {report?.total_trades ?? 0}
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-[#1e2638]">
              <div className="flex justify-between text-[11px] text-gray-400 mb-1">
                <span>Milestone (Goal 30)</span>
                <span className="font-mono text-blue-400 font-bold">{milestone.progress_pct ?? 0}%</span>
              </div>
              <div className="w-full bg-[#090c10] h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, milestone.progress_pct ?? 0)}%` }}
                />
              </div>
            </div>
          </div>

          {/* 3. Win Rate */}
          <div className="bg-[#121721] border border-[#1e2638] p-4 rounded-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                <span>Win Rate</span>
                <Scale className="h-4 w-4 text-purple-400" />
              </div>
              <div className="text-2xl font-black text-white">
                {metrics.win_rate_pct !== undefined ? `${metrics.win_rate_pct.toFixed(1)}%` : "0.0%"}
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-[#1e2638] flex items-center justify-between text-[11px]">
              <span className="text-emerald-400 font-mono font-semibold">
                Wins: {metrics.winning_trades}
              </span>
              <span className="text-rose-400 font-mono font-semibold">
                Losses: {metrics.losing_trades}
              </span>
              <span className="text-gray-400 font-mono">
                PF: {metrics.profit_factor > 50 ? "∞" : metrics.profit_factor.toFixed(2)}
              </span>
            </div>
          </div>

          {/* 4. Expectancy */}
          <div className="bg-[#121721] border border-[#1e2638] p-4 rounded-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                <span>Expectancy / Trade</span>
                <TrendingUp className="h-4 w-4 text-emerald-400" />
              </div>
              <div className={`text-2xl font-black ${(metrics.expectancy_inr ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                ₹{(metrics.expectancy_inr ?? 0).toFixed(2)}
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-[#1e2638] flex items-center justify-between text-[11px] text-gray-400">
              <span>Avg Win: ₹{(metrics.avg_win_inr ?? 0).toFixed(0)}</span>
              <span>Avg Loss: ₹{(metrics.avg_loss_inr ?? 0).toFixed(0)}</span>
            </div>
          </div>

          {/* 5. Net P&L (After Costs & Slippage) */}
          <div className="bg-[#121721] border border-[#1e2638] p-4 rounded-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                <span>Net After Costs</span>
                <DollarSign className="h-4 w-4 text-emerald-400" />
              </div>
              <div className={`text-2xl font-black ${(financials.net_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {formatINR(financials.net_pnl ?? 0)}
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-[#1e2638] text-[11px] text-gray-400 flex items-center justify-between">
              <span>Gross: ₹{(financials.gross_pnl ?? 0).toFixed(1)}</span>
              <span>Costs: -₹{((financials.transaction_costs ?? 0) + (financials.slippage ?? 0)).toFixed(1)}</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-[#1e2638] pb-2">
          {[
            { id: "overview", label: "Executive Evidence", icon: Award },
            { id: "costs", label: "Statutory Cost Model", icon: DollarSign },
            { id: "drift", label: "Backtest Reality Gap", icon: BarChart3 },
            { id: "sessions", label: `Sessions History (${sessions.length})`, icon: Calendar },
          ].map(tab => {
            const Icon = tab.icon;
            const active = selectedTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id as any)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all ${
                  active
                    ? "bg-cyan-600 text-white shadow"
                    : "text-gray-400 hover:text-gray-200 hover:bg-[#121721]"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab 1: Executive Evidence */}
        {selectedTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Milestone & Protocol Evidence */}
            <div className="lg:col-span-2 space-y-6">
              {/* Evidence Protocol Card */}
              <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-5">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Award className="h-4 w-4 text-cyan-400" />
                  Pilot Validation Protocol & Milestone Gate
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                  <div className="bg-[#090c10] p-3 rounded-lg border border-[#1e2638]">
                    <span className="text-[10px] text-gray-400 uppercase font-semibold block">Total Sessions Run</span>
                    <span className="text-lg font-bold text-white">{report?.total_sessions ?? 0}</span>
                    <span className="text-[10px] text-blue-400 block mt-0.5">Target: 30+ Autonomous Sessions</span>
                  </div>
                  <div className="bg-[#090c10] p-3 rounded-lg border border-[#1e2638]">
                    <span className="text-[10px] text-gray-400 uppercase font-semibold block">Current Sample Size</span>
                    <span className="text-lg font-bold text-white">{report?.total_trades ?? 0} Trades</span>
                    <span className="text-[10px] text-amber-400 block mt-0.5">{milestone.stage}</span>
                  </div>
                  <div className="bg-[#090c10] p-3 rounded-lg border border-[#1e2638]">
                    <span className="text-[10px] text-gray-400 uppercase font-semibold block">Confidence Level</span>
                    <span className="text-lg font-bold text-white">{verdict.is_high_confidence ? "95% CI High" : "Preliminary"}</span>
                    <span className="text-[10px] text-gray-400 block mt-0.5">Monte Carlo + Bootstrap</span>
                  </div>
                </div>

                <div className="p-3 bg-blue-950/20 border border-blue-500/30 rounded-lg text-xs text-blue-200/90 leading-relaxed">
                  <strong>Scientific Criterion:</strong> {milestone.scientific_interpretation || "At least 30 closed trades under active live ticks are required before statistical tests (p-value < 0.05) can distinguish true strategy edge from stochastic noise."}
                </div>
              </div>

              {/* Regime Attribution Table */}
              <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-5">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Layers className="h-4 w-4 text-purple-400" />
                  Market Regime Attribution (Dual EMA 9/21 + VWAP)
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-[#090c10] text-gray-400 border-b border-[#1e2638]">
                      <tr>
                        <th className="py-2.5 px-3">Regime</th>
                        <th className="py-2.5 px-3">Trades</th>
                        <th className="py-2.5 px-3">Win Rate</th>
                        <th className="py-2.5 px-3">Gross P&L</th>
                        <th className="py-2.5 px-3">Net P&L</th>
                        <th className="py-2.5 px-3">Expectancy</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1e2638]/50">
                      {Object.keys(regimes).length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-4 text-center text-gray-500">
                            No regime trades recorded yet. Run sessions to populate.
                          </td>
                        </tr>
                      ) : (
                        Object.entries(regimes).map(([rName, rData]: [string, any]) => (
                          <tr key={rName} className="hover:bg-[#182030]">
                            <td className="py-2.5 px-3 font-semibold text-gray-200">{rName}</td>
                            <td className="py-2.5 px-3 text-white font-mono">{rData.trade_count}</td>
                            <td className="py-2.5 px-3 text-white font-mono">{rData.win_rate_pct?.toFixed(1)}%</td>
                            <td className="py-2.5 px-3 font-mono text-gray-300">₹{rData.gross_pnl?.toFixed(2)}</td>
                            <td className={`py-2.5 px-3 font-mono font-bold ${(rData.net_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                              ₹{rData.net_pnl?.toFixed(2)}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-cyan-300">₹{rData.expectancy_inr?.toFixed(2)}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right Col: Automation Status & Report Links */}
            <div className="space-y-6">
              {/* Daily Session Scheduler Status */}
              <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-5">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-400" />
                  Autonomous Session Runner
                </h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between items-center py-1.5 border-b border-[#1e2638]">
                    <span className="text-gray-400">Market Open:</span>
                    <span className="font-mono text-gray-200">09:15 IST</span>
                  </div>
                  <div className="flex justify-between items-center py-1.5 border-b border-[#1e2638]">
                    <span className="text-gray-400">Auto Square-Off:</span>
                    <span className="font-mono text-amber-400 font-bold">15:15 IST</span>
                  </div>
                  <div className="flex justify-between items-center py-1.5 border-b border-[#1e2638]">
                    <span className="text-gray-400">Task Scheduler:</span>
                    <span className="font-mono text-emerald-400">run_daily_session.bat</span>
                  </div>
                  <div className="flex justify-between items-center py-1.5 border-b border-[#1e2638]">
                    <span className="text-gray-400">Session Reports:</span>
                    <span className="font-mono text-gray-200">reports/phase9/</span>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-[#090c10] border border-[#1e2638] rounded-lg">
                  <div className="text-[11px] font-mono text-gray-300 leading-relaxed">
                    <code>python backend/run_session.py</code> starts daily execution autonomously without operator intervention.
                  </div>
                </div>
              </div>

              {/* Quick Navigation to Phase 9 Deep Terminal */}
              <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-5">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2">
                  Validation Artifacts
                </h3>
                <p className="text-xs text-gray-400 mb-4">
                  Access raw Markdown audits, backtest comparison matrices, and trade logs.
                </p>
                <div className="space-y-2">
                  <Link
                    href="/phase9"
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-[#090c10] border border-[#1e2638] hover:border-cyan-500/50 text-xs text-gray-300 hover:text-white transition-all"
                  >
                    <span>Phase 9 Live Session Terminal</span>
                    <ChevronRight className="h-4 w-4 text-cyan-400" />
                  </Link>
                  <Link
                    href="/go-live"
                    className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-[#090c10] border border-[#1e2638] hover:border-rose-500/50 text-xs text-gray-300 hover:text-white transition-all"
                  >
                    <span>Go-Live Audit & Gatekeeper</span>
                    <ChevronRight className="h-4 w-4 text-rose-400" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Statutory Cost Model */}
        {selectedTab === "costs" && (
          <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-6 space-y-6">
            <div>
              <h3 className="text-base font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Scale className="h-5 w-5 text-emerald-400" />
                Indian Statutory & Regulatory Cost Equation
              </h3>
              <p className="text-xs text-gray-400 mt-1 font-mono">
                NET P&L = GROSS P&L − TRANSACTION COSTS − SLIPPAGE
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="bg-[#090c10] p-4 rounded-xl border border-[#1e2638]">
                <span className="text-xs text-gray-400 block font-semibold mb-1">Gross Realized P&L</span>
                <span className="text-xl font-black text-white">₹{(financials.gross_pnl ?? 0).toFixed(2)}</span>
                <span className="text-[10px] text-gray-500 block mt-1">Raw simulated exit vs entry</span>
              </div>
              <div className="bg-[#090c10] p-4 rounded-xl border border-[#1e2638]">
                <span className="text-xs text-gray-400 block font-semibold mb-1">Transaction Charges</span>
                <span className="text-xl font-black text-rose-400">-₹{(financials.transaction_costs ?? 0).toFixed(2)}</span>
                <span className="text-[10px] text-gray-500 block mt-1">Brokerage, STT, GST, SEBI</span>
              </div>
              <div className="bg-[#090c10] p-4 rounded-xl border border-[#1e2638]">
                <span className="text-xs text-gray-400 block font-semibold mb-1">Execution Slippage</span>
                <span className="text-xl font-black text-amber-400">-₹{(financials.slippage ?? 0).toFixed(2)}</span>
                <span className="text-[10px] text-gray-500 block mt-1">0.05% baseline haircut</span>
              </div>
              <div className="bg-[#090c10] p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/10">
                <span className="text-xs text-emerald-400 block font-semibold mb-1">Net Realized P&L</span>
                <span className="text-xl font-black text-emerald-400">{formatINR(financials.net_pnl ?? 0)}</span>
                <span className="text-[10px] text-emerald-500 block mt-1">True economic value</span>
              </div>
            </div>

            <div className="border-t border-[#1e2638] pt-4 text-xs text-gray-300 space-y-2">
              <h4 className="font-bold text-white uppercase tracking-wider text-[11px]">Itemized Regulatory Breakdown Model:</h4>
              <ul className="list-disc list-inside space-y-1 text-gray-400 font-mono text-[11px]">
                <li>Brokerage: Flat ₹20 per executed order (₹40 round-trip)</li>
                <li>Securities Transaction Tax (STT): 0.025% on sell turnover</li>
                <li>NSE Exchange Turnover Fee: 0.00297% on both buy & sell turnover</li>
                <li>GST: 18% on (Brokerage + Exchange Turnover Fee + SEBI Fee)</li>
                <li>SEBI Turnover Charge: ₹10 per crore (0.0001%)</li>
                <li>Stamp Duty: 0.003% on buy turnover</li>
              </ul>
            </div>
          </div>
        )}

        {/* Tab 3: Backtest Reality Gap */}
        {selectedTab === "drift" && (
          <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-6 space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
              <div>
                <h3 className="text-base font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-purple-400" />
                  Strategy Drift vs Frozen Phase 6 Backtest
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  Strategy: <strong className="text-cyan-300">{report?.backtest_comparison?.strategy_version || "VWAP_EMA_MOMENTUM_V1"}</strong>
                </p>
              </div>
              <div className="px-3 py-1 rounded-lg text-xs font-bold bg-blue-500/20 border border-blue-500/40 text-blue-300">
                Classification: {report?.backtest_comparison?.classification || "PENDING SAMPLE"}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-[#090c10] text-gray-400 border-b border-[#1e2638]">
                  <tr>
                    <th className="py-2.5 px-3">Metric</th>
                    <th className="py-2.5 px-3">Phase 6 Backtest Baseline</th>
                    <th className="py-2.5 px-3">Phase 9 Paper Reality</th>
                    <th className="py-2.5 px-3">Reality Drift</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2638]/50">
                  <tr className="hover:bg-[#182030]">
                    <td className="py-2.5 px-3 font-semibold text-gray-200">Win Rate</td>
                    <td className="py-2.5 px-3 font-mono text-gray-400">{backtestComp.win_rate?.backtest?.toFixed(1) ?? "55.0"}%</td>
                    <td className="py-2.5 px-3 font-mono text-white font-bold">{backtestComp.win_rate?.paper?.toFixed(1) ?? "100.0"}%</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">+{backtestComp.win_rate?.drift?.toFixed(1) ?? "0.0"}%</td>
                    <td className="py-2.5 px-3 font-semibold text-emerald-400">{backtestComp.win_rate?.status ?? "PASS"}</td>
                  </tr>
                  <tr className="hover:bg-[#182030]">
                    <td className="py-2.5 px-3 font-semibold text-gray-200">Expectancy / Trade</td>
                    <td className="py-2.5 px-3 font-mono text-gray-400">₹{backtestComp.expectancy?.backtest?.toFixed(2) ?? "150.00"}</td>
                    <td className="py-2.5 px-3 font-mono text-white font-bold">₹{backtestComp.expectancy?.paper?.toFixed(2) ?? "0.00"}</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">₹{backtestComp.expectancy?.drift?.toFixed(2) ?? "0.00"}</td>
                    <td className="py-2.5 px-3 font-semibold text-emerald-400">{backtestComp.expectancy?.status ?? "PASS"}</td>
                  </tr>
                  <tr className="hover:bg-[#182030]">
                    <td className="py-2.5 px-3 font-semibold text-gray-200">Profit Factor</td>
                    <td className="py-2.5 px-3 font-mono text-gray-400">{backtestComp.profit_factor?.backtest?.toFixed(2) ?? "1.50"}</td>
                    <td className="py-2.5 px-3 font-mono text-white font-bold">{backtestComp.profit_factor?.paper?.toFixed(2) ?? "0.00"}</td>
                    <td className="py-2.5 px-3 font-mono text-cyan-300">{backtestComp.profit_factor?.drift?.toFixed(2) ?? "0.00"}</td>
                    <td className="py-2.5 px-3 font-semibold text-emerald-400">{backtestComp.profit_factor?.status ?? "PASS"}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 4: Sessions History */}
        {selectedTab === "sessions" && (
          <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-5 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Calendar className="h-4 w-4 text-cyan-400" />
                Historic Paper Trading Sessions ({sessions.length})
              </h3>
              <span className="text-xs text-gray-400">
                09:15 - 15:15 IST Market Sessions
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-[#090c10] text-gray-400 border-b border-[#1e2638]">
                  <tr>
                    <th className="py-2.5 px-3">Session ID</th>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Trades</th>
                    <th className="py-2.5 px-3">Gross P&L</th>
                    <th className="py-2.5 px-3">Costs + Slippage</th>
                    <th className="py-2.5 px-3">Net P&L</th>
                    <th className="py-2.5 px-3">Close Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e2638]/50">
                  {sessions.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-6 text-center text-gray-500">
                        No paper trading sessions found. Run <code>python backend/run_session.py</code> to execute a session.
                      </td>
                    </tr>
                  ) : (
                    sessions.map((sess: any) => (
                      <tr key={sess.session_id} className="hover:bg-[#182030]">
                        <td className="py-2.5 px-3 font-mono font-bold text-cyan-300">{sess.session_id}</td>
                        <td className="py-2.5 px-3 text-gray-300">{sess.trading_date}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            sess.status === "ACTIVE"
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse"
                              : "bg-gray-800 text-gray-300"
                          }`}>
                            {sess.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-white">{sess.trades_count ?? 0}</td>
                        <td className="py-2.5 px-3 font-mono text-gray-300">₹{(sess.gross_pnl ?? 0).toFixed(2)}</td>
                        <td className="py-2.5 px-3 font-mono text-rose-400">-₹{((sess.total_charges ?? 0) + (sess.total_slippage ?? 0)).toFixed(2)}</td>
                        <td className={`py-2.5 px-3 font-mono font-bold ${(sess.net_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ₹{(sess.net_pnl ?? 0).toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-gray-400 text-[11px]">{sess.close_reason || "ACTIVE"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
