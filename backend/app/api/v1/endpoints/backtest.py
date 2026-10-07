import os
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.data.historical_loader import HistoricalDataLoader
from app.strategies.registry import StrategyRegistry
from app.backtest.engine import BacktestEngine, BacktestConfig
from app.backtest.walk_forward import WalkForwardAnalyzer
from app.backtest.sensitivity import ParameterSensitivityAnalyzer
from app.backtest.monte_carlo import MonteCarloAnalyzer
from app.backtest.comparison import StrategyComparisonService
from app.backtest.qualification import DatasetQualificationService
from app.backtest.multi_symbol import MultiSymbolBacktestService
from app.backtest.segmentation import GranularSegmentationService
from app.backtest.rolling_walk_forward import RollingWalkForwardService
from app.backtest.overfitting import OverfittingDetector
from app.backtest.monte_carlo_enhanced import EnhancedMonteCarloAnalyzer
from app.backtest.validation_report import StrategyValidationReportGenerator
from app.backtest.data_quality_audit import HistoricalDataQualityAuditEngine
from app.backtest.phase6_validator import Phase6EmpiricalValidator
from app.backtest.phase6_report import Phase6ReportGenerator
from app.schemas.schemas import (
    BacktestRunRequest,
    BacktestResultResponse,
    WalkForwardRequest,
    WalkForwardResponse,
    MonteCarloRequest,
    MonteCarloResponse,
    ParameterAnalysisRequest,
    ParameterAnalysisResponse
)

router = APIRouter()

# In-memory store for backtest execution runs
_backtest_runs: Dict[int, Dict[str, Any]] = {}
_run_counter = 0

def _get_dataset_df(symbol: str, dataset_file: Optional[str] = None):
    data_dir = "data/historical"
    if dataset_file and os.path.exists(dataset_file):
        file_path = dataset_file
    else:
        matched = None
        if os.path.exists(data_dir):
            for f in os.listdir(data_dir):
                if symbol.upper() in f.upper() and f.endswith(".csv"):
                    matched = os.path.join(data_dir, f)
                    break
        file_path = matched or os.path.join(data_dir, "SAMPLE_RELIANCE_5m.csv")

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Historical dataset file not found: {file_path}. Please place CSV data in data/historical/."
        )

    return HistoricalDataLoader.load_csv(file_path, symbol=symbol)

@router.get("/strategies")
def get_registered_strategies():
    return StrategyRegistry.list_strategies()

@router.get("/datasets")
def get_available_datasets():
    return HistoricalDataLoader.get_available_datasets()

@router.get("/results")
def get_latest_backtest_results():
    if not _backtest_runs:
        df = _get_dataset_df("RELIANCE")
        engine = BacktestEngine()
        res = engine.run(df, "RELIANCE")
        _backtest_runs[1] = res
        return res
    latest_id = max(_backtest_runs.keys())
    return _backtest_runs[latest_id]

@router.get("/validation-report")
def get_validation_report(symbol: str = Query("RELIANCE")):
    df = _get_dataset_df(symbol)
    engine = BacktestEngine()
    bt_res = engine.run(df, symbol)

    qualification = DatasetQualificationService.qualify_dataset("SAMPLE_RELIANCE_5m.csv", len(df))
    wf_res = WalkForwardAnalyzer.analyze(df, symbol)
    overfitting = OverfittingDetector.calculate_overfitting_score(
        train_pf=wf_res["training_period"]["profit_factor"],
        val_pf=wf_res["validation_period"]["profit_factor"],
        oos_pf=wf_res["out_of_sample_period"]["profit_factor"],
        train_return=wf_res["training_period"]["return_pct"],
        oos_return=wf_res["out_of_sample_period"]["return_pct"]
    )
    mc_res = EnhancedMonteCarloAnalyzer.simulate_dual_mode(bt_res.get("trades", []), iterations=1000)

    return StrategyValidationReportGenerator.generate_report(
        backtest_result=bt_res,
        qualification=qualification,
        overfitting=overfitting,
        walk_forward=wf_res,
        monte_carlo=mc_res
    )

