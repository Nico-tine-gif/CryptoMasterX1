#!/usr/bin/env python3

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "CryptoMasterX1"
PHASE = "PHASE_8"
VERSION = "8.0-FINAL-VALIDATION"

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
REPORT_DIR = BASE_DIR / "reports"

PHASE7_STATE = STATE_DIR / "phase7_entry_intelligence.json"
PHASE8_STATE = STATE_DIR / "phase8_final_validation.json"
PHASE8_REPORT = REPORT_DIR / "phase8_final_validation_report.json"

REFRESH_SECONDS = 60

MIN_CONFIDENCE = 75.0
MIN_RR = 1.50

# HARD EXECUTION SAFETY BOUNDARY
EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
WITHDRAWALS = False
DEPOSITS = False
TRANSFERS = False
TRANSMISSION = "LOCKED"


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


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

    return state, ready


def number(value, default=0.0):
    try:
        value = float(value)
        if math.isfinite(value):
            return value
    except (TypeError, ValueError):
        pass

    return default


def validate_candidate(candidate):
    symbol = candidate.get("symbol", "UNKNOWN")
    direction = candidate.get("direction")

    confidence = number(
        candidate.get("confidence")
    )

    rr = number(
        candidate.get("rr")
    )

    entry = candidate.get("entry")
    sl = candidate.get("sl")
    tp1 = candidate.get("tp1")
    tp2 = candidate.get("tp2")

    reasons = []

    # --------------------------------------------------------------
    # IDENTITY / DIRECTION
    # --------------------------------------------------------------

    if not symbol:
        reasons.append("MISSING_SYMBOL")

    if direction not in ("LONG", "SHORT"):
        reasons.append("INVALID_DIRECTION")

    # --------------------------------------------------------------
    # CONFIDENCE / R:R
    # --------------------------------------------------------------

    if confidence < MIN_CONFIDENCE:
        reasons.append("CONFIDENCE_BELOW_GATE")

    if rr < MIN_RR:
        reasons.append("RR_BELOW_GATE")

    # --------------------------------------------------------------
    # REQUIRED TRADE-CONSTRUCTION FIELDS
    # --------------------------------------------------------------

    levels = {
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
    }

    numeric = {}

    for name, value in levels.items():

        if value is None:
            reasons.append(
                f"MISSING_{name.upper()}"
            )
            continue

        try:
            converted = float(value)

            if not math.isfinite(converted):
                raise ValueError

            if converted <= 0:
                reasons.append(
                    f"INVALID_{name.upper()}"
                )
            else:
                numeric[name] = converted

        except (TypeError, ValueError):
            reasons.append(
                f"INVALID_{name.upper()}"
            )

    # --------------------------------------------------------------
    # PRICE STRUCTURE
    # --------------------------------------------------------------

    if len(numeric) == 4 and direction in ("LONG", "SHORT"):

        entry_f = numeric["entry"]
        sl_f = numeric["sl"]
        tp1_f = numeric["tp1"]
        tp2_f = numeric["tp2"]

        if direction == "LONG":

            if not (
                sl_f < entry_f < tp1_f <= tp2_f
            ):
                reasons.append(
                    "INVALID_LONG_PRICE_STRUCTURE"
                )

        else:

            if not (
                tp2_f <= tp1_f < entry_f < sl_f
            ):
                reasons.append(
                    "INVALID_SHORT_PRICE_STRUCTURE"
                )

        # Recalculate R:R independently.
        risk = abs(entry_f - sl_f)
        reward = abs(tp2_f - entry_f)

        if risk <= 0:
            reasons.append("ZERO_RISK")
            calculated_rr = 0.0
        else:
            calculated_rr = reward / risk

        if abs(calculated_rr - rr) > 0.01:
            reasons.append(
                "RR_CALCULATION_MISMATCH"
            )

    else:
        calculated_rr = 0.0

    # --------------------------------------------------------------
    # PHASE 7 CONSTRUCTION CONTRACT
    # --------------------------------------------------------------

    construction_contract = candidate.get(
        "construction_contract",
        {},
    )

    if not isinstance(construction_contract, dict):
        construction_contract = {}

    if construction_contract.get(
        "fresh_market_feed_required"
    ) is not True:
        reasons.append(
            "FRESH_FEED_CONTRACT_MISSING"
        )

    if construction_contract.get(
        "entry_constructed_here"
    ) is not True:
        reasons.append(
            "ENTRY_OWNERSHIP_CONTRACT_FAILED"
        )

    if construction_contract.get(
        "sl_constructed_here"
    ) is not True:
        reasons.append(
            "SL_OWNERSHIP_CONTRACT_FAILED"
        )

    if construction_contract.get(
        "tp1_constructed_here"
    ) is not True:
        reasons.append(
            "TP1_OWNERSHIP_CONTRACT_FAILED"
        )

    if construction_contract.get(
        "tp2_constructed_here"
    ) is not True:
        reasons.append(
            "TP2_OWNERSHIP_CONTRACT_FAILED"
        )

    if construction_contract.get(
        "rr_calculated_here"
    ) is not True:
        reasons.append(
            "RR_OWNERSHIP_CONTRACT_FAILED"
        )

    # --------------------------------------------------------------
    # FRESH-FEED EVIDENCE
    # --------------------------------------------------------------

    if not candidate.get("feed_checked_utc"):
        reasons.append(
            "FRESH_FEED_TIMESTAMP_MISSING"
        )

    if candidate.get("fresh_direction") not in (
        "LONG",
        "SHORT",
    ):
        reasons.append(
            "FRESH_DIRECTION_MISSING"
        )

    if candidate.get("analytical_direction") != direction:
        reasons.append(
            "ANALYTICAL_DIRECTION_MISMATCH"
        )

    if (
        candidate.get("fresh_direction")
        != direction
    ):
        reasons.append(
            "FRESH_DIRECTION_MISMATCH"
        )

    # --------------------------------------------------------------
    # RESULT
    # --------------------------------------------------------------

    validated = not reasons

    return {
        "symbol": symbol,
        "direction": direction,
        "confidence": confidence,
        "phase6_quality_score": number(
            candidate.get(
                "phase6_quality_score"
            )
        ),
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr,
        "calculated_rr": round(
            calculated_rr,
            6,
        ),
        "validated": validated,
        "reasons": reasons,
        "source_phase": "PHASE_7",
        "validation_phase": "PHASE_8",
        "levels_owner": "PHASE_7",
    }


