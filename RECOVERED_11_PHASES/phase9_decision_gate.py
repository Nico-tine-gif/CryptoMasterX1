import json
import time
from pathlib import Path
from datetime import datetime, timezone

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_9"
VERSION = "9.0-CLEAN"

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
REPORT_DIR = BASE_DIR / "reports"

PHASE8_STATE = STATE_DIR / "phase8_entry_validation.json"
PHASE9_STATE = STATE_DIR / "phase9_decision_gate.json"
PHASE9_REPORT = REPORT_DIR / "phase9_decision_gate_report.json"

REFRESH_SECONDS = 60

# SAFETY BOUNDARY — NEVER ENABLED BY THIS PHASE
EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, default=str)
    )


def load_phase8():
    if not PHASE8_STATE.exists():
        raise FileNotFoundError(
            f"Phase 8 state not found: {PHASE8_STATE}"
        )

    state = json.loads(PHASE8_STATE.read_text())

    validation = state.get("validation", {})

    candidates = validation.get(
        "validated_candidates",
        []
    )

    if not isinstance(candidates, list):
        candidates = []

    return candidates


def validate_candidate(candidate):
    symbol = candidate.get("symbol")
    direction = candidate.get("direction")

    reasons = []

    try:
        confidence = float(
            candidate.get("confidence", 0)
        )
    except (TypeError, ValueError):
        confidence = 0
        reasons.append("INVALID_CONFIDENCE")

    try:
        rr = float(
            candidate.get("rr", 0)
        )
    except (TypeError, ValueError):
        rr = 0
        reasons.append("INVALID_RR")

    entry = candidate.get("entry")
    sl = candidate.get("sl")
    tp1 = candidate.get("tp1")
    tp2 = candidate.get("tp2")

    if not symbol:
        reasons.append("MISSING_SYMBOL")

    if direction not in ("LONG", "SHORT"):
        reasons.append("INVALID_DIRECTION")

    if confidence < 75:
        reasons.append("CONFIDENCE_BELOW_GATE")

    if rr < 1.50:
        reasons.append("RR_BELOW_GATE")

    levels = {
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
    }

    numeric = {}

    for name, value in levels.items():
        if value is None:
            reasons.append(f"MISSING_{name.upper()}")
            continue

        try:
            value_f = float(value)

            if value_f <= 0:
                reasons.append(
                    f"INVALID_{name.upper()}"
                )
            else:
                numeric[name] = value_f

        except (TypeError, ValueError):
            reasons.append(
                f"INVALID_{name.upper()}"
            )

    if len(numeric) == 4 and direction in ("LONG", "SHORT"):
        entry_f = numeric["entry"]
        sl_f = numeric["sl"]
        tp1_f = numeric["tp1"]
        tp2_f = numeric["tp2"]

        if direction == "LONG":
            if not (
                sl_f
                < entry_f
                < tp1_f
                <= tp2_f
            ):
                reasons.append(
                    "INVALID_LONG_PRICE_STRUCTURE"
                )

        elif direction == "SHORT":
            if not (
                tp2_f
                <= tp1_f
                < entry_f
                < sl_f
            ):
                reasons.append(
                    "INVALID_SHORT_PRICE_STRUCTURE"
                )

    approved = len(reasons) == 0

    return {
        "symbol": symbol,
        "direction": direction,
        "confidence": confidence,
        "rr": rr,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "decision": (
            "QUALIFIED"
            if approved
            else "REJECTED"
        ),
        "qualified": approved,
        "reasons": reasons,
        "source_phase": "PHASE_8",
    }