@router.get("/comparison/matrix")
def get_strategy_comparison(symbol: str = Query("RELIANCE")):
    df = _get_dataset_df(symbol)
    return StrategyComparisonService.compare(df, symbol=symbol)

# ==========================================
# PHASE 6 ENDPOINTS: EMPIRICAL VALIDATION & REPORTS
# ==========================================

@router.post("/phase6/validate")
def execute_phase6_validation(symbol: str = Query("RELIANCE"), universe_id: str = Query("LIQUID_TOP_10")):
    val_data = Phase6EmpiricalValidator.execute_validation(symbol=symbol, universe_id=universe_id)
    # Save reports to disk
    report_files = Phase6ReportGenerator.generate_and_save(val_data)
    val_data["report_files"] = report_files
    return val_data

@router.get("/phase6/report")
def get_phase6_report():
    md_path = "reports/phase6_strategy_validation.md"
    json_path = "reports/phase6_strategy_validation.json"
    if not os.path.exists(md_path) or not os.path.exists(json_path):
        val_data = Phase6EmpiricalValidator.execute_validation()
        Phase6ReportGenerator.generate_and_save(val_data)

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    return {
        "markdown_content": md_content,
        "validation_data": json_data
    }

@router.get("/phase6/quality-audit")
def get_dataset_quality_audit(symbol: str = Query("RELIANCE")):
    df = _get_dataset_df(symbol)
    return HistoricalDataQualityAuditEngine.audit_dataset(df, symbol=symbol)

@router.post("/run", response_model=BacktestResultResponse)
def run_backtest(req: BacktestRunRequest):
    global _run_counter
    df = _get_dataset_df(req.symbol, req.dataset_file)

    config = BacktestConfig(
        strategy_id=req.strategy_id,
        initial_capital=req.initial_capital,
        risk_per_trade_pct=req.risk_per_trade_pct,
        max_capital_exposure_pct=req.max_capital_exposure_pct,
        max_daily_loss_amount=req.max_daily_loss_amount,
        exit_time=req.exit_time,
        slippage_pct=req.slippage_pct,
        same_candle_conflict_resolution=req.same_candle_conflict_resolution,
        strategy_params=req.strategy_params
    )

    engine = BacktestEngine(config)
    result = engine.run(df, symbol=req.symbol)

    qualification = DatasetQualificationService.qualify_dataset(
        filename=req.dataset_file or "SAMPLE_RELIANCE_5m.csv",
        total_candles=len(df)
    )
    result["qualification"] = qualification

    _run_counter += 1
    result["id"] = _run_counter
    _backtest_runs[_run_counter] = result

    return result

@router.post("/walk-forward", response_model=WalkForwardResponse)
def run_walk_forward_validation(req: WalkForwardRequest):
    df = _get_dataset_df(req.symbol, req.dataset_file)
    cfg = BacktestConfig(strategy_id=req.strategy_id, initial_capital=req.initial_capital)
    return WalkForwardAnalyzer.analyze(df, symbol=req.symbol, config=cfg)

@router.post("/parameter-analysis", response_model=ParameterAnalysisResponse)
def run_parameter_sensitivity(req: ParameterAnalysisRequest):
    df = _get_dataset_df(req.symbol, req.dataset_file)
    cfg = BacktestConfig(strategy_id=req.strategy_id, initial_capital=req.initial_capital)
    return ParameterSensitivityAnalyzer.analyze(df, symbol=req.symbol, base_config=cfg)

@router.post("/monte-carlo", response_model=MonteCarloResponse)
def run_monte_carlo_simulation(req: MonteCarloRequest):
    trades = req.trades
    if not trades and _backtest_runs:
        latest_id = max(_backtest_runs.keys())
        trades = _backtest_runs[latest_id].get("trades", [])
    
    return MonteCarloAnalyzer.simulate(
        trades=trades or [],
        initial_capital=req.initial_capital,
        iterations=req.iterations
    )

@router.post("/multi-symbol")
def run_multi_symbol_backtest(universe_id: str = Query("LIQUID_TOP_10")):
    return MultiSymbolBacktestService.run_universe_backtest(universe_id=universe_id)

