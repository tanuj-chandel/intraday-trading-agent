"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { MarketOverview } from "@/components/MarketOverview";
import { GlobalMarketWidget } from "@/components/GlobalMarketWidget";
import { TopRankedStocks } from "@/components/TopRankedStocks";
import { ActivePositions } from "@/components/ActivePositions";
import { LiveSignals } from "@/components/LiveSignals";
import { NewsIntelligence } from "@/components/NewsIntelligence";
import { PerformanceMetrics } from "@/components/PerformanceMetrics";
import { TradeJournal } from "@/components/TradeJournal";
import { PreMarketModal } from "@/components/PreMarketModal";
import { DataQualityModal } from "@/components/DataQualityModal";
import { EmergencyStopModal } from "@/components/EmergencyStopModal";
import { MobileNotificationCard } from "@/components/MobileNotificationCard";

import {
  fetchSystemStatus,
  fetchMarketOverview,
  fetchGlobalMarkets,
  fetchGiftNifty,
  setManualGiftNifty,
  fetchDataQuality,
  fetchCategorizedTopStocks,
  fetchNews,
  fetchSignals,
  generateSignals,
  approveSignal,
  rejectSignal,
  fetchPositions,
  closePosition,
  fetchTrades,
  fetchPerformance,
  runPreMarketAnalysis,
  triggerEmergencyStop
} from "@/lib/api";

import {
  SystemStatus,
  MarketOverviewResponse,
  GlobalMarketResponse,
  GiftNiftyResponse,
  DataQualityResponse,
  StockScore,
  NewsItem,
  TradeSignal,
  PaperPosition,
  TradeJournalItem,
  PerformanceMetrics as PerformanceMetricsType,
  PreMarketAnalysis
} from "@/types";

