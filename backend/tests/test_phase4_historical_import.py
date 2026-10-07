import pytest
from app.data.importer import DataImportService

def test_import_and_validate_csv(tmp_path):
    csv_content = (
        "timestamp,open,high,low,close,volume\n"
        "2026-08-25 09:15:00,100.0,105.0,99.0,103.0,50000\n"
        "2026-08-25 09:20:00,103.0,107.0,102.0,106.0,60000\n"
        "2026-08-25 09:25:00,106.0,108.0,104.0,105.0,40000\n"
        "2026-08-25 09:30:00,105.0,109.0,103.0,107.0,70000\n"
        "2026-08-25 09:35:00,107.0,110.0,106.0,109.0,80000\n"
        "2026-08-25 09:40:00,109.0,111.0,108.0,110.0,90000\n"
        "2026-08-25 09:45:00,110.0,112.0,109.0,111.0,55000\n"
        "2026-08-25 09:50:00,111.0,113.0,110.0,112.0,65000\n"
        "2026-08-25 09:55:00,112.0,114.0,111.0,113.0,75000\n"
        "2026-08-25 10:00:00,113.0,115.0,112.0,114.0,85000\n"
    ).encode("utf-8")

    res = DataImportService.import_and_validate(
        content=csv_content,
        filename="test_upload.csv",
        symbol="TESTSTOCK",
        save_dir=str(tmp_path)
    )

    assert res["validation_status"] == "PASSED"
    assert res["total_candles"] == 10
    assert res["symbol"] == "TESTSTOCK"
    assert res["corporate_action_status"] == "CORPORATE_ACTION_ADJUSTED"

def test_import_invalid_ohlc_rejection(tmp_path):
    bad_csv = (
        "timestamp,open,high,low,close,volume\n"
        "2026-08-25 09:15:00,100.0,90.0,99.0,103.0,50000\n" # Invalid high < open
    ).encode("utf-8")

    with pytest.raises(ValueError):
        DataImportService.import_and_validate(
            content=bad_csv,
            filename="bad_upload.csv",
            symbol="BADSTOCK",
            save_dir=str(tmp_path)
        )
