import os
import pytest
from app.backtest.phase6_validator import Phase6EmpiricalValidator
from app.backtest.phase6_report import Phase6ReportGenerator

def test_phase6_report_generation_to_disk():
    val_data = Phase6EmpiricalValidator.execute_validation(symbol="RELIANCE")
    report_res = Phase6ReportGenerator.generate_and_save(val_data, output_dir="reports")

    assert os.path.exists(report_res["markdown_path"])
    assert os.path.exists(report_res["json_path"])
    assert "PHASE 6 — STRATEGY VALIDATION AUDIT REPORT" in report_res["markdown_content"]
    assert "FINAL VERDICT" in report_res["markdown_content"]
