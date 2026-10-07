"use client";
import React, { useState, useEffect, useCallback, Component } from "react";

// Safe API base URL resolver (127.0.0.1 is immune to Windows IPv6 loopback issues)
const getApiUrl = () => {
  if (typeof window !== "undefined" && window.location.hostname) {
    return `http://${window.location.hostname}:8000/api/live`;
  }
  return "http://127.0.0.1:8000/api/live";
};

const fmtNum = (v: any, d = 2) => {
  const n = Number(v);
  return !isNaN(n) && isFinite(n) ? n.toFixed(d) : (0).toFixed(d);
};

// ─── Component Level Error Boundary ──────────────────────────────────────────
interface PanelErrorBoundaryProps {
  title: string;
  children: React.ReactNode;
}
interface PanelErrorBoundaryState {
  hasError: boolean;
}

class PanelErrorBoundary extends Component<PanelErrorBoundaryProps, PanelErrorBoundaryState> {
  constructor(props: PanelErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: any) {
    console.error(`Error in ${this.props.title}:`, error);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="border border-red-900 bg-red-950/30 rounded p-4 text-xs text-red-300 font-mono">
          <p className="font-bold mb-1">⚠ {this.props.title} temporarily unavailable</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-2 px-2 py-1 bg-red-800 text-white rounded text-[11px]"
          >
            Retry Panel
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ─── Types ────────────────────────────────────────────────────────────────────

interface DataGate {
  status?: string;
  can_generate_signals?: boolean;
  reason?: string;
  data_age_seconds?: number;
}

interface KillSwitchStatus {
  current_level?: number;
  level_name?: string;
  is_active?: boolean;
  restrictions?: string[];
  can_generate_signals?: boolean;
  can_open_new_positions?: boolean;
  manual_reset_required?: boolean;
}

interface RealityGap {
  verdict?: string;
  paper_trades?: number;
  live_win_rate?: number;
  is_sufficient_data?: boolean;
  threshold_breaches?: string[];
}

interface Portfolio {
  open_positions_count?: number;
  today_realized_pnl?: number;
  today_unrealized_pnl?: number;
  today_total_pnl?: number;
  daily_loss_remaining?: number;
  is_kill_switch_triggered?: boolean;
}

interface AutoApproveStatus {
  enabled?: boolean;
  is_active?: boolean;
  expiry?: string | null;
}

interface MarketKnowledge {
  total_trades_analyzed?: number;
  winning_trades?: number;
  losing_trades?: number;
  overall_win_rate_pct?: number;
  best_symbols?: string[];
  caution_symbols?: string[];
  recommended_sl_pct?: number;
  recommended_tp_pct?: number;
  current_sl_multiplier?: number;
  current_tp_multiplier?: number;
  insights?: string[];
  last_updated?: string | null;
  learning_status?: string;
}

interface Signal {
  id: number;
  symbol: string;
  direction: string;
  entry_price?: number;
  stop_loss?: number;
  target_price?: number;
  quantity?: number;
  risk_reward_ratio?: number;
  strategy_score?: number;
  reason?: string;
  market_regime?: string;
  status?: string;
}

interface Position {
  id?: number;
  symbol: string;
  side: string;
  quantity?: number;
  entry_price?: number;
  current_price?: number;
  stop_loss?: number;
  target_price?: number;
  unrealized_pnl?: number | null;
  unrealized_pnl_pct?: number | null;
  status?: string;
  slippage_incurred?: number | null;
  statutory_charges?: number | null;
}

interface AuditEvent {
  id?: number;
  event_type?: string;
  symbol?: string;
  details?: string;
  timestamp?: string;
}

// ─── Data Quality Banner ──────────────────────────────────────────────────────

function DataQualityBanner({ gate }: { gate: DataGate | null }) {
  if (!gate) return null;
  const isLive = gate.status === "LIVE";
  const color = isLive ? "border-green-500 bg-green-900/30" : "border-red-500 bg-red-900/30";
  const textColor = isLive ? "text-green-400" : "text-red-400";
  return (
    <div className={`border rounded p-3 mb-4 ${color}`}>
      <div className="flex items-center justify-between">
        <div>
          <span className={`font-mono font-bold text-lg ${textColor}`}>
            DATA: {gate.status || "UNKNOWN"}
          </span>
          {gate.data_age_seconds !== undefined && (
            <span className="ml-3 text-gray-400 text-sm">Age: {fmtNum(gate.data_age_seconds, 1)}s</span>
          )}
        </div>
        <span className={`text-sm px-3 py-1 rounded border ${color} ${textColor}`}>
          SIGNALS: {gate.can_generate_signals ? "ENABLED ✓" : "BLOCKED ✗"}
        </span>
      </div>
      {!isLive && gate.reason && (
        <p className="mt-1 text-sm text-red-300 font-mono">{gate.reason}</p>
      )}
    </div>
  );
}

// ─── Kill Switch Panel ─────────────────────────────────────────────────────────

function KillSwitchPanel({ ks, onActivate, onReset }: {
  ks: KillSwitchStatus | null;
  onActivate: (level: number) => void;
  onReset: () => void;
}) {
  const levels = [
    { n: 1, label: "L1 PAUSE SIGNALS", color: "bg-yellow-700 hover:bg-yellow-600" },
    { n: 2, label: "L2 NO NEW ENTRIES", color: "bg-orange-700 hover:bg-orange-600" },
    { n: 3, label: "L3 EMERGENCY STOP", color: "bg-red-700 hover:bg-red-600" },
    { n: 4, label: "L4 FREEZE ALL", color: "bg-red-900 hover:bg-red-800" },
    { n: 5, label: "L5 FULL HALT", color: "bg-purple-900 hover:bg-purple-800" },
  ];
  return (
    <div className="border border-gray-700 rounded p-4">
      <h3 className="text-yellow-400 font-mono font-bold mb-3">
        ⚡ KILL SWITCH — Level {ks?.current_level ?? 0}/5
        {ks?.is_active && <span className="ml-2 text-red-400 animate-pulse">● ACTIVE</span>}
      </h3>
      <div className="grid grid-cols-5 gap-2 mb-3">
        {levels.map(({ n, label, color }) => (
          <button
            key={n}
            onClick={() => onActivate(n)}
            className={`text-xs font-mono p-2 rounded ${color} text-white transition-colors`}
          >
            {label}
          </button>
        ))}
      </div>
      {ks?.is_active && (
        <div className="mb-2">
          <p className="text-xs text-red-300 font-mono">
            Restrictions: {Array.isArray(ks?.restrictions) && ks.restrictions.length > 0 ? ks.restrictions.join(" | ") : "Active"}
          </p>
          {ks.manual_reset_required && (
            <p className="text-xs text-purple-300 font-mono mt-1">⚠ Level 5 — Manual reset required</p>
          )}
        </div>
      )}
      <button
        onClick={onReset}
        className="text-xs font-mono px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white transition-colors"
      >
        RESET KILL SWITCH
      </button>
    </div>
  );
}

// ─── Pending Signals Panel ─────────────────────────────────────────────────────

function PendingSignalsPanel({ signals, autoApprove, onApprove, onReject }: {
  signals: Signal[];
  autoApprove?: AutoApproveStatus | null;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
}) {
  const safeSignals = Array.isArray(signals) ? signals : [];
  const pending = safeSignals.filter(s => s && s.status === "PENDING");
  return (
    <div className="border border-gray-700 rounded p-4">
      <h3 className="text-blue-400 font-mono font-bold mb-3 flex items-center justify-between">
        <div>
          📡 PENDING SIGNALS ({pending.length})
          {autoApprove?.is_active ? (
            <span className="ml-2 text-xs text-green-400 bg-green-950/60 border border-green-700 px-2 py-0.5 rounded">
              ⚡ AUTO-APPROVE ACTIVE (Bypassing Human Approval)
            </span>
          ) : (
            <span className="ml-2 text-xs text-yellow-400">— Human approval required</span>
          )}
        </div>
      </h3>
      {pending.length === 0 ? (
        <p className="text-gray-500 text-sm font-mono">No pending signals.</p>
      ) : (
        <div className="space-y-2">
          {pending.map((sig, idx) => (
            <div key={sig.id ?? idx} className="border border-blue-900 rounded p-3 bg-blue-950/20">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className={`font-mono font-bold ${sig.direction === "BUY" ? "text-green-400" : "text-red-400"}`}>
                    {sig.direction} {sig.symbol}
                  </span>
                  <span className="ml-2 text-gray-400 text-xs">#{sig.id} | Score: {fmtNum(sig.strategy_score, 1)}</span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onApprove(sig.id)}
                    className="text-xs px-3 py-1 bg-green-800 hover:bg-green-700 rounded text-white font-mono"
                  >
                    ✓ APPROVE
                  </button>
                  <button
                    onClick={() => onReject(sig.id)}
                    className="text-xs px-3 py-1 bg-red-900 hover:bg-red-800 rounded text-white font-mono"
                  >
                    ✗ REJECT
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-2 text-xs font-mono text-gray-300">
                <span>Entry: ₹{fmtNum(sig.entry_price)}</span>
                <span>SL: ₹{fmtNum(sig.stop_loss)}</span>
                <span>TP: ₹{fmtNum(sig.target_price)}</span>
                <span>RR: {fmtNum(sig.risk_reward_ratio, 1)}x</span>
              </div>
              {sig.reason && (
                <p className="text-xs text-gray-500 mt-1 font-mono">{sig.reason}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Open Positions Panel ──────────────────────────────────────────────────────

function OpenPositionsPanel({ positions }: { positions: Position[] }) {
  const safePositions = Array.isArray(positions) ? positions : [];
  const open = safePositions.filter(p => p && p.status === "OPEN");
  return (
    <div className="border border-gray-700 rounded p-4">
      <h3 className="text-green-400 font-mono font-bold mb-3">
        📊 OPEN POSITIONS ({open.length})
        <span className="ml-2 text-xs text-gray-400">PAPER ONLY</span>
      </h3>
      {open.length === 0 ? (
        <p className="text-gray-500 text-sm font-mono">No open positions.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="text-left py-1">Symbol</th>
                <th className="text-left">Side</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Entry</th>
                <th className="text-right">Current</th>
                <th className="text-right">SL</th>
                <th className="text-right">TP</th>
                <th className="text-right">Unreal P&L</th>
              </tr>
            </thead>
            <tbody>
              {open.map((pos, idx) => (
                <tr key={pos.id ?? idx} className="border-b border-gray-800">
                  <td className="py-1 text-white font-bold">{pos.symbol}</td>
                  <td className={pos.side === "BUY" ? "text-green-400 font-bold" : "text-red-400 font-bold"}>{pos.side}</td>
                  <td className="text-right text-gray-300">{pos.quantity ?? 0}</td>
                  <td className="text-right text-gray-300">₹{fmtNum(pos.entry_price)}</td>
                  <td className="text-right text-white">₹{fmtNum(pos.current_price)}</td>
                  <td className="text-right text-red-400">₹{fmtNum(pos.stop_loss)}</td>
                  <td className="text-right text-green-400">₹{fmtNum(pos.target_price)}</td>
                  <td className={`text-right ${(pos.unrealized_pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                    ₹{fmtNum(pos.unrealized_pnl)} ({fmtNum(pos.unrealized_pnl_pct)}%)
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Reality Gap Panel ────────────────────────────────────────────────────────

function RealityGapPanel({ rg }: { rg: RealityGap | null }) {
  if (!rg) return null;
  const verdictColor: Record<string, string> = {
    INSUFFICIENT_LIVE_DATA: "text-gray-400",
    CONTINUE_PAPER_TRADING: "text-blue-400",
    REALITY_GAP_DETECTED: "text-yellow-400",
    STRATEGY_DEGRADATION_DETECTED: "text-orange-400",
    PAPER_VALIDATION_PASSED: "text-green-400",
  };
  const color = verdictColor[rg.verdict || ""] || "text-gray-400";
  return (
    <div className="border border-gray-700 rounded p-4">
      <h3 className="text-purple-400 font-mono font-bold mb-3">📉 REALITY-GAP ANALYSIS</h3>
      <div className={`text-lg font-mono font-bold mb-2 ${color}`}>{rg.verdict || "ANALYZING..."}</div>
      <div className="grid grid-cols-3 gap-2 text-xs font-mono text-gray-300 mb-2">
        <span>Paper Trades: {rg.paper_trades ?? 0}</span>
        <span>Live Win Rate: {fmtNum(rg.live_win_rate, 1)}%</span>
        <span>Sufficient: {rg.is_sufficient_data ? "✅" : "❌ Need 30+"}</span>
      </div>
      {Array.isArray(rg?.threshold_breaches) && rg.threshold_breaches.length > 0 && (
        <div className="mt-2">
          <p className="text-xs text-yellow-400 font-mono mb-1">Threshold Breaches:</p>
          {rg.threshold_breaches.map((b, i) => (
            <p key={i} className="text-xs text-orange-300 font-mono">⚠ {String(b)}</p>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Portfolio Summary Panel ───────────────────────────────────────────────────

function PortfolioPanel({ portfolio }: { portfolio: Portfolio | null }) {
  if (!portfolio) return null;
  const pnl = portfolio.today_total_pnl ?? 0;
  return (
    <div className="border border-gray-700 rounded p-4">
      <h3 className="text-cyan-400 font-mono font-bold mb-3">💼 PAPER PORTFOLIO (Today)</h3>
      <div className="grid grid-cols-3 gap-4 text-sm font-mono">
        <div>
          <p className="text-gray-400 text-xs">Total P&L</p>
          <p className={`text-lg font-bold ${pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
            ₹{fmtNum(pnl)}
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Realized</p>
          <p className="text-white">₹{fmtNum(portfolio.today_realized_pnl)}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Unrealized</p>
          <p className="text-white">₹{fmtNum(portfolio.today_unrealized_pnl)}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Open Positions</p>
          <p className="text-white">{portfolio.open_positions_count ?? 0}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Daily Loss Remaining</p>
          <p className="text-yellow-400">₹{fmtNum(portfolio.daily_loss_remaining)}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Kill Switch</p>
          <p className={portfolio.is_kill_switch_triggered ? "text-red-400" : "text-green-400"}>
            {portfolio.is_kill_switch_triggered ? "TRIGGERED ⚠" : "CLEAR ✓"}
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── Audit Log Panel ──────────────────────────────────────────────────────────

function AuditLogPanel({ events }: { events: AuditEvent[] }) {
  const safeEvents = Array.isArray(events) ? events : [];
  return (
    <div className="border border-gray-700 rounded p-4">
      <h3 className="text-gray-400 font-mono font-bold mb-3">📋 AUDIT LOG (Last 20)</h3>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {safeEvents.length === 0 ? (
          <p className="text-gray-500 text-xs font-mono">No events yet.</p>
        ) : (
          [...safeEvents].reverse().slice(0, 20).map((ev, idx) => {
            let timeStr = "";
            try {
              timeStr = ev?.timestamp ? new Date(ev.timestamp).toLocaleTimeString("en-IN") : "";
            } catch {
              timeStr = "";
            }
            return (
              <div key={ev?.id ?? idx} className="text-xs font-mono flex gap-2">
                <span className="text-gray-500 shrink-0">{timeStr}</span>
                <span className="text-blue-400 shrink-0">[{ev?.event_type || "EVENT"}]</span>
                {ev?.symbol && <span className="text-yellow-400 shrink-0">{ev.symbol}</span>}
                <span className="text-gray-300 truncate">{ev?.details || ""}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

// ─── Market Knowledge & Adaptive Learning Panel ─────────────────────────────

function MarketKnowledgePanel({ knowledge, onTriggerLearn }: {
  knowledge: MarketKnowledge | null;
  onTriggerLearn: () => void;
}) {
  const slMult = knowledge?.current_sl_multiplier ?? (knowledge?.recommended_sl_pct ? knowledge.recommended_sl_pct * 100 : 1.5);
  const tpMult = knowledge?.current_tp_multiplier ?? (knowledge?.recommended_tp_pct ? knowledge.recommended_tp_pct * 100 : 3.0);

  return (
    <div className="border border-purple-800/60 bg-purple-950/20 rounded p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-purple-400 font-mono font-bold flex items-center gap-2">
          🧠 MARKET KNOWLEDGE & ADAPTIVE LEARNING
          <span className="text-xs bg-purple-900 border border-purple-600 px-2 py-0.5 rounded text-purple-200">
            {knowledge?.learning_status || "ACTIVE"}
          </span>
        </h3>
        <button
          onClick={onTriggerLearn}
          className="text-xs font-mono px-3 py-1 bg-purple-700 hover:bg-purple-600 rounded text-white transition-colors"
        >
          🔄 RETRAIN / LEARN NOW
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4 text-xs font-mono mb-3">
        <div>
          <span className="text-gray-400">Trades Analyzed:</span>
          <p className="text-white font-bold text-sm">{knowledge?.total_trades_analyzed ?? 0}</p>
        </div>
        <div>
          <span className="text-gray-400">Historical Win Rate:</span>
          <p className="text-green-400 font-bold text-sm">{fmtNum(knowledge?.overall_win_rate_pct, 1)}%</p>
        </div>
        <div>
          <span className="text-gray-400">SL Multiplier:</span>
          <p className="text-yellow-400 font-bold text-sm">{fmtNum(slMult, 1)}x</p>
        </div>
        <div>
          <span className="text-gray-400">TP Multiplier:</span>
          <p className="text-blue-400 font-bold text-sm">{fmtNum(tpMult, 1)}x</p>
        </div>
      </div>

      {/* Symbol Affinity */}
      <div className="flex gap-4 text-xs font-mono mb-2">
        <div>
          <span className="text-green-400 font-bold">Top Performing: </span>
          <span className="text-gray-200">
            {Array.isArray(knowledge?.best_symbols) && knowledge.best_symbols.length > 0 
              ? knowledge.best_symbols.join(", ") 
              : "None yet"}
          </span>
        </div>
        <div>
          <span className="text-orange-400 font-bold">Caution: </span>
          <span className="text-gray-200">
            {Array.isArray(knowledge?.caution_symbols) && knowledge.caution_symbols.length > 0 
              ? knowledge.caution_symbols.join(", ") 
              : "None yet"}
          </span>
        </div>
      </div>

      {/* Insights */}
      {Array.isArray(knowledge?.insights) && knowledge.insights.length > 0 && (
        <div className="mt-2 border-t border-purple-900/50 pt-2 space-y-1">
          {knowledge.insights.map((ins, i) => (
            <p key={i} className="text-xs text-purple-300 font-mono flex items-center gap-1.5">
              <span>💡</span> {String(ins)}
            </p>
          ))}
        </div>
      )}
      <p className="text-[11px] text-gray-500 font-mono mt-2">
        Last Learned: {knowledge?.last_updated || "Not yet updated"}
      </p>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function LivePaperPage() {
  const [mounted, setMounted] = useState(false);
  const [dataGate, setDataGate] = useState<DataGate | null>(null);
  const [killSwitch, setKillSwitch] = useState<KillSwitchStatus | null>(null);
  const [realityGap, setRealityGap] = useState<RealityGap | null>(null);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [autoApprove, setAutoApprove] = useState<AutoApproveStatus | null>(null);
  const [knowledge, setKnowledge] = useState<MarketKnowledge | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [lastRefresh, setLastRefresh] = useState<string>("");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchAll = useCallback(async () => {
    const api = getApiUrl();
    try {
      const [statusRes, signalsRes, positionsRes, auditRes, knowledgeRes] = await Promise.all([
        fetch(`${api}/status`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch(`${api}/signals`).then(r => r.ok ? r.json() : []).catch(() => []),
        fetch(`${api}/positions`).then(r => r.ok ? r.json() : []).catch(() => []),
        fetch(`${api}/audit?limit=20`).then(r => r.ok ? r.json() : []).catch(() => []),
        fetch(`${api}/knowledge`).then(r => r.ok ? r.json() : null).catch(() => null),
      ]);
      if (statusRes) {
        setDataGate(statusRes.data_quality_gate || null);
        setKillSwitch(statusRes.kill_switch || null);
        setRealityGap(statusRes.reality_gap || null);
        setPortfolio(statusRes.portfolio_summary || null);
        if (statusRes.auto_approve) {
          setAutoApprove(statusRes.auto_approve);
        }
      }
      if (knowledgeRes) {
        setKnowledge(knowledgeRes);
      }
      setSignals(Array.isArray(signalsRes) ? signalsRes : []);
      setPositions(Array.isArray(positionsRes) ? positionsRes : []);
      setAuditEvents(Array.isArray(auditRes) ? auditRes : []);
      try {
        setLastRefresh(new Date().toLocaleTimeString("en-IN"));
      } catch {
        setLastRefresh("");
      }
    } catch (e) {
      // Backend may not be reachable
    }
  }, []);

  const triggerLearn = async () => {
    const api = getApiUrl();
    try {
      const res = await fetch(`${api}/learn`, { method: "POST" });
      const data = await res.json();
      if (data.success && data.knowledge) {
        setKnowledge(data.knowledge);
        setMessage("🧠 Market knowledge updated and strategy weights recalibrated!");
      }
    } catch {
      setMessage("Failed to trigger learning");
    }
  };

  useEffect(() => {
    if (!mounted) return;
    fetchAll();
    const interval = setInterval(fetchAll, 4000);
    return () => clearInterval(interval);
  }, [mounted, fetchAll]);

  const approveSignal = async (id: number) => {
    const api = getApiUrl();
    try {
      const res = await fetch(`${api}/signal/${id}/approve`, { method: "POST" });
      const data = await res.json();
      setMessage(res.ok ? `✓ Signal #${id} approved` : `✗ ${data.detail || "Approval rejected"}`);
      fetchAll();
    } catch { setMessage("Request failed"); }
  };

  const rejectSignal = async (id: number) => {
    const api = getApiUrl();
    try {
      await fetch(`${api}/signal/${id}/reject`, { method: "POST" });
      setMessage(`Signal #${id} rejected`);
      fetchAll();
    } catch { setMessage("Request failed"); }
  };

  const activateKillSwitch = async (level: number) => {
    if (!confirm(`Activate Kill Switch Level ${level}?`)) return;
    const api = getApiUrl();
    try {
      const res = await fetch(`${api}/kill-switch/${level}?reason=Manual+dashboard+activation`, { method: "POST" });
      const data = await res.json();
      setMessage(`Kill Switch L${level}: ${data.level_name || "activated"}`);
      fetchAll();
    } catch { setMessage("Request failed"); }
  };

  const resetKillSwitch = async () => {
    const code = killSwitch?.manual_reset_required ? "CONFIRM_MANUAL_RESET" : "";
    const api = getApiUrl();
    try {
      const res = await fetch(`${api}/kill-switch/reset?manual_operator_code=${code}`, { method: "POST" });
      const data = await res.json();
      setMessage(data.success ? "Kill switch reset ✓" : `Reset failed: ${data.error || "Error"}`);
      fetchAll();
    } catch { setMessage("Request failed"); }
  };

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-950 text-gray-100 p-8 font-mono flex items-center justify-center">
        <div className="text-blue-400 animate-pulse text-sm">Initializing Live Paper Trading Terminal...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-4 font-mono">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-white">
            🇮🇳 LIVE PAPER TRADING — PHASE 7
          </h1>
          <p className="text-xs text-gray-500">
            Strategy: VWAP_EMA_MOMENTUM_V1 | EMA 9/21 | RVOL≥1.15 | ATR SL 1.5× TP 3.0×
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-red-400 font-bold border border-red-700 px-2 py-1 rounded mb-1">
            REAL ORDERS: DISABLED (PAPER MODE)
          </div>
          <div className="text-xs text-gray-500">Updated: {lastRefresh || "Connecting..."}</div>
        </div>
      </div>

      {/* Notification bar */}
      {message && (
        <div className="mb-3 p-2 bg-blue-900/40 border border-blue-700 rounded text-xs text-blue-300 flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage("")} className="text-gray-400 hover:text-white px-2">✕</button>
        </div>
      )}

      {/* Data Quality Banner */}
      <PanelErrorBoundary title="Data Quality Banner">
        <DataQualityBanner gate={dataGate} />
      </PanelErrorBoundary>

      {/* Top row: Portfolio + Kill Switch */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <PanelErrorBoundary title="Portfolio Panel">
          <PortfolioPanel portfolio={portfolio} />
        </PanelErrorBoundary>
        <PanelErrorBoundary title="Kill Switch Panel">
          <KillSwitchPanel ks={killSwitch} onActivate={activateKillSwitch} onReset={resetKillSwitch} />
        </PanelErrorBoundary>
      </div>

      {/* Market Knowledge & Adaptive Learning */}
      <PanelErrorBoundary title="Market Knowledge Panel">
        <MarketKnowledgePanel knowledge={knowledge} onTriggerLearn={triggerLearn} />
      </PanelErrorBoundary>

      {/* Middle: Signals */}
      <div className="mb-4">
        <PanelErrorBoundary title="Signals Panel">
          <PendingSignalsPanel
            signals={signals}
            autoApprove={autoApprove}
            onApprove={approveSignal}
            onReject={rejectSignal}
          />
        </PanelErrorBoundary>
      </div>

      {/* Open Positions */}
      <div className="mb-4">
        <PanelErrorBoundary title="Open Positions Panel">
          <OpenPositionsPanel positions={positions} />
        </PanelErrorBoundary>
      </div>

      {/* Bottom row: Reality Gap + Audit Log */}
      <div className="grid grid-cols-2 gap-4">
        <PanelErrorBoundary title="Reality Gap Panel">
          <RealityGapPanel rg={realityGap} />
        </PanelErrorBoundary>
        <PanelErrorBoundary title="Audit Log Panel">
          <AuditLogPanel events={auditEvents} />
        </PanelErrorBoundary>
      </div>

      {/* Disclaimer */}
      <div className="mt-4 text-center text-xs text-gray-600">
        PAPER TRADING SIMULATION ONLY — Real-money execution is permanently disabled.
        Past paper results do not guarantee future real-money performance.
      </div>
    </div>
  );
}
