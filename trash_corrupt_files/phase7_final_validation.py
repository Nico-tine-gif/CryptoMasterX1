#!/usr/bin/env python3

"""
CryptoMasterX1
PHASE 7 — EXECUTION + ORDER OPENING

Phase 7 owns the exchange execution boundary.

IMPORTANT:
    This implementation is intentionally LOCKED.

It can validate Phase 6 trade-ready objects and prepare an
execution request, but cannot submit a live order until the
explicit global execution gates are changed during a separate
verified activation process.

Withdrawals remain permanently forbidden.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"

PHASE6_STATE = STATE / "phase6_trade_intelligence.json"
PHASE7_STATE = STATE / "phase7_final_validation.json"

EXECUTION_AUTHORIZED = False
BOT_ARMED = False
LIVE_EXECUTION = False
ORDER_SUBMISSION = False

# HARD SAFETY BOUNDARY
WITHDRAWALS = False


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def load_json(path):
    return json.loads(path.read_text())


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def validate_trade(trade):
    required = (
        "symbol",
        "direction",
        "entry",
        "sl",
        "tp1",
        "tp2",
        "risk",
        "reward",
        "rr",
    )

    for key in required:
        if trade.get(key) is None:
            return False, f"missing {key}"

    entry = float(trade["entry"])
    sl = float(trade["sl"])
    tp1 = float(trade["tp1"])
    tp2 = float(trade["tp2"])
    rr = float(trade["rr"])

    if trade["direction"] == "LONG":
        if not sl < entry < tp1 < tp2:
            return False, "invalid LONG price structure"

    elif trade["direction"] == "SHORT":
        if sl > entry > tp1 > tp2:
            pass
        else:
            return False, "invalid SHORT price structure"

    else:
        return False, "invalid direction"

    risk = abs(entry - sl)
    reward = abs(tp2 - entry)

    if risk <= 0:
        return False, "zero risk"

    calculated_rr = reward / risk

    if calculated_rr < 1.50:
        return False, "R:R below minimum"

    if abs(calculated_rr - rr) > 1e-8:
        return False, "R:R mismatch"

    return True, "VALID"


def execution_enabled():
    return bool(
        EXECUTION_AUTHORIZED
        and BOT_ARMED
        and LIVE_EXECUTION
        and ORDER_SUBMISSION
        and not WITHDRAWALS
    )


def main():
    STATE.mkdir(exist_ok=True)

    source = load_json(PHASE6_STATE)

    valid = []
    rejected = []

    for trade in source.get("trades", []):
        ok, reason = validate_trade(trade)

        if ok:
            valid.append(trade)
        else:
            rejected.append({
                "symbol": trade.get("symbol"),
                "reason": reason,
            })

    output = {
        "phase": 7,
        "phase_name": "EXECUTION + ORDER OPENING",
        "timestamp_utc": now_utc(),

        "phase6_input": len(source.get("trades", [])),
        "validated_trades": len(valid),
        "rejected_trades": len(rejected),

        "validated": valid,
        "rejected": rejected,

        "execution_boundary": {
            "execution_authorized": EXECUTION_AUTHORIZED,
            "bot_armed": BOT_ARMED,
            "live_execution": LIVE_EXECUTION,
            "order_submission": ORDER_SUBMISSION,
            "withdrawals": WITHDRAWALS,
            "execution_enabled": execution_enabled(),
        },

        "order_submission_status": "LOCKED",
    }

    save_json(PHASE7_STATE, output)

    print()
    print("PHASE 7 — EXECUTION + ORDER OPENING")
    print(f"Phase 6 input       : {source.get('trades', []).__len__()}")
    print(f"Validated           : {len(valid)}")
    print(f"Rejected            : {len(rejected)}")
    print(f"Execution enabled   : {execution_enabled()}")
    print("Order submission    : LOCKED")
    print("Withdrawals         : FORBIDDEN")
    print(f"State saved         : {PHASE7_STATE}")


if __name__ == "__main__":
    main()
