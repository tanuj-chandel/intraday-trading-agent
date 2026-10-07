"use client";

import React from "react";
import { NewsItem } from "@/types";
import { Newspaper, Flame, TrendingUp, TrendingDown, Minus, ShieldCheck, Tag } from "lucide-react";

interface NewsIntelligenceProps {
  news: NewsItem[];
  loading: boolean;
}

export const NewsIntelligence: React.FC<NewsIntelligenceProps> = ({ news, loading }) => {
  if (loading) {
    return (
      <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 animate-pulse">
        <div className="h-6 w-36 bg-gray-800 rounded mb-4"></div>
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-800 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case "BULLISH":
        return (
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Bullish
          </span>
        );
      case "BEARISH":
        return (
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center gap-1">
            <TrendingDown className="h-3 w-3" />
            Bearish
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-500/10 border border-slate-500/30 text-slate-400 flex items-center gap-1">
            <Minus className="h-3 w-3" />
            Neutral
          </span>
        );
    }
  };

  const getReliabilityTag = (rel: string) => {
    if (rel === "LEVEL_1") {
      return (
        <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-0.5">
          <ShieldCheck className="h-2.5 w-2.5" /> L1 Exchange Filing
        </span>
      );
    } else if (rel === "LEVEL_2") {
      return (
        <span className="text-[9px] font-medium px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40">
          L2 Financial Media
        </span>
      );
    }
    return (
      <span className="text-[9px] px-1.5 py-0.2 rounded bg-gray-700 text-gray-300 border border-gray-600">
        L3 Unverified
      </span>
    );
  };

  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Newspaper className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            News Intelligence & Corporate Disclosure Stream
          </h2>
        </div>
        <span className="text-[11px] text-gray-400">
          Official Exchange Filings & Tier-1 Media Feed
        </span>
      </div>

      <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
        {news.map((item, idx) => (
          <div
            key={item.id || idx}
            className="bg-[#090c10] border border-[#1e2638] rounded-lg p-3 hover:border-gray-700 transition-colors"
          >
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-[10px] font-semibold text-gray-300 font-mono">{item.source}</span>
                {getReliabilityTag(item.source_reliability)}
                <span className="text-[9px] font-semibold px-1.5 py-0.2 rounded bg-[#1e2638] text-gray-300 flex items-center gap-0.5">
                  <Tag className="h-2.5 w-2.5 text-blue-400" /> {item.event_category}
                </span>
                {item.impact === "HIGH" && (
                  <span className="text-[9px] font-bold px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-0.5">
                    <Flame className="h-2.5 w-2.5" /> High Impact
                  </span>
                )}
              </div>
              {getSentimentBadge(item.sentiment)}
            </div>

            <p className="text-xs font-semibold text-gray-200 leading-snug mb-2">
              {item.headline}
            </p>

            <div className="flex items-center justify-between text-[10px] text-gray-400 border-t border-gray-800/60 pt-1.5">
              <div className="flex items-center gap-1.5 flex-wrap">
                {item.related_symbols.map((sym) => (
                  <span
                    key={sym}
                    className="px-1.5 py-0.5 rounded bg-[#1e2638] text-blue-300 font-mono"
                  >
                    {sym}
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-2">
                <span>Impact Score: <strong className="text-white font-mono">{item.impact_score?.toFixed(0) || 50}/100</strong></span>
                <span>{new Date(item.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
