# Phase 7 Safety Controls

## Absolute Safety Rules

1. **PAPER_TRADING_ONLY = TRUE** — Cannot be changed via API; hardcoded in `config.py`
2. **No real broker SDK installed** — `kiteconnect`, `upstox-python-sdk`, `smartapi-python` are not in `requirements.txt`
3. **No order placement endpoints** — No `/order/place` or equivalent endpoint exists
4. **Real orders placed = 0** — All responses include `"real_orders_placed": 0`

---

## Kill Switch System (5 Levels)

| Level | Name | Trigger Condition | Effect |
|-------|------|-------------------|--------|
| L1 | PAUSE_SIGNALS | Temporary suspension | Signal generation blocked |
| L2 | NO_NEW_ENTRIES | Orderly winddown | No new positions; exits managed |
| L3 | CLOSE_ALL | Emergency stop | All positions squared off immediately |
| L4 | FREEZE_ALL | Investigation mode | All activity blocked; alerts fired |
| L5 | FULL_HALT | Critical failure | System halted; manual reset required |

**Escalation rule**: Levels only go up. Level 3 cannot be auto-downgraded to Level 1.

**Level 5 Reset**: Requires explicit `POST /api/live/kill-switch/reset?manual_operator_code=CONFIRM_MANUAL_RESET`

---

## Daily Risk Limits

| Control | Value | Where Enforced |
|---------|-------|---------------|
| Max daily loss | ₹3,000 | `LivePositionManager.max_daily_loss` + `RiskManager.max_daily_loss_amount` |
| Max open positions | Configurable (default 5) | `RiskManager.max_open_positions` |
| Max trades per day | Configurable (default 10) | `RiskManager.max_trades_per_day` |
| Min risk-reward ratio | 2.0 | `RiskManager.min_risk_reward_ratio` |
| Max risk per trade | 1% of equity | `RiskManager.max_risk_per_trade_pct` |

---

## Mandatory Square-Off

- **Time**: 15:15 IST
- **Trigger**: Manual `POST /api/live/square-off` OR automatic via `LivePositionManager.square_off_all_positions()`
- **Strategy**: All open positions closed at last known LTP
- **Reason logged**: `"15:15_MANDATORY_SQUARE_OFF"`

---

## RiskManager Gates (9 Checks)

All signals must pass all 9 risk checks before execution:

1. Emergency stop not active
2. Max daily loss not reached
3. Max open positions not exceeded
4. Max trades per day not exceeded
5. Risk-reward ratio ≥ minimum
6. Position size within 1% equity risk
7. Trading cutoff time not reached (15:15 IST)
8. No duplicate position in same symbol
9. Capital adequacy (not negative equity)

---

## Human Approval Architecture

```
Signal Generated → Status: PENDING
       ↓
Human reviews signal at /api/live/signals
       ↓
   ┌──────────────┐
   │ APPROVE      │ → POST /api/live/signal/{id}/approve
   │ REJECT       │ → POST /api/live/signal/{id}/reject
   └──────────────┘
       ↓ (Approved only)
RiskManager.validate_trade() [9 checks]
       ↓ (All passed)
LivePaperExecutionEngine.execute_paper_order()
       ↓
Paper position opened in memory + DB
```

No signal can auto-execute without human approval.

---

## Data Safety

- **Mock data guard**: `LiveDataQualityGate` blocks signals if `is_mock_provider=True`
- **Staleness guard**: Blocks signals if data age > 30 seconds
- **No look-ahead**: Candle builder only evaluates after candle closes
- **Audit trail**: All events written to `system_logs` table and in-memory log
- **DB persistence**: Signals and positions survive backend restart via `live_signals` and `live_positions` tables

---

## Reporting & Disclaimer

All Phase 7 reports include:
```
PAPER TRADING SIMULATION ONLY.
Real-money orders: 0 (STRICTLY DISABLED).
Past paper trading results do not guarantee future real-money performance.
```
