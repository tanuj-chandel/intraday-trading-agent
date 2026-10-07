"use client";

import React from "react";
import { PreMarketAnalysis } from "@/types";
import { formatINR } from "@/lib/utils";
import { FileText, Globe, AlertTriangle, CheckCircle, TrendingUp, X } from "lucide-react";

interface PreMarketModalProps {
  data: PreMarketAnalysis | null;
  isOpen: boolean;
  onClose: () => void;
  loading: boolean;
}

export const PreMarketModal: React.FC<PreMarketModalProps> = ({
  data,
  isOpen,
  onClose,
  loading
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#121721] border border-[#1e2638] rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e2638] bg-[#090c10]">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <FileText className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white uppercase tracking-wider">
                Pre-Market Intelligence Report (08:45 IST)
              </h2>
              <span className="text-xs text-gray-400">
                Indian Equities Macro, Global Cues & Actionable Setups
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-gray-300">
          {loading || !data ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-3"></div>
              <p className="text-gray-400">Aggregating global cues, sector flows, and running stock universe ranking...</p>
            </div>
          ) : (
            <>
              {/* Top Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-[#090c10] border border-[#1e2638] p-3.5 rounded-xl">
                  <div className="flex items-center gap-1.5 font-bold text-blue-400 mb-1.5 uppercase text-[11px]">
                    <Globe className="h-3.5 w-3.5" />
                    Global Market Cues
                  </div>
                  <p className="leading-relaxed text-gray-200">{data.global_market_summary}</p>
                </div>

                <div className="bg-[#090c10] border border-[#1e2638] p-3.5 rounded-xl">
                  <div className="flex items-center gap-1.5 font-bold text-emerald-400 mb-1.5 uppercase text-[11px]">
                    <TrendingUp className="h-3.5 w-3.5" />
                    Indian Benchmark Stance ({data.market_regime})
                  </div>
                  <p className="leading-relaxed text-gray-200">{data.market_overview}</p>
                </div>
              </div>

              {/* Risk Warnings & Guardrails */}
              <div className="bg-amber-500/10 border border-amber-500/30 p-3.5 rounded-xl text-amber-200">
                <div className="flex items-center gap-1.5 font-bold uppercase text-[11px] mb-1.5 text-amber-300">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                  Intraday Risk Parameters & Execution Warnings
                </div>
                <ul className="list-disc list-inside space-y-1 text-[11px]">
                  {data.risk_warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>

              {/* Sector Performance Bar */}
              <div>
                <h3 className="text-xs font-bold uppercase text-gray-400 tracking-wider mb-2">
                  Relative Sector Strength Heatmap
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {Object.entries(data.sector_performance).map(([sec, val]) => (
                    <div key={sec} className="bg-[#090c10] border border-[#1e2638] p-2 rounded text-center">
                      <span className="block text-[10px] text-gray-400 truncate">{sec}</span>
                      <strong className={`font-mono text-xs ${val >= 70 ? "text-emerald-400" : val >= 50 ? "text-blue-400" : "text-rose-400"}`}>
                        {val.toFixed(0)}/100
                      </strong>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top 5 Highlight Setups */}
              <div>
                <h3 className="text-xs font-bold uppercase text-gray-400 tracking-wider mb-2">
                  Top Recommended Candidate Setups
                </h3>
                <div className="space-y-2">
                  {data.top_ranked_stocks.slice(0, 5).map((stock) => (
                    <div key={stock.symbol} className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-sm">{stock.symbol}</span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 font-bold">
                            {stock.direction}
                          </span>
                          <span className="text-[10px] text-gray-400">Score: {stock.total_score.toFixed(1)}</span>
                        </div>
                        <p className="text-[11px] text-gray-400 mt-0.5">{stock.reason}</p>
                      </div>

                      <div className="flex items-center gap-4 text-[11px] font-mono shrink-0">
                        <div>
                          <span className="text-[9px] text-gray-500 block">ENTRY ZONE</span>
                          <span className="text-gray-200">{stock.entry_zone}</span>
                        </div>
                        <div>
                          <span className="text-[9px] text-rose-400 block">STOP LOSS</span>
                          <span className="text-rose-400 font-bold">{formatINR(stock.stop_loss)}</span>
                        </div>
                        <div>
                          <span className="text-[9px] text-emerald-400 block">TARGET (1:2)</span>
                          <span className="text-emerald-400 font-bold">{formatINR(stock.target)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-[#1e2638] bg-[#090c10] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
          >
            Acknowledge & Close
          </button>
        </div>
      </div>
    </div>
  );
};
