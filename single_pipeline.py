#!/usr/bin/env python3

"""
CryptoMasterX1 — Single Pipeline Entry Point

This file does NOT duplicate the recovered phase source.
It loads the real recovered master_pipeline.py.

Execution remains locked by the project's own safety controls.
"""

from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / "master_pipeline.py"

if not MASTER.is_file():
    raise FileNotFoundError(
        f"REAL master_pipeline.py not found: {MASTER}"
    )

sys.path.insert(0, str(ROOT))

print("=" * 64)
print(" CryptoMasterX1 — SINGLE 11-PHASE PIPELINE")
print("=" * 64)
print(f"Source root: {ROOT}")
print(f"Master pipeline: {MASTER}")
print("Execution boundary: LOCKED")
print("Live execution: DISABLED")
print("Withdrawals/transfers: FORBIDDEN")
print("=" * 64)

# Execute the real recovered master pipeline.
runpy.run_path(str(MASTER), run_name="__main__")
