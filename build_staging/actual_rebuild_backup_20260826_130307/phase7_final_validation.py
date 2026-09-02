#!/usr/bin/env python3

import json
import time
from pathlib import Path
from datetime import datetime, timezone

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_7"
VERSION = "7.0-CONSOLIDATED"

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
REPORTS = ROOT / "reports"

PHASE6_STATE = STATE / "phase6_trade_intelligence.json"
PHASE7_STATE = STATE / "phase7_final_validation.json"
PHASE7_REPORT = REPORTS / "phase7_final_validation_report.json"

MIN_CONFIDENCE = 75.0
MIN_RR = 1.50

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


def load():
    if not PHASE6_STATE.exists():
        raise FileNotFoundError(
            f"Phase 6 state missing: {PHASE6_STATE}"
        )

    return json.loads(PHASE6_STATE.read_text())


def validate(candidate):
    reasons = []

    symbol = candidate.get("symbol")
    direction = candidate.get("direction")

    if not symbol:
        reasons.append("MISSING_SYMBOL")

    if direction not in ("LONG", "SHORT"):
        reasons.append("INVALID_DIRECTION")

    try:
        confidence = float(
            candidate.get("confidence", 0)
        )
    except Exception:
        confidence = 0
        reasons.append("INVALID_CONFIDENCE")

    try:
        rr = float(candidate.get("rr", 0))
    except Exception:
        rr = 0
        reasons.append("INVALID_RR")

    if confidence < MIN_CONFIDENCE:
        reasons.append("CONFIDENCE_BELOW_GATE")

    if rr < MIN_RR:
        reasons.append("RR_BELOW_GATE")

    levels = {}

    for name in (
        "entry",
        "sl",
        "tp1",
        "tp2",
    ):
        value = candidate.get(name)

        if value is None:
            reasons.append(
                f"MISSING_{name.upper()}"
            )
            continue

        try:
            value = float(value)

            if value <= 0:
                reasons.append(
                    f"INVALID_{name.upper()}"
                )
            else:
                levels[name] = value

        except Exception:
            reasons.append(
                f"INVALID_{name.upper()}"
            )

    # Freshness must have been proven by Phase 6.
    if candidate.get("fresh_data_verified") is not True:
        reasons.append("FRESH_DATA_NOT_VERIFIED")

    if candidate.get("fresh_market") is None:
        reasons.append("FRESH_MARKET_MISSING")

    sizing = candidate.get("position_size")

    if not isinstance(sizing, dict):
        reasons.append("POSITION_SIZE_MISSING")
    else:
        try:
            if float(sizing.get("quantity", 0)) <= 0:
                reasons.append("INVALID_POSITION_SIZE")
        except Exception:
            reasons.append("INVALID_POSITION_SIZE")

    if len(levels) == 4:
        entry = levels["entry"]
        sl = levels["sl"]
        tp1 = levels["tp1"]
        tp2 = levels["tp2"]

        if direction == "LONG":
            if not (
                sl < entry < tp1 <= tp2
            ):
                reasons.append(
                    "INVALID_LONG_PRICE_STRUCTURE"
                )

        elif direction == "SHORT":
            if not (
                tp2 <= tp1 < entry < sl
            ):
                reasons.append(
                    "INVALID_SHORT_PRICE_STRUCTURE"
                )

        risk = abs(entry - sl)
        reward = abs(tp2 - entry)

        if risk <= 0:
            reasons.append("ZERO_RISK")

        else:
            actual_rr = reward / risk

            if abs(actual_rr - rr) > 1e-9:
                reasons.append(
                    "RR_DOES_NOT_MATCH_ACTUAL_LEVELS"
                )

            if actual_rr < MIN_RR:
                reasons.append(
                    "ACTUAL_RR_BELOW_GATE"
                )

    return {
        **candidate,

        "decision": (
            "QUALIFIED"
            if not reasons
            else "REJECTED"
        ),

        "qualified": not reasons,
        "validation_reasons": reasons,

        "final_validation_owner": "PHASE_7",
        "levels_owner": "PHASE_6",

        "validated_utc": now(),
    }


def run_once():
    state = load()

    candidates = state.get(
        "constructed_candidates",
        [],
    )

    if not isinstance(candidates, list):
        candidates = []

    qualified = []
    rejected = []

    print(
        f"PHASE 7 STARTING — FINAL VALIDATION OF "
        f"{len(candidates)} PHASE 6 CANDIDATES",
        flush=True,
    )

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        symbol = candidate.get(
            "symbol",
            "UNKNOWN",
        )

        print(
            f"PHASE 7 {index}/{len(candidates)} "
            f"FINAL DECISION {symbol}",
            flush=True,
        )

        result = validate(candidate)

        if result["qualified"]:
            qualified.append(result)
        else:
            rejected.append(result)

    qualified.sort(
        key=lambda x: (
            x.get("confidence", 0),
            x.get("rr", 0),
        ),
        reverse=True,
    )

    result = {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now(),

        "phase6_candidates": len(candidates),
        "evaluated": len(candidates),
        "qualified": len(qualified),
        "rejected": len(rejected),

        "qualified_candidates": qualified,
        "rejected_candidates": rejected,

        "decision_gate": {
            "minimum_confidence": MIN_CONFIDENCE,
            "minimum_rr": MIN_RR,
            "fresh_data_required": True,
            "position_size_required": True,
            "single_authoritative_gate": True,
        },

        "execution_boundary": {
            "execution_authorized": False,
            "order_submission": False,
            "bot_armed": False,
            "live_execution": False,
            "transmission_locked": True,
            "withdrawals": False,
            "deposits": False,
            "transfers": False,
        },
    }

    save(PHASE7_STATE, result)
    save(PHASE7_REPORT, result)

    print()
    print("=" * 78)
    print("CRYPTOMASTERX1 — PHASE 7 COMPLETE")
    print("=" * 78)
    print(f"Phase 6 candidates : {len(candidates)}")
    print(f"Qualified          : {len(qualified)}")
    print(f"Rejected           : {len(rejected)}")
    print()

    for i, item in enumerate(
        qualified,
        start=1,
    ):
        print(
            f"{i:2}. "
            f"{item['symbol']:<16} "
            f"{item['direction']:<6} "
            f"CONF:{item['confidence']:.2f} "
            f"ENTRY:{item['entry']} "
            f"SL:{item['sl']} "
            f"TP1:{item['tp1']} "
            f"TP2:{item['tp2']} "
            f"R:R:{item['rr']:.2f} "
            f"QTY:{item['position_size']['quantity_decimal']}"
        )

    print()
    print("FINAL DECISION GATE: PASS/REJECT")
    print("Execution boundary: LOCKED")
    print("Order submission   : DISABLED")
    print("Withdrawals        : FORBIDDEN")
    print("=" * 78)

    return result


if __name__ == "__main__":
    run_once()
