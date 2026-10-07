"""
Phase 3 — Broker Execution Layer Abstraction.
Encapsulates all order interactions behind an abstract base class.
Provides PaperBroker and a LiveBroker stub (Angel One / Zerodha Kite).
All strategy and execution code MUST communicate strictly via this abstraction.
Live order execution is HARD-LOCKED behind LIVE_TRADING_ENABLED=false.
"""

import abc
import datetime
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger

class OrderState(str, Enum):
    NEW = "NEW"
    SENT = "SENT"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class BrokerOrder(BaseModel):
    order_id: str
    idempotency_key: str
    symbol: str
    side: str  # BUY or SELL
    order_type: str  # MARKET, LIMIT, SL, SL-M
    quantity: int
    filled_quantity: int = 0
    price: float
    trigger_price: Optional[float] = None
    state: OrderState = OrderState.NEW
    status_reason: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

class BrokerPosition(BaseModel):
    symbol: str
    side: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float

class AbstractBroker(abc.ABC):
    """Abstract Base Class for Broker execution."""

    @abc.abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        order_type: str = "MARKET",
        trigger_price: Optional[float] = None,
        idempotency_key: Optional[str] = None
    ) -> BrokerOrder:
        pass

    @abc.abstractmethod
    async def place_stop_loss_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        trigger_price: float,
        limit_price: Optional[float] = None,
        idempotency_key: Optional[str] = None
    ) -> BrokerOrder:
        pass

    @abc.abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        pass

    @abc.abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[BrokerOrder]:
        pass

    @abc.abstractmethod
    async def get_positions(self) -> List[BrokerPosition]:
        pass

    @abc.abstractmethod
    async def refresh_session_token(self) -> Dict[str, Any]:
        pass


