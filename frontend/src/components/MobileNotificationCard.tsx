"use client";

import React, { useState, useEffect } from "react";
import {
  Bell,
  Send,
  CheckCircle2,
  AlertTriangle,
  Smartphone,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Sliders,
  Radio
} from "lucide-react";
import {
  fetchNotificationStatus,
  fetchRecentAlerts,
  configureTelegram,
  sendTestNotification
} from "@/lib/api";

interface NotificationStatus {
  service: string;
  telegram_configured: boolean;
  bot_token_set: boolean;
  chat_id_set: boolean;
  chat_id: string;
  total_alerts_dispatched: number;
  recent_alerts_count: number;
  setup_instructions?: {
    step_1: string;
    step_2: string;
    step_3: string;
    step_4: string;
  };
}

interface AlertItem {
  id: string;
  timestamp: string;
  type: string;
  title: string;
  symbol?: string;
  message: string;
  sent_to_telegram: boolean;
}

export const MobileNotificationCard: React.FC = () => {
  const [status, setStatus] = useState<NotificationStatus | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [showConfig, setShowConfig] = useState<boolean>(false);

  // Form state
  const [botToken, setBotToken] = useState<string>("");
  const [chatId, setChatId] = useState<string>("");
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: "success" | "error" | "info" } | null>(null);

  const loadData = async () => {
    try {
      const [statusRes, alertsRes] = await Promise.allSettled([
        fetchNotificationStatus(),
        fetchRecentAlerts(20)
      ]);
      if (statusRes.status === "fulfilled") {
        setStatus(statusRes.value);
        if (statusRes.value.chat_id) {
          setChatId(statusRes.value.chat_id);
        }
      }
      if (alertsRes.status === "fulfilled") {
        setAlerts(alertsRes.value.alerts || []);
      }
    } catch (err) {
      console.error("Failed to load notification status", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!botToken.trim() || !chatId.trim()) {
      setStatusMsg({ text: "Please enter both Bot Token and Chat ID.", type: "error" });
      return;
    }
    setIsSaving(true);
    setStatusMsg(null);
    try {
      const res = await configureTelegram(botToken.trim(), chatId.trim(), true);
      if (res.status === "connected") {
        setStatusMsg({ text: `Connected successfully to @${res.bot_name || "Bot"}!`, type: "success" });
        setBotToken(""); // Clear secret from form
        setShowConfig(false);
      } else {
        setStatusMsg({ text: res.message || "Saved, but connection verification failed.", type: "error" });
      }
      await loadData();
    } catch (err: any) {
      setStatusMsg({ text: err.message || "Failed to configure Telegram bot.", type: "error" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSendTest = async () => {
    setIsTesting(true);
    setStatusMsg(null);
    try {
      const res = await sendTestNotification("Testing connection from your AI Intraday Trading Terminal! Real-time alerts are live.");
      if (res.sent_to_telegram) {
        setStatusMsg({ text: "Test alert delivered to your Telegram phone app!", type: "success" });
      } else {
        setStatusMsg({ text: `Alert recorded locally: ${res.message || "Telegram not connected"}`, type: "info" });
      }
      await loadData();
    } catch (err: any) {
      setStatusMsg({ text: err.message || "Failed to trigger test alert.", type: "error" });
    } finally {
      setIsTesting(false);
    }
  };

  const getBadgeColor = (type: string) => {
    switch (type) {
      case "SIGNAL":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "ORDER_FILLED":
        return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "BREAKEVEN":
        return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "POSITION_CLOSED":
        return "bg-purple-500/20 text-purple-400 border-purple-500/30";
      case "EMERGENCY_STOP":
        return "bg-rose-500/20 text-rose-400 border-rose-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  return (
    <div className="bg-[#121721] border border-[#1e2638] rounded-xl p-5 shadow-lg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-[#1e2638] pb-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <Smartphone className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white tracking-wide">
                Telegram Mobile Signal Bot
              </h2>
              {status?.telegram_configured ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  <CheckCircle2 className="h-3 w-3" /> Connected
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  <Radio className="h-3 w-3" /> Ready to Pair
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Instant mobile trade signals, auto-breakeven locking & emergency stop alerts sent directly to your phone.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#1a2233] text-gray-300 hover:text-white hover:bg-[#222d44] border border-[#2a3650] transition-colors"
          >
            <Sliders className="h-3.5 w-3.5" />
            {showConfig ? "Hide Config" : "Bot Settings"}
          </button>
          <button
            onClick={handleSendTest}
            disabled={isTesting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-md disabled:opacity-50 transition-colors"
          >
            <Send className="h-3.5 w-3.5" />
            {isTesting ? "Sending..." : "Ping Phone"}
          </button>
        </div>
      </div>

      {/* Status banner */}
      {statusMsg && (
        <div
          className={`mt-3 p-3 rounded-lg text-xs flex items-center justify-between border ${
            statusMsg.type === "success"
              ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
              : statusMsg.type === "error"
              ? "bg-rose-950/40 border-rose-500/40 text-rose-300"
              : "bg-sky-950/40 border-sky-500/40 text-sky-300"
          }`}
        >
          <span>{statusMsg.text}</span>
          <button onClick={() => setStatusMsg(null)} className="text-gray-400 hover:text-white font-bold ml-2">
            ✕
          </button>
        </div>
      )}

      {/* Bot Configuration Panel */}
      {showConfig && (
        <form onSubmit={handleSaveConfig} className="mt-4 p-4 rounded-lg bg-[#090c10] border border-[#1e2638] space-y-3">
          <div className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-sky-400" />
            Quick Telegram Bot Setup (Takes 30 seconds)
          </div>

          <div className="text-[11px] text-gray-400 bg-[#121721] p-2.5 rounded border border-[#1e2638] space-y-1">
            <p>1. Open Telegram and search for <strong>@BotFather</strong></p>
            <p>2. Send <code className="bg-[#090c10] px-1 py-0.5 rounded text-sky-300">/newbot</code>, choose a name and username to receive your <strong>HTTP API Bot Token</strong></p>
            <p>3. Search for <strong>@userinfobot</strong> or send any message to your new bot, then find your numeric <strong>Chat ID</strong></p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div>
              <label className="block text-[11px] font-semibold text-gray-300 mb-1">
                Telegram Bot Token
              </label>
              <input
                type="password"
                value={botToken}
                onChange={(e) => setBotToken(e.target.value)}
                placeholder={status?.bot_token_set ? "••••••••••••••••••••••••••••••••" : "e.g. 123456789:ABCdefGhIJKlmNoPQRstuVWXyz"}
                className="w-full bg-[#121721] border border-[#2a3650] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-gray-300 mb-1">
                Your Telegram Chat ID
              </label>
              <input
                type="text"
                value={chatId}
                onChange={(e) => setChatId(e.target.value)}
                placeholder="e.g. 987654321"
                className="w-full bg-[#121721] border border-[#2a3650] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowConfig(false)}
              className="px-3 py-1.5 text-xs rounded text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-4 py-1.5 text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white rounded shadow disabled:opacity-50"
            >
              {isSaving ? "Saving & Testing..." : "Save & Verify Connection"}
            </button>
          </div>
        </form>
      )}

      {/* Live Dispatched Alerts Feed */}
      <div className="mt-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
            <Bell className="h-3.5 w-3.5 text-sky-400" />
            Recent Dispatched Trade Alerts ({alerts.length})
          </span>
          <button
            onClick={loadData}
            className="text-[11px] text-gray-400 hover:text-white flex items-center gap-1"
          >
            <RefreshCw className="h-3 w-3" /> Refresh
          </button>
        </div>

        {alerts.length === 0 ? (
          <div className="text-center py-6 text-xs text-gray-500 bg-[#090c10] rounded-lg border border-[#1e2638]">
            No mobile notifications dispatched yet. Use "Ping Phone" above to test or wait for strategy buy/sell triggers.
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="p-3 bg-[#090c10] border border-[#1e2638] rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getBadgeColor(alert.type)}`}>
                      {alert.type}
                    </span>
                    {alert.symbol && (
                      <span className="font-bold text-white font-mono">{alert.symbol}</span>
                    )}
                    <span className="text-gray-200 font-semibold">{alert.title}</span>
                  </div>
                  <p className="text-gray-400 text-[11px] whitespace-pre-wrap">{alert.message}</p>
                </div>
                <div className="flex sm:flex-col items-center sm:items-end justify-between text-[10px] text-gray-500 shrink-0">
                  <span>{new Date(alert.timestamp).toLocaleTimeString("en-IN")}</span>
                  {alert.sent_to_telegram ? (
                    <span className="text-emerald-400 flex items-center gap-1 mt-0.5">
                      ✓ Sent to Telegram
                    </span>
                  ) : (
                    <span className="text-gray-400 mt-0.5">Local Log</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
