import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.data.factory import get_market_data_provider
from app.data.global_market import GlobalMarketAnalyzer
from app.data.gift_nifty_provider import GiftNiftyProvider
from app.data.data_quality import DataQualityService
from app.market.regime import MarketRegimeEngine
from app.schemas.schemas import (
    MarketOverviewResponse,
    MarketIndexOverview,
    GlobalMarketResponse,
    GiftNiftyResponse,
    DataQualityResponse,
    ManualGiftNiftyRequest
)

router = APIRouter()

@router.get("/overview", response_model=MarketOverviewResponse)
async def get_market_overview(db: Session = Depends(get_db)):
    market_data_provider = get_market_data_provider()
    nifty_quote = await market_data_provider.get_quote("NIFTY 50")
    bank_nifty_quote = await market_data_provider.get_quote("BANK NIFTY")
    
    nifty_candles = await market_data_provider.get_candles("NIFTY 50", limit=60)
    regime_res = MarketRegimeEngine.classify_regime(nifty_candles)
    
    def _extract_index(quote, sym, regime="NORMAL", adx=20.0, vol="NORMAL"):
        cp = float(quote.get("current_price", quote.get("ltp", 0.0)) or 0.0)
        pc = float(quote.get("prev_close", cp) or cp)
        chg = float(quote.get("change", cp - pc) or 0.0)
        chg_pct = float(quote.get("change_pct", (chg / pc * 100 if pc else 0.0)) or 0.0)
        return MarketIndexOverview(
            symbol=sym,
            current_price=cp,
            change=round(chg, 2),
            change_pct=round(chg_pct, 2),
            open=float(quote.get("open", cp) or cp),
            high=float(quote.get("high", cp) or cp),
            low=float(quote.get("low", cp) or cp),
            prev_close=pc,
            regime=regime,
            adx=adx,
            volatility=vol
        )

    indices = [
        _extract_index(
            nifty_quote, "NIFTY 50",
            regime=regime_res["regime"],
            adx=regime_res["adx_value"],
            vol=regime_res["regime"] if "VOLATILITY" in regime_res["regime"] else "NORMAL"
        ),
        _extract_index(
            bank_nifty_quote, "BANK NIFTY",
            regime=regime_res["regime"],
            adx=regime_res["adx_value"],
            vol="NORMAL"
        )
    ]
    
    return MarketOverviewResponse(
        indices=indices,
        market_regime=regime_res["regime"],
        regime_description=regime_res["description"],
        advance_decline_ratio=1.65,
        market_status="OPEN",
        timestamp=datetime.datetime.now()
    )

@router.get("/global", response_model=GlobalMarketResponse)
def get_global_market_analysis():
    return GlobalMarketAnalyzer.get_global_market_summary()

@router.get("/gift-nifty", response_model=GiftNiftyResponse)
async def get_gift_nifty_gap():
    market_data_provider = get_market_data_provider()
    nifty = await market_data_provider.get_quote("NIFTY 50")
    return GiftNiftyProvider.get_gap_analysis(spot_nifty_close=nifty["current_price"])

@router.post("/gift-nifty/manual")
def set_manual_gift_nifty(req: ManualGiftNiftyRequest):
    GiftNiftyProvider.set_manual_price(req.price)
    return {"message": "Manual GIFT Nifty level registered", "price": req.price}

@router.get("/data-sources", response_model=DataQualityResponse)
def get_data_quality_report():
    return DataQualityService.get_quality_report()
