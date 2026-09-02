#!/usr/bin/env python3

"""
CryptoMasterX1 — Persistent Application Entry Point

Runs the verified Phase 4→8 pipeline continuously.

Safety:
    LIVE_EXECUTION = False
    ORDER_SUBMISSION = False
    WITHDRAWALS = False

This launcher does NOT activate live trading.
"""

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"

CYCLE_SECONDS = 60


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def run_phase(label, script):
    print()
    print("=" * 70)
    print(label)
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, str(ROOT / script), "--once"],
        cwd=ROOT,
    )

    print(f"{label} EXIT CODE: {result.returncode}")

    return result.returncode


def run_cycle(cycle):
    print()
    print("=" * 78)
    print(f"CRYPTOMASTERX1 — CYCLE {cycle}")
    print(f"UTC: {timestamp()}")
    print("=" * 78)

    phases = [
        ("PHASE 4 — MARKET DISCOVERY", "phase4_market_discovery.py"),
        ("PHASE 5 — TRADE INTELLIGENCE", "phase5_market_intelligence.py"),
        ("PHASE 6 — FINAL TRADE CONSTRUCTION", "phase6_trade_intelligence.py"),
        ("PHASE 7 — EXECUTION GATE", "phase7_final_validation.py"),
        ("PHASE 8 — TRADE LIFECYCLE", "phase8_execution_lifecycle_v8.py"),
    ]

    failures = []

    for label, script in phases:
        code = run_phase(label, script)

        if code != 0:
            failures.append((label, code))
            break

    print()
    print("=" * 78)

    if failures:
        print("CMX1 CYCLE STATUS: FAILED")
        for label, code in failures:
            print(f"{label}: EXIT {code}")
    else:
        print("CMX1 CYCLE STATUS: COMPLETE")

    print("LIVE EXECUTION: LOCKED")
    print("ORDER SUBMISSION: LOCKED")
    print("WITHDRAWALS: FORBIDDEN")
    print("=" * 78)

    return len(failures) == 0


def main():
    LOG_DIR.mkdir(exist_ok=True)

    print("=" * 78)
    print("CRYPTOMASTERX1 — PERSISTENT APPLICATION")
    print("=" * 78)
    print("Application started.")
    print("The process remains active between scan cycles.")
    print("Live execution: LOCKED")
    print("Order submission: LOCKED")
    print("Withdrawals: FORBIDDEN")
    print("=" * 78)

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


if __name__ == "__main__":
    main()
