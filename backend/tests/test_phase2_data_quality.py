import pytest
import time
from app.data.data_quality import DataQualityService, DataQualityRecord

def test_data_quality_recording():
    DataQualityService.record_update(
        dataset_name="TEST_FEED",
        source="TEST_PROVIDER",
        status="LIVE",
        latency_ms=50
    )
    report = DataQualityService.get_quality_report()
    assert report["overall_status"] in ["HEALTHY", "WARNING_STALE"]
    assert "TEST_FEED" in report["datasets"]
    assert report["datasets"]["TEST_FEED"]["source"] == "TEST_PROVIDER"

def test_stale_data_warning():
    record = DataQualityRecord(
        dataset_name="STALE_FEED",
        source="OLD_BROKER",
        status="LIVE"
    )
    # Check is_stale with threshold of 0 seconds
    assert record.is_stale(max_seconds=0) is True
    d = record.to_dict()
    assert "age_seconds" in d
