import pytest
import datetime
from app.data.market_calendar import IndianMarketCalendar

def test_indian_market_calendar_holidays():
    # Republic Day: 26 Jan 2026
    republic_day = datetime.datetime(2026, 1, 26, 10, 0, 0)
    assert IndianMarketCalendar.is_trading_day(republic_day) is False
    assert IndianMarketCalendar.is_market_open(republic_day) is False

    # Regular Trading Day: Tuesday 27 Jan 2026 @ 10:30 AM IST
    regular_day_open = datetime.datetime(2026, 1, 27, 10, 30, 0)
    assert IndianMarketCalendar.is_trading_day(regular_day_open) is True
    assert IndianMarketCalendar.is_market_open(regular_day_open) is True

    # Weekend (Sunday): 25 Jan 2026
    sunday = datetime.datetime(2026, 1, 25, 11, 0, 0)
    assert IndianMarketCalendar.is_trading_day(sunday) is False

def test_market_calendar_session_status():
    status = IndianMarketCalendar.get_session_status()
    assert "is_trading_day" in status
    assert "is_market_open" in status
    assert "upcoming_holidays" in status
    assert len(status["upcoming_holidays"]) > 0
