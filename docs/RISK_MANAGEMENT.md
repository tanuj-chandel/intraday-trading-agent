# Risk Management Engine Specification

## Independent Veto Authority

The `RiskManager` operates independently from the strategy engine and has unconditional veto authority over all trade signals.

---

## Guardrails & Parameters

| Parameter | Default Value | Description |
|---|---|---|
| **Max Risk Per Trade** | $1.0\%$ of Equity | Enforces fixed fractional risk; sizes quantities accordingly. |
| **Max Daily Drawdown** | $3.0\%$ (₹3,000) | Halts all new trading if realized loss hits ₹3,000 in a day. |
| **Max Open Positions** | 3 Simultaneous | Prevents excessive simultaneous market exposure. |
| **Max Daily Trades** | 10 Trades | Protects against churning and revenge trading. |
| **Min Risk/Reward Ratio** | 1 : 1.5 | Rejects setups offering insufficient reward relative to risk. |
| **Max Single Stock Exposure**| $30\%$ Capital | Prevents capital concentration in a single stock. |
| **Consecutive Loss Circuit** | 3 Losses | Halts new entries after 3 straight losing trades. |
| **Trading Cutoff Time** | 15:15 IST | Blocks new trades after 15:15 IST and triggers auto-squareoff. |
| **Emergency Kill Switch** | Instant | Liquidates all positions and halts execution on command. |

---

## Statutory Brokerage & Tax Accounting

Simulation includes accurate Indian equity charges:
- **Brokerage**: ₹20 flat or 0.03% (whichever is lower) per order leg.
- **STT (Securities Transaction Tax)**: 0.025% on intraday equity sell side.
- **Exchange Turnover Charges**: 0.00345% on turnover.
- **SEBI Charges**: ₹10 per crore turnover.
- **GST**: 18% on (Brokerage + Exchange Charges + SEBI).
- **Stamp Duty**: 0.003% on buy side.
