import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Intraday Trading Agent India"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    TIMEZONE: str = "Asia/Kolkata"
    
    # SAFETY ENFORCEMENT: Initial mode MUST be PAPER TRADING
    TRADING_MODE: str = "PAPER"  # "PAPER" or "SIMULATION"
    IS_PAPER_TRADING: bool = True
    LIVE_TRADING_ENABLED: bool = False  # Global Rule: Must stay False by default, require explicit configuration
    EMERGENCY_STOP_TRIGGERED: bool = False
    
    # Auto-Execution Mode (Entries require manual/telegram approval when False)
    AUTO_APPROVE: bool = False  # Default False: nothing enters without approval
    AUTO_APPROVE_SIGNALS: bool = False  # Backward-compatible alias
    AUTO_APPROVE_EXPIRY_DATE: Optional[str] = None
    APPROVAL_TIMEOUT_SECONDS: int = 120  # Signal expires after 120 seconds
    MAX_ENTRY_DRIFT_PCT: float = 0.003  # 0.3% max entry drift allowed on approval
    STALE_FEED_SECONDS: int = 15  # Health watchdog stale threshold (default 15s)
    
    # Adaptive Market Learning Engine (Phase 5: Safe Learner)
    ADAPTIVE_LEARNING_ENABLED: bool = True
    ADAPTIVE_MIN_WIN_RATE: float = 0.50
    ADAPTIVE_LOOKBACK_TRADES: int = 200
    MIN_TRADES_FOR_LEARNING: int = 100  # Minimum sample: no parameter change without at least 100 completed trades
    LEARNER_RECOMMEND_ONLY: bool = True  # Recommend-only mode: write proposals to DB, do not auto-apply
    DEFAULT_ATR_SL_MULTIPLIER: float = 1.5
    MIN_ATR_SL_MULTIPLIER: float = 1.3
    MAX_ATR_SL_MULTIPLIER: float = 2.0
    MAX_ATR_PARAM_STEP: float = 0.1  # Each change is at most 0.1
    TARGET_RISK_REWARD_RATIO: float = 2.0

    # Phase 6: Go-Live Criteria Thresholds
    GO_LIVE_MIN_TRADES: int = 150
    GO_LIVE_MAX_DRAWDOWN_PCT: float = 5.0
    GO_LIVE_INCIDENT_WINDOW_DAYS: int = 10
    
    # Market Data Provider: "zerodha", "upstox", "angelone", "historical", "mock"
    MARKET_DATA_PROVIDER: str = "angelone"
    
    # Zerodha Kite Connect Credentials
    ZERODHA_API_KEY: Optional[str] = None
    ZERODHA_API_SECRET: Optional[str] = None
    ZERODHA_ACCESS_TOKEN: Optional[str] = None
    
    # Upstox API Credentials
    UPSTOX_API_KEY: Optional[str] = None
    UPSTOX_API_SECRET: Optional[str] = None
    UPSTOX_ACCESS_TOKEN: Optional[str] = None
    
    # Angel One SmartAPI Credentials
    ANGELONE_API_KEY: Optional[str] = None
    ANGELONE_CLIENT_CODE: Optional[str] = None
    ANGELONE_PIN: Optional[str] = None
    ANGELONE_TOTP_SECRET: Optional[str] = None
    ANGELONE_JWT_TOKEN: Optional[str] = None
    
    # News & External Data APIs (Optional)
    NEWS_API_KEY: Optional[str] = None
    GLOBAL_DATA_API_KEY: Optional[str] = None
    
    # Telegram Mobile Notifications & Two-Way Approval
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_ALLOWED_CHAT_ID: Optional[str] = None  # Security: Only this chat ID can approve/command
    TELEGRAM_ENABLED: bool = True
    
    # Generic Broker Fallback Settings
    BROKER_NAME: Optional[str] = "MOCK"
    BROKER_API_KEY: Optional[str] = None
    BROKER_API_SECRET: Optional[str] = None
    BROKER_ACCESS_TOKEN: Optional[str] = None
    
    # Data Quality & Freshness
    DATA_FRESHNESS_MAX_SECONDS: int = 300  # 5 minutes threshold for stale warning
    CACHE_TTL_SECONDS: int = 3  # In-memory quote cache TTL
    
    # Liquidity Filter Thresholds (NSE Intraday Equities)
    MIN_AVG_DAILY_VOLUME: int = 100000  # Min 1 Lakh shares/day
    MIN_DAILY_TURNOVER_INR: float = 50000000.0  # Min ₹5 Crore daily turnover
    MIN_STOCK_PRICE: float = 50.0  # Avoid penny stocks
    MAX_STOCK_PRICE: float = 15000.0  # High priced filter
    MAX_BID_ASK_SPREAD_PCT: float = 0.0015  # 0.15% max spread
    
    # Database
    DATABASE_URL: str = "sqlite:///./trading_agent.db"
    
    # Risk Parameters (Strict Defaults for Capital Protection)
    INITIAL_CAPITAL: float = 500000.0  # ₹5,00,000 INR
    MAX_RISK_PER_TRADE_PCT: float = 0.005  # 0.5% (was 2.0%)
    MAX_DAILY_LOSS_PCT: float = 0.02  # 2.0% of capital (was 3.0%)
    MAX_DAILY_LOSS_AMOUNT: float = 10000.0  # ₹10,000 (2.0% of ₹5,00,000)
    MAX_OPEN_POSITIONS: int = 5
    MAX_POSITION_NOTIONAL_PCT: float = 0.20  # Max 20% of capital per position
    MAX_TOTAL_EXPOSURE_PCT: float = 1.00  # Max 100% of capital across open positions
    MIS_LEVERAGE: float = 5.0  # 5x Intraday MIS leverage
    
    # Trade Quotas, Thresholds & Cooldowns
    MAX_TRADES_PER_DAY: int = 10  # Ceiling, not a target
    MIN_SIGNAL_SCORE: float = 70.0  # Minimum signal score; no trade below it
    MAX_TRADES_PER_SYMBOL_PER_DAY: int = 2  # Max trades per symbol per day
    COOLDOWN_AFTER_SL_MINUTES: int = 45  # Cooldown after SL hit per symbol
    MAX_POSITIONS_PER_SECTOR: int = 2  # Max concurrent positions per sector
    
    MIN_RISK_REWARD_RATIO: float = 2.0
    MAX_CONSECUTIVE_LOSSES: int = 3
    TRADING_CUTOFF_TIME: str = "15:15"  # IST Auto square-off
    MARKET_OPEN_TIME: str = "09:15"
    MARKET_CLOSE_TIME: str = "15:30"
    
    # Broker & Statutory Charges (NSE Intraday Equities Estimates)
    BROKERAGE_PER_ORDER: float = 20.0  # ₹20 flat or 0.03%
    BROKERAGE_PCT: float = 0.0003
    STT_PCT_SELL: float = 0.00025  # 0.025% on sell for intraday equity
    EXCHANGE_TURNOVER_PCT: float = 0.0000345  # 0.00345%
    SEBI_CHARGES_PCT: float = 0.000001  # ₹10 per crore
    GST_PCT_ON_CHARGES: float = 0.18  # 18% on (Brokerage + Exchange)
    STAMP_DUTY_PCT_BUY: float = 0.00003  # 0.003% on buy
    
    # Phase 4: Trade Quality Filters (Individually Toggleable)
    # 1. Time Filters
    TIME_FILTER_ENABLED: bool = True
    NO_ENTRY_BEFORE_TIME: str = "09:25"  # No new entries in first 10 minutes (09:15-09:25)
    NO_ENTRY_AFTER_TIME: str = "14:30"   # No new entries after 14:30 IST
    LUNCH_CHOP_FILTER_ENABLED: bool = True
    LUNCH_CHOP_START_TIME: str = "12:00"
    LUNCH_CHOP_END_TIME: str = "13:30"
    LUNCH_CHOP_MIN_SCORE: float = 85.0   # Higher score threshold during lunch chop

    # 2. Market Regime Filters
    REGIME_FILTER_ENABLED: bool = True
    INDIA_VIX_HIGH_VOL_THRESHOLD: float = 22.0
    INDIA_VIX_EXTREME_THRESHOLD: float = 26.0
    BLOCK_ENTRIES_IN_CHOPPY: bool = False
    BLOCK_ENTRIES_IN_HIGH_VOL: bool = False
    REGIME_CHOPPY_MIN_SCORE: float = 85.0
    REGIME_HIGH_VOL_MIN_SCORE: float = 85.0

    # 3. Tradability Checks
    TRADABILITY_CHECKS_ENABLED: bool = True
    CIRCUIT_LIMIT_BUFFER_PCT: float = 0.01  # Skip stocks within 1% of circuit limit
    SKIP_CIRCUIT_STOCKS: bool = True
    SKIP_HALTED_STOCKS: bool = True
    SKIP_ASM_GSM_STOCKS: bool = True
    SKIP_CORPORATE_ACTION_TODAY: bool = True
    ASM_GSM_SYMBOLS: List[str] = ["IDEA", "YESBANK", "SUZLON", "RCOM", "DHFL"]

    # 4. Event-Day Mode
    EVENT_DAY_FILTER_ENABLED: bool = True
    EVENT_DAYS: List[str] = ["2026-02-01", "2026-04-09", "2026-06-05", "2026-08-07", "2026-10-08", "2026-12-04"]
    EVENT_DAY_ACTION: str = "REDUCE_RISK"  # "PAUSE_TRADING" or "REDUCE_RISK"
    EVENT_DAY_RISK_MULTIPLIER: float = 0.5  # Halves risk on event days

    # 5. Slippage Realism
    DYNAMIC_SLIPPAGE_ENABLED: bool = True

    # 6. News Sentiment Pipeline
    NEWS_FILTER_ENABLED: bool = True
    NEWS_MAX_AGE_MINUTES: int = 120  # Ignore news older than 120 minutes
    NEWS_MAX_ALPHA_WEIGHT: float = 10.0  # Cap maximum news weight in alpha score (10 points out of 100)

    # Slippage simulation in %
    SLIPPAGE_PCT: float = 0.0005  # 0.05%
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
