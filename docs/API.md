# API Reference: AI Intraday Trading Agent India

Base URL: `http://localhost:8000/api` or `http://localhost:8000/api/v1`

---

## Endpoints

### Health & System Status
- `GET /health`: Returns service health status and trading mode.
- `GET /system/status`: Returns portfolio equity, daily realized/unrealized P&L, daily loss remaining, and active positions count.
- `GET /system/schedule`: Returns Indian market session timetable (Pre-market, Market Open, Cutoff, Market Close).
- `GET /system/logs`: Returns structured audit logs.

### Market Intelligence & Technicals
- `GET /market/overview`: Returns NIFTY 50 and BANK NIFTY quotes, classified market regime, and breadth.
- `GET /stocks`: Returns tradable stock universe.
- `GET /stocks/top?limit=10`: Returns Top 10 ranked candidate stocks with 0-100 scores and trade setups.
- `GET /stocks/{symbol}/technicals`: Returns computed indicators (SMA, EMA, RSI, MACD, VWAP, ATR, BB, RVOL, S/R).
- `GET /news`: Returns latest financial news items with sentiment ratings.

### Pre-Market Engine
- `POST /premarket/analyze`: Triggers full pre-market analysis pipeline, global cue aggregation, sector ranking, and candidate trade setups.

### Trading Signals & Human Approval
- `GET /signals`: Lists generated signals.
- `POST /signals/generate`: Scans universe using strategy and outputs pending candidate signals.
- `POST /signals/{id}/approve`: Approves a signal, verifies risk limits, and executes it into a live paper position.
- `POST /signals/{id}/reject`: Rejects a pending signal.

### Paper Trading & Positions
- `GET /positions?status=OPEN`: Lists active paper positions with unrealized P&L and trailing stop status.
- `POST /positions/{id}/close`: Manually closes an open paper position and records to trade journal.
- `POST /paper-trading/start`: Activates paper trading engine.
- `POST /paper-trading/stop`: Pauses paper trading engine.

### Risk Controls & Emergency Stop
- `POST /trading/emergency-stop`: Immediately liquidates all open positions, cancels pending signals, and halts execution.

### Performance & Trade Journal
- `GET /trades`: Returns historical trade journal with gross P&L, statutory taxes & brokerage, net P&L, and exit reasons.
- `GET /performance`: Returns quantitative performance metrics (Win Rate, Profit Factor, Max Drawdown, Avg Win/Loss, Sharpe proxy).
