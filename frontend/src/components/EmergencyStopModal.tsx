"use client";

import React, { useState } from "react";
import { ShieldAlert, AlertOctagon, X } from "lucide-react";

interface EmergencyStopModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason: string) => void;
  loading: boolean;
}

export const EmergencyStopModal: React.FC<EmergencyStopModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  loading
}) => {
  const [reason, setReason] = useState("Manual User Emergency Override");

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#181115] border border-rose-900/60 rounded-2xl max-w-md w-full p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-rose-900/40">
          <div className="flex items-center gap-2.5 text-rose-500 font-bold">
            <AlertOctagon className="h-6 w-6" />
            <h2 className="text-base tracking-wider uppercase">Emergency Kill Switch</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="my-4 text-xs text-rose-200/90 space-y-3">
          <p className="font-semibold text-white">
            WARNING: Triggering the Emergency Stop will immediately:
          </p>
          <ul className="list-disc list-inside space-y-1 text-rose-300">
            <li>Liquidate and close all active paper positions at market prices.</li>
            <li>Cancel and reject all pending trading signals.</li>
            <li>Halt all further automated order execution.</li>
          </ul>

          <div className="mt-4">
            <label className="block text-[11px] text-gray-400 uppercase font-bold mb-1">
              Reason for Kill Switch
            </label>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-[#090c10] border border-rose-900/60 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 pt-3 border-t border-rose-900/40">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(reason)}
            disabled={loading}
            className="px-5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-black tracking-wider uppercase shadow-lg disabled:opacity-50 flex items-center gap-1.5"
          >
            <ShieldAlert className="h-4 w-4" />
            {loading ? "HALTING..." : "CONFIRM KILL SWITCH"}
          </button>
        </div>
      </div>
    </div>
  );
};
