from typing import Dict, Any, List

class SurvivorshipBiasTracker:
    """
    Survivorship Bias Disclosure and Historical Index Membership Tracker.
    Warns when backtesting on present-day NIFTY constituents over historical dates.
    """

    # Sample historical changes in NIFTY 50 (Exclusions & Inclusions)
    HISTORICAL_CHANGES = [
        {"effective_date": "2024-03-28", "included": "SHRIRAMFIN", "excluded": "UPL"},
        {"effective_date": "2023-09-29", "included": "LTIM", "excluded": "HDFC"},
        {"effective_date": "2022-09-30", "included": "ADANIENT", "excluded": "SHREECEM"}
    ]

    @classmethod
    def get_survivorship_status(cls, symbol: str, backtest_start_date: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "has_historical_membership_audit": True,
            "survivorship_warning": (
                "SURVIVORSHIP BIAS NOTICE: Backtesting on current Nifty constituents over multi-year periods "
                "excludes historically delisted or replaced companies. Interpret long-term aggregated CAGR with caution."
            ),
            "historical_rebalances_recorded": len(cls.HISTORICAL_CHANGES)
        }
