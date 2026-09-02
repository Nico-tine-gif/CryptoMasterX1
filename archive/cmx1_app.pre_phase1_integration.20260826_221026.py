#!/usr/bin/env python3
"""
CryptoMasterX1 — AUTHORITATIVE PERSISTENT RUNTIME

Authoritative pipeline:

Phase 4  — Market Discovery
Phase 5  — Market Intelligence
Phase 6  — Trade Quality
Phase 7  — Entry Intelligence / Trade Construction
Phase 8  — Final Validation
Phase 9  — Execution + Lifecycle
Phase 10 — Pre-Execution System Gate
Phase 11 — Full System Verification

SAFETY:
    Execution boundary  = LOCKED
    Execution authorized = FALSE
    Order submission    = FALSE
    Bot armed           = FALSE
    Live execution      = FALSE
    Withdrawals         = FALSE

This runtime does NOT authorize live trading.
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CYCLE_SECONDS = 60

# ============================================================
# HARD SAFETY BOUNDARY
# ============================================================

EXECUTION_BOUNDARY = "LOCKED"
EXECUTION_AUTHORIZED = False
ORDER_SUBMISSION = False
BOT_ARMED = False
LIVE_EXECUTION = False
WITHDRAWALS = False


PHASES = [
    ("PHASE 4 — MARKET DISCOVERY", "phase4_market_discovery.py"),
    ("PHASE 5 — MARKET INTELLIGENCE", "phase5_market_intelligence.py"),
    ("PHASE 6 — TRADE QUALITY", "phase6_trade_quality.py"),
    ("PHASE 7 — ENTRY INTELLIGENCE / TRADE CONSTRUCTION",
     "phase7_entry_intelligence.py"),
    ("PHASE 8 — FINAL VALIDATION", "phase8_final_validation.py"),
    ("PHASE 9 — EXECUTION + LIFECYCLE", "phase9_execution_lifecycle.py"),
    ("PHASE 10 — PRE-EXECUTION SYSTEM GATE", "phase10_pre_execution_gate.py"),
    ("PHASE 11 — FULL SYSTEM VERIFICATION",
     "phase11_full_system_verification.py"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safety_banner() -> None:
    print("=" * 78)
    print("CRYPTOMASTERX1 — AUTHORITATIVE PERSISTENT RUNTIME")
    print("=" * 78)
    print("Authoritative pipeline: PHASE 4 → PHASE 11")
    print(f"Execution boundary:     {EXECUTION_BOUNDARY}")
    print(f"Execution authorized:   {EXECUTION_AUTHORIZED}")
    print(f"Order submission:       {ORDER_SUBMISSION}")
    print(f"Bot armed:              {BOT_ARMED}")
    print(f"Live execution:         {LIVE_EXECUTION}")
    print(f"Withdrawals:            {WITHDRAWALS}")
    print("=" * 78)


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
    print(f"UTC: {utc_now()}")
    print("=" * 78)

    failures = []

    for label, script in PHASES:
        code = run_phase(label, script)

        if code != 0:
            failures.append((label, code))
            print()
            print("PIPELINE STOPPED — UPSTREAM PHASE FAILED")
            break

    print()
    print("=" * 78)

    if failures:
        print("CMX1 CYCLE STATUS: FAILED")
        for label, code in failures:
            print(f"{label}: EXIT {code}")
    else:
        print("CMX1 CYCLE STATUS: COMPLETE")
        print("PHASE 4 → PHASE 11: SUCCESS")

    print()
    print("EXECUTION BOUNDARY : LOCKED")
    print("EXECUTION AUTHORIZED: FALSE")
    print("ORDER SUBMISSION    : DISABLED")
    print("BOT ARMED           : NO")
    print("LIVE EXECUTION      : FALSE")
    print("WITHDRAWALS         : FORBIDDEN")
    print("=" * 78)

    return not failures


def main() -> int:
    safety_banner()

    cycle = 0

    try:
        while True:
            cycle += 1

            run_cycle(cycle)

            print()
            print(f"NEXT CMX1 CYCLE IN {CYCLE_SECONDS} SECONDS")
            print("Press Ctrl+C to stop the application.")

            time.sleep(CYCLE_SECONDS)

    except KeyboardInterrupt:
        print()
        print("=" * 78)
        print("CRYPTOMASTERX1 — APPLICATION STOPPED BY USER")
        print("=" * 78)
        print("Execution boundary: LOCKED")
        print("Order submission: DISABLED")
        print("Withdrawals: FORBIDDEN")
        print("=" * 78)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
