import json
import os
import datetime
from typing import Dict, Any, Tuple, Optional, List
from app.core.config import settings
from app.schemas.schemas import TradeSignalCreate, RiskCheckResponse

class RiskManager:
    """
    Independent Risk Management Engine.
    Enforces strict risk guardrails, position exposure caps, margin requirements,
    sector concentration limits, and has the authority to veto any trade signal.
    """

    def __init__(
        self,
        max_risk_per_trade_pct: float = settings.MAX_RISK_PER_TRADE_PCT,
        max_daily_loss_amount: float = settings.MAX_DAILY_LOSS_AMOUNT,
        max_open_positions: int = settings.MAX_OPEN_POSITIONS,
        max_trades_per_day: int = settings.MAX_TRADES_PER_DAY,
        min_risk_reward_ratio: float = settings.MIN_RISK_REWARD_RATIO,
        max_consecutive_losses: int = settings.MAX_CONSECUTIVE_LOSSES,
        cutoff_time_str: str = settings.TRADING_CUTOFF_TIME,
        enforce_market_hours: bool = False,
        max_position_notional_pct: float = settings.MAX_POSITION_NOTIONAL_PCT,
        max_total_exposure_pct: float = settings.MAX_TOTAL_EXPOSURE_PCT,
        mis_leverage: float = settings.MIS_LEVERAGE,
        min_signal_score: float = settings.MIN_SIGNAL_SCORE,
        max_trades_per_symbol_per_day: int = settings.MAX_TRADES_PER_SYMBOL_PER_DAY,
        cooldown_after_sl_minutes: int = settings.COOLDOWN_AFTER_SL_MINUTES,
        max_positions_per_sector: int = settings.MAX_POSITIONS_PER_SECTOR,
        sector_map_path: Optional[str] = None
    ):
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_daily_loss_amount = max_daily_loss_amount
        self.max_open_positions = max_open_positions
        self.max_trades_per_day = max_trades_per_day
        self.min_risk_reward_ratio = min_risk_reward_ratio
        self.max_consecutive_losses = max_consecutive_losses
        self.cutoff_time_str = cutoff_time_str
        self.enforce_market_hours = enforce_market_hours
        self.emergency_stop_triggered = False

        # Phase 1 Sizing & Exposure Caps
        self.max_position_notional_pct = max_position_notional_pct
        self.max_total_exposure_pct = max_total_exposure_pct
        self.mis_leverage = mis_leverage
        self.min_signal_score = min_signal_score
        self.max_trades_per_symbol_per_day = max_trades_per_symbol_per_day
        self.cooldown_after_sl_minutes = cooldown_after_sl_minutes
        self.max_positions_per_sector = max_positions_per_sector

        # Per-symbol state tracking
        self.symbol_daily_trade_counts: Dict[str, int] = {}
        self.symbol_last_sl_time: Dict[str, datetime.datetime] = {}

        # Sector mapping
        if sector_map_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sector_map_path = os.path.join(base_dir, "data", "sector_map.json")
        self.sector_map = self._load_sector_map(sector_map_path)

    def _load_sector_map(self, path: str) -> Dict[str, str]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_symbol_sector(self, symbol: str) -> str:
        return self.sector_map.get(symbol.upper(), "Unknown")

    def record_sl_hit(self, symbol: str, hit_time: Optional[datetime.datetime] = None):
        """Records a stop loss hit timestamp for cool-down enforcement."""
        self.symbol_last_sl_time[symbol.upper()] = hit_time or datetime.datetime.now()

    def record_trade_executed(self, symbol: str):
        """Increments the daily trade count for a symbol."""
        sym = symbol.upper()
        self.symbol_daily_trade_counts[sym] = self.symbol_daily_trade_counts.get(sym, 0) + 1

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        current_equity: float,
        current_total_exposure: float = 0.0,
        risk_pct_override: Optional[float] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Calculates position quantity using 3 constraints:
        1. Risk-based quantity = floor((Equity * risk%) / |Entry - SL|)
        2. Notional-cap quantity = floor((Equity * MAX_POSITION_NOTIONAL_PCT) / Entry)
           and constrained by remaining allowed portfolio exposure
        3. Margin-based quantity = floor(available_margin * MIS_LEVERAGE / Entry)
        Final quantity = min(risk_qty, notional_qty, margin_qty).
        """
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share <= 0 or entry_price <= 0 or current_equity <= 0:
            return 0, {"reason": "Invalid entry or stop loss price"}

        risk_pct = risk_pct_override if risk_pct_override is not None else self.max_risk_per_trade_pct
        risk_budget = current_equity * risk_pct
        qty_risk = int(risk_budget / risk_per_share)

        # Notional cap per single position
        max_notional_capital = current_equity * self.max_position_notional_pct
        qty_notional_single = int(max_notional_capital / entry_price)

        # Remaining total portfolio exposure limit
        max_total_allowed_exposure = current_equity * self.max_total_exposure_pct
        remaining_exposure = max(0.0, max_total_allowed_exposure - current_total_exposure)
        qty_portfolio_exposure = int(remaining_exposure / entry_price)

        qty_notional = min(qty_notional_single, qty_portfolio_exposure)

        # Margin / Leverage check
        # Margin needed per share for MIS = entry_price / MIS_LEVERAGE
        # Available capital for new position (equity remaining after existing positions)
        available_capital = max(0.0, current_equity - (current_total_exposure / self.mis_leverage))
        available_margin_for_pos = min(available_capital, max_notional_capital / self.mis_leverage)
        qty_margin = int((available_margin_for_pos * self.mis_leverage) / entry_price)

        final_qty = min(qty_risk, qty_notional, qty_margin)

        sizing_metrics = {
            "qty_risk": qty_risk,
            "qty_notional": qty_notional,
            "qty_margin": qty_margin,
            "final_qty": final_qty,
            "risk_budget": round(risk_budget, 2),
            "risk_per_share": round(risk_per_share, 2),
            "max_notional_capital": round(max_notional_capital, 2),
            "remaining_exposure": round(remaining_exposure, 2),
            "available_capital": round(available_capital, 2)
        }
        return final_qty, sizing_metrics

    def trigger_emergency_stop(self):
        self.emergency_stop_triggered = True

    def reset_emergency_stop(self):
        self.emergency_stop_triggered = False

    def is_past_cutoff_time(self, current_time: Optional[datetime.datetime] = None) -> bool:
        if not self.enforce_market_hours and current_time is None:
            return False
            
        if current_time is None:
            current_time = datetime.datetime.now()
            
        cutoff_hour, cutoff_min = map(int, self.cutoff_time_str.split(":"))
        return (current_time.hour > cutoff_hour) or (
            current_time.hour == cutoff_hour and current_time.minute >= cutoff_min
        )

    def validate_trade(
        self,
        signal: TradeSignalCreate,
        current_equity: float,
        today_realized_loss: float,
        open_positions_count: int,
        trades_count_today: int,
        consecutive_losses: int = 0,
        current_time: Optional[datetime.datetime] = None,
        open_positions_symbols: Optional[List[str]] = None,
        current_total_exposure: float = 0.0,
        symbol_today_trades: Optional[int] = None,
        symbol_last_sl_time: Optional[datetime.datetime] = None
    ) -> RiskCheckResponse:
        """
        Runs comprehensive institutional risk checks against a proposed trade signal.
        """
        now = current_time or datetime.datetime.now()
        symbol = signal.symbol.upper()

        # 1. Emergency Stop Check
        if self.emergency_stop_triggered:
            return RiskCheckResponse(
                passed=False,
                rejection_reason="Emergency Stop is active. All trading halted.",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "EMERGENCY_STOP"}
            )

        # 2. Time Cutoff Check (No new trades after 15:15 IST)
        if self.is_past_cutoff_time(current_time):
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Trading cutoff time ({self.cutoff_time_str} IST) reached. No new positions permitted.",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "CUTOFF_TIME"}
            )

        # 3. Maximum Daily Drawdown Check (Daily loss floor default 2% of capital)
        # Check against configured max_daily_loss_amount or today_realized_loss threshold
        if abs(today_realized_loss) >= self.max_daily_loss_amount and today_realized_loss < 0:
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Max daily loss limit breached (-₹{abs(today_realized_loss):.2f} >= ₹{self.max_daily_loss_amount:.2f}). Trading locked for today.",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "MAX_DAILY_LOSS", "limit": self.max_daily_loss_amount}
            )

        # 4. Maximum Open Positions
        if open_positions_count >= self.max_open_positions:
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Max simultaneous positions limit reached ({open_positions_count}/{self.max_open_positions}).",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "MAX_OPEN_POSITIONS", "limit": self.max_open_positions}
            )

        # 5. Maximum Trades Per Day (Ceiling)
        if trades_count_today >= self.max_trades_per_day:
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Max daily trade count reached ({trades_count_today}/{self.max_trades_per_day}). Overtrading protection active.",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "MAX_TRADES_PER_DAY", "limit": self.max_trades_per_day}
            )

        # 6. Minimum Signal Score threshold
        signal_score = getattr(signal, "strategy_score", 0.0) or 0.0
        if signal_score < self.min_signal_score:
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Signal score {signal_score:.1f} is below minimum required threshold {self.min_signal_score:.1f}.",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "MIN_SIGNAL_SCORE", "score": signal_score, "threshold": self.min_signal_score}
            )

        # 7. Consecutive Loss Circuit Breaker
        if consecutive_losses >= self.max_consecutive_losses:
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Consecutive loss protection triggered ({consecutive_losses} consecutive losses). Cool-off required.",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "CONSECUTIVE_LOSS_LIMIT", "limit": self.max_consecutive_losses}
            )

        # 8. Per-Symbol Daily Trade Cap (default 2 trades per day)
        sym_trades = symbol_today_trades if symbol_today_trades is not None else self.symbol_daily_trade_counts.get(symbol, 0)
        if sym_trades >= self.max_trades_per_symbol_per_day:
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Max daily trades for symbol {symbol} reached ({sym_trades}/{self.max_trades_per_symbol_per_day}).",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "MAX_TRADES_PER_SYMBOL", "symbol": symbol, "limit": self.max_trades_per_symbol_per_day}
            )

        # 9. Cooldown After Stop Loss Hit (default 45 minutes)
        last_sl = symbol_last_sl_time if symbol_last_sl_time is not None else self.symbol_last_sl_time.get(symbol)
        if last_sl:
            elapsed_minutes = (now - last_sl).total_seconds() / 60.0
            if elapsed_minutes < self.cooldown_after_sl_minutes:
                remaining_cd = self.cooldown_after_sl_minutes - elapsed_minutes
                return RiskCheckResponse(
                    passed=False,
                    rejection_reason=f"Symbol {symbol} in post-SL cooldown ({remaining_cd:.1f}m remaining of {self.cooldown_after_sl_minutes}m).",
                    current_daily_loss=today_realized_loss,
                    current_open_positions=open_positions_count,
                    calculated_risk_amount=0.0,
                    metrics={"rule": "COOLDOWN_AFTER_SL", "symbol": symbol, "remaining_minutes": round(remaining_cd, 1)}
                )

        # 10. Sector / Correlation Concentration Limit (default 2 per sector)
        if open_positions_symbols:
            target_sector = self.get_symbol_sector(symbol)
            if target_sector != "Unknown":
                sector_positions = sum(
                    1 for s in open_positions_symbols
                    if self.get_symbol_sector(s) == target_sector
                )
                if sector_positions >= self.max_positions_per_sector:
                    return RiskCheckResponse(
                        passed=False,
                        rejection_reason=f"Sector limit reached for '{target_sector}' ({sector_positions}/{self.max_positions_per_sector} open positions).",
                        current_daily_loss=today_realized_loss,
                        current_open_positions=open_positions_count,
                        calculated_risk_amount=0.0,
                        metrics={"rule": "MAX_POSITIONS_PER_SECTOR", "sector": target_sector, "count": sector_positions}
                    )

        # 11. Risk / Reward Ratio Check
        risk_per_share = abs(signal.entry_price - signal.stop_loss)
        reward_per_share = abs(signal.target_price - signal.entry_price)
        
        if risk_per_share <= 0:
            return RiskCheckResponse(
                passed=False,
                rejection_reason="Invalid Stop Loss (must not equal entry price).",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "INVALID_STOP_LOSS"}
            )

        rr_ratio = reward_per_share / risk_per_share
        if rr_ratio < self.min_risk_reward_ratio:
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Risk/Reward ratio {rr_ratio:.2f} is below required minimum of 1:{self.min_risk_reward_ratio:.2f}.",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                metrics={"rule": "MIN_RR_RATIO", "ratio": round(rr_ratio, 2)}
            )

        # 12. Tri-Constraint Position Sizing & Exposure Enforcement
        # Quantity = min(risk-based qty, notional-cap qty, margin-based qty)
        final_qty, sizing_metrics = self.calculate_position_size(
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            current_equity=current_equity,
            current_total_exposure=current_total_exposure
        )

        if final_qty < 1:
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Position size calculation resulted in 0 shares (insufficient capital, margin or exposure ceiling).",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=0.0,
                allowed_quantity=0,
                metrics={"rule": "INSUFFICIENT_QTY_SIZING", **sizing_metrics}
            )

        # If requested quantity in signal is greater than what our strict sizing permits,
        # adjust or reject based on whether quantity exceeds final_qty significantly
        total_risk_amount = risk_per_share * final_qty
        total_position_value = signal.entry_price * final_qty

        # Total Exposure Check after adding this position
        if (current_total_exposure + total_position_value) > (current_equity * self.max_total_exposure_pct * 1.01):
            return RiskCheckResponse(
                passed=False,
                rejection_reason=f"Adding position value ₹{total_position_value:.2f} exceeds total portfolio exposure limit (₹{current_equity * self.max_total_exposure_pct:.2f}).",
                current_daily_loss=today_realized_loss,
                current_open_positions=open_positions_count,
                calculated_risk_amount=total_risk_amount,
                allowed_quantity=final_qty,
                metrics={"rule": "MAX_TOTAL_EXPOSURE", "total_exposure": current_total_exposure + total_position_value}
            )

        return RiskCheckResponse(
            passed=True,
            rejection_reason=None,
            current_daily_loss=today_realized_loss,
            current_open_positions=open_positions_count,
            calculated_risk_amount=total_risk_amount,
            allowed_quantity=final_qty,
            metrics={
                "risk_amount": round(total_risk_amount, 2),
                "reward_amount": round(reward_per_share * final_qty, 2),
                "rr_ratio": round(rr_ratio, 2),
                "position_value": round(total_position_value, 2),
                "allowed_quantity": final_qty,
                **sizing_metrics
            }
        )
