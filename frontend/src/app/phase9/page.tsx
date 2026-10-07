"use client";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ShieldAlert, Activity, RefreshCw, BarChart2, Clock, PieChart, CheckCircle2, AlertTriangle, FileText, Play, Square } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000/api/phase9";

export default function Phase9Dashboard() {
  const [status, setStatus] = useState<any>(null);
  const [session, setSession] = useState<any>(null);
  const [comparison, setComparison] = useState<any>(null);
  const [evidence, setEvidence] = useState<any>(null);
  const [regimes, setRegimes] = useState<any>(null);
  const [timeSlots, setTimeSlots] = useState<any>(null);
  const [concentration, setConcentration] = useState<any>(null);
  const [dqImpact, setDqImpact] = useState<any>(null);
  const [verdict, setVerdict] = useState<any>(null);
  const [trades, setTrades] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"backtest" | "regimes" | "time" | "concentration" | "data_quality" | "trades">("backtest");
  const [isLoading, setIsLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [
        statusRes,
        sessRes,
        compRes,
        evRes,
        regRes,
        timeRes,
        concRes,
        dqRes,
        verdRes,
        tradesRes
      ] = await Promise.all([
        fetch(`${API_BASE}/status`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/session/current`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/backtest-comparison`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/statistics`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/regime-performance`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/time-performance`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/concentration`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/data-quality-impact`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/verdict`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/trades?limit=50`).then(r => r.json()).catch(() => null),
      ]);

      if (statusRes) setStatus(statusRes);
      if (sessRes) setSession(sessRes.session);
      if (compRes) setComparison(compRes);
      if (evRes) setEvidence(evRes);
      if (regRes) setRegimes(regRes);
      if (timeRes) setTimeSlots(timeRes);
      if (concRes) setConcentration(concRes);
      if (dqImpact) setDqImpact(dqRes);
      if (verdRes) setVerdict(verdRes);
      if (tradesRes?.trades) setTrades(tradesRes.trades);
    } catch (err) {
      console.error("Phase 9 fetch error", err);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleStartSession = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/session/start?provider=ZERODHA_KITE`, { method: "POST" });
      const data = await res.json();
      setActionMsg(data.message || "Session started");
      fetchData();
    } catch (e: any) {
      setActionMsg("Failed to start session");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseSession = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/session/close?reason=MANUAL_CLOSE`, { method: "POST" });
      const data = await res.json();
      setActionMsg(data.message || "Session closed");
      fetchData();
    } catch (e: any) {
      setActionMsg("Failed to close session");
    } finally {
      setIsLoading(false);
    }
  };

  const totalTrades = evidence?.sample_size ?? trades.length;
  const milestoneStage = evidence?.milestone?.stage ?? "INSUFFICIENT";
  const metrics = evidence?.metrics ?? {};
  const uiMode = status?.data_mode ?? { badge: "⚪ MOCK / SIMULATION", color: "slate" };

  // Calculate milestone progress targets
  const milestones = [
    { target: 30, label: "Early", active: totalTrades >= 30 },
    { target: 100, label: "Preliminary", active: totalTrades >= 100 },
    { target: 300, label: "Empirical", active: totalTrades >= 300 },
    { target: 500, label: "High-Confidence", active: totalTrades >= 500 },
  ];

  return (
    <div className="min-h-screen bg-[#090c10] text-gray-200 p-4 md:p-6 font-sans">
      <div className="max-w-[1600px] mx-auto space-y-6">

        {/* ── TOP BANNER: Strict Safety & Provenance ───────────────────────── */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 flex flex-col lg:flex-row items-center justify-between gap-4 shadow-lg">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 border border-amber-500/50 text-amber-300 animate-pulse">
                <span className="h-2 w-2 rounded-full bg-amber-400"></span>
                PAPER TRADING ONLY — NO REAL MONEY ORDERS
              </span>
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-rose-950/50 border border-rose-500/40 text-rose-300">
                REAL ORDERS: STRICTLY DISABLED
              </span>
            </div>

            {/* Data Mode Badge */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 font-semibold">DATA MODE:</span>
              <span className={`text-xs font-bold font-mono px-3 py-1 rounded-full border ${
                uiMode.color === "emerald"
                  ? "bg-emerald-500/20 border-emerald-500/60 text-emerald-300"
                  : uiMode.color === "amber"
                  ? "bg-amber-500/20 border-amber-500/60 text-amber-300"
                  : uiMode.color === "rose"
                  ? "bg-rose-500/20 border-rose-500/60 text-rose-300"
                  : "bg-slate-700/30 border-slate-600 text-slate-300"
              }`}>
                {uiMode.badge}
              </span>
            </div>

            {/* Session indicator */}
            <div className="text-xs text-gray-400 font-mono">
              SESSION: <strong className="text-blue-400">{session?.session_id || "NONE"}</strong> ({session?.trading_date || "N/A"})
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={fetchData}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1a2234] hover:bg-[#222d44] border border-[#2a3754] text-xs font-semibold text-gray-300 transition-all"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </button>
            <button
              onClick={handleStartSession}
              disabled={isLoading || session?.status === "ACTIVE"}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/80 hover:bg-blue-600 disabled:opacity-40 text-xs font-bold text-white transition-all"
            >
              <Play className="h-3.5 w-3.5" />
              Start Session
            </button>
            <button
              onClick={handleCloseSession}
              disabled={isLoading || session?.status !== "ACTIVE"}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600/80 hover:bg-rose-600 disabled:opacity-40 text-xs font-bold text-white transition-all"
            >
              <Square className="h-3.5 w-3.5" />
              Close Session
            </button>
            <Link
              href="/api/phase9/report?report_type=cumulative"
              target="_blank"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/80 hover:bg-emerald-600 text-xs font-bold text-white transition-all"
            >
              <FileText className="h-3.5 w-3.5" />
              Report
            </Link>
          </div>
        </div>

        {actionMsg && (
          <div className="bg-blue-950/40 border border-blue-500/40 px-4 py-2 rounded-lg text-xs text-blue-300 flex items-center justify-between">
            <span>{actionMsg}</span>
            <button onClick={() => setActionMsg(null)} className="text-gray-400 hover:text-white">✕</button>
          </div>
        )}

        {/* ── VALIDATION MILESTONES ───────────────────────────────────────── */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-5 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-blue-400" />
                Validation Milestones & Empirical Progress
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Strategy: <strong className="text-gray-200">VWAP_EMA_MOMENTUM_V1</strong> (Phase 6 Frozen Baseline) — Real paper observations required for statistical power.
              </p>
            </div>
            <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-blue-950/60 border border-blue-500/50 text-blue-300">
              STAGE: {milestoneStage}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
            {milestones.map((m) => (
              <div
                key={m.target}
                className={`p-3 rounded-lg border text-xs ${
                  m.active
                    ? "bg-emerald-950/30 border-emerald-500/50 text-emerald-300"
                    : "bg-[#161d2b] border-[#222d44] text-gray-400"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold">{m.label}</span>
                  {m.active ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <span className="text-[10px] font-mono">PENDING</span>}
                </div>
                <div className="mt-2 text-lg font-mono font-extrabold text-white">
                  {Math.min(totalTrades, m.target)} / {m.target}
                </div>
                <div className="w-full bg-[#090c10] h-1.5 rounded-full mt-2 overflow-hidden">
                  <div
                    className={`h-full ${m.active ? "bg-emerald-500" : "bg-blue-500"}`}
                    style={{ width: `${Math.min(100, (totalTrades / m.target) * 100)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── KEY PERFORMANCE METRIC CARDS ─────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          <div className="bg-[#121721] border border-[#1e2638] p-3.5 rounded-xl">
            <span className="text-[11px] text-gray-400 uppercase font-semibold">Today's P&L</span>
            <div className={`text-base font-mono font-bold mt-1 ${(session?.net_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
              ₹{(session?.net_pnl ?? 0).toFixed(2)}
            </div>
            <span className="text-[10px] text-gray-500">Gross: ₹{(session?.gross_pnl ?? 0).toFixed(2)}</span>
          </div>

          <div className="bg-[#121721] border border-[#1e2638] p-3.5 rounded-xl">
            <span className="text-[11px] text-gray-400 uppercase font-semibold">Cumulative P&L</span>
            <div className={`text-base font-mono font-bold mt-1 ${(metrics.total_net_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
              ₹{(metrics.total_net_pnl ?? 0).toFixed(2)}
            </div>
            <span className="text-[10px] text-gray-500">{totalTrades} Total Trades</span>
          </div>

          <div className="bg-[#121721] border border-[#1e2638] p-3.5 rounded-xl">
            <span className="text-[11px] text-gray-400 uppercase font-semibold">Win Rate</span>
            <div className="text-base font-mono font-bold text-white mt-1">
              {(metrics.win_rate_pct ?? 0).toFixed(1)}%
            </div>
            <span className="text-[10px] text-gray-500">{metrics.winning_trades ?? 0}W / {metrics.losing_trades ?? 0}L</span>
          </div>

          <div className="bg-[#121721] border border-[#1e2638] p-3.5 rounded-xl">
            <span className="text-[11px] text-gray-400 uppercase font-semibold">Expectancy</span>
            <div className={`text-base font-mono font-bold mt-1 ${(metrics.expectancy_inr ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
              ₹{(metrics.expectancy_inr ?? 0).toFixed(2)}
            </div>
            <span className="text-[10px] text-gray-500">Per trade edge</span>
          </div>

          <div className="bg-[#121721] border border-[#1e2638] p-3.5 rounded-xl">
            <span className="text-[11px] text-gray-400 uppercase font-semibold">Profit Factor</span>
            <div className="text-base font-mono font-bold text-white mt-1">
              {(metrics.profit_factor ?? 0).toFixed(2)}
            </div>
            <span className="text-[10px] text-gray-500">Gross wins / losses</span>
          </div>

          <div className="bg-[#121721] border border-[#1e2638] p-3.5 rounded-xl">
            <span className="text-[11px] text-gray-400 uppercase font-semibold">Max Drawdown</span>
            <div className="text-base font-mono font-bold text-rose-400 mt-1">
              ₹{(session?.max_drawdown ?? 0).toFixed(2)}
            </div>
            <span className="text-[10px] text-gray-500">Peak-to-trough</span>
          </div>

          <div className="bg-[#121721] border border-[#1e2638] p-3.5 rounded-xl">
            <span className="text-[11px] text-gray-400 uppercase font-semibold">Total Slippage</span>
            <div className="text-base font-mono font-bold text-amber-400 mt-1">
              ₹{(session?.slippage ?? 0).toFixed(2)}
            </div>
            <span className="text-[10px] text-gray-500">Bid/ask cost</span>
          </div>

          <div className="bg-[#121721] border border-[#1e2638] p-3.5 rounded-xl">
            <span className="text-[11px] text-gray-400 uppercase font-semibold">Taxes & Charges</span>
            <div className="text-base font-mono font-bold text-purple-400 mt-1">
              ₹{(session?.transaction_costs ?? 0).toFixed(2)}
            </div>
            <span className="text-[10px] text-gray-500">STT/GST/Brokerage</span>
          </div>
        </div>

        {/* ── SCIENTIFIC VERDICT CARD ──────────────────────────────────────── */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-5 shadow-lg">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <span className="text-xs uppercase tracking-wider text-gray-400 font-bold">Empirical Scientific Verdict</span>
              <h3 className="text-xl font-bold font-mono text-white mt-1 flex items-center gap-2">
                {verdict?.is_high_confidence ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <AlertTriangle className="h-5 w-5 text-amber-400" />}
                {verdict?.verdict || "EVALUATING PAPER SAMPLE..."}
              </h3>
            </div>
            <span className="text-xs font-mono px-3 py-1 rounded bg-[#161d2b] border border-[#222d44] text-gray-300">
              Sample Size: {verdict?.sample_size ?? 0} Trades
            </span>
          </div>
          <p className="text-sm text-gray-300 mt-2 leading-relaxed">
            {verdict?.explanation || "Collecting real-market observations to establish statistically sound empirical evidence."}
          </p>
          <div className="mt-3 pt-3 border-t border-[#1e2638] flex flex-wrap items-center justify-between text-xs text-gray-500 gap-2">
            <span>Prohibited promotional claims (e.g. &quot;guaranteed&quot;, &quot;profitable&quot;) strictly filtered and banned.</span>
            <span className="font-mono text-amber-400/80">FORMULA: GROSS P&L − TRANSACTION COST − SLIPPAGE = NET P&L</span>
          </div>
        </div>

        {/* ── ANALYTICAL TABS & CONTENT ────────────────────────────────────── */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl overflow-hidden shadow-lg">
          {/* Tab Navigation */}
          <div className="flex border-b border-[#1e2638] bg-[#0d1117] overflow-x-auto">
            <button
              onClick={() => setActiveTab("backtest")}
              className={`px-4 py-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "backtest" ? "border-blue-500 text-blue-400 bg-[#121721]" : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <BarChart2 className="h-3.5 w-3.5" />
              Backtest vs Paper
            </button>

            <button
              onClick={() => setActiveTab("regimes")}
              className={`px-4 py-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "regimes" ? "border-blue-500 text-blue-400 bg-[#121721]" : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              Regime Performance (9)
            </button>

            <button
              onClick={() => setActiveTab("time")}
              className={`px-4 py-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "time" ? "border-blue-500 text-blue-400 bg-[#121721]" : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              Time-of-Day (5 Slots)
            </button>

            <button
              onClick={() => setActiveTab("concentration")}
              className={`px-4 py-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "concentration" ? "border-blue-500 text-blue-400 bg-[#121721]" : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <PieChart className="h-3.5 w-3.5" />
              Symbol Concentration
            </button>

            <button
              onClick={() => setActiveTab("data_quality")}
              className={`px-4 py-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "data_quality" ? "border-blue-500 text-blue-400 bg-[#121721]" : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5" />
              Data Quality Impact
            </button>

            <button
              onClick={() => setActiveTab("trades")}
              className={`px-4 py-3 text-xs font-bold flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "trades" ? "border-blue-500 text-blue-400 bg-[#121721]" : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Recent Paper Trades ({trades.length})
            </button>
          </div>

          {/* Tab 1: Backtest vs Paper */}
          {activeTab === "backtest" && (
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-white">Frozen Phase 6 Backtest vs Phase 9 Paper Trading Drift</h4>
                  <p className="text-xs text-gray-400">Classification: <strong className="text-blue-400">{comparison?.classification || "UNKNOWN"}</strong></p>
                </div>
                <span className="text-xs text-gray-500 font-mono">Baseline: {comparison?.baseline_source || "Phase 6"}</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#161d2b] text-gray-400 uppercase font-semibold">
                    <tr>
                      <th className="p-3">Metric</th>
                      <th className="p-3">Phase 6 Backtest</th>
                      <th className="p-3">Phase 9 Paper</th>
                      <th className="p-3">Drift</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2638] font-mono">
                    <tr>
                      <td className="p-3 text-white font-sans font-semibold">Win Rate</td>
                      <td className="p-3">{comparison?.comparison?.win_rate?.backtest ?? 55.0}%</td>
                      <td className="p-3">{comparison?.comparison?.win_rate?.paper ?? 0.0}%</td>
                      <td className={`p-3 ${(comparison?.comparison?.win_rate?.drift ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {(comparison?.comparison?.win_rate?.drift ?? 0) >= 0 ? "+" : ""}{comparison?.comparison?.win_rate?.drift ?? 0.0}%
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          comparison?.comparison?.win_rate?.status === "PASS" ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
                        }`}>
                          {comparison?.comparison?.win_rate?.status ?? "N/A"}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 text-white font-sans font-semibold">Expectancy</td>
                      <td className="p-3">₹{comparison?.comparison?.expectancy?.backtest ?? 150.00}</td>
                      <td className="p-3">₹{comparison?.comparison?.expectancy?.paper ?? 0.00}</td>
                      <td className={`p-3 ${(comparison?.comparison?.expectancy?.drift ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {(comparison?.comparison?.expectancy?.drift ?? 0) >= 0 ? "+" : ""}₹{comparison?.comparison?.expectancy?.drift ?? 0.00}
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          comparison?.comparison?.expectancy?.status === "PASS" ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
                        }`}>
                          {comparison?.comparison?.expectancy?.status ?? "N/A"}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 text-white font-sans font-semibold">Profit Factor</td>
                      <td className="p-3">{comparison?.comparison?.profit_factor?.backtest ?? 1.50}</td>
                      <td className="p-3">{comparison?.comparison?.profit_factor?.paper ?? 0.00}</td>
                      <td className={`p-3 ${(comparison?.comparison?.profit_factor?.drift ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {(comparison?.comparison?.profit_factor?.drift ?? 0) >= 0 ? "+" : ""}{comparison?.comparison?.profit_factor?.drift ?? 0.00}
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          comparison?.comparison?.profit_factor?.status === "PASS" ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
                        }`}>
                          {comparison?.comparison?.profit_factor?.status ?? "N/A"}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 text-white font-sans font-semibold">Avg Win / Loss</td>
                      <td className="p-3">₹{comparison?.comparison?.avg_win?.backtest ?? 350.0} / ₹{comparison?.comparison?.avg_loss?.backtest ?? 200.0}</td>
                      <td className="p-3">₹{comparison?.comparison?.avg_win?.paper ?? 0.0} / ₹{comparison?.comparison?.avg_loss?.paper ?? 0.0}</td>
                      <td className="p-3 text-gray-500">—</td>
                      <td className="p-3 text-gray-500">—</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Regime Performance */}
          {activeTab === "regimes" && (
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white">Performance Across 9 Indian Market Regimes</h4>
                <span className="text-xs text-gray-500">Purely observational evidence (no auto-disabling)</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#161d2b] text-gray-400 uppercase font-semibold">
                    <tr>
                      <th className="p-3">Regime</th>
                      <th className="p-3">Trades</th>
                      <th className="p-3">Win Rate</th>
                      <th className="p-3">Net P&L</th>
                      <th className="p-3">Expectancy</th>
                      <th className="p-3">Profit Factor</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2638] font-mono">
                    {Object.entries(regimes?.regimes || {}).map(([rName, rData]: [string, any]) => (
                      <tr key={rName}>
                        <td className="p-3 text-white font-sans font-semibold">{rName}</td>
                        <td className="p-3">{rData.trade_count}</td>
                        <td className="p-3">{rData.win_rate_pct}%</td>
                        <td className={`p-3 ${rData.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ₹{rData.net_pnl.toFixed(2)}
                        </td>
                        <td className="p-3">₹{rData.expectancy_inr.toFixed(2)}</td>
                        <td className="p-3">{rData.profit_factor}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 3: Time-of-Day Performance */}
          {activeTab === "time" && (
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white">Intraday Time-of-Day Execution Windows</h4>
                <span className="text-xs text-gray-500">Mandatory Square-off at 15:15 IST</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#161d2b] text-gray-400 uppercase font-semibold">
                    <tr>
                      <th className="p-3">Time Window</th>
                      <th className="p-3">Trades</th>
                      <th className="p-3">Win Rate</th>
                      <th className="p-3">Net P&L</th>
                      <th className="p-3">Avg Slippage</th>
                      <th className="p-3">Expectancy</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2638] font-mono">
                    {Object.entries(timeSlots?.time_slots || {}).map(([sName, sData]: [string, any]) => (
                      <tr key={sName}>
                        <td className="p-3 text-white font-sans font-semibold">{sName}</td>
                        <td className="p-3">{sData.trade_count}</td>
                        <td className="p-3">{sData.win_rate_pct}%</td>
                        <td className={`p-3 ${sData.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ₹{sData.net_pnl.toFixed(2)}
                        </td>
                        <td className="p-3 text-amber-400">₹{sData.avg_slippage_inr.toFixed(2)}</td>
                        <td className="p-3">₹{sData.expectancy_inr.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 4: Symbol Concentration */}
          {activeTab === "concentration" && (
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-white">Symbol Profit Concentration Risk</h4>
                  <p className="text-xs text-gray-400">{concentration?.warning || "Concentration evaluation active."}</p>
                </div>
                <span className={`px-3 py-1 rounded text-xs font-bold font-mono ${
                  concentration?.concentration_risk === "HIGH_CONCENTRATION_RISK"
                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/50"
                    : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50"
                }`}>
                  {concentration?.concentration_risk || "EVALUATING"}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-[#161d2b] border border-[#222d44]">
                  <span className="text-gray-400 text-xs">Top 1 Contribution</span>
                  <div className="text-lg font-mono font-bold text-white mt-1">{concentration?.top1_contribution_pct ?? 0}%</div>
                </div>
                <div className="p-3 rounded-lg bg-[#161d2b] border border-[#222d44]">
                  <span className="text-gray-400 text-xs">Top 3 Contribution</span>
                  <div className="text-lg font-mono font-bold text-white mt-1">{concentration?.top3_contribution_pct ?? 0}%</div>
                </div>
                <div className="p-3 rounded-lg bg-[#161d2b] border border-[#222d44]">
                  <span className="text-gray-400 text-xs">Active Symbols</span>
                  <div className="text-lg font-mono font-bold text-white mt-1">{concentration?.active_symbols_count ?? 0}</div>
                </div>
              </div>

              <div className="overflow-x-auto pt-2">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#161d2b] text-gray-400 uppercase font-semibold">
                    <tr>
                      <th className="p-3">Symbol</th>
                      <th className="p-3">Trades</th>
                      <th className="p-3">Win Rate</th>
                      <th className="p-3">Net P&L</th>
                      <th className="p-3">Contribution</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2638] font-mono">
                    {(concentration?.symbols || []).slice(0, 10).map((s: any) => (
                      <tr key={s.symbol}>
                        <td className="p-3 text-white font-sans font-semibold">{s.symbol}</td>
                        <td className="p-3">{s.trade_count}</td>
                        <td className="p-3">{s.win_rate_pct}%</td>
                        <td className={`p-3 ${s.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ₹{s.net_pnl.toFixed(2)}
                        </td>
                        <td className="p-3">{s.contribution_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 5: Data Quality Impact */}
          {activeTab === "data_quality" && (
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-white">Market Feed Latency & Incident Correlation</h4>
                <span className="text-xs text-gray-400">Analyzes how feed degradation impacts slippage and expectancy</span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-[#161d2b] border border-[#222d44]">
                  <span className="text-gray-400 text-xs">Low Latency (&lt;100ms) Slip</span>
                  <div className="text-base font-mono font-bold text-white mt-1">
                    ₹{dqImpact?.latency_breakdown?.avg_slippage_low_latency_inr ?? 0.00}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-[#161d2b] border border-[#222d44]">
                  <span className="text-gray-400 text-xs">High Latency (&ge;100ms) Slip</span>
                  <div className="text-base font-mono font-bold text-amber-400 mt-1">
                    ₹{dqImpact?.latency_breakdown?.avg_slippage_high_latency_inr ?? 0.00}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-[#161d2b] border border-[#222d44]">
                  <span className="text-gray-400 text-xs">Low Latency Expectancy</span>
                  <div className="text-base font-mono font-bold text-white mt-1">
                    ₹{dqImpact?.latency_breakdown?.avg_net_pnl_low_latency_inr ?? 0.00}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-[#161d2b] border border-[#222d44]">
                  <span className="text-gray-400 text-xs">High Latency Expectancy</span>
                  <div className="text-base font-mono font-bold text-white mt-1">
                    ₹{dqImpact?.latency_breakdown?.avg_net_pnl_high_latency_inr ?? 0.00}
                  </div>
                </div>
              </div>

              <div className="bg-[#090c10] border border-[#1e2638] p-4 rounded-lg space-y-1 text-xs">
                <span className="font-bold text-gray-300">Empirical Observations:</span>
                {(dqImpact?.findings || []).map((f: string, idx: number) => (
                  <p key={idx} className="text-gray-400">• {f}</p>
                ))}
              </div>
            </div>
          )}

          {/* Tab 6: Recent Paper Trades */}
          {activeTab === "trades" && (
            <div className="p-5 space-y-4">
              <h4 className="text-sm font-bold text-white">Itemized Paper Trade Ledger</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#161d2b] text-gray-400 uppercase font-semibold">
                    <tr>
                      <th className="p-2.5">ID</th>
                      <th className="p-2.5">Symbol</th>
                      <th className="p-2.5">Side</th>
                      <th className="p-2.5">Intended</th>
                      <th className="p-2.5">Fill</th>
                      <th className="p-2.5">Slippage</th>
                      <th className="p-2.5">Charges</th>
                      <th className="p-2.5">Gross P&L</th>
                      <th className="p-2.5">Net P&L</th>
                      <th className="p-2.5">Regime</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2638] font-mono">
                    {trades.map((t) => (
                      <tr key={t.trade_id}>
                        <td className="p-2.5 text-gray-500">#{t.trade_id}</td>
                        <td className="p-2.5 text-white font-sans font-semibold">{t.symbol}</td>
                        <td className="p-2.5">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            t.direction === "BUY" ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"
                          }`}>
                            {t.direction}
                          </span>
                        </td>
                        <td className="p-2.5">₹{t.intended_entry_price}</td>
                        <td className="p-2.5">₹{t.simulated_fill_price}</td>
                        <td className="p-2.5 text-amber-400">₹{(t.entry_slippage + t.exit_slippage).toFixed(2)}</td>
                        <td className="p-2.5 text-purple-400">₹{t.total_cost.toFixed(2)}</td>
                        <td className="p-2.5">₹{t.gross_pnl.toFixed(2)}</td>
                        <td className={`p-2.5 font-bold ${t.net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ₹{t.net_pnl.toFixed(2)}
                        </td>
                        <td className="p-2.5 text-gray-400 font-sans">{t.market_regime}</td>
                      </tr>
                    ))}
                    {trades.length === 0 && (
                      <tr>
                        <td colSpan={10} className="p-4 text-center text-gray-500">
                          No paper trades recorded in active session.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