export default function Dashboard() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [marketOverview, setMarketOverview] = useState<MarketOverviewResponse | null>(null);
  const [globalData, setGlobalData] = useState<GlobalMarketResponse | null>(null);
  const [giftNifty, setGiftNifty] = useState<GiftNiftyResponse | null>(null);
  const [dataQuality, setDataQuality] = useState<DataQualityResponse | null>(null);

  const [topOverall, setTopOverall] = useState<StockScore[]>([]);
  const [topLongs, setTopLongs] = useState<StockScore[]>([]);
  const [topShorts, setTopShorts] = useState<StockScore[]>([]);

  const [news, setNews] = useState<NewsItem[]>([]);
  const [signals, setSignals] = useState<TradeSignal[]>([]);
  const [positions, setPositions] = useState<PaperPosition[]>([]);
  const [trades, setTrades] = useState<TradeJournalItem[]>([]);
  const [performance, setPerformance] = useState<PerformanceMetricsType | null>(null);

  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isGeneratingSignals, setIsGeneratingSignals] = useState(false);
  const [isPreMarketOpen, setIsPreMarketOpen] = useState(false);
  const [preMarketData, setPreMarketData] = useState<PreMarketAnalysis | null>(null);
  const [isPreMarketLoading, setIsPreMarketLoading] = useState(false);
  const [isDataQualityOpen, setIsDataQualityOpen] = useState(false);
  const [isEmergencyStopOpen, setIsEmergencyStopOpen] = useState(false);
  const [isEmergencyLoading, setIsEmergencyLoading] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  const loadAllData = useCallback(async () => {
    try {
      const [
        statusRes,
        marketRes,
        globalRes,
        giftRes,
        qualityRes,
        categorizedRes,
        newsRes,
        signalsRes,
        posRes,
        tradesRes,
        perfRes
      ] = await Promise.allSettled([
        fetchSystemStatus(),
        fetchMarketOverview(),
        fetchGlobalMarkets(),
        fetchGiftNifty(),
        fetchDataQuality(),
        fetchCategorizedTopStocks(),
        fetchNews(15),
        fetchSignals(),
        fetchPositions(),
        fetchTrades(),
        fetchPerformance()
      ]);

      if (statusRes.status === "fulfilled") setStatus(statusRes.value);
      if (marketRes.status === "fulfilled") setMarketOverview(marketRes.value);
      if (globalRes.status === "fulfilled") setGlobalData(globalRes.value);
      if (giftRes.status === "fulfilled") setGiftNifty(giftRes.value);
      if (qualityRes.status === "fulfilled") setDataQuality(qualityRes.value);

      if (categorizedRes.status === "fulfilled") {
        setTopOverall(categorizedRes.value.top_overall);
        setTopLongs(categorizedRes.value.top_longs);
        setTopShorts(categorizedRes.value.top_shorts);
      }

      if (newsRes.status === "fulfilled") setNews(newsRes.value);
      if (signalsRes.status === "fulfilled") setSignals(signalsRes.value);
      if (posRes.status === "fulfilled") setPositions(posRes.value);
      if (tradesRes.status === "fulfilled") setTrades(tradesRes.value);
      if (perfRes.status === "fulfilled") setPerformance(perfRes.value);
    } catch (err) {
      console.error("Error refreshing dashboard data:", err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 5000);
    return () => clearInterval(interval);
  }, [loadAllData]);

  const handleRefreshData = async () => {
    setIsRefreshing(true);
    await loadAllData();
    showNotification("Data refreshed from active market providers.");
  };

  const handleUpdateManualGiftNifty = async (price: number) => {
    try {
      await setManualGiftNifty(price);
      showNotification(`GIFT Nifty manually set to ₹${price}`);
      await loadAllData();
    } catch (err) {
      showNotification("Failed to update manual GIFT Nifty level.");
    }
  };

  const handleGenerateSignals = async () => {
    setIsGeneratingSignals(true);
    try {
      const newSigs = await generateSignals();
      showNotification(`Scanner complete: Generated ${newSigs.length} high-probability trade setups.`);
      await loadAllData();
    } catch (err) {
      showNotification("Failed to scan for signals.");
    } finally {
      setIsGeneratingSignals(false);
    }
  };

  const handleApproveSignal = async (id: number) => {
    try {
      const res = await approveSignal(id);
      showNotification(res.message || "Signal approved & paper order executed!");
      await loadAllData();
    } catch (err: any) {
      showNotification(`Approval failed: ${err.message}`);
    }
  };

  const handleRejectSignal = async (id: number) => {
    try {
      await rejectSignal(id);
      showNotification("Signal rejected.");
      await loadAllData();
    } catch (err) {
      showNotification("Failed to reject signal.");
    }
  };

  const handleClosePosition = async (id: number) => {
    try {
      const res = await closePosition(id);
      showNotification(res.message || "Position closed successfully.");
      await loadAllData();
    } catch (err: any) {
      showNotification(`Close failed: ${err.message}`);
    }
  };

  const handleOpenPreMarket = async () => {
    setIsPreMarketOpen(true);
    setIsPreMarketLoading(true);
    try {
      const analysis = await runPreMarketAnalysis();
      setPreMarketData(analysis);
    } catch (err) {
      showNotification("Failed to generate pre-market report.");
    } finally {
      setIsPreMarketLoading(false);
    }
  };

  const handleEmergencyStopConfirm = async (reason: string) => {
    setIsEmergencyLoading(true);
    try {
      const res = await triggerEmergencyStop(reason);
      showNotification(`EMERGENCY STOP TRIGGERED: Liquidated ${res.positions_closed} positions.`);
      setIsEmergencyStopOpen(false);
      await loadAllData();
    } catch (err) {
      showNotification("Failed to trigger emergency stop.");
    } finally {
      setIsEmergencyLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090c10]">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 bg-blue-600 text-white px-4 py-2.5 rounded-lg shadow-xl border border-blue-400 font-semibold text-xs animate-bounce">
          {notification}
        </div>
      )}

      {/* Persistent Status & Control Header */}
      <Header
        status={status}
        onOpenPreMarket={handleOpenPreMarket}
        onOpenEmergencyStop={() => setIsEmergencyStopOpen(true)}
        onOpenDataSources={() => setIsDataQualityOpen(true)}
        onGenerateSignals={handleGenerateSignals}
        onRefreshData={handleRefreshData}
        isGeneratingSignals={isGeneratingSignals}
        isRefreshing={isRefreshing}
      />

      {/* Main Terminal Grid */}
      <main className="max-w-[1600px] w-full mx-auto p-4 flex-1 space-y-4">
        {/* Section 1: Benchmark Indices & Market Regime */}
        <MarketOverview data={marketOverview} loading={loading} />

        {/* Section 2: Global Macro Cues & GIFT Nifty Opening Projection */}
        <GlobalMarketWidget
          globalData={globalData}
          giftNifty={giftNifty}
          onUpdateManualGiftNifty={handleUpdateManualGiftNifty}
          loading={loading}
        />

        {/* Section 3: Alpha Ranking Matrix (Top 10 Overall, Longs, Shorts) */}
        <TopRankedStocks
          topOverall={topOverall}
          topLongs={topLongs}
          topShorts={topShorts}
          loading={loading}
        />

        {/* Section 4 & 5: Active Paper Positions & Strategy Signals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ActivePositions
            positions={positions}
            onClosePosition={handleClosePosition}
            loading={loading}
          />
          <LiveSignals
            signals={signals}
            onApprove={handleApproveSignal}
            onReject={handleRejectSignal}
            loading={loading}
          />
        </div>

        {/* Section 6: News Intelligence & Corporate Disclosures */}
        <NewsIntelligence news={news} loading={loading} />

        {/* Section 7: Quantitative Performance Scorecard */}
        <PerformanceMetrics metrics={performance} loading={loading} />

        {/* Section 8: Mobile Signals & Telegram Bot Dispatcher */}
        <MobileNotificationCard />

        {/* Section 9: Trade Journal & Historical Execution Trail */}
        <TradeJournal trades={trades} loading={loading} />
      </main>

      {/* Pre-Market Intelligence Report Modal */}
      <PreMarketModal
        isOpen={isPreMarketOpen}
        onClose={() => setIsPreMarketOpen(false)}
        data={preMarketData}
        loading={isPreMarketLoading}
      />

      {/* Data Quality & Provenance Inspector Modal */}
      <DataQualityModal
        isOpen={isDataQualityOpen}
        onClose={() => setIsDataQualityOpen(false)}
        data={dataQuality}
        loading={loading}
      />

      {/* Emergency Stop Kill Switch Modal */}
      <EmergencyStopModal
        isOpen={isEmergencyStopOpen}
        onClose={() => setIsEmergencyStopOpen(false)}
        onConfirm={handleEmergencyStopConfirm}
        loading={isEmergencyLoading}
      />

      {/* Terminal Footer */}
      <footer className="border-t border-[#1e2638] bg-[#090c10] py-3 text-center text-gray-500 text-[11px]">
        <div className="max-w-[1600px] mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            AI Intraday Trading Agent India &bull; Phase 2: Real Market Data & Pre-Market Intelligence Platform
          </span>
          <span className="text-amber-500/80 font-medium">
            Strict Paper Mode &bull; Real capital orders disabled &bull; No profit guarantees
          </span>
        </div>
      </footer>
    </div>
  );
}
