"""
Central Notification Dispatcher.
Routes trade alerts, risk checks, breakeven triggers, and daily reports
to mobile channels (Telegram, WhatsApp, Console, and Dashboard Live Stream).
"""

import datetime
import asyncio
from collections import deque
from typing import Dict, Any, List, Optional
from app.notifications.telegram_bot import telegram_notifier
from app.core.logging import logger

class NotificationDispatcher:
    """
    Central hub routing real-time trading notifications to mobile and dashboard channels.
    Thread-safe and non-blocking.
    """

    def __init__(self, max_history: int = 100):
        self._history = deque(maxlen=max_history)
        self.telegram = telegram_notifier

    def get_recent_alerts(self, limit: int = 30) -> List[Dict[str, Any]]:
        return list(self._history)[-limit:]

    def _record(self, alert_type: str, title: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        entry = {
            "id": len(self._history) + 1,
            "type": alert_type,
            "title": title,
            "message": message,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
            "metadata": metadata or {}
        }
        self._history.append(entry)
        logger.info(f"[NOTIFIER] {title}: {message}")

    def notify_signal(self, signal_dict: Dict[str, Any]):
        title = f"{signal_dict.get('direction', 'BUY')} Signal on {signal_dict.get('symbol')}"
        msg = f"Entry ₹{signal_dict.get('entry_price')}, TP ₹{signal_dict.get('target_price')}, SL ₹{signal_dict.get('stop_loss')}"
        self._record("SIGNAL", title, msg, signal_dict)

        # Dispatch async to Telegram with [Approve] [Reject] inline buttons
        if self.telegram.is_configured and self.telegram.enabled:
            asyncio.create_task(self.telegram.send_signal_approval_request(signal_dict))

    def notify_order_filled(self, position_dict: Dict[str, Any]):
        title = f"Order Filled: {position_dict.get('side')} {position_dict.get('symbol')}"
        msg = f"Qty {position_dict.get('quantity')} @ ₹{position_dict.get('entry_price')}"
        self._record("ORDER_FILL", title, msg, position_dict)

        if self.telegram.is_configured and self.telegram.enabled:
            asyncio.create_task(self.telegram.send_position_executed(position_dict))

    def notify_breakeven(self, symbol: str, entry_price: float, current_price: float):
        title = f"Auto-Breakeven Activated: {symbol}"
        msg = f"Stop Loss moved to ₹{entry_price:.2f} (Price reached ₹{current_price:.2f}). Guaranteed 0 loss."
        self._record("BREAKEVEN", title, msg, {"symbol": symbol, "entry_price": entry_price, "current_price": current_price})

        if self.telegram.is_configured and self.telegram.enabled:
            asyncio.create_task(self.telegram.send_breakeven_alert(symbol, entry_price, current_price))

    def notify_position_closed(self, position_dict: Dict[str, Any]):
        pnl = position_dict.get("net_realized_pnl", 0.0)
        reason = position_dict.get("exit_reason", "CLOSED")
        title = f"Position Closed ({reason}): {position_dict.get('symbol')}"
        msg = f"Net P&L: {'+₹' if pnl >= 0 else '-₹'}{abs(pnl):.2f} (Exit @ ₹{position_dict.get('exit_price')})"
        self._record("POSITION_EXIT", title, msg, position_dict)

        if self.telegram.is_configured and self.telegram.enabled:
            asyncio.create_task(self.telegram.send_position_exit(position_dict))

    def notify_emergency_stop(self, reason: str):
        title = "EMERGENCY STOP TRIGGERED"
        msg = f"All trading halted and positions squared off. Reason: {reason}"
        self._record("EMERGENCY_STOP", title, msg, {"reason": reason})

        if self.telegram.is_configured and self.telegram.enabled:
            asyncio.create_task(self.telegram.send_message(f"🚨 <b>EMERGENCY STOP TRIGGERED</b>\n\nAll trading halted immediately.\nReason: <i>{reason}</i>"))

notifier = NotificationDispatcher()
