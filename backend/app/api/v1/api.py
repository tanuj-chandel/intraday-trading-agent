from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, market, stocks, news, signals, positions, trades, performance, premarket, paper_trading, system, backtest, data_management, live, phase9, learning, notifications
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(market.router, prefix="/market", tags=["Market Overview"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks & Technicals"])
api_router.include_router(news.router, prefix="/news", tags=["News & Sentiment"])
api_router.include_router(signals.router, prefix="/signals", tags=["Trading Signals"])
api_router.include_router(positions.router, prefix="/positions", tags=["Paper Positions"])
api_router.include_router(trades.router, prefix="/trades", tags=["Trade Journal"])
api_router.include_router(performance.router, prefix="/performance", tags=["Performance Metrics"])
api_router.include_router(premarket.router, prefix="/premarket", tags=["Pre-Market Intelligence"])
api_router.include_router(paper_trading.router, prefix="/paper-trading", tags=["Paper Trading Controls"])
api_router.include_router(system.router, prefix="/system", tags=["System & Controls"])
api_router.include_router(system.router, prefix="/trading", tags=["Emergency Stop Direct"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["Backtesting & Validation"])
api_router.include_router(data_management.router, prefix="/data", tags=["Data Connectors & Health"])
api_router.include_router(live.router, prefix="/live", tags=["Live Paper Trading"])
api_router.include_router(phase9.router, prefix="/phase9", tags=["Phase 9 Controlled Pilot"])
api_router.include_router(learning.router, prefix="/learning", tags=["Self-Learning & Optimization"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Mobile Alerts & Telegram"])


