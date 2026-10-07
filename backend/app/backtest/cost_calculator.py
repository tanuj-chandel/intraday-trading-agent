from typing import Dict, Any
from app.core.config import settings

class TransactionCostConfig:
    def __init__(
        self,
        brokerage_per_order: float = settings.BROKERAGE_PER_ORDER,
        brokerage_pct: float = settings.BROKERAGE_PCT,
        stt_pct_sell: float = settings.STT_PCT_SELL,
        exchange_turnover_pct: float = settings.EXCHANGE_TURNOVER_PCT,
        sebi_charges_pct: float = settings.SEBI_CHARGES_PCT,
        gst_pct: float = settings.GST_PCT_ON_CHARGES,
        stamp_duty_pct_buy: float = settings.STAMP_DUTY_PCT_BUY,
        slippage_pct: float = settings.SLIPPAGE_PCT
    ):
        self.brokerage_per_order = brokerage_per_order
        self.brokerage_pct = brokerage_pct
        self.stt_pct_sell = stt_pct_sell
        self.exchange_turnover_pct = exchange_turnover_pct
        self.sebi_charges_pct = sebi_charges_pct
        self.gst_pct = gst_pct
        self.stamp_duty_pct_buy = stamp_duty_pct_buy
        self.slippage_pct = slippage_pct

class TransactionCostCalculator:
    """
    Dedicated Transaction Cost & Statutory Taxes Engine for Indian Intraday Equities.
    Computes exact statutory taxes: STT, Exchange Fees, SEBI, GST, Stamp Duty, Brokerage, and Slippage.
    """

    @classmethod
    def apply_slippage(
        cls,
        price: float,
        side: str,  # "BUY" or "SELL"
        slippage_pct: float = 0.0005
    ) -> float:
        if side.upper() == "BUY":
            # Buy orders fill slightly higher due to ask spread
            return round(price * (1.0 + slippage_pct), 2)
        else:
            # Sell orders fill slightly lower due to bid spread
            return round(price * (1.0 - slippage_pct), 2)

    @classmethod
    def calculate_round_trip_costs(
        cls,
        buy_price: float,
        sell_price: float,
        quantity: int,
        config: TransactionCostConfig = None
    ) -> Dict[str, Any]:
        if config is None:
            config = TransactionCostConfig()

        buy_turnover = buy_price * quantity
        sell_turnover = sell_price * quantity
        total_turnover = buy_turnover + sell_turnover

        # 1. Brokerage (₹20 per order or 0.03%, whichever is lower)
        buy_brokerage = min(config.brokerage_per_order, buy_turnover * config.brokerage_pct)
        sell_brokerage = min(config.brokerage_per_order, sell_turnover * config.brokerage_pct)
        total_brokerage = round(buy_brokerage + sell_brokerage, 2)

        # 2. STT (0.025% on Intraday Equity Sell only)
        stt = round(sell_turnover * config.stt_pct_sell, 2)

        # 3. Exchange Turnover Charge (NSE: 0.00345%)
        exchange_charges = round(total_turnover * config.exchange_turnover_pct, 2)

        # 4. SEBI Turnover Charges (₹10 per crore)
        sebi_charges = round(total_turnover * config.sebi_charges_pct, 2)

        # 5. GST (18% on Brokerage + Exchange Charges)
        gst = round((total_brokerage + exchange_charges) * config.gst_pct, 2)

        # 6. Stamp Duty (0.003% on Buy side only)
        stamp_duty = round(buy_turnover * config.stamp_duty_pct_buy, 2)

        # Total Statutory and Brokerage Deductions
        total_charges = round(total_brokerage + stt + exchange_charges + sebi_charges + gst + stamp_duty, 2)

        return {
            "total_turnover": round(total_turnover, 2),
            "brokerage": total_brokerage,
            "stt": stt,
            "exchange_charges": exchange_charges,
            "sebi_charges": sebi_charges,
            "gst": gst,
            "stamp_duty": stamp_duty,
            "total_charges": total_charges,
            "breakdown_summary": f"Brokerage ₹{total_brokerage:.2f} + STT ₹{stt:.2f} + Exchange ₹{exchange_charges:.2f} + GST ₹{gst:.2f} + Stamp ₹{stamp_duty:.2f}"
        }
