"use client";

import React, { useState } from "react";
import { GlobalMarketResponse, GiftNiftyResponse } from "@/types";
import { formatINR, formatPercent } from "@/lib/utils";
import { Globe, TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, Edit3, ShieldAlert, Sparkles } from "lucide-react";

interface GlobalMarketWidgetProps {
  globalData: GlobalMarketResponse | null;
  giftNifty: GiftNiftyResponse | null;
  onUpdateManualGiftNifty: (price: number) => void;
  loading: boolean;
}

export const GlobalMarketWidget: React.FC<GlobalMarketWidgetProps> = ({
  globalData,
  giftNifty,
  onUpdateManualGiftNifty,
  loading
}) => {
  const [isEditingGift, setIsEditingGift] = useState(false);
  const [manualPrice, setManualPrice] = useState<string>("");

  if (loading || !globalData || !giftNifty) {
    return (
      <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 animate-pulse">
        <div className="h-6 w-48 bg-gray-800 rounded mb-3"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="h-20 bg-gray-800 rounded"></div>
          <div className="h-20 bg-gray-800 rounded"></div>
          <div className="h-20 bg-gray-800 rounded"></div>
          <div className="h-20 bg-gray-800 rounded"></div>
        </div>
      </div>
    );
  }

  const score = globalData.global_market_score;
  const isBullish = score > 15;
  const isBearish = score < -15;

  const getScoreColor = () => {
    if (isBullish) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
    if (isBearish) return "text-rose-400 bg-rose-500/10 border-rose-500/30";
    return "text-slate-400 bg-slate-500/10 border-slate-500/30";
  };

  const handleSaveManualGift = () => {
    const val = parseFloat(manualPrice);
    if (!isNaN(val) && val > 10000) {
      onUpdateManualGiftNifty(val);
      setIsEditingGift(false);
      setManualPrice("");
    }
  };

  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Global Macro Sentiment & GIFT Nifty Pre-Open Stance
          </h2>
        </div>

        {/* Global Sentiment Meter */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-gray-400">Macro Bias:</span>
          <span className={`text-xs font-black px-2.5 py-0.5 rounded border uppercase flex items-center gap-1 ${getScoreColor()}`}>
            {isBullish ? <TrendingUp className="h-3.5 w-3.5" /> : isBearish ? <TrendingDown className="h-3.5 w-3.5" /> : null}
            {globalData.sentiment} ({score > 0 ? `+${score}` : score}/100)
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
        {/* Card 1: GIFT NIFTY Opening Projection */}
        <div className="bg-[#090c10] border border-blue-500/30 rounded-lg p-3.5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-400 flex items-center gap-1">
                <Sparkles className="h-3.5 w-3.5" /> GIFT NIFTY (NSE IX)
              </span>
              <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 uppercase">
                {giftNifty.data_status}
              </span>
            </div>

            <div className="my-2">
              <div className="text-xl font-black text-white">
                {formatINR(giftNifty.gift_nifty_price)}
              </div>
              <div className="flex items-center gap-1 text-xs mt-0.5">
                <span className={`font-bold ${giftNifty.gap_points >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {giftNifty.gap_points >= 0 ? `+${giftNifty.gap_points.toFixed(1)}` : giftNifty.gap_points.toFixed(1)} pts
                </span>
                <span className="text-gray-400 font-medium">
                  ({formatPercent(giftNifty.gap_pct)})
                </span>
                <span className="text-[10px] px-1 rounded bg-gray-800 text-gray-300 font-bold ml-1">
                  {giftNifty.gap_direction}
                </span>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-800/80 pt-2 flex items-center justify-between text-[10px]">
            <span className="text-gray-400 truncate max-w-[140px]">Source: {giftNifty.source}</span>
            <button
              onClick={() => setIsEditingGift(true)}
              className="text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold"
            >
              <Edit3 className="h-3 w-3" /> Manual Input
            </button>
          </div>

          {/* Manual Input Dialog */}
          {isEditingGift && (
            <div className="mt-2 pt-2 border-t border-gray-800">
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  placeholder="e.g. 24850"
                  value={manualPrice}
                  onChange={(e) => setManualPrice(e.target.value)}
                  className="bg-[#121721] border border-gray-700 rounded px-2 py-1 text-xs text-white w-full focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleSaveManualGift}
                  className="px-2 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold"
                >
                  Set
                </button>
                <button
                  onClick={() => setIsEditingGift(false)}
                  className="px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs"
                >
                  X
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Card 2: US Equity Cues */}
        <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-bold text-gray-300 mb-2">
              <span>US Benchmarks</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${globalData.us_trend === "BULLISH" ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"}`}>
                {globalData.us_trend}
              </span>
            </div>
            <div className="space-y-1.5 text-xs">
              {globalData.indices.filter(i => i.region === "US").map(idx => (
                <div key={idx.name} className="flex items-center justify-between">
                  <span className="text-gray-400 text-[11px]">{idx.name}</span>
                  <span className={`font-mono font-semibold ${idx.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {idx.price.toLocaleString()} ({formatPercent(idx.change_pct)})
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="text-[10px] text-gray-500 border-t border-gray-800/60 pt-1.5 mt-2">
            Tech leadership providing risk-on cues
          </div>
        </div>

        {/* Card 3: Asian Equity Cues */}
        <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-bold text-gray-300 mb-2">
              <span>Asian Equities</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded font-bold text-blue-400 bg-blue-500/10">
                {globalData.asia_trend}
              </span>
            </div>
            <div className="space-y-1.5 text-xs">
              {globalData.indices.filter(i => i.region === "Asia").map(idx => (
                <div key={idx.name} className="flex items-center justify-between">
                  <span className="text-gray-400 text-[11px]">{idx.name}</span>
                  <span className={`font-mono font-semibold ${idx.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {idx.price.toLocaleString()} ({formatPercent(idx.change_pct)})
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="text-[10px] text-gray-500 border-t border-gray-800/60 pt-1.5 mt-2">
            Nikkei & Hang Seng regional tone
          </div>
        </div>

        {/* Card 4: Commodities & Macro (Crude, Gold, DXY) */}
        <div className="bg-[#090c10] border border-[#1e2638] rounded-lg p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-bold text-gray-300 mb-2">
              <span>Commodities & DXY</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded font-bold text-emerald-400 bg-emerald-500/10">
                Tailwind
              </span>
            </div>
            <div className="space-y-1.5 text-xs">
              {globalData.indices.filter(i => ["Commodity", "Currencies", "Bonds"].includes(i.region)).slice(0, 3).map(idx => (
                <div key={idx.name} className="flex items-center justify-between">
                  <span className="text-gray-400 text-[11px] truncate max-w-[110px]">{idx.name}</span>
                  <span className={`font-mono font-semibold ${idx.change_pct <= 0 ? "text-emerald-400" : "text-amber-400"}`}>
                    {idx.price} ({formatPercent(idx.change_pct)})
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="text-[10px] text-gray-400 border-t border-gray-800/60 pt-1.5 mt-2 truncate">
            {globalData.crude_oil_stance}
          </div>
        </div>
      </div>
    </div>
  );
};
