"""
Telegram Bot Notification & Interactive Two-Way Control Engine for Indian Market Trading.
Delivers real-time trade signals with [Approve] [Reject] inline buttons,
handles operator commands (/status, /pnl, /positions, /pause, /resume, /close, /help),
and enforces strict TELEGRAM_ALLOWED_CHAT_ID security.
"""

import datetime
import asyncio
import httpx
from typing import Dict, Any, Optional, List, Union
from app.core.config import settings
from app.core.logging import logger

class TelegramNotifier:
    """
    Asynchronous Telegram Bot client for mobile notifications and interactive controls.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        allowed_chat_id: Optional[str] = None,
        enabled: Optional[bool] = None
    ):
        self.bot_token = bot_token or getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
        self.chat_id = chat_id or getattr(settings, "TELEGRAM_CHAT_ID", "") or ""
        self.allowed_chat_id = allowed_chat_id or getattr(settings, "TELEGRAM_ALLOWED_CHAT_ID", "") or self.chat_id
        self.enabled = enabled if enabled is not None else getattr(settings, "TELEGRAM_ENABLED", False)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self._last_update_id = 0
        self._is_paused = False

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id and self.bot_token != "your_bot_token_here")

    def is_chat_authorized(self, incoming_chat_id: Union[int, str]) -> bool:
        """
        Security: Accept commands and callbacks ONLY from TELEGRAM_ALLOWED_CHAT_ID / chat_id.
        Ignore everyone else silently.
        """
        if not self.allowed_chat_id:
            # Fall back to configured chat_id if allowed_chat_id not separately specified
            return str(incoming_chat_id) == str(self.chat_id)
        return str(incoming_chat_id) == str(self.allowed_chat_id)

    async def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
        target_chat_id: Optional[Union[str, int]] = None
    ) -> bool:
        """
        Sends an HTML formatted message to Telegram, optionally with inline keyboard buttons.
        """
        if not self.is_configured or not self.enabled:
            logger.debug(f"[Telegram Disabled/Unconfigured] Alert suppressed: {text[:80]}...")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": str(target_chat_id or self.chat_id),
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=8.0, verify=False) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return True
                else:
                    logger.warning(f"Telegram send failed (HTTP {resp.status_code}): {resp.text}")
                    return False
        except Exception as e:
            logger.warning(f"Telegram network error: {e}")
            return False

    async def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None) -> bool:
        """Acknowledges inline button clicks to dismiss client loading spinners."""
        if not self.is_configured:
            return False
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        try:
            async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                await client.post(url, json=payload)
                return True
        except Exception:
            return False

    async def send_signal_approval_request(self, signal: Dict[str, Any]) -> bool:
        """
        Sends a live trade signal alert with inline [Approve] and [Reject] buttons.
        Shows symbol, side, entry, SL, TP, qty, risk in INR, R:R, score, and reasons.
        """
        direction = signal.get("direction", "BUY")
        emoji = "🟢" if direction == "BUY" else "🔴"
        symbol = signal.get("symbol", "NIFTY")
        sig_id = signal.get("id", 0)
        entry = signal.get("entry_price", 0.0)
        sl = signal.get("stop_loss", 0.0)
        tp = signal.get("target_price", 0.0)
        qty = signal.get("quantity", 1)
        rr = signal.get("risk_reward_ratio", 2.5)
        reason = signal.get("reason", "Technical Setup")
        score = signal.get("strategy_score", 85.0)

        risk_amount = abs(entry - sl) * qty
        reward_amount = abs(tp - entry) * qty
        timeout_sec = getattr(settings, "APPROVAL_TIMEOUT_SECONDS", 120)

        msg = (
            f"<b>{emoji} ACTION REQUIRED: {direction} SIGNAL #{sig_id}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Symbol:</b> <code>{symbol}</code> ({direction})\n"
            f"<b>Entry Price:</b> ₹{entry:,.2f}\n"
            f"<b>Stop Loss (SL):</b> ₹{sl:,.2f} (-₹{risk_amount:,.2f})\n"
            f"<b>Target (TP):</b> ₹{tp:,.2f} (+₹{reward_amount:,.2f})\n"
            f"<b>Quantity:</b> {qty} shares\n"
            f"<b>Risk Amount:</b> ₹{risk_amount:,.2f}\n"
            f"<b>Risk:Reward:</b> 1:{rr} (Asymmetric)\n"
            f"<b>Signal Score:</b> {score:.1f}/100\n"
            f"<b>Rationale:</b> <i>{reason}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ <b>Expires in {timeout_sec}s</b> &bull; Click below to enter:"
        )

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": f"✅ Approve {direction} #{sig_id}", "callback_data": f"approve_{sig_id}"},
                    {"text": f"❌ Reject #{sig_id}", "callback_data": f"reject_{sig_id}"}
                ]
            ]
        }

        return await self.send_message(msg, reply_markup=inline_keyboard)

    async def send_signal_alert(self, signal: Dict[str, Any]) -> bool:
        """Alias for approval request or fallback notification."""
        return await self.send_signal_approval_request(signal)

    async def send_position_executed(self, pos: Dict[str, Any]) -> bool:
        direction = pos.get("side", "BUY")
        emoji = "🚀" if direction == "BUY" else "🔻"
        symbol = pos.get("symbol", "")
        entry = pos.get("entry_price", 0.0)
        qty = pos.get("quantity", 0)
        capital = entry * qty
        sl = pos.get("stop_loss", 0.0)
        tp = pos.get("target_price", 0.0)

        msg = (
            f"<b>{emoji} ORDER EXECUTED — POSITION ACTIVE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Symbol:</b> <code>{symbol}</code> ({direction})\n"
            f"<b>Filled At:</b> ₹{entry:,.2f} | <b>Qty:</b> {qty}\n"
            f"<b>Capital Deployed:</b> ₹{capital:,.2f}\n"
            f"<b>Initial Stop Loss:</b> ₹{sl:,.2f}\n"
            f"<b>Profit Target:</b> ₹{tp:,.2f}\n"
            f"<b>Auto-Breakeven:</b> Active at +0.8R\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <i>Live MTM tracking initiated.</i>"
        )
        return await self.send_message(msg)

    async def send_breakeven_alert(self, symbol: str, entry_price: float, current_price: float) -> bool:
        msg = (
            f"<b>🛡️ BREAKEVEN ACTIVATED — ZERO RISK</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Symbol:</b> <code>{symbol}</code>\n"
            f"<b>Status:</b> Price reached +0.8R profit (₹{current_price:,.2f})\n"
            f"<b>Stop Loss:</b> Moved to Entry (₹{entry_price:,.2f})\n"
            f"<b>Guaranteed Outcome:</b> Risk eliminated. $0 capital loss possible.\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>Letting winner ride to 2.5R target!</i>"
        )
        return await self.send_message(msg)

    async def send_position_exit(self, pos: Dict[str, Any]) -> bool:
        pnl = pos.get("net_realized_pnl", 0.0)
        is_win = pnl > 0
        emoji = "🎯" if is_win else "🛑"
        symbol = pos.get("symbol", "")
        exit_price = pos.get("exit_price", 0.0)
        reason = pos.get("exit_reason", "CLOSED")
        charges = pos.get("statutory_charges", 0.0)

        pnl_str = f"+₹{pnl:,.2f}" if is_win else f"-₹{abs(pnl):,.2f}"
        msg = (
            f"<b>{emoji} POSITION CLOSED ({reason})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Symbol:</b> <code>{symbol}</code>\n"
            f"<b>Exit Price:</b> ₹{exit_price:,.2f}\n"
            f"<b>Net Realized P&L:</b> <b>{pnl_str}</b>\n"
            f"<b>Statutory Taxes:</b> ₹{charges:,.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ <i>{datetime.datetime.now().strftime('%H:%M:%S IST')}</i>"
        )
        return await self.send_message(msg)

    async def handle_callback_query(self, cb: Dict[str, Any]) -> Optional[str]:
        """
        Handles inline button clicks [Approve #id] [Reject #id] or [Confirm Close ALL].
        Enforces chat authorization and triggers streamer approval/rejection.
        """
        cb_id = cb.get("id")
        user = cb.get("from", {})
        message = cb.get("message", {})
        chat = message.get("chat", {}) or user
        chat_id = str(chat.get("id", ""))
        data = cb.get("data", "")

        # Security Check
        if not self.is_chat_authorized(chat_id):
            logger.warning(f"[Security Violation] Unauthorized Telegram callback attempt from chat_id={chat_id}")
            if cb_id:
                await self.answer_callback_query(cb_id, "Access Denied: Unauthorized account.")
            return "UNAUTHORIZED"

        if cb_id:
            await self.answer_callback_query(cb_id)

        from app.live.streamer import live_streamer

        if data.startswith("approve_"):
            try:
                sig_id = int(data.split("_")[1])
                pos = live_streamer.approve_signal(sig_id)
                if pos:
                    await self.send_message(
                        f"✅ <b>Signal #{sig_id} Approved!</b> Executed as Position #{pos.id} on {pos.symbol} ({pos.quantity} shares @ ₹{pos.entry_price:.2f}).",
                        target_chat_id=chat_id
                    )
                    return "APPROVED"
                else:
                    sig = live_streamer.signal_engine.get_signal(sig_id)
                    reason = sig.risk_notes if sig else "Signal already executed, expired, or failed risk checks."
                    await self.send_message(
                        f"⚠️ <b>Cannot Execute Signal #{sig_id}</b>: {reason}",
                        target_chat_id=chat_id
                    )
                    return "FAILED_OR_IDEMPOTENT"
            except Exception as e:
                logger.error(f"Error handling approval callback: {e}")
                return "ERROR"

        elif data.startswith("reject_"):
            try:
                sig_id = int(data.split("_")[1])
                live_streamer.reject_signal(sig_id, reason="Rejected via Telegram inline button")
                await self.send_message(f"❌ <b>Signal #{sig_id} Rejected.</b>", target_chat_id=chat_id)
                return "REJECTED"
            except Exception as e:
                logger.error(f"Error handling rejection callback: {e}")
                return "ERROR"

        elif data == "confirm_close_all":
            summary = live_streamer.position_manager.get_portfolio_summary()
            current_prices = {s: t.ltp for s, t in live_streamer.latest_ticks.items()}
            closed = live_streamer.position_manager.square_off_all_positions(current_prices, reason="TELEGRAM_CLOSE_ALL")
            await self.send_message(
                f"🚨 <b>Emergency Square-Off Complete:</b> Liquidated {len(closed)} open positions.",
                target_chat_id=chat_id
            )
            return "CLOSED_ALL"

        elif data == "cancel_close_all":
            await self.send_message("Action cancelled. Open positions remain active.", target_chat_id=chat_id)
            return "CANCELLED"

        return None

    async def handle_command(self, text: str, chat_id: Union[str, int]) -> Optional[str]:
        """
        Executes text commands:
        /status, /pnl, /positions, /pause, /resume, /close SYMBOL, /close ALL, /help
        """
        # Security Check: Silently ignore unauthorized users
        if not self.is_chat_authorized(chat_id):
            logger.warning(f"[Security Violation] Unauthorized Telegram command from chat_id={chat_id}: {text}")
            return "UNAUTHORIZED"

        cmd = text.strip()
        cmd_parts = cmd.split()
        root_cmd = cmd_parts[0].lower().split("@")[0]  # Strip bot handle if present

        from app.live.streamer import live_streamer

        if root_cmd == "/help" or root_cmd == "/start":
            msg = (
                "<b>🤖 AI Trading Agent Commands:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "• <code>/status</code> — System mode, stream state & metrics\n"
                "• <code>/pnl</code> — Today's realized & unrealized P&L\n"
                "• <code>/positions</code> — Open paper trades and trailing stops\n"
                "• <code>/pause</code> — Temporarily pause new signal generation\n"
                "• <code>/resume</code> — Resume normal signal scanner\n"
                "• <code>/close SYMBOL</code> — Manually exit a specific stock\n"
                "• <code>/close ALL</code> — Square off all positions (with confirmation)\n"
                "• <code>/proposals</code> — List pending parameter change proposals\n"
                "• <code>/approve_param ID</code> — Approve a proposed parameter change\n"
                "• <code>/rollback_param</code> — Roll back parameters to previous version\n"
                "• <code>/help</code> — Show this commands manual"
            )
            await self.send_message(msg, target_chat_id=chat_id)
            return "HELP"

        elif root_cmd == "/status":
            summary = live_streamer.position_manager.get_portfolio_summary()
            pending_count = len(live_streamer.signal_engine.get_pending_signals())
            auto_app = "ACTIVE" if live_streamer.is_auto_approve_active() else "DISABLED (Manual Approval Required)"
            stream_status = "CONNECTED" if live_streamer.is_connected else "STANDBY"
            pause_status = "PAUSED" if self._is_paused else "RUNNING"

            msg = (
                f"<b>📊 SYSTEM STATUS</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Engine State:</b> {pause_status} ({stream_status})\n"
                f"<b>Auto-Approve:</b> {auto_app}\n"
                f"<b>Open Positions:</b> {summary['open_positions_count']}\n"
                f"<b>Pending Signals:</b> {pending_count}\n"
                f"<b>Today Total P&L:</b> ₹{summary['today_total_pnl']:,.2f}\n"
                f"<b>Loss Limit Remaining:</b> ₹{summary['daily_loss_remaining']:,.2f}\n"
                f"<b>Trading Mode:</b> STRICT PAPER ONLY"
            )
            await self.send_message(msg, target_chat_id=chat_id)
            return "STATUS"

        elif root_cmd == "/pnl":
            summary = live_streamer.position_manager.get_portfolio_summary()
            realized = summary["today_realized_pnl"]
            unrealized = summary["today_unrealized_pnl"]
            total = summary["today_total_pnl"]

            msg = (
                f"<b>💰 TODAY'S P&L SUMMARY</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Realized P&L:</b> {'+₹' if realized >= 0 else '-₹'}{abs(realized):,.2f}\n"
                f"<b>Unrealized MTM:</b> {'+₹' if unrealized >= 0 else '-₹'}{abs(unrealized):,.2f}\n"
                f"<b>Total Daily P&L:</b> <b>{'+₹' if total >= 0 else '-₹'}{abs(total):,.2f}</b>\n"
                f"<b>Daily Loss Floor:</b> ₹{settings.MAX_DAILY_LOSS_AMOUNT:,.2f}"
            )
            await self.send_message(msg, target_chat_id=chat_id)
            return "PNL"

        elif root_cmd == "/positions":
            positions = live_streamer.position_manager.get_open_positions()
            if not positions:
                await self.send_message("No open positions currently active.", target_chat_id=chat_id)
                return "POSITIONS_EMPTY"

            lines = ["<b>📈 OPEN POSITIONS</b>\n━━━━━━━━━━━━━━━━━━━━"]
            for p in positions:
                pnl = p.unrealized_pnl
                pnl_str = f"+₹{pnl:,.2f}" if pnl >= 0 else f"-₹{abs(pnl):,.2f}"
                effective_sl = p.trailing_stop or p.stop_loss
                lines.append(
                    f"• <b>{p.symbol}</b> ({p.side}) | Qty: {p.quantity}\n"
                    f"  Entry: ₹{p.entry_price:.2f} | LTP: ₹{p.current_price:.2f}\n"
                    f"  SL: ₹{effective_sl:.2f} | TP: ₹{p.target_price:.2f}\n"
                    f"  MTM: <b>{pnl_str}</b>"
                )
            await self.send_message("\n".join(lines), target_chat_id=chat_id)
            return "POSITIONS"

        elif root_cmd == "/pause":
            self._is_paused = True
            live_streamer.activate_kill_switch(1, reason="Paused by operator via Telegram /pause")
            await self.send_message("⏸️ <b>Trading Scanner Paused:</b> Signal generation temporarily halted.", target_chat_id=chat_id)
            return "PAUSE"

        elif root_cmd == "/resume":
            self._is_paused = False
            live_streamer.reset_kill_switch()
            await self.send_message("▶️ <b>Trading Scanner Resumed:</b> Normal signal generation active.", target_chat_id=chat_id)
            return "RESUME"

        elif root_cmd == "/close":
            if len(cmd_parts) < 2:
                await self.send_message("Usage: <code>/close SYMBOL</code> or <code>/close ALL</code>", target_chat_id=chat_id)
                return "CLOSE_INVALID"

            target_arg = cmd_parts[1].upper()
            if target_arg == "ALL":
                # Requires a confirm button
                confirm_keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "⚠️ CONFIRM CLOSE ALL", "callback_data": "confirm_close_all"},
                            {"text": "Cancel", "callback_data": "cancel_close_all"}
                        ]
                    ]
                }
                await self.send_message(
                    "⚠️ <b>CONFIRM EMERGENCY SQUARE-OFF:</b> Are you sure you want to market close ALL open positions?",
                    reply_markup=confirm_keyboard,
                    target_chat_id=chat_id
                )
                return "CLOSE_ALL_REQUESTED"
            else:
                positions = live_streamer.position_manager.get_open_positions()
                target_pos = next((p for p in positions if p.symbol == target_arg), None)
                if not target_pos:
                    await self.send_message(f"No active open position found for symbol {target_arg}.", target_chat_id=chat_id)
                    return "CLOSE_NOT_FOUND"

                current_price = live_streamer.latest_ticks.get(target_arg).ltp if target_arg in live_streamer.latest_ticks else target_pos.current_price
                closed = live_streamer.position_manager.close_position(target_pos.id, current_price, reason="TELEGRAM_MANUAL_CLOSE")
                pnl = closed.net_realized_pnl
                await self.send_message(
                    f"✅ Closed <b>{target_arg}</b> at ₹{current_price:.2f} | Net P&L: <b>{'+₹' if pnl >= 0 else '-₹'}{abs(pnl):,.2f}</b>",
                    target_chat_id=chat_id
                )
                return "CLOSE_SYMBOL_SUCCESS"

        elif root_cmd == "/proposals":
            from app.core.database import SessionLocal
            from app.learning.learner import market_learner
            db = SessionLocal()
            try:
                proposals = market_learner.get_pending_proposals(db)
                if not proposals:
                    await self.send_message("No pending parameter change proposals at this time.", target_chat_id=chat_id)
                    return "PROPOSALS_EMPTY"

                lines = ["<b>💡 PENDING PARAMETER PROPOSALS</b>\n━━━━━━━━━━━━━━━━━━━━"]
                for p in proposals:
                    lines.append(
                        f"• <b>Proposal #{p['id']}</b> ({p['param_name']})\n"
                        f"  Change: {p['old_value']:.2f}x ➔ <b>{p['new_value']:.2f}x</b> (TP: {p['tp_multiplier']:.2f}x, R:R 1:{p['target_rr']:.1f})\n"
                        f"  Sample: {p['sample_size']} trades (Win Rate: {p['win_rate_pct']:.1f}%)\n"
                        f"  Evidence: {p['evidence']}\n"
                        f"  👉 To apply: <code>/approve_param {p['id']}</code>"
                    )
                await self.send_message("\n\n".join(lines), target_chat_id=chat_id)
                return "PROPOSALS_LIST"
            finally:
                db.close()

        elif root_cmd == "/approve_param":
            if len(cmd_parts) < 2:
                await self.send_message("Usage: <code>/approve_param ID</code> (e.g. <code>/approve_param 1</code>)", target_chat_id=chat_id)
                return "APPROVE_PARAM_USAGE"

            try:
                param_id = int(cmd_parts[1])
            except ValueError:
                await self.send_message("Invalid proposal ID. Must be an integer.", target_chat_id=chat_id)
                return "APPROVE_PARAM_INVALID_ID"

            from app.core.database import SessionLocal
            from app.learning.learner import market_learner
            db = SessionLocal()
            try:
                res = market_learner.approve_proposal(db, param_id, approved_by="TELEGRAM")
                if res.get("success"):
                    await self.send_message(
                        f"✅ <b>Parameter Proposal #{param_id} Approved!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"• Version: <b>v{res['version']}</b>\n"
                        f"• {res['param_name']}: {res['old_value']:.2f}x ➔ <b>{res['new_value']:.2f}x</b>\n"
                        f"• TP Multiplier: <b>{res['tp_multiplier']:.2f}x</b>\n"
                        f"• Rollback with <code>/rollback_param</code> if needed.",
                        target_chat_id=chat_id
                    )
                    return "APPROVE_PARAM_SUCCESS"
                else:
                    await self.send_message(f"❌ Failed to approve proposal #{param_id}: {res.get('error')}", target_chat_id=chat_id)
                    return "APPROVE_PARAM_FAILED"
            finally:
                db.close()

        elif root_cmd == "/reject_param":
            if len(cmd_parts) < 2:
                await self.send_message("Usage: <code>/reject_param ID</code>", target_chat_id=chat_id)
                return "REJECT_PARAM_USAGE"

            try:
                param_id = int(cmd_parts[1])
            except ValueError:
                await self.send_message("Invalid proposal ID. Must be an integer.", target_chat_id=chat_id)
                return "REJECT_PARAM_INVALID_ID"

            from app.core.database import SessionLocal
            from app.learning.learner import market_learner
            db = SessionLocal()
            try:
                res = market_learner.reject_proposal(db, param_id, reason="Rejected via Telegram")
                if res.get("success"):
                    await self.send_message(f"❌ <b>Proposal #{param_id} Rejected.</b>", target_chat_id=chat_id)
                    return "REJECT_PARAM_SUCCESS"
                else:
                    await self.send_message(f"Failed to reject proposal #{param_id}: {res.get('error')}", target_chat_id=chat_id)
                    return "REJECT_PARAM_FAILED"
            finally:
                db.close()

        elif root_cmd == "/rollback_param":
            from app.core.database import SessionLocal
            from app.learning.learner import market_learner
            db = SessionLocal()
            try:
                res = market_learner.rollback_to_previous_version(db, approved_by="TELEGRAM")
                if res.get("success"):
                    await self.send_message(
                        f"🔄 <b>Parameter Rollback Executed (v{res['version']})</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"• Restored SL: <b>{res['restored_value']:.2f}x</b> (was {res['old_value']:.2f}x)\n"
                        f"• Restored TP: <b>{res['tp_multiplier']:.2f}x</b>\n"
                        f"• Action: {res['action']}",
                        target_chat_id=chat_id
                    )
                    return "ROLLBACK_PARAM_SUCCESS"
                else:
                    await self.send_message(f"Rollback failed: {res.get('error')}", target_chat_id=chat_id)
                    return "ROLLBACK_PARAM_FAILED"
            finally:
                db.close()

        elif root_cmd == "/eod_report":
            res = await self.send_end_of_day_report(target_chat_id=chat_id)
            return "EOD_REPORT_SENT" if res.get("success") else "EOD_REPORT_FAILED"

        return "UNKNOWN_COMMAND"

    async def send_end_of_day_report(self, target_chat_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """
        Sends the 15:45 IST End-of-Day trading report containing:
        - Completed trades and Win Rate
        - Net P&L & statutory charges
        - Key metrics (Average R, Profit Factor, Expectancy, Max Drawdown)
        - Rejected signals count with top reasons
        - System warnings and watchdog incidents
        """
        from app.core.database import SessionLocal
        from app.models.models import Trade, TradeSignal, SystemLog
        from app.analytics.performance import PerformanceEngine
        
        db = SessionLocal()
        try:
            today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            trades_today = db.query(Trade).filter(Trade.exit_time >= today_start).all()
            total_trades = len(trades_today)
            wins = sum(1 for t in trades_today if t.net_pnl > 0)
            losses = sum(1 for t in trades_today if t.net_pnl <= 0)
            win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0
            gross_pnl = sum(t.gross_pnl for t in trades_today)
            charges = sum(t.estimated_charges for t in trades_today)
            net_pnl = sum(t.net_pnl for t in trades_today)
            
            metrics = PerformanceEngine.calculate_metrics(db)
            
            rejected_signals = db.query(TradeSignal).filter(
                TradeSignal.timestamp >= today_start,
                TradeSignal.status == "REJECTED"
            ).all()
            rejected_count = len(rejected_signals)
            
            reasons_counter: Dict[str, int] = {}
            for s in rejected_signals:
                r = s.reject_reason or s.explanation or "Risk filter block"
                reasons_counter[r] = reasons_counter.get(r, 0) + 1
            top_reasons = sorted(reasons_counter.items(), key=lambda x: x[1], reverse=True)[:3]
            
            warnings = db.query(SystemLog).filter(
                SystemLog.timestamp >= today_start,
                SystemLog.level.in_(["WARNING", "ERROR"])
            ).all()
            warnings_count = len(warnings)
            
            pnl_sign = "+₹" if net_pnl >= 0 else "-₹"
            pnl_color = "🟢" if net_pnl >= 0 else "🔴"
            
            lines = [
                f"<b>📊 END-OF-DAY TRADING REPORT (15:45 IST)</b>",
                f"━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"📅 <b>Date:</b> {datetime.date.today().strftime('%d %b %Y')}",
                f"{pnl_color} <b>Realized Net P&L:</b> <b>{pnl_sign}{abs(net_pnl):,.2f}</b>",
                f"💰 <b>Gross P&L:</b> ₹{gross_pnl:,.2f} | <b>Charges:</b> ₹{charges:,.2f}",
                f"",
                f"<b>📈 Trade Performance:</b>",
                f"• Trades Executed: <b>{total_trades}</b> (Wins: {wins}, Losses: {losses})",
                f"• Win Rate: <b>{win_rate:.1f}%</b>",
                f"• Average Achieved R: <b>{metrics.average_r:.2f}R</b>",
                f"• Profit Factor: <b>{metrics.profit_factor:.2f}</b>",
                f"• Net Expectancy/Trade: <b>₹{metrics.expectancy_per_trade:,.2f}</b>",
                f"• Max Drawdown: <b>₹{metrics.max_drawdown:,.2f} ({metrics.max_drawdown_pct:.1f}%)</b>",
                f"• Longest Losing Streak: <b>{metrics.longest_losing_streak}</b>",
                f"",
                f"<b>🚫 Signal Rejections: {rejected_count}</b>"
            ]
            
            if top_reasons:
                for reason_text, count in top_reasons:
                    lines.append(f"  • {count}x: {reason_text[:40]}")
            else:
                lines.append("  • No rejected signals today.")
                
            lines.append("")
            lines.append(f"<b>⚠️ System Warnings & Watchdog: {warnings_count}</b>")
            if warnings:
                for w in warnings[-3:]:
                    lines.append(f"  • [{w.module}] {w.message[:45]}")
            else:
                lines.append("  • ✅ Zero critical warnings. Clean operational session.")
                
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("<i>AI Intraday Trading Agent • Safe Mode Active</i>")
            
            report_text = "\n".join(lines)
            sent = await self.send_message(report_text, target_chat_id=target_chat_id)
            return {
                "success": sent,
                "total_trades": total_trades,
                "net_pnl": net_pnl,
                "rejected_count": rejected_count,
                "warnings_count": warnings_count,
                "report_text": report_text
            }
        finally:
            db.close()

    async def poll_telegram_updates(self):
        """
        Long-polling worker reading updates (messages and button callback clicks) from Telegram.
        """
        if not self.is_configured or not self.enabled:
            return

        url = f"{self.base_url}/getUpdates"
        params = {"offset": self._last_update_id + 1, "timeout": 5}

        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        self._last_update_id = max(self._last_update_id, update.get("update_id", 0))

                        # 1. Handle Callback Query (Inline Button Click)
                        if "callback_query" in update:
                            await self.handle_callback_query(update["callback_query"])

                        # 2. Handle Text Message Command
                        elif "message" in update and "text" in update["message"]:
                            msg = update["message"]
                            chat_id = msg.get("chat", {}).get("id")
                            text = msg.get("text", "")
                            if text.startswith("/"):
                                await self.handle_command(text, chat_id)
        except Exception as e:
            logger.debug(f"Telegram polling loop exception: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": "Bot Token or Chat ID is missing or using placeholder.",
                "configured": False
            }

        test_msg = (
            f"<b>🤖 AI Intraday Trading Agent Connected!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>Mobile Alert Channel:</b> Active\n"
            f"💰 <b>Paper Capital:</b> ₹5,00,000 INR\n"
            f"🛡️ <b>Two-Way Approval:</b> Inline Buttons Active\n"
            f"📡 <b>Live Feed:</b> National Stock Exchange (NSE)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Send <code>/help</code> for available interactive commands!"
        )
        success = await self.send_message(test_msg)
        return {
            "success": success,
            "configured": True,
            "bot_token_set": bool(self.bot_token),
            "chat_id_set": bool(self.chat_id)
        }

telegram_notifier = TelegramNotifier()
