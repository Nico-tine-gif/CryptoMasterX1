#!/usr/bin/env python3

"""
CryptoMasterX1 — Phase 8 Execution + Lifecycle

This phase consumes ONLY Phase 7 QUALIFIED candidates.

It does NOT:
- redo market analysis
- reconstruct Entry/SL/TP
- change R:R
- change position size
- override Phase 7
- enable withdrawals

Execution remains locked until deliberately authorized
outside this preparation pipeline.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"

PHASE7_STATE = STATE / "phase7_final_validation.json"
PHASE8_STATE = STATE / "phase8_execution_lifecycle.json"

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
TRANSMISSION_LOCKED = True

WITHDRAWALS = False
DEPOSITS = False
TRANSFERS = False


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def main():
    if not PHASE7_STATE.exists():
        raise FileNotFoundError(
            f"Phase 7 decision state missing: {PHASE7_STATE}"
        )

    state = json.loads(
        PHASE7_STATE.read_text()
    )

    qualified = state.get(
        "qualified_candidates",
        [],
    )

    # Hard safety boundary.
    execution_enabled = (
        EXECUTION_AUTHORIZED
        and ORDER_SUBMISSION
        and BOT_ARMED
        and LIVE_EXECUTION
        and not TRANSMISSION_LOCKED
    )

    result = {
        "project": "CryptoMasterX1",
        "phase": "PHASE_8",
        "version": "8.0-CONSOLIDATED",
        "timestamp_utc": now(),

        "phase7_qualified_input": len(qualified),

        "execution_enabled": execution_enabled,

        "execution_boundary": {
            "execution_authorized": EXECUTION_AUTHORIZED,
            "order_submission": ORDER_SUBMISSION,
            "bot_armed": BOT_ARMED,
            "live_execution": LIVE_EXECUTION,
            "transmission_locked": TRANSMISSION_LOCKED,
            "withdrawals": False,
            "deposits": False,
            "transfers": False,
        },

        "qualified_candidates": qualified,

        "orders_submitted": 0,
        "status": (
            "READY_BUT_LOCKED"
            if qualified
            else "NO_QUALIFIED_TRADES"
        ),
    }

    save(PHASE8_STATE, result)

    print("=" * 78)
    print("CRYPTOMASTERX1 — PHASE 8 EXECUTION + LIFECYCLE")
    print("=" * 78)
    print(
        f"Phase 7 qualified input : {len(qualified)}"
    )
    print(
        f"Execution enabled       : {execution_enabled}"
    )
    print(
        "Orders submitted        : 0"
    )
    print(
        "Transmission            : LOCKED"
    )
    print(
        "Withdrawals             : FORBIDDEN"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
