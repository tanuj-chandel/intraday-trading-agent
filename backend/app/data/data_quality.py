import datetime
from typing import Dict, Any, Optional
from app.core.config import settings

class DataQualityRecord:
    def __init__(
        self,
        dataset_name: str,
        source: str,
        status: str = "LIVE",  # "LIVE", "DELAYED", "MOCK", "STALE", "ERROR"
        latency_ms: int = 45,
        completeness_pct: float = 100.0,
        error_message: Optional[str] = None
    ):
        self.dataset_name = dataset_name
        self.source = source
        self.timestamp = datetime.datetime.now()
        self.status = status
        self.latency_ms = latency_ms
        self.completeness_pct = completeness_pct
        self.error_message = error_message

    def is_stale(self, max_seconds: int = settings.DATA_FRESHNESS_MAX_SECONDS) -> bool:
        age = (datetime.datetime.now() - self.timestamp).total_seconds()
        return age >= max_seconds

    def to_dict(self) -> Dict[str, Any]:
        age_seconds = round((datetime.datetime.now() - self.timestamp).total_seconds(), 1)
        stale = self.is_stale()
        computed_status = "STALE" if (stale and self.status == "LIVE") else self.status
        
        return {
            "dataset_name": self.dataset_name,
            "source": self.source,
            "status": computed_status,
            "age_seconds": age_seconds,
            "freshness": "FRESH" if age_seconds < 60 else ("ACCEPTABLE" if not stale else "STALE WARNING"),
            "latency_ms": self.latency_ms,
            "completeness_pct": self.completeness_pct,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }

class DataQualityService:
    """
    Central Data Provenance & Freshness Engine.
    Tracks and validates all incoming market data streams.
    """
    _records: Dict[str, DataQualityRecord] = {}

    @classmethod
    def record_update(
        cls,
        dataset_name: str,
        source: str,
        status: str = "LIVE",
        latency_ms: int = 45,
        completeness_pct: float = 100.0,
        error_message: Optional[str] = None
    ):
        cls._records[dataset_name] = DataQualityRecord(
            dataset_name=dataset_name,
            source=source,
            status=status,
            latency_ms=latency_ms,
            completeness_pct=completeness_pct,
            error_message=error_message
        )

    @classmethod
    def get_quality_report(cls) -> Dict[str, Any]:
        report = {}
        has_stale = False
        has_error = False

        for name, record in cls._records.items():
            d = record.to_dict()
            report[name] = d
            if d["status"] == "STALE":
                has_stale = True
            if d["status"] == "ERROR":
                has_error = True

        overall_status = "HEALTHY"
        if has_error:
            overall_status = "ERROR"
        elif has_stale:
            overall_status = "WARNING_STALE"

        return {
            "overall_status": overall_status,
            "total_datasets": len(cls._records),
            "datasets": report,
            "checked_at": datetime.datetime.now().isoformat()
        }
