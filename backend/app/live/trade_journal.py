"""
Phase 8 — Trade Journal
Persistent, queryable paper trading journal with full analytics.
Computes: win rate, expectancy, PF, drawdown, MFE, MAE, regime performance,
concentration analysis, consecutive streaks, hold time distribution.

Paper Trading ONLY. No real money. No real orders.
"""
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class TradeJournalEntry:
    """Complete auditable record for one paper trade lifecycle."""
    trade_id: int
    session_date: str

    # Identity
    symbol: str
    strategy_name: str = "VWAP_EMA_MOMENTUM_V1"
    data_provenance: str = "UNKNOWN"

    # Signal
    signal_id: Optional[int] = None
    direction: str = "BUY"
    market_regime: str = "UNKNOWN"
    time_of_day_bucket: str = "MID_SESSION"   # OPEN_30M, MID_SESSION, CLOSE_1H

    # Entry
    intended_entry_price: float = 0.0
    simulated_fill_price: float = 0.0
    entry_slippage_inr: float = 0.0
    entry_slippage_pct: float = 0.0
    quantity: int = 1
    opened_at: Optional[datetime.datetime] = None

    # Stops
    stop_loss: float = 0.0
    target_price: float = 0.0
    risk_reward_ratio: float = 0.0

    # Exit
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    closed_at: Optional[datetime.datetime] = None
    holding_minutes: float = 0.0

    # P&L
    gross_pnl: float = 0.0
    brokerage: float = 0.0
    stt: float = 0.0
    exchange_charges: float = 0.0
    sebi_charges: float = 0.0
    gst: float = 0.0
    stamp_duty: float = 0.0
    total_charges: float = 0.0
    net_pnl: float = 0.0

    # Excursions
    mfe_inr: float = 0.0    # Maximum Favorable Excursion
    mae_inr: float = 0.0    # Maximum Adverse Excursion
    mfe_pct: float = 0.0
    mae_pct: float = 0.0

    # Execution quality
    execution_latency_ms: float = 0.0
    data_age_at_signal_ms: float = 0.0

    # Human approval
    human_approved: bool = True

    # Indicator snapshot at signal time
    indicator_snapshot: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        if self.opened_at:
            d["opened_at"] = self.opened_at.isoformat()
        if self.closed_at:
            d["closed_at"] = self.closed_at.isoformat()
        return d


