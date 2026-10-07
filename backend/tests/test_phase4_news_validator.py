import pytest
import datetime
from app.news.timestamp_validator import NewsTimestampValidator, NewsTimestampValidationError

def test_news_causal_validation_success():
    sim_time = datetime.datetime(2026, 8, 25, 11, 0, 0)
    valid_news = [
        {"headline": "News A", "published_at": "2026-08-25T10:15:00"},
        {"headline": "News B", "published_at": "2026-08-25T10:45:00"}
    ]
    causal = NewsTimestampValidator.filter_causal_news(valid_news, sim_time)
    assert len(causal) == 2

def test_news_future_leak_detection_failure():
    sim_time = datetime.datetime(2026, 8, 25, 10, 0, 0)
    future_news = [
        {"headline": "Future News C", "published_at": "2026-08-25T11:30:00"} # 11:30 > 10:00
    ]
    with pytest.raises(NewsTimestampValidationError):
        NewsTimestampValidator.filter_causal_news(future_news, sim_time)
