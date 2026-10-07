"use client";

import React, { useState } from "react";
import { StockScore } from "@/types";
import { formatINR, formatPercent } from "@/lib/utils";
import { Award, ArrowUpRight, ArrowDownRight, TrendingUp, TrendingDown, ChevronRight, Layers, ShieldCheck } from "lucide-react";

interface TopRankedStocksProps {
  topOverall: StockScore[];
  topLongs: StockScore[];
  topShorts: StockScore[];
  onGenerateTop10?: () => void;
  loading: boolean;
}

export const TopRankedStocks: React.FC<TopRankedStocksProps> = ({
  topOverall,
  topLongs,
  topShorts,
  onGenerateTop10,
  loading
}) => {
  const [activeTab, setActiveTab] = useState<"OVERALL" | "LONGS" | "SHORTS">("OVERALL");
  const [selectedStock, setSelectedStock] = useState<StockScore | null>(null);

  if (loading) {
    return (
      <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 animate-pulse">
        <div className="h-6 w-48 bg-gray-800 rounded mb-4"></div>
        <div className="space-y-2">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-10 bg-gray-800 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const currentList =
    activeTab === "LONGS" ? topLongs : activeTab === "SHORTS" ? topShorts : topOverall;

  const getScoreColor = (score: number) => {
    if (score >= 85) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
    if (score >= 70) return "text-blue-400 bg-blue-500/10 border-blue-500/30";
    if (score >= 50) return "text-amber-400 bg-amber-500/10 border-amber-500/30";
    return "text-rose-400 bg-rose-500/10 border-rose-500/30";
  };

  const getReliabilityBadge = (rel?: string) => {
    if (rel === "LEVEL_1") {
      return (
        <span className="text-[9px] px-1 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40">
          L1 Official
        </span>
      );
    }
    return (
      <span className="text-[9px] px-1 py-0.2 rounded bg-blue-500/20 text-blue-300 font-medium border border-blue-500/40">
        L2 Media
      </span>
    );
  };

  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
      {/* Tab Navigation Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3 border-b border-[#1e2638] pb-3">
        <div className="flex items-center gap-2">
          <Award className="h-4 w-4 text-amber-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Intraday Alpha Ranking Matrix (Liquid Universe)
          </h2>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center gap-1.5 bg-[#090c10] p-1 rounded-lg border border-[#1e2638]">
          <button
            onClick={() => setActiveTab("OVERALL")}
            className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${
              activeTab === "OVERALL"
                ? "bg-blue-600 text-white shadow"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Top 10 Overall ({topOverall.length})
          </button>

          <button
            onClick={() => setActiveTab("LONGS")}
            className={`px-3 py-1 rounded-md text-xs font-bold transition-all flex items-center gap-1 ${
              activeTab === "LONGS"
                ? "bg-emerald-600 text-white shadow"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            <TrendingUp className="h-3 w-3" />
            Top 10 Longs ({topLongs.length})
          </button>

          <button
            onClick={() => setActiveTab("SHORTS")}
            className={`px-3 py-1 rounded-md text-xs font-bold transition-all flex items-center gap-1 ${
              activeTab === "SHORTS"
                ? "bg-rose-600 text-white shadow"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            <TrendingDown className="h-3 w-3" />
            Top 10 Shorts ({topShorts.length})
          </button>
        </div>
      </div>

      {/* Main Candidates Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#1e2638] text-gray-400 uppercase text-[10px] bg-[#090c10]/60">
              <th className="py-2.5 px-3">#</th>
              <th className="py-2.5 px-3">Symbol / Sector</th>
              <th className="py-2.5 px-3 text-center">Score</th>
              <th className="py-2.5 px-3">Bias</th>
              <th className="py-2.5 px-3 text-right">CMP</th>
              <th className="py-2.5 px-3 text-right">Gap %</th>
              <th className="py-2.5 px-3">Entry Zone</th>
              <th className="py-2.5 px-3">Stop Loss</th>
              <th className="py-2.5 px-3">Target</th>
              <th className="py-2.5 px-3 text-center">R : R</th>
              <th className="py-2.5 px-3">Primary Catalyst / Reason</th>
              <th className="py-2.5 px-2 text-center">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2638]/50">
            {currentList.map((stock) => {
              const isBull = stock.direction === "BULLISH";
              return (
                <tr
                  key={stock.symbol}
                  className="hover:bg-[#182030]/60 transition-colors group cursor-pointer"
                  onClick={() => setSelectedStock(stock)}
                >
                  <td className="py-2 px-3 font-bold text-gray-400">
                    <span className="h-5 w-5 rounded-full bg-[#1e2638] flex items-center justify-center text-[10px]">
                      {stock.rank}
                    </span>
                  </td>
                  <td className="py-2 px-3">
                    <div className="font-bold text-white group-hover:text-blue-400 transition-colors flex items-center gap-1.5">
                      <span>{stock.symbol}</span>
                      {getReliabilityBadge(stock.source_reliability)}
                    </div>
                    <div className="text-[10px] text-gray-400">{stock.sector}</div>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded font-black text-xs border ${getScoreColor(
                        stock.total_score
                      )}`}
                    >
                      {stock.total_score.toFixed(1)}
                    </span>
                  </td>
                  <td className="py-2 px-3">
                    <span
                      className={`inline-flex items-center gap-1 text-[11px] font-bold px-1.5 py-0.5 rounded ${
                        isBull
                          ? "text-emerald-400 bg-emerald-500/10"
                          : "text-rose-400 bg-rose-500/10"
                      }`}
                    >
                      {isBull ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                      {stock.direction}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right font-semibold text-white font-mono">
                    {formatINR(stock.current_price)}
                  </td>
                  <td className={`py-2 px-3 text-right font-mono text-[11px] font-semibold ${stock.gap_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {formatPercent(stock.gap_pct || 0)}
                  </td>
                  <td className="py-2 px-3 font-mono text-gray-300">{stock.entry_zone}</td>
                  <td className="py-2 px-3 font-mono text-rose-400">{formatINR(stock.stop_loss)}</td>
                  <td className="py-2 px-3 font-mono text-emerald-400">{formatINR(stock.target)}</td>
                  <td className="py-2 px-3 text-center font-bold text-blue-400 font-mono">
                    1 : {stock.risk_reward_ratio.toFixed(1)}
                  </td>
                  <td className="py-2 px-3 text-gray-300 max-w-xs truncate text-[11px]">
                    {stock.reason}
                  </td>
                  <td className="py-2 px-2 text-center text-gray-400 group-hover:text-blue-400">
                    <ChevronRight className="h-4 w-4 inline" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Factor Breakdown Modal */}
      {selectedStock && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
          <div className="bg-[#121721] border border-[#1e2638] rounded-xl max-w-lg w-full p-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#1e2638] pb-3 mb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>{selectedStock.symbol}</span>
                  <span className="text-xs text-gray-400 font-normal">({selectedStock.company_name})</span>
                </h3>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-blue-400 font-semibold">{selectedStock.sector}</span>
                  <span className="text-[10px] px-1.5 rounded bg-gray-800 text-gray-300">
                    Liquidity: {selectedStock.liquidity_classification}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-lg font-black px-2.5 py-0.5 rounded border ${getScoreColor(selectedStock.total_score)}`}>
                  {selectedStock.total_score.toFixed(1)} / 100
                </span>
                <span className="block text-[10px] text-gray-400 mt-1 uppercase">Composite Score</span>
              </div>
            </div>

            <div className="space-y-3 mb-4">
              <h4 className="text-xs font-bold uppercase text-gray-400 tracking-wider">Scoring Factor Matrix</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(selectedStock.components || {}).map(([key, val]) => (
                  <div key={key} className="bg-[#090c10] border border-[#1e2638] p-2 rounded flex justify-between items-center">
                    <span className="text-gray-400 capitalize">{key.replace("_", " ")}</span>
                    <strong className="text-white font-mono">{val}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg mb-4 text-xs space-y-2">
              <div>
                <span className="text-[10px] uppercase font-bold text-gray-400 block mb-0.5">Technical Rationale</span>
                <p className="text-gray-200 leading-relaxed">{selectedStock.reason}</p>
              </div>

              {selectedStock.risk_warnings && selectedStock.risk_warnings.length > 0 && (
                <div className="pt-2 border-t border-gray-800 text-amber-300 text-[11px]">
                  <span className="font-bold block uppercase text-[10px]">Specific Risk Warnings:</span>
                  <ul className="list-disc list-inside space-y-0.5 mt-0.5">
                    {selectedStock.risk_warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setSelectedStock(null)}
                className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