class Phase8TradeJournal:
    """
    Production-quality paper trading journal.
    Stores every trade with complete lifecycle, costs, MFE/MAE, and regime context.
    Provides rich analytics for reality-gap comparison and validation reporting.
    """

    def __init__(self):
        self._entries: List[TradeJournalEntry] = []
        self._trade_id_counter: int = 0
        self._session_date: str = datetime.datetime.now().strftime("%Y-%m-%d")

    def record_trade(self, entry: TradeJournalEntry) -> int:
        """Add a completed trade to the journal. Returns trade ID."""
        self._trade_id_counter += 1
        entry.trade_id = self._trade_id_counter
        entry.session_date = self._session_date
        self._entries.append(entry)
        # Persist to DB best-effort
        self._persist(entry)
        return entry.trade_id

    def get_all_entries(self) -> List[dict]:
        return [e.to_dict() for e in self._entries]

    def get_entry(self, trade_id: int) -> Optional[dict]:
        for e in self._entries:
            if e.trade_id == trade_id:
                return e.to_dict()
        return None

    def compute_analytics(self) -> Dict[str, Any]:
        """Compute comprehensive analytics over all journaled trades."""
        entries = self._entries
        n = len(entries)
        if n == 0:
            return {"total_trades": 0, "status": "NO_TRADES_RECORDED"}

        wins = [e for e in entries if e.net_pnl > 0]
        losses = [e for e in entries if e.net_pnl <= 0]
        win_rate = len(wins) / n * 100.0

        total_net_pnl = sum(e.net_pnl for e in entries)
        gross_wins = sum(e.net_pnl for e in wins)
        gross_losses = abs(sum(e.net_pnl for e in losses))
        avg_win = gross_wins / len(wins) if wins else 0.0
        avg_loss = gross_losses / len(losses) if losses else 0.0
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float("inf")

        # Drawdown
        equity_curve = []
        running = 0.0
        peak = 0.0
        max_dd = 0.0
        for e in sorted(entries, key=lambda x: x.closed_at or datetime.datetime.min):
            running += e.net_pnl
            equity_curve.append(running)
            if running > peak:
                peak = running
            dd = peak - running
            if dd > max_dd:
                max_dd = dd

        # Consecutive streaks
        max_consec_wins = max_consec_losses = cur_wins = cur_losses = 0
        for e in entries:
            if e.net_pnl > 0:
                cur_wins += 1
                cur_losses = 0
                max_consec_wins = max(max_consec_wins, cur_wins)
            else:
                cur_losses += 1
                cur_wins = 0
                max_consec_losses = max(max_consec_losses, cur_losses)

        # MFE / MAE
        avg_mfe = sum(e.mfe_inr for e in entries) / n
        avg_mae = sum(e.mae_inr for e in entries) / n

        # Hold time
        hold_times = [e.holding_minutes for e in entries if e.holding_minutes > 0]
        avg_hold_min = sum(hold_times) / len(hold_times) if hold_times else 0.0

        # Slippage & charges
        avg_slippage = sum(e.entry_slippage_inr for e in entries) / n
        total_charges = sum(e.total_charges for e in entries)

        # Regime performance
        regime_perf = self._regime_breakdown(entries)

        # Symbol concentration
        symbol_perf = self._symbol_breakdown(entries)

        # Validation milestone
        milestone = self._milestone(n)

        return {
            "total_trades": n,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate_pct": round(win_rate, 2),
            "avg_win_inr": round(avg_win, 2),
            "avg_loss_inr": round(avg_loss, 2),
            "expectancy_inr": round(expectancy, 2),
            "profit_factor": round(profit_factor, 3) if profit_factor != float("inf") else "INF",
            "gross_wins_inr": round(gross_wins, 2),
            "gross_losses_inr": round(gross_losses, 2),
            "total_net_pnl_inr": round(total_net_pnl, 2),
            "max_drawdown_inr": round(max_dd, 2),
            "max_consecutive_wins": max_consec_wins,
            "max_consecutive_losses": max_consec_losses,
            "avg_mfe_inr": round(avg_mfe, 2),
            "avg_mae_inr": round(avg_mae, 2),
            "avg_hold_time_minutes": round(avg_hold_min, 1),
            "avg_slippage_per_trade_inr": round(avg_slippage, 2),
            "total_charges_inr": round(total_charges, 2),
            "regime_performance": regime_perf,
            "symbol_concentration": symbol_perf,
            "validation_milestone": milestone,
            "strategy_version": "VWAP_EMA_MOMENTUM_V1",
            "paper_trading_only": True,
            "disclaimer": "PAPER TRADING SIMULATION ONLY. Real money orders: 0 (STRICTLY DISABLED).",
        }

    def _regime_breakdown(self, entries: List[TradeJournalEntry]) -> Dict[str, Any]:
        regimes: Dict[str, List[float]] = {}
        for e in entries:
            r = e.market_regime or "UNKNOWN"
            if r not in regimes:
                regimes[r] = []
            regimes[r].append(e.net_pnl)
        result = {}
        for regime, pnls in regimes.items():
            wins = [p for p in pnls if p > 0]
            result[regime] = {
                "trades": len(pnls),
                "win_rate_pct": round(len(wins) / len(pnls) * 100, 1),
                "net_pnl_inr": round(sum(pnls), 2),
            }
        return result

    def _symbol_breakdown(self, entries: List[TradeJournalEntry]) -> List[dict]:
        symbols: Dict[str, Dict] = {}
        total_gross = sum(abs(e.net_pnl) for e in entries) or 1.0
        for e in entries:
            s = e.symbol
            if s not in symbols:
                symbols[s] = {"trades": 0, "net_pnl": 0.0}
            symbols[s]["trades"] += 1
            symbols[s]["net_pnl"] += e.net_pnl

        result = sorted(
            [{"symbol": k, "trades": v["trades"],
              "net_pnl_inr": round(v["net_pnl"], 2),
              "contribution_pct": round(abs(v["net_pnl"]) / total_gross * 100, 1)}
             for k, v in symbols.items()],
            key=lambda x: abs(x["net_pnl_inr"]), reverse=True
        )

        # Concentration flags
        if result:
            top1_pct = result[0]["contribution_pct"]
            top3_pct = sum(r["contribution_pct"] for r in result[:3])
            if top1_pct > 50:
                for r in result:
                    r["concentration_alert"] = f"Top stock contributes {top1_pct}% of gross P&L"
                    break
            if top3_pct > 80:
                result[0]["top3_concentration_alert"] = f"Top 3 stocks: {top3_pct}% concentration"

        return result

    @staticmethod
    def _milestone(n: int) -> dict:
        if n < 30:
            return {"stage": "INSUFFICIENT_LIVE_DATA", "trades": n, "next_milestone": 30,
                    "progress_pct": round(n / 30 * 100)}
        elif n < 100:
            return {"stage": "EARLY_PAPER_ASSESSMENT", "trades": n, "next_milestone": 100,
                    "progress_pct": round(n / 100 * 100)}
        elif n < 300:
            return {"stage": "PRELIMINARY_PAPER_ASSESSMENT", "trades": n, "next_milestone": 300,
                    "progress_pct": round(n / 300 * 100)}
        elif n < 500:
            return {"stage": "EMPIRICAL_PAPER_ASSESSMENT", "trades": n, "next_milestone": 500,
                    "progress_pct": round(n / 500 * 100)}
        else:
            return {"stage": "HIGH_CONFIDENCE_CANDIDATE", "trades": n, "next_milestone": None,
                    "progress_pct": 100}

    def _persist(self, entry: TradeJournalEntry):
        """Write to Phase8TradeJournal DB table. Best-effort, never raises."""
        try:
            from app.core.database import SessionLocal
            from app.models.models import Phase8TradeJournalRecord
            db = SessionLocal()
            try:
                record = Phase8TradeJournalRecord(
                    trade_id=entry.trade_id,
                    session_date=entry.session_date,
                    symbol=entry.symbol,
                    direction=entry.direction,
                    strategy_name=entry.strategy_name,
                    data_provenance=entry.data_provenance,
                    market_regime=entry.market_regime,
                    time_of_day_bucket=entry.time_of_day_bucket,
                    intended_entry_price=entry.intended_entry_price,
                    simulated_fill_price=entry.simulated_fill_price,
                    quantity=entry.quantity,
                    stop_loss=entry.stop_loss,
                    target_price=entry.target_price,
                    risk_reward_ratio=entry.risk_reward_ratio,
                    exit_price=entry.exit_price,
                    exit_reason=entry.exit_reason,
                    holding_minutes=entry.holding_minutes,
                    gross_pnl=entry.gross_pnl,
                    total_charges=entry.total_charges,
                    net_pnl=entry.net_pnl,
                    entry_slippage_inr=entry.entry_slippage_inr,
                    mfe_inr=entry.mfe_inr,
                    mae_inr=entry.mae_inr,
                    opened_at=entry.opened_at,
                    closed_at=entry.closed_at,
                )
                db.add(record)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()
        except Exception:
            pass


# Global singleton
trade_journal = Phase8TradeJournal()
