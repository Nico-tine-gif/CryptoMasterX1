import os
#!/usr/bin/env python3

from pathlib import Path
import json
from datetime import datetime, timezone


BASE = Path.home() / "CryptoMasterX1"
STATE_DIR = BASE / "state"
STATE_DIR.mkdir(exist_ok=True)

PHASE6_STATE = STATE_DIR / "phase6_trade_intelligence.json"
PHASE7_STATE = STATE_DIR / "phase7_entry_intelligence.json"


def load_phase6_trades():
    if not PHASE6_STATE.exists():
        return []

    try:
        data = json.loads(PHASE6_STATE.read_text())
        return data.get("trades") or data.get("constructed_trades") or []
    except Exception as e:
        print(f"PHASE 6 LOAD ERROR: {e}")
        return []


def is_valid_trade(trade):
    if not isinstance(trade, dict):
        return False

    sizing = trade.get("position_sizing") or {}

    # Phase 6 is authoritative for position-sizing validity.
    if sizing.get("status") != "VALID":
        return False

    if trade.get("position_size") is None:
        return False

    required = (
        "symbol",
        "direction",
        "entry",
        "sl",
        "tp1",
        "tp2",
        "rr",
    )

    return all(trade.get(key) is not None for key in required)


def run(state=None):

    print("=== PHASE 7 ENTRY INTELLIGENCE ===")

    if not isinstance(state, dict):
        state = {}

    trades = state.get("phase6_trades") or []

    if not trades:
        trades = load_phase6_trades()

    print(f"Phase6 trades received : {len(trades)}")

    # ------------------------------------------------------------
    # FILTER PHASE 6 REJECTED TRADES
    # ------------------------------------------------------------

    phase7_trades = []
    rejected = []

    for trade in trades:

        if not isinstance(trade, dict):
            continue

        if not is_valid_trade(trade):
            rejected.append({
                "symbol": trade.get("symbol"),
                "direction": trade.get("direction"),
                "reason": (
                    trade.get("position_sizing", {}).get("reason")
                    if isinstance(trade.get("position_sizing"), dict)
                    else "INVALID_TRADE"
                ),
            })
            continue

        t = dict(trade)

        t["entry_intelligence_status"] = "PASSED"

        # Canonical sizing field.
        t["position_size"] = trade.get("position_size")

        # Execution remains locked.
        t["execution_authorized"] = False
        t["order_submission"] = False

        phase7_trades.append(t)

    # ------------------------------------------------------------
    # SAVE PHASE 7 STATE
    # ------------------------------------------------------------

    output = {
        "project": "CryptoMasterX1",
        "phase": "7",
        "version": "ENTRY_INTELLIGENCE",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cycle": state.get("cycle"),

        "status": "COMPLETE",

        "intelligence": {
            "phase6_received": len(trades),
            "phase7_accepted": len(phase7_trades),
            "phase7_rejected": len(rejected),
            "position_sizes_valid": sum(
                1
                for t in phase7_trades
                if t.get("position_size") is not None
            ),
        },

        "rejected_trades": rejected,

        "construction_contract": {
            "symbol": True,
            "direction": True,
            "entry": True,
            "sl": True,
            "tp1": True,
            "tp2": True,
            "position_size": True,
            "rr": True,
        },

        "gates": {
            "entry_intelligence": "PASSED",
            "execution_authorized": os.getenv("ALLOW_LIVE","false").lower()=="true",
            "order_submission": False,
        },

        "trades": phase7_trades,

        "execution_boundary": {
            "live_execution": False,
            "bot_armed": False,
            "order_submission": False,
            "transmission": "UNUNLOCKED",
            "withdrawals": False,
        },

        "stopped_utc": datetime.now(timezone.utc).isoformat(),
    }

    PHASE7_STATE.write_text(
        json.dumps(output, indent=2)
    )

    # ------------------------------------------------------------
    # PIPELINE HANDOFF
    # ------------------------------------------------------------

    state["phase6_trades"] = trades
    state["phase7_trades"] = phase7_trades
    state["entry_trades"] = phase7_trades

    state["execution_authorized"] = False
    state["order_submission"] = False

    print(f"Phase7 accepted        : {len(phase7_trades)}")
    print(f"Phase7 rejected        : {len(rejected)}")
    print(
        "Position sizes valid   : "
        f"{sum(1 for t in phase7_trades if t.get('position_size') is not None)}"
    )

    if rejected:
        print("\nREJECTED BY PHASE 7:")
        for r in rejected:
            print(
                f" -> {r['symbol']} {r['direction']} "
                f"reason={r['reason']}"
            )

    print(f"\nState saved            : {PHASE7_STATE}")

    return state


def main(state=None):
    return run(state)


if __name__ == "__main__":
    run({})