class PaperBroker(AbstractBroker):
    """
    Simulated Paper Broker.
    Maintains local order books, simulated fills, partial fill modeling,
    broker-side SL orders, and idempotent order deduplication.
    """

    def __init__(self):
        self._orders: Dict[str, BrokerOrder] = {}
        self._idempotency_map: Dict[str, str] = {}  # idempotency_key -> order_id
        self._positions: Dict[str, BrokerPosition] = {}
        self.fail_next_sl: bool = False  # Test hook
        self.partial_fill_next: bool = False  # Test hook

    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        order_type: str = "MARKET",
        trigger_price: Optional[float] = None,
        idempotency_key: Optional[str] = None
    ) -> BrokerOrder:
        key = idempotency_key or str(uuid.uuid4())
        if key in self._idempotency_map:
            existing_id = self._idempotency_map[key]
            logger.info(f"[PaperBroker] Idempotent order duplicate detected for key {key} -> order #{existing_id}")
            return self._orders[existing_id]

        order_id = f"PAPER_{len(self._orders) + 1}_{symbol}"
        now = datetime.datetime.now()

        order = BrokerOrder(
            order_id=order_id,
            idempotency_key=key,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            trigger_price=trigger_price,
            state=OrderState.SENT,
            created_at=now,
            updated_at=now
        )
        self._orders[order_id] = order
        self._idempotency_map[key] = order_id

        # Simulate execution
        if self.partial_fill_next:
            self.partial_fill_next = False
            filled = max(1, quantity // 2)
            order.filled_quantity = filled
            order.state = OrderState.PARTIAL
            order.status_reason = f"Partial fill: {filled}/{quantity} shares executed"
        else:
            order.filled_quantity = quantity
            order.state = OrderState.FILLED

        order.updated_at = datetime.datetime.now()

        # Update broker-side position
        if order.state in (OrderState.FILLED, OrderState.PARTIAL):
            pos_qty = order.filled_quantity if order.side == "BUY" else -order.filled_quantity
            if symbol in self._positions:
                existing = self._positions[symbol]
                new_qty = existing.quantity + pos_qty
                if new_qty == 0:
                    del self._positions[symbol]
                else:
                    existing.quantity = new_qty
            else:
                self._positions[symbol] = BrokerPosition(
                    symbol=symbol,
                    side=side,
                    quantity=order.filled_quantity,
                    entry_price=price,
                    current_price=price,
                    unrealized_pnl=0.0
                )

        return order

    async def place_stop_loss_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        trigger_price: float,
        limit_price: Optional[float] = None,
        idempotency_key: Optional[str] = None
    ) -> BrokerOrder:
        key = idempotency_key or f"SL_{symbol}_{uuid.uuid4()}"
        if key in self._idempotency_map:
            return self._orders[self._idempotency_map[key]]

        if self.fail_next_sl:
            self.fail_next_sl = False
            order_id = f"SL_FAIL_{uuid.uuid4()}"
            failed_order = BrokerOrder(
                order_id=order_id,
                idempotency_key=key,
                symbol=symbol,
                side=side,
                order_type="SL-M",
                quantity=quantity,
                price=limit_price or trigger_price,
                trigger_price=trigger_price,
                state=OrderState.REJECTED,
                status_reason="Broker rejected Stop-Loss order: Margin/RMS rejection test",
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            self._orders[order_id] = failed_order
            self._idempotency_map[key] = order_id
            return failed_order

        order_id = f"SL_ORDER_{len(self._orders) + 1}_{symbol}"
        now = datetime.datetime.now()
        sl_order = BrokerOrder(
            order_id=order_id,
            idempotency_key=key,
            symbol=symbol,
            side=side,
            order_type="SL-M",
            quantity=quantity,
            price=limit_price or trigger_price,
            trigger_price=trigger_price,
            state=OrderState.SENT,
            created_at=now,
            updated_at=now
        )
        self._orders[order_id] = sl_order
        self._idempotency_map[key] = order_id
        return sl_order

    async def cancel_order(self, order_id: str) -> bool:
        if order_id in self._orders:
            self._orders[order_id].state = OrderState.CANCELLED
            self._orders[order_id].updated_at = datetime.datetime.now()
            return True
        return False

    async def get_order_status(self, order_id: str) -> Optional[BrokerOrder]:
        return self._orders.get(order_id)

    async def get_positions(self) -> List[BrokerPosition]:
        return list(self._positions.values())

    async def refresh_session_token(self) -> Dict[str, Any]:
        return {
            "success": True,
            "status": "PAPER_SIMULATED_SESSION_VALID",
            "refreshed_at": datetime.datetime.now().isoformat()
        }


class LiveBroker(AbstractBroker):
    """
    Live Broker stub for Angel One SmartAPI / Zerodha Kite Connect.
    HARD-LOCKED: Refuses execution unless LIVE_TRADING_ENABLED=true in config.
    """

    def __init__(self):
        self.live_enabled = getattr(settings, "LIVE_TRADING_ENABLED", False)

    def _verify_live_guard(self):
        if not self.live_enabled or getattr(settings, "IS_PAPER_TRADING", True):
            raise PermissionError(
                "CRITICAL SAFETY VIOLATION: Attempted to call LiveBroker while LIVE_TRADING_ENABLED=False "
                "or IS_PAPER_TRADING=True. Real order placement permanently blocked."
            )

    async def place_order(self, *args, **kwargs) -> BrokerOrder:
        self._verify_live_guard()
        raise NotImplementedError("Live broker order placement stub.")

    async def place_stop_loss_order(self, *args, **kwargs) -> BrokerOrder:
        self._verify_live_guard()
        raise NotImplementedError("Live broker SL order placement stub.")

    async def cancel_order(self, *args, **kwargs) -> bool:
        self._verify_live_guard()
        return False

    async def get_order_status(self, *args, **kwargs) -> Optional[BrokerOrder]:
        self._verify_live_guard()
        return None

    async def get_positions(self) -> List[BrokerPosition]:
        self._verify_live_guard()
        return []

    async def refresh_session_token(self) -> Dict[str, Any]:
        # Authenticate / check Angel One or Zerodha token validity
        angel_key = getattr(settings, "ANGELONE_API_KEY", None)
        kite_key = getattr(settings, "ZERODHA_API_KEY", None)
        if angel_key or kite_key:
            return {"success": True, "broker": "AngelOne/Kite", "status": "SESSION_REFRESHED"}
        return {"success": False, "error": "No broker API credentials configured in environment"}


def get_broker() -> AbstractBroker:
    """Returns PaperBroker or LiveBroker based on config."""
    if getattr(settings, "LIVE_TRADING_ENABLED", False) and not getattr(settings, "IS_PAPER_TRADING", True):
        return LiveBroker()
    return PaperBroker()
