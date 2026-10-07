"use client";

import { useEffect } from "react";

export default function GlobalErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard render error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#090c10] text-gray-100 p-8 font-mono flex flex-col items-center justify-center">
      <div className="max-w-md w-full border border-[#1e2638] bg-[#121721] p-6 rounded-xl text-center">
        <h2 className="text-xl font-bold text-amber-400 mb-2">Terminal View Restored</h2>
        <p className="text-xs text-gray-400 mb-4">
          Trading engine is operating normally in the background. Click below to reconnect the UI.
        </p>
        <p className="text-[11px] text-gray-500 font-mono bg-black/40 p-2 rounded mb-4 overflow-x-auto text-left">
          {error.message || "Unknown error"}
        </p>
        <button
          onClick={() => reset()}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-xs text-white font-bold transition-colors"
        >
          ↻ Refresh Terminal
        </button>
      </div>
    </div>
  );
}
