"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { SystemStatus } from "@/types";
import { formatINR } from "@/lib/utils";
import { ShieldAlert, Activity, FileText, Zap, RefreshCw, Database, BarChart3, LayoutDashboard, HeartPulse, FlaskConical } from "lucide-react";

interface HeaderProps {
  status: SystemStatus | null;
  onOpenPreMarket?: () => void;
  onOpenEmergencyStop?: () => void;
  onOpenDataSources?: () => void;
  onGenerateSignals?: () => void;
  onRefreshData?: () => void;
  isGeneratingSignals?: boolean;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  onOpenPreMarket,
  onOpenEmergencyStop,
  onOpenDataSources,
  onGenerateSignals,
  onRefreshData,
  isGeneratingSignals = false,
  isRefreshing = false
}) => {
  const pathname = usePathname();
  const pnl = status?.today_total_pnl ?? 0;
  const isPnlPositive = pnl >= 0;
  const providerLabel = status?.market_data_provider || "MOCK";
  const isStale = status?.data_quality_status === "WARNING_STALE";
  const isBacktesting = pathname === "/backtesting";
  const isDataHealth = pathname === "/data-health";
  const isLivePage = pathname === "/live";
  const isPhase9 = pathname === "/phase9";
  const isGoLive = pathname === "/go-live";
  const isReports = pathname === "/reports";

  return (
    <header className="bg-[#121721] border-b border-[#1e2638] px-4 py-3 sticky top-0 z-40">
      <div className="max-w-[1600px] mx-auto flex flex-col xl:flex-row items-center justify-between gap-4">
        {/* Left: Branding & Navigation Tabs */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-bold">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-white tracking-wide uppercase">
                  AI Intraday Trading Agent
                </h1>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-500/20 border border-blue-500/40 text-blue-400">
                  NSE / BSE
                </span>
              </div>
              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 border border-amber-500/50 text-amber-300 animate-pulse">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400"></span>
                  PAPER TRADING ONLY
                </span>

                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-950/40 border border-rose-500/40 text-rose-300">
                  REAL ORDERS: DISABLED
                </span>

                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#090c10] border border-[#1e2638] text-gray-300">
                  DATA: <strong className="text-blue-400">{providerLabel}</strong>
                </span>

                {isStale ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/20 border border-rose-500/50 text-rose-300">
                    WARNING: STALE
                  </span>
                ) : (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                    DATA FRESH
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Module Switcher Tabs */}
          <div className="flex items-center gap-1 bg-[#090c10] p-1 rounded-lg border border-[#1e2638] ml-2">
            <Link
              href="/"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                pathname === "/"
                  ? "bg-blue-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <LayoutDashboard className="h-3.5 w-3.5" />
              Live Terminal
            </Link>

            <Link
              href="/backtesting"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                isBacktesting
                  ? "bg-purple-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <BarChart3 className="h-3.5 w-3.5" />
              Backtesting & Validation
            </Link>

            <Link
              href="/data-health"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                isDataHealth
                  ? "bg-emerald-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <HeartPulse className="h-3.5 w-3.5" />
              Data Health & Importer
            </Link>

            <Link
              href="/live"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                isLivePage
                  ? "bg-amber-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              Live Paper
            </Link>

            <Link
              href="/phase9"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                isPhase9
                  ? "bg-indigo-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <FlaskConical className="h-3.5 w-3.5" />
              Phase 9 Pilot
            </Link>

            <Link
              href="/go-live"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                isGoLive
                  ? "bg-rose-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5" />
              Go-Live Readiness
            </Link>

            <Link
              href="/reports"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                isReports
                  ? "bg-cyan-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Pilot Reports
            </Link>
          </div>
        </div>

        {/* Center: Live Financial Metrics (Only on live dashboard) */}
        {pathname === "/" && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#090c10] px-4 py-2 rounded-lg border border-[#1e2638] text-xs">
            <div>
              <span className="text-gray-400 block text-[9px] uppercase font-semibold">Simulated Equity</span>
              <span className="font-bold text-white text-sm">
                {status ? formatINR(status.portfolio_value) : "₹1,00,000.00"}
              </span>
            </div>

            <div>
              <span className="text-gray-400 block text-[9px] uppercase font-semibold">Today's P&L</span>
              <span className={`font-bold text-sm ${isPnlPositive ? "text-emerald-400" : "text-rose-400"}`}>
                {status ? (isPnlPositive ? `+${formatINR(pnl)}` : formatINR(pnl)) : "₹0.00"}
              </span>
            </div>

            <div>
              <span className="text-gray-400 block text-[9px] uppercase font-semibold">Loss Limit Left</span>
              <span className="font-bold text-amber-400 text-sm">
                {status ? formatINR(status.daily_loss_remaining) : "₹3,000.00"}
              </span>
            </div>

            <div>
              <span className="text-gray-400 block text-[9px] uppercase font-semibold">Paper Positions</span>
              <span className="font-bold text-white text-sm">
                {status?.open_positions_count ?? 0} / 3 Open
              </span>
            </div>
          </div>
        )}

        {/* Right: Actions */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {onRefreshData && (
            <button
              onClick={onRefreshData}
              disabled={isRefreshing}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#1e2638] hover:bg-[#2a364f] text-gray-200 text-xs font-semibold border border-[#2e3a52] transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 text-blue-400 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
          )}

          {onOpenDataSources && (
            <button
              onClick={onOpenDataSources}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#1e2638] hover:bg-[#2a364f] text-gray-200 text-xs font-semibold border border-[#2e3a52] transition-colors"
            >
              <Database className="h-3.5 w-3.5 text-cyan-400" />
              Sources
            </button>
          )}

          {onOpenPreMarket && (
            <button
              onClick={onOpenPreMarket}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-semibold border border-blue-500/40 transition-colors"
            >
              <FileText className="h-3.5 w-3.5 text-blue-400" />
              Pre-Market
            </button>
          )}

          {onGenerateSignals && (
            <button
              onClick={onGenerateSignals}
              disabled={isGeneratingSignals}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors disabled:opacity-50"
            >
              <Activity className={`h-3.5 w-3.5 ${isGeneratingSignals ? "animate-spin" : ""}`} />
              {isGeneratingSignals ? "Scanning..." : "Scan Signals"}
            </button>
          )}

          {onOpenEmergencyStop && (
            <button
              onClick={onOpenEmergencyStop}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white text-xs font-bold border border-rose-500/50 transition-colors"
            >
              <ShieldAlert className="h-3.5 w-3.5" />
              EMERGENCY STOP
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
