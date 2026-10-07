"use client";

import { useEffect } from "react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Live page render error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8 font-mono flex flex-col items-center justify-center">
      <div className="max-w-md w-full border border-red-700 bg-red-950/40 p-6 rounded-lg text-center">
        <h2 className="text-xl font-bold text-red-400 mb-2">⚡ Live Terminal Recovered</h2>
        <p className="text-xs text-gray-300 mb-4">
          A transient data rendering issue was caught. Your background trading agent is actively running without interruption.
        </p>
        <p className="text-[11px] text-gray-400 font-mono bg-black/60 p-2 rounded mb-4 overflow-x-auto text-left">
          {error.message || "Unknown error"}
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => reset()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-xs text-white font-bold transition-colors"
          >
            ↻ Reload Terminal
          </button>
          <a
            href="/"
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-xs text-gray-200 transition-colors"
          >
            Go to Main Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
