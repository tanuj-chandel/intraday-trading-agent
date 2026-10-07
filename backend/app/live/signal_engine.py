import datetime
from typing import Dict, Any, List, Optional
from app.live.data_types import LiveSignalItem, LiveCandle
from app.live.indicators import LiveIndicatorCalculator
from app.live.deduplicator import DuplicateSignalDeduplicator
from app.risk.manager import RiskManager
from app.news.aggregator import news_aggregator
from app.learning.learner import market_learner
from app.live.audit import LiveAuditLogger
from app.core.config import settings

class LiveSignalEngine:
    """
    Evaluates real-time candles against baseline VWAP_EMA_MOMENTUM_V1.
    Integrates news sentiment filtering, adaptive parameter self-learning,
    and generates PENDING signals for paper execution.
    """

    def __init__(self, risk_manager: Optional[RiskManager] = None):
        self.deduplicator = DuplicateSignalDeduplicator(cooldown_minutes=15)
        self.risk_manager = risk_manager or RiskManager()
        self._signal_counter = 0
        self._pending_signals: Dict[int, LiveSignalItem] = {}

    def evaluate_symbol(
        self,
        symbol: str,
        candles: List[LiveCandle],
        market_regime: str = "TRENDING_UP",
        data_freshness: float = 1.0,
        initial_capital: float = 500000.0
    ) -> Optional[LiveSignalItem]:
        if not self.deduplicator.can_generate_signal(symbol):
            return None

        if len(candles) < 5:
            return None

        ind = LiveIndicatorCalculator.calculate_indicators(candles)
        if not ind["is_valid"]:
            return None

        last_close = candles[-1].close
        direction = None
        reason = ""

        # Phase 4: Event-Day Mode Check
        from app.strategies.quality_filters import quality_filters
        can_trade_event, risk_mult, event_msg = quality_filters.check_event_day(symbol=symbol)
        if not can_trade_event:
            return None

        # Phase 4: Tradability Check (ASM/GSM, Halted, Corporate Actions, Circuit limits)
        passed_tradability, trade_msg = quality_filters.check_tradability(symbol=symbol, ltp=last_close)
        if not passed_tradability:
            return None

        # Query Adaptive Self-Learning parameters
        knowledge = market_learner.get_knowledge()
        caution_symbols = knowledge.get("caution_symbols", [])
        best_symbols = knowledge.get("best_symbols", [])
        recommended_sl = knowledge.get("recommended_sl_pct", 0.010)

        # Asymmetric Risk-Reward: Tight Stop (1.0x - 1.2x ATR) vs High Target (2.5x - 3.0x ATR)
        sl_mult = 1.2 if recommended_sl > 0.011 else 1.0
        tp_mult = round(sl_mult * 2.5, 2)  # 1:2.5 Asymmetric R:R

        # Technical Strategy Logic
        # LONG Condition
        if (
            last_close > ind["vwap"]
            and ind["ema_fast"] > ind["ema_slow"]
            and 45.0 <= ind["rsi"] <= 75.0
            and ind["macd_hist"] > 0
            and ind["rvol"] >= 1.15
        ):
            direction = "BUY"
            atr_val = max(1.0, ind["atr"])
            sl = round(last_close - (sl_mult * atr_val), 2)
            tp = round(last_close + (tp_mult * atr_val), 2)
            reason = f"Bullish momentum: Price ({last_close}) > VWAP ({ind['vwap']}), EMA9 > EMA21, RVOL={ind['rvol']:.2f}"

        # SHORT Condition
        elif (
            last_close < ind["vwap"]
            and ind["ema_fast"] < ind["ema_slow"]
            and 25.0 <= ind["rsi"] <= 55.0
            and ind["macd_hist"] < 0
            and ind["rvol"] >= 1.15
        ):
            direction = "SELL"
            atr_val = max(1.0, ind["atr"])
            sl = round(last_close + (sl_mult * atr_val), 2)
            tp = round(last_close - (tp_mult * atr_val), 2)
            reason = f"Bearish breakdown: Price ({last_close}) < VWAP ({ind['vwap']}), EMA9 < EMA21, RVOL={ind['rvol']:.2f}"

        if not direction:
            return None

        # News Sentiment Filter Gate
        news_info = news_aggregator.get_sentiment_for_symbol(symbol)
        news_sentiment = news_info.get("sentiment_score", 0.0)
        news_headline = news_info.get("headline")

        # Block BUY signals on negative news
        if direction == "BUY" and news_sentiment < -0.3:
            LiveAuditLogger.log(
                "SIGNAL_BLOCKED_NEWS",
                f"BUY blocked for {symbol} due to adverse news ({news_sentiment:+.2f}): {news_headline}",
                symbol=symbol
            )
            return None

        # Block SELL signals on strong bullish news
        if direction == "SELL" and news_sentiment > 0.3:
            LiveAuditLogger.log(
                "SIGNAL_BLOCKED_NEWS",
                f"SELL blocked for {symbol} due to bullish news ({news_sentiment:+.2f}): {news_headline}",
                symbol=symbol
            )
            return None

        # High Profit / Minimum Loss Sizing Architecture:
        risk_pct = getattr(settings, "MAX_RISK_PER_TRADE_PCT", 0.005)
        if risk_mult < 1.0:
            risk_pct = max(0.002, risk_pct * risk_mult)
            reason += f" [Event-Day Scaled Risk {risk_pct*100:.2f}%]"
        if symbol in caution_symbols:
            risk_pct = max(0.002, risk_pct * 0.5)
            reason += f" [Min-Loss Caution Sizing {risk_pct*100:.2f}%]"
        elif symbol in best_symbols or (direction == "BUY" and news_sentiment > 0.2):
            risk_pct = min(0.01, risk_pct * 1.5)
            reason += f" [High-Profit Alpha Sizing {risk_pct*100:.2f}%]"

        if news_headline:
            reason += f" | Live News: {news_headline[:60]} (Score: {news_sentiment:+.2f})"

        qty, _ = self.risk_manager.calculate_position_size(
            entry_price=last_close,
            stop_loss=sl,
            current_equity=initial_capital,
            risk_pct_override=risk_pct
        )
        if qty < 1:
            return None

        base_score = 80.0
        if symbol in best_symbols:
            base_score += 5.0
        if (direction == "BUY" and news_sentiment > 0.2) or (direction == "SELL" and news_sentiment < -0.2):
            base_score += 5.0

        # Reject if below MIN_SIGNAL_SCORE
        min_score = getattr(settings, "MIN_SIGNAL_SCORE", 70.0)
        final_score = min(99.0, base_score)
        if final_score < min_score:
            return None

        # Phase 4: Time Filters Check (09:15-09:25 block, >14:30 block, lunch chop reduction)
        passed_time, time_reason = quality_filters.check_time_filter(score=final_score, symbol=symbol)
        if not passed_time:
            return None

        # Phase 4: Market Regime Filter Check (TRENDING / CHOPPY / HIGH_VOL)
        passed_regime, regime_reason = quality_filters.check_regime_filter(regime=market_regime, score=final_score, symbol=symbol)
        if not passed_regime:
            return None

        self._signal_counter += 1
        sig = LiveSignalItem(
            id=self._signal_counter,
            symbol=symbol,
            direction=direction,
            entry_price=last_close,
            stop_loss=sl,
            target_price=tp,
            quantity=qty,
            risk_reward_ratio=2.5,
            strategy_name="VWAP_EMA_MOMENTUM_V1",
            strategy_score=min(99.0, base_score),
            status="PENDING_APPROVAL",
            market_regime=market_regime,
            indicator_snapshot=ind,
            data_freshness_seconds=data_freshness,
            created_at=datetime.datetime.now(),
            reason=reason,
            risk_passed=True
        )

        self.deduplicator.register_signal(symbol)
        self._pending_signals[sig.id] = sig
        return sig

    def check_and_expire_signals(self, timeout_seconds: Optional[int] = None) -> List[LiveSignalItem]:
        """
        Expires signals pending approval longer than APPROVAL_TIMEOUT_SECONDS.
        """
        limit_sec = timeout_seconds if timeout_seconds is not None else getattr(settings, "APPROVAL_TIMEOUT_SECONDS", 120)
        now = datetime.datetime.now()
        expired = []
        for sig in self._pending_signals.values():
            if sig.status in ("PENDING", "PENDING_APPROVAL"):
                age = (now - sig.created_at).total_seconds()
                if age >= limit_sec:
                    sig.status = "EXPIRED"
                    sig.risk_notes = f"Signal expired after {int(age)}s without approval (timeout={limit_sec}s)"
                    LiveAuditLogger.log("SIGNAL_EXPIRED", f"Signal #{sig.id} ({sig.symbol}) expired after {int(age)}s", symbol=sig.symbol)
                    expired.append(sig)
        return expired

    def get_pending_signals(self) -> List[LiveSignalItem]:
        self.check_and_expire_signals()
        return [s for s in self._pending_signals.values() if s.status in ("PENDING", "PENDING_APPROVAL")]

    def get_signal(self, signal_id: int) -> Optional[LiveSignalItem]:
        return self._pending_signals.get(signal_id)

    def update_signal_status(self, signal_id: int, status: str, reject_reason: Optional[str] = None):
        if signal_id in self._pending_signals:
            self._pending_signals[signal_id].status = status
            if reject_reason:
                self._pending_signals[signal_id].risk_notes = reject_reason
