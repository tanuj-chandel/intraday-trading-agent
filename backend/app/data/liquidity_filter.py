from typing import List, Dict, Any
from app.core.config import settings
from app.data.universe import IndianStockMetadata

class LiquidityFilter:
    """
    Configurable Liquidity & Quality Filter for Indian Stock Market.
    Ensures only highly liquid, institutional-grade stocks are selected for intraday setups.
    """

    def __init__(
        self,
        min_avg_daily_volume: int = settings.MIN_AVG_DAILY_VOLUME,
        min_daily_turnover_inr: float = settings.MIN_DAILY_TURNOVER_INR,
        min_price: float = settings.MIN_STOCK_PRICE,
        max_price: float = settings.MAX_STOCK_PRICE,
        max_spread_pct: float = settings.MAX_BID_ASK_SPREAD_PCT
    ):
        self.min_avg_daily_volume = min_avg_daily_volume
        self.min_daily_turnover_inr = min_daily_turnover_inr
        self.min_price = min_price
        self.max_price = max_price
        self.max_spread_pct = max_spread_pct

    def evaluate_stock(
        self,
        stock: IndianStockMetadata,
        current_price: float,
        current_volume: float = 0.0,
        bid_ask_spread_pct: float = 0.0005
    ) -> Dict[str, Any]:
        reasons = []
        passed = True

        # 1. Active status
        if not stock.is_active:
            passed = False
            reasons.append("Stock is marked inactive")

        # 2. Average Daily Volume
        if stock.avg_daily_volume < self.min_avg_daily_volume:
            passed = False
            reasons.append(f"Avg daily volume ({stock.avg_daily_volume:,.0f}) below min threshold ({self.min_avg_daily_volume:,.0f})")

        # 3. Turnover (Turnover in Cr * 1e7)
        turnover_inr = stock.avg_daily_turnover_cr * 10000000.0
        if turnover_inr < self.min_daily_turnover_inr:
            passed = False
            reasons.append(f"Turnover (₹{stock.avg_daily_turnover_cr:.1f} Cr) below min threshold (₹{self.min_daily_turnover_inr/1e7:.1f} Cr)")

        # 4. Price range
        if current_price < self.min_price:
            passed = False
            reasons.append(f"Price ₹{current_price:.2f} below min allowable price ₹{self.min_price:.2f} (penny stock protection)")
        elif current_price > self.max_price:
            passed = False
            reasons.append(f"Price ₹{current_price:.2f} exceeds max price limit ₹{self.max_price:.2f}")

        # 5. Bid-Ask Spread check
        if bid_ask_spread_pct > self.max_spread_pct:
            passed = False
            reasons.append(f"Spread {bid_ask_spread_pct*100:.3f}% exceeds maximum allowable spread {self.max_spread_pct*100:.3f}%")

        return {
            "symbol": stock.symbol,
            "passed": passed,
            "reasons": reasons,
            "liquidity_classification": stock.liquidity_classification,
            "avg_turnover_cr": stock.avg_daily_turnover_cr
        }

    def filter_universe(
        self,
        universe: List[IndianStockMetadata],
        quotes: Dict[str, float]
    ) -> List[IndianStockMetadata]:
        eligible = []
        for stock in universe:
            price = quotes.get(stock.symbol, 1000.0)
            res = self.evaluate_stock(stock, current_price=price)
            if res["passed"]:
                eligible.append(stock)
        return eligible
