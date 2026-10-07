"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import {
  fetchDataHealthReport,
  testProviderConnection,
  uploadHistoricalDataset,
  fetchMarketCalendar,
  fetchCorporateAnnouncements,
  fetchSystemStatus
} from "@/lib/api";
import { ProviderHealthReport, CorporateAnnouncementItem, SystemStatus } from "@/types";
import { formatPercent } from "@/lib/utils";
import {
  HeartPulse,
  Database,
  ShieldCheck,
  Upload,
  Calendar,
  FileCheck,
  RefreshCw,
  Zap,
  Globe,
  Radio,
  Tag
} from "lucide-react";

export default function DataHealthPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [healthReport, setHealthReport] = useState<ProviderHealthReport | null>(null);
  const [calendar, setCalendar] = useState<any>(null);
  const [announcements, setAnnouncements] = useState<CorporateAnnouncementItem[]>([]);
  const [loading, setLoading] = useState(true);

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [symbol, setSymbol] = useState("RELIANCE");
  const [timeframe, setTimeframe] = useState("5m");
  const [corporateAdjusted, setCorporateAdjusted] = useState(true);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  const loadData = async () => {
    try {
      const [sysStatus, health, cal, ann] = await Promise.all([
        fetchSystemStatus(),
        fetchDataHealthReport(),
        fetchMarketCalendar(),
        fetchCorporateAnnouncements(10)
      ]);
      setStatus(sysStatus);
      setHealthReport(health);
      setCalendar(cal);
      setAnnouncements(ann);
    } catch (err) {
      console.error("Failed to load data health:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleTestConnection = async (provider: string) => {
    try {
      const res = await testProviderConnection(provider);
      showNotification(`Tested ${provider}: Status is ${res.status} (${res.connected ? "Connected" : "Not Connected"})`);
      await loadData();
    } catch (err) {
      showNotification("Connection test failed.");
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      showNotification("Please select a CSV or Parquet file to upload.");
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("symbol", symbol);
    formData.append("timeframe", timeframe);
    formData.append("corporate_action_adjusted", String(corporateAdjusted));

    try {
      const res = await uploadHistoricalDataset(formData);
      setUploadResult(res);
      showNotification(`Dataset ${res.dataset_name} imported successfully! Total candles: ${res.total_candles}`);
      setSelectedFile(null);
    } catch (err: any) {
      showNotification(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090c10]">
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 bg-emerald-600 text-white px-4 py-2.5 rounded-lg shadow-xl border border-emerald-400 font-semibold text-xs animate-bounce">
          {notification}
        </div>
      )}

      {/* Header */}
      <Header status={status} />

      <main className="max-w-[1600px] w-full mx-auto p-4 flex-1 space-y-4">
        {/* Top Disclaimer Banner */}
        <div className="bg-emerald-950/30 border border-emerald-800/40 rounded-xl p-3.5 flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
              <HeartPulse className="h-5 w-5" />
            </div>
            <div>
              <span className="font-bold text-white block uppercase text-xs">
                Real Market Data Provenance, Historical Importer & Health Inspector
              </span>
              <span className="text-[11px] text-gray-300">
                Audits connection states, latency, timestamps, and statutory exchange calendars. Never falsely claims LIVE status.
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase">
              STATUS AUDITING ACTIVE
            </span>
          </div>
        </div>

        {/* SECTION 1: LIVE CONNECTION HEALTH MATRIX */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
          <div className="flex items-center justify-between mb-3 border-b border-[#1e2638] pb-3">
            <div className="flex items-center gap-2">
              <Radio className="h-4 w-4 text-emerald-400" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
                Data Providers & Connector Diagnostics
              </h2>
            </div>
            <button
              onClick={loadData}
              className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1"
            >
              <RefreshCw className="h-3 w-3" /> Re-Check Handshakes
            </button>
          </div>

          {loading || !healthReport ? (
            <div className="text-center py-8 text-gray-400 animate-pulse">
              Auditing data connectors...
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
              {/* Card 1: Market Data Adapter */}
              <div className="bg-[#090c10] border border-[#1e2638] p-3.5 rounded-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white uppercase text-[11px] flex items-center gap-1.5">
                      <Database className="h-3.5 w-3.5 text-blue-400" /> Market Data Feed
                    </span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.2 rounded border ${
                        healthReport.market_data.status === "LIVE"
                          ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                          : healthReport.market_data.status === "MOCK"
                          ? "text-amber-400 bg-amber-500/10 border-amber-500/30"
                          : "text-rose-400 bg-rose-500/10 border-rose-500/30"
                      }`}
                    >
                      {healthReport.market_data.status}
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px]">Provider: <strong>{healthReport.market_data.provider}</strong></p>
                  <p className="text-gray-400 text-[10px] mt-1">
                    {healthReport.market_data.note || healthReport.market_data.error || "Adapter active."}
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-gray-800 flex justify-between items-center text-[10px]">
                  <span className="text-gray-400">Latency: {healthReport.market_data.latency_ms}ms</span>
                  <button
                    onClick={() => handleTestConnection("zerodha")}
                    className="text-blue-400 hover:text-blue-300 font-semibold"
                  >
                    Test Ping
                  </button>
                </div>
              </div>

              {/* Card 2: Official Corporate Announcements */}
              <div className="bg-[#090c10] border border-[#1e2638] p-3.5 rounded-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white uppercase text-[11px] flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" /> Exchange Disclosures
                    </span>
                    <span className="text-[9px] font-bold px-1.5 py-0.2 rounded border text-emerald-400 bg-emerald-500/10 border-emerald-500/30">
                      {healthReport.corporate_announcements.status}
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px]">Source: <strong>{healthReport.corporate_announcements.provider}</strong></p>
                  <p className="text-gray-400 text-[10px] mt-1">
                    Level-1 verified corporate announcements, board meetings & results.
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-gray-800 text-[10px] text-gray-400">
                  Latency: {healthReport.corporate_announcements.latency_ms}ms
                </div>
              </div>

              {/* Card 3: Global Macro Feed */}
              <div className="bg-[#090c10] border border-[#1e2638] p-3.5 rounded-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white uppercase text-[11px] flex items-center gap-1.5">
                      <Globe className="h-3.5 w-3.5 text-cyan-400" /> Global Macro Cues
                    </span>
                    <span className="text-[9px] font-bold px-1.5 py-0.2 rounded border text-emerald-400 bg-emerald-500/10 border-emerald-500/30">
                      {healthReport.global_markets.status}
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px]">US, Asia, Brent & DXY Feed</p>
                  <p className="text-gray-400 text-[10px] mt-1">
                    Score: <strong className="text-white">{healthReport.global_markets.score > 0 ? `+${healthReport.global_markets.score}` : healthReport.global_markets.score}/100</strong>
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-gray-800 text-[10px] text-gray-400">
                  Data Age: {healthReport.global_markets.data_age_seconds}s | Latency: {healthReport.global_markets.latency_ms}ms
                </div>
              </div>

              {/* Card 4: GIFT Nifty Opening Gap */}
              <div className="bg-[#090c10] border border-[#1e2638] p-3.5 rounded-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white uppercase text-[11px] flex items-center gap-1.5">
                      <Zap className="h-3.5 w-3.5 text-amber-400" /> GIFT NIFTY (NSE IX)
                    </span>
                    <span className="text-[9px] font-bold px-1.5 py-0.2 rounded border text-amber-400 bg-amber-500/10 border-amber-500/30">
                      {healthReport.gift_nifty.status}
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px]">Feed: <strong>{healthReport.gift_nifty.provider}</strong></p>
                  <p className="text-gray-400 text-[10px] mt-1">
                    Gap: <strong className="text-white">{healthReport.gift_nifty.gap_points > 0 ? `+${healthReport.gift_nifty.gap_points.toFixed(2)}` : healthReport.gift_nifty.gap_points.toFixed(2)} pts</strong> ({formatPercent(healthReport.gift_nifty.gap_pct)})
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-gray-800 text-[10px] text-gray-400">
                  Latency: {healthReport.gift_nifty.latency_ms}ms
                </div>
              </div>

              {/* Card 5: News Intelligence Feed */}
              <div className="bg-[#090c10] border border-[#1e2638] p-3.5 rounded-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white uppercase text-[11px] flex items-center gap-1.5">
                      <Radio className="h-3.5 w-3.5 text-purple-400" /> News Intelligence
                    </span>
                    <span className="text-[9px] font-bold px-1.5 py-0.2 rounded border text-emerald-400 bg-emerald-500/10 border-emerald-500/30">
                      {healthReport.news.status}
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px]">Feed: <strong>{healthReport.news.provider}</strong></p>
                  <p className="text-gray-400 text-[10px] mt-1">{healthReport.news.quality}</p>
                </div>
                <div className="mt-3 pt-2 border-t border-gray-800 text-[10px] text-gray-400">
                  Age: {healthReport.news.data_age_seconds}s | Latency: {healthReport.news.latency_ms}ms
                </div>
              </div>

              {/* Card 6: Market Calendar */}
              <div className="bg-[#090c10] border border-[#1e2638] p-3.5 rounded-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white uppercase text-[11px] flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-pink-400" /> NSE/BSE Calendar
                    </span>
                    <span className="text-[9px] font-bold px-1.5 py-0.2 rounded border text-emerald-400 bg-emerald-500/10 border-emerald-500/30">
                      {healthReport.market_calendar.status}
                    </span>
                  </div>
                  <p className="text-gray-300 text-[11px]">
                    Trading Day: <strong className={healthReport.market_calendar.is_trading_day ? "text-emerald-400" : "text-rose-400"}>
                      {healthReport.market_calendar.is_trading_day ? "YES" : "NO"}
                    </strong>
                  </p>
                  <p className="text-gray-400 text-[10px] mt-1">{healthReport.market_calendar.regular_market_hours}</p>
                </div>
                <div className="mt-3 pt-2 border-t border-gray-800 text-[10px] text-gray-400">
                  {healthReport.market_calendar.current_time_ist}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* SECTION 2 & 3: HISTORICAL DATA IMPORTER & EXCHANGE CALENDAR */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Uploader Form */}
          <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Upload className="h-4 w-4 text-emerald-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-200">
                  Historical Market Dataset Importer (CSV / Parquet)
                </h3>
              </div>

              <form onSubmit={handleFileUpload} className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Symbol</label>
                    <input
                      type="text"
                      value={symbol}
                      onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                      className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-white w-full font-mono text-xs focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Timeframe</label>
                    <select
                      value={timeframe}
                      onChange={(e) => setTimeframe(e.target.value)}
                      className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-white w-full font-mono text-xs focus:outline-none"
                    >
                      <option value="1m">1-Minute</option>
                      <option value="5m">5-Minute</option>
                      <option value="15m">15-Minute</option>
                      <option value="1d">Daily</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-gray-400 block text-[10px] uppercase font-semibold mb-1">Upload File (.csv, .parquet)</label>
                  <input
                    type="file"
                    accept=".csv,.parquet"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="bg-[#090c10] border border-gray-700 rounded px-2.5 py-1.5 text-gray-300 w-full text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-gray-800 file:text-gray-300"
                  />
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="corpAdj"
                    checked={corporateAdjusted}
                    onChange={(e) => setCorporateAdjusted(e.target.checked)}
                    className="rounded bg-gray-800 border-gray-700 text-emerald-500"
                  />
                  <label htmlFor="corpAdj" className="text-gray-300 text-[11px]">
                    Validate Corporate Actions (Split / Bonus Adjusted)
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={isUploading || !selectedFile}
                  className="w-full mt-2 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  <FileCheck className="h-4 w-4" />
                  {isUploading ? "Validating & Ingesting..." : "Validate & Import Dataset"}
                </button>
              </form>
            </div>

            {uploadResult && (
              <div className="mt-3 p-3 bg-[#090c10] border border-emerald-500/40 rounded-lg text-xs space-y-1">
                <span className="font-bold text-emerald-400 block uppercase text-[10px]">
                  Validation Scorecard: {uploadResult.validation_status}
                </span>
                <div className="text-gray-300 text-[11px] grid grid-cols-2 gap-1">
                  <span>Candles: <strong className="text-white font-mono">{uploadResult.total_candles}</strong></span>
                  <span>Duplicates Dropped: <strong className="text-white font-mono">{uploadResult.duplicate_candles_dropped}</strong></span>
                  <span>Anomalies: <strong className="text-white font-mono">{uploadResult.extreme_anomalies_detected}</strong></span>
                  <span>Rating: <strong className="text-emerald-400 font-mono">{uploadResult.quality_rating}</strong></span>
                </div>
              </div>
            )}
          </div>

          {/* NSE/BSE 2026 Exchange Holiday Calendar */}
          <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Calendar className="h-4 w-4 text-pink-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-200">
                  NSE / BSE Official 2026 Exchange Holidays
                </h3>
              </div>

              <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                {calendar?.upcoming_holidays?.map((h: any, idx: number) => (
                  <div
                    key={idx}
                    className="bg-[#090c10] border border-[#1e2638] p-2 rounded-lg flex items-center justify-between text-xs"
                  >
                    <span className="font-mono text-gray-300 font-bold">{h.date}</span>
                    <span className="text-pink-300 font-semibold">{h.holiday}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-gray-800 text-[10px] text-gray-400">
              Automatic trading signal generation is disabled on exchange holidays.
            </div>
          </div>
        </div>

        {/* SECTION 4: OFFICIAL CORPORATE DISCLOSURES FEED */}
        <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-4">
          <div className="flex items-center justify-between mb-3 border-b border-[#1e2638] pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-gray-200">
                Official Level-1 Corporate Filings & Exchange Announcements
              </h3>
            </div>
            <span className="text-[11px] text-gray-400">Source: NSE / BSE Disclosures</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {announcements.map((a) => (
              <div key={a.id} className="bg-[#090c10] border border-[#1e2638] p-3 rounded-lg hover:border-gray-700 transition-colors">
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-white font-mono">{a.symbol}</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40">
                      {a.reliability}
                    </span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-gray-800 text-gray-300 flex items-center gap-0.5">
                      <Tag className="h-2.5 w-2.5 text-blue-400" /> {a.category}
                    </span>
                  </div>
                  <span className="text-[10px] text-gray-500 font-mono">
                    {new Date(a.published_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
                <p className="font-semibold text-gray-200 leading-snug mb-1 text-[11px]">{a.headline}</p>
                <p className="text-gray-400 text-[10px]">{a.details}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
