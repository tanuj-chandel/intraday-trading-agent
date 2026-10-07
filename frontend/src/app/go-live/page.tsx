"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { fetchSystemStatus, fetchGoLiveChecklist, toggleLiveTrading, triggerEodReport } from "@/lib/api";
import { SystemStatus } from "@/types";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Send,
  Lock,
  Unlock,
  Activity,
  Layers,
  Scale,
  TrendingUp,
  FileCheck2
} from "lucide-react";

interface ChecklistItem {
  id: string;
  name: string;
  description: string;
  current_value: string;
  target: string;
  status: "PASS" | "FAIL";
  passed: boolean;
}

interface GoLiveResponse {
  overall_status: "READY" | "NOT_READY";
  all_passed: boolean;
  live_trading_enabled: boolean;
  is_paper_trading: boolean;
  total_trades: number;
  items: ChecklistItem[];
}

export default function GoLivePage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [checklist, setChecklist] = useState<GoLiveResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  const showNotification = (msg: string, type: "success" | "error" = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [sysStatus, clData] = await Promise.all([
        fetchSystemStatus(),
        fetchGoLiveChecklist()
      ]);
      setStatus(sysStatus);
      setChecklist(clData);
    } catch (err: any) {
      showNotification("Failed to load Go-Live checklist data: " + err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleLive = async (enable: boolean) => {
    if (enable && !checklist?.all_passed) {
      showNotification("Cannot enable live trading: Not all checklist criteria have passed.", "error");
      return;
    }
    setActionLoading(true);
    try {
      const res = await toggleLiveTrading(enable);
      showNotification(res.message || "Trading mode updated", "success");
      await loadData();
    } catch (err: any) {
      showNotification(err.message, "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleTriggerEod = async () => {
    setActionLoading(true);
    try {
      const res = await triggerEodReport();
      if (res.success) {
        showNotification("EOD Telegram report dispatched successfully!", "success");
      } else {
        showNotification("EOD report failed: Telegram bot unconfigured or network issue", "error");
      }
    } catch (err: any) {
      showNotification("Failed to trigger EOD report: " + err.message, "error");
    } finally {
      setActionLoading(false);
    }
  };

  const getIconForCheck = (id: string) => {
    switch (id) {
      case "MIN_PAPER_TRADES":
        return <Layers className="w-5 h-5 text-blue-400" />;
      case "POSITIVE_EXPECTANCY":
        return <Scale className="w-5 h-5 text-emerald-400" />;
      case "MAX_DRAWDOWN":
        return <TrendingUp className="w-5 h-5 text-amber-400" />;
      case "INCIDENTS_ZERO":
        return <Activity className="w-5 h-5 text-purple-400" />;
      default:
        return <FileCheck2 className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-gray-200">
      <Header status={status} onRefreshData={loadData} isRefreshing={loading} />

      <main className="max-w-[1400px] mx-auto p-4 md:p-6 space-y-6">
        {/* Banner Alert */}
        {notification && (
          <div
            className={`p-3 rounded-lg border text-sm font-semibold flex items-center justify-between transition-all ${
              notification.type === "success"
                ? "bg-emerald-950/40 border-emerald-500/50 text-emerald-300"
                : "bg-rose-950/40 border-rose-500/50 text-rose-300"
            }`}
          >
            <span>{notification.msg}</span>
            <button
              onClick={() => setNotification(null)}
              className="text-xs opacity-70 hover:opacity-100 ml-4 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#161b22] border border-[#30363d] p-5 rounded-xl">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white tracking-wide">
                  Production Readiness & Go-Live Criteria
                </h1>
                <p className="text-xs text-gray-400 mt-0.5">
                  Automated audit evaluating real paper trade history, net expectancy, drawdown bounds, and watchdog telemetry.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleTriggerEod}
              disabled={actionLoading}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-xs font-semibold text-gray-200 transition-all disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5 text-blue-400" />
              Send EOD Telegram Report
            </button>
            <button
              onClick={loadData}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-xs font-semibold text-gray-200 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Re-evaluate
            </button>
          </div>
        </div>

        {/* Status Overview Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Status Box */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 flex flex-col justify-between">
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">
              Audit Readiness Verdict
            </div>
            <div className="my-3 flex items-center gap-3">
              {checklist?.all_passed ? (
                <div className="h-10 w-10 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
              ) : (
                <div className="h-10 w-10 rounded-full bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
                  <XCircle className="w-6 h-6" />
                </div>
              )}
              <div>
                <div
                  className={`text-2xl font-black ${
                    checklist?.all_passed ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {checklist?.all_passed ? "GO-LIVE READY" : "QUALIFICATION INCOMPLETE"}
                </div>
                <div className="text-xs text-gray-400">
                  {checklist?.all_passed
                    ? "All 4 statistical and stability gates verified."
                    : "Live trading disabled until all criteria pass."}
                </div>
              </div>
            </div>
            <div className="text-[11px] text-gray-500 border-t border-[#21262d] pt-2">
              Completed Trades: <strong className="text-white">{checklist?.total_trades || 0}</strong>
            </div>
          </div>

          {/* Current Execution Mode */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 flex flex-col justify-between">
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">
              Current Execution Mode
            </div>
            <div className="my-3">
              {checklist?.live_trading_enabled ? (
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-rose-950/60 border border-rose-500/50 text-rose-300 font-bold text-sm">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
                  LIVE TRADING ACTIVE (REAL BROKER)
                </div>
              ) : (
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-950/60 border border-amber-500/50 text-amber-300 font-bold text-sm">
                  <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                  PAPER TRADING ONLY (IS_PAPER_TRADING=True)
                </div>
              )}
              <p className="text-xs text-gray-400 mt-2">
                Real broker orders require explicit checklist qualification and manual confirmation.
              </p>
            </div>
            <div className="text-[11px] text-gray-500 border-t border-[#21262d] pt-2">
              Fail-closed guard active • Synthetic feeds blocked
            </div>
          </div>

          {/* Master Control Switch */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 flex flex-col justify-between">
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">
              Live Order Placement Guard
            </div>
            <div className="my-3">
              {checklist?.all_passed ? (
                <div className="space-y-2">
                  {checklist.live_trading_enabled ? (
                    <button
                      onClick={() => handleToggleLive(false)}
                      disabled={actionLoading}
                      className="w-full py-2.5 px-4 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow"
                    >
                      <Lock className="w-4 h-4" />
                      Switch Back to Paper Trading
                    </button>
                  ) : (
                    <button
                      onClick={() => handleToggleLive(true)}
                      disabled={actionLoading}
                      className="w-full py-2.5 px-4 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow"
                    >
                      <Unlock className="w-4 h-4" />
                      Activate Live Trading (Real Orders)
                    </button>
                  )}
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-black/40 border border-[#30363d] text-center">
                  <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-gray-400">
                    <Lock className="w-3.5 h-3.5 text-rose-400" />
                    LIVE TRADING LOCKED
                  </div>
                  <p className="text-[11px] text-gray-500 mt-1">
                    Cannot be activated. Resolve failing criteria below.
                  </p>
                </div>
              )}
            </div>
            <div className="text-[11px] text-gray-500 border-t border-[#21262d] pt-2">
              Default: LIVE_TRADING_ENABLED=False
            </div>
          </div>
        </div>

        {/* 4 Checklist Criteria Cards */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-blue-400" />
            Mandatory Qualification Checklist
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {checklist?.items?.map((item) => (
              <div
                key={item.id}
                className={`p-4 rounded-xl border transition-all ${
                  item.passed
                    ? "bg-[#0d1117] border-emerald-500/30"
                    : "bg-[#0d1117] border-rose-500/30"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-[#161b22] border border-[#30363d] mt-0.5">
                      {getIconForCheck(item.id)}
                    </div>
                    <div>
                      <div className="font-bold text-sm text-white">{item.name}</div>
                      <p className="text-xs text-gray-400 mt-0.5">{item.description}</p>
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-md text-xs font-extrabold flex items-center gap-1 shrink-0 ${
                      item.passed
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                        : "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                    }`}
                  >
                    {item.passed ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" /> PASS
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3.5 h-3.5" /> FAIL
                      </>
                    )}
                  </span>
                </div>

                <div className="mt-4 pt-3 border-t border-[#21262d] flex items-center justify-between text-xs">
                  <div>
                    <span className="text-gray-500">Current Real Data: </span>
                    <strong className="text-white font-mono">{item.current_value}</strong>
                  </div>
                  <div>
                    <span className="text-gray-500">Required Target: </span>
                    <strong className="text-blue-400 font-mono">{item.target}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
