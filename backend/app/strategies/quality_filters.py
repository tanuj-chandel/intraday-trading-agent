import datetime
from typing import Dict, Any, Optional, Tuple, List
from app.core.config import settings
from app.live.audit import LiveAuditLogger

class TradeQualityFilterEngine:
    """
    Trade Quality Filters for Intraday Trading:
    1. Time filters (09:15-09:25 blocked, > 14:30 blocked, lunch chop 12:00-13:30 higher threshold)
    2. Market regime filter (India VIX & Nifty trend: TRENDING / CHOPPY / HIGH_VOL)
    3. Tradability checks (circuit limits buffer, halted, ASM/GSM, results/corporate actions)
    4. Event-day mode (macro event dates: pause or reduce risk)
    All filters are individually toggleable via config.py and log when blocking a trade.
    """

    @classmethod
    def check_time_filter(
        cls,
        dt: Optional[datetime.datetime] = None,
        score: float = 80.0,
        symbol: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        No new entries in the first 10 minutes (09:15-09:25) and after 14:30 IST.
        Optional lunch-chop reduction (12:00-13:30) with a higher score threshold.
        """
        if not getattr(settings, "TIME_FILTER_ENABLED", True):
            return True, None

        now = dt or datetime.datetime.now()
        curr_time = now.strftime("%H:%M")

        no_entry_before = getattr(settings, "NO_ENTRY_BEFORE_TIME", "09:25")
        no_entry_after = getattr(settings, "NO_ENTRY_AFTER_TIME", "14:30")

        # 1. Early morning opening volatility filter
        if curr_time < no_entry_before:
            reason = f"No new entries allowed in opening window ({curr_time} < {no_entry_before} IST)"
            LiveAuditLogger.log("TIME_FILTER_BLOCKED", reason, symbol=symbol)
            return False, reason

        # 2. Late afternoon auto square-off proximity filter
        if curr_time > no_entry_after:
            reason = f"No new entries allowed late in session ({curr_time} > {no_entry_after} IST)"
            LiveAuditLogger.log("TIME_FILTER_BLOCKED", reason, symbol=symbol)
            return False, reason

        # 3. Lunch chop window filter
        if getattr(settings, "LUNCH_CHOP_FILTER_ENABLED", True):
            lunch_start = getattr(settings, "LUNCH_CHOP_START_TIME", "12:00")
            lunch_end = getattr(settings, "LUNCH_CHOP_END_TIME", "13:30")
            min_lunch_score = getattr(settings, "LUNCH_CHOP_MIN_SCORE", 85.0)

            if lunch_start <= curr_time <= lunch_end:
                if score < min_lunch_score:
                    reason = f"Lunch-chop reduction active ({lunch_start}-{lunch_end} IST): Signal score {score:.1f} < threshold {min_lunch_score:.1f}"
                    LiveAuditLogger.log("LUNCH_CHOP_BLOCKED", reason, symbol=symbol)
                    return False, reason

        return True, None

    @classmethod
    def check_regime_filter(
        cls,
        regime: str,
        score: float = 80.0,
        india_vix: Optional[float] = None,
        symbol: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Market regime filter: classify TRENDING / CHOPPY / HIGH_VOL.
        In CHOPPY or extreme HIGH_VOL, raise score threshold or block entries.
        """
        if not getattr(settings, "REGIME_FILTER_ENABLED", True):
            return True, None

        regime_norm = regime.upper()
        vix = india_vix if india_vix is not None else 15.0

        vix_extreme_threshold = getattr(settings, "INDIA_VIX_EXTREME_THRESHOLD", 26.0)
        vix_high_threshold = getattr(settings, "INDIA_VIX_HIGH_VOL_THRESHOLD", 22.0)
        block_high_vol = getattr(settings, "BLOCK_ENTRIES_IN_HIGH_VOL", False)
        block_choppy = getattr(settings, "BLOCK_ENTRIES_IN_CHOPPY", False)
        high_vol_min_score = getattr(settings, "REGIME_HIGH_VOL_MIN_SCORE", 85.0)
        choppy_min_score = getattr(settings, "REGIME_CHOPPY_MIN_SCORE", 85.0)

        # Check VIX-driven extreme volatility
        if vix >= vix_extreme_threshold:
            if block_high_vol:
                reason = f"Extreme India VIX ({vix:.1f} >= {vix_extreme_threshold:.1f}): Entries blocked"
                LiveAuditLogger.log("REGIME_FILTER_BLOCKED", reason, symbol=symbol)
                return False, reason
            elif score < high_vol_min_score:
                reason = f"Extreme India VIX ({vix:.1f}): Score {score:.1f} < required {high_vol_min_score:.1f}"
                LiveAuditLogger.log("REGIME_FILTER_BLOCKED", reason, symbol=symbol)
                return False, reason

        # Check regime classification
        if regime_norm in ("CHOPPY", "SIDEWAYS"):
            if block_choppy:
                reason = f"Market regime is {regime_norm}: New entries blocked by regime filter"
                LiveAuditLogger.log("REGIME_FILTER_BLOCKED", reason, symbol=symbol)
                return False, reason
            elif score < choppy_min_score:
                reason = f"Market regime is {regime_norm}: Score {score:.1f} < required {choppy_min_score:.1f}"
                LiveAuditLogger.log("REGIME_FILTER_BLOCKED", reason, symbol=symbol)
                return False, reason

        elif regime_norm in ("HIGH_VOL", "HIGH_VOLATILITY") or vix >= vix_high_threshold:
            if block_high_vol:
                reason = f"High volatility regime ({regime_norm}, VIX={vix:.1f}): Entries blocked"
                LiveAuditLogger.log("REGIME_FILTER_BLOCKED", reason, symbol=symbol)
                return False, reason
            elif score < high_vol_min_score:
                reason = f"High volatility regime ({regime_norm}, VIX={vix:.1f}): Score {score:.1f} < required {high_vol_min_score:.1f}"
                LiveAuditLogger.log("REGIME_FILTER_BLOCKED", reason, symbol=symbol)
                return False, reason

        return True, None

    @classmethod
    def check_tradability(
        cls,
        symbol: str,
        ltp: float,
        upper_circuit: Optional[float] = None,
        lower_circuit: Optional[float] = None,
        is_halted: bool = False,
        corporate_action_today: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Tradability checks:
        - Skip stocks at or near circuit limits (within CIRCUIT_LIMIT_BUFFER_PCT, default 1%)
        - Skip halted stocks
        - Skip ASM/GSM-listed stocks
        - Skip stocks with results / corporate actions today
        """
        if not getattr(settings, "TRADABILITY_CHECKS_ENABLED", True):
            return True, None

        sym_clean = symbol.upper().replace(".NS", "")

        # 1. Exchange Halted Check
        if getattr(settings, "SKIP_HALTED_STOCKS", True) and is_halted:
            reason = f"Stock {sym_clean} is halted from exchange trading"
            LiveAuditLogger.log("TRADABILITY_BLOCKED", reason, symbol=sym_clean)
            return False, reason

        # 2. ASM / GSM Surveillance Check
        if getattr(settings, "SKIP_ASM_GSM_STOCKS", True):
            asm_gsm_list = getattr(settings, "ASM_GSM_SYMBOLS", [])
            if sym_clean in [s.upper() for s in asm_gsm_list]:
                reason = f"Stock {sym_clean} is under exchange surveillance (ASM/GSM list)"
                LiveAuditLogger.log("TRADABILITY_BLOCKED", reason, symbol=sym_clean)
                return False, reason

        # 3. Circuit Limit Proximity Check
        if getattr(settings, "SKIP_CIRCUIT_STOCKS", True) and ltp > 0:
            buffer_pct = getattr(settings, "CIRCUIT_LIMIT_BUFFER_PCT", 0.01)
            if upper_circuit and upper_circuit > 0:
                threshold_uc = upper_circuit * (1.0 - buffer_pct)
                if ltp >= threshold_uc:
                    reason = f"Stock {sym_clean} near Upper Circuit: LTP ₹{ltp:.2f} >= ₹{threshold_uc:.2f} (UC ₹{upper_circuit:.2f})"
                    LiveAuditLogger.log("TRADABILITY_BLOCKED", reason, symbol=sym_clean)
                    return False, reason

            if lower_circuit and lower_circuit > 0:
                threshold_lc = lower_circuit * (1.0 + buffer_pct)
                if ltp <= threshold_lc:
                    reason = f"Stock {sym_clean} near Lower Circuit: LTP ₹{ltp:.2f} <= ₹{threshold_lc:.2f} (LC ₹{lower_circuit:.2f})"
                    LiveAuditLogger.log("TRADABILITY_BLOCKED", reason, symbol=sym_clean)
                    return False, reason

        # 4. Results / Corporate Actions Today Check
        if getattr(settings, "SKIP_CORPORATE_ACTION_TODAY", True) and corporate_action_today:
            reason = f"Stock {sym_clean} has results/corporate action today: {corporate_action_today}"
            LiveAuditLogger.log("TRADABILITY_BLOCKED", reason, symbol=sym_clean)
            return False, reason

        return True, None

    @classmethod
    def check_event_day(
        cls,
        dt: Optional[datetime.datetime] = None,
        symbol: Optional[str] = None
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Event-day mode:
        A config list of dates (RBI MPC, Union Budget, Monthly F&O Expiry) that
        reduces risk or pauses trading.
        Returns: (can_trade: bool, risk_multiplier: float, reason: Optional[str])
        """
        if not getattr(settings, "EVENT_DAY_FILTER_ENABLED", True):
            return True, 1.0, None

        now = dt or datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        event_days = getattr(settings, "EVENT_DAYS", [])

        if today_str in event_days:
            action = getattr(settings, "EVENT_DAY_ACTION", "REDUCE_RISK").upper()
            if action == "PAUSE_TRADING":
                reason = f"Event-Day Mode ({today_str} scheduled macro event): Trading paused"
                LiveAuditLogger.log("EVENT_DAY_PAUSE", reason, symbol=symbol)
                return False, 0.0, reason
            else:
                multiplier = getattr(settings, "EVENT_DAY_RISK_MULTIPLIER", 0.5)
                reason = f"Event-Day Mode ({today_str} macro event): Risk scaled by {multiplier:.1f}x"
                LiveAuditLogger.log("EVENT_DAY_REDUCED_RISK", reason, symbol=symbol)
                return True, multiplier, reason

        return True, 1.0, None

quality_filters = TradeQualityFilterEngine()
