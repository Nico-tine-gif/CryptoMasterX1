#!/usr/bin/env python3
"""
CryptoMasterX1 — PHASE 9
Execution + Lifecycle

OWNER:
    Phase 9 owns execution and position lifecycle only.

INPUT:
    state/phase8_final_validation.json

SAFETY:
    Execution remains LOCKED.
    Order submission remains DISABLED.
    Bot remains UNARMED.
    Live execution remains FALSE.
    Withdrawals remain FORBIDDEN.

Phase 9 MUST NOT reconstruct or modify:
    Entry
    SL
    TP1
    TP2
    R:R
    Confidence
    Direction

Those values are owned by Phase 7 and validated by Phase 8.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT_STATE = ROOT / "state" / "phase8_final_validation.json"
OUTPUT_STATE = ROOT / "state" / "phase9_execution_lifecycle.json"


# ============================================================
# HARD EXECUTION SAFETY BOUNDARY
# ============================================================

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
WITHDRAWALS = False

EXECUTION_BOUNDARY = "LOCKED"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_phase8() -> dict:
    if not INPUT_STATE.exists():
        raise FileNotFoundError(
            f"Missing Phase 8 state: {INPUT_STATE}"
        )

    with INPUT_STATE.open("r", encoding="utf-8") as f:
        state = json.load(f)

    return state


def get_validated_candidates(state: dict) -> list:
    """
    Phase 8 is the sole upstream authority for final trade candidates.
    Support the expected schema without inventing candidates.
    """

    validation = state.get("validation", {})

    # Phase 8 authoritative schema:
    # validation.validated_candidates contains the
    # immutable trades constructed by Phase 7 and
    # successfully validated by Phase 8.
    candidates = validation.get("validated_candidates", [])

    if not isinstance(candidates, list):
        candidates = []

    return candidates


def verify_trade_immutability(item: dict) -> tuple[bool, str]:
    """
    Phase 9 accepts the constructed trade as immutable.
    """

    required = (
        "symbol",
        "direction",
        "entry",
        "sl",
        "tp1",
        "tp2",
        "rr",
        "confidence",
    )

    missing = [key for key in required if key not in item]

    if missing:
        return False, f"missing required fields: {', '.join(missing)}"

    return True, "immutable trade fields present"


def build_lifecycle_record(item: dict) -> dict:
    """
    Create a lifecycle record without changing trade construction.
    """

    return {
        "symbol": item["symbol"],
        "direction": item["direction"],
        "entry": item["entry"],
        "sl": item["sl"],
        "tp1": item["tp1"],
        "tp2": item["tp2"],
        "rr": item["rr"],
        "confidence": item["confidence"],

        "status": "VALIDATED_AWAITING_EXECUTION",
        "order_status": "NOT_SUBMITTED",
        "fill_status": "NOT_FILLED",

        "orders_submitted": 0,
        "active": False,
        "tp1_hit": False,
        "tp2_hit": False,
        "sl_hit": False,

        "execution_authorized": EXECUTION_AUTHORIZED,
        "order_submission": ORDER_SUBMISSION,
        "bot_armed": BOT_ARMED,
        "live_execution": LIVE_EXECUTION,
        "withdrawals": WITHDRAWALS,

        "created_utc": utc_now(),
    }


def save_state(records: list, source_count: int, rejected: list) -> None:
    OUTPUT_STATE.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "phase": 9,
        "name": "Execution + Lifecycle",
        "cycle": 1,
        "utc": utc_now(),

        "input": {
            "source": str(INPUT_STATE.relative_to(ROOT)),
            "phase": 8,
            "validated_candidates": source_count,
        },

        "lifecycle": {
            "orders_submitted": 0,
            "active_positions": [],
            "fills": [],
            "partial_fills": [],
            "closed_positions": [],
            "lifecycle_events": [],
        },

        "candidates": records,

        "rejected": rejected,

        "execution_boundary": {
            "status": EXECUTION_BOUNDARY,
            "execution_authorized": EXECUTION_AUTHORIZED,
            "order_submission": ORDER_SUBMISSION,
            "bot_armed": BOT_ARMED,
            "live_execution": LIVE_EXECUTION,
            "withdrawals": WITHDRAWALS,
        },

        "ownership": {
            "trade_construction": "PHASE 7",
            "final_validation": "PHASE 8",
            "execution": "PHASE 9",
            "trade_reconstruction": False,
            "entry_modification": False,
            "sl_modification": False,
            "tp_modification": False,
        },
    }

    with OUTPUT_STATE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def run_once() -> int:
    print("=" * 78)
    print("CRYPTOMASTERX1 — PHASE 9 EXECUTION + LIFECYCLE")
    print("=" * 78)

    state = load_phase8()

    candidates = get_validated_candidates(state)

    print(f"Phase 8 validated input : {len(candidates)}")
    print("Execution boundary      : LOCKED")
    print("Order submission        : DISABLED")
    print("Bot armed               : NO")
    print("Live execution          : FALSE")
    print("Withdrawals             : FORBIDDEN")
    print()

    records = []
    rejected = []

    for index, item in enumerate(candidates, 1):
        symbol = item.get("symbol", "UNKNOWN")

        print(
            f"PHASE 9 LIFECYCLE CHECK "
            f"{index}/{len(candidates)} {symbol}"
        )

        ok, reason = verify_trade_immutability(item)

        if not ok:
            rejected.append({
                "symbol": symbol,
                "reason": reason,
            })
            print(f"  REJECTED: {reason}")
            continue

        record = build_lifecycle_record(item)
        records.append(record)

        print(
            f"  {item['direction']} "
            f"CONF:{item['confidence']} "
            f"R:R:{item['rr']} "
            f"STATUS:AWAITING_EXECUTION"
        )

    save_state(records, len(candidates), rejected)

    print()
    print("=" * 78)
    print("PHASE 9 EXECUTION + LIFECYCLE COMPLETE")
    print("=" * 78)

    print(f"Validated input         : {len(candidates)}")
    print(f"Lifecycle-ready         : {len(records)}")
    print(f"Rejected                : {len(rejected)}")
    print()
    print("Orders submitted        : 0")
    print("Active positions        : 0")
    print("Fills                   : 0")
    print("Partial fills           : 0")
    print("Closed positions        : 0")
    print()
    print("Trade reconstruction    : FORBIDDEN")
    print("Entry modification      : FORBIDDEN")
    print("SL modification         : FORBIDDEN")
    print("TP modification         : FORBIDDEN")
    print()
    print("Execution boundary      : LOCKED")
    print("Order submission        : DISABLED")
    print("Bot armed               : NO")
    print("Live execution          : FALSE")
    print("Withdrawals             : FORBIDDEN")
    print("=" * 78)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if not args.once:
        print("Use: python -u phase9_execution_lifecycle.py --once")
        return 0

    try:
        return run_once()
    except Exception as exc:
        print()
        print("PHASE 9 ERROR:", type(exc).__name__, str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