def scan():
    candidates = load_phase8()

    results = []
    qualified = []
    rejected = []

    started = time.time()

    print(
        f"PHASE 9 STARTING — "
        f"{len(candidates)} PHASE 8 VALIDATED CANDIDATES",
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
            f"PHASE 9 DECISION {index}/"
            f"{len(candidates)} {symbol}",
            flush=True,
        )

        try:
            result = validate_candidate(
                candidate
            )

            results.append(result)

            if result["qualified"]:
                qualified.append(result)
            else:
                rejected.append(result)

        except Exception as exc:
            rejected.append({
                "symbol": symbol,
                "decision": "REJECTED",
                "qualified": False,
                "reasons": [
                    f"DECISION_ERROR: {exc}"
                ],
                "source_phase": "PHASE_8",
            })

    qualified.sort(
        key=lambda x: (
            x.get("confidence", 0),
            x.get("rr", 0),
        ),
        reverse=True,
    )

    elapsed = round(
        time.time() - started,
        2,
    )

    return {
        "phase8_candidates": len(candidates),
        "evaluated": len(results),
        "qualified": len(qualified),
        "rejected": len(rejected),
        "scan_seconds": elapsed,
        "qualified_candidates": qualified,
        "rejected_candidates": rejected,
        "all_results": results,
    }


def build_state(
    result,
    cycle,
    status="RUNNING",
):
    return {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now_utc(),
        "cycle": cycle,
        "status": status,

        "decision_gate": {
            "phase8_candidates":
                result["phase8_candidates"],
            "evaluated":
                result["evaluated"],
            "qualified":
                result["qualified"],
            "rejected":
                result["rejected"],
            "scan_seconds":
                result["scan_seconds"],
            "qualified_candidates":
                result["qualified_candidates"],
            "rejected_candidates":
                result["rejected_candidates"],
            "all_results":
                result["all_results"],
        },

        "gates": {
            "minimum_confidence": 75.0,
            "minimum_rr": 1.50,
            "price_structure_required": True,
        },

        "execution_boundary": {
            "execution_authorized": False,
            "order_submission": False,
            "bot_armed": False,
            "live_execution": False,
            "withdrawals": False,
            "deposits": False,
            "transfers": False,
        },
    }


def display(result, cycle):
    print()
    print("=" * 78)
    print(
        "CRYPTOMASTERX1 — "
        "PHASE 9 DECISION GATE"
    )
    print("=" * 78)

    print(f"Cycle                    : {cycle}")
    print(f"UTC                      : {now_utc()}")
    print(
        "Phase 8 validated input : "
        f"{result['phase8_candidates']}"
    )
    print(
        f"Evaluated                : "
        f"{result['evaluated']}"
    )
    print(
        f"Qualified                : "
        f"{result['qualified']}"
    )
    print(
        f"Rejected                 : "
        f"{result['rejected']}"
    )

    print()
    print("QUALIFIED CANDIDATES")
    print("-" * 78)

    if not result["qualified_candidates"]:
        print("None")
    else:
        for index, item in enumerate(
            result["qualified_candidates"],
            start=1,
        ):
            print(
                f"{index:2}. "
                f"{item['symbol']:<16} "
                f"{item['direction']:<6} "
                f"CONF: "
                f"{item['confidence']:.2f} "
                f"R:R: "
                f"{item['rr']:.2f} "
                f"DECISION: "
                f"{item['decision']}"
            )

    print()
    print("=" * 78)
    print("PHASE 9 DECISION GATE COMPLETE")
    print("=" * 78)

    print()
    print("Execution boundary: LOCKED")
    print("Order submission   : DISABLED")
    print("Bot armed          : NO")
    print("Live execution     : FALSE")


def main():
    cycle = 0

    while True:
        cycle += 1

        try:
            result = scan()

            state = build_state(
                result,
                cycle,
                "RUNNING",
            )

            save_json(
                PHASE9_STATE,
                state,
            )

            save_json(
                PHASE9_REPORT,
                state,
            )

            display(
                result,
                cycle,
            )

            print(
                f"\nNext Phase 9 scan in "
                f"{REFRESH_SECONDS} seconds...",
                flush=True,
            )

            time.sleep(
                REFRESH_SECONDS
            )

        except KeyboardInterrupt:
            if PHASE9_STATE.exists():
                existing = json.loads(
                    PHASE9_STATE.read_text()
                )

                existing["status"] = "STOPPED"
                existing["stopped_utc"] = now_utc()

                save_json(
                    PHASE9_STATE,
                    existing,
                )

            print(
                "\nPHASE 9 STOPPED.",
                flush=True,
            )

            break

        except Exception as exc:
            print(
                f"PHASE 9 ERROR: {exc}",
                flush=True,
            )

            time.sleep(
                REFRESH_SECONDS
            )


if __name__ == "__main__":
    main()
