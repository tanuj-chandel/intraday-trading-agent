from typing import Optional, Tuple
from app.data.universe import EXPANDED_INDIAN_UNIVERSE
from app.core.config import settings

class DynamicSlippageModel:
    """
    Dynamic Slippage Model for Indian Equities Execution Realism.
    Uses next tick price after approval and scales slippage by:
    1. Bid-ask spread of the stock
    2. Liquidity tier (VERY_HIGH, HIGH, MEDIUM, LOW)
    """

    _LIQUIDITY_MAP = {s.symbol.upper(): s.liquidity_classification for s in EXPANDED_INDIAN_UNIVERSE}

    _TIER_SLIPPAGE_PCT = {
        "VERY_HIGH": 0.0002,  # 0.02%
        "HIGH": 0.0005,       # 0.05%
        "MEDIUM": 0.0010,     # 0.10%
        "LOW": 0.0020         # 0.20%
    }

    @classmethod
    def get_liquidity_tier(cls, symbol: str) -> str:
        sym = symbol.upper().replace(".NS", "")
        return cls._LIQUIDITY_MAP.get(sym, "HIGH")

    @classmethod
    def get_slippage_pct(cls, symbol: str) -> float:
        tier = cls.get_liquidity_tier(symbol)
        return cls._TIER_SLIPPAGE_PCT.get(tier, 0.0005)

    @classmethod
    def calculate_execution_price(
        cls,
        symbol: str,
        direction: str,
        market_price: float,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        quantity: int = 1
    ) -> Tuple[float, float]:
        """
        Determines the realistic fill price and slippage amount.
        Returns: (fill_price: float, slippage_incurred: float)
        """
        if not getattr(settings, "DYNAMIC_SLIPPAGE_ENABLED", True):
            # Fallback to fixed 0.05%
            pct = getattr(settings, "SLIPPAGE_PCT", 0.0005)
            fill_price = round(market_price * (1.0 + pct) if direction == "BUY" else market_price * (1.0 - pct), 2)
            slippage = abs(fill_price - market_price) * quantity
            return fill_price, round(slippage, 2)

        tier = cls.get_liquidity_tier(symbol)
        tier_pct = cls._TIER_SLIPPAGE_PCT.get(tier, 0.0005)

        # Spread scaling
        spread_pct = 0.0003  # default 0.03%
        if bid and ask and ask > bid and market_price > 0:
            spread_pct = (ask - bid) / market_price

        # Half-spread + liquidity tier slippage
        total_slippage_pct = (spread_pct / 2.0) + tier_pct

        if direction == "BUY":
            # For BUY: use ask if available, or market price + slippage
            base = ask if (ask and ask >= market_price) else market_price
            fill_price = round(base * (1.0 + total_slippage_pct), 2)
        else:
            # For SELL: use bid if available, or market price - slippage
            base = bid if (bid and bid <= market_price) else market_price
            fill_price = round(base * (1.0 - total_slippage_pct), 2)

        slippage = abs(fill_price - market_price) * quantity
        return fill_price, round(slippage, 2)
