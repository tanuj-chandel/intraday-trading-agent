from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.data.health_checker import DataProviderHealthChecker
from app.data.importer import DataImportService
from app.data.historical_loader import HistoricalDataLoader
from app.data.market_calendar import IndianMarketCalendar
from app.news.announcements import CorporateAnnouncementProvider

router = APIRouter()

@router.get("/health")
def get_data_health():
    """
    Returns full health status across Market Data, News, Global Cues, Corporate Disclosures, and Calendar.
    """
    return DataProviderHealthChecker.check_all_providers()

@router.get("/providers")
def get_providers_list():
    return {
        "market_data_adapters": [
            {"id": "zerodha", "name": "Zerodha Kite Connect v3", "type": "BROKER_API", "status": "ADAPTER_AVAILABLE"},
            {"id": "upstox", "name": "Upstox API v2", "type": "BROKER_API", "status": "ADAPTER_AVAILABLE"},
            {"id": "angelone", "name": "Angel One SmartAPI", "type": "BROKER_API", "status": "ADAPTER_AVAILABLE"},
            {"id": "historical", "name": "Historical CSV / Parquet", "type": "LOCAL_DATASET", "status": "ACTIVE"},
            {"id": "mock", "name": "Simulated Indian Market Feed", "type": "SIMULATOR", "status": "ACTIVE"}
        ],
        "news_connectors": [
            {"id": "nse_bse_filings", "name": "Official Exchange Announcements", "reliability": "LEVEL_1", "status": "CONNECTED"},
            {"id": "financial_rss", "name": "Tier-1 Financial Media Stream", "reliability": "LEVEL_2", "status": "CONNECTED"}
        ]
    }

@router.post("/test-connection")
def test_provider_connection(provider: str = Query("zerodha")):
    return DataProviderHealthChecker.check_all_providers()["market_data"]

@router.post("/import")
async def import_historical_dataset(
    file: UploadFile = File(...),
    symbol: str = Form("RELIANCE"),
    timeframe: str = Form("5m"),
    corporate_action_adjusted: bool = Form(True)
):
    """
    Uploads and validates historical CSV or Parquet market data files.
    """
    content = await file.read()
    try:
        res = DataImportService.import_and_validate(
            content=content,
            filename=file.filename,
            symbol=symbol,
            timeframe=timeframe,
            corporate_action_adjusted=corporate_action_adjusted
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/datasets")
def get_historical_datasets():
    return HistoricalDataLoader.get_available_datasets()

@router.get("/quality")
def get_data_quality():
    return DataProviderHealthChecker.check_all_providers()

@router.get("/calendar")
def get_market_calendar():
    return IndianMarketCalendar.get_session_status()

@router.get("/announcements")
def get_corporate_announcements(limit: int = Query(10, ge=1, le=50)):
    return CorporateAnnouncementProvider.get_latest_announcements(limit=limit)
