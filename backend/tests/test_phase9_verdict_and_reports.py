"""
Phase 9 — Verdict & Automated Reporting Tests

Tests the 5 allowed scientific verdicts, prohibited language auditing,
and automated generation of 20-section daily session and cumulative pilot reports.
"""
import os
import json
import pytest
from app.phase9.verdict_engine import Phase9VerdictEngine
from app.phase9.reporting import Phase9ReportGenerator


def test_allowed_verdicts_only():
    """Verify verdict engine only returns one of the 5 allowed scientific verdicts."""
    v1 = Phase9VerdictEngine.determine_verdict(10, expectancy=50.0, win_rate=60.0, profit_factor=1.5)
    assert v1["verdict"] == "INSUFFICIENT LIVE PAPER DATA"

    v2 = Phase9VerdictEngine.determine_verdict(45, expectancy=50.0, win_rate=60.0, profit_factor=1.5)
    assert v2["verdict"] == "EARLY PAPER EVIDENCE"

    v3 = Phase9VerdictEngine.determine_verdict(150, expectancy=80.0, win_rate=58.0, profit_factor=1.4)
    assert v3["verdict"] == "PRELIMINARY PAPER EVIDENCE"

    v4 = Phase9VerdictEngine.determine_verdict(350, expectancy=100.0, win_rate=57.0, profit_factor=1.45)
    assert v4["verdict"] == "EMPIRICAL PAPER EVIDENCE"

    v5 = Phase9VerdictEngine.determine_verdict(550, expectancy=120.0, win_rate=58.0, profit_factor=1.5)
    assert v5["verdict"] == "HIGH-CONFIDENCE PAPER CANDIDATE"

    for v in [v1, v2, v3, v4, v5]:
        assert v["verdict"] in Phase9VerdictEngine.ALLOWED_VERDICTS


def test_prohibited_terms_audit():
    """Verify audit_text flags forbidden promotional terms."""
    clean_text = "The empirical paper trading pilot observed an expectancy of 120 INR across 300 trades."
    violations = Phase9VerdictEngine.audit_text(clean_text)
    assert len(violations) == 0

    bad_text = "This proven strategy will make money and offers guaranteed profitable returns with safe investment."
    violations = Phase9VerdictEngine.audit_text(bad_text)
    assert "proven strategy" in violations
    assert "will make money" in violations
    assert "guaranteed" in violations
    assert "profitable" in violations
    assert "safe investment" in violations


def test_generate_daily_session_report():
    """Verify 20-section daily session report is generated on disk."""
    session_data = {
        "session_id": "SESS-2026-09-04-TEST",
        "trading_date": "2026-09-04",
        "provider": "ZERODHA_KITE",
        "status": "CLOSED",
        "valid_ticks": 12000,
        "rejected_ticks": 2,
        "generated_signals": 4,
        "approved_signals": 3,
        "rejected_signals": 1,
        "executed_paper_trades": 3,
        "exits": 3,
        "gross_pnl": 750.0,
        "transaction_costs": 120.0,
        "slippage": 15.0,
        "net_pnl": 615.0,
        "max_drawdown": 100.0,
        "daily_loss": 0.0,
        "kill_switch_events": 0,
        "data_quality_incidents": 0,
    }

    trades = [
        {"net_pnl": 300.0, "gross_pnl": 350.0, "total_cost": 40.0, "entry_slippage": 5.0, "exit_slippage": 5.0, "holding_minutes": 35.0, "market_regime": "TRENDING_UP", "time_of_day_bucket": "10:00–11:30", "symbol": "RELIANCE"},
        {"net_pnl": 400.0, "gross_pnl": 450.0, "total_cost": 40.0, "entry_slippage": 5.0, "exit_slippage": 5.0, "holding_minutes": 45.0, "market_regime": "TRENDING_UP", "time_of_day_bucket": "10:00–11:30", "symbol": "TCS"},
        {"net_pnl": -85.0, "gross_pnl": -50.0, "total_cost": 40.0, "entry_slippage": 5.0, "exit_slippage": 5.0, "holding_minutes": 25.0, "market_regime": "RANGE_BOUND", "time_of_day_bucket": "11:30–13:30", "symbol": "INFY"},
    ]

    res = Phase9ReportGenerator.generate_daily_report(session_data, trades)
    assert os.path.exists(res["markdown_path"])
    assert os.path.exists(res["json_path"])

    with open(res["markdown_path"], "r", encoding="utf-8") as f:
        content = f.read()

    assert "PAPER TRADING ONLY — NO REAL MONEY ORDERS" in content
    assert "SESS-2026-09-04-TEST" in content
    assert "Net Realized P&L" in content

    with open(res["json_path"], "r", encoding="utf-8") as f:
        data = json.load(f)

    # Verify 20 sections are present in JSON
    for i in range(1, 21):
        matching_keys = [k for k in data.keys() if k.startswith(f"{i}_")]
        assert len(matching_keys) == 1, f"Missing section {i} in JSON report"


def test_generate_cumulative_report():
    """Verify cumulative pilot report is generated on disk."""
    res = Phase9ReportGenerator.generate_cumulative_report()
    assert os.path.exists(res["markdown_path"])
    assert os.path.exists(res["json_path"])

    with open(res["markdown_path"], "r", encoding="utf-8") as f:
        content = f.read()
    assert "Phase 9 Cumulative Controlled Paper Trading Pilot Report" in content
    assert "PAPER TRADING ONLY — NO REAL MONEY ORDERS" in content
