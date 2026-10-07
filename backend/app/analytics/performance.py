from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import Trade
from app.core.config import settings
from app.schemas.schemas import PerformanceMetricsResponse

class PerformanceEngine:
    """
    Computes professional quantitative trading performance metrics and risk-adjusted returns.
    """

    @classmethod
    def calculate_metrics(cls, db: Session) -> PerformanceMetricsResponse:
        trades = db.query(Trade).order_by(Trade.exit_time.asc()).all()
        
        total_trades = len(trades)
        if total_trades == 0:
            return PerformanceMetricsResponse(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                gross_profit=0.0,
                gross_loss=0.0,
                net_pnl=0.0,
                total_charges=0.0,
                average_win=0.0,
                average_loss=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                max_drawdown_pct=0.0,
                average_holding_time_minutes=0.0,
                risk_reward_achieved=0.0,
                consecutive_wins=0,
                consecutive_losses=0,
                longest_losing_streak=0,
                average_r=0.0,
                expectancy_per_trade=0.0,
                expectancy_r=0.0,
                average_slippage=0.0,
                performance_by_strategy={},
                performance_by_time_of_day={},
                performance_by_symbol={},
                performance_by_market_regime={},
                initial_capital=settings.INITIAL_CAPITAL,
                current_equity=settings.INITIAL_CAPITAL
            )

        winning_trades = [t for t in trades if t.net_pnl > 0]
        losing_trades = [t for t in trades if t.net_pnl <= 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades) * 100.0

        gross_profit = sum(t.gross_pnl for t in winning_trades)
        gross_loss = abs(sum(t.gross_pnl for t in losing_trades))
        total_charges = sum(t.estimated_charges for t in trades)
        net_pnl = sum(t.net_pnl for t in trades)

        avg_win = (gross_profit / win_count) if win_count > 0 else 0.0
        avg_loss = (gross_loss / loss_count) if loss_count > 0 else 0.0
        profit_factor = (gross_profit / (gross_loss + 1e-10)) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)
        
        # Max Drawdown computation on equity curve
        running_equity = settings.INITIAL_CAPITAL
        peak_equity = settings.INITIAL_CAPITAL
        max_drawdown = 0.0
        max_drawdown_pct = 0.0

        for t in trades:
            running_equity += t.net_pnl
            if running_equity > peak_equity:
                peak_equity = running_equity
            dd = peak_equity - running_equity
            dd_pct = (dd / peak_equity) * 100.0 if peak_equity > 0 else 0.0
            if dd > max_drawdown:
                max_drawdown = dd
            if dd_pct > max_drawdown_pct:
                max_drawdown_pct = dd_pct

        avg_holding_time = sum(t.holding_time_minutes for t in trades) / total_trades
        rr_achieved = (avg_win / (avg_loss + 1e-10)) if avg_loss > 0 else 0.0

        # Streak calculation
        max_consec_wins = 0
        max_consec_losses = 0
        cur_wins = 0
        cur_losses = 0

        for t in trades:
            if t.net_pnl > 0:
                cur_wins += 1
                cur_losses = 0
            else:
                cur_losses += 1
                cur_wins = 0
            if cur_wins > max_consec_wins:
                max_consec_wins = cur_wins
            if cur_losses > max_consec_losses:
                max_consec_losses = cur_losses

        # Phase 6: R-Multiples, Expectancy & Slippage
        r_multiples: List[float] = []
        win_r_multiples: List[float] = []
        loss_r_multiples: List[float] = []
        slippages: List[float] = []

        for t in trades:
            # Achieved R
            if getattr(t, "achieved_r", None) is not None:
                r_val = float(t.achieved_r)
            else:
                init_risk = abs(t.entry_price - t.stop_loss)
                if init_risk > 1e-4:
                    if t.direction == "BUY":
                        r_val = (t.exit_price - t.entry_price) / init_risk
                    else:
                        r_val = (t.entry_price - t.exit_price) / init_risk
                else:
                    r_val = 0.0
            r_multiples.append(r_val)
            if t.net_pnl > 0:
                win_r_multiples.append(r_val)
            else:
                loss_r_multiples.append(r_val)

            # Slippage
            slip = getattr(t, "slippage_incurred", 0.0) or 0.0
            slippages.append(float(slip))

        avg_r = (sum(r_multiples) / total_trades) if total_trades > 0 else 0.0
        avg_slippage = (sum(slippages) / total_trades) if total_trades > 0 else 0.0
        expectancy_inr = (net_pnl / total_trades) if total_trades > 0 else 0.0

        win_prob = win_count / total_trades if total_trades > 0 else 0.0
        loss_prob = loss_count / total_trades if total_trades > 0 else 0.0
        avg_win_r = (sum(win_r_multiples) / len(win_r_multiples)) if win_r_multiples else 0.0
        avg_loss_r = (sum(loss_r_multiples) / len(loss_r_multiples)) if loss_r_multiples else 0.0
        expectancy_r = (win_prob * avg_win_r) + (loss_prob * avg_loss_r)

        # Segmented Helper
        def _aggregate_segment(group_trades: List[Trade]) -> Dict[str, Any]:
            count = len(group_trades)
            if count == 0:
                return {"trades": 0, "win_rate_pct": 0.0, "net_pnl": 0.0, "profit_factor": 0.0}
            w_count = sum(1 for gt in group_trades if gt.net_pnl > 0)
            gp = sum(gt.gross_pnl for gt in group_trades if gt.net_pnl > 0)
            gl = abs(sum(gt.gross_pnl for gt in group_trades if gt.net_pnl <= 0))
            pf = (gp / (gl + 1e-10)) if gl > 0 else (gp if gp > 0 else 1.0)
            return {
                "trades": count,
                "win_rate_pct": round((w_count / count) * 100.0, 2),
                "net_pnl": round(sum(gt.net_pnl for gt in group_trades), 2),
                "profit_factor": round(pf, 2)
            }

        # 1. Performance by Strategy
        perf_by_strategy: Dict[str, Any] = {}
        strategies = set(t.strategy for t in trades if t.strategy)
        for s in strategies:
            perf_by_strategy[s] = _aggregate_segment([t for t in trades if t.strategy == s])

        # 2. Performance by Time of Day
        def _get_time_bucket(entry_dt) -> str:
            if not entry_dt:
                return "MID_SESSION"
            t_str = entry_dt.strftime("%H:%M")
            if "09:15" <= t_str < "09:45":
                return "OPEN_30M"
            elif "09:45" <= t_str < "14:15":
                return "MID_SESSION"
            elif "14:15" <= t_str <= "15:30":
                return "CLOSE_1H"
            return "OTHER"

        perf_by_time: Dict[str, Any] = {
            "OPEN_30M": _aggregate_segment([t for t in trades if _get_time_bucket(t.entry_time) == "OPEN_30M"]),
            "MID_SESSION": _aggregate_segment([t for t in trades if _get_time_bucket(t.entry_time) == "MID_SESSION"]),
            "CLOSE_1H": _aggregate_segment([t for t in trades if _get_time_bucket(t.entry_time) == "CLOSE_1H"])
        }

        # 3. Performance by Symbol
        perf_by_symbol: Dict[str, Any] = {}
        symbols = set(t.symbol for t in trades if t.symbol)
        for sym in symbols:
            perf_by_symbol[sym] = _aggregate_segment([t for t in trades if t.symbol == sym])

        # 4. Performance by Market Regime
        perf_by_regime: Dict[str, Any] = {}
        regimes = set(t.market_regime or "TRENDING" for t in trades)
        for reg in regimes:
            perf_by_regime[reg] = _aggregate_segment([t for t in trades if (t.market_regime or "TRENDING") == reg])

        return PerformanceMetricsResponse(
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate_pct=round(win_rate, 2),
            gross_profit=round(gross_profit, 2),
            gross_loss=round(gross_loss, 2),
            net_pnl=round(net_pnl, 2),
            total_charges=round(total_charges, 2),
            average_win=round(avg_win, 2),
            average_loss=round(avg_loss, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown=round(max_drawdown, 2),
            max_drawdown_pct=round(max_drawdown_pct, 2),
            average_holding_time_minutes=round(avg_holding_time, 1),
            risk_reward_achieved=round(rr_achieved, 2),
            consecutive_wins=max_consec_wins,
            consecutive_losses=max_consec_losses,
            longest_losing_streak=max_consec_losses,
            average_r=round(avg_r, 2),
            expectancy_per_trade=round(expectancy_inr, 2),
            expectancy_r=round(expectancy_r, 2),
            average_slippage=round(avg_slippage, 2),
            performance_by_strategy=perf_by_strategy,
            performance_by_time_of_day=perf_by_time,
            performance_by_symbol=perf_by_symbol,
            performance_by_market_regime=perf_by_regime,
            initial_capital=settings.INITIAL_CAPITAL,
            current_equity=round(settings.INITIAL_CAPITAL + net_pnl, 2)
        )
