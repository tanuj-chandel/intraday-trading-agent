from typing import Dict
from app.core.config import settings

class IndianBrokerageCalculator:
    """
    Calculates exact statutory and broker charges for NSE Intraday Equity trades.
    Includes:
    - Brokerage (e.g. ₹20 flat or 0.03% per order, whichever is lower)
    - STT (Securities Transaction Tax) - 0.025% on Sell side
    - Exchange Turnover Charges - 0.00345%
    - SEBI Turnover Charges - ₹10 per crore (0.0001%)
    - GST - 18% on (Brokerage + Exchange turnover charges + SEBI charges)
    - Stamp Duty - 0.003% on Buy side
    """

    @classmethod
    def calculate_intraday_charges(
        cls,
        buy_price: float,
        sell_price: float,
        quantity: int
    ) -> Dict[str, float]:
        buy_turnover = buy_price * quantity
        sell_turnover = sell_price * quantity
        total_turnover = buy_turnover + sell_turnover

        # 1. Brokerage (Zerodha/Groww style: min of ₹20 or 0.03% per leg)
        buy_brokerage = min(settings.BROKERAGE_PER_ORDER, buy_turnover * settings.BROKERAGE_PCT)
        sell_brokerage = min(settings.BROKERAGE_PER_ORDER, sell_turnover * settings.BROKERAGE_PCT)
        total_brokerage = buy_brokerage + sell_brokerage

        # 2. STT (Intraday equity: 0.025% on sell leg)
        stt = sell_turnover * settings.STT_PCT_SELL

        # 3. Exchange Turnover Charges (0.00345% on both legs)
        exchange_charges = total_turnover * settings.EXCHANGE_TURNOVER_PCT

        # 4. SEBI Charges
        sebi_charges = total_turnover * settings.SEBI_CHARGES_PCT

        # 5. GST (18% on Brokerage + Exchange + SEBI)
        taxable_services = total_brokerage + exchange_charges + sebi_charges
        gst = taxable_services * settings.GST_PCT_ON_CHARGES

        # 6. Stamp Duty (0.003% on buy leg)
        stamp_duty = buy_turnover * settings.STAMP_DUTY_PCT_BUY

        total_charges = round(total_brokerage + stt + exchange_charges + sebi_charges + gst + stamp_duty, 2)

        return {
            "brokerage": round(total_brokerage, 2),
            "stt": round(stt, 2),
            "exchange_charges": round(exchange_charges, 2),
            "sebi_charges": round(sebi_charges, 2),
            "gst": round(gst, 2),
            "stamp_duty": round(stamp_duty, 2),
            "total_charges": total_charges
        }
