"use client";

import React from "react";
import { TradeJournalItem } from "@/types";
import { formatINR } from "@/lib/utils";
import { BookOpen, ArrowUpRight, ArrowDownRight } from "lucide-react";

interface TradeJournalProps {
  trades: TradeJournalItem[];
  loading: boolean;
}

export const TradeJournal: React.FC<TradeJournalProps> = ({ trades, loading }) => {
  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-purple-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Trade Journal & Audit Log ({trades.length} Executed)
          </h2>
        </div>
        <span className="text-[11px] text-gray-400">
          Transparent Execution Trail
        </span>
      </div>

      {trades.length === 0 ? (
        <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-6 text-center text-xs text-gray-500">
          No executed trades recorded in journal yet.
        </div>
      ) : (
        <div className="overflow-x-auto max-h-[360px] overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#1e2638] text-gray-400 uppercase text-[10px] bg-[#090c10]/60 sticky top-0">
                <th className="py-2.5 px-3">Date / Time</th>
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Side</th>
                <th className="py-2.5 px-3 text-right">Entry</th>
                <th className="py-2.5 px-3 text-right">Exit</th>
                <th className="py-2.5 px-3 text-center">Qty</th>
                <th className="py-2.5 px-3 text-right">Gross P&L</th>
                <th className="py-2.5 px-3 text-right">Charges</th>
                <th className="py-2.5 px-3 text-right">Net P&L</th>
                <th className="py-2.5 px-3">Exit Reason</th>
                <th className="py-2.5 px-3">Hold Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e2638]/50">
              {trades.map((t) => {
                const isBuy = t.direction === "BUY";
                const isNetWin = t.net_pnl > 0;
                return (
                  <tr key={t.id} className="hover:bg-[#182030]/60 transition-colors">
                    <td className="py-2 px-3 text-[11px] text-gray-400 font-mono">
                      {new Date(t.exit_time).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}{" "}
                      {new Date(t.exit_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                    <td className="py-2 px-3 font-bold text-white">{t.symbol}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`inline-flex items-center gap-0.5 font-bold px-1.5 py-0.2 rounded text-[10px] ${
                          isBuy ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"
                        }`}
                      >
                        {isBuy ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                        {t.direction}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-gray-300">{formatINR(t.entry_price)}</td>
                    <td className="py-2 px-3 text-right font-mono text-gray-300">{formatINR(t.exit_price)}</td>
                    <td className="py-2 px-3 text-center font-mono">{t.quantity}</td>
                    <td className={`py-2 px-3 text-right font-mono font-medium ${t.gross_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {t.gross_pnl >= 0 ? `+${formatINR(t.gross_pnl)}` : formatINR(t.gross_pnl)}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-gray-400">{formatINR(t.estimated_charges)}</td>
                    <td className={`py-2 px-3 text-right font-mono font-bold ${isNetWin ? "text-emerald-400" : "text-rose-400"}`}>
                      {isNetWin ? `+${formatINR(t.net_pnl)}` : formatINR(t.net_pnl)}
                    </td>
                    <td className="py-2 px-3">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-300 font-mono">
                        {t.reason_for_exit || "AUTO_EXIT"}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-gray-400 font-mono text-[11px]">{t.holding_time_minutes.toFixed(0)}m</td>
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
