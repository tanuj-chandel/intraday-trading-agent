"""
Phase 9 — Intraday Time-of-Day Performance Analyzer

Segment paper trade results across 5 distinct NSE trading windows:
1. 09:15–10:00: Opening drive & initial volatility
2. 10:00–11:30: Morning institutional trend
3. 11:30–13:30: Mid-day consolidation
4. 13:30–14:30: Afternoon session / European open
5. 14:30–15:15: Closing drive before mandatory 15:15 IST square-off
"""
import datetime
from typing import Dict, Any, List
import pytz

IST = pytz.timezone("Asia/Kolkata")


class Phase9TimeOfDayAnalyzer:
    """
    Evaluates paper trade execution quality and profitability partitioned by execution time.
    """

    TIME_SLOTS = [
        "09:15–10:00",
        "10:00–11:30",
        "11:30–13:30",
        "13:30–14:30",
        "14:30–15:15",
    ]

    @classmethod
    def classify_slot(cls, dt: datetime.datetime) -> str:
        """Classify datetime into one of the 5 trading time slots."""
        if dt.tzinfo is None:
            t = dt.time()
        else:
            t = dt.astimezone(IST).time()

        t_min = t.hour * 60 + t.minute

        if t_min < (9 * 60 + 15):
            return "09:15–10:00"
        elif t_min <= (10 * 60):
            return "09:15–10:00"
        elif t_min <= (11 * 60 + 30):
            return "10:00–11:30"
        elif t_min <= (13 * 60 + 30):
            return "11:30–13:30"
        elif t_min <= (14 * 60 + 30):
            return "13:30–14:30"
        else:
            return "14:30–15:15"

    @classmethod
    def analyze(cls, paper_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Group trades by time slot and calculate trade count, win rate, expectancy, net P&L, slippage, drawdown.
        """
        slots: Dict[str, List[Dict[str, Any]]] = {s: [] for s in cls.TIME_SLOTS}

        for t in paper_trades:
            slot = t.get("time_of_day_bucket")
            if not slot or slot not in slots:
                # Try parsing opened_at timestamp
                opened = t.get("opened_at")
                if opened:
                    try:
                        dt = datetime.datetime.fromisoformat(opened)
                        slot = cls.classify_slot(dt)
                    except Exception:
                        slot = "10:00–11:30"
                else:
                    slot = "10:00–11:30"

            slots[slot].append(t)

        results = {}
        for slot_name, trades in slots.items():
            count = len(trades)
            if count == 0:
                results[slot_name] = {
                    "trade_count": 0,
                    "win_rate_pct": 0.0,
                    "expectancy_inr": 0.0,
                    "net_pnl": 0.0,
                    "avg_slippage_inr": 0.0,
                    "max_drawdown": 0.0,
                }
                continue

            pnls = [t.get("net_pnl", 0.0) for t in trades]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p <= 0]
            win_rate = (len(wins) / count * 100.0)

            avg_win = sum(wins) / len(wins) if wins else 0.0
            avg_loss = abs(sum(losses)) / len(losses) if losses else 0.0
            expectancy = (win_rate / 100.0 * avg_win) - ((1.0 - win_rate / 100.0) * avg_loss)

            slippage = sum(t.get("entry_slippage", 0.0) + t.get("exit_slippage", 0.0) for t in trades) / count

            # Drawdown
            running = 0.0
            peak = 0.0
            max_dd = 0.0
            for p in pnls:
                running += p
                if running > peak:
                    peak = running
                dd = peak - running
                if dd > max_dd:
                    max_dd = dd

            results[slot_name] = {
                "trade_count": count,
                "win_rate_pct": round(win_rate, 2),
                "expectancy_inr": round(expectancy, 2),
                "net_pnl": round(sum(pnls), 2),
                "avg_slippage_inr": round(slippage, 2),
                "max_drawdown": round(max_dd, 2),
            }

        return {
            "total_trades_analyzed": len(paper_trades),
            "time_slots": results,
            "best_time_slot": max(
                (s for s, d in results.items() if d["trade_count"] > 0),
                key=lambda s: results[s]["expectancy_inr"],
                default=None
            ),
            "worst_time_slot": min(
                (s for s, d in results.items() if d["trade_count"] > 0),
                key=lambda s: results[s]["expectancy_inr"],
                default=None
            ),
            "disclaimer": "PAPER TRADING ONLY — Shows empirical intraday distribution of strategy edge."
        }
