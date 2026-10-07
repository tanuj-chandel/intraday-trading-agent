import datetime
import asyncio
from typing import Dict, Any, Callable, List
from app.core.logging import logger
from app.core.config import settings

class IntradayScheduler:
    """
    Intraday schedule state machine for Indian market sessions.
    Configurable and non-blocking.
    """

    SCHEDULE_EVENTS = [
        {"time": "08:00", "event": "PRE_MARKET_INIT", "desc": "Initialize market data feeds and database connections"},
        {"time": "08:15", "event": "NEWS_RESEARCH", "desc": "Fetch macroeconomic releases and corporate sentiment"},
        {"time": "08:30", "event": "STOCK_RANKING", "desc": "Run multi-factor scoring on Indian stock universe"},
        {"time": "08:45", "event": "GENERATE_PLAN", "desc": "Generate Top 10 candidate trade setups and entry zones"},
        {"time": "09:00", "event": "USER_REVIEW", "desc": "Present trading plan on dashboard for operator approval"},
        {"time": "09:15", "event": "MARKET_OPEN", "desc": "NSE/BSE Regular trading session begins"},
        {"time": "15:15", "event": "INTRADAY_CUTOFF", "desc": "Intraday cutoff: Halt new entries & square off remaining positions"},
        {"time": "15:30", "event": "MARKET_CLOSE", "desc": "Market closes, generate daily performance report and journal"},
        {"time": "15:45", "event": "EOD_TELEGRAM_REPORT", "desc": "Dispatch End-of-Day Telegram report with P&L, metrics, rejections, and warnings"}
    ]

    def __init__(self):
        self.is_running = False
        self.current_session_phase = "PRE_MARKET"
        self._handlers: Dict[str, List[Callable]] = {}

    def get_market_session_phase(self, current_time: datetime.datetime = None) -> str:
        if current_time is None:
            current_time = datetime.datetime.now()
            
        time_str = current_time.strftime("%H:%M")
        
        if time_str < "09:15":
            return "PRE_MARKET"
        elif "09:15" <= time_str < "15:15":
            return "LIVE_SESSION"
        elif "15:15" <= time_str < "15:30":
            return "CUTOFF_SQUAREOFF"
        else:
            return "POST_MARKET_CLOSED"

    def get_schedule(self) -> List[Dict[str, Any]]:
        current_phase = self.get_market_session_phase()
        res = []
        for item in self.SCHEDULE_EVENTS:
            res.append({
                **item,
                "is_current_phase": (item["time"] <= datetime.datetime.now().strftime("%H:%M"))
            })
        return res
