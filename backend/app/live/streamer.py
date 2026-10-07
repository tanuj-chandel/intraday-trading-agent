import datetime
from typing import Dict, Any, List, Optional
from app.live.data_types import LiveTick, LiveSignalItem, LivePaperPosition
from app.live.candle_builder import LiveCandleBuilder
from app.live.signal_engine import LiveSignalEngine
from app.live.position_manager import LivePositionManager
from app.live.quality_gate import LiveDataQualityGate
from app.live.execution import LivePaperExecutionEngine
from app.live.audit import LiveAuditLogger
from app.live.report import Phase7ReportGenerator
from app.live.kill_switch import HierarchicalKillSwitch, KillSwitchLevel
from app.live.reality_gap import RealityGapAnalyzer
from app.risk.manager import RiskManager
from app.schemas.schemas import TradeSignalCreate
from app.core.config import settings

# Phase 8 additions
from app.live.tick_validator import Phase8TickValidator
from app.live.data_quality_monitor import Phase8DataQualityMonitor
from app.live.alerter import alert_engine, AlertType, AlertSeverity
from app.live.trade_journal import trade_journal, TradeJournalEntry
from app.live.regime_segmenter import Phase8RegimeSegmenter

class LiveTickStreamer:
    """
    Central Coordinator for Live Real-Time Indian Market Paper Trading:
    - Ingests streaming live ticks (Phase 8: with tick validation and quality monitoring)
    - Builds live multi-timeframe candles
    - Evaluates live signals
    - Executes paper trades upon human approval
    - Manages live positions and SL/TP mark-to-market
    - Phase 8: Trade journal, alerting, regime segmentation
    """

    def __init__(self):
        self.candle_builder = LiveCandleBuilder()
        self.risk_manager = RiskManager()
        self.signal_engine = LiveSignalEngine(self.risk_manager)
        self.position_manager = LivePositionManager(max_daily_loss=getattr(settings, "MAX_DAILY_LOSS_AMOUNT", 15000.0))
        self.kill_switch = HierarchicalKillSwitch()
        self.reality_gap = RealityGapAnalyzer()
        self.latest_ticks: Dict[str, LiveTick] = {}
        self.is_connected = False
        self.provider_name = "ZERODHA_KITE / MOCK"
        self.is_mock = True  # Defaults to True until real API credentials are authenticated
        self._has_credentials = False  # Set True only when real broker creds verified

        # Phase 8: New quality & journal modules
        self.tick_validator = Phase8TickValidator()
        self.data_quality_monitor = Phase8DataQualityMonitor()
        
        # Auto-Execution Mode (Defaults to False; nothing enters without approval)
        self.auto_approve_enabled = getattr(settings, "AUTO_APPROVE", False) or getattr(settings, "AUTO_APPROVE_SIGNALS", False)
        self.auto_approve_expiry = getattr(settings, "AUTO_APPROVE_EXPIRY_DATE", None)

    def is_auto_approve_active(self) -> bool:
        if not self.auto_approve_enabled:
            return False
        if self.auto_approve_expiry:
            try:
                expiry_dt = datetime.datetime.fromisoformat(self.auto_approve_expiry)
                if datetime.datetime.now() > expiry_dt:
                    return False
            except Exception:
                pass
        return True

    def set_auto_approve(self, enabled: bool, expiry_iso: Optional[str] = None):
        self.auto_approve_enabled = enabled
        if expiry_iso is not None:
            self.auto_approve_expiry = expiry_iso
        LiveAuditLogger.log(
            "AUTO_APPROVE_TOGGLED",
            f"Auto-approval set to {enabled} (Expiry: {self.auto_approve_expiry})"
        )

    def connect(self, provider: str = "ZERODHA_KITE", is_mock: bool = True, has_credentials: bool = False):
        from app.execution.safety_service import execution_safety
        execution_safety.verify_live_startup_guard(provider, is_mock=is_mock)
        self.is_connected = True
        self.provider_name = provider
        self.is_mock = is_mock
        self._has_credentials = has_credentials
        LiveAuditLogger.log("DATA_CONNECTED", f"Connected to {provider} (Mock={is_mock}, Credentials={'SET' if has_credentials else 'NOT SET'})")

    def disconnect(self, reason: str = "User disconnect"):
        self.is_connected = False
        LiveAuditLogger.log("DATA_DISCONNECT", f"Provider disconnected: {reason}")

    def ingest_tick(self, tick: LiveTick) -> Dict[str, Any]:
        received_at = datetime.datetime.now()

        # Phase 8: Validate tick before accepting it
        validation = self.tick_validator.validate(
            symbol=tick.symbol,
            ltp=tick.ltp,
            open_=tick.open,
            high=tick.high,
            low=tick.low,
            close=tick.close,
            volume=tick.volume,
            bid=tick.bid,
            ask=tick.ask,
            tick_timestamp=tick.timestamp,
            received_at=received_at,
        )

        # Record quality metric regardless of validity
        self.data_quality_monitor.record_tick(
            symbol=tick.symbol,
            latency_ms=validation.latency_ms,
            is_valid=validation.is_valid,
            is_duplicate=(validation.rejection_code is not None and
                          validation.rejection_code.value == "DUPLICATE_TICK")
        )

        # Reject invalid ticks — fail closed, never process corrupted data
        if not validation.is_valid:
            LiveAuditLogger.log(
                "TICK_REJECTED",
                f"Tick for {tick.symbol} rejected: {validation.rejection_reason}",
                symbol=tick.symbol
            )
            # Fire alert if invalid tick rate is high
            stats = self.tick_validator.get_stats()
            if stats["invalid_rate_pct"] > 5.0:
                alert_engine.invalid_tick_rate(tick.symbol, stats["invalid_rate_pct"])
            return {
                "symbol": tick.symbol,
                "ltp": tick.ltp,
                "tick_rejected": True,
                "rejection_reason": validation.rejection_reason,
                "gate": {"status": "INVALID", "can_generate_signals": False},
                "closed_candles": {},
                "generated_signal": None,
                "exited_positions": []
            }

        self.latest_ticks[tick.symbol] = tick
        from app.execution.safety_service import execution_safety
        execution_safety.record_tick_timestamp(tick.symbol)
        LiveAuditLogger.log("DATA_RECEIVED", f"Tick for {tick.symbol} LTP={tick.ltp}", symbol=tick.symbol)

        # 1. Update Open Position MTM & check SL/TP
        exited_positions = self.position_manager.update_market_price(tick.symbol, tick.ltp)
        for pos in exited_positions:
            LiveAuditLogger.log("POSITION_EXITED", f"Position #{pos.id} ({pos.symbol}) exited. Reason: {pos.exit_reason}, Net P&L: ₹{pos.net_realized_pnl}", symbol=pos.symbol)

        # 2. Ingest into candle builder
        closed_candles = self.candle_builder.ingest_tick(tick)

        # 3. Check Live Quality Gate
        gate = LiveDataQualityGate.evaluate_live_feed(
            last_tick_time=tick.timestamp,
            is_market_connected=self.is_connected,
            is_mock_provider=self.is_mock,
            has_credentials=self._has_credentials,
            last_tick_price=tick.ltp
        )

        generated_signal = None
        # Only evaluate signal if quality gate passes and sufficient bars exist
        candles_5m = self.candle_builder.get_candles(tick.symbol, "5m")
        if gate["can_generate_signals"] and len(candles_5m) >= 5:
            from app.market.regime import MarketRegimeEngine
            current_regime = MarketRegimeEngine.get_current_regime_info()["regime"]
            generated_signal = self.signal_engine.evaluate_symbol(
                symbol=tick.symbol,
                candles=candles_5m,
                market_regime=current_regime,
                data_freshness=gate.get("data_age_seconds", 0.0)
            )
            if generated_signal:
                LiveAuditLogger.log("SIGNAL_CREATED", f"Signal #{generated_signal.id} ({generated_signal.direction}) created for {tick.symbol}", symbol=tick.symbol)
                try:
                    from app.notifications.dispatcher import notifier
                    notifier.notify_signal(generated_signal.model_dump())
                except Exception:
                    pass
                # Auto-execution check
                if self.is_auto_approve_active():
                    auto_pos = self.approve_signal(generated_signal.id)
                    if auto_pos:
                        LiveAuditLogger.log(
                            "AUTO_EXECUTE",
                            f"Auto-approved and executed Signal #{generated_signal.id} as Position #{auto_pos.id} for {tick.symbol}",
                            symbol=tick.symbol
                        )

        return {
            "symbol": tick.symbol,
            "ltp": tick.ltp,
            "tick_rejected": False,
            "tick_latency_ms": round(validation.latency_ms, 1),
            "gate": gate,
            "closed_candles": {k: v.model_dump() if v else None for k, v in closed_candles.items()},
            "generated_signal": generated_signal.model_dump() if generated_signal else None,
            "exited_positions": [p.model_dump() for p in exited_positions]
        }

    def approve_signal(self, signal_id: int) -> Optional[LivePaperPosition]:
        sig = self.signal_engine.get_signal(signal_id)
        if not sig or sig.status not in ("PENDING", "PENDING_APPROVAL"):
            return None

        # Check Expiry
        timeout_sec = getattr(settings, "APPROVAL_TIMEOUT_SECONDS", 120)
        age = (datetime.datetime.now() - sig.created_at).total_seconds()
        if age >= timeout_sec:
            self.signal_engine.update_signal_status(signal_id, "EXPIRED", reject_reason=f"Approval timeout exceeded ({int(age)}s >= {timeout_sec}s)")
            LiveAuditLogger.log("SIGNAL_EXPIRED", f"Signal #{sig.id} expired upon approval attempt ({int(age)}s)", symbol=sig.symbol)
            return None

        # Fetch latest market price for drift & SL/TP validation
        current_tick = self.latest_ticks.get(sig.symbol)
        mkt_price = current_tick.ltp if current_tick else sig.entry_price

        # Check if SL or TP is already breached
        if sig.direction == "BUY":
            if mkt_price <= sig.stop_loss:
                self.signal_engine.update_signal_status(signal_id, "CANCELLED", reject_reason=f"Current price ₹{mkt_price:.2f} already hit Stop Loss ₹{sig.stop_loss:.2f}")
                LiveAuditLogger.log("ENTRY_CANCELLED", f"Signal #{sig.id} cancelled: SL already breached before entry", symbol=sig.symbol)
                return None
            if mkt_price >= sig.target_price:
                self.signal_engine.update_signal_status(signal_id, "CANCELLED", reject_reason=f"Current price ₹{mkt_price:.2f} already hit Target ₹{sig.target_price:.2f}")
                LiveAuditLogger.log("ENTRY_CANCELLED", f"Signal #{sig.id} cancelled: Target already reached before entry", symbol=sig.symbol)
                return None
        else: # SELL
            if mkt_price >= sig.stop_loss:
                self.signal_engine.update_signal_status(signal_id, "CANCELLED", reject_reason=f"Current price ₹{mkt_price:.2f} already hit Stop Loss ₹{sig.stop_loss:.2f}")
                LiveAuditLogger.log("ENTRY_CANCELLED", f"Signal #{sig.id} cancelled: SL already breached before entry", symbol=sig.symbol)
                return None
            if mkt_price <= sig.target_price:
                self.signal_engine.update_signal_status(signal_id, "CANCELLED", reject_reason=f"Current price ₹{mkt_price:.2f} already hit Target ₹{sig.target_price:.2f}")
                LiveAuditLogger.log("ENTRY_CANCELLED", f"Signal #{sig.id} cancelled: Target already reached before entry", symbol=sig.symbol)
                return None

        # Price drift check (MAX_ENTRY_DRIFT_PCT default 0.3%)
        max_drift_pct = getattr(settings, "MAX_ENTRY_DRIFT_PCT", 0.003)
        drift_pct = abs(mkt_price - sig.entry_price) / (sig.entry_price + 1e-10)
        if drift_pct > max_drift_pct:
            drift_msg = f"Price drifted {drift_pct*100:.2f}% (from ₹{sig.entry_price:.2f} to ₹{mkt_price:.2f}), exceeding max allowed drift of {max_drift_pct*100:.2f}%"
            self.signal_engine.update_signal_status(signal_id, "CANCELLED", reject_reason=drift_msg)
            LiveAuditLogger.log("ENTRY_DRIFT_REJECTED", f"Signal #{sig.id} cancelled: {drift_msg}", symbol=sig.symbol)
            return None

        # Build portfolio context for RiskManager
        portfolio = self.position_manager.get_portfolio_summary()
        current_equity = getattr(settings, "INITIAL_CAPITAL", 500000.0) + portfolio["today_total_pnl"]
        
        # Recompute quantity if price drifted slightly
        recalc_qty, _ = self.risk_manager.calculate_position_size(
            entry_price=mkt_price,
            stop_loss=sig.stop_loss,
            current_equity=current_equity,
            current_total_exposure=portfolio.get("current_total_exposure", 0.0)
        )
        if recalc_qty > 0:
            sig.quantity = recalc_qty

        sig_create = TradeSignalCreate(
            symbol=sig.symbol,
            direction=sig.direction,
            entry_price=mkt_price,
            stop_loss=sig.stop_loss,
            target_price=sig.target_price,
            quantity=sig.quantity,
            strategy_name=sig.strategy_name,
            strategy_score=sig.strategy_score,
            explanation=sig.reason
        )

        # RiskManager validation — mandatory gate before any paper execution
        risk_res = self.risk_manager.validate_trade(
            signal=sig_create,
            current_equity=current_equity,
            today_realized_loss=min(0.0, portfolio["today_realized_pnl"]),
            open_positions_count=portfolio["open_positions_count"],
            trades_count_today=0,
            consecutive_losses=0,
            open_positions_symbols=portfolio.get("open_positions_symbols", []),
            current_total_exposure=portfolio.get("current_total_exposure", 0.0)
        )

        if not risk_res.passed:
            self.signal_engine.update_signal_status(signal_id, "REJECTED_BY_RISK", reject_reason=risk_res.rejection_reason)
            LiveAuditLogger.log(
                "RISK_REJECTED",
                f"Signal #{sig.id} rejected by RiskManager: {risk_res.rejection_reason}",
                symbol=sig.symbol
            )
            return None

        # Apply risk-verified allowed quantity
        if risk_res.allowed_quantity and risk_res.allowed_quantity > 0:
            sig.quantity = risk_res.allowed_quantity

        # Phase 3 Execution Layer Safety: Broker Entry with immediate Broker-side SL
        from app.execution.safety_service import execution_safety
        pos = execution_safety.execute_entry_with_broker_sl_sync(
            signal=sig,
            current_market_price=mkt_price,
            position_id=len(self.position_manager.get_open_positions()) + len(self.position_manager.get_closed_positions()) + 1
        )

        if not pos:
            self.signal_engine.update_signal_status(signal_id, "EXECUTION_FAILED", reject_reason="Broker entry or SL placement rejected")
            LiveAuditLogger.log("EXECUTION_FAILED", f"Signal #{sig.id} execution failed at broker level", symbol=sig.symbol)
            return None

        self.position_manager.add_position(pos)
        self.signal_engine.update_signal_status(signal_id, "EXECUTED")
        try:
            from app.notifications.dispatcher import notifier
            notifier.notify_order_filled(pos.model_dump())
        except Exception:
            pass
        LiveAuditLogger.log(
            "APPROVAL_GRANTED",
            f"Signal #{sig.id} approved & executed as Position #{pos.id} (RR={sig.risk_reward_ratio})",
            symbol=sig.symbol
        )
        return pos

    def reject_signal(self, signal_id: int, reason: str = "User rejected") -> bool:
        sig = self.signal_engine.get_signal(signal_id)
        if not sig:
            return False
        self.signal_engine.update_signal_status(signal_id, "REJECTED")
        LiveAuditLogger.log("APPROVAL_REJECTED", f"Signal #{sig.id} rejected by user: {reason}", symbol=sig.symbol)
        return True

    # ── Kill Switch methods ────────────────────────────────────────────────────

    def activate_kill_switch(self, level: int, reason: str = "Manual activation") -> Dict[str, Any]:
        """Activate a specific kill switch level (1–5)."""
        from app.live.kill_switch import KillSwitchLevel as KSL
        level_map = {
            1: KSL.L1_PAUSE_SIGNALS,
            2: KSL.L2_NO_NEW_ENTRIES,
            3: KSL.L3_CLOSE_ALL_POSITIONS,
            4: KSL.L4_FREEZE_ALL,
            5: KSL.L5_FULL_HALT,
        }
        ks_level = level_map.get(level, KSL.L3_CLOSE_ALL_POSITIONS)
        result = self.kill_switch.activate(ks_level, reason)

        # Level 3+: square off all positions
        if level >= 3:
            self.risk_manager.trigger_emergency_stop()
            prices = {s: t.ltp for s, t in self.latest_ticks.items()}
            closed = self.position_manager.square_off_all_positions(prices, reason=f"KILL_SWITCH_L{level}: {reason}")
            result["positions_closed"] = len(closed)
            LiveAuditLogger.log("KILL_SWITCH", f"Level {level} activated: {reason}. Closed {len(closed)} positions.")
        else:
            LiveAuditLogger.log("KILL_SWITCH", f"Level {level} activated: {reason}")

        return result

    def trigger_emergency_stop(self, reason: str = "User Emergency Stop") -> Dict[str, Any]:
        """Level 3 kill switch — preserves backward compatibility."""
        return self.activate_kill_switch(3, reason)

    def reset_kill_switch(self, manual_operator_code: str = "") -> Dict[str, Any]:
        result = self.kill_switch.reset(manual_operator_code)
        if result.get("success"):
            self.risk_manager.reset_emergency_stop()
            LiveAuditLogger.log("KILL_SWITCH_RESET", "Kill switch reset. System operational.")
        return result

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        summary = self.position_manager.get_portfolio_summary()
        last_tick_time = max([t.timestamp for t in self.latest_ticks.values()]) if self.latest_ticks else None
        gate = LiveDataQualityGate.evaluate_live_feed(
            last_tick_time=last_tick_time,
            is_market_connected=self.is_connected,
            is_mock_provider=self.is_mock,
            has_credentials=self._has_credentials
        )

        # Reality gap analysis
        closed_trades = [p.model_dump() for p in self.position_manager.get_closed_positions()]
        reality_gap_report = self.reality_gap.analyze(
            backtest_metrics={"win_rate": 55.0, "expectancy": 150.0, "profit_factor": 1.5},
            paper_trades=closed_trades
        )

        from app.market.regime import MarketRegimeEngine
        regime_info = MarketRegimeEngine.get_current_regime_info()

        return {
            "trading_mode": "PAPER_TRADING_ONLY",
            "real_order_execution": "DISABLED",
            "is_connected": self.is_connected,
            "provider_name": self.provider_name,
            "is_mock": self.is_mock,
            "market_regime": regime_info["regime"],
            "market_regime_details": regime_info,
            "data_quality_gate": gate,
            "kill_switch": self.kill_switch.get_status(),
            "reality_gap": {
                "verdict": reality_gap_report.verdict,
                "paper_trades": reality_gap_report.paper_trades_count,
                "live_win_rate": reality_gap_report.live_win_rate,
                "is_sufficient_data": reality_gap_report.is_sufficient_data,
                "threshold_breaches": reality_gap_report.threshold_breaches
            },
            "symbols_monitored_count": len(self.latest_ticks),
            "auto_approve": {
                "enabled": self.auto_approve_enabled,
                "is_active": self.is_auto_approve_active(),
                "expiry": self.auto_approve_expiry
            },
            "portfolio_summary": summary,
            "open_positions": [p.model_dump() for p in self.position_manager.get_open_positions()],
            "pending_signals": [s.model_dump() for s in self.signal_engine.get_pending_signals()]
        }

# Global singleton instance
live_streamer = LiveTickStreamer()
