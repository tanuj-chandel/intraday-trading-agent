"""
Phase 9 — Concentration & Data Quality Impact Tests

Tests symbol concentration flags (Top 1 > 50%, Top 3 > 80%)
and correlation between feed latency and slippage/P&L.
"""
import pytest
from app.phase9.symbol_concentration import Phase9SymbolConcentrationEngine
from app.phase9.data_quality_impact import Phase9DataQualityImpactEngine


def test_symbol_concentration_flag():
    """Heavy reliance on 1 symbol must trigger HIGH_CONCENTRATION_RISK."""
    trades = [
        {"symbol": "RELIANCE", "net_pnl": 1000.0, "gross_pnl": 1050.0},
        {"symbol": "TCS", "net_pnl": 50.0, "gross_pnl": 70.0},
        {"symbol": "INFY", "net_pnl": 50.0, "gross_pnl": 60.0},
    ]

    conc = Phase9SymbolConcentrationEngine.analyze(trades)
    assert conc["active_symbols_count"] == 3
    assert conc["top1_contribution_pct"] > 50.0
    assert conc["concentration_risk"] == "HIGH_CONCENTRATION_RISK"
    assert "High concentration risk" in conc["warning"]


def test_symbol_well_diversified():
    """Even distribution should be WELL_DIVERSIFIED."""
    trades = [
        {"symbol": "RELIANCE", "net_pnl": 200.0, "gross_pnl": 220.0},
        {"symbol": "TCS", "net_pnl": 200.0, "gross_pnl": 220.0},
        {"symbol": "INFY", "net_pnl": 200.0, "gross_pnl": 220.0},
        {"symbol": "HDFCBANK", "net_pnl": 200.0, "gross_pnl": 220.0},
        {"symbol": "ICICIBANK", "net_pnl": 200.0, "gross_pnl": 220.0},
    ]

    conc = Phase9SymbolConcentrationEngine.analyze(trades)
    assert conc["concentration_risk"] == "WELL_DIVERSIFIED"


def test_data_quality_latency_correlation():
    """High latency trades correlate with higher slippage."""
    trades = [
        # Low latency (<100ms) with small slippage
        {"latency_ms": 25.0, "entry_slippage": 1.0, "exit_slippage": 1.0, "net_pnl": 200.0},
        {"latency_ms": 30.0, "entry_slippage": 1.5, "exit_slippage": 1.0, "net_pnl": 250.0},
        # High latency (>=100ms) with larger slippage
        {"latency_ms": 150.0, "entry_slippage": 8.0, "exit_slippage": 7.0, "net_pnl": 50.0},
        {"latency_ms": 200.0, "entry_slippage": 10.0, "exit_slippage": 9.0, "net_pnl": -30.0},
    ]

    dq = Phase9DataQualityImpactEngine.analyze(trades)
    assert dq["total_trades_analyzed"] == 4
    low_slip = dq["latency_breakdown"]["avg_slippage_low_latency_inr"]
    high_slip = dq["latency_breakdown"]["avg_slippage_high_latency_inr"]
    assert high_slip > low_slip
    assert any("latency" in f.lower() for f in dq["findings"])
