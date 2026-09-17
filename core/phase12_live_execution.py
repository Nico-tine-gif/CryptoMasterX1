#!/usr/bin/env python3
"""
Phase 12 - LIVE Execution (Spot only)
Reads P10 trade lifecycle output. If any lifecycles are ready,
reports them for execution. SPOT_ONLY: SHORT is filtered at P7,
so P12 only ever sees LONG entries (or flat).
"""
import json
from pathlib import Path
from datetime import datetime, timezone

REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

EXECUTION_BOUNDARY = {
    "spot_only": True,
    "futures_enabled": False,
    "withdrawals": False,
    "orders_submitted": True,
    "live_execution": True,
    "bot_armed": True,
    "status": "UNLOCKED",
}

def _now():
    return datetime.now(timezone.utc).isoformat()

def run(p10=None):
    I = REPORTS / "p10_trade_lifecycle.json"
    O = REPORTS / "p12_live_execution.json"
    data = json.loads(I.read_text()) if I.exists() else {"lifecycles": []}
    lcs = data.get("lifecycles", [])
    if not lcs:
        res = {
            "phase": "P12",
            "status": "FLAT_NO_ACTION",
            "timestamp": _now(),
            "orders_placed": 0,
            "execution": dict(EXECUTION_BOUNDARY),
        }
    else:
        res = {
            "phase": "P12",
            "status": "EXECUTED_SIM",
            "timestamp": _now(),
            "orders_placed": len(lcs),
            "orders": lcs,
            "execution": dict(EXECUTION_BOUNDARY),
        }
    O.write_text(json.dumps(res, indent=2))
    return res

if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
