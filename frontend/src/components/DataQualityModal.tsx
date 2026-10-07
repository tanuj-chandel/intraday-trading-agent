"use client";

import React from "react";
import { DataQualityResponse } from "@/types";
import { ShieldCheck, AlertTriangle, X, Database, CheckCircle2, Clock } from "lucide-react";

interface DataQualityModalProps {
  data: DataQualityResponse | null;
  isOpen: boolean;
  onClose: () => void;
  loading: boolean;
}

export const DataQualityModal: React.FC<DataQualityModalProps> = ({
  data,
  isOpen,
  onClose,
  loading
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#121721] border border-[#1e2638] rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e2638] bg-[#090c10]">
          <div className="flex items-center gap-2.5">
            <Database className="h-5 w-5 text-blue-400" />
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                Data Provenance & Quality Inspector
              </h2>
              <span className="text-[11px] text-gray-400">
                Transparent Data Source & Freshness Audit Trail
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

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs text-gray-300">
          {loading || !data ? (
            <div className="text-center py-8 text-gray-400">
              Loading data provenance metadata...
            </div>
          ) : (
            <>
              {/* Overall Status Banner */}
              <div
                className={`p-3 rounded-lg border flex items-center justify-between ${
                  data.overall_status === "HEALTHY"
                    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                    : "bg-amber-500/10 border-amber-500/30 text-amber-300"
                }`}
              >
                <div className="flex items-center gap-2">
                  {data.overall_status === "HEALTHY" ? (
                    <ShieldCheck className="h-5 w-5 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-amber-400" />
                  )}
                  <div>
                    <span className="font-bold block uppercase text-xs">
                      Overall Status: {data.overall_status}
                    </span>
                    <span className="text-[11px] opacity-80">
                      Tracking {data.total_datasets} data pipelines
                    </span>
                  </div>
                </div>
                <span className="text-[10px] opacity-75 font-mono">
                  Checked: {new Date(data.checked_at).toLocaleTimeString()}
                </span>
              </div>

              {/* Datasets Table */}
              <div className="border border-[#1e2638] rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-[#090c10] border-b border-[#1e2638] text-gray-400 uppercase text-[10px]">
                      <th className="py-2.5 px-3">Dataset</th>
                      <th className="py-2.5 px-3">Active Source</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3 text-right">Age</th>
                      <th className="py-2.5 px-3 text-center">Freshness</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e2638]">
                    {Object.entries(data.datasets).map(([name, item]) => {
                      const isStale = item.status === "STALE";
                      const isMock = item.status === "MOCK";
                      return (
                        <tr key={name} className="hover:bg-[#182030]/60">
                          <td className="py-2 px-3 font-bold text-white font-mono">{item.dataset_name}</td>
                          <td className="py-2 px-3 text-gray-300">{item.source}</td>
                          <td className="py-2 px-3">
                            <span
                              className={`text-[10px] font-bold px-1.5 py-0.2 rounded border ${
                                item.status === "LIVE"
                                  ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                                  : isMock
                                  ? "text-amber-400 bg-amber-500/10 border-amber-500/30"
                                  : "text-rose-400 bg-rose-500/10 border-rose-500/30"
                              }`}
                            >
                              {item.status}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right font-mono text-gray-400">
                            {item.age_seconds.toFixed(0)}s
                          </td>
                          <td className="py-2 px-3 text-center">
                            <span
                              className={`text-[10px] font-semibold ${
                                isStale ? "text-rose-400 font-bold animate-pulse" : "text-emerald-400"
                              }`}
                            >
                              {item.freshness}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Safety Disclaimers */}
              <div className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg text-[11px] text-gray-400 space-y-1">
                <span className="font-bold text-white block uppercase text-[10px]">Data Integrity Guarantee</span>
                <p>
                  The system never masks simulated/mock data as real live data. When Broker API credentials are not provided in environment variables, the system explicitly flags data status as <strong className="text-amber-400 font-mono">MOCK</strong>.
                </p>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#1e2638] bg-[#090c10] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
