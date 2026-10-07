# Backtesting & Replay Engine

## Data Providers

The system provides two pluggable data ingestion providers:

1. **`MockMarketDataProvider`**:
   - Generates realistic geometric Brownian motion price action with intraday drift, volatility bursts, and volume surges.
   - Models top NSE equities (RELIANCE, HDFCBANK, TCS, INFY, ICICIBANK, TATAMOTORS, SBIN, etc.) and benchmarks (NIFTY 50, BANK NIFTY).

2. **`HistoricalCSVMarketDataProvider`**:
   - Ingests standard 5-minute or 1-minute historical intraday CSV files from `app/data/sample_data/<SYMBOL>.csv`.
   - CSV format: `timestamp,open,high,low,close,volume`.

---

## Running Automated Replay Tests

```bash
cd backend
.\venv\Scripts\pytest tests/test_paper_trading.py -v
```
