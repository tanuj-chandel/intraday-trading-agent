from fastapi import APIRouter, Query
from typing import List, Optional
from app.news.aggregator import NewsAggregator
from app.schemas.schemas import NewsItem

router = APIRouter()
news_provider = NewsAggregator()

@router.get("", response_model=List[NewsItem])
async def get_news(
    symbol: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50)
):
    if symbol:
        return await news_provider.get_news_for_symbol(symbol, limit=limit)
    return await news_provider.get_latest_news(limit=limit)
