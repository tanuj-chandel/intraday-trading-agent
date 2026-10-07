from typing import List
from app.schemas.schemas import StockBase

class IndianStockMetadata(StockBase):
    nse_symbol: str
    index_name: str
    exchange: str = "NSE"
    liquidity_classification: str = "VERY_HIGH"  # "VERY_HIGH", "HIGH", "MEDIUM", "LOW"
    avg_daily_volume: float = 1000000.0
    avg_daily_turnover_cr: float = 150.0  # in ₹ Crores
    lot_size: int = 1
    tick_size: float = 0.05
    is_active: bool = True

EXPANDED_INDIAN_UNIVERSE: List[IndianStockMetadata] = [
    # --- NIFTY 50 CORE BLUE CHIPS ---
    IndianStockMetadata(
        symbol="RELIANCE", nse_symbol="RELIANCE", company_name="Reliance Industries Ltd.",
        sector="Energy", industry="Oil & Gas", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=6500000.0, avg_daily_turnover_cr=1950.0
    ),
    IndianStockMetadata(
        symbol="HDFCBANK", nse_symbol="HDFCBANK", company_name="HDFC Bank Ltd.",
        sector="Financial Services", industry="Private Banking", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=18000000.0, avg_daily_turnover_cr=2900.0
    ),
    IndianStockMetadata(
        symbol="ICICIBANK", nse_symbol="ICICIBANK", company_name="ICICI Bank Ltd.",
        sector="Financial Services", industry="Private Banking", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=12000000.0, avg_daily_turnover_cr=1400.0
    ),
    IndianStockMetadata(
        symbol="INFY", nse_symbol="INFY", company_name="Infosys Ltd.",
        sector="IT", industry="IT Services", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=7000000.0, avg_daily_turnover_cr=1250.0
    ),
    IndianStockMetadata(
        symbol="TCS", nse_symbol="TCS", company_name="Tata Consultancy Services Ltd.",
        sector="IT", industry="IT Services", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=2500000.0, avg_daily_turnover_cr=1050.0
    ),
    IndianStockMetadata(
        symbol="TATAMOTORS", nse_symbol="TATAMOTORS", company_name="Tata Motors Ltd.",
        sector="Auto", industry="Automobiles", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=14000000.0, avg_daily_turnover_cr=1450.0
    ),
    IndianStockMetadata(
        symbol="SBIN", nse_symbol="SBIN", company_name="State Bank of India",
        sector="Financial Services", industry="PSU Banking", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=16000000.0, avg_daily_turnover_cr=1300.0
    ),
    IndianStockMetadata(
        symbol="BHARTIARTL", nse_symbol="BHARTIARTL", company_name="Bharti Airtel Ltd.",
        sector="Telecom", industry="Telecom Services", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=5500000.0, avg_daily_turnover_cr=800.0
    ),
    IndianStockMetadata(
        symbol="ITC", nse_symbol="ITC", company_name="ITC Ltd.",
        sector="FMCG", industry="Diversified FMCG", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=11000000.0, avg_daily_turnover_cr=550.0
    ),
    IndianStockMetadata(
        symbol="LT", nse_symbol="LT", company_name="Larsen & Toubro Ltd.",
        sector="Capital Goods", industry="Engineering & Construction", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=2800000.0, avg_daily_turnover_cr=1020.0
    ),
    IndianStockMetadata(
        symbol="KOTAKBANK", nse_symbol="KOTAKBANK", company_name="Kotak Mahindra Bank Ltd.",
        sector="Financial Services", industry="Private Banking", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=3800000.0, avg_daily_turnover_cr=680.0
    ),
    IndianStockMetadata(
        symbol="AXISBANK", nse_symbol="AXISBANK", company_name="Axis Bank Ltd.",
        sector="Financial Services", industry="Private Banking", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=6500000.0, avg_daily_turnover_cr=780.0
    ),
    IndianStockMetadata(
        symbol="SUNPHARMA", nse_symbol="SUNPHARMA", company_name="Sun Pharmaceutical Industries",
        sector="Healthcare", industry="Pharmaceuticals", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=2200000.0, avg_daily_turnover_cr=380.0
    ),
    IndianStockMetadata(
        symbol="BAJFINANCE", nse_symbol="BAJFINANCE", company_name="Bajaj Finance Ltd.",
        sector="Financial Services", industry="NBFC", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=1200000.0, avg_daily_turnover_cr=850.0
    ),
    IndianStockMetadata(
        symbol="TITAN", nse_symbol="TITAN", company_name="Titan Company Ltd.",
        sector="Consumer Durables", industry="Gems & Jewellery", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=1100000.0, avg_daily_turnover_cr=390.0
    ),
    IndianStockMetadata(
        symbol="MARUTI", nse_symbol="MARUTI", company_name="Maruti Suzuki India Ltd.",
        sector="Auto", industry="Passenger Vehicles", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=450000.0, avg_daily_turnover_cr=540.0
    ),
    IndianStockMetadata(
        symbol="M&M", nse_symbol="M&M", company_name="Mahindra & Mahindra Ltd.",
        sector="Auto", industry="Automobiles", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=3200000.0, avg_daily_turnover_cr=890.0
    ),
    IndianStockMetadata(
        symbol="NTPC", nse_symbol="NTPC", company_name="NTPC Ltd.",
        sector="Power", industry="Power Generation", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=14000000.0, avg_daily_turnover_cr=560.0
    ),
    IndianStockMetadata(
        symbol="HINDUNILVR", nse_symbol="HINDUNILVR", company_name="Hindustan Unilever Ltd.",
        sector="FMCG", industry="FMCG Household", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=1600000.0, avg_daily_turnover_cr=440.0
    ),
    IndianStockMetadata(
        symbol="POWERGRID", nse_symbol="POWERGRID", company_name="Power Grid Corporation of India",
        sector="Power", industry="Power Transmission", index_name="NIFTY 50",
        liquidity_classification="HIGH", avg_daily_volume=9500000.0, avg_daily_turnover_cr=320.0
    ),

    # --- NIFTY NEXT 50 & LIQUID NIFTY 100 CONSTITUENTS ---
    IndianStockMetadata(
        symbol="ZOMATO", nse_symbol="ZOMATO", company_name="Zomato Ltd.",
        sector="Consumer Services", industry="E-Commerce Delivery", index_name="NIFTY NEXT 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=35000000.0, avg_daily_turnover_cr=920.0
    ),
    IndianStockMetadata(
        symbol="JIOFIN", nse_symbol="JIOFIN", company_name="Jio Financial Services Ltd.",
        sector="Financial Services", industry="NBFC & Fintech", index_name="NIFTY NEXT 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=22000000.0, avg_daily_turnover_cr=750.0
    ),
    IndianStockMetadata(
        symbol="TRENT", nse_symbol="TRENT", company_name="Trent Ltd.",
        sector="Consumer Services", industry="Retail", index_name="NIFTY NEXT 50",
        liquidity_classification="HIGH", avg_daily_volume=1800000.0, avg_daily_turnover_cr=1200.0
    ),
    IndianStockMetadata(
        symbol="BEL", nse_symbol="BEL", company_name="Bharat Electronics Ltd.",
        sector="Capital Goods", industry="Defense & Aerospace", index_name="NIFTY NEXT 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=19000000.0, avg_daily_turnover_cr=580.0
    ),
    IndianStockMetadata(
        symbol="HAL", nse_symbol="HAL", company_name="Hindustan Aeronautics Ltd.",
        sector="Capital Goods", industry="Defense & Aerospace", index_name="NIFTY NEXT 50",
        liquidity_classification="HIGH", avg_daily_volume=2400000.0, avg_daily_turnover_cr=1100.0
    ),
    IndianStockMetadata(
        symbol="VEDL", nse_symbol="VEDL", company_name="Vedanta Ltd.",
        sector="Metals & Mining", industry="Diversified Metals", index_name="NIFTY 100",
        liquidity_classification="VERY_HIGH", avg_daily_volume=25000000.0, avg_daily_turnover_cr=1150.0
    ),
    IndianStockMetadata(
        symbol="DLF", nse_symbol="DLF", company_name="DLF Ltd.",
        sector="Realty", industry="Real Estate Development", index_name="NIFTY 100",
        liquidity_classification="HIGH", avg_daily_volume=4800000.0, avg_daily_turnover_cr=410.0
    ),
    IndianStockMetadata(
        symbol="TATASTEEL", nse_symbol="TATASTEEL", company_name="Tata Steel Ltd.",
        sector="Metals & Mining", industry="Iron & Steel", index_name="NIFTY 50",
        liquidity_classification="VERY_HIGH", avg_daily_volume=38000000.0, avg_daily_turnover_cr=580.0
    )
]
