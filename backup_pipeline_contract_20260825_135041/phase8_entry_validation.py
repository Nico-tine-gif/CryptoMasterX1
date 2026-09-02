import json
import time
from pathlib import Path
from datetime import datetime, timezone

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_8"
VERSION = "8.0-CLEAN"

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
REPORT_DIR = BASE_DIR / "reports"

PHASE7_STATE = STATE_DIR / "phase7_entry_intelligence.json"
PHASE8_STATE = STATE_DIR / "phase8_entry_validation.json"
PHASE8_REPORT = REPORT_DIR / "phase8_entry_validation_report.json"

REFRESH_SECONDS = 60

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def load_phase7():
    if not PHASE7_STATE.exists():
        raise FileNotFoundError(
            f"Phase 7 state not found: {PHASE7_STATE}"
        )

    state = json.loads(PHASE7_STATE.read_text())

    intelligence = state.get("intelligence", {})
    ready = intelligence.get("ready", [])

    if not isinstance(ready, list):
        ready = []

    return ready


def validate_entry(candidate):
    symbol = candidate.get("symbol")
    direction = candidate.get("direction")

    confidence = float(
        candidate.get(
            "confidence",
            candidate.get("phase6_confidence", 0),
        )
    )

    rr = float(
        candidate.get(
            "rr",
            candidate.get("phase6_rr", 0),
        )
    )

    entry = candidate.get("entry")
    sl = candidate.get("sl")
    tp1 = candidate.get("tp1")
    tp2 = candidate.get("tp2")

    reasons = []

    if not symbol:
        reasons.append("MISSING_SYMBOL")

    if direction not in ("LONG", "SHORT"):
        reasons.append("INVALID_DIRECTION")

    if confidence < 75:
        reasons.append("CONFIDENCE_BELOW_GATE")

    if rr < 1.50:
        reasons.append("RR_BELOW_GATE")

    numeric_levels = {
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
    }

    for name, value in numeric_levels.items():
        if value is None:
            reasons.append(f"MISSING_{name.upper()}")
        else:
            try:
                if float(value) <= 0:
                    reasons.append(f"INVALID_{name.upper()}")
            except (TypeError, ValueError):
                reasons.append(f"INVALID_{name.upper()}")

    if not reasons:
        entry_f = float(entry)
        sl_f = float(sl)
        tp1_f = float(tp1)
        tp2_f = float(tp2)

        if direction == "LONG":
            if not (sl_f < entry_f < tp1_f <= tp2_f):
                reasons.append("INVALID_LONG_PRICE_STRUCTURE")

        elif direction == "SHORT":
            if not (tp2_f <= tp1_f < entry_f < sl_f):
                reasons.append("INVALID_SHORT_PRICE_STRUCTURE")

    validated = not reasons

    return {
        "symbol": symbol,
        "direction": direction,
        "confidence": confidence,
        "rr": rr,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "validated": validated,
        "reasons": reasons,
        "source_phase": "PHASE_7",
    }


def scan():
    candidates = load_phase7()

    results = []
    validated = []
    rejected = []

    started = time.time()

    print(
        f"PHASE 8 STARTING — {len(candidates)} PHASE 7 READY CANDIDATES",
        flush=True,
    )

    for index, candidate in enumerate(candidates, start=1):
        symbol = candidate.get("symbol", "UNKNOWN")

        print(
            f"PHASE 8 VALIDATING {index}/{len(candidates)} {symbol}",
            flush=True,
        )

        try:
            result = validate_entry(candidate)
            results.append(result)

            if result["validated"]:
                validated.append(result)
            else:
                rejected.append(result)

        except Exception as exc:
            rejected.append({
                "symbol": symbol,
                "validated": False,
                "reasons": [f"VALIDATION_ERROR: {exc}"],
            })

    validated.sort(
        key=lambda x: (
            x.get("confidence", 0),
            x.get("rr", 0),
        ),
        reverse=True,
    )

    elapsed = round(time.time() - started, 2)

    return {
        "phase7_candidates": len(candidates),
        "evaluated": len(results),
        "validated": len(validated),
        "rejected": len(rejected),
        "scan_seconds": elapsed,
        "validated_candidates": validated,
        "rejected_candidates": rejected,
        "all_results": results,
    }


def build_state(result, cycle, status="RUNNING"):
    return {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now_utc(),
        "cycle": cycle,
        "status": status,

        "validation": {
            "phase7_candidates": result["phase7_candidates"],
            "evaluated": result["evaluated"],
            "validated": result["validated"],
            "rejected": result["rejected"],
            "scan_seconds": result["scan_seconds"],
            "validated_candidates": result["validated_candidates"],
            "rejected_candidates": result["rejected_candidates"],
            "all_results": result["all_results"],
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
    print("CRYPTOMASTERX1 — PHASE 8 ENTRY VALIDATION")
    print("=" * 78)

    print(f"Cycle                    : {cycle}")
    print(f"UTC                      : {now_utc()}")
    print(f"Phase 7 ready input      : {result['phase7_candidates']}")
    print(f"Evaluated                : {result['evaluated']}")
    print(f"Validated                : {result['validated']}")
    print(f"Rejected                 : {result['rejected']}")

    print()
    print("VALIDATED CANDIDATES")
    print("-" * 78)

    if not result["validated_candidates"]:
        print("None")
    else:
        for index, item in enumerate(
            result["validated_candidates"],
            start=1,
        ):
            print(
                f"{index:2}. "
                f"{item['symbol']:<16} "
                f"{item['direction']:<6} "
                f"CONF: {item['confidence']:.2f} "
                f"R:R: {item['rr']:.2f} "
                f"ENTRY: {item['entry']}"
            )

    print()
    print("=" * 78)
    print("PHASE 8 ENTRY VALIDATION COMPLETE")
    print("=" * 78)

    print()
    print("Execution boundary: LOCKED")
    print("Order submission   : DISABLED")
    print("Bot armed          : NO")


def main():
    cycle = 0

    import sys
    once = '--once' in sys.argv
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
                PHASE8_STATE,
                state,
            )

            save_json(
                PHASE8_REPORT,
                state,
            )

            display(
                result,
                cycle,
            )

            print(
                f"\nNext Phase 8 scan in {REFRESH_SECONDS} seconds...",
                flush=True,
            )

            import sys
            if '--once' in sys.argv or once:
                print('ONCE MODE - EXIT'); break
            time.sleep(REFRESH_SECONDS)

        except KeyboardInterrupt:
            if PHASE8_STATE.exists():
                existing = json.loads(
                    PHASE8_STATE.read_text()
                )

                existing["status"] = "STOPPED"
                existing["stopped_utc"] = now_utc()

                save_json(
                    PHASE8_STATE,
                    existing,
                )

            print("\nPHASE 8 STOPPED.", flush=True)
            break

        except Exception as exc:
            print(
                f"PHASE 8 ERROR: {exc}",
                flush=True,
            )

            import sys
            if '--once' in sys.argv or once:
                print('ONCE MODE - EXIT'); break
            time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()
