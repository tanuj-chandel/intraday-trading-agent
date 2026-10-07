import datetime
from typing import Dict, Any, Optional
from app.data.data_quality import DataQualityService

class GiftNiftyProvider:
    """
    GIFT Nifty (NSE IX) intelligence provider for Indian market pre-open gap estimations.
    Operates strictly via authorized sources, manual input, or simulation. (No unauthorized web scraping).
    """
    _manual_gift_nifty_price: Optional[float] = None
    _manual_update_time: Optional[datetime.datetime] = None

    @classmethod
    def set_manual_price(cls, price: float):
        cls._manual_gift_nifty_price = price
        cls._manual_update_time = datetime.datetime.now()
        DataQualityService.record_update(
            dataset_name="GIFT_NIFTY",
            source="MANUAL_INPUT",
            status="LIVE",
            latency_ms=0
        )

    @classmethod
    def get_gap_analysis(cls, spot_nifty_close: float = 24800.0) -> Dict[str, Any]:
        now = datetime.datetime.now()
        
        # 1. Check if operator manually specified GIFT Nifty level
        if cls._manual_gift_nifty_price and cls._manual_update_time:
            age = (now - cls._manual_update_time).total_seconds()
            if age < 7200:  # Valid for 2 hours
                gift_price = cls._manual_gift_nifty_price
                source_label = "OPERATOR_MANUAL_INPUT"
                status_label = "LIVE"
            else:
                gift_price = spot_nifty_close + 65.0
                source_label = "MOCK_ESTIMATE"
                status_label = "MOCK"
        else:
            # Simulated institutional premium based on global sentiment drift
            gift_price = round(spot_nifty_close + 55.50, 2)
            source_label = "SIMULATED_GIFT_FEED"
            status_label = "MOCK"

        DataQualityService.record_update(
            dataset_name="GIFT_NIFTY",
            source=source_label,
            status=status_label,
            latency_ms=30
        )

        gap_points = round(gift_price - spot_nifty_close, 2)
        gap_pct = round((gap_points / spot_nifty_close) * 100.0, 2)

        if gap_pct >= 0.5:
            gap_direction = "GAP_UP"
            gap_magnitude = "STRONG"
        elif gap_pct >= 0.15:
            gap_direction = "GAP_UP"
            gap_magnitude = "MODERATE"
        elif gap_pct <= -0.5:
            gap_direction = "GAP_DOWN"
            gap_magnitude = "STRONG"
        elif gap_pct <= -0.15:
            gap_direction = "GAP_DOWN"
            gap_magnitude = "MODERATE"
        else:
            gap_direction = "FLAT"
            gap_magnitude = "MILD"

        return {
            "gift_nifty_price": gift_price,
            "spot_nifty_close": spot_nifty_close,
            "gap_points": gap_points,
            "gap_pct": gap_pct,
            "gap_direction": gap_direction,
            "gap_magnitude": gap_magnitude,
            "source": source_label,
            "data_status": status_label,
            "timestamp": now.isoformat()
        }
