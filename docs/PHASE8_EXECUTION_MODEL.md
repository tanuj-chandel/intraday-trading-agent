# Phase 8 — Execution Model Documentation
## Paper Trade Execution: Simulation, Costs, and P&L

> ⚠️ **PAPER TRADING ONLY. All executions are simulations. No real money involved.**

---

## Execution Flow

```
Signal APPROVED (human clicks button)
    ↓
LivePaperExecutionEngine.execute(signal, market_tick)
    ↓
[1] Slippage Calculation
    ↓
[2] Fill Price Determination
    ↓
[3] Indian Statutory Charges
    ↓
[4] LivePaperPosition created
    ↓
[5] Phase8TradeJournalEntry created
    ↓
[6] LivePositionManager adds position
    ↓
Real-time MTM begins → MFE/MAE tracked
```

---

## Slippage Model

Three configurable slippage modes:

### IMMEDIATE_FILL (default)
```python
buy_fill  = ask_price          # Worst-case buy at ask
sell_fill = bid_price          # Worst-case sell at bid
slippage  = ask - mid          # Half-spread cost
```

### TWAP_APPROX
```python
fill_price = (bid + ask) / 2   # Mid-point approximation
slippage   = fill_price - signal_price
```

### VWAP_APPROX
```python
fill_price ≈ VWAP from last closed 5m candle
```

**Default**: `IMMEDIATE_FILL` — most conservative (realistic for retail intraday).

---

## Indian Statutory Charges (Simulated)

All charges are computed accurately for NSE intraday equity:

| Charge | Rate | Notes |
|--------|------|-------|
| Brokerage | ₹20 flat | Per executed trade (each leg) |
| STT (Securities Transaction Tax) | 0.025% of turnover | Buy + Sell sides |
| Exchange Transaction Charges | 0.00345% | NSE rate |
| SEBI Turnover Fee | ₹10 per crore | Regulatory fee |
| GST | 18% | On brokerage + exchange charges |
| Stamp Duty | 0.003% of buy-side value | State government |

### Example Calculation

Trade: Buy 10 shares of RELIANCE at ₹2,982 → Sell at ₹3,010

```
Trade Value (buy):  ₹29,820
Trade Value (sell): ₹30,100
Total Turnover:     ₹59,920

Brokerage:    ₹20 × 2 = ₹40.00
STT:          0.025% × ₹59,920 = ₹14.98
Exchange:     0.00345% × ₹59,920 = ₹2.07
SEBI:         ₹10 / crore × ₹59,920 ≈ ₹0.01
GST:          18% × (₹40 + ₹2.07) = ₹7.57
Stamp Duty:   0.003% × ₹29,820 = ₹0.89

Total Charges: ₹65.52
Gross P&L:    ₹280.00
Net P&L:      ₹214.48
```

---

## MFE / MAE Tracking (Phase 8)

### Maximum Favorable Excursion (MFE)
The highest unrealized profit reached during the trade's lifetime.

```python
# For a BUY position:
mfe_inr = (peak_price - entry_fill_price) * quantity

# For a SELL position:
mfe_inr = (entry_fill_price - trough_price) * quantity
```

### Maximum Adverse Excursion (MAE)
The highest unrealized loss reached during the trade's lifetime.

```python
# For a BUY position:
mae_inr = (entry_fill_price - trough_price) * quantity
```

**Interpretation**:
- High MFE / High MAE → Trade came close to both targets and stops → "Noisy" signal
- High MFE / Low MAE → Clean directional move → Strategy working well
- Low MFE / High MAE → Trade moved against entry immediately → Likely bad signal

---

## Position MTM (Mark-to-Market)

On every valid tick received:

```python
LivePositionManager.update_market_price(symbol, ltp)
```

Updates:
- `current_price` → latest LTP
- `unrealized_pnl` → (current - entry) × qty × direction
- `unrealized_pnl_pct` → as % of entry value
- `mfe_inr` → track running maximum favorable
- `mae_inr` → track running maximum adverse
- Check SL: if price ≤ stop_loss (BUY) → exit STOP_LOSS
- Check TP: if price ≥ target_price (BUY) → exit TARGET_HIT
- Check trailing stop if configured

---

## Position Exit Reasons

| Reason | Trigger |
|--------|---------|
| `TARGET_HIT` | Price reached take-profit level |
| `STOP_LOSS_HIT` | Price hit stop-loss level |
| `TRAILING_STOP` | Price reversed past trailing stop |
| `15:15_MANDATORY_SQUARE_OFF` | Auto-close at 15:15 IST |
| `MANUAL_SQUARE_OFF` | Manual via API |
| `KILL_SWITCH_L3` | Kill switch Level 3 triggered |

---

## P&L Attribution

```
Gross P&L = (exit_price - entry_fill_price) × quantity × direction
Net P&L   = Gross P&L − Total Charges
```

All P&L figures are in ₹ (Indian Rupee).

---

## Paper Trading vs Real Trading Differences

| Aspect | Paper Trading | Real Trading |
|--------|--------------|--------------|
| Order fill | Always filled instantly | May partially fill or fail |
| Slippage | Estimated (bid/ask spread) | Actual market impact |
| Execution latency | 0ms (instant simulation) | 50–500ms real latency |
| Market impact | None (ignored) | Price moves against large orders |
| Liquidity | Always assumed sufficient | Real limit: volume × circuit limits |
| Margin calls | Not modelled | Real risk of forced liquidation |
| Circuit filters | Not modelled | NSE may halt trading |

**This execution model is realistic for small retail intraday positions (< ₹2 lakh per trade).**
For larger positions, real market impact would be significantly larger than simulated slippage.
