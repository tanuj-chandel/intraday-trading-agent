from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.data.factory import get_market_data_provider
from app.news.aggregator import NewsAggregator
from app.premarket.analyzer import PreMarketAnalyzer
from app.technical.indicators import TechnicalAnalysis
from app.schemas.schemas import StockBase, StockScoreResponse, TechnicalIndicatorsResponse, CategorizedTopStocksResponse

router = APIRouter()
news_provider = NewsAggregator()

def get_premarket_analyzer() -> PreMarketAnalyzer:
    return PreMarketAnalyzer(get_market_data_provider(), news_provider)

@router.get("", response_model=List[StockBase])
async def get_stocks(db: Session = Depends(get_db)):
    market_data_provider = get_market_data_provider()
    return await market_data_provider.get_universe()

@router.get("/top", response_model=List[StockScoreResponse])
async def get_top_stocks(limit: int = Query(10, ge=1, le=20)):
    analyzer = get_premarket_analyzer()
    analysis = await analyzer.analyze()
    return analysis.top_ranked_stocks[:limit]

@router.get("/top-categorized", response_model=CategorizedTopStocksResponse)
async def get_top_categorized_stocks():
    analyzer = get_premarket_analyzer()
    return await analyzer.get_categorized_top_stocks()

@router.get("/{symbol}/technicals", response_model=TechnicalIndicatorsResponse)
async def get_stock_technicals(symbol: str):
    market_data_provider = get_market_data_provider()
    candles = await market_data_provider.get_candles(symbol, limit=60)
    df_calc = TechnicalAnalysis.compute_all_indicators(candles)
    latest = df_calc.iloc[-1]
    sup, res = TechnicalAnalysis.find_support_resistance(candles)
    
    return TechnicalIndicatorsResponse(
        symbol=symbol,
        timestamp=latest["timestamp"],
        sma_20=round(float(latest["sma_20"]), 2),
        sma_50=round(float(latest["sma_50"]), 2),
        ema_9=round(float(latest["ema_9"]), 2),
        ema_21=round(float(latest["ema_21"]), 2),
        rsi_14=round(float(latest["rsi_14"]), 2),
        macd=round(float(latest["macd"]), 2),
        macd_signal=round(float(latest["macd_signal"]), 2),
        macd_hist=round(float(latest["macd_hist"]), 2),
        vwap=round(float(latest["vwap"]), 2),
        atr_14=round(float(latest["atr_14"]), 2),
        bb_upper=round(float(latest["bb_upper"]), 2),
        bb_middle=round(float(latest["bb_middle"]), 2),
        bb_lower=round(float(latest["bb_lower"]), 2),
        rvol=round(float(latest["rvol"]), 2),
        support_level=round(sup, 2),
        resistance_level=round(res, 2)
    )
