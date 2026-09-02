#!/usr/bin/env python3
"""
CryptoMasterX1 — PHASE 10
PRE-EXECUTION SYSTEM GATE

Purpose:
    Verify the Phase 7 -> Phase 8 -> Phase 9 handoff.

Phase 10 DOES NOT:
    - construct trades
    - modify Entry
    - modify SL
    - modify TP1
    - modify TP2
    - recalculate trade levels
    - submit orders
    - arm the bot
    - authorize live execution
    - enable withdrawals

Phase ownership:
    Phase 7  = Trade Construction
    Phase 8  = Final Validation
    Phase 9  = Execution + Lifecycle
    Phase 10 = Pre-Execution System Gate

SAFETY:
    Execution remains LOCKED.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent

PHASE8_STATE = ROOT / "state" / "phase8_final_validation.json"
PHASE9_STATE = ROOT / "state" / "phase9_execution_lifecycle.json"
OUTPUT_STATE = ROOT / "state" / "phase10_pre_execution_gate.json"


# ============================================================
# HARD SAFETY BOUNDARY
# ============================================================

EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
WITHDRAWALS = False

EXECUTION_BOUNDARY = "LOCKED"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required state: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_phase8(state: dict) -> tuple[bool, list[str]]:
    errors = []

    if state.get("phase") != "PHASE_8":
        errors.append("Phase 8 state identifier invalid")

    if state.get("status") != "COMPLETE":
        errors.append("Phase 8 status is not COMPLETE")

    validation = state.get("validation", {})

    validated = validation.get("validated_candidates", [])

    if not isinstance(validated, list):
        errors.append("Phase 8 validated_candidates is not a list")
        return False, errors

    if len(validated) == 0:
        errors.append("Phase 8 contains zero validated candidates")

    if validation.get("validated") != len(validated):
        errors.append("Phase 8 validated count mismatch")

    if validation.get("rejected") != len(validation.get("rejected_candidates", [])):
        errors.append("Phase 8 rejected count mismatch")

    contract = state.get("validation_contract", {})

    if contract.get("phase7_owns_trade_construction") is not True:
        errors.append("Phase 7 trade-construction ownership missing")

    if contract.get("phase8_reconstructs_trade") is not False:
        errors.append("Phase 8 reconstruction boundary violated")

    if contract.get("phase8_changes_entry") is not False:
        errors.append("Phase 8 entry modification boundary violated")

    if contract.get("phase8_changes_sl") is not False:
        errors.append("Phase 8 SL modification boundary violated")

    if contract.get("phase8_changes_tp1") is not False:
        errors.append("Phase 8 TP1 modification boundary violated")

    if contract.get("phase8_changes_tp2") is not False:
        errors.append("Phase 8 TP2 modification boundary violated")

    return len(errors) == 0, errors


def validate_phase9(state: dict, phase8_count: int) -> tuple[bool, list[str]]:
    errors = []

    if state.get("phase") != 9:
        errors.append("Phase 9 identifier invalid")

    if state.get("name") != "Execution + Lifecycle":
        errors.append("Phase 9 name invalid")

    candidates = state.get("candidates", [])

    if len(candidates) != phase8_count:
        errors.append(
            f"Phase 9 candidate count mismatch: "
            f"{len(candidates)} != {phase8_count}"
        )

    inp = state.get("input", {})

    if inp.get("phase") != 8:
        errors.append("Phase 9 input phase is not 8")

    if inp.get("validated_candidates") != phase8_count:
        errors.append("Phase 9 input validated count mismatch")

    boundary = state.get("execution_boundary", {})

    if boundary.get("status") != "LOCKED":
        errors.append("Execution boundary is not LOCKED")

    if boundary.get("execution_authorized") is not False:
        errors.append("Execution authorization is not FALSE")

    if boundary.get("order_submission") is not False:
        errors.append("Order submission is not DISABLED")

    if boundary.get("bot_armed") is not False:
        errors.append("Bot is armed")

    if boundary.get("live_execution") is not False:
        errors.append("Live execution is not FALSE")

    if boundary.get("withdrawals") is not False:
        errors.append("Withdrawals are not forbidden")

    lifecycle = state.get("lifecycle", {})

    if lifecycle.get("orders_submitted") != 0:
        errors.append("Orders submitted is not zero")

    if lifecycle.get("active_positions") != []:
        errors.append("Active positions are not empty")

    if lifecycle.get("fills") != []:
        errors.append("Fills are not empty")

    if lifecycle.get("partial_fills") != []:
        errors.append("Partial fills are not empty")

    if lifecycle.get("closed_positions") != []:
        errors.append("Closed positions are not empty")

    ownership = state.get("ownership", {})

    if ownership.get("trade_construction") != "PHASE 7":
        errors.append("Trade construction owner is incorrect")

    if ownership.get("final_validation") != "PHASE 8":
        errors.append("Final validation owner is incorrect")

    if ownership.get("execution") != "PHASE 9":
        errors.append("Execution owner is incorrect")

    for key in (
        "trade_reconstruction",
        "entry_modification",
        "sl_modification",
        "tp_modification",
    ):
        if ownership.get(key) is not False:
            errors.append(f"Phase 9 {key} boundary violated")

    return len(errors) == 0, errors


def compare_phase8_phase9(
    phase8: dict,
    phase9: dict,
) -> tuple[bool, list[str]]:
    errors = []

    p8 = phase8["validation"]["validated_candidates"]
    p9 = phase9["candidates"]

    if len(p8) != len(p9):
        return False, ["Phase 8/Phase 9 candidate count mismatch"]

    fields = (
        "symbol",
        "direction",
        "entry",
        "sl",
        "tp1",
        "tp2",
        "rr",
        "confidence",
    )

    for index, (a, b) in enumerate(zip(p8, p9), 1):
        for field in fields:
            if a.get(field) != b.get(field):
                errors.append(
                    f"Candidate {index} {a.get('symbol')} "
                    f"field changed: {field}"
                )

    return len(errors) == 0, errors


def save_state(
    phase8_count: int,
    phase9_count: int,
    checks: dict,
    errors: list[str],
) -> None:

    OUTPUT_STATE.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "project": "CryptoMasterX1",
        "phase": "PHASE_10",
        "version": "10.0-PRE-EXECUTION-GATE",
        "timestamp_utc": utc_now(),
        "cycle": 1,

        "status": "PASS" if not errors else "FAIL",

        "pipeline": {
            "phase7": "TRADE CONSTRUCTION",
            "phase8": "FINAL VALIDATION",
            "phase9": "EXECUTION + LIFECYCLE",
            "phase10": "PRE-EXECUTION SYSTEM GATE",
        },

        "counts": {
            "phase8_validated": phase8_count,
            "phase9_lifecycle_ready": phase9_count,
        },

        "checks": checks,

        "errors": errors,

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
            "execution_lifecycle": "PHASE 9",
            "pre_execution_gate": "PHASE 10",
            "trade_reconstruction": False,
            "trade_modification": False,
        },
    }

    with OUTPUT_STATE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def run_once() -> int:
    print("=" * 78)
    print("CRYPTOMASTERX1 — PHASE 10 PRE-EXECUTION SYSTEM GATE")
    print("=" * 78)

    phase8 = load_json(PHASE8_STATE)
    phase9 = load_json(PHASE9_STATE)

    errors: list[str] = []
    checks = {}

    ok8, err8 = validate_phase8(phase8)
    checks["phase8_integrity"] = ok8
    errors.extend(err8)

    phase8_count = len(
        phase8.get("validation", {}).get("validated_candidates", [])
    )

    ok9, err9 = validate_phase9(phase9, phase8_count)
    checks["phase9_integrity"] = ok9
    errors.extend(err9)

    phase9_count = len(phase9.get("candidates", []))

    if ok8 and ok9:
        ok_handoff, err_handoff = compare_phase8_phase9(
            phase8,
            phase9,
        )
    else:
        ok_handoff = False
        err_handoff = ["Handoff comparison skipped because upstream check failed"]

    checks["phase8_to_phase9_immutable_handoff"] = ok_handoff
    errors.extend(err_handoff)

    checks["execution_locked"] = (
        EXECUTION_BOUNDARY == "LOCKED"
        and EXECUTION_AUTHORIZED is False
        and ORDER_SUBMISSION is False
        and BOT_ARMED is False
        and LIVE_EXECUTION is False
        and WITHDRAWALS is False
    )

    if not checks["execution_locked"]:
        errors.append("HARD EXECUTION SAFETY CHECK FAILED")

    passed = not errors

    save_state(
        phase8_count,
        phase9_count,
        checks,
        errors,
    )

    print(f"Phase 8 validated        : {phase8_count}")
    print(f"Phase 9 lifecycle-ready  : {phase9_count}")
    print()

    for name, result in checks.items():
        print(
            f"{name:<40}: "
            f"{'PASS' if result else 'FAIL'}"
        )

    print()
    print("-" * 78)

    if passed:
        print("PHASE 10 STATUS          : PASS")
    else:
        print("PHASE 10 STATUS          : FAIL")

        for error in errors:
            print("ERROR:", error)

    print("-" * 78)

    print("Execution boundary       : LOCKED")
    print("Execution authorized     : FALSE")
    print("Order submission         : DISABLED")
    print("Bot armed                : NO")
    print("Live execution           : FALSE")
    print("Withdrawals              : FORBIDDEN")
    print("=" * 78)

    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if not args.once:
        print("Use: python -u phase10_pre_execution_gate.py --once")
        return 0

    try:
        return run_once()
    except Exception as exc:
        print(
            "PHASE 10 ERROR:",
            type(exc).__name__,
            str(exc),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
