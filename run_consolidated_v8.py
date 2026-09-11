#!/usr/bin/env python3

"""
CryptoMasterX1 — Consolidated 8-Phase Runner

Legacy phases are deliberately NOT called for Phases 6-9.

Current authoritative path:

Phase 5
   ↓
Phase 6 — Digest + Fresh Construction + Sizing
   ↓
Phase 7 — Single Final Validation + Decision
   ↓
Phase 8 — Execution + Lifecycle
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(script):
    print()
    print("=" * 78)
    print(f"RUNNING {script}")
    print("=" * 78)

    result = subprocess.run(
        [sys.executable, str(ROOT / script)],
        cwd=ROOT,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"{script} FAILED with exit code "
            f"{result.returncode}"
        )


def main():
    # Phase 5 is the existing market-intelligence producer.
    if not (ROOT / "state/phase5_market_intelligence.json").exists():
        print(
            "ERROR: Phase 5 state does not exist."
        )
        print(
            "Run Phase 5 market intelligence first."
        )
        raise SystemExit(1)

    # Consolidated Phase 6.
    run("phase6_trade_intelligence.py")

    # Single validation + decision gate.
    run("phase7_final_validation.py")

    # Locked execution/lifecycle boundary.
    run("phase8_execution_lifecycle_v8.py")


if __name__ == "__main__":
    main()
