#!/usr/bin/env python3
"""
CryptoMasterX1 — AUTHORITATIVE PERSISTENT RUNTIME

AUTHORITATIVE PIPELINE:

Phase 4  = Market Discovery
Phase 5  = Market Intelligence
Phase 6  = Trade Quality
Phase 7  = Entry Intelligence / Trade Construction
Phase 8  = Final Validation
Phase 9  = Execution + Lifecycle
Phase 10 = Pre-Execution System Gate
Phase 11 = Full System Verification

SAFETY:
Execution remains LOCKED.
Order submission remains DISABLED.
Bot remains UNARMED.
Live execution remains FALSE.
Withdrawals remain FORBIDDEN.

This launcher does not alter trade construction or validation.
It only orchestrates the authoritative phase chain.
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CYCLE_SECONDS = 60

PHASES = [
    ("PHASE 4 — MARKET DISCOVERY", "phase4_market_discovery.py"),
    ("PHASE 5 — MARKET INTELLIGENCE", "phase5_market_intelligence.py"),
    ("PHASE 6 — TRADE QUALITY", "phase6_trade_quality.py"),
    ("PHASE 7 — ENTRY INTELLIGENCE / TRADE CONSTRUCTION",
     "phase7_entry_intelligence.py"),
    ("PHASE 8 — FINAL VALIDATION", "phase8_final_validation.py"),
    ("PHASE 9 — EXECUTION + LIFECYCLE",
     "phase9_execution_lifecycle.py"),
    ("PHASE 10 — PRE-EXECUTION SYSTEM GATE",
     "phase10_pre_execution_gate.py"),
    ("PHASE 11 — FULL SYSTEM VERIFICATION",
     "phase11_full_system_verification.py"),
]

SAFETY = {
    "execution_boundary": "LOCKED",
    "execution_authorized": False,
    "order_submission": False,
    "bot_armed": False,
    "live_execution": False,
    "withdrawals": False,
}


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def safety_ok() -> bool:
    return (
        SAFETY["execution_boundary"] == "LOCKED"
        and SAFETY["execution_authorized"] is False
        and SAFETY["order_submission"] is False
        and SAFETY["bot_armed"] is False
        and SAFETY["live_execution"] is False
        and SAFETY["withdrawals"] is False
    )


def run_phase(label: str, script: str) -> int:
    print()
    print("=" * 78)
    print(label)
    print("=" * 78)

    path = ROOT / script

    if not path.exists():
        print(f"ERROR: Missing phase file: {script}")
        return 1

    result = subprocess.run(
        [sys.executable, str(path), "--once"],
        cwd=ROOT,
    )

    print(f"{label} EXIT CODE: {result.returncode}")
    return result.returncode


def run_cycle(cycle: int) -> bool:
    print()
    print("=" * 78)
    print(f"CRYPTOMASTERX1 — AUTHORITATIVE CYCLE {cycle}")
    print(f"UTC: {timestamp()}")
    print("=" * 78)

    if not safety_ok():
        print("HARD SAFETY FAILURE — RUNTIME REFUSED")
        return False

    for label, script in PHASES:
        code = run_phase(label, script)

        if code != 0:
            print()
            print(f"PIPELINE STOPPED AT: {label}")
            print(f"EXIT CODE: {code}")
            print("NO DOWNSTREAM PHASES WILL RUN.")
            return False

        if not safety_ok():
            print()
            print("HARD SAFETY FAILURE AFTER PHASE.")
            print("PIPELINE STOPPED.")
            return False

    print()
    print("=" * 78)
    print("CRYPTOMASTERX1 — AUTHORITATIVE CYCLE COMPLETE")
    print("=" * 78)
    print("PHASE 4  → MARKET DISCOVERY")
    print("PHASE 5  → MARKET INTELLIGENCE")
    print("PHASE 6  → TRADE QUALITY")
    print("PHASE 7  → ENTRY INTELLIGENCE / TRADE CONSTRUCTION")
    print("PHASE 8  → FINAL VALIDATION")
    print("PHASE 9  → EXECUTION + LIFECYCLE")
    print("PHASE 10 → PRE-EXECUTION SYSTEM GATE")
    print("PHASE 11 → FULL SYSTEM VERIFICATION")
    print()
    print("EXECUTION BOUNDARY : LOCKED")
    print("EXECUTION AUTHORIZED: FALSE")
    print("ORDER SUBMISSION    : DISABLED")
    print("BOT ARMED           : NO")
    print("LIVE EXECUTION      : FALSE")
    print("WITHDRAWALS         : FORBIDDEN")
    print("=" * 78)

    return True


def main() -> int:
    print("=" * 78)
    print("CRYPTOMASTERX1 — AUTHORITATIVE PERSISTENT RUNTIME")
    print("=" * 78)
    print("Authoritative pipeline loaded.")
    print("Execution boundary: LOCKED")
    print("Order submission: DISABLED")
    print("Withdrawals: FORBIDDEN")
    print("=" * 78)

    cycle = 0

    try:
        while True:
            cycle += 1

            run_cycle(cycle)

            print()
            print(f"NEXT CYCLE IN {CYCLE_SECONDS} SECONDS")
            print("Press Ctrl+C to stop.")

            time.sleep(CYCLE_SECONDS)

    except KeyboardInterrupt:
        print()
        print("=" * 78)
        print("CRYPTOMASTERX1 — RUNTIME STOPPED BY USER")
        print("=" * 78)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
