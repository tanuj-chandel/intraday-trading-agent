"use client";

import React from "react";
import { TradeSignal } from "@/types";
import { formatINR } from "@/lib/utils";
import { CheckCircle2, XCircle, Zap, Shield, ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";

interface LiveSignalsProps {
  signals: TradeSignal[];
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
  loading: boolean;
}

export const LiveSignals: React.FC<LiveSignalsProps> = ({
  signals,
  onApprove,
  onReject,
  loading
}) => {
  const pendingSignals = signals.filter((s) => s.status === "PENDING" || s.status === "PENDING_APPROVAL");

  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Strategy Signals & Approval Workflow ({pendingSignals.length} Pending)
          </h2>
        </div>
        <span className="text-[11px] text-gray-400">
          Two-Way Telegram & Web Safe Approval
        </span>
      </div>

      {signals.length === 0 ? (
        <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-6 text-center text-xs text-gray-500">
          No active signals in stream. Click "Scan Signals" or run Pre-Market Analysis to trigger scanner.
        </div>
      ) : (
        <div className="space-y-3 max-h-[340px] overflow-y-auto pr-1">
          {signals.map((sig) => {
            const isBuy = sig.direction === "BUY";
            const isPending = sig.status === "PENDING" || sig.status === "PENDING_APPROVAL";
            const isExecuted = sig.status === "EXECUTED";
            const isRejected = sig.status === "REJECTED";
            const isExpired = sig.status === "EXPIRED" || sig.status === "CANCELLED";

            return (
              <div
                key={sig.id}
                className={`bg-[#090c10] border rounded-lg p-3.5 transition-all ${
                  isPending ? "border-blue-500/40 shadow-sm" : "border-[#1e2638] opacity-75"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-black text-white">{sig.symbol}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 ${
                        isBuy ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/30" : "text-rose-400 bg-rose-500/10 border border-rose-500/30"
                      }`}
                    >
                      {isBuy ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                      {sig.direction}
                    </span>
                    <span className="text-[10px] bg-gray-800 text-gray-300 px-1.5 py-0.5 rounded">
                      Score: {sig.strategy_score.toFixed(0)}
                    </span>
                  </div>

                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
                      isPending
                        ? "text-amber-300 bg-amber-500/10 border-amber-500/30 animate-pulse"
                        : isExecuted
                        ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                        : "text-rose-400 bg-rose-500/10 border-rose-500/30"
                    }`}
                  >
                    {sig.status}
                  </span>
                </div>

                {/* Price and Parameters Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 my-2.5 bg-[#121721] p-2 rounded text-[11px] border border-gray-800">
                  <div>
                    <span className="text-gray-400 block text-[9px] uppercase">Entry</span>
                    <strong className="text-white font-mono">{formatINR(sig.entry_price)}</strong>
                  </div>
                  <div>
                    <span className="text-gray-400 block text-[9px] uppercase">Stop Loss</span>
                    <strong className="text-rose-400 font-mono">{formatINR(sig.stop_loss)}</strong>
                  </div>
                  <div>
                    <span className="text-gray-400 block text-[9px] uppercase">Target (1:2 R:R)</span>
                    <strong className="text-emerald-400 font-mono">{formatINR(sig.target_price)}</strong>
                  </div>
                  <div>
                    <span className="text-gray-400 block text-[9px] uppercase">Qty / Risk</span>
                    <strong className="text-blue-400 font-mono">{sig.quantity} sh ({formatINR(sig.risk_amount)})</strong>
                  </div>
                </div>

                {/* Rationale description */}
                <p className="text-[11px] text-gray-300 leading-relaxed mb-2">
                  {sig.explanation}
                </p>

                {/* Show rejection / cancellation reason if present */}
                {sig.reject_reason && (
                  <div className="text-[10px] text-rose-300 bg-rose-950/30 border border-rose-500/20 rounded p-1.5 mb-2 font-mono">
                    <strong>Note:</strong> {sig.reject_reason}
                  </div>
                )}

                {/* Action Buttons if Pending */}
                {isPending && (
                  <div className="flex items-center justify-end gap-2 border-t border-gray-800 pt-2">
                    <button
                      onClick={() => onReject(sig.id)}
                      className="px-3 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 text-xs font-semibold border border-rose-500/30 transition-colors flex items-center gap-1"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                      Reject
                    </button>
                    <button
                      onClick={() => onApprove(sig.id)}
                      className="px-4 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors flex items-center gap-1 shadow-md"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Approve Entry
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
