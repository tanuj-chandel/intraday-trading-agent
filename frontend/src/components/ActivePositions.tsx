"use client";

import React from "react";
import { PaperPosition } from "@/types";
import { formatINR, formatPercent } from "@/lib/utils";
import { Layers, XCircle, ArrowUpRight, ArrowDownRight, ShieldCheck } from "lucide-react";

interface ActivePositionsProps {
  positions: PaperPosition[];
  onClosePosition: (id: number) => void;
  loading: boolean;
}

export const ActivePositions: React.FC<ActivePositionsProps> = ({
  positions,
  onClosePosition,
  loading
}) => {
  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-emerald-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Active Paper Positions ({positions.length}/3)
          </h2>
        </div>
        <span className="text-[11px] text-gray-400">
          Trailing Stops & Auto-Squareoff (15:15 IST) Active
        </span>
      </div>

      {positions.length === 0 ? (
        <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-6 text-center text-xs text-gray-500">
          No open positions. Generate signals or run pre-market scan to initiate simulated trades.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#1e2638] text-gray-400 uppercase text-[10px] bg-[#090c10]/60">
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Side</th>
                <th className="py-2.5 px-3 text-center">Qty</th>
                <th className="py-2.5 px-3 text-right">Entry Price</th>
                <th className="py-2.5 px-3 text-right">CMP</th>
                <th className="py-2.5 px-3">Trailing SL</th>
                <th className="py-2.5 px-3">Target</th>
                <th className="py-2.5 px-3 text-right">Unrealized P&L</th>
                <th className="py-2.5 px-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2638]/50">
              {positions.map((pos) => {
                const isBuy = pos.side === "BUY";
                const isProfit = pos.unrealized_pnl >= 0;
                return (
                  <tr key={pos.id} className="hover:bg-[#182030]/60 transition-colors">
                    <td className="py-2 px-3 font-bold text-white">{pos.symbol}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`inline-flex items-center gap-1 font-bold px-1.5 py-0.5 rounded text-[10px] ${
                          isBuy ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"
                        }`}
                      >
                        {isBuy ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                        {pos.side}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center font-mono">{pos.quantity}</td>
                    <td className="py-2 px-3 text-right font-mono text-gray-300">{formatINR(pos.entry_price)}</td>
                    <td className="py-2 px-3 text-right font-mono font-bold text-white">{formatINR(pos.current_price)}</td>
                    <td className="py-2 px-3 font-mono text-amber-400">
                      <div className="flex items-center gap-1">
                        <ShieldCheck className="h-3 w-3 inline" />
                        {formatINR(pos.trailing_stop || pos.stop_loss)}
                      </div>
                    </td>
                    <td className="py-2 px-3 font-mono text-emerald-400">{formatINR(pos.target_price)}</td>
                    <td className={`py-2 px-3 text-right font-bold font-mono ${isProfit ? "text-emerald-400" : "text-rose-400"}`}>
                      {isProfit ? `+${formatINR(pos.unrealized_pnl)}` : formatINR(pos.unrealized_pnl)}
                      <span className="block text-[10px] opacity-80 font-normal">
                        ({formatPercent(pos.unrealized_pnl_pct)})
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <button
                        onClick={() => onClosePosition(pos.id)}
                        className="px-2.5 py-1 rounded bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white text-[11px] font-semibold border border-rose-500/40 transition-colors inline-flex items-center gap-1"
                      >
                        <XCircle className="h-3 w-3" />
                        Close
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