def scan():

    phase7_state, candidates = load_phase7()

    results = []
    validated = []
    rejected = []

    started = time.time()

    print(
        f"PHASE 8 STARTING — "
        f"{len(candidates)} PHASE 7 READY CANDIDATES",
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
            f"PHASE 8 FINAL VALIDATION "
            f"{index}/{len(candidates)} "
            f"{symbol}",
            flush=True,
        )

        try:

            result = validate_candidate(
                candidate
            )

            results.append(result)

            if result["validated"]:
                validated.append(result)
            else:
                rejected.append(result)

        except Exception as exc:

            failed = {
                "symbol": symbol,
                "validated": False,
                "reasons": [
                    f"VALIDATION_ERROR: {exc}"
                ],
                "source_phase": "PHASE_8",
            }

            results.append(failed)
            rejected.append(failed)

    validated.sort(
        key=lambda x: (
            number(
                x.get("confidence")
            ),
            number(
                x.get("rr")
            ),
        ),
        reverse=True,
    )

    elapsed = round(
        time.time() - started,
        2,
    )

    return {
        "phase7_candidates": len(candidates),
        "evaluated": len(results),
        "validated": len(validated),
        "rejected": len(rejected),
        "scan_seconds": elapsed,
        "validated_candidates": validated,
        "rejected_candidates": rejected,
        "all_results": results,
        "phase7_timestamp_utc": phase7_state.get(
            "timestamp_utc"
        ),
    }


