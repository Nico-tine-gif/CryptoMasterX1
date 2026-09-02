# CryptoMasterX1 — Consolidated 8-Phase Architecture

## Phase 1 — Machine Core
Runtime, filesystem, configuration and machine health.

## Phase 2 — Account Binding/Security
Account identity, credentials, security restrictions and withdrawal prohibition.

## Phase 3 — Account Verification
Binance connectivity, permissions and usable trading state.

## Phase 4 — Market Discovery/Safety
Tradable universe, liquidity, symbol eligibility and market safety.

## Phase 5 — Market Intelligence
Complete market intelligence:
- H1 regime
- 15M structure
- 5M structure
- momentum
- pullback/reclaim
- RSI
- ATR
- support/resistance
- liquidity
- direction
- confidence
- quality/evidence

Phase 5 does NOT own executable levels.

## Phase 6 — Trade Intelligence + Fresh Construction

Consumes ALL Phase 5 intelligence.

Then:
1. Refreshes Binance market data.
2. Reconciles Phase 5 direction with fresh direction.
3. Rejects stale/conflicting setups.
4. Applies anti-chase and reference-drift protection.
5. Constructs fresh Entry.
6. Constructs SL from fresh ATR.
7. Constructs TP1.
8. Constructs TP2.
9. Calculates actual R:R.
10. Calculates Binance Spot position size.

Phase 6 owns:
- Entry
- SL
- TP1
- TP2
- R:R
- Position size

## Phase 7 — Final Validation + Decision

The ONLY final gate.

Validates:
- symbol
- direction
- confidence
- freshness
- Entry
- SL
- TP1
- TP2
- actual R:R
- position size
- price structure

Output:
- QUALIFIED
- REJECTED

No second decision gate exists.

## Phase 8 — Execution + Lifecycle

Consumes only Phase 7 QUALIFIED trades.

Responsible for:
- execution authorization
- order transmission
- fill tracking
- position lifecycle
- SL/TP lifecycle
- execution failure handling

It must never reinterpret Phase 6/7 trading decisions.

## Legacy files

The old Phase 6, 7, 8, 9, position-sizing and Phase 10 files remain untouched.

They are NOT authoritative for the consolidated path.

## Safety

Current build remains:

LIVE_EXECUTION=False
BOT_ARMED=False
ORDER_SUBMISSION=False
EXECUTION_AUTHORIZED=False
TRANSMISSION_LOCKED=True
WITHDRAWALS=False
DEPOSITS=False
TRANSFERS=False
