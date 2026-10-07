# Antigravity Trading System Rules: AI Intraday Trading Agent India

This workspace hosts the autonomous quantitative paper trading platform for Indian Equities (NSE/BSE).

## 🔒 1. Mandatory Safety & Paper Trading Guardrails
- **Paper Trading Inviolability:** `IS_PAPER_TRADING` must remain `True`. Live brokerage API execution endpoints must never be armed without explicit operator manual flags and multi-signature authorization.
- **Risk Floor & Kill-Switch:** Daily loss limit is strictly capped at ₹15,000 (3% of simulated ₹5,00,000 capital). If breached, trading freezes, open positions liquidate, and high-priority alerts are dispatched.
- **Max Capital at Risk:** Never risk more than 2% of capital (₹10,000) on any single trade.

## ⏰ 2. Market Microstructure & Time Windows (Asia/Kolkata - IST)
- **09:00 - 09:15 IST:** Pre-market routine (GIFT Nifty, Global macro signals, regime classification, sentiment scoring).
- **09:15 - 15:15 IST:** Active intraday scanning (VWAP + Dual EMA 9/21 cross + RVOL $\ge 1.15$).
- **15:15 IST:** Mandatory intraday auto-square-off across all open positions.
- **No Overnight Holding:** Intraday positions must never roll over into swing/delivery holdings.

## 📊 3. Indian Statutory Cost Modeling
Every simulated order must account for accurate regulatory charges:
- Brokerage: ₹20 per executed order
- STT: 0.025% on sell turnover
- Exchange turnover fees + GST (18%) + SEBI turnover fee + Stamp duty
- Slippage model: 0.05% baseline

## 🗄️ 4. Data & Database Architecture
- SQLite (`trading_agent.db`) via SQLAlchemy ORM must operate in WAL mode.
- Local API credentials (Angel One SmartAPI, Zerodha, Telegram bot tokens) must stay strictly isolated in `.env`.
