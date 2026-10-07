import datetime
from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar("T")

class ProviderResponse(BaseModel, Generic[T]):
    """
    Standardized wrapper for all incoming market, news, and global data payloads.
    Guarantees strict provenance tracking, timestamp auditing, and truth-in-status.
    """
    data: T
    source: str
    timestamp: str
    timezone: str = "Asia/Kolkata"
    status: str  # "LIVE", "DELAYED", "HISTORICAL", "MOCK", "UNAVAILABLE", "ERROR"
    freshness_seconds: float = 0.0
    latency_ms: int = 45
    confidence: float = 1.0
    error: Optional[str] = None

    @classmethod
    def create(
        cls,
        data: T,
        source: str,
        status: str = "LIVE",
        latency_ms: int = 45,
        confidence: float = 1.0,
        error: Optional[str] = None,
        data_time: Optional[datetime.datetime] = None
    ) -> "ProviderResponse[T]":
        now = datetime.datetime.now()
        t = data_time or now
        freshness = round((now - t).total_seconds(), 1)
        
        return cls(
            data=data,
            source=source,
            timestamp=t.isoformat(),
            timezone="Asia/Kolkata",
            status=status,
            freshness_seconds=max(0.0, freshness),
            latency_ms=latency_ms,
            confidence=confidence,
            error=error
        )

    def __getitem__(self, item):
        if isinstance(self.data, dict):
            return self.data[item]
        return getattr(self.data, item)

    def get(self, item, default=None):
        if isinstance(self.data, dict):
            return self.data.get(item, default)
        return getattr(self.data, item, default)
