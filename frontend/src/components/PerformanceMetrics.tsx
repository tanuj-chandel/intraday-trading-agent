"use client";

import React from "react";
import { PerformanceMetrics as PerformanceMetricsType } from "@/types";
import { formatINR, formatPercent } from "@/lib/utils";
import { BarChart3, TrendingUp, DollarSign, Percent, ShieldCheck, Scale, Award } from "lucide-react";

interface PerformanceProps {
  metrics: PerformanceMetricsType | null;
  loading: boolean;
}

export const PerformanceMetrics: React.FC<PerformanceProps> = ({ metrics, loading }) => {
  if (loading || !metrics) {
    return (
      <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 animate-pulse">
        <div className="h-6 w-48 bg-gray-800 rounded mb-4"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-800 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const isNetProfit = metrics.net_pnl >= 0;

  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Performance Analytics & Risk-Adjusted Metrics
          </h2>
        </div>
        <span className="text-[11px] text-gray-400">
          Simulation History Tracker
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Metric 1: Win Rate */}
        <div className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Win Rate</span>
            <Percent className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="text-lg font-black text-white">{metrics.win_rate_pct.toFixed(1)}%</div>
          <span className="text-[10px] text-gray-500">
            {metrics.winning_trades}W / {metrics.losing_trades}L ({metrics.total_trades} total)
          </span>
        </div>

        {/* Metric 2: Net P&L */}
        <div className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Net Realized P&L</span>
            <DollarSign className="h-3.5 w-3.5 text-blue-400" />
          </div>
          <div className={`text-lg font-black ${isNetProfit ? "text-emerald-400" : "text-rose-400"}`}>
            {isNetProfit ? `+${formatINR(metrics.net_pnl)}` : formatINR(metrics.net_pnl)}
          </div>
          <span className="text-[10px] text-gray-500">
            Gross: {formatINR(metrics.gross_profit - metrics.gross_loss)}
          </span>
        </div>

        {/* Metric 3: Profit Factor */}
        <div className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Profit Factor</span>
            <Scale className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <div className="text-lg font-black text-white">{metrics.profit_factor.toFixed(2)}</div>
          <span className="text-[10px] text-gray-500">
            Avg W/L: {(metrics.average_win / (metrics.average_loss || 1)).toFixed(2)}
          </span>
        </div>

        {/* Metric 4: Max Drawdown */}
        <div className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Max Drawdown</span>
            <TrendingUp className="h-3.5 w-3.5 text-rose-400" />
          </div>
          <div className="text-lg font-black text-rose-400">-{formatINR(metrics.max_drawdown)}</div>
          <span className="text-[10px] text-gray-500">
            {metrics.max_drawdown_pct.toFixed(2)}% of peak equity
          </span>
        </div>

        {/* Metric 5: Avg Holding Time */}
        <div className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Avg Holding Time</span>
            <Award className="h-3.5 w-3.5 text-purple-400" />
          </div>
          <div className="text-lg font-black text-white">{metrics.average_holding_time_minutes.toFixed(0)} min</div>
          <span className="text-[10px] text-gray-500">Intraday Scalps / Swings</span>
        </div>

        {/* Metric 6: Statutory Taxes & Brokerage */}
        <div className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg">
          <div className="flex items-center justify-between text-gray-400 mb-1">
            <span className="text-[10px] uppercase font-bold">Brokerage & Taxes</span>
            <ShieldCheck className="h-3.5 w-3.5 text-gray-400" />
          </div>
          <div className="text-lg font-black text-gray-300">{formatINR(metrics.total_charges)}</div>
          <span className="text-[10px] text-gray-500">STT, Exchange, GST & SEBI</span>
        </div>
      </div>
    </div>
  );
};
