"use client";

import React from "react";
import { MarketOverviewResponse } from "@/types";
import { formatINR, formatPercent } from "@/lib/utils";
import { TrendingUp, TrendingDown, Activity, AlertCircle, Compass } from "lucide-react";

interface MarketOverviewProps {
  data: MarketOverviewResponse | null;
  loading: boolean;
}

export const MarketOverview: React.FC<MarketOverviewProps> = ({ data, loading }) => {
  if (loading || !data) {
    return (
      <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 animate-pulse">
        <div className="h-6 w-48 bg-gray-800 rounded mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-24 bg-gray-800 rounded"></div>
          <div className="h-24 bg-gray-800 rounded"></div>
          <div className="h-24 bg-gray-800 rounded"></div>
        </div>
      </div>
    );
  }

  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case "TRENDING_UP":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
      case "TRENDING_DOWN":
        return "text-rose-400 bg-rose-500/10 border-rose-500/30";
      case "GAP_UP":
        return "text-blue-400 bg-blue-500/10 border-blue-500/30";
      case "HIGH_VOLATILITY":
        return "text-amber-400 bg-amber-500/10 border-amber-500/30";
      default:
        return "text-slate-400 bg-slate-500/10 border-slate-500/30";
    }
  };

  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Compass className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Market Regime & Benchmark Overview
          </h2>
        </div>
        <span className="text-[11px] text-gray-400">
          Adv/Dec Ratio: <strong className="text-emerald-400">{data.advance_decline_ratio}:1</strong>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Index Cards */}
        {data.indices.map((idx) => {
          const isUp = idx.change >= 0;
          return (
            <div
              key={idx.symbol}
              className="bg-[#090c10] border border-[#1e2638] rounded-lg p-3 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-300">{idx.symbol}</span>
                <span
                  className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border flex items-center gap-1 ${
                    isUp
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                      : "text-rose-400 bg-rose-500/10 border-rose-500/30"
                  }`}
                >
                  {isUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {formatPercent(idx.change_pct)}
                </span>
              </div>

              <div className="my-2">
                <span className="text-xl font-black text-white">{formatINR(idx.current_price)}</span>
                <span className={`text-xs ml-2 font-medium ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                  {isUp ? `+${idx.change.toFixed(2)}` : idx.change.toFixed(2)}
                </span>
              </div>

              <div className="flex items-center justify-between text-[11px] text-gray-500 border-t border-gray-800/60 pt-1.5">
                <span>H: {idx.high.toFixed(1)}</span>
                <span>L: {idx.low.toFixed(1)}</span>
                <span>Prev: {idx.prev_close.toFixed(1)}</span>
              </div>
            </div>
          );
        })}

        {/* Market Regime Summary Card */}
        <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-300">Classified Regime</span>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded border uppercase ${getRegimeColor(data.market_regime)}`}>
                {data.market_regime.replace("_", " ")}
              </span>
            </div>
            <p className="text-xs text-gray-300 mt-2 line-clamp-2 leading-relaxed">
              {data.regime_description}
            </p>
          </div>

          <div className="flex items-center justify-between text-[11px] text-gray-400 border-t border-gray-800/60 pt-1.5 mt-2">
            <span>Volatility: <strong className="text-blue-400">Normal</strong></span>
            <span>Intraday Bias: <strong className="text-emerald-400">Selective Long</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
