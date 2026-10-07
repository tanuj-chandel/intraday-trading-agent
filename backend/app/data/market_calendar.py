import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
from app.core.config import settings

# 2026 Official NSE / BSE Intraday Equity Trading Holiday Calendar
DEFAULT_NSE_HOLIDAYS_2026 = {
    "2026-01-26": "Republic Day",
    "2026-02-18": "Mahashivratri",
    "2026-03-04": "Holi",
    "2026-03-20": "Id-Ul-Fitr (Ramzan Id)",
    "2026-03-27": "Ram Navami",
    "2026-03-31": "Mahavir Jayanti",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-05-27": "Bakri Id / Eid ul-Adha",
    "2026-08-15": "Independence Day",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-08": "Diwali Laxmi Pujan (Muhurat Trading Special Session)",
    "2026-11-10": "Diwali Balipratipada",
    "2026-11-24": "Gurunanak Jayanti",
    "2026-12-25": "Christmas"
}

class IndianMarketCalendar:
    """
    NSE / BSE Indian Market Trading Session & Holiday Calendar.
    Enforces trading day checks and rejects regular signal generation on exchange holidays.
    """
    _holidays: Dict[str, str] = DEFAULT_NSE_HOLIDAYS_2026.copy()

    @classmethod
    def add_holiday(cls, date_str: str, description: str):
        cls._holidays[date_str] = description

    @classmethod
    def is_trading_day(cls, dt: Optional[datetime.datetime] = None) -> bool:
        check_dt = dt or datetime.datetime.now()
        # Weekends (Saturday=5, Sunday=6)
        if check_dt.weekday() >= 5:
            return False
        
        date_str = check_dt.strftime("%Y-%m-%d")
        if date_str in cls._holidays:
            # Special exemption for Muhurat trading if applicable
            if "Muhurat" in cls._holidays[date_str]:
                return True
            return False
        
        return True

    @classmethod
    def is_market_open(cls, dt: Optional[datetime.datetime] = None) -> bool:
        check_dt = dt or datetime.datetime.now()
        if not cls.is_trading_day(check_dt):
            return False

        curr_time = check_dt.time()
        open_time = pd.to_datetime(settings.MARKET_OPEN_TIME).time()
        close_time = pd.to_datetime(settings.MARKET_CLOSE_TIME).time()

        return open_time <= curr_time <= close_time

    @classmethod
    def get_session_status(cls, dt: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        check_dt = dt or datetime.datetime.now()
        date_str = check_dt.strftime("%Y-%m-%d")
        is_holiday = date_str in cls._holidays
        is_weekend = check_dt.weekday() >= 5
        is_trade_day = cls.is_trading_day(check_dt)
        is_open = cls.is_market_open(check_dt)

        status_label = "REGULAR_MARKET_OPEN" if is_open else (
            "EXCHANGE_HOLIDAY" if is_holiday else (
                "WEEKEND_CLOSED" if is_weekend else "MARKET_CLOSED"
            )
        )

        return {
            "current_time_ist": check_dt.strftime("%Y-%m-%d %H:%M:%S IST"),
            "is_trading_day": is_trade_day,
            "is_market_open": is_open,
            "status": status_label,
            "holiday_name": cls._holidays.get(date_str),
            "regular_market_hours": f"{settings.MARKET_OPEN_TIME} to {settings.MARKET_CLOSE_TIME} IST",
            "upcoming_holidays": [
                {"date": k, "holiday": v}
                for k, v in sorted(cls._holidays.items())
                if k >= date_str
            ][:5]
        }
