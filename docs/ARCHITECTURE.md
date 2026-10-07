# System Architecture: AI Intraday Trading Agent India

## Overview

The **AI Intraday Trading Agent India** is a modular, production-grade algorithmic trading and market intelligence platform designed exclusively for the Indian stock market (NSE / BSE).

The system strictly enforces **PAPER TRADING / SIMULATION MODE ONLY**, ensuring no real financial capital is put at risk while providing quantitative analysis, risk-adjusted scoring, automated trade setups, and transparent execution simulation.

---

## High-Level Architecture Diagram

```
+-------------------------------------------------------------------------+
|                       Next.js Financial Terminal UI                     |
|  - Real-time Benchmark Tickers (NIFTY / BANK NIFTY)                     |
|  - Top 10 Ranked Alpha Candidates & Factor Explainability Popovers      |
|  - Live Paper Positions & Trailing Stop Status                          |
|  - Strategy Signal Approval Workflow (Human-in-the-Loop)                 |
|  - News Sentiment Stream & Macro Feed                                   |
|  - Quantitative Performance Analytics & Trade Journal                   |
|  - Emergency STOP TRADING Kill Switch                                   |
+------------------------------------+------------------------------------+
                                     | REST (FastAPI)
                                     v
+-------------------------------------------------------------------------+
|                       FastAPI Backend Core Services                     |
|                                                                         |
|  +---------------------------+       +-------------------------------+  |
|  | Market Data Engine        | ----> | Technical Analysis Engine     |  |
|  | - MarketDataProvider Base |       | - SMA, EMA, RSI, MACD, VWAP   |  |
|  | - MockMarketDataProvider  |       | - ATR, Bollinger, RVOL        |  |
|  | - HistoricalCSVProvider   |       | - Support / Resistance Levels |  |
|  +---------------------------+       +---------------+---------------+  |
|                                                      |                  |
|  +---------------------------+                       v                  |
|  | News Sentiment Engine     | ----> +-------------------------------+  |
|  | - NewsProvider Base       |       | Market Regime Classifier      |  |
|  | - MockNewsProvider        |       | - TRENDING_UP, TRENDING_DOWN  |  |
|  +-------------+-------------+       | - SIDEWAYS, HIGH_VOLATILITY   |  |
|                |                     +---------------+---------------+  |
|                +-----------------+                   |                  |
|                                  v                   v                  |
|                      +----------------------------------+               |
|                      | Multi-Factor Stock Scorer (0-100)|               |
|                      | - Explainable sub-score breakdown|               |
|                      +-----------------+----------------+               |
|                                        |                                |
|                                        v                                |
|                      +----------------------------------+               |
|                      | Pre-Market Analysis Service      |               |
|                      | - Top 10 Setup Generation        |               |
|                      +-----------------+----------------+               |
|                                        |                                |
|                                        v                                |
|                      +----------------------------------+               |
|                      | Strategy Engine (VWAP+EMA+Moment)|               |
|                      | - BUY, SELL, HOLD, NO_TRADE      |               |
|                      +-----------------+----------------+               |
|                                        |                                |
|                                        v                                |
|                      +----------------------------------+               |
|                      | Independent Risk Manager (Veto)  |               |
|                      | - Max Daily Loss (-3%)           |               |
|                      | - Max Risk Per Trade (1%)        |               |
|                      | - Cutoff Time (15:15 IST)        |               |
|                      +-----------------+----------------+               |
|                                        |                                |
|                                        v                                |
|                      +----------------------------------+               |
|                      | Paper Trading Simulation Engine  |               |
|                      | - Simulated Slippage (0.05%)     |               |
|                      | - Indian Statutory Taxes & Broker|               |
|                      | - Trailing SL & Trade Journal    |               |
|                      +-----------------+----------------+               |
+----------------------------------------+--------------------------------+
                                         |
                                         v
+-------------------------------------------------------------------------+
|                  Database Layer (SQLAlchemy ORM)                        |
|  - SQLite (Local development/testing) / PostgreSQL (Docker/Prod)        |
|  - Tables: stocks, market_data, news, regimes, indicators, scores,      |
|    signals, risk_checks, orders, positions, trades, snapshots, logs     |
+-------------------------------------------------------------------------+
```

---

## Core Design Principles

1. **Safety First**: Paper trading is hardcoded as default. Hard risk limits veto trades automatically.
2. **Provider Abstraction**: Market data and news engines use clean abstract interfaces (`MarketDataProvider`, `NewsProvider`) so live Indian brokers (Zerodha Kite Connect, Angel One SmartAPI, Upstox) can be plugged in without refactoring core logic.
3. **Transparent Explainability**: Every score from 0-100 is decomposed into constituent factors (Trend, VWAP, RVOL, Momentum, Sector, News). No black-box decisions.
4. **Realistic Simulation**: Order execution accounts for slippage and calculates exact Indian regulatory charges (STT, Exchange turnover charges, SEBI turnover fees, GST, Stamp duty, Brokerage).