def build_state(
    result,
    cycle,
    status="COMPLETE",
):

    return {
        "project": PROJECT,
        "phase": PHASE,
        "version": VERSION,
        "timestamp_utc": now_utc(),
        "cycle": cycle,
        "status": status,

        "input": {
            "source_phase": "PHASE_7",
            "source_state": str(
                PHASE7_STATE
            ),
            "phase7_timestamp_utc":
                result[
                    "phase7_timestamp_utc"
                ],
        },

        "validation": {
            "phase7_candidates":
                result[
                    "phase7_candidates"
                ],
            "evaluated":
                result["evaluated"],
            "validated":
                result["validated"],
            "rejected":
                result["rejected"],
            "scan_seconds":
                result["scan_seconds"],
            "validated_candidates":
                result[
                    "validated_candidates"
                ],
            "rejected_candidates":
                result[
                    "rejected_candidates"
                ],
            "all_results":
                result["all_results"],
        },

        "validation_contract": {
            "phase7_owns_trade_construction":
                True,
            "phase8_reconstructs_trade":
                False,
            "phase8_changes_entry":
                False,
            "phase8_changes_sl":
                False,
            "phase8_changes_tp1":
                False,
            "phase8_changes_tp2":
                False,
            "phase8_recalculates_rr_for_validation":
                True,
            "fresh_feed_evidence_required":
                True,
            "minimum_confidence":
                MIN_CONFIDENCE,
            "minimum_rr":
                MIN_RR,
        },

        "execution_boundary": {
            "execution_authorized":
                EXECUTION_AUTHORIZED,
            "order_submission":
                ORDER_SUBMISSION,
            "bot_armed":
                BOT_ARMED,
            "live_execution":
                LIVE_EXECUTION,
            "withdrawals":
                WITHDRAWALS,
            "deposits":
                DEPOSITS,
            "transfers":
                TRANSFERS,
            "transmission":
                TRANSMISSION,
        },
    }


def display(result, cycle):

    print()
    print("=" * 78)
    print(
        "CRYPTOMASTERX1 — "
        "PHASE 8 FINAL VALIDATION"
    )
    print("=" * 78)

    print(
        f"Cycle                    : {cycle}"
    )
    print(
        f"UTC                      : {now_utc()}"
    )
    print(
        f"Phase 7 ready input      : "
        f"{result['phase7_candidates']}"
    )
    print(
        f"Evaluated                : "
        f"{result['evaluated']}"
    )
    print(
        f"Validated                : "
        f"{result['validated']}"
    )
    print(
        f"Rejected                 : "
        f"{result['rejected']}"
    )

    print()
    print("FINAL VALIDATED CANDIDATES")
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
                f"CONF: "
                f"{item['confidence']:.2f} "
                f"R:R: "
                f"{item['rr']:.2f} "
                f"ENTRY: "
                f"{item['entry']} "
                f"SL: "
                f"{item['sl']} "
                f"TP1: "
                f"{item['tp1']} "
                f"TP2: "
                f"{item['tp2']}"
            )

    print()
    print("=" * 78)
    print(
        "PHASE 8 FINAL VALIDATION COMPLETE"
    )
    print("=" * 78)

    print()
    print("Trade construction owner : PHASE 7")
    print("Trade reconstruction     : FORBIDDEN")
    print("Entry modification       : FORBIDDEN")
    print("SL modification          : FORBIDDEN")
    print("TP modification          : FORBIDDEN")
    print("Fresh-feed evidence      : REQUIRED")

    print()
    print("Execution boundary       : LOCKED")
    print("Order submission         : DISABLED")
    print("Bot armed                : NO")
    print("Live execution           : FALSE")
    print("Withdrawals              : FORBIDDEN")


def main():

    import sys

    once = "--once" in sys.argv
    cycle = 0

    while True:

        cycle += 1

        try:

            result = scan()

            state = build_state(
                result,
                cycle,
                "COMPLETE",
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

            if once:
                print(
                    "\nONCE MODE - EXIT"
                )
                break

            print(
                f"\nNext Phase 8 scan in "
                f"{REFRESH_SECONDS} seconds...",
                flush=True,
            )

            time.sleep(
                REFRESH_SECONDS
            )

        except KeyboardInterrupt:

            if PHASE8_STATE.exists():

                try:
                    existing = json.loads(
                        PHASE8_STATE.read_text()
                    )
                except Exception:
                    existing = {}

                existing["status"] = "STOPPED"
                existing["stopped_utc"] = now_utc()

                existing[
                    "execution_boundary"
                ] = {
                    "execution_authorized":
                        False,
                    "order_submission":
                        False,
                    "bot_armed":
                        False,
                    "live_execution":
                        False,
                    "withdrawals":
                        False,
                    "deposits":
                        False,
                    "transfers":
                        False,
                    "transmission":
                        "LOCKED",
                }

                save_json(
                    PHASE8_STATE,
                    existing,
                )

            print(
                "\nPHASE 8 STOPPED — "
                "EXECUTION REMAINS LOCKED"
            )

            break

        except Exception as exc:

            print(
                f"\nPHASE 8 ERROR: {exc}",
                flush=True,
            )

            if once:
                raise

            time.sleep(
                REFRESH_SECONDS,
            )


if __name__ == "__main__":
    main()
