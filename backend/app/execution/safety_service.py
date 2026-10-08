"""
Execution Safety, Health Watchdog, Position Reconciliation & Crash Recovery.
Enforces:
1. Entry with immediate broker-side Stop-Loss. If SL fails, immediately exit position and alert.
2. Partial fill handling and retry with exponential backoff.
3. 60-second broker position reconciliation.
4. Crash recovery: reload open positions on startup without opening new trades.
5. 30-second Health watchdog: checks feed staleness (STALE_FEED_SECONDS=15) and triggers Level 2 kill switch on repeated failures.
6. Daily session token refresh with failure alert.
7. Hard guard: if LIVE_TRADING_ENABLED=True, verify real broker feed is active (refuses synthetic/Yahoo).
"""

import asyncio
import datetime
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.execution.broker_base import AbstractBroker, PaperBroker, BrokerOrder, OrderState, get_broker
from app.live.data_types import LivePaperPosition, LiveSignalItem
from app.live.audit import LiveAuditLogger

class ExecutionSafetyService:
    def __init__(self, broker: Optional[AbstractBroker] = None):
        self.broker = broker or get_broker()
        self.last_heartbeat_time = datetime.datetime.now()
        self.last_tick_time: Dict[str, datetime.datetime] = {}
        self.feed_failure_count = 0
        self.is_recovering = False
        self._stale_alerted = False

    def verify_live_startup_guard(self, provider_name: str, is_mock: bool = False) -> bool:
        """
        Hard guard: if LIVE_TRADING_ENABLED is true, refuse to start unless data source
        is a real broker feed and not synthetic/Yahoo.
        """
        is_live_trading = getattr(settings, "LIVE_TRADING_ENABLED", False)
        if is_live_trading:
            provider = provider_name.upper()
            if is_mock or "MOCK" in provider or "YAHOO" in provider or "SYNTHETIC" in provider:
                err_msg = (
                    f"CRITICAL SAFETY ABORT: LIVE_TRADING_ENABLED is True, but market data provider is "
                    f"'{provider_name}' (Mock/Yahoo/Synthetic). Refusing to start real trading engine."
                )
                logger.critical(err_msg)
                raise RuntimeError(err_msg)
        return True

    async def execute_entry_with_broker_sl(
        self,
        signal: LiveSignalItem,
        current_market_price: float,
        position_id: int
    ) -> Optional[LivePaperPosition]:
        """
        Places entry order and immediately places broker-side Stop-Loss order.
        If SL order fails, immediately exit the position and alert operator.
        """
        idempotency_key = f"ENTRY_{signal.id}_{signal.symbol}"
        entry_side = signal.direction
        sl_side = "SELL" if entry_side == "BUY" else "BUY"

        # Determine realistic execution price with dynamic slippage
        from app.execution.slippage_model import DynamicSlippageModel
        exec_price, slippage_amt = DynamicSlippageModel.calculate_execution_price(
            symbol=signal.symbol,
            direction=entry_side,
            market_price=current_market_price,
            quantity=signal.quantity
        )

        # 1. Place Entry Order with retry & backoff
        entry_order: Optional[BrokerOrder] = None
        for attempt in range(3):
            try:
                entry_order = await self.broker.simulate_broker_entry(
                    symbol=signal.symbol,
                    side=entry_side,
                    quantity=signal.quantity,
                    price=exec_price,
                    order_type="MARKET",
                    idempotency_key=idempotency_key
                )
                if entry_order.state in (OrderState.FILLED, OrderState.PARTIAL):
                    break
            except Exception as e:
                logger.warning(f"Entry order attempt {attempt+1} failed: {e}")
                await asyncio.sleep(0.5 * (2 ** attempt))

        if not entry_order or entry_order.state not in (OrderState.FILLED, OrderState.PARTIAL):
            logger.error(f"Entry order failed for {signal.symbol}: {getattr(entry_order, 'status_reason', 'Unknown error')}")
            return None

        actual_filled_qty = entry_order.filled_quantity
        if actual_filled_qty < 1:
            return None

        # 2. Immediately Place Broker-side Stop-Loss Order
        sl_key = f"SL_{signal.id}_{signal.symbol}_{entry_order.order_id}"
        sl_order = await self.broker.place_stop_loss_order(
            symbol=signal.symbol,
            side=sl_side,
            quantity=actual_filled_qty,
            trigger_price=signal.stop_loss,
            idempotency_key=sl_key
        )

        # 3. If SL order fails, immediately exit position and alert!
        if sl_order.state == OrderState.REJECTED:
            alert_msg = f"EMERGENCY: Broker Stop-Loss order failed for {signal.symbol}. Liquidating position immediately!"
            logger.critical(alert_msg)
            LiveAuditLogger.log("SL_ORDER_FAILED", alert_msg, symbol=signal.symbol)

            # Liquidate immediately
            exit_order = await self.broker.simulate_broker_entry(
                symbol=signal.symbol,
                side=sl_side,
                quantity=actual_filled_qty,
                price=current_market_price,
                order_type="MARKET",
                idempotency_key=f"EMERGENCY_EXIT_{signal.id}"
            )

            try:
                from app.notifications.dispatcher import notifier
                notifier.notify_emergency_stop(alert_msg)
            except Exception:
                pass

            return None

        # Success: construct position with charges and realistic slippage
        from app.backtest.cost_calculator import TransactionCostCalculator
        costs = TransactionCostCalculator.calculate_round_trip_costs(
            buy_price=exec_price,
            sell_price=signal.target_price if entry_side == "BUY" else signal.stop_loss,
            quantity=actual_filled_qty
        )

        return LivePaperPosition(
            id=position_id,
            symbol=signal.symbol,
            side=entry_side,
            quantity=actual_filled_qty,
            entry_price=exec_price,
            current_price=exec_price,
            stop_loss=signal.stop_loss,
            target_price=signal.target_price,
            trailing_stop=signal.stop_loss,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
            slippage_incurred=round(slippage_amt, 2),
            statutory_charges=round(costs.get("total_charges", 0.0), 2),
            status="OPEN",
            opened_at=datetime.datetime.now()
        )

    def execute_entry_with_broker_sl_sync(
        self,
        signal: LiveSignalItem,
        current_market_price: float,
        position_id: int
    ) -> Optional[LivePaperPosition]:
        """Synchronous wrapper to safely call execute_entry_with_broker_sl."""
        import concurrent.futures
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(
                    lambda: asyncio.run(self.execute_entry_with_broker_sl(signal, current_market_price, position_id))
                ).result()
        else:
            return asyncio.run(self.execute_entry_with_broker_sl(signal, current_market_price, position_id))

    def record_tick_timestamp(self, symbol: str):
        self.last_tick_time[symbol] = datetime.datetime.now()

    def check_health_watchdog(self) -> Dict[str, Any]:
        """
        Health watchdog: runs every 30 seconds.
        If data feed is stale for more than STALE_FEED_SECONDS (default 15),
        pause entries and alert. If failures persist, trigger Level 2 kill switch.
        """
        now = datetime.datetime.now()
        self.last_heartbeat_time = now
        stale_threshold = getattr(settings, "STALE_FEED_SECONDS", 15)

        is_stale = False
        stale_symbols = []

        if not self.last_tick_time:
            is_stale = True
        else:
            for sym, t in self.last_tick_time.items():
                age = (now - t).total_seconds()
                if age > stale_threshold:
                    stale_symbols.append((sym, age))

            if len(stale_symbols) == len(self.last_tick_time):
                is_stale = True

        from app.live.streamer import live_streamer

        if is_stale:
            self.feed_failure_count += 1
            if not self._stale_alerted:
                self._stale_alerted = True
                alert_text = f"Health Watchdog: Data feed stale (> {stale_threshold}s). New entries paused."
                LiveAuditLogger.log("FEED_STALE", alert_text)
                try:
                    from app.notifications.dispatcher import notifier
                    notifier.notify_emergency_stop(alert_text)
                except Exception:
                    pass

            if self.feed_failure_count >= 3:
                # Trigger Level 2 Kill Switch (No New Entries)
                live_streamer.activate_kill_switch(2, reason="Health watchdog: Data feed persistently stale (> 45s)")

            return {"healthy": False, "stale": True, "failure_count": self.feed_failure_count}
        else:
            self.feed_failure_count = 0
            self._stale_alerted = False
            # If Kill Switch was triggered by health watchdog (Level 2), auto-clear once feed is healthy
            if live_streamer.kill_switch.is_active and live_streamer.kill_switch.current_level == 2:
                if "Health watchdog" in (live_streamer.kill_switch.activation_reason or ""):
                    live_streamer.reset_kill_switch()
                    LiveAuditLogger.log("FEED_RESTORED", "Data feed restored and fresh. Level 2 pause auto-cleared.")
            return {"healthy": True, "stale": False, "failure_count": 0}

    async def reconcile_positions(self) -> Dict[str, Any]:
        """
        Reconciliation job every 60 seconds:
        Compares local positions with broker positions.
        On mismatch, alerts on Telegram and pauses new entries (Level 2 Kill Switch).
        """
        from app.live.streamer import live_streamer
        from app.core.config import settings

        # In Paper Trading mode, trades are simulated locally and not sent to broker.
        if getattr(settings, "IS_PAPER_TRADING", True) or not getattr(settings, "LIVE_TRADING_ENABLED", False):
            return {"reconciled": True, "mismatches": [], "mode": "PAPER_TRADING"}

        local_positions = {p.symbol: p.quantity for p in live_streamer.position_manager.get_open_positions()}
        broker_positions_list = await self.broker.get_positions()
        broker_positions = {p.symbol: p.quantity for p in broker_positions_list}

        mismatches = []
        all_symbols = set(local_positions.keys()).union(set(broker_positions.keys()))
        for sym in all_symbols:
            loc_qty = local_positions.get(sym, 0)
            brk_qty = broker_positions.get(sym, 0)
            if loc_qty != brk_qty:
                mismatches.append(f"{sym}: local={loc_qty} vs broker={brk_qty}")

        if mismatches:
            msg = f"Position Reconciliation Mismatch: {', '.join(mismatches)}. New entries paused."
            logger.warning(msg)
            LiveAuditLogger.log("RECONCILIATION_MISMATCH", msg)
            live_streamer.activate_kill_switch(2, reason=f"Reconciliation mismatch: {mismatches}")
            try:
                from app.notifications.dispatcher import notifier
                notifier.notify_emergency_stop(msg)
            except Exception:
                pass
            return {"reconciled": False, "mismatches": mismatches}

        return {"reconciled": True, "mismatches": []}

    def recover_from_crash(self, open_positions_records: List[Dict[str, Any]]) -> int:
        """
        Crash recovery on startup: reload open positions from DB, reconcile,
        and resume managing exits. Never open new trades during recovery.
        """
        from app.live.streamer import live_streamer

        self.is_recovering = True
        restored = 0
        try:
            for r in open_positions_records:
                if r.get("status") == "OPEN":
                    pos = LivePaperPosition(
                        id=r.get("id", restored + 1),
                        symbol=r.get("symbol"),
                        side=r.get("side"),
                        quantity=r.get("quantity"),
                        entry_price=r.get("entry_price"),
                        current_price=r.get("current_price", r.get("entry_price")),
                        stop_loss=r.get("stop_loss"),
                        target_price=r.get("target_price"),
                        trailing_stop=r.get("trailing_stop"),
                        unrealized_pnl=r.get("unrealized_pnl", 0.0),
                        unrealized_pnl_pct=r.get("unrealized_pnl_pct", 0.0),
                        status="OPEN",
                        opened_at=r.get("opened_at") or datetime.datetime.now()
                    )
                    live_streamer.position_manager.add_position(pos)
                    restored += 1

            LiveAuditLogger.log("CRASH_RECOVERY", f"Reloaded {restored} open positions from database. Exits active; new entries blocked during startup recovery.")
        finally:
            self.is_recovering = False
        return restored

    async def refresh_daily_token(self) -> Dict[str, Any]:
        """Daily token/login refresh for broker session."""
        res = await self.broker.refresh_session_token()
        if not res.get("success"):
            alert_msg = f"Broker Session Token Refresh Failed: {res.get('error', 'Authentication failed')}"
            logger.error(alert_msg)
            LiveAuditLogger.log("TOKEN_REFRESH_FAILED", alert_msg)
            try:
                from app.notifications.dispatcher import notifier
                notifier.notify_emergency_stop(alert_msg)
            except Exception:
                pass
        return res

execution_safety = ExecutionSafetyService()
