from app.core.config import settings
from app.data.base import MarketDataProvider
from app.data.mock_provider import MockMarketDataProvider
from app.data.csv_provider import HistoricalCSVMarketDataProvider
from app.data.broker_provider import BrokerMarketDataProvider

from app.data.live_market_provider import LiveNSEMarketDataProvider

_provider_instance = None

def get_market_data_provider() -> MarketDataProvider:
    """
    Factory resolving the active MarketDataProvider based on configuration.
    Supports: "angelone", "live", "nse", "broker", "historical", "mock"
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_type = (settings.MARKET_DATA_PROVIDER or "live").lower()
    
    if provider_type in ("live", "nse", "angelone"):
        _provider_instance = LiveNSEMarketDataProvider()
    elif provider_type == "broker":
        _provider_instance = BrokerMarketDataProvider()
    elif provider_type == "historical":
        _provider_instance = HistoricalCSVMarketDataProvider()
    else:
        _provider_instance = MockMarketDataProvider()
        
    return _provider_instance
