# Trading Engine Specification

## 1. Technical Analysis Engine

All indicators are calculated mathematically without opaque black-box dependencies:

- **SMA & EMA**: 9, 20, 21, and 50 period trend filters.
- **RSI (14)**: Wilder's smoothing algorithm. Identifies momentum zones (Bullish 52-70, Bearish 30-48).
- **MACD (12, 26, 9)**: Fast line, Signal line, and Histogram expansion.
- **VWAP**: Intraday Volume-Weighted Average Price resetting daily.
- **ATR (14)**: Average True Range for dynamic volatility-based stop loss sizing.
- **Bollinger Bands (20, 2)**: Dynamic range envelope for mean-reversion and expansion detection.
- **RVOL (20)**: Relative Volume ($Volume / Volume MA$). Values $>1.2$ confirm institutional participation.

---

## 2. Market Regime Engine

Classifies the Indian benchmark state into one of 7 measurable regimes:
1. `TRENDING_UP`: Price $> EMA9 > EMA21 > SMA50$, $RSI > 55$, Price $> VWAP$.
2. `TRENDING_DOWN`: Price $< EMA9 < EMA21 < SMA50$, $RSI < 45$, Price $< VWAP$.
3. `SIDEWAYS`: Contracting moving averages, low ADX, price oscillating near VWAP.
4. `HIGH_VOLATILITY`: ATR exceeds $1.8\%$ of index price or Bollinger Bandwidth expands beyond $3.5\%$.
5. `GAP_UP`: Open price exceeds previous close by $\ge +0.7\%$.
6. `GAP_DOWN`: Open price falls below previous close by $\le -0.7\%$.
7. `UNKNOWN`: Insufficient candle data.

---

## 3. Stock Scoring Engine (0-100 Score)

A composite quantitative ranking mechanism combining:
- **Trend Alignment (15 pts)**: Multi-EMA structure.
- **Market Regime Alignment (10 pts)**: Correlation with benchmark trend.
- **Momentum (15 pts)**: RSI and MACD Histogram.
- **Relative Volume (15 pts)**: RVOL expansion.
- **VWAP Proximity (15 pts)**: Proximity to intraday VWAP equilibrium.
- **Breakout Setup (10 pts)**: Range breakout detection.
- **Sector Strength (10 pts)**: Sector relative strength.
- **News Sentiment (10 pts)**: Sentiment polarity and impact.

> **IMPORTANT DISCLAIMER**: The 0–100 score is a relative ranking heuristic, NOT a probability of profit.

---

## 4. VWAP + EMA + Momentum Strategy

- **Long Entry Rules**:
  - Price holds above VWAP.
  - EMA 9 > EMA 21.
  - RSI between 52 and 72.
  - RVOL $\ge 1.1$.
  - Positive MACD histogram.
- **Risk / Reward**: Minimum 1:2 R:R. Stop Loss placed at $1.5 \times ATR$. Target placed at $2 \times Risk$.