@router.post("/segmentation")
def run_segmentation_analysis(backtest_id: Optional[int] = None):
    trades = []
    initial_capital = 100000.0
    return_pct = 0.0
    pf = 1.0

    if _backtest_runs:
        bid = backtest_id or max(_backtest_runs.keys())
        target_run = _backtest_runs.get(bid, {})
        trades = target_run.get("trades", [])
        initial_capital = target_run.get("initial_capital", 100000.0)
        return_pct = target_run.get("return_pct", 0.0)
        pf = target_run.get("profit_factor", 1.0)

    regimes = GranularSegmentationService.analyze_market_regimes(trades)
    time_of_day = GranularSegmentationService.analyze_time_of_day(trades)
    long_short = GranularSegmentationService.analyze_long_vs_short(trades)
    cost_slippage = GranularSegmentationService.analyze_cost_and_slippage_sensitivity(trades, initial_capital)
    benchmarks = GranularSegmentationService.compare_benchmarks(return_pct, pf, len(trades))

    return {
        "regimes": regimes,
        "time_of_day": time_of_day,
        "long_short": long_short,
        "cost_slippage": cost_slippage,
        "benchmarks": benchmarks
    }

@router.post("/rolling-walk-forward")
def run_rolling_walk_forward(symbol: str = Query("RELIANCE"), windows: int = Query(3, ge=2, le=6)):
    df = _get_dataset_df(symbol)
    return RollingWalkForwardService.run_rolling_walk_forward(df, symbol=symbol, windows_count=windows)

@router.post("/overfitting-score")
def evaluate_overfitting_score(symbol: str = Query("RELIANCE")):
    df = _get_dataset_df(symbol)
    wf_res = WalkForwardAnalyzer.analyze(df, symbol=symbol)
    train_pf = wf_res["training_period"]["profit_factor"]
    val_pf = wf_res["validation_period"]["profit_factor"]
    oos_pf = wf_res["out_of_sample_period"]["profit_factor"]
    train_ret = wf_res["training_period"]["return_pct"]
    oos_ret = wf_res["out_of_sample_period"]["return_pct"]

    return OverfittingDetector.calculate_overfitting_score(
        train_pf=train_pf,
        val_pf=val_pf,
        oos_pf=oos_pf,
        train_return=train_ret,
        oos_return=oos_ret
    )

@router.post("/enhanced-monte-carlo")
def run_enhanced_monte_carlo(iterations: int = Query(1000, ge=100, le=5000)):
    trades = []
    if _backtest_runs:
        latest_id = max(_backtest_runs.keys())
        trades = _backtest_runs[latest_id].get("trades", [])

    return EnhancedMonteCarloAnalyzer.simulate_dual_mode(
        trades=trades,
        initial_capital=100000.0,
        iterations=iterations
    )

@router.get("/{backtest_id}")
def get_backtest_by_id(backtest_id: int):
    if backtest_id not in _backtest_runs:
        raise HTTPException(status_code=404, detail="Backtest ID not found")
    return _backtest_runs[backtest_id]

@router.get("/{backtest_id}/trades")
def get_backtest_trades(backtest_id: int):
    if backtest_id not in _backtest_runs:
        raise HTTPException(status_code=404, detail="Backtest ID not found")
    return _backtest_runs[backtest_id].get("trades", [])

@router.get("/{backtest_id}/equity")
def get_backtest_equity_curve(backtest_id: int):
    if backtest_id not in _backtest_runs:
        raise HTTPException(status_code=404, detail="Backtest ID not found")
    return _backtest_runs[backtest_id].get("equity_curve", [])

@router.get("/{backtest_id}/drawdown")
def get_backtest_drawdown(backtest_id: int):
    if backtest_id not in _backtest_runs:
        raise HTTPException(status_code=404, detail="Backtest ID not found")
    eq = _backtest_runs[backtest_id].get("equity_curve", [])
    return [{"timestamp": e["timestamp"], "drawdown": e["drawdown"], "drawdown_pct": e["drawdown_pct"]} for e in eq]
