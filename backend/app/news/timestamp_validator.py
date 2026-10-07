import datetime
from typing import List, Dict, Any

class NewsTimestampValidationError(Exception):
    pass

class NewsTimestampValidator:
    """
    Validates news publication timestamps during historical simulation and backtesting.
    Enforces strict causality: Rejects any news items published after the candle simulation timestamp.
    """

    @classmethod
    def filter_causal_news(
        cls,
        news_items: List[Dict[str, Any]],
        current_sim_time: datetime.datetime
    ) -> List[Dict[str, Any]]:
        causal_news = []
        for n in news_items:
            pub_time = pd_to_dt(n.get("published_at"))
            if pub_time is None:
                continue

            if pub_time > current_sim_time:
                # Look-ahead violation detected
                raise NewsTimestampValidationError(
                    f"Look-Ahead Bias Violation: News published at {pub_time.isoformat()} cannot be used at simulation time {current_sim_time.isoformat()}."
                )
            causal_news.append(n)

        return causal_news

def pd_to_dt(val: Any) -> datetime.datetime:
    if isinstance(val, datetime.datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return datetime.datetime.now()
    return datetime.datetime.now()
