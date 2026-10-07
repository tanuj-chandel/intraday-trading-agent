"""
Market Knowledge & Safe Adaptive Learning Engine (Phase 5 Refactored)
Safeguards:
1. Minimum sample: no parameter change unless at least MIN_TRADES_FOR_LEARNING (default 100) trades are available.
2. Bounds: ATR multiplier must stay within [1.3, 2.0]. Each change is at most 0.1.
3. Keep R:R fixed: if SL multiplier changes, TP changes with it so R:R stays at configured value.
4. Recommend-only mode (default): writes proposals to table `parameter_proposals`; does not apply automatically.
   Approved via Telegram (/approve_param ID) or dashboard.
5. Version history: saves every applied parameter set to `parameter_version_history` with single-command rollback.
6. Segment stats by market regime and time of day (no mixing trending and choppy days).
"""

import datetime
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.models import Trade, ParameterProposal, ParameterVersionHistory
from app.core.config import settings
from app.core.logging import logger
from app.live.audit import LiveAuditLogger
from app.live.regime_segmenter import Phase8RegimeSegmenter

class MarketKnowledgeLearner:
    """
    Production-grade Safe Adaptive Learner for Indian Market Equities.
    """

    def __init__(self):
        self.last_learning_time: Optional[datetime.datetime] = None
        self.current_atr_sl_multiplier: float = getattr(settings, "DEFAULT_ATR_SL_MULTIPLIER", 1.5)
        self.current_target_rr: float = getattr(settings, "TARGET_RISK_REWARD_RATIO", 2.0)
        self.current_atr_tp_multiplier: float = round(self.current_atr_sl_multiplier * self.current_target_rr, 2)
        
        self.symbol_performance: Dict[str, Dict[str, Any]] = {}
        self.regime_performance: Dict[str, Dict[str, Any]] = {}
        self.time_bucket_performance: Dict[str, Dict[str, Any]] = {}

        self.knowledge_summary: Dict[str, Any] = {
            "total_trades_analyzed": 0,
            "overall_win_rate_pct": 0.0,
            "best_symbols": [],
            "caution_symbols": [],
            "current_sl_multiplier": self.current_atr_sl_multiplier,
            "current_tp_multiplier": self.current_atr_tp_multiplier,
            "current_target_rr": self.current_target_rr,
            "active_version": 1,
            "regime_segments": {},
            "time_segments": {},
            "learning_status": "INITIALIZED",
            "insights": [],
            "pending_proposals_count": 0,
            "last_updated": None
        }

    def learn_from_database(self, db: Session) -> Dict[str, Any]:
        """
        Reads completed trades, segments performance by regime & time-of-day,
        enforces sample threshold, and generates bounded proposals.
        """
        lookback = getattr(settings, "ADAPTIVE_LOOKBACK_TRADES", 200)
        trades: List[Trade] = db.query(Trade).order_by(Trade.exit_time.desc()).limit(lookback).all()

        total = len(trades)
        min_sample = getattr(settings, "MIN_TRADES_FOR_LEARNING", 100)

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        self.last_learning_time = datetime.datetime.now()

        # 1. Enforce Minimum Sample Gate
        if total < min_sample:
            status_msg = f"Insufficient sample size: {total} completed trades available; minimum {min_sample} required."
            logger.info(f"[SafeLearner] {status_msg}")
            self.knowledge_summary.update({
                "total_trades_analyzed": total,
                "learning_status": "INSUFFICIENT_SAMPLE",
                "sample_threshold": min_sample,
                "sample_met": False,
                "insights": [status_msg],
                "last_updated": now_str
            })
            return self.knowledge_summary

        # 2. Global Performance Metrics
        wins = [t for t in trades if (t.net_pnl or 0) > 0]
        losses = [t for t in trades if (t.net_pnl or 0) <= 0]
        win_rate = (len(wins) / total * 100.0) if total > 0 else 0.0

        # 3. Symbol-Level Attribution
        sym_map: Dict[str, Dict[str, Any]] = {}
        for t in trades:
            s = t.symbol
            if s not in sym_map:
                sym_map[s] = {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0}
            sym_map[s]["trades"] += 1
            if (t.net_pnl or 0) > 0:
                sym_map[s]["wins"] += 1
            else:
                sym_map[s]["losses"] += 1
            sym_map[s]["net_pnl"] += round(t.net_pnl or 0.0, 2)

        self.symbol_performance = sym_map
        best_symbols = [s for s, data in sym_map.items() if data["net_pnl"] > 0]
        caution_symbols = [s for s, data in sym_map.items() if data["net_pnl"] < 0]

        # 4. Segment by Market Regime
        regime_stats: Dict[str, Dict[str, Any]] = {}
        for t in trades:
            reg = (t.market_regime or "UNKNOWN").upper()
            if "TRENDING" in reg:
                norm_reg = "TRENDING"
            elif "CHOPPY" in reg or "SIDEWAYS" in reg:
                norm_reg = "CHOPPY"
            elif "HIGH_VOL" in reg:
                norm_reg = "HIGH_VOL"
            else:
                norm_reg = "OTHER"

            if norm_reg not in regime_stats:
                regime_stats[norm_reg] = {"trades": 0, "wins": 0, "losses": 0, "sl_hits": 0, "tp_hits": 0, "net_pnl": 0.0}
            regime_stats[norm_reg]["trades"] += 1
            if (t.net_pnl or 0) > 0:
                regime_stats[norm_reg]["wins"] += 1
            else:
                regime_stats[norm_reg]["losses"] += 1
            if t.reason_for_exit == "STOP_LOSS_HIT":
                regime_stats[norm_reg]["sl_hits"] += 1
            elif t.reason_for_exit == "TARGET_HIT":
                regime_stats[norm_reg]["tp_hits"] += 1
            regime_stats[norm_reg]["net_pnl"] += round(t.net_pnl or 0.0, 2)

        for reg, data in regime_stats.items():
            cnt = data["trades"]
            data["win_rate_pct"] = round((data["wins"] / cnt * 100.0) if cnt > 0 else 0.0, 1)

        self.regime_performance = regime_stats

        # 5. Segment by Time of Day
        time_stats: Dict[str, Dict[str, Any]] = {}
        for t in trades:
            bucket = Phase8RegimeSegmenter.classify_time_bucket(t.entry_time)
            if bucket not in time_stats:
                time_stats[bucket] = {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0}
            time_stats[bucket]["trades"] += 1
            if (t.net_pnl or 0) > 0:
                time_stats[bucket]["wins"] += 1
            else:
                time_stats[bucket]["losses"] += 1
            time_stats[bucket]["net_pnl"] += round(t.net_pnl or 0.0, 2)

        for b, data in time_stats.items():
            cnt = data["trades"]
            data["win_rate_pct"] = round((data["wins"] / cnt * 100.0) if cnt > 0 else 0.0, 1)

        self.time_bucket_performance = time_stats

        # 6. Evaluate Bounded Parameter Changes Based Strictly on Trending Segments
        trending_data = regime_stats.get("TRENDING", {"trades": 0, "sl_hits": 0, "tp_hits": 0, "win_rate_pct": 50.0})
        trending_trades = trending_data["trades"]

        insights = [
            f"Segmented analysis on {total} completed trades across {len(regime_stats)} regimes.",
            f"Trending Regime: {trending_trades} trades, Win Rate {trending_data.get('win_rate_pct', 0.0)}%."
        ]

        # Determine if an adjustment is indicated
        current_sl = self.current_atr_sl_multiplier
        step = getattr(settings, "MAX_ATR_PARAM_STEP", 0.1)
        min_bound = getattr(settings, "MIN_ATR_SL_MULTIPLIER", 1.3)
        max_bound = getattr(settings, "MAX_ATR_SL_MULTIPLIER", 2.0)
        target_rr = getattr(settings, "TARGET_RISK_REWARD_RATIO", 2.0)

        proposed_sl = current_sl
        proposal_reason = ""

        # Only evaluate parameter changes if trending regime has sufficient sample (>= 30 trades)
        if trending_trades >= 30:
            sl_hits = trending_data.get("sl_hits", 0)
            tp_hits = trending_data.get("tp_hits", 0)
            
            if sl_hits > tp_hits * 1.5 and current_sl < max_bound:
                proposed_sl = round(min(max_bound, current_sl + step), 2)
                proposal_reason = (
                    f"Stop-loss hit rate ({sl_hits}) exceeds target hits ({tp_hits}) by >1.5x in trending regime. "
                    f"Recommend widening ATR SL multiplier from {current_sl:.2f}x to {proposed_sl:.2f}x (+{step:.1f} bounded)."
                )
            elif tp_hits > sl_hits * 2.0 and current_sl > min_bound:
                proposed_sl = round(max(min_bound, current_sl - step), 2)
                proposal_reason = (
                    f"Target conversion is exceptionally high ({tp_hits} vs {sl_hits} SL hits). "
                    f"Recommend tightening ATR SL multiplier from {current_sl:.2f}x to {proposed_sl:.2f}x (-{step:.1f} bounded)."
                )

        # 7. Formulate Bounded, Fixed R:R Proposal
        pending_count = db.query(ParameterProposal).filter(ParameterProposal.status == "PENDING").count()

        if proposed_sl != current_sl and proposal_reason:
            proposed_tp = round(proposed_sl * target_rr, 2)
            insights.append(proposal_reason)

            # Check for existing duplicate pending proposal
            existing_pending = db.query(ParameterProposal).filter(
                ParameterProposal.param_name == "atr_sl_multiplier",
                ParameterProposal.new_value == proposed_sl,
                ParameterProposal.status == "PENDING"
            ).first()

            if not existing_pending:
                stats_payload = {
                    "total_trades": total,
                    "win_rate_pct": win_rate,
                    "regime_stats": regime_stats,
                    "time_stats": time_stats
                }
                proposal = ParameterProposal(
                    param_name="atr_sl_multiplier",
                    old_value=current_sl,
                    new_value=proposed_sl,
                    tp_multiplier=proposed_tp,
                    target_rr=target_rr,
                    status="PENDING",
                    evidence=proposal_reason,
                    stats_json=json.dumps(stats_payload),
                    sample_size=total,
                    win_rate_pct=win_rate,
                    created_at=datetime.datetime.utcnow()
                )
                db.add(proposal)
                db.commit()
                db.refresh(proposal)

                pending_count += 1
                alert_text = (
                    f"💡 <b>New Parameter Proposal #{proposal.id} Generated:</b>\n"
                    f"• Parameter: ATR SL Multiplier\n"
                    f"• Change: {current_sl:.2f}x ➔ {proposed_sl:.2f}x (bounded)\n"
                    f"• Target R:R: 1:{target_rr:.1f} (TP Multiplier: {proposed_tp:.2f}x)\n"
                    f"• Evidence: {proposal_reason}\n"
                    f"• Action: Approve via <code>/approve_param {proposal.id}</code> or Dashboard."
                )
                LiveAuditLogger.log("PARAM_PROPOSAL_CREATED", f"Proposal #{proposal.id}: SL {current_sl:.2f} -> {proposed_sl:.2f}")
                logger.info(f"[SafeLearner] Created Parameter Proposal #{proposal.id}")
                try:
                    from app.notifications.dispatcher import notifier
                    notifier.notify_alert({"type": "PARAM_PROPOSAL", "message": alert_text})
                except Exception:
                    pass
        else:
            insights.append("Parameters remain optimal within current volatility and regime constraints.")

        self.knowledge_summary = {
            "total_trades_analyzed": total,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "overall_win_rate_pct": round(win_rate, 1),
            "best_symbols": best_symbols[:5],
            "caution_symbols": caution_symbols[:5],
            "current_sl_multiplier": self.current_atr_sl_multiplier,
            "current_tp_multiplier": self.current_atr_tp_multiplier,
            "current_target_rr": self.current_target_rr,
            "sample_threshold": min_sample,
            "sample_met": True,
            "regime_segments": regime_stats,
            "time_segments": time_stats,
            "insights": insights,
            "pending_proposals_count": pending_count,
            "last_updated": now_str,
            "learning_status": "OPTIMAL"
        }

        LiveAuditLogger.log(
            "MARKET_KNOWLEDGE_UPDATED",
            f"Analyzed {total} trades across {len(regime_stats)} regimes. Trending Win Rate: {trending_data.get('win_rate_pct', 0.0)}%"
        )
        return self.knowledge_summary

    def approve_proposal(self, db: Session, proposal_id: int, approved_by: str = "TELEGRAM") -> Dict[str, Any]:
        """
        Approves a parameter proposal:
        1. Updates proposal status to APPLIED.
        2. Logs entry to ParameterVersionHistory with rollback metadata.
        3. Applies parameter to active learner state.
        """
        proposal = db.query(ParameterProposal).filter(ParameterProposal.id == proposal_id).first()
        if not proposal:
            return {"success": False, "error": f"Proposal #{proposal_id} not found."}

        if proposal.status != "PENDING":
            return {"success": False, "error": f"Proposal #{proposal_id} is already {proposal.status}."}

        # Determine next version number
        last_version = db.query(ParameterVersionHistory).order_by(ParameterVersionHistory.version_number.desc()).first()
        next_ver = (last_version.version_number + 1) if last_version else 2

        old_val = self.current_atr_sl_multiplier
        new_val = proposal.new_value
        tp_val = proposal.tp_multiplier

        # Record version history
        hist = ParameterVersionHistory(
            version_number=next_ver,
            param_name=proposal.param_name,
            applied_value=new_val,
            tp_multiplier=tp_val,
            previous_value=old_val,
            applied_at=datetime.datetime.utcnow(),
            approved_by=approved_by,
            change_summary=f"Approved Proposal #{proposal.id}: {old_val:.2f} -> {new_val:.2f} (TP {tp_val:.2f}, R:R 1:{proposal.target_rr:.1f})"
        )
        db.add(hist)

        # Update proposal state
        proposal.status = "APPLIED"
        proposal.resolved_at = datetime.datetime.utcnow()
        db.commit()

        # Update active learner state
        self.current_atr_sl_multiplier = new_val
        self.current_atr_tp_multiplier = tp_val
        self.current_target_rr = proposal.target_rr
        self.knowledge_summary["current_sl_multiplier"] = new_val
        self.knowledge_summary["current_tp_multiplier"] = tp_val
        self.knowledge_summary["active_version"] = next_ver

        msg = f"Proposal #{proposal_id} Approved (v{next_ver}): SL={new_val:.2f}x, TP={tp_val:.2f}x"
        LiveAuditLogger.log("PARAM_PROPOSAL_APPLIED", msg)
        logger.info(f"[SafeLearner] {msg}")

        return {
            "success": True,
            "version": next_ver,
            "param_name": proposal.param_name,
            "old_value": old_val,
            "new_value": new_val,
            "tp_multiplier": tp_val,
            "approved_by": approved_by
        }

    def reject_proposal(self, db: Session, proposal_id: int, reason: str = "Operator Rejected") -> Dict[str, Any]:
        """Rejects a parameter proposal."""
        proposal = db.query(ParameterProposal).filter(ParameterProposal.id == proposal_id).first()
        if not proposal:
            return {"success": False, "error": f"Proposal #{proposal_id} not found."}

        if proposal.status != "PENDING":
            return {"success": False, "error": f"Proposal #{proposal_id} is already {proposal.status}."}

        proposal.status = "REJECTED"
        proposal.resolved_at = datetime.datetime.utcnow()
        db.commit()

        LiveAuditLogger.log("PARAM_PROPOSAL_REJECTED", f"Proposal #{proposal_id} rejected: {reason}")
        return {"success": True, "proposal_id": proposal_id, "status": "REJECTED"}

    def rollback_to_previous_version(self, db: Session, approved_by: str = "TELEGRAM") -> Dict[str, Any]:
        """
        Single-command rollback: restores parameter values to the previous version in history.
        """
        latest_hist = db.query(ParameterVersionHistory).order_by(ParameterVersionHistory.version_number.desc()).first()
        if not latest_hist or latest_hist.version_number <= 1:
            # Fallback to defaults
            old_val = self.current_atr_sl_multiplier
            default_val = getattr(settings, "DEFAULT_ATR_SL_MULTIPLIER", 1.5)
            target_rr = getattr(settings, "TARGET_RISK_REWARD_RATIO", 2.0)
            default_tp = round(default_val * target_rr, 2)

            self.current_atr_sl_multiplier = default_val
            self.current_atr_tp_multiplier = default_tp
            self.knowledge_summary["current_sl_multiplier"] = default_val
            self.knowledge_summary["current_tp_multiplier"] = default_tp

            return {
                "success": True,
                "action": "RESET_TO_DEFAULT",
                "old_value": old_val,
                "restored_value": default_val,
                "tp_multiplier": default_tp,
                "version": 1
            }

        prev_val = latest_hist.previous_value
        target_rr = getattr(settings, "TARGET_RISK_REWARD_RATIO", 2.0)
        prev_tp = round(prev_val * target_rr, 2)
        next_ver = latest_hist.version_number + 1

        # Record rollback as a new version entry
        rollback_entry = ParameterVersionHistory(
            version_number=next_ver,
            param_name=latest_hist.param_name,
            applied_value=prev_val,
            tp_multiplier=prev_tp,
            previous_value=latest_hist.applied_value,
            applied_at=datetime.datetime.utcnow(),
            approved_by=approved_by,
            change_summary=f"Rolled back v{latest_hist.version_number} to previous value {prev_val:.2f}"
        )
        db.add(rollback_entry)
        db.commit()

        # Update active learner state
        old_val = self.current_atr_sl_multiplier
        self.current_atr_sl_multiplier = prev_val
        self.current_atr_tp_multiplier = prev_tp
        self.knowledge_summary["current_sl_multiplier"] = prev_val
        self.knowledge_summary["current_tp_multiplier"] = prev_tp
        self.knowledge_summary["active_version"] = next_ver

        msg = f"Rollback executed (v{next_ver}): Restored SL={prev_val:.2f}x, TP={prev_tp:.2f}x"
        LiveAuditLogger.log("PARAM_ROLLBACK", msg)
        logger.info(f"[SafeLearner] {msg}")

        return {
            "success": True,
            "action": "ROLLBACK_APPLIED",
            "old_value": old_val,
            "restored_value": prev_val,
            "tp_multiplier": prev_tp,
            "version": next_ver
        }

    def get_version_history(self, db: Session) -> List[Dict[str, Any]]:
        rows = db.query(ParameterVersionHistory).order_by(ParameterVersionHistory.version_number.desc()).all()
        return [
            {
                "id": r.id,
                "version_number": r.version_number,
                "param_name": r.param_name,
                "applied_value": r.applied_value,
                "tp_multiplier": r.tp_multiplier,
                "previous_value": r.previous_value,
                "applied_at": r.applied_at.isoformat() if r.applied_at else None,
                "approved_by": r.approved_by,
                "change_summary": r.change_summary
            }
            for r in rows
        ]

    def get_pending_proposals(self, db: Session) -> List[Dict[str, Any]]:
        rows = db.query(ParameterProposal).filter(ParameterProposal.status == "PENDING").all()
        return [
            {
                "id": r.id,
                "param_name": r.param_name,
                "old_value": r.old_value,
                "new_value": r.new_value,
                "tp_multiplier": r.tp_multiplier,
                "target_rr": r.target_rr,
                "status": r.status,
                "evidence": r.evidence,
                "sample_size": r.sample_size,
                "win_rate_pct": r.win_rate_pct,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in rows
        ]

    def get_knowledge(self) -> Dict[str, Any]:
        return self.knowledge_summary

market_learner = MarketKnowledgeLearner()
