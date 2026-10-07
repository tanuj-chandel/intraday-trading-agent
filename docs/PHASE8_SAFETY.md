# Phase 8 — Safety Documentation
## Paper Trading Safety System Overview

> ⛔ **ABSOLUTE RULE: PAPER TRADING ONLY. ZERO REAL MONEY ORDERS. PERMANENTLY DISABLED.**

---

## Layer 1 — Configuration Safety

```python
# backend/app/core/config.py
IS_PAPER_TRADING: bool = True          # Cannot be changed at runtime
TRADING_MODE: str = "PAPER"           # Cannot be set to "LIVE" 
AUTO_PAPER_EXECUTION: bool = False     # Signals always require human approval
```

These are hardcoded defaults. There is **no environment variable, API endpoint, or code path** that can enable real-money trading — because no order placement code exists in the system.

---

## Layer 2 — Zero Order Placement Code

Security scan result (run via `test_phase8_security_audit.py`):

| Pattern | Count in codebase |
|---------|------------------|
| `place_order(` | **0** |
| `create_order(` | **0** |
| `submit_order(` | **0** |
| `execute_order(` | **0** |
| `send_order(` | **0** |

All broker adapters are **read-only** — they only call market data endpoints (`GET /quote`). No write endpoints.

---

## Layer 3 — 7-State Data Provenance Gate

Only **LIVE** state permits signal generation. All other 6 states block signals:

```
UNCONFIGURED → No credentials → BLOCKED
MOCK         → Mock provider  → BLOCKED
DISCONNECTED → Feed down      → BLOCKED  
STALE        → Age > 30s      → BLOCKED
INVALID      → Price ≤ 0      → BLOCKED
ERROR        → HTTP failure   → BLOCKED
LIVE         → All checks OK  → SIGNALS PERMITTED
```

The gate is evaluated on **every single tick** before any signal evaluation.

---

## Layer 4 — Human Approval Workflow

```
AI Signal → Risk Manager → PENDING (human must approve)
                            ↓
Human clicks APPROVE → paper execution only
Human clicks REJECT  → signal discarded
Signal expires       → auto-discarded after timeout
```

`AUTO_PAPER_EXECUTION = False` is enforced. No signal can execute without explicit human button click.

---

## Layer 5 — RiskManager (9 Independent Checks)

Every approval request goes through `RiskManager.validate_trade()`:

1. `IS_PAPER_TRADING == True` enforced
2. Max daily loss limit (default ₹3,000)
3. Max open positions (default 3)
4. Minimum risk-reward ratio (≥ 2.0)
5. 15:15 IST cutoff time
6. Max trades per day
7. Max consecutive losses (default 5)
8. Minimum position size validity
9. Signal freshness (age ≤ 30s)

**No bypass path exists.** All 9 checks must pass.

---

## Layer 6 — Tick Validator (Phase 8)

Every incoming tick is validated before touching any downstream system:

| Validation | Fail behaviour |
|-----------|---------------|
| Zero/negative price | REJECT, audit log, alert if rate > 5% |
| Impossible OHLC (High < Low) | REJECT |
| Future timestamp (> 5s) | REJECT |
| Duplicate tick (same ts) | REJECT |
| Negative volume | REJECT |
| Price spike > 20% | WARN (not reject) |
| Volume spike > 100x | WARN (not reject) |

---

## Layer 7 — 5-Level Hierarchical Kill Switch

| Level | Name | Effect | Reset |
|-------|------|--------|-------|
| L1 | PAUSE_SIGNALS | No new signals generated | Any operator |
| L2 | NO_NEW_ENTRIES | No new position entries | Any operator |
| L3 | CLOSE_ALL_POSITIONS | Close all open positions NOW | Any operator |
| L4 | FREEZE_ALL | All operations frozen | Any operator |
| L5 | FULL_HALT | System fully halted | Requires `CONFIRM_MANUAL_RESET` code |

**Kill switch is escalation-only** — cannot reduce level via activate(). Level 5 requires a manual override code.

---

## Layer 8 — 15:15 IST Mandatory Square-Off

The `LivePositionManager` auto-closes **all open positions at 15:15 IST** without exception. This prevents overnight risk and ensures clean session accounting.

---

## Layer 9 — Audit Trail

Every event is dual-written to:
- In-memory ring buffer (last 500 events) — real-time dashboard
- `system_logs` DB table — permanent audit trail

Events include: tick received/rejected, signal created/approved/rejected, position opened/closed/exited, kill switch activations, provenance state changes.

---

## Layer 10 — Report Disclaimers

Every Phase 8 report, endpoint response, and dashboard element contains:

```
PAPER TRADING SIMULATION ONLY.
Real money orders: 0 (STRICTLY DISABLED).
Results represent hypothetical paper performance only.
Past paper-trading results do not predict future real-market performance.
```

---

## What Cannot Happen

1. ❌ Real money order sent to any broker
2. ❌ Mock data labelled as LIVE data
3. ❌ Signal generated when DataProvenanceState ≠ LIVE
4. ❌ Signal auto-executed without human approval
5. ❌ Position opened after 15:15 IST
6. ❌ Kill switch reduced in level (can only escalate)
7. ❌ L5 kill switch reset without correct code
8. ❌ Strategy parameters changed (VWAP_EMA_MOMENTUM_V1 is frozen)
9. ❌ Zero/negative price tick entering the signal pipeline
10. ❌ DB failure blocking or corrupting live trading
